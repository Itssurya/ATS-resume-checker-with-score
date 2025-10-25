"""
Resume Recommendation Engine

This module provides intelligent recommendations for resume improvement
based on ATS analysis results and best practices.
"""

from typing import List, Dict, Any, Tuple
import re
from .utils import TextProcessor


class ResumeRecommender:
    """
    A class to generate intelligent recommendations for resume improvement.
    
    Features:
    - Keyword optimization suggestions
    - Format and structure recommendations
    - ATS-specific improvements
    - Industry-specific advice
    """
    
    def __init__(self):
        """Initialize the ResumeRecommender."""
        self.text_processor = TextProcessor()
        
        # Common ATS-friendly keywords by category
        self.keyword_categories = {
            'action_verbs': [
                'achieved', 'developed', 'implemented', 'managed', 'led',
                'created', 'designed', 'optimized', 'improved', 'increased',
                'reduced', 'solved', 'delivered', 'executed', 'coordinated',
                'collaborated', 'analyzed', 'researched', 'innovated', 'transformed'
            ],
            'technical_skills': [
                'programming', 'software development', 'database management',
                'cloud computing', 'machine learning', 'data analysis',
                'web development', 'mobile development', 'devops', 'agile',
                'scrum', 'version control', 'api development', 'microservices'
            ],
            'soft_skills': [
                'leadership', 'communication', 'problem solving', 'teamwork',
                'project management', 'time management', 'adaptability',
                'critical thinking', 'creativity', 'attention to detail'
            ],
            'quantifiers': [
                'increased by', 'reduced by', 'improved by', 'achieved',
                'managed', 'led team of', 'budget of', 'revenue of',
                'saved', 'generated', 'delivered', 'completed'
            ]
        }
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive recommendations based on analysis results.
        
        Args:
            analysis (Dict[str, Any]): Analysis results from ATSResumeScorer
            
        Returns:
            Dict[str, Any]: Comprehensive recommendations
        """
        recommendations = {
            'priority': 'high',  # high, medium, low
            'sections': {},
            'keywords': {},
            'format': {},
            'content': {},
            'ats_optimization': {},
            'overall_score': 0
        }
        
        ats_score = analysis.get('ats_score', 0)
        missing_keywords = analysis.get('missing_keywords', [])
        resume_keywords = analysis.get('resume_keywords', [])
        
        # Determine priority level
        recommendations['priority'] = self._determine_priority(ats_score)
        
        # Generate section-specific recommendations
        recommendations['sections'] = self._analyze_sections(analysis)
        
        # Generate keyword recommendations
        recommendations['keywords'] = self._analyze_keywords(missing_keywords, resume_keywords)
        
        # Generate format recommendations
        recommendations['format'] = self._analyze_format(analysis)
        
        # Generate content recommendations
        recommendations['content'] = self._analyze_content(analysis)
        
        # Generate ATS-specific recommendations
        recommendations['ats_optimization'] = self._analyze_ats_optimization(analysis)
        
        # Calculate overall recommendation score
        recommendations['overall_score'] = self._calculate_recommendation_score(recommendations)
        
        return recommendations
    
    def _determine_priority(self, ats_score: float) -> str:
        """Determine priority level based on ATS score."""
        if ats_score < 30:
            return 'high'
        elif ats_score < 60:
            return 'medium'
        else:
            return 'low'
    
    def _analyze_sections(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resume sections and provide recommendations."""
        sections = {
            'summary': {
                'present': False,
                'recommendations': []
            },
            'experience': {
                'present': False,
                'recommendations': []
            },
            'skills': {
                'present': False,
                'recommendations': []
            },
            'education': {
                'present': False,
                'recommendations': []
            }
        }
        
        # Basic section analysis (would need more sophisticated parsing in real implementation)
        resume_text = analysis.get('resume_text', '').lower()
        
        # Check for common section headers
        if any(word in resume_text for word in ['summary', 'objective', 'profile']):
            sections['summary']['present'] = True
        else:
            sections['summary']['recommendations'].append("Add a professional summary section")
        
        if any(word in resume_text for word in ['experience', 'employment', 'work history']):
            sections['experience']['present'] = True
        else:
            sections['experience']['recommendations'].append("Add work experience section")
        
        if any(word in resume_text for word in ['skills', 'technical skills', 'competencies']):
            sections['skills']['present'] = True
        else:
            sections['skills']['recommendations'].append("Add skills section")
        
        if any(word in resume_text for word in ['education', 'academic', 'degree']):
            sections['education']['present'] = True
        else:
            sections['education']['recommendations'].append("Add education section")
        
        return sections
    
    def _analyze_keywords(self, missing_keywords: List[str], resume_keywords: List[str]) -> Dict[str, Any]:
        """Analyze keywords and provide optimization suggestions."""
        keyword_analysis = {
            'missing_count': len(missing_keywords),
            'present_count': len(resume_keywords),
            'recommendations': [],
            'suggested_additions': [],
            'optimization_tips': []
        }
        
        # Categorize missing keywords
        missing_by_category = self._categorize_keywords(missing_keywords)
        
        # Generate recommendations based on missing categories
        for category, keywords in missing_by_category.items():
            if keywords:
                keyword_analysis['recommendations'].append(
                    f"Add {category} keywords: {', '.join(keywords[:3])}"
                )
                keyword_analysis['suggested_additions'].extend(keywords[:5])
        
        # General keyword optimization tips
        if len(resume_keywords) < 10:
            keyword_analysis['optimization_tips'].append(
                "Increase keyword density by including more relevant technical terms"
            )
        
        if len(missing_keywords) > 10:
            keyword_analysis['optimization_tips'].append(
                "Focus on adding the most important missing keywords first"
            )
        
        return keyword_analysis
    
    def _categorize_keywords(self, keywords: List[str]) -> Dict[str, List[str]]:
        """Categorize keywords by type."""
        categorized = {
            'technical': [],
            'action_verbs': [],
            'soft_skills': [],
            'quantifiers': [],
            'other': []
        }
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            categorized_flag = False
            
            for category, category_keywords in self.keyword_categories.items():
                if any(cat_kw in keyword_lower for cat_kw in category_keywords):
                    categorized[category].append(keyword)
                    categorized_flag = True
                    break
            
            if not categorized_flag:
                categorized['other'].append(keyword)
        
        return categorized
    
    def _analyze_format(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resume format and provide recommendations."""
        format_analysis = {
            'recommendations': [],
            'warnings': [],
            'tips': []
        }
        
        resume_text = analysis.get('resume_text', '')
        word_count = analysis.get('resume_word_count', 0)
        
        # Check resume length
        if word_count < 200:
            format_analysis['warnings'].append("Resume is too short - consider adding more detail")
        elif word_count > 800:
            format_analysis['warnings'].append("Resume is too long - consider condensing content")
        
        # Check for common formatting issues
        if '  ' in resume_text:  # Double spaces
            format_analysis['tips'].append("Remove extra spaces for better ATS parsing")
        
        if '\t' in resume_text:  # Tabs
            format_analysis['tips'].append("Replace tabs with spaces for better ATS compatibility")
        
        # General format recommendations
        format_analysis['recommendations'].extend([
            "Use standard section headers (Experience, Education, Skills)",
            "Use bullet points for easy scanning",
            "Keep formatting simple and consistent",
            "Use standard fonts (Arial, Calibri, Times New Roman)"
        ])
        
        return format_analysis
    
    def _analyze_content(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resume content and provide recommendations."""
        content_analysis = {
            'recommendations': [],
            'strengths': [],
            'improvements': []
        }
        
        ats_score = analysis.get('ats_score', 0)
        missing_keywords = analysis.get('missing_keywords', [])
        
        # Content recommendations based on ATS score
        if ats_score < 50:
            content_analysis['improvements'].extend([
                "Rewrite job descriptions to match the target role",
                "Include specific technologies and tools mentioned in the job posting",
                "Quantify achievements with numbers and metrics"
            ])
        elif ats_score < 70:
            content_analysis['improvements'].extend([
                "Fine-tune keyword usage to better match job requirements",
                "Add more specific technical details",
                "Include more quantifiable achievements"
            ])
        else:
            content_analysis['strengths'].append("Good keyword alignment with job requirements")
        
        # General content recommendations
        content_analysis['recommendations'].extend([
            "Use action verbs to start bullet points",
            "Include specific technologies and tools",
            "Quantify achievements with numbers",
            "Tailor content to the specific job posting",
            "Use industry-specific terminology"
        ])
        
        return content_analysis
    
    def _analyze_ats_optimization(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ATS-specific optimization opportunities."""
        ats_analysis = {
            'recommendations': [],
            'critical_issues': [],
            'optimization_tips': []
        }
        
        resume_text = analysis.get('resume_text', '')
        
        # Check for ATS-unfriendly elements
        if any(char in resume_text for char in ['\t', '  ']):
            ats_analysis['critical_issues'].append("Remove tabs and extra spaces")
        
        if re.search(r'[^\x00-\x7F]', resume_text):  # Non-ASCII characters
            ats_analysis['critical_issues'].append("Remove special characters and symbols")
        
        # ATS optimization recommendations
        ats_analysis['recommendations'].extend([
            "Use standard section headers",
            "Avoid tables and complex formatting",
            "Use simple bullet points",
            "Include relevant keywords naturally",
            "Save as PDF for best compatibility"
        ])
        
        # Optimization tips
        ats_analysis['optimization_tips'].extend([
            "Test your resume with ATS checkers",
            "Use keywords from the job description",
            "Keep formatting simple and clean",
            "Use standard fonts and sizes",
            "Avoid graphics and images"
        ])
        
        return ats_analysis
    
    def _calculate_recommendation_score(self, recommendations: Dict[str, Any]) -> int:
        """Calculate overall recommendation score (0-100)."""
        score = 100
        
        # Deduct points for issues
        if recommendations['priority'] == 'high':
            score -= 30
        elif recommendations['priority'] == 'medium':
            score -= 15
        
        # Deduct for missing sections
        sections = recommendations['sections']
        missing_sections = sum(1 for section in sections.values() if not section['present'])
        score -= missing_sections * 10
        
        # Deduct for keyword issues
        keywords = recommendations['keywords']
        if keywords['missing_count'] > 10:
            score -= 20
        elif keywords['missing_count'] > 5:
            score -= 10
        
        return max(0, min(100, score))
    
    def get_priority_recommendations(self, recommendations: Dict[str, Any], limit: int = 5) -> List[str]:
        """
        Get top priority recommendations.
        
        Args:
            recommendations (Dict[str, Any]): Full recommendations
            limit (int): Maximum number of recommendations to return
            
        Returns:
            List[str]: Top priority recommendations
        """
        priority_recs = []
        
        # Add critical issues first
        ats_issues = recommendations.get('ats_optimization', {}).get('critical_issues', [])
        priority_recs.extend(ats_issues[:limit])
        
        # Add section recommendations
        sections = recommendations.get('sections', {})
        for section_name, section_data in sections.items():
            if not section_data['present'] and len(priority_recs) < limit:
                priority_recs.append(f"Add {section_name} section")
        
        # Add keyword recommendations
        keyword_recs = recommendations.get('keywords', {}).get('recommendations', [])
        priority_recs.extend(keyword_recs[:limit - len(priority_recs)])
        
        return priority_recs[:limit]



