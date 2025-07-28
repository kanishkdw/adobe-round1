"""
Main extractor for Round 1B: Multi-PDF relevance extraction.
Orchestrates the complete pipeline from multiple PDFs to ranked relevant sections.
"""

import os
import sys
import json
import time
import logging
from typing import Dict, Any, List, Tuple

# Import local modules
from utils import DocumentProcessor, OutputFormatter, DocumentSection
from ranker import HybridRanker, RelevanceFilter
from summarizer import HybridSummarizer
from persona_matcher import PersonaJobMatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiPDFRelevanceExtractor:
    """Main class for extracting relevant sections from multiple PDFs."""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.ranker = HybridRanker()
        self.relevance_filter = RelevanceFilter()
        self.summarizer = HybridSummarizer()
        self.persona_matcher = PersonaJobMatcher()
        
    def process_documents(self, input_dir: str, output_path: str, 
                         persona: str, job: str) -> bool:
        """
        Process multiple PDF documents and extract relevant sections.
        
        Args:
            input_dir: Directory containing PDF files
            output_path: Path to output JSON file
            persona: User persona description
            job: Job to be done description
            
        Returns:
            bool: True if successful, False otherwise
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting multi-PDF relevance extraction")
            logger.info(f"Persona: {persona}")
            logger.info(f"Job: {job}")
            
            # Load PDF documents
            pdf_files = self.document_processor.load_documents(input_dir)
            if not pdf_files:
                logger.error("No PDF files found in input directory")
                return False
                
            if len(pdf_files) > 10:
                logger.warning(f"Found {len(pdf_files)} PDFs, processing first 10")
                pdf_files = pdf_files[:10]
                
            # Extract sections from all documents
            all_sections = []
            for pdf_file in pdf_files:
                logger.info(f"Processing: {os.path.basename(pdf_file)}")
                sections = self.document_processor.extract_sections_from_document(pdf_file)
                all_sections.extend(sections)
                
            logger.info(f"Extracted {len(all_sections)} sections from {len(pdf_files)} documents")
            
            if not all_sections:
                logger.error("No sections extracted from documents")
                return False
                
            # Analyze persona-job context
            context_analysis = self.persona_matcher.analyze_context(persona, job)
            logger.info(f"Context analysis complete. Persona-job match: {context_analysis['matching_score']:.3f}")
            
            # Rank sections by relevance
            ranked_sections = self.ranker.rank_sections(all_sections, persona, job)
            logger.info(f"Ranked {len(ranked_sections)} sections")
            
            # Filter relevant sections
            filtered_sections = self.relevance_filter.filter_sections(ranked_sections)
            logger.info(f"Filtered to {len(filtered_sections)} relevant sections")
            
            # Take top 5 sections
            top_sections = filtered_sections[:5]
            
            # Enhance sections with summarization
            enhanced_sections = []
            for section, score in top_sections:
                # Summarize if content is too long
                if len(section.content) > 500:
                    summarized_content = self.summarizer.summarize_section(section, max_sentences=3)
                    enhanced_section = DocumentSection(
                        document_name=section.document_name,
                        section_title=section.section_title,
                        content=summarized_content,
                        page_number=section.page_number
                    )
                else:
                    enhanced_section = section
                    
                enhanced_sections.append((enhanced_section, score))
            
            # Format output
            output_data = self._format_output(
                enhanced_sections, pdf_files, persona, job
            )
            
            # Save to output file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
                
            processing_time = time.time() - start_time
            logger.info(f"Successfully completed processing in {processing_time:.2f} seconds")
            logger.info(f"Output saved to: {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing documents: {str(e)}")
            return False
            
    def extract_to_dict(self, input_dir: str, persona: str, job: str) -> Dict[str, Any]:
        """
        Extract relevant sections and return as dictionary (without saving to file).
        
        Args:
            input_dir: Directory containing PDF files
            persona: User persona description
            job: Job to be done description
            
        Returns:
            Dictionary with extraction results, or None if failed
        """
        try:
            # Load documents
            pdf_files = self.document_processor.load_documents(input_dir)
            if not pdf_files:
                return None
                
            # Extract and process sections
            all_sections = []
            for pdf_file in pdf_files[:10]:  # Limit to 10 PDFs
                sections = self.document_processor.extract_sections_from_document(pdf_file)
                all_sections.extend(sections)
                
            if not all_sections:
                return None
                
            # Rank and filter sections
            ranked_sections = self.ranker.rank_sections(all_sections, persona, job)
            filtered_sections = self.relevance_filter.filter_sections(ranked_sections)
            top_sections = filtered_sections[:5]
            
            # Format and return output
            return self._format_output(top_sections, pdf_files, persona, job)
            
        except Exception as e:
            logger.error(f"Error extracting sections: {str(e)}")
            return None
            
    def _format_output(self, sections: List[Tuple[DocumentSection, float]], 
                      pdf_files: List[str], persona: str, job: str) -> Dict[str, Any]:
        """Format the output according to Round 1B specifications."""
        
        # Create metadata
        metadata = OutputFormatter.create_metadata(pdf_files, persona, job)
        
        # Format extracted sections
        extracted_sections = OutputFormatter.format_extracted_sections(sections)
        
        # Format subsection analysis
        subsection_analysis = OutputFormatter.format_subsection_analysis(sections)
        
        return {
            "metadata": {
                "input_documents": metadata.input_documents,
                "persona": metadata.persona,
                "job_to_be_done": metadata.job_to_be_done,
                "processing_timestamp": metadata.processing_timestamp
            },
            "extracted_sections": extracted_sections,
            "subsection_analysis": subsection_analysis
        }

def main():
    """Main entry point for the application."""
    # Docker paths
    input_dir = "/app/input"
    output_dir = "/app/output"
    
    # Load configuration (persona and job) from environment or files
    persona, job = load_configuration(input_dir)
    
    if not persona or not job:
        logger.error("Persona and job configuration not found")
        sys.exit(1)
        
    # Create output file path
    output_json = os.path.join(output_dir, "relevant_sections.json")
    
    # Process the documents
    extractor = MultiPDFRelevanceExtractor()
    success = extractor.process_documents(input_dir, output_json, persona, job)
    
    if not success:
        logger.error("Failed to process documents")
        sys.exit(1)
        
    logger.info("Multi-PDF relevance extraction completed successfully")

def load_configuration(input_dir: str) -> Tuple[str, str]:
    """
    Load persona and job configuration from files or environment.
    
    Args:
        input_dir: Input directory to look for config files
        
    Returns:
        Tuple of (persona, job) strings
    """
    persona = ""
    job = ""
    
    # Try to load from environment variables first
    persona = os.environ.get('PERSONA', '')
    job = os.environ.get('JOB', '')
    
    if persona and job:
        return persona, job
    
    # Try to load from config files
    config_file = os.path.join(input_dir, "config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                persona = config.get('persona', '')
                job = config.get('job', '')
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
    
    # Try individual files
    if not persona:
        persona_file = os.path.join(input_dir, "persona.txt")
        if os.path.exists(persona_file):
            try:
                with open(persona_file, 'r', encoding='utf-8') as f:
                    persona = f.read().strip()
            except Exception as e:
                logger.error(f"Error loading persona file: {e}")
    
    if not job:
        job_file = os.path.join(input_dir, "job.txt")
        if os.path.exists(job_file):
            try:
                with open(job_file, 'r', encoding='utf-8') as f:
                    job = f.read().strip()
            except Exception as e:
                logger.error(f"Error loading job file: {e}")
    
    # Default values for testing
    if not persona:
        persona = "Food Contractor"
        logger.warning("Using default persona: Food Contractor")
        
    if not job:
        job = "Create a vegetarian dinner buffet plan with gluten-free items"
        logger.warning("Using default job: Create a vegetarian dinner buffet plan with gluten-free items")
    
    return persona, job

if __name__ == "__main__":
    main() 