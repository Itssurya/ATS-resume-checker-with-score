"""
Flask Web Application for ATS Resume Analyzer SaaS

This module provides a comprehensive web interface for the ATS Resume Analyzer SaaS platform,
including user authentication, subscription management, and advanced analysis features.
"""

import os
import sys
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import json
from datetime import datetime
import io

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.parser import ResumeParser
from src.scorer import EnhancedATSResumeScorer as ATSResumeScorer
from src.recommender import ResumeRecommender
from src.utils import Config, FileHandler
from src.models import db, User, Analysis, SubscriptionPlan

# Import Neon.tech database config
from database_config import db_config, check_database_health
from src.auth import AuthManager, require_auth, require_subscription_plan, check_upload_limit, get_session_id
from src.billing import BillingManager, PlanManager
from src.report_generator import PDFReportGenerator

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Initialize Neon.tech PostgreSQL database
print("🔧 Initializing Neon.tech PostgreSQL database...")
try:
    # Set the database URL
    database_url = db_config.get_database_url()
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 5,
        'max_overflow': 10
    }
    
    # Initialize SQLAlchemy with app
    db.init_app(app)
    
    # Test connection
    if db_config.test_connection():
        print("✅ Neon.tech PostgreSQL database initialized successfully!")
    else:
        raise Exception("Database connection test failed")
        
except Exception as e:
    print(f"❌ Failed to initialize Neon.tech database: {e}")
    print("Please check your DATABASE_URL and Neon.tech connection")
    sys.exit(1)

# Upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Stripe configuration
app.config['STRIPE_PUBLISHABLE_KEY'] = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY', '')
app.config['STRIPE_WEBHOOK_SECRET'] = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
app.config['STRIPE_MEDIUM_PRICE_ID'] = os.environ.get('STRIPE_MEDIUM_PRICE_ID', '')
app.config['STRIPE_PRO_PRICE_ID'] = os.environ.get('STRIPE_PRO_PRICE_ID', '')

# Initialize extensions (db is already initialized above)
migrate = Migrate(app, db)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Ensure upload directory exists
FileHandler.ensure_directory(UPLOAD_FOLDER)

# Initialize components
parser = ResumeParser()
scorer = ATSResumeScorer()
recommender = ResumeRecommender()
billing_manager = BillingManager()
report_generator = PDFReportGenerator()


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        user, message = AuthManager.register_user(email, password, first_name, last_name)
        
        if user:
            login_user(user)
            return jsonify({
                'success': True,
                'message': message,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.get_full_name()
                }
            })
        else:
            return jsonify({'success': False, 'error': message}), 400
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        user, message = AuthManager.authenticate_user(email, password)
        
        if user:
            login_user(user, remember=True)
            return jsonify({
                'success': True,
                'message': message,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.get_full_name()
                }
            })
        else:
            return jsonify({'success': False, 'error': message}), 401
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('profile.html', user=current_user)


@app.route('/api/profile', methods=['GET', 'PUT'])
@login_required
def api_profile():
    """Get or update user profile."""
    if request.method == 'GET':
        return jsonify({
            'id': current_user.id,
            'email': current_user.email,
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'created_at': current_user.created_at.isoformat(),
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        user, message = AuthManager.update_user_profile(
            current_user.id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email')
        )
        
        if user:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400


@app.route('/api/profile/password', methods=['PUT'])
@login_required
def api_change_password():
    """Change user password."""
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    success, message = AuthManager.change_password(
        current_user.id, current_password, new_password
    )
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'error': message}), 400


# Subscription Routes
@app.route('/pricing')
def pricing():
    """Pricing page."""
    plans = billing_manager.get_all_plans()
    return render_template('pricing.html', plans=plans)


@app.route('/api/subscription/status')
@login_required
def subscription_status():
    """Get subscription status."""
    status = billing_manager.get_subscription_status(current_user)
    usage_stats = PlanManager.get_usage_stats(current_user)
    
    return jsonify({
        'subscription': status,
        'usage': usage_stats
    })


@app.route('/api/subscription/create', methods=['POST'])
@login_required
def create_subscription():
    """Create or update subscription."""
    data = request.get_json()
    plan_name = data.get('plan')
    payment_method_id = data.get('payment_method_id')
    
    try:
        plan = SubscriptionPlan(plan_name)
        subscription, error = billing_manager.create_subscription(
            current_user, plan, payment_method_id
        )
        
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({
            'success': True,
            'subscription_id': subscription.id,
            'client_secret': subscription.latest_invoice.payment_intent.client_secret
        })
    
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid plan'}), 400


@app.route('/api/subscription/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel subscription."""
    subscription, error = billing_manager.cancel_subscription(current_user)
    
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    return jsonify({'success': True, 'message': 'Subscription cancelled successfully'})


# Dashboard Routes
@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard."""
    # Get recent analyses
    recent_analyses = current_user.analyses.order_by(Analysis.created_at.desc()).limit(10).all()
    
    # Get usage stats
    usage_stats = PlanManager.get_usage_stats(current_user)
    
    # Get subscription status
    subscription_status = billing_manager.get_subscription_status(current_user)
    
    return render_template('dashboard.html', 
                         analyses=recent_analyses,
                         usage_stats=usage_stats,
                         subscription=subscription_status)


@app.route('/api/analyses')
@login_required
def get_analyses():
    """Get user's analysis history."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    analyses = current_user.analyses.order_by(Analysis.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'analyses': [analysis.to_dict() for analysis in analyses.items],
        'total': analyses.total,
        'pages': analyses.pages,
        'current_page': page
    })


