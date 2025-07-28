"""
PDF utility functions for Round 1A outline extraction.
Contains heading detection and hierarchy analysis logic.
"""

import sys
import os
import re
from typing import List, Dict, Tuple, Any
import logging

from shared.text_extractor import PDFTextExtractor, TextBlock


logger = logging.getLogger(__name__)

class HeadingDetector:
    """Detects and classifies headings from PDF text blocks."""
    
    def __init__(self):
        self.extractor = PDFTextExtractor()
        
    def detect_headings(self, pdf_path: str, exclude_title: str = None) -> List[Dict[str, Any]]:
        """
        Detect headings from a PDF file and classify them into H1, H2, H3.
        
        Args:
            pdf_path: Path to the PDF file
            exclude_title: Title text to exclude from headings
            
        Returns:
            List of heading dictionaries with level, text, and page
        """
        if not self.extractor.load_pdf(pdf_path):
            return []
            
        try:
            # Extract all text blocks
            text_blocks = self.extractor.extract_text_blocks()
            if not text_blocks:
                return []
                
            # Calculate statistics for heading detection
            avg_font_size = self.extractor.calculate_average_font_size(text_blocks)
            
            # Find potential headings
            potential_headings = []
            for block in text_blocks:
                if self.extractor.is_likely_heading(block, avg_font_size):
                    # Exclude the document title from headings
                    if exclude_title and block.text.strip() == exclude_title.strip():
                        continue
                    potential_headings.append(block)
                    
            # Sort by page and position
            potential_headings.sort(key=lambda x: (x.page_num, x.bbox[1]))
            
            # Classify heading levels
            classified_headings = self._classify_heading_levels(potential_headings, avg_font_size)
            
            return classified_headings
            
        finally:
            self.extractor.close()
            
    def _classify_heading_levels(self, headings: List[TextBlock], avg_font_size: float) -> List[Dict[str, Any]]:
        """
        Classify headings into H1, H2, H3 levels based on font size and hierarchy.
        
        Args:
            headings: List of potential heading text blocks
            avg_font_size: Average font size of the document
            
        Returns:
            List of classified headings
        """
        if not headings:
            return []
            
        # Group headings by font size
        font_sizes = sorted(set(h.font_size for h in headings), reverse=True)
        
        # Create font size to level mapping
        level_mapping = {}
        if len(font_sizes) >= 3:
            # Use top 3 font sizes for H1, H2, H3
            level_mapping[font_sizes[0]] = "H1"
            level_mapping[font_sizes[1]] = "H2" 
            level_mapping[font_sizes[2]] = "H3"
        elif len(font_sizes) == 2:
            level_mapping[font_sizes[0]] = "H1"
            level_mapping[font_sizes[1]] = "H2"
        else:
            level_mapping[font_sizes[0]] = "H1"
            
        classified = []
        for heading in headings:
            # Determine level based on font size mapping
            level = "H3"  # Default
            for size, assigned_level in level_mapping.items():
                if heading.font_size >= size:
                    level = assigned_level
                    break
                    
            # Additional heuristics for level determination
            level = self._refine_heading_level(heading, level, avg_font_size)
            
            # Clean the heading text
            clean_text = self._clean_heading_text(heading.text)
            if clean_text:  # Only add non-empty headings
                classified.append({
                    "level": level,
                    "text": clean_text,
                    "page": heading.page_num
                })
                
        return self._validate_hierarchy(classified)
        
    def _refine_heading_level(self, heading: TextBlock, initial_level: str, avg_font_size: float) -> str:
        """
        Refine heading level using additional heuristics.
        
        Args:
            heading: The heading text block
            initial_level: Initially assigned level
            avg_font_size: Average font size
            
        Returns:
            Refined heading level
        """
        font_ratio = heading.font_size / avg_font_size
        
        # Very large fonts are likely H1
        if font_ratio > 2.0:
            return "H1"
        elif font_ratio > 1.5 and heading.is_bold:
            return "H1"
        elif font_ratio > 1.3:
            return "H2" if initial_level != "H1" else "H1"
        elif font_ratio > 1.1 and heading.is_bold:
            return "H2" if initial_level == "H3" else initial_level
            
        # Pattern-based refinement
        text = heading.text.strip()
        
        # Chapter/section patterns typically indicate H1
        if re.match(r'^\s*(chapter|section|part)\s+\d+', text, re.IGNORECASE):
            return "H1"
            
        # Numbered sections (1., 1.1, 1.1.1)
        if re.match(r'^\d+\.\s+', text):
            return "H1"
        elif re.match(r'^\d+\.\d+\s+', text):
            return "H2"
        elif re.match(r'^\d+\.\d+\.\d+\s+', text):
            return "H3"
            
        # Letter enumeration (A., a.)
        if re.match(r'^[A-Z]\.\s+', text):
            return "H2"
        elif re.match(r'^[a-z]\.\s+', text):
            return "H3"
            
        return initial_level
        
    def _clean_heading_text(self, text: str) -> str:
        """
        Clean and normalize heading text.
        
        Args:
            text: Raw heading text
            
        Returns:
            Cleaned heading text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common PDF artifacts
        text = re.sub(r'[^\x00-\x7F]+', '', text)  # Non-ASCII
        text = re.sub(r'\s*\.\s*$', '', text)  # Trailing dots
        
        # Limit length for headings
        if len(text) > 200:
            text = text[:200] + "..."
            
        return text
        
    def _validate_hierarchy(self, headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and adjust heading hierarchy to ensure logical structure.
        
        Args:
            headings: List of classified headings
            
        Returns:
            Validated and adjusted headings
        """
        if not headings:
            return []
            
        validated = []
        last_level = None
        level_order = {"H1": 1, "H2": 2, "H3": 3}
        
        for heading in headings:
            current_level = heading["level"]
            current_order = level_order[current_level]
            
            # First heading
            if last_level is None:
                validated.append(heading)
                last_level = current_level
                continue
                
            last_order = level_order[last_level]
            
            # Validate hierarchy rules
            if current_order > last_order + 1:
                # Skip levels (e.g., H1 -> H3), adjust to appropriate level
                adjusted_level = f"H{last_order + 1}"
                logger.warning(f"Adjusted heading level from {current_level} to {adjusted_level}: {heading['text']}")
                heading["level"] = adjusted_level
                
            validated.append(heading)
            last_level = heading["level"]
            
        return validated

class OutlineExtractor:
    """Main class for extracting document outline."""
    
    def __init__(self):
        self.heading_detector = HeadingDetector()
        self.text_extractor = PDFTextExtractor()
        
    def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract complete outline from PDF including title and headings.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with title and outline structure
        """
        # Extract document title
        if not self.text_extractor.load_pdf(pdf_path):
            return {"title": "Untitled Document", "outline": []}
            
        try:
            title = self.text_extractor.get_document_title()
        finally:
            self.text_extractor.close()
            
        # Extract headings, excluding the title
        headings = self.heading_detector.detect_headings(pdf_path, exclude_title=title)
        
        return {
            "title": title,
            "outline": headings
        } 