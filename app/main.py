#!/usr/bin/env python3
"""
ATS Resume Analyzer - Main Entry Point

This script analyzes resumes against job descriptions and provides ATS scores
along with improvement suggestions.

Usage:
    python main.py <resume_file> <job_description_text>
    python main.py resume.pdf "Software Engineer with Python experience..."
"""

import sys
import os
from typing import Optional
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.parser import ResumeParser
from src.scorer import ATSResumeScorer


def print_banner():
    """Print the application banner."""
    print("=" * 60)
    print("🎯 ATS RESUME ANALYZER")
    print("=" * 60)
    print("Analyzing resumes against job descriptions for ATS optimization")
    print("=" * 60)


def print_results(analysis: dict):
    """
    Print the analysis results in a formatted way.
    
    Args:
        analysis (dict): Analysis results from ATSResumeScorer
    """
    print("\n📊 ANALYSIS RESULTS")
    print("-" * 40)
    
    # ATS Score
    score = analysis['ats_score']
    score_emoji = "🎉" if score >= 85 else "✅" if score >= 70 else "⚠️" if score >= 50 else "❌"
    print(f"{score_emoji} ATS Score: {score}/100")
    
    # Similarity Score
    print(f"📈 Similarity Score: {analysis['similarity_score']:.4f}")
    
    # Statistics
    print(f"📝 Resume Word Count: {analysis.get('resume_word_count', 'N/A')}")
    print(f"📄 Job Description Word Count: {analysis.get('job_description_word_count', 'N/A')}")
    print(f"🔗 Keyword Overlap: {analysis.get('keyword_overlap_count', 'N/A')} keywords")
    print(f"📊 Keyword Overlap Percentage: {analysis.get('keyword_overlap_percentage', 'N/A')}%")
    
    # Missing Keywords
    missing_keywords = analysis['missing_keywords']
    if missing_keywords:
        print(f"\n❌ Missing Keywords ({len(missing_keywords)}):")
        print("-" * 30)
        for i, keyword in enumerate(missing_keywords[:10], 1):  # Show top 10
            print(f"{i:2d}. {keyword}")
        if len(missing_keywords) > 10:
            print(f"    ... and {len(missing_keywords) - 10} more")
    else:
        print("\n✅ No missing keywords found!")
    
    # Resume Keywords
    resume_keywords = analysis['resume_keywords']
    if resume_keywords:
        print(f"\n✅ Resume Keywords ({len(resume_keywords)}):")
        print("-" * 30)
        for i, keyword in enumerate(resume_keywords[:10], 1):  # Show top 10
            print(f"{i:2d}. {keyword}")
        if len(resume_keywords) > 10:
            print(f"    ... and {len(resume_keywords) - 10} more")
    
    # Suggestions
    suggestions = analysis['suggestions']
    if suggestions:
        print(f"\n💡 IMPROVEMENT SUGGESTIONS")
        print("-" * 40)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")


def get_job_description_input() -> str:
    """
    Get job description from user input.
    
    Returns:
        str: Job description text
    """
    print("\n📝 Enter Job Description:")
    print("(Type your job description and press Enter twice when done)")
    print("-" * 50)
    
    lines = []
    empty_lines = 0
    
    while True:
        try:
            line = input()
            if line.strip() == "":
                empty_lines += 1
                if empty_lines >= 2:
                    break
            else:
                empty_lines = 0
                lines.append(line)
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            sys.exit(1)
    
    return '\n'.join(lines).strip()


def main():
    """Main function to run the ATS Resume Analyzer."""
    print_banner()
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("❌ Error: Resume file path is required!")
        print("\nUsage:")
        print("  python main.py <resume_file> [job_description_text]")
        print("\nExamples:")
        print("  python main.py resume.pdf")
        print('  python main.py resume.pdf "Software Engineer with Python experience..."')
        sys.exit(1)
    
    resume_file = sys.argv[1]
    
    # Check if resume file exists
    if not os.path.exists(resume_file):
        print(f"❌ Error: Resume file '{resume_file}' not found!")
        sys.exit(1)
    
    # Initialize components
    parser = ResumeParser()
    scorer = ATSResumeScorer()
    
    # Check file format
    if not parser.is_supported_format(resume_file):
        print(f"❌ Error: Unsupported file format!")
        print(f"Supported formats: {', '.join(parser.supported_formats)}")
        sys.exit(1)
    
    print(f"📄 Processing resume: {resume_file}")
    
    # Extract text from resume
    try:
        resume_text = parser.extract_text(resume_file)
        if not resume_text:
            print("❌ Error: Could not extract text from resume file!")
            sys.exit(1)
        
        print(f"✅ Successfully extracted {len(resume_text.split())} words from resume")
        
    except Exception as e:
        print(f"❌ Error extracting text from resume: {str(e)}")
        sys.exit(1)
    
    # Get job description
    if len(sys.argv) > 2:
        # Job description provided as command line argument
        job_description = ' '.join(sys.argv[2:])
        print(f"📝 Using job description from command line ({len(job_description.split())} words)")
    else:
        # Get job description from user input
        job_description = get_job_description_input()
        if not job_description:
            print("❌ Error: No job description provided!")
            sys.exit(1)
        print(f"📝 Using job description from input ({len(job_description.split())} words)")
    
    # Perform analysis
    print("\n🔍 Analyzing resume against job description...")
    try:
        analysis = scorer.get_detailed_analysis(resume_text, job_description)
        print_results(analysis)
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
