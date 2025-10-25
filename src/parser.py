"""
Resume Parser Module

This module handles text extraction from PDF and DOCX resume files.
Supports both PDF (using pdfplumber) and DOCX (using python-docx) formats.
"""

import os
from typing import Optional
import pdfplumber
from docx import Document


class ResumeParser:
    """
    A class to parse resume files and extract text content.
    
    Supports:
    - PDF files using pdfplumber
    - DOCX files using python-docx
    """
    
    def __init__(self):
        """Initialize the ResumeParser."""
        self.supported_formats = ['.pdf', '.docx']
    
    def extract_text(self, file_path: str) -> Optional[str]:
        """
        Extract text from a resume file.
        
        Args:
            file_path (str): Path to the resume file
            
        Returns:
            Optional[str]: Extracted text content or None if extraction fails
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}. "
                           f"Supported formats: {', '.join(self.supported_formats)}")
        
        try:
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension == '.docx':
                return self._extract_from_docx(file_path)
        except Exception as e:
            print(f"Error extracting text from {file_path}: {str(e)}")
            return None
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file using pdfplumber.
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            str: Extracted text content
        """
        text_content = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
        
        return '\n'.join(text_content)
    
    def _extract_from_docx(self, file_path: str) -> str:
        """
        Extract text from DOCX file using python-docx.
        
        Args:
            file_path (str): Path to the DOCX file
            
        Returns:
            str: Extracted text content
        """
        doc = Document(file_path)
        text_content = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content.append(paragraph.text)
        
        return '\n'.join(text_content)
    
    def is_supported_format(self, file_path: str) -> bool:
        """
        Check if the file format is supported.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            bool: True if format is supported, False otherwise
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        return file_extension in self.supported_formats
