"""
Shared text extraction utilities for PDF processing.
Used by both Round 1A and Round 1B for common PDF operations.
"""

import fitz  # PyMuPDF
import re
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TextBlock:
    """Represents a text block with positioning and formatting information."""
    text: str
    page_num: int
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    font_size: float
    font_name: str
    is_bold: bool
    
class PDFTextExtractor:
    """Shared PDF text extraction utilities."""
    
    def __init__(self):
        self.doc = None
        
    def load_pdf(self, pdf_path: str) -> bool:
        """Load a PDF file for processing."""
        try:
            self.doc = fitz.open(pdf_path)
            logger.info(f"Loaded PDF: {pdf_path} ({len(self.doc)} pages)")
            return True
        except Exception as e:
            logger.error(f"Failed to load PDF {pdf_path}: {e}")
            return False
            
    def close(self):
        """Close the PDF document."""
        if self.doc:
            self.doc.close()
            
    def get_page_count(self) -> int:
        """Get total number of pages."""
        return len(self.doc) if self.doc else 0
        
    def extract_text_blocks(self, page_num: int = None) -> List[TextBlock]:
        """Extract text blocks with formatting information from specific page or all pages."""
        if not self.doc:
            return []
            
        text_blocks = []
        pages = [page_num] if page_num is not None else range(len(self.doc))
        
        for page_idx in pages:
            page = self.doc[page_idx]
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                            
                        # Extract formatting information
                        font_name = span["font"]
                        font_size = span["size"]
                        flags = span["flags"]
                        is_bold = bool(flags & 2**4)  # Bold flag
                        
                        text_block = TextBlock(
                            text=text,
                            page_num=page_idx + 1,  # 1-indexed
                            bbox=span["bbox"],
                            font_size=font_size,
                            font_name=font_name,
                            is_bold=is_bold
                        )
                        text_blocks.append(text_block)
                        
        return text_blocks
        
    def extract_page_text(self, page_num: int) -> str:
        """Extract plain text from a specific page."""
        if not self.doc or page_num < 1 or page_num > len(self.doc):
            return ""
            
        page = self.doc[page_num - 1]  # Convert to 0-indexed
        return page.get_text()
        
    def get_document_title(self) -> str:
        """Extract document title from metadata or first page."""
        if not self.doc:
            return "Untitled Document"
            
        # Look for title-like text on first page first (more reliable)
        text_blocks = self.extract_text_blocks(0)  # First page
        if text_blocks:
            # Find largest font size on first page (likely title)
            max_font_size = max(block.font_size for block in text_blocks)
            title_candidates = [
                block.text for block in text_blocks 
                if block.font_size >= max_font_size * 0.9 and len(block.text) > 5
            ]
            
            if title_candidates:
                # Return the first substantial title candidate
                return title_candidates[0]
        
        # Fallback: try metadata
        metadata = self.doc.metadata
        if metadata.get("title"):
            return metadata["title"].strip()
            
        return "Untitled Document"
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove common PDF artifacts
        text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII
        return text.strip()
        
    def is_likely_heading(self, block: TextBlock, avg_font_size: float) -> bool:
        """Determine if a text block is likely a heading based on formatting."""
        # Headings are typically:
        # 1. Larger than average font size
        # 2. Bold or have specific formatting
        # 3. Not too long (not paragraphs)
        # 4. Start with capital letter or number
        
        if len(block.text) > 200:  # Too long for heading
            return False
            
        if not re.match(r'^[A-Z0-9]', block.text):  # Should start with capital/number
            return False
            
        # Font size check
        font_ratio = block.font_size / avg_font_size if avg_font_size > 0 else 1
        
        # Consider it a heading if:
        # - Significantly larger font (>1.2x average)
        # - Bold and reasonably larger (>1.1x average)
        # - Very large font regardless of bold
        
        is_large_font = font_ratio > 1.2
        is_bold_and_larger = block.is_bold and font_ratio > 1.1
        is_very_large = font_ratio > 1.5
        
        return is_large_font or is_bold_and_larger or is_very_large
        
    def calculate_average_font_size(self, text_blocks: List[TextBlock]) -> float:
        """Calculate average font size for the document."""
        if not text_blocks:
            return 12.0  # Default font size
            
        total_size = sum(block.font_size * len(block.text) for block in text_blocks)
        total_chars = sum(len(block.text) for block in text_blocks)
        
        return total_size / total_chars if total_chars > 0 else 12.0 