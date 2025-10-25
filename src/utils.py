"""
Utility functions for the ATS Resume Analyzer

This module contains helper functions for text processing, file handling,
and other common utilities used throughout the application.
"""

import os
import re
import json
from typing import List, Dict, Any, Optional, Union
from pathlib import Path


class TextProcessor:
    """Utility class for text processing operations."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text by removing extra whitespace and special characters.
        
        Args:
            text (str): Raw text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep alphanumeric and basic punctuation
        text = re.sub(r'[^\w\s.,!?;:-]', ' ', text)
        
        # Remove extra spaces again
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """
        Extract email addresses from text.
        
        Args:
            text (str): Text to search for emails
            
        Returns:
            List[str]: List of found email addresses
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """
        Extract phone numbers from text.
        
        Args:
            text (str): Text to search for phone numbers
            
        Returns:
            List[str]: List of found phone numbers
        """
        phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        return re.findall(phone_pattern, text)
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """
        Extract URLs from text.
        
        Args:
            text (str): Text to search for URLs
            
        Returns:
            List[str]: List of found URLs
        """
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
    
    @staticmethod
    def word_count(text: str) -> int:
        """
        Count words in text.
        
        Args:
            text (str): Text to count words in
            
        Returns:
            int: Number of words
        """
        if not text:
            return 0
        return len(text.split())
    
    @staticmethod
    def sentence_count(text: str) -> int:
        """
        Count sentences in text.
        
        Args:
            text (str): Text to count sentences in
            
        Returns:
            int: Number of sentences
        """
        if not text:
            return 0
        # Simple sentence counting based on punctuation
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])


class FileHandler:
    """Utility class for file operations."""
    
    @staticmethod
    def ensure_directory(path: str) -> None:
        """
        Ensure directory exists, create if it doesn't.
        
        Args:
            path (str): Directory path to ensure exists
        """
        Path(path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """
        Get file extension from file path.
        
        Args:
            file_path (str): Path to file
            
        Returns:
            str: File extension (with dot)
        """
        return os.path.splitext(file_path)[1].lower()
    
    @staticmethod
    def is_valid_file(file_path: str, allowed_extensions: List[str]) -> bool:
        """
        Check if file has valid extension.
        
        Args:
            file_path (str): Path to file
            allowed_extensions (List[str]): List of allowed extensions
            
        Returns:
            bool: True if file has valid extension
        """
        if not os.path.exists(file_path):
            return False
        
        extension = FileHandler.get_file_extension(file_path)
        return extension in allowed_extensions
    
    @staticmethod
    def save_json(data: Dict[Any, Any], file_path: str) -> bool:
        """
        Save data to JSON file.
        
        Args:
            data (Dict[Any, Any]): Data to save
            file_path (str): Path to save file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving JSON file: {e}")
            return False
    
    @staticmethod
    def load_json(file_path: str) -> Optional[Dict[Any, Any]]:
        """
        Load data from JSON file.
        
        Args:
            file_path (str): Path to JSON file
            
        Returns:
            Optional[Dict[Any, Any]]: Loaded data or None if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return None
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        Get file size in bytes.
        
        Args:
            file_path (str): Path to file
            
        Returns:
            int: File size in bytes
        """
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0


class Config:
    """Configuration class for application settings."""
    
    # File processing settings
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    SUPPORTED_FORMATS = ['.pdf', '.docx', '.txt']
    
    # Text processing settings
    MAX_TEXT_LENGTH = 100000  # 100k characters
    MIN_TEXT_LENGTH = 50  # 50 characters
    
    # Scoring settings
    MIN_ATS_SCORE = 0
    MAX_ATS_SCORE = 100
    
    # Keyword settings
    MAX_KEYWORDS = 50
    MIN_KEYWORD_LENGTH = 2
    
    # Model settings
    TFIDF_MAX_FEATURES = 1000
    TFIDF_NGRAM_RANGE = (1, 2)
    
    @classmethod
    def validate_file(cls, file_path: str) -> Dict[str, Any]:
        """
        Validate file for processing.
        
        Args:
            file_path (str): Path to file to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check if file exists
        if not os.path.exists(file_path):
            result['valid'] = False
            result['errors'].append("File does not exist")
            return result
        
        # Check file extension
        if not FileHandler.is_valid_file(file_path, cls.SUPPORTED_FORMATS):
            result['valid'] = False
            result['errors'].append(f"Unsupported file format. Supported: {cls.SUPPORTED_FORMATS}")
            return result
        
        # Check file size
        file_size = FileHandler.get_file_size(file_path)
        if file_size > cls.MAX_FILE_SIZE:
            result['valid'] = False
            result['errors'].append(f"File too large. Max size: {cls.MAX_FILE_SIZE / (1024*1024):.1f}MB")
        
        if file_size == 0:
            result['valid'] = False
            result['errors'].append("File is empty")
        
        return result