@app.route('/api/analyses/<int:analysis_id>')
@login_required
def get_analysis(analysis_id):
    """Get specific analysis details."""
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first()
    
    if not analysis:
        return jsonify({'error': 'Analysis not found'}), 404
    
    return jsonify(analysis.to_dict())


@app.route('/analyze', methods=['POST'])
def analyze_resume():
    """Analyze uploaded resume against job description."""
    try:
        # Debug: Print request data
        print(f"DEBUG: Form data: {dict(request.form)}")
        print(f"DEBUG: Files: {list(request.files.keys())}")
        
        # Get form data
        job_description = request.form.get('job_description', '').strip()
        
        if not job_description:
            return jsonify({
                'success': False,
                'error': 'Job description is required'
            }), 400
        
        # Check upload limits
        can_upload, limit_message = check_upload_limit()
        if not can_upload:
            return jsonify({
                'success': False,
                'error': limit_message
            }), 403
        
        # Check if file was uploaded
        if 'resume_file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No resume file uploaded'
            }), 400
        
        file = request.files['resume_file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Please upload PDF, DOCX, or TXT files.'
            }), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Validate file
            validation = Config.validate_file(file_path)
            if not validation['valid']:
                return jsonify({
                    'success': False,
                    'error': f"File validation failed: {', '.join(validation['errors'])}"
                }), 400
            
            # Extract text from resume
            resume_text = parser.extract_text(file_path)
            if not resume_text:
                return jsonify({
                    'success': False,
                    'error': 'Could not extract text from resume file'
                }), 400
            
            # Perform analysis
            analysis = scorer.get_detailed_analysis(resume_text, job_description)
            
            # Generate recommendations
            recommendations = recommender.generate_recommendations(analysis)
            
            # Save analysis to database
            user_context = get_session_id() if not current_user.is_authenticated else None
            user_id = current_user.id if current_user.is_authenticated else None
            
            analysis_record = Analysis(
                user_id=user_id,
                session_id=user_context,
                resume_filename=filename,
                resume_text=resume_text,
                job_description=job_description,
                ats_score=analysis['ats_score'],
                similarity_score=analysis['similarity_score'],
                missing_keywords=analysis.get('missing_keywords', []),
                resume_keywords=analysis.get('resume_keywords', []),
                job_keywords=analysis.get('job_keywords', []),
                suggestions=analysis.get('suggestions', []),
                recommendations=recommendations,
                resume_word_count=analysis.get('resume_word_count', 0),
                job_description_word_count=analysis.get('job_description_word_count', 0),
                keyword_overlap_count=analysis.get('keyword_overlap_count', 0),
                keyword_overlap_percentage=analysis.get('keyword_overlap_percentage', 0),
                missing_keyword_count=analysis.get('missing_keyword_count', 0)
            )
            
            db.session.add(analysis_record)
            db.session.commit()
            
            # Track usage
            from src.auth import AuthManager
            AuthManager.track_usage(
                user_id=user_id,
                session_id=user_context,
                action='upload',
                details={'filename': filename, 'ats_score': analysis['ats_score']},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            # Prepare response
            response_data = {
                'success': True,
                'analysis': analysis,
                'recommendations': recommendations,
                'filename': filename,
                'analysis_id': analysis_record.id
            }
            
            return jsonify(response_data)
            
        finally:
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }), 500


@app.route('/api/analyze-text', methods=['POST'])
def analyze_text():
    """Analyze resume text directly (for demo purposes)."""
    try:
        data = request.get_json()
        resume_text = data.get('resume_text', '').strip()
        job_description = data.get('job_description', '').strip()
        
        if not resume_text or not job_description:
            return jsonify({
                'success': False,
                'error': 'Both resume text and job description are required'
            }), 400
        
        # Perform analysis
        analysis = scorer.get_detailed_analysis(resume_text, job_description)
        
        # Generate recommendations
        recommendations = recommender.generate_recommendations(analysis)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'recommendations': recommendations
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }), 500


# PDF Export Routes
@app.route('/api/export/pdf/<int:analysis_id>')
@login_required
@require_subscription_plan(SubscriptionPlan.MEDIUM)
def export_pdf(analysis_id):
    """Export analysis as PDF report."""
    analysis = Analysis.query.filter_by(id=analysis_id, user_id=current_user.id).first()
    
    if not analysis:
        return jsonify({'error': 'Analysis not found'}), 404
    
    # Generate PDF report
    user_info = {
        'name': current_user.get_full_name(),
        'email': current_user.email
    }
    
    pdf_content = report_generator.generate_report(
        analysis.to_dict(),
        user_info=user_info
    )
    
    # Create response
    response = send_file(
        io.BytesIO(pdf_content),
        as_attachment=True,
        download_name=f'ats_analysis_report_{analysis_id}.pdf',
        mimetype='application/pdf'
    )
    
    return response


# Stripe Webhook
@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events."""
    payload = request.get_data()
    signature = request.headers.get('Stripe-Signature')
    
    success, message = billing_manager.handle_webhook(payload, signature)
    
    if success:
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'error': message}), 400


@app.route('/health')
def health_check():
    """Health check endpoint."""
    try:
        db_health = check_database_health()
        return jsonify({
            'status': 'healthy' if db_health['status'] == 'healthy' else 'unhealthy',
            'version': '1.0.0',
            'database': db_health
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'version': '1.0.0',
            'database': {'error': str(e)}
        })


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 16MB.'
    }), 413


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Page not found'
    }), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    FileHandler.ensure_directory(UPLOAD_FOLDER)
    
    # Run the app
    app.run(debug=False, host='0.0.0.0', port=5000)
