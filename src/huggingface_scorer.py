"""
Enhanced ATS Resume Scorer with Hugging Face Models

This module provides advanced resume analysis using Hugging Face transformers
for better semantic understanding and more accurate ATS scoring.
"""

import re
import numpy as np
from typing import List, Dict, Tuple, Set
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
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


class HuggingFaceATSResumeScorer:
    """
    Advanced ATS Resume Scorer using Hugging Face models.
    
    Features:
    - Semantic similarity using transformer models
    - Enhanced keyword extraction
    - Better context understanding
    - Improved ATS scoring accuracy
    """
    
    def __init__(self, model_name: str = "anass1209/resume-job-matcher-all-MiniLM-L6-v2"):
        """
        Initialize the HuggingFaceATSResumeScorer.
        
        Args:
            model_name (str): Hugging Face model name for resume analysis
        """
        self.model_name = model_name
        self.stop_words = set(stopwords.words('english'))
        
        print(f"🔄 Loading Hugging Face model: {model_name}")
        try:
            # Load the sentence transformer model
            self.model = SentenceTransformer(model_name)
            print(f"✅ Successfully loaded model: {model_name}")
        except Exception as e:
            print(f"❌ Failed to load {model_name}: {e}")
            print("🔄 Falling back to general-purpose model...")
            # Fallback to general-purpose model
            self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            print("✅ Loaded fallback model: all-MiniLM-L6-v2")
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text by cleaning and normalizing.
        
        Args:
            text (str): Raw text to preprocess
            
        Returns:
            str: Preprocessed text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces and alphanumeric
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_keywords(self, text: str, top_k: int = 20) -> List[str]:
        """
        Extract important keywords from text.
        
        Args:
            text (str): Input text
            top_k (int): Number of top keywords to return
            
        Returns:
            List[str]: List of important keywords
        """
        if not text:
            return []
        
        # Tokenize and filter
        tokens = word_tokenize(text.lower())
        keywords = [token for token in tokens 
                   if token not in self.stop_words 
                   and len(token) > 2 
                   and token.isalpha()]
        
        # Count frequency
        keyword_freq = {}
        for keyword in keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, freq in sorted_keywords[:top_k]]
    
    def calculate_semantic_similarity(self, resume_text: str, job_description: str) -> float:
        """
        Calculate semantic similarity between resume and job description using Hugging Face model.
        
        Args:
            resume_text (str): Resume content
            job_description (str): Job description content
            
        Returns:
            float: Similarity score between 0 and 1
        """
        try:
            # Preprocess texts
            resume_clean = self.preprocess_text(resume_text)
            job_clean = self.preprocess_text(job_description)
            
            if not resume_clean or not job_clean:
                return 0.0
            
            # Get embeddings using the Hugging Face model
            resume_embedding = self.model.encode([resume_clean])
            job_embedding = self.model.encode([job_clean])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(resume_embedding, job_embedding)[0][0]
            
            return float(similarity)
            
        except Exception as e:
            print(f"❌ Error calculating semantic similarity: {e}")
            return 0.0
    
    def find_missing_keywords(self, resume_text: str, job_description: str) -> List[str]:
        """
        Find keywords present in job description but missing from resume.
        
        Args:
            resume_text (str): Resume content
            job_description (str): Job description content
            
        Returns:
            List[str]: List of missing keywords
        """
        resume_keywords = set(self.extract_keywords(resume_text))
        job_keywords = set(self.extract_keywords(job_description))
        
        missing_keywords = job_keywords - resume_keywords
        return list(missing_keywords)[:10]  # Return top 10 missing keywords
    
    def calculate_ats_score(self, resume_text: str, job_description: str) -> Dict[str, any]:
        """
        Calculate comprehensive ATS score using Hugging Face model.
        
        Args:
            resume_text (str): Resume content
            job_description (str): Job description content
            
        Returns:
            Dict[str, any]: Comprehensive analysis results
        """
        try:
            # Calculate semantic similarity (main ATS score)
            semantic_similarity = self.calculate_semantic_similarity(resume_text, job_description)
            ats_score = semantic_similarity * 100  # Convert to 0-100 scale
            
            # Extract keywords
            resume_keywords = self.extract_keywords(resume_text)
            job_keywords = self.extract_keywords(job_description)
            missing_keywords = self.find_missing_keywords(resume_text, job_description)
            
            # Calculate keyword overlap
            keyword_overlap = len(set(resume_keywords) & set(job_keywords))
            keyword_coverage = (keyword_overlap / len(job_keywords)) * 100 if job_keywords else 0
            
            # Generate improvement suggestions
            suggestions = self.generate_suggestions(missing_keywords, ats_score)
            
            return {
                'ats_score': round(ats_score, 2),
                'semantic_similarity': round(semantic_similarity, 4),
                'keyword_coverage': round(keyword_coverage, 2),
                'resume_keywords': resume_keywords[:15],  # Top 15 keywords
                'job_keywords': job_keywords[:15],
                'missing_keywords': missing_keywords,
                'suggestions': suggestions,
                'model_used': self.model_name,
                'analysis_type': 'huggingface_semantic'
            }
            
        except Exception as e:
            print(f"❌ Error calculating ATS score: {e}")
            return {
                'ats_score': 0.0,
                'semantic_similarity': 0.0,
                'keyword_coverage': 0.0,
                'resume_keywords': [],
                'job_keywords': [],
                'missing_keywords': [],
                'suggestions': ['Error in analysis. Please try again.'],
                'model_used': self.model_name,
                'analysis_type': 'huggingface_semantic',
                'error': str(e)
            }
    
    def generate_suggestions(self, missing_keywords: List[str], ats_score: float) -> List[str]:
        """
        Generate improvement suggestions based on missing keywords and ATS score.
        
        Args:
            missing_keywords (List[str]): Missing keywords from resume
            ats_score (float): Current ATS score
            
        Returns:
            List[str]: List of improvement suggestions
        """
        suggestions = []
        
        if ats_score < 30:
            suggestions.append("🔴 Critical: Resume needs significant improvement to match job requirements")
        elif ats_score < 50:
            suggestions.append("🟡 Moderate: Resume needs improvement to better align with job requirements")
        elif ats_score < 70:
            suggestions.append("🟢 Good: Resume is well-aligned but could be improved further")
        else:
            suggestions.append("✅ Excellent: Resume is very well-aligned with job requirements")
        
        if missing_keywords:
            suggestions.append(f"📝 Add these missing keywords: {', '.join(missing_keywords[:5])}")
        
        if ats_score < 60:
            suggestions.extend([
                "💡 Include more specific technical skills mentioned in the job description",
                "📊 Quantify your achievements with numbers and metrics",
                "🎯 Tailor your experience to match the job requirements more closely"
            ])
        
        return suggestions


# Example usage and testing
if __name__ == "__main__":
    # Test the Hugging Face scorer
    scorer = HuggingFaceATSResumeScorer()
    
    # Sample resume and job description
    sample_resume = """
    John Doe
    Software Engineer with 5 years of experience in Python, JavaScript, and React.
    Worked on web applications using Django and Node.js.
    Experience with AWS cloud services and database design.
    Strong problem-solving skills and team collaboration.
    """
    
    sample_job = """
    We are looking for a Senior Software Engineer with experience in:
    - Python, JavaScript, React, Node.js
    - AWS cloud services
    - Database design and optimization
    - Agile development methodologies
    - Team leadership and mentoring
    """
    
    # Calculate ATS score
    result = scorer.calculate_ats_score(sample_resume, sample_job)
    
    print("🎯 Hugging Face ATS Analysis Results:")
    print(f"ATS Score: {result['ats_score']}/100")
    print(f"Semantic Similarity: {result['semantic_similarity']}")
    print(f"Keyword Coverage: {result['keyword_coverage']}%")
    print(f"Missing Keywords: {result['missing_keywords']}")
    print(f"Model Used: {result['model_used']}")
    print("\n💡 Suggestions:")
    for suggestion in result['suggestions']:
        print(f"  {suggestion}")

