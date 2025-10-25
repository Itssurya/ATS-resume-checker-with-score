#!/usr/bin/env python3
"""
Example usage of the ATS Resume Analyzer

This script demonstrates how to use the ATSResumeScorer and ResumeParser
classes programmatically.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.parser import ResumeParser
from src.scorer import ATSResumeScorer


def example_usage():
    """Demonstrate basic usage of the ATS Resume Analyzer."""
    
    # Sample resume text (in real usage, this would come from a file)
    sample_resume = """
    John Doe
    Software Engineer
    
    EXPERIENCE:
    - 3 years of Python development experience
    - Built web applications using Django and Flask
    - Database management with PostgreSQL and MySQL
    - API development and integration
    - Version control with Git
    
    SKILLS:
    - Python, JavaScript, HTML, CSS
    - Django, Flask, React
    - PostgreSQL, MySQL
    - Git, Docker
    - RESTful API development
    """
    
    # Sample job description
    sample_job_description = """
    We are looking for a Software Engineer with:
    - 3+ years of Python programming experience
    - Experience with Django and Flask frameworks
    - Database experience with PostgreSQL
    - API development skills
    - Machine learning knowledge preferred
    - Cloud computing experience (AWS/Azure)
    - Strong problem-solving abilities
    """
    
    print("🎯 ATS Resume Analyzer - Example Usage")
    print("=" * 50)
    
    # Initialize components
    parser = ResumeParser()
    scorer = ATSResumeScorer()
    
    # Perform analysis
    print("📊 Analyzing sample resume against job description...")
    analysis = scorer.get_detailed_analysis(sample_resume, sample_job_description)
    
    # Display results
    print(f"\n✅ ATS Score: {analysis['ats_score']}/100")
    print(f"📈 Similarity Score: {analysis['similarity_score']:.4f}")
    print(f"🔗 Keyword Overlap: {analysis.get('keyword_overlap_count', 'N/A')} keywords")
    print(f"📊 Overlap Percentage: {analysis.get('keyword_overlap_percentage', 'N/A')}%")
    
    print(f"\n❌ Missing Keywords ({len(analysis['missing_keywords'])}):")
    for i, keyword in enumerate(analysis['missing_keywords'][:5], 1):
        print(f"  {i}. {keyword}")
    
    print(f"\n💡 Suggestions:")
    for i, suggestion in enumerate(analysis['suggestions'][:3], 1):
        print(f"  {i}. {suggestion}")


if __name__ == "__main__":
    example_usage()
