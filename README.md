# 🎯 ATS Resume Analyzer

A powerful AI-powered Application Tracking System (ATS) that analyzes resumes against job descriptions using advanced NLP models and provides detailed scoring insights.

## ✨ Features

- **🤖 AI-Powered Analysis**: Uses Hugging Face's `sentence-transformers` model for semantic similarity
- **📊 Hybrid Scoring**: Combines TF-IDF keyword matching with semantic analysis
- **🔐 User Authentication**: Secure login/registration system
- **💳 Subscription Plans**: Free, Medium, and Pro tiers with usage limits
- **📈 Analytics Dashboard**: Track usage statistics and analysis history
- **☁️ Cloud Database**: PostgreSQL with Neon.tech for scalable data storage
- **📄 Multi-format Support**: PDF, DOCX, and TXT resume uploads

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database (Neon.tech recommended)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/P-ATS.git
   cd P-ATS
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements_huggingface.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your database credentials
   ```

5. **Initialize database**
   ```bash
   python create_neon_tables.py
   ```

6. **Run the application**
   ```bash
   cd app
   python app.py
   ```

7. **Access the application**
   - Open your browser to `http://localhost:5000`
   - Register a new account or use admin credentials:
     - Email: `admin@atsanalyzer.com`
     - Password: `admin123`

## 🏗️ Architecture

### Tech Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL with Neon.tech
- **AI Models**: Hugging Face Transformers
- **Frontend**: HTML5, CSS3, JavaScript
- **Authentication**: Flask-Login
- **ORM**: SQLAlchemy
- **Migrations**: Alembic

### Project Structure

```
P-ATS/
├── app/                    # Flask application
│   ├── app.py             # Main application file
│   ├── templates/         # HTML templates
│   ├── static/            # CSS, JS, images
│   └── uploads/           # File uploads
├── src/                   # Core modules
│   ├── auth.py            # Authentication logic
│   ├── billing.py         # Subscription management
│   ├── models.py          # Database models
│   ├── scorer.py          # Resume scoring engine
│   └── utils.py           # Utility functions
├── models/                # AI model storage
├── data/                  # Sample data
├── alembic/              # Database migrations
└── requirements.txt       # Dependencies
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/database?sslmode=require

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Hugging Face Model
HF_MODEL_NAME=anass1209/resume-job-matcher-all-MiniLM-L6-v2
```

### Database Setup

1. **Create Neon.tech account** at [neon.tech](https://neon.tech)
2. **Create new project** and get connection string
3. **Update DATABASE_URL** in `.env` file
4. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

## 📊 AI Models

### Primary Model
- **Model**: `anass1209/resume-job-matcher-all-MiniLM-L6-v2`
- **Purpose**: Semantic similarity between resume and job description
- **Type**: Sentence Transformers
- **Performance**: Optimized for resume-job matching

### Scoring Algorithm

1. **TF-IDF Analysis**: Keyword frequency and importance
2. **Semantic Similarity**: Contextual understanding using transformers
3. **Hybrid Scoring**: Weighted combination of both methods
4. **Detailed Breakdown**: Skills, experience, education scoring

## 💳 Subscription Plans

| Plan | Price | Analyses/Month | Features |
|------|-------|----------------|----------|
| **Free** | $0 | 5 | Basic analysis |
| **Medium** | $9.99 | 50 | Advanced insights |
| **Pro** | $19.99 | Unlimited | Full features + API |

## 🔐 Security Features

- **Password Hashing**: Secure password storage with Werkzeug
- **Session Management**: Flask-Login integration
- **File Validation**: Secure file upload handling
- **SQL Injection Protection**: SQLAlchemy ORM
- **Environment Variables**: Sensitive data protection

## 📈 Usage Analytics

Track your analysis history with:
- **Usage Statistics**: Monthly analysis counts
- **Score Trends**: Performance over time
- **Plan Limits**: Current subscription status
- **History**: Previous analysis results

## 🚀 Deployment

### Production Deployment

1. **Set production environment variables**
2. **Use production WSGI server** (Gunicorn recommended)
3. **Configure reverse proxy** (Nginx)
4. **Set up SSL certificates**
5. **Configure database connection pooling**

### Docker Deployment

```bash
# Build image
docker build -t ats-analyzer .

# Run container
docker run -p 5000:5000 ats-analyzer
```

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=src tests/
```

## 📝 API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - User logout

### Analysis
- `POST /analyze` - Analyze resume
- `GET /analysis/<id>` - Get analysis result
- `GET /dashboard` - User dashboard

### Billing
- `GET /pricing` - Subscription plans
- `POST /subscribe` - Subscribe to plan
- `GET /billing` - Billing history

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Hugging Face](https://huggingface.co/) for transformer models
- [Neon.tech](https://neon.tech/) for PostgreSQL hosting
- [Flask](https://flask.palletsprojects.com/) web framework
- [Sentence Transformers](https://www.sbert.net/) for semantic analysis

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/P-ATS/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/P-ATS/wiki)
- **Email**: support@atsanalyzer.com

## 🔄 Changelog

### v1.0.0 (Current)
- Initial release with core ATS functionality
- Hugging Face model integration
- PostgreSQL with Neon.tech
- User authentication and subscription system
- Hybrid scoring algorithm

---

**Made with ❤️ for better hiring decisions**
