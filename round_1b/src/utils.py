"""
Utility functions for Round 1B: Multi-PDF relevance extraction.
Contains common functions for text processing, scoring, and document handling.
"""

import os
import sys
import re
import json
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from shared.text_extractor import PDFTextExtractor

logger = logging.getLogger(__name__)

@dataclass
class DocumentSection:
    """Represents a document section with metadata and content."""
    document_name: str
    section_title: str
    content: str
    page_number: int
    start_page: int = None
    end_page: int = None
    
@dataclass
class ProcessingMetadata:
    """Metadata for the processing run."""
    input_documents: List[str]
    persona: str
    job_to_be_done: str
    processing_timestamp: str

class TextProcessor:
    """Text processing utilities for Round 1B."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove common PDF artifacts
        text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII
        text = re.sub(r'\s*\n\s*', ' ', text)  # Normalize line breaks
        return text.strip()
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        # Simple keyword extraction - can be enhanced with NLP
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        # Remove common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'over', 'after', 'this', 'that',
            'these', 'those', 'can', 'will', 'should', 'would', 'could', 'may',
            'might', 'must', 'shall', 'have', 'has', 'had', 'be', 'been', 'being',
            'is', 'are', 'was', 'were', 'do', 'does', 'did', 'get', 'got', 'make',
            'made', 'take', 'took', 'come', 'came', 'go', 'went', 'see', 'saw'
        }
        return [word for word in words if word not in stop_words and len(word) > 3]

    @staticmethod
    def clean_section_title(title: str) -> str:
        """Clean section title using regex patterns."""
        # Pattern from the prompt for cleaning section headers
        title = re.sub(r'[^A-Za-z0-9\s\-]', '', title).strip()
        if re.match(r'^[A-Z][A-Za-z0-9\s\-]*$', title):
            return title
        # If doesn't match pattern, try to fix capitalization
        return title.title() if title else "Untitled Section"

class DocumentProcessor:
    """Process multiple PDF documents and extract sections."""
    
    def __init__(self):
        self.extractor = PDFTextExtractor()
        
    def load_documents(self, input_dir: str) -> List[str]:
        """Load all PDF files from input directory."""
        pdf_files = []
        if os.path.exists(input_dir):
            for filename in os.listdir(input_dir):
                if filename.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(input_dir, filename))
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        return sorted(pdf_files)
    
    def extract_sections_from_document(self, pdf_path: str) -> List[DocumentSection]:
        """Extract sections from a single PDF document."""
        if not self.extractor.load_pdf(pdf_path):
            return []
            
        try:
            sections = []
            document_name = os.path.basename(pdf_path)
            
            # Get total pages
            total_pages = self.extractor.get_page_count()
            
            # Extract text from all pages and identify sections
            all_text_blocks = self.extractor.extract_text_blocks()
            
            if not all_text_blocks:
                # Fallback: treat each page as a section
                for page_num in range(1, total_pages + 1):
                    page_text = self.extractor.extract_page_text(page_num)
                    if page_text.strip():
                        sections.append(DocumentSection(
                            document_name=document_name,
                            section_title=f"Page {page_num}",
                            content=TextProcessor.clean_text(page_text),
                            page_number=page_num
                        ))
                return sections
            
            # Group text blocks by potential sections
            current_section = None
            current_content = []
            
            avg_font_size = self.extractor.calculate_average_font_size(all_text_blocks)
            
            for block in all_text_blocks:
                if self.extractor.is_likely_heading(block, avg_font_size):
                    # Save previous section if exists
                    if current_section and current_content:
                        sections.append(DocumentSection(
                            document_name=document_name,
                            section_title=current_section,
                            content=TextProcessor.clean_text(' '.join(current_content)),
                            page_number=block.page_num
                        ))
                    
                    # Start new section
                    current_section = TextProcessor.clean_section_title(block.text)
                    current_content = []
                else:
                    current_content.append(block.text)
            
            # Don't forget the last section
            if current_section and current_content:
                sections.append(DocumentSection(
                    document_name=document_name,
                    section_title=current_section,
                    content=TextProcessor.clean_text(' '.join(current_content)),
                    page_number=all_text_blocks[-1].page_num if all_text_blocks else 1
                ))
            
            # If no sections found, create page-based sections
            if not sections:
                for page_num in range(1, total_pages + 1):
                    page_text = self.extractor.extract_page_text(page_num)
                    if page_text.strip():
                        sections.append(DocumentSection(
                            document_name=document_name,
                            section_title=f"Content from Page {page_num}",
                            content=TextProcessor.clean_text(page_text),
                            page_number=page_num
                        ))
            
            return sections
            
        finally:
            self.extractor.close()

class ScoringUtils:
    """Utilities for scoring and ranking content relevance."""
    
    @staticmethod
    def calculate_keyword_overlap(text1: str, text2: str) -> float:
        """Calculate keyword overlap between two texts."""
        keywords1 = set(TextProcessor.extract_keywords(text1))
        keywords2 = set(TextProcessor.extract_keywords(text2))
        
        if not keywords1 or not keywords2:
            return 0.0
            
        intersection = keywords1.intersection(keywords2)
        union = keywords1.union(keywords2)
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def calculate_title_relevance(section_title: str, persona: str, job: str) -> float:
        """Calculate how relevant a section title is to the persona and job."""
        combined_context = f"{persona} {job}".lower()
        section_lower = section_title.lower()
        
        # Direct keyword matches
        context_keywords = set(TextProcessor.extract_keywords(combined_context))
        title_keywords = set(TextProcessor.extract_keywords(section_lower))
        
        if not context_keywords or not title_keywords:
            return 0.0
            
        overlap = len(context_keywords.intersection(title_keywords))
        return overlap / len(context_keywords) if context_keywords else 0.0
    
    @staticmethod
    def calculate_content_relevance(content: str, persona: str, job: str) -> float:
        """Calculate content relevance to persona and job."""
        # Simple TF-IDF-like scoring
        persona_keywords = set(TextProcessor.extract_keywords(persona.lower()))
        job_keywords = set(TextProcessor.extract_keywords(job.lower()))
        content_keywords = set(TextProcessor.extract_keywords(content.lower()))
        
        # Weight persona and job keywords
        relevant_keywords = persona_keywords.union(job_keywords)
        
        if not relevant_keywords or not content_keywords:
            return 0.0
            
        matches = len(relevant_keywords.intersection(content_keywords))
        return matches / len(relevant_keywords) if relevant_keywords else 0.0
    
    @staticmethod
    def calculate_position_score(page_number: int, total_pages: int) -> float:
        """Calculate position-based relevance (earlier pages may be more important)."""
        if total_pages <= 1:
            return 1.0
        # Linear decay from front to back
        return 1.0 - (page_number - 1) / (total_pages - 1) * 0.3  # Max 30% penalty for last page
    
    @staticmethod
    def calculate_composite_score(section: DocumentSection, persona: str, job: str, 
                                weights: Dict[str, float] = None, total_pages: int = 1) -> float:
        """Calculate composite relevance score using multiple factors."""
        if weights is None:
            weights = {
                'content_relevance': 0.5,
                'title_relevance': 0.3,
                'position_score': 0.2
            }
        
        content_score = ScoringUtils.calculate_content_relevance(section.content, persona, job)
        title_score = ScoringUtils.calculate_title_relevance(section.section_title, persona, job)
        position_score = ScoringUtils.calculate_position_score(section.page_number, total_pages)
        
        composite = (
            weights['content_relevance'] * content_score +
            weights['title_relevance'] * title_score +
            weights['position_score'] * position_score
        )
        
        return composite

class OutputFormatter:
    """Format output according to Round 1B specifications."""
    
    @staticmethod
    def create_metadata(pdf_files: List[str], persona: str, job: str) -> ProcessingMetadata:
        """Create processing metadata."""
        return ProcessingMetadata(
            input_documents=[os.path.basename(f) for f in pdf_files],
            persona=persona,
            job_to_be_done=job,
            processing_timestamp=datetime.now().isoformat()
        )
    
    @staticmethod
    def format_extracted_sections(sections: List[Tuple[DocumentSection, float]]) -> List[Dict[str, Any]]:
        """Format extracted sections for output."""
        formatted = []
        for i, (section, score) in enumerate(sections[:5], 1):  # Max 5 sections
            formatted.append({
                "document": section.document_name,
                "section_title": section.section_title,
                "importance_rank": i,
                "page_number": section.page_number
            })
        return formatted
    
    @staticmethod
    def format_subsection_analysis(sections: List[Tuple[DocumentSection, float]]) -> List[Dict[str, Any]]:
        """Format subsection analysis for output."""
        formatted = []
        for section, score in sections[:5]:  # Max 5 sections
            # Extract refined text (summary or key content)
            refined_text = section.content
            if len(refined_text) > 500:  # Truncate if too long
                refined_text = refined_text[:500] + "..."
                
            formatted.append({
                "document": section.document_name,
                "refined_text": refined_text,
                "page_number": section.page_number
            })
        return formatted 