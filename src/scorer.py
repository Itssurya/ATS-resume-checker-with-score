"""
Enhanced ATS Resume Scorer with Multiple Model Support

This module provides resume analysis using both traditional TF-IDF and 
Hugging Face transformer models for maximum accuracy and flexibility.
"""

import re
import nltk
from typing import List, Dict, Tuple, Set, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from .model_manager import model_manager
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Try to import Hugging Face models
try:
    from sentence_transformers import SentenceTransformer
    HUGGINGFACE_AVAILABLE = True
    print("✅ Hugging Face models available")
except ImportError:
    HUGGINGFACE_AVAILABLE = False
    print("⚠️  Hugging Face models not available. Install with: pip install sentence-transformers")


class EnhancedATSResumeScorer:
    """
    Enhanced ATS Resume Scorer with support for multiple model types.
    
    Features:
    - Traditional TF-IDF analysis (fast, lightweight)
    - Hugging Face transformer models (high accuracy)
    - Automatic model selection based on availability
    - Hybrid scoring combining multiple approaches
    """
    
    def __init__(self, model_name: str = "default", use_huggingface: bool = True):
        """
        Initialize the EnhancedATSResumeScorer.
        
        Args:
            model_name (str): Model name for TF-IDF
            use_huggingface (bool): Whether to use Hugging Face models if available
        """
        self.model_name = model_name
        self.use_huggingface = use_huggingface and HUGGINGFACE_AVAILABLE
        self.stop_words = set(stopwords.words('english'))
        
        # Initialize TF-IDF model
        self.vectorizer = model_manager.load_tfidf_model(model_name)
        if self.vectorizer is None:
            print(f"🔄 No existing TF-IDF model found. Creating new one: {model_name}")
            self.vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=1000,
                lowercase=True,
                min_df=1,
                max_df=0.95
            )
            
            # Train with sample data
            sample_texts = [
                "software engineer python javascript react node.js aws full-stack development database design cloud architecture agile git ci/cd",
                "data scientist machine learning python r sql tensorflow scikit-learn statistical analysis data visualization business acumen",
                "product manager agile scrum user research product strategy cross-functional leadership analytical skills stakeholder management",
                "marketing manager digital marketing social media content strategy google analytics facebook ads seo budget management roi optimization",
                "sales representative b2b sales crm systems lead generation relationship building communication skills customer service negotiation",
                "ux ui designer user research wireframing prototyping figma sketch mobile design accessibility responsive design user testing",
                "devops engineer aws docker kubernetes terraform jenkins linux monitoring security automation ci/cd cloud architecture",
                "business analyst requirements gathering process improvement sql excel tableau data analysis stakeholder management communication skills"
            ]
            
            self.vectorizer.fit(sample_texts)
            model_manager.save_tfidf_model(self.vectorizer, model_name)
            print(f"✅ Trained and saved TF-IDF model: {model_name}")
        
        # Initialize Hugging Face model if available and requested
        self.hf_model = None
        if self.use_huggingface:
            try:
                # Use the best resume-specific model
                hf_model_name = "anass1209/resume-job-matcher-all-MiniLM-L6-v2"
                print(f"🔄 Loading Hugging Face model: {hf_model_name}")
                self.hf_model = SentenceTransformer(hf_model_name)
                print(f"✅ Successfully loaded Hugging Face model: {hf_model_name}")
            except Exception as e:
                print(f"❌ Failed to load Hugging Face model: {e}")
                print("🔄 Falling back to general-purpose model...")
                try:
                    self.hf_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
                    print("✅ Loaded fallback Hugging Face model")
                except Exception as e2:
                    print(f"❌ Failed to load fallback model: {e2}")
                    self.hf_model = None
                    self.use_huggingface = False
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text by cleaning and normalizing."""
        if not text:
            return ""
        
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def extract_keywords(self, text: str, top_k: int = 20) -> List[str]:
        """Extract important keywords from text."""
        if not text:
            return []
        
        tokens = word_tokenize(text.lower())
        keywords = [token for token in tokens 
                   if token not in self.stop_words 
                   and len(token) > 2 
                   and token.isalpha()]
        
        keyword_freq = {}
        for keyword in keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, freq in sorted_keywords[:top_k]]
    
    def calculate_tfidf_similarity(self, resume_text: str, job_description: str) -> float:
        """Calculate similarity using TF-IDF approach."""
        try:
            resume_clean = self.preprocess_text(resume_text)
            job_clean = self.preprocess_text(job_description)
            
            if not resume_clean or not job_clean:
                return 0.0
            
            # Vectorize texts
            resume_vector = self.vectorizer.transform([resume_clean])
            job_vector = self.vectorizer.transform([job_clean])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(resume_vector, job_vector)[0][0]
            return float(similarity)
            
        except Exception as e:
            print(f"❌ Error in TF-IDF similarity calculation: {e}")
            return 0.0
    
    def calculate_huggingface_similarity(self, resume_text: str, job_description: str) -> float:
        """Calculate similarity using Hugging Face model."""
        if not self.hf_model:
            return 0.0
        
        try:
            resume_clean = self.preprocess_text(resume_text)
            job_clean = self.preprocess_text(job_description)
            
            if not resume_clean or not job_clean:
                return 0.0
            
            # Get embeddings
            resume_embedding = self.hf_model.encode([resume_clean])
            job_embedding = self.hf_model.encode([job_clean])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(resume_embedding, job_embedding)[0][0]
            return float(similarity)
            
        except Exception as e:
            print(f"❌ Error in Hugging Face similarity calculation: {e}")
            return 0.0
    
    def calculate_hybrid_similarity(self, resume_text: str, job_description: str) -> Dict[str, float]:
        """Calculate similarity using both approaches and combine them."""
        tfidf_sim = self.calculate_tfidf_similarity(resume_text, job_description)
        hf_sim = self.calculate_huggingface_similarity(resume_text, job_description) if self.use_huggingface else 0.0
        
        # Weighted combination (Hugging Face gets more weight if available)
        if self.use_huggingface and self.hf_model:
            # 70% Hugging Face, 30% TF-IDF
            combined_sim = (0.7 * hf_sim) + (0.3 * tfidf_sim)
            method = "hybrid_huggingface_tfidf"
        else:
            # Pure TF-IDF
            combined_sim = tfidf_sim
            method = "tfidf_only"
        
        return {
            'combined_similarity': combined_sim,
            'tfidf_similarity': tfidf_sim,
            'huggingface_similarity': hf_sim,
            'method': method
        }
    
    def find_missing_keywords(self, resume_text: str, job_description: str) -> List[str]:
        """Find keywords present in job description but missing from resume."""
        resume_keywords = set(self.extract_keywords(resume_text))
        job_keywords = set(self.extract_keywords(job_description))
        
        missing_keywords = job_keywords - resume_keywords
        return list(missing_keywords)[:10]
    
    def generate_suggestions(self, missing_keywords: List[str], ats_score: float) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        if ats_score < 30:
            suggestions.append("🔴 Critical: Resume needs significant improvement")
        elif ats_score < 50:
            suggestions.append("🟡 Moderate: Resume needs improvement")
        elif ats_score < 70:
            suggestions.append("🟢 Good: Resume is well-aligned but could improve")
        else:
            suggestions.append("✅ Excellent: Resume is very well-aligned")
        
        if missing_keywords:
            suggestions.append(f"📝 Add missing keywords: {', '.join(missing_keywords[:5])}")
        
        if ats_score < 60:
            suggestions.extend([
                "💡 Include more specific technical skills",
                "📊 Quantify achievements with numbers",
                "🎯 Tailor experience to job requirements"
            ])
        
        return suggestions
    
    def calculate_ats_score(self, resume_text: str, job_description: str) -> Dict[str, any]:
        """
        Calculate comprehensive ATS score using the best available method.
        
        Args:
            resume_text (str): Resume content
            job_description (str): Job description content
            
        Returns:
            Dict[str, any]: Comprehensive analysis results
        """
        try:
            # Calculate similarities
            similarity_results = self.calculate_hybrid_similarity(resume_text, job_description)
            ats_score = similarity_results['combined_similarity'] * 100
            
            # Extract keywords
            resume_keywords = self.extract_keywords(resume_text)
            job_keywords = self.extract_keywords(job_description)
            missing_keywords = self.find_missing_keywords(resume_text, job_description)
            
            # Calculate keyword coverage
            keyword_overlap = len(set(resume_keywords) & set(job_keywords))
            keyword_coverage = (keyword_overlap / len(job_keywords)) * 100 if job_keywords else 0
            
            # Generate suggestions
            suggestions = self.generate_suggestions(missing_keywords, ats_score)
            
            return {
                'ats_score': round(ats_score, 2),
                'similarity_score': round(similarity_results['combined_similarity'], 4),
                'tfidf_similarity': round(similarity_results['tfidf_similarity'], 4),
                'huggingface_similarity': round(similarity_results['huggingface_similarity'], 4),
                'keyword_coverage': round(keyword_coverage, 2),
                'resume_keywords': resume_keywords[:15],
                'job_keywords': job_keywords[:15],
                'missing_keywords': missing_keywords,
                'suggestions': suggestions,
                'model_method': similarity_results['method'],
                'huggingface_available': self.use_huggingface,
                'analysis_type': 'enhanced_hybrid'
            }
            
        except Exception as e:
            print(f"❌ Error calculating ATS score: {e}")
            return {
                'ats_score': 0.0,
                'similarity_score': 0.0,
                'tfidf_similarity': 0.0,
                'huggingface_similarity': 0.0,
                'keyword_coverage': 0.0,
                'resume_keywords': [],
                'job_keywords': [],
                'missing_keywords': [],
                'suggestions': ['Error in analysis. Please try again.'],
                'model_method': 'error',
                'huggingface_available': False,
                'analysis_type': 'enhanced_hybrid',
                'error': str(e)
            }


# For backward compatibility, create an alias
ATSResumeScorer = EnhancedATSResumeScorer
