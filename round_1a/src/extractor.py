"""
Main extractor for Round 1A: PDF outline extraction.
Handles the complete pipeline from PDF input to structured JSON output.
"""

import os
import sys
import json
import time
import logging
from typing import Dict, Any

# Import local modules
from pdf_utils import OutlineExtractor
from schema_validator import OutlineValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFOutlineExtractor:
    """Main class for extracting PDF outlines with validation."""
    
    def __init__(self):
        self.outline_extractor = OutlineExtractor()
        self.validator = OutlineValidator()
        
    def process_pdf(self, input_path: str, output_path: str) -> bool:
        """
        Process a PDF file and extract its outline structure.
        
        Args:
            input_path: Path to input PDF file
            output_path: Path to output JSON file
            
        Returns:
            bool: True if successful, False otherwise
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting PDF outline extraction: {input_path}")
            
            # Check if input file exists
            if not os.path.exists(input_path):
                logger.error(f"Input file does not exist: {input_path}")
                return False
                
            # Extract outline
            outline_data = self.outline_extractor.extract_outline(input_path)
            
            # Validate the extracted data
            validated_data = self.validator.validate_and_clean(outline_data)
            if validated_data is None:
                logger.error("Validation failed for extracted outline")
                errors = self.validator.get_validation_errors(outline_data)
                for error in errors:
                    logger.error(f"Validation error: {error}")
                return False
                
            # Save to output file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(validated_data, f, indent=2, ensure_ascii=False)
                
            processing_time = time.time() - start_time
            logger.info(f"Successfully extracted outline in {processing_time:.2f} seconds")
            logger.info(f"Found {len(validated_data['outline'])} headings")
            logger.info(f"Output saved to: {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return False
            
    def extract_to_dict(self, input_path: str) -> Dict[str, Any]:
        """
        Extract outline and return as dictionary (without saving to file).
        
        Args:
            input_path: Path to input PDF file
            
        Returns:
            Dictionary with outline data, or None if failed
        """
        try:
            outline_data = self.outline_extractor.extract_outline(input_path)
            validated_data = self.validator.validate_and_clean(outline_data)
            return validated_data
        except Exception as e:
            logger.error(f"Error extracting outline: {str(e)}")
            return None

def main():
    """Main entry point for the application."""
    # Docker paths
    input_dir = "/app/input"
    output_dir = "/app/output"
    
    # Find all PDF files in input directory
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        logger.error("No PDF files found in input directory")
        sys.exit(1)
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF file
    extractor = PDFOutlineExtractor()
    success_count = 0
    
    for pdf_file in sorted(pdf_files):
        input_pdf = os.path.join(input_dir, pdf_file)
        
        # Create output filename based on input filename
        base_name = os.path.splitext(pdf_file)[0]
        output_json = os.path.join(output_dir, f"{base_name}_outline.json")
        
        logger.info(f"Processing: {pdf_file}")
        success = extractor.process_pdf(input_pdf, output_json)
        
        if success:
            success_count += 1
            logger.info(f"Successfully processed {pdf_file}")
        else:
            logger.error(f"Failed to process {pdf_file}")
    
    if success_count == len(pdf_files):
        logger.info(f"All {success_count} PDF files processed successfully")
        sys.exit(0)
    else:
        logger.error(f"Processed {success_count}/{len(pdf_files)} files successfully")
        sys.exit(1)

if __name__ == "__main__":
    main() 