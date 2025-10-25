"""
ATS Resume Analyzer - Core Source Package

This package contains the core functionality for resume analysis and ATS scoring.
"""

from .parser import ResumeParser
from .scorer import ATSResumeScorer
from .recommender import ResumeRecommender
from .utils import TextProcessor, FileHandler

__version__ = "1.0.0"
__author__ = "ATS Resume Analyzer Team"

__all__ = [
    "ResumeParser",
    "ATSResumeScorer", 
    "ResumeRecommender",
    "TextProcessor",
    "FileHandler"
]



