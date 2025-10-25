"""
Database Models for ATS Resume Analyzer SaaS

This module contains SQLAlchemy models for user management,
subscriptions, usage tracking, and analysis history.
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import enum

db = SQLAlchemy()


class SubscriptionPlan(enum.Enum):
    """Subscription plan types."""
    FREE = "free"
    MEDIUM = "medium"
    PRO = "pro"


class User(UserMixin, db.Model):
    """User model for authentication and profile management."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    subscription = db.relationship('Subscription', backref='user', uselist=False, cascade='all, delete-orphan')
    analyses = db.relationship('Analysis', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    usage_tracking = db.relationship('UsageTracking', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def get_current_plan(self):
        """Get current subscription plan."""
        if self.subscription and self.subscription.is_active():
            return SubscriptionPlan(self.subscription.plan)
        return SubscriptionPlan.FREE
    
    def can_upload_resume(self):
        """Check if user can upload resume based on plan limits."""
        plan = self.get_current_plan()
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Count uploads this month
        uploads_this_month = self.analyses.filter(
            Analysis.created_at >= current_month
        ).count()
        
        # Check limits based on plan
        if plan == SubscriptionPlan.FREE:
            return uploads_this_month < 3
        elif plan == SubscriptionPlan.MEDIUM:
            return uploads_this_month < 30
        else:  # PRO
            return True
    
    def get_remaining_uploads(self):
        """Get remaining uploads for current month."""
        plan = self.get_current_plan()
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        uploads_this_month = self.analyses.filter(
            Analysis.created_at >= current_month
        ).count()
        
        if plan == SubscriptionPlan.FREE:
            return max(0, 3 - uploads_this_month)
        elif plan == SubscriptionPlan.MEDIUM:
            return max(0, 30 - uploads_this_month)
        else:  # PRO
            return float('inf')
    
    def __repr__(self):
        return f'<User {self.email}>'


class Subscription(db.Model):
    """Subscription model for managing user plans and billing."""
    
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan = db.Column(db.String(20), nullable=False, default='free')
    status = db.Column(db.String(20), nullable=False, default='active')  # active, cancelled, expired
    stripe_subscription_id = db.Column(db.String(100), unique=True, nullable=True)
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_active(self):
        """Check if subscription is active."""
        if self.status != 'active':
            return False
        
        if self.plan == SubscriptionPlan.FREE:
            return True
        
        if self.current_period_end:
            return datetime.utcnow() < self.current_period_end
        
        return True
    
    def get_plan_features(self):
        """Get features available for current plan."""
        features = {
            SubscriptionPlan.FREE: {
                'max_uploads_per_month': 3,
                'has_advanced_suggestions': False,
                'has_export_reports': False,
                'has_ai_suggestions': False,
                'has_priority_support': False,
                'has_multi_language': False,
                'max_history': 0
            },
            SubscriptionPlan.MEDIUM: {
                'max_uploads_per_month': 30,
                'has_advanced_suggestions': True,
                'has_export_reports': True,
                'has_ai_suggestions': False,
                'has_priority_support': False,
                'has_multi_language': False,
                'max_history': 10
            },
            SubscriptionPlan.PRO: {
                'max_uploads_per_month': -1,  # unlimited
                'has_advanced_suggestions': True,
                'has_export_reports': True,
                'has_ai_suggestions': True,
                'has_priority_support': True,
                'has_multi_language': True,
                'max_history': -1  # unlimited
            }
        }
        return features.get(self.plan, features[SubscriptionPlan.FREE])
    
    def __repr__(self):
        return f'<Subscription {self.user.email} - {self.plan.value}>'


class Analysis(db.Model):
    """Analysis model for storing resume analysis results."""
    
    __tablename__ = 'analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for free users
    session_id = db.Column(db.String(100), nullable=True)  # For anonymous users
    
    # Analysis data
    resume_filename = db.Column(db.String(255), nullable=False)
    resume_text = db.Column(db.Text, nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    
    # Results
    ats_score = db.Column(db.Float, nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    missing_keywords = db.Column(db.JSON, nullable=True)  # List of missing keywords
    resume_keywords = db.Column(db.JSON, nullable=True)   # List of resume keywords
    job_keywords = db.Column(db.JSON, nullable=True)      # List of job keywords
    suggestions = db.Column(db.JSON, nullable=True)       # List of suggestions
    recommendations = db.Column(db.JSON, nullable=True)   # Detailed recommendations
    
    # Metadata
    resume_word_count = db.Column(db.Integer, nullable=True)
    job_description_word_count = db.Column(db.Integer, nullable=True)
    keyword_overlap_count = db.Column(db.Integer, nullable=True)
    keyword_overlap_percentage = db.Column(db.Float, nullable=True)
    missing_keyword_count = db.Column(db.Integer, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert analysis to dictionary for API responses."""
        return {
            'id': self.id,
            'ats_score': self.ats_score,
            'similarity_score': self.similarity_score,
            'missing_keywords': self.missing_keywords or [],
            'resume_keywords': self.resume_keywords or [],
            'job_keywords': self.job_keywords or [],
            'suggestions': self.suggestions or [],
            'recommendations': self.recommendations or {},
            'resume_word_count': self.resume_word_count,
            'job_description_word_count': self.job_description_word_count,
            'keyword_overlap_count': self.keyword_overlap_count,
            'keyword_overlap_percentage': self.keyword_overlap_percentage,
            'missing_keyword_count': self.missing_keyword_count,
            'created_at': self.created_at.isoformat(),
            'resume_filename': self.resume_filename
        }
    
    def __repr__(self):
        return f'<Analysis {self.id} - Score: {self.ats_score}>'


class UsageTracking(db.Model):
    """Usage tracking model for monitoring user activity."""
    
    __tablename__ = 'usage_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=True)
    
    action = db.Column(db.String(50), nullable=False)  # upload, analysis, export, etc.
    details = db.Column(db.JSON, nullable=True)        # Additional action details
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UsageTracking {self.action} - {self.created_at}>'


class PaymentHistory(db.Model):
    """Payment history model for tracking transactions."""
    
    __tablename__ = 'payment_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    
    stripe_payment_intent_id = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Amount in cents
    currency = db.Column(db.String(3), nullable=False, default='usd')
    status = db.Column(db.String(20), nullable=False)  # succeeded, failed, pending
    plan = db.Column(db.String(20), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PaymentHistory {self.stripe_payment_intent_id} - {self.status}>'


class SystemConfig(db.Model):
    """System configuration model for storing app settings."""
    
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemConfig {self.key}>'




