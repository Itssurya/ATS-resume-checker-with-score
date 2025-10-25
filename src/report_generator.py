"""
PDF Report Generator Module

This module generates detailed PDF reports for resume analysis results,
including ATS scores, recommendations, and improvement suggestions.
"""

import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend


class PDFReportGenerator:
    """PDF report generator for resume analysis results."""
    
    def __init__(self):
        """Initialize the PDF generator."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#34495e'),
            borderWidth=1,
            borderColor=colors.HexColor('#bdc3c7'),
            borderPadding=8,
            backColor=colors.HexColor('#ecf0f1')
        ))
        
        # Score style
        self.styles.add(ParagraphStyle(
            name='ScoreStyle',
            parent=self.styles['Normal'],
            fontSize=48,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#27ae60'),
            spaceAfter=20
        ))
        
        # Keyword style
        self.styles.add(ParagraphStyle(
            name='KeywordStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            leftIndent=20,
            spaceAfter=5,
            backColor=colors.HexColor('#f8f9fa'),
            borderWidth=1,
            borderColor=colors.HexColor('#dee2e6'),
            borderPadding=5
        ))
        
        # Recommendation style
        self.styles.add(ParagraphStyle(
            name='RecommendationStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=15,
            spaceAfter=8,
            bulletIndent=10,
            bulletText='•'
        ))
    
    def generate_report(self, analysis_data, user_info=None, filename=None):
        """
        Generate a comprehensive PDF report for resume analysis.
        
        Args:
            analysis_data (dict): Analysis results from ATSResumeScorer
            user_info (dict): User information (optional)
            filename (str): Output filename (optional)
            
        Returns:
            bytes: PDF content as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build content
        story = []
        
        # Add header
        story.extend(self._create_header(analysis_data, user_info))
        
        # Add executive summary
        story.extend(self._create_executive_summary(analysis_data))
        
        # Add ATS score section
        story.extend(self._create_ats_score_section(analysis_data))
        
        # Add keyword analysis
        story.extend(self._create_keyword_analysis(analysis_data))
        
        # Add recommendations
        story.extend(self._create_recommendations_section(analysis_data))
        
        # Add detailed analysis
        story.extend(self._create_detailed_analysis(analysis_data))
        
        # Add footer
        story.extend(self._create_footer())
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    def _create_header(self, analysis_data, user_info):
        """Create report header."""
        story = []
        
        # Title
        title = Paragraph("ATS Resume Analysis Report", self.styles['CustomTitle'])
        story.append(title)
        
        # Subtitle
        subtitle = Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            self.styles['Normal']
        )
        story.append(subtitle)
        
        if user_info:
            user_name = user_info.get('name', 'User')
            story.append(Spacer(1, 12))
            user_para = Paragraph(f"Prepared for: {user_name}", self.styles['Normal'])
            story.append(user_para)
        
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#3498db')))
        
        return story
    
    def _create_executive_summary(self, analysis_data):
        """Create executive summary section."""
        story = []
        
        # Section header
        header = Paragraph("Executive Summary", self.styles['SectionHeader'])
        story.append(header)
        
        # ATS Score summary
        ats_score = analysis_data.get('ats_score', 0)
        score_interpretation = self._get_score_interpretation(ats_score)
        
        summary_text = f"""
        Your resume achieved an ATS score of <b>{ats_score}/100</b>, which indicates 
        <b>{score_interpretation['level']}</b> compatibility with Applicant Tracking Systems. 
        {score_interpretation['description']}
        """
        
        summary = Paragraph(summary_text, self.styles['Normal'])
        story.append(summary)
        story.append(Spacer(1, 12))
        
        # Key metrics
        metrics_data = [
            ['Metric', 'Value'],
            ['ATS Score', f"{ats_score}/100"],
            ['Similarity Score', f"{analysis_data.get('similarity_score', 0):.3f}"],
            ['Missing Keywords', str(len(analysis_data.get('missing_keywords', [])))],
            ['Keyword Overlap', f"{analysis_data.get('keyword_overlap_percentage', 0):.1f}%"],
            ['Resume Word Count', str(analysis_data.get('resume_word_count', 0))],
            ['Job Description Word Count', str(analysis_data.get('job_description_word_count', 0))]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_ats_score_section(self, analysis_data):
        """Create ATS score visualization section."""
        story = []
        
        # Section header
        header = Paragraph("ATS Score Analysis", self.styles['SectionHeader'])
        story.append(header)
        
        # Score display
        ats_score = analysis_data.get('ats_score', 0)
        score_color = self._get_score_color(ats_score)
        
        score_text = f"<font color='{score_color}'>{ats_score}</font>"
        score_para = Paragraph(score_text, self.styles['ScoreStyle'])
        story.append(score_para)
        
        # Score interpretation
        interpretation = self._get_score_interpretation(ats_score)
        interpretation_text = f"""
        <b>Score Interpretation:</b> {interpretation['level']}<br/>
        {interpretation['description']}<br/>
        <b>Recommendation:</b> {interpretation['recommendation']}
        """
        
        interpretation_para = Paragraph(interpretation_text, self.styles['Normal'])
        story.append(interpretation_para)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_keyword_analysis(self, analysis_data):
        """Create keyword analysis section."""
        story = []
        
        # Section header
        header = Paragraph("Keyword Analysis", self.styles['SectionHeader'])
        story.append(header)
        
        # Missing keywords
        missing_keywords = analysis_data.get('missing_keywords', [])
        if missing_keywords:
            story.append(Paragraph("<b>Missing Keywords:</b>", self.styles['Normal']))
            story.append(Spacer(1, 8))
            
            # Group keywords in columns
            keywords_per_row = 3
            keyword_rows = []
            for i in range(0, len(missing_keywords), keywords_per_row):
                row_keywords = missing_keywords[i:i+keywords_per_row]
                # Pad with empty strings if needed
                while len(row_keywords) < keywords_per_row:
                    row_keywords.append("")
                keyword_rows.append(row_keywords)
            
            if keyword_rows:
                keywords_table = Table(keyword_rows, colWidths=[1.8*inch, 1.8*inch, 1.8*inch])
                keywords_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fdf2f2')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#fecaca'))
                ]))
                story.append(keywords_table)
        else:
            story.append(Paragraph("✅ No missing keywords found! Your resume includes all important terms.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Resume keywords
        resume_keywords = analysis_data.get('resume_keywords', [])
        if resume_keywords:
            story.append(Paragraph("<b>Resume Keywords Found:</b>", self.styles['Normal']))
            story.append(Spacer(1, 8))
            
            # Show top 15 keywords
            top_keywords = resume_keywords[:15]
            keyword_text = ", ".join(top_keywords)
            if len(resume_keywords) > 15:
                keyword_text += f" ... and {len(resume_keywords) - 15} more"
            
            keyword_para = Paragraph(keyword_text, self.styles['Normal'])
            story.append(keyword_para)
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_recommendations_section(self, analysis_data):
        """Create recommendations section."""
        story = []
        
        # Section header
        header = Paragraph("Improvement Recommendations", self.styles['SectionHeader'])
        story.append(header)
        
        # Get recommendations
        suggestions = analysis_data.get('suggestions', [])
        recommendations = analysis_data.get('recommendations', {})
        
        if suggestions:
            story.append(Paragraph("<b>Priority Actions:</b>", self.styles['Normal']))
            story.append(Spacer(1, 8))
            
            for i, suggestion in enumerate(suggestions[:10], 1):  # Limit to top 10
                suggestion_text = f"{i}. {suggestion}"
                suggestion_para = Paragraph(suggestion_text, self.styles['RecommendationStyle'])
                story.append(suggestion_para)
        
        # Additional recommendations from recommender
        if recommendations:
            priority_recs = recommendations.get('keywords', {}).get('recommendations', [])
            if priority_recs:
                story.append(Spacer(1, 12))
                story.append(Paragraph("<b>Keyword Optimization:</b>", self.styles['Normal']))
                story.append(Spacer(1, 8))
                
                for rec in priority_recs[:5]:  # Limit to top 5
                    rec_para = Paragraph(f"• {rec}", self.styles['RecommendationStyle'])
                    story.append(rec_para)
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_detailed_analysis(self, analysis_data):
        """Create detailed analysis section."""
        story = []
        
        # Section header
        header = Paragraph("Detailed Analysis", self.styles['SectionHeader'])
        story.append(header)
        
        # Text statistics
        story.append(Paragraph("<b>Text Statistics:</b>", self.styles['Normal']))
        story.append(Spacer(1, 8))
        
        stats_data = [
            ['Resume Word Count', str(analysis_data.get('resume_word_count', 0))],
            ['Job Description Word Count', str(analysis_data.get('job_description_word_count', 0))],
            ['Keyword Overlap Count', str(analysis_data.get('keyword_overlap_count', 0))],
            ['Keyword Overlap Percentage', f"{analysis_data.get('keyword_overlap_percentage', 0):.1f}%"],
            ['Missing Keyword Count', str(analysis_data.get('missing_keyword_count', 0))]
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_footer(self):
        """Create report footer."""
        story = []
        
        story.append(PageBreak())
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#bdc3c7')))
        story.append(Spacer(1, 12))
        
        footer_text = """
        <b>About This Report</b><br/>
        This ATS Resume Analysis Report was generated using advanced natural language processing 
        and machine learning algorithms to evaluate your resume's compatibility with Applicant 
        Tracking Systems (ATS).<br/><br/>
        
        <b>Methodology:</b> The analysis uses TF-IDF (Term Frequency-Inverse Document Frequency) 
        vectorization to compare your resume against the job description, calculating similarity 
        scores and identifying missing keywords.<br/><br/>
        
        <b>Disclaimer:</b> This analysis is for informational purposes only and should be used 
        as a guide to improve your resume. Results may vary based on specific ATS systems and 
        job requirements.
        """
        
        footer = Paragraph(footer_text, self.styles['Normal'])
        story.append(footer)
        
        return story
    
    def _add_page_number(self, canvas, doc):
        """Add page numbers to PDF."""
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(200*mm, 20*mm, text)
        canvas.restoreState()
    
    def _get_score_interpretation(self, score):
        """Get score interpretation based on ATS score."""
        if score >= 85:
            return {
                'level': 'Excellent',
                'description': 'Your resume is well-optimized for ATS systems and should pass most screening processes.',
                'recommendation': 'Maintain current optimization level and focus on interview preparation.'
            }
        elif score >= 70:
            return {
                'level': 'Good',
                'description': 'Your resume shows good ATS compatibility with room for minor improvements.',
                'recommendation': 'Make small adjustments to keywords and formatting for better results.'
            }
        elif score >= 50:
            return {
                'level': 'Moderate',
                'description': 'Your resume has moderate ATS compatibility but needs significant improvements.',
                'recommendation': 'Focus on adding missing keywords and improving content structure.'
            }
        elif score >= 30:
            return {
                'level': 'Low',
                'description': 'Your resume has low ATS compatibility and requires substantial improvements.',
                'recommendation': 'Consider rewriting key sections and adding more relevant keywords.'
            }
        else:
            return {
                'level': 'Very Low',
                'description': 'Your resume has very low ATS compatibility and may not pass initial screening.',
                'recommendation': 'Consider a complete resume rewrite with ATS optimization in mind.'
            }
    
    def _get_score_color(self, score):
        """Get color for score display."""
        if score >= 85:
            return '#27ae60'  # Green
        elif score >= 70:
            return '#f39c12'  # Orange
        elif score >= 50:
            return '#e67e22'  # Dark orange
        elif score >= 30:
            return '#e74c3c'  # Red
        else:
            return '#c0392b'  # Dark red




