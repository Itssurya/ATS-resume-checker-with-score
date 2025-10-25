"""
Authentication and User Management Module

This module handles user authentication, registration, and session management
for the ATS Resume Analyzer SaaS platform.
"""

import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import re

from .models import db, User, Subscription, SubscriptionPlan, UsageTracking


class AuthManager:
    """Authentication manager for handling user operations."""
    
    @staticmethod
    def validate_email(email):
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password):
        """Validate password strength."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        return True, "Password is valid"
    
    @staticmethod
    def register_user(email, password, first_name, last_name):
        """Register a new user."""
        # Validate input
        if not AuthManager.validate_email(email):
            return None, "Invalid email format"
        
        is_valid, message = AuthManager.validate_password(password)
        if not is_valid:
            return None, message
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return None, "Email already registered"
        
        # Create user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_verified=False
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Create free subscription
            subscription = Subscription(
                user_id=user.id,
                plan='free',
                status='active'
            )
            db.session.add(subscription)
            db.session.commit()
            
            return user, "User registered successfully"
        
        except Exception as e:
            db.session.rollback()
            return None, f"Registration failed: {str(e)}"
    
    @staticmethod
    def authenticate_user(email, password):
        """Authenticate user with email and password."""
        user = User.query.filter_by(email=email).first()
        
        if user and user.is_active:
            # For development, also check if password is 'admin123' for admin user
            if email == 'admin@atsanalyzer.com' and password == 'admin123':
                user.last_login = datetime.utcnow()
                db.session.commit()
                return user, "Login successful"
            elif user.check_password(password):
                user.last_login = datetime.utcnow()
                db.session.commit()
                return user, "Login successful"
        
        return None, "Invalid email or password"
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID."""
        return db.session.get(User, user_id)
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email."""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def update_user_profile(user_id, **kwargs):
        """Update user profile information."""
        user = User.query.get(user_id)
        if not user:
            return None, "User not found"
        
        try:
            # Update allowed fields
            allowed_fields = ['first_name', 'last_name', 'email']
            for field, value in kwargs.items():
                if field in allowed_fields and value:
                    setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            return user, "Profile updated successfully"
        
        except Exception as e:
            db.session.rollback()
            return None, f"Update failed: {str(e)}"
    
    @staticmethod
    def change_password(user_id, current_password, new_password):
        """Change user password."""
        user = User.query.get(user_id)
        if not user:
            return False, "User not found"
        
        if not user.check_password(current_password):
            return False, "Current password is incorrect"
        
        is_valid, message = AuthManager.validate_password(new_password)
        if not is_valid:
            return False, message
        
        try:
            user.set_password(new_password)
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            return True, "Password changed successfully"
        
        except Exception as e:
            db.session.rollback()
            return False, f"Password change failed: {str(e)}"
    
    @staticmethod
    def track_usage(user_id, session_id, action, details=None, ip_address=None, user_agent=None):
        """Track user usage for analytics and billing."""
        try:
            usage = UsageTracking(
                user_id=user_id,
                session_id=session_id,
                action=action,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.add(usage)
            db.session.commit()
        except Exception as e:
            # Don't fail the main operation if tracking fails
            current_app.logger.error(f"Usage tracking failed: {str(e)}")


def require_auth(f):
    """Decorator to require authentication for API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def require_subscription_plan(required_plan):
    """Decorator to require specific subscription plan."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_plan = current_user.get_current_plan()
            plan_hierarchy = {
                SubscriptionPlan.FREE: 0,
                SubscriptionPlan.MEDIUM: 1,
                SubscriptionPlan.PRO: 2
            }
            
            if plan_hierarchy.get(user_plan, 0) < plan_hierarchy.get(required_plan, 0):
                return jsonify({
                    'error': f'{required_plan.value.title()} plan required',
                    'current_plan': user_plan.value,
                    'required_plan': required_plan.value
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_session_id():
    """Get or create session ID for anonymous users."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        session_id = secrets.token_urlsafe(32)
    return session_id


def check_upload_limit():
    """Check if user can upload resume based on plan limits."""
    if current_user.is_authenticated:
        if not current_user.can_upload_resume():
            plan = current_user.get_current_plan()
            remaining = current_user.get_remaining_uploads()
            return False, f"Upload limit reached for {plan.value} plan. Remaining: {remaining}"
        return True, "Upload allowed"
    else:
        # For anonymous users, check session-based limits
        session_id = get_session_id()
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        uploads_this_month = UsageTracking.query.filter(
            UsageTracking.session_id == session_id,
            UsageTracking.action == 'upload',
            UsageTracking.created_at >= current_month
        ).count()
        
        if uploads_this_month >= 3:  # Free limit for anonymous users
            return False, "Upload limit reached for anonymous users (3 per month). Please sign up for more uploads."
        
        return True, "Upload allowed"


class SessionManager:
    """Session management for anonymous and authenticated users."""
    
    @staticmethod
    def create_session():
        """Create a new session for anonymous users."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_user_context():
        """Get current user context (authenticated or anonymous)."""
        if current_user.is_authenticated:
            return {
                'user_id': current_user.id,
                'session_id': None,
                'is_authenticated': True,
                'plan': current_user.get_current_plan().value,
                'remaining_uploads': current_user.get_remaining_uploads()
            }
        else:
            session_id = get_session_id()
            return {
                'user_id': None,
                'session_id': session_id,
                'is_authenticated': False,
                'plan': 'free',
                'remaining_uploads': 3  # Default free limit
            }




