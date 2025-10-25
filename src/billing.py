"""
Billing and Subscription Management Module

This module handles subscription management, payment processing,
and plan upgrades/downgrades for the ATS Resume Analyzer SaaS platform.
"""

import stripe
from datetime import datetime, timedelta
from flask import current_app
from .models import db, User, Subscription, SubscriptionPlan, PaymentHistory, Analysis
from .auth import AuthManager


class BillingManager:
    """Billing manager for handling subscriptions and payments."""
    
    def __init__(self):
        """Initialize billing manager."""
        self._stripe_initialized = False
    
    def _init_stripe(self):
        """Initialize Stripe with API key if not already done."""
        if not self._stripe_initialized:
            stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY', '')
            self._stripe_initialized = True
    
    def create_customer(self, user, payment_method_id=None):
        """Create Stripe customer for user."""
        self._init_stripe()
        try:
            customer_data = {
                'email': user.email,
                'name': user.get_full_name(),
                'metadata': {
                    'user_id': str(user.id)
                }
            }
            
            if payment_method_id:
                customer_data['payment_method'] = payment_method_id
                customer_data['invoice_settings'] = {
                    'default_payment_method': payment_method_id
                }
            
            customer = stripe.Customer.create(**customer_data)
            
            # Update user's subscription with customer ID
            if user.subscription:
                user.subscription.stripe_customer_id = customer.id
                db.session.commit()
            
            return customer, None
        
        except stripe.error.StripeError as e:
            return None, str(e)
    
    def create_subscription(self, user, plan, payment_method_id=None):
        """Create or update subscription for user."""
        self._init_stripe()
        try:
            # Get plan pricing
            plan_prices = {
                SubscriptionPlan.MEDIUM: current_app.config.get('STRIPE_MEDIUM_PRICE_ID'),
                SubscriptionPlan.PRO: current_app.config.get('STRIPE_PRO_PRICE_ID')
            }
            
            price_id = plan_prices.get(plan)
            if not price_id:
                return None, f"Invalid plan: {plan}"
            
            # Create or get customer
            if not user.subscription or not user.subscription.stripe_customer_id:
                customer, error = self.create_customer(user, payment_method_id)
                if error:
                    return None, error
            else:
                customer_id = user.subscription.stripe_customer_id
                customer = stripe.Customer.retrieve(customer_id)
            
            # Create subscription
            subscription_data = {
                'customer': customer.id,
                'items': [{'price': price_id}],
                'payment_behavior': 'default_incomplete',
                'payment_settings': {'save_default_payment_method': 'on_subscription'},
                'expand': ['latest_invoice.payment_intent'],
            }
            
            if payment_method_id:
                subscription_data['default_payment_method'] = payment_method_id
            
            stripe_subscription = stripe.Subscription.create(**subscription_data)
            
            # Update or create local subscription
            if user.subscription:
                subscription = user.subscription
            else:
                subscription = Subscription(user_id=user.id)
                db.session.add(subscription)
            
            subscription.plan = plan
            subscription.status = 'active'
            subscription.stripe_subscription_id = stripe_subscription.id
            subscription.stripe_customer_id = customer.id
            subscription.current_period_start = datetime.fromtimestamp(
                stripe_subscription.current_period_start
            )
            subscription.current_period_end = datetime.fromtimestamp(
                stripe_subscription.current_period_end
            )
            
            db.session.commit()
            
            return stripe_subscription, None
        
        except stripe.error.StripeError as e:
            return None, str(e)
    
    def cancel_subscription(self, user):
        """Cancel user's subscription."""
        self._init_stripe()
        try:
            if not user.subscription or not user.subscription.stripe_subscription_id:
                return None, "No active subscription found"
            
            stripe_subscription = stripe.Subscription.retrieve(
                user.subscription.stripe_subscription_id
            )
            
            # Cancel at period end
            stripe.Subscription.modify(
                user.subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            # Update local subscription
            user.subscription.status = 'cancelled'
            db.session.commit()
            
            return stripe_subscription, None
        
        except stripe.error.StripeError as e:
            return None, str(e)
    
    def reactivate_subscription(self, user):
        """Reactivate cancelled subscription."""
        self._init_stripe()
        try:
            if not user.subscription or not user.subscription.stripe_subscription_id:
                return None, "No subscription found"
            
            stripe_subscription = stripe.Subscription.retrieve(
                user.subscription.stripe_subscription_id
            )
            
            # Remove cancellation
            stripe.Subscription.modify(
                user.subscription.stripe_subscription_id,
                cancel_at_period_end=False
            )
            
            # Update local subscription
            user.subscription.status = 'active'
            db.session.commit()
            
            return stripe_subscription, None
        
        except stripe.error.StripeError as e:
            return None, str(e)
    
    def get_subscription_status(self, user):
        """Get detailed subscription status."""
        self._init_stripe()
        if not user.subscription:
            return {
                'plan': 'free',
                'status': 'active',
                'current_period_end': None,
                'cancel_at_period_end': False,
                'features': self.get_plan_features(SubscriptionPlan.FREE)
            }
        
        try:
            if user.subscription.stripe_subscription_id:
                stripe_subscription = stripe.Subscription.retrieve(
                    user.subscription.stripe_subscription_id
                )
                
                return {
                    'plan': user.subscription.plan,
                    'status': stripe_subscription.status,
                    'current_period_end': datetime.fromtimestamp(
                        stripe_subscription.current_period_end
                    ).isoformat(),
                    'cancel_at_period_end': stripe_subscription.cancel_at_period_end,
                    'features': self.get_plan_features(SubscriptionPlan(user.subscription.plan))
                }
            else:
                return {
                    'plan': user.subscription.plan,
                    'status': user.subscription.status,
                    'current_period_end': user.subscription.current_period_end.isoformat() if user.subscription.current_period_end else None,
                    'cancel_at_period_end': False,
                    'features': self.get_plan_features(SubscriptionPlan(user.subscription.plan))
                }
        
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error: {str(e)}")
            return {
                'plan': user.subscription.plan,
                'status': user.subscription.status,
                'current_period_end': user.subscription.current_period_end.isoformat() if user.subscription.current_period_end else None,
                'cancel_at_period_end': False,
                'features': self.get_plan_features(SubscriptionPlan(user.subscription.plan))
            }
    
    def get_plan_features(self, plan):
        """Get features for a specific plan."""
        if plan == SubscriptionPlan.FREE:
            return {
                'max_uploads_per_month': 3,
                'has_advanced_suggestions': False,
                'has_export_reports': False,
                'has_ai_suggestions': False,
                'has_priority_support': False,
                'has_multi_language': False,
                'max_history': 0,
                'price': 0
            }
        elif plan == SubscriptionPlan.MEDIUM:
            return {
                'max_uploads_per_month': 30,
                'has_advanced_suggestions': True,
                'has_export_reports': True,
                'has_ai_suggestions': False,
                'has_priority_support': False,
                'has_multi_language': False,
                'max_history': 10,
                'price': 9.99
            }
        else:  # PRO
            return {
                'max_uploads_per_month': -1,  # unlimited
                'has_advanced_suggestions': True,
                'has_export_reports': True,
                'has_ai_suggestions': True,
                'has_priority_support': True,
                'has_multi_language': True,
                'max_history': -1,  # unlimited
                'price': 29.99
            }
    
    def get_all_plans(self):
        """Get all available plans with features."""
        return {
            'free': self.get_plan_features(SubscriptionPlan.FREE),
            'medium': self.get_plan_features(SubscriptionPlan.MEDIUM),
            'pro': self.get_plan_features(SubscriptionPlan.PRO)
        }
    
    def handle_webhook(self, payload, signature):
        """Handle Stripe webhook events."""
        self._init_stripe()
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, current_app.config.get('STRIPE_WEBHOOK_SECRET')
            )
        except ValueError:
            return False, "Invalid payload"
        except stripe.error.SignatureVerificationError:
            return False, "Invalid signature"
        
        # Handle different event types
        if event['type'] == 'customer.subscription.updated':
            self._handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            self._handle_subscription_deleted(event['data']['object'])
        elif event['type'] == 'invoice.payment_succeeded':
            self._handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            self._handle_payment_failed(event['data']['object'])
        
        return True, "Webhook processed successfully"
    
    def _handle_subscription_updated(self, subscription_data):
        """Handle subscription updated webhook."""
        try:
            subscription = Subscription.query.filter_by(
                stripe_subscription_id=subscription_data['id']
            ).first()
            
            if subscription:
                subscription.status = subscription_data['status']
                subscription.current_period_start = datetime.fromtimestamp(
                    subscription_data['current_period_start']
                )
                subscription.current_period_end = datetime.fromtimestamp(
                    subscription_data['current_period_end']
                )
                db.session.commit()
        
        except Exception as e:
            current_app.logger.error(f"Error handling subscription update: {str(e)}")
    
    def _handle_subscription_deleted(self, subscription_data):
        """Handle subscription deleted webhook."""
        try:
            subscription = Subscription.query.filter_by(
                stripe_subscription_id=subscription_data['id']
            ).first()
            
            if subscription:
                subscription.status = 'cancelled'
                subscription.plan = 'free'
                db.session.commit()
        
        except Exception as e:
            current_app.logger.error(f"Error handling subscription deletion: {str(e)}")
    
    def _handle_payment_succeeded(self, invoice_data):
        """Handle successful payment webhook."""
        try:
            subscription_id = invoice_data.get('subscription')
            if subscription_id:
                subscription = Subscription.query.filter_by(
                    stripe_subscription_id=subscription_id
                ).first()
                
                if subscription:
                    # Record payment history
                    payment = PaymentHistory(
                        user_id=subscription.user_id,
                        subscription_id=subscription.id,
                        stripe_payment_intent_id=invoice_data['payment_intent'],
                        amount=invoice_data['amount_paid'],
                        currency=invoice_data['currency'],
                        status='succeeded',
                        plan=subscription.plan
                    )
                    db.session.add(payment)
                    db.session.commit()
        
        except Exception as e:
            current_app.logger.error(f"Error handling payment success: {str(e)}")
    
    def _handle_payment_failed(self, invoice_data):
        """Handle failed payment webhook."""
        try:
            subscription_id = invoice_data.get('subscription')
            if subscription_id:
                subscription = Subscription.query.filter_by(
                    stripe_subscription_id=subscription_id
                ).first()
                
                if subscription:
                    # Record failed payment
                    payment = PaymentHistory(
                        user_id=subscription.user_id,
                        subscription_id=subscription.id,
                        stripe_payment_intent_id=invoice_data['payment_intent'],
                        amount=invoice_data['amount_due'],
                        currency=invoice_data['currency'],
                        status='failed',
                        plan=subscription.plan
                    )
                    db.session.add(payment)
                    db.session.commit()
        
        except Exception as e:
            current_app.logger.error(f"Error handling payment failure: {str(e)}")


class PlanManager:
    """Plan management utilities."""
    
    @staticmethod
    def can_access_feature(user, feature_name):
        """Check if user can access a specific feature."""
        if not user.is_authenticated:
            return False
        
        plan = user.get_current_plan()
        features = BillingManager().get_plan_features(plan)
        
        return features.get(feature_name, False)
    
    @staticmethod
    def get_usage_stats(user):
        """Get user's usage statistics for current month."""
        if not user.is_authenticated:
            return None
        
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        uploads_this_month = user.analyses.filter(
            Analysis.created_at >= current_month
        ).count()
        
        plan = user.get_current_plan()
        features = BillingManager().get_plan_features(plan)
        max_uploads = features['max_uploads_per_month']
        
        return {
            'uploads_this_month': uploads_this_month,
            'max_uploads': max_uploads,
            'remaining_uploads': max_uploads - uploads_this_month if max_uploads > 0 else float('inf'),
            'plan': plan.value if hasattr(plan, 'value') else plan
        }




