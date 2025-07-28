"""
Ranker module for Round 1B: Multi-PDF relevance extraction.
Implements section ranking and relevance scoring algorithms.
"""

import math
import logging
from typing import List, Dict, Any, Tuple
from collections import Counter
import re

from utils import DocumentSection, ScoringUtils, TextProcessor

logger = logging.getLogger(__name__)

class TFIDFRanker:
    """TF-IDF based ranking for document sections."""
    
    def __init__(self):
        self.document_frequencies = {}
        self.total_documents = 0
        
    def compute_tf_idf_scores(self, sections: List[DocumentSection], 
                             persona: str, job: str) -> List[Tuple[DocumentSection, float]]:
        """
        Compute TF-IDF based relevance scores for sections.
        
        Args:
            sections: List of document sections
            persona: User persona description
            job: Job to be done description
            
        Returns:
            List of (section, score) tuples sorted by relevance
        """
        if not sections:
            return []
            
        # Combine persona and job for query context
        query_text = f"{persona} {job}".lower()
        query_terms = TextProcessor.extract_keywords(query_text)
        
        if not query_terms:
            logger.warning("No query terms extracted from persona and job")
            return [(section, 0.0) for section in sections]
        
        # Build document frequency dictionary
        self._build_document_frequencies(sections)
        
        scored_sections = []
        for section in sections:
            score = self._calculate_tfidf_score(section, query_terms)
            scored_sections.append((section, score))
            
        # Sort by score (descending)
        scored_sections.sort(key=lambda x: x[1], reverse=True)
        return scored_sections
    
    def _build_document_frequencies(self, sections: List[DocumentSection]):
        """Build document frequency dictionary for IDF calculation."""
        self.document_frequencies = {}
        self.total_documents = len(sections)
        
        for section in sections:
            section_terms = set(TextProcessor.extract_keywords(section.content.lower()))
            for term in section_terms:
                self.document_frequencies[term] = self.document_frequencies.get(term, 0) + 1
    
    def _calculate_tfidf_score(self, section: DocumentSection, query_terms: List[str]) -> float:
        """Calculate TF-IDF score for a section given query terms."""
        section_text = section.content.lower()
        section_terms = TextProcessor.extract_keywords(section_text)
        
        if not section_terms:
            return 0.0
            
        # Calculate term frequencies
        term_counts = Counter(section_terms)
        total_terms = len(section_terms)
        
        score = 0.0
        for query_term in query_terms:
            if query_term in term_counts:
                # TF: Term frequency in document
                tf = term_counts[query_term] / total_terms
                
                # IDF: Inverse document frequency
                df = self.document_frequencies.get(query_term, 0)
                if df > 0:
                    idf = math.log(self.total_documents / df)
                else:
                    idf = 0
                
                score += tf * idf
                
        return score

class SemanticRanker:
    """Semantic similarity-based ranking using keyword overlap and context."""
    
    def __init__(self):
        self.persona_weight = 0.6
        self.job_weight = 0.4
        
    def compute_semantic_scores(self, sections: List[DocumentSection], 
                               persona: str, job: str) -> List[Tuple[DocumentSection, float]]:
        """
        Compute semantic similarity scores for sections.
        
        Args:
            sections: List of document sections
            persona: User persona description
            job: Job to be done description
            
        Returns:
            List of (section, score) tuples sorted by relevance
        """
        if not sections:
            return []
            
        scored_sections = []
        for section in sections:
            score = self._calculate_semantic_score(section, persona, job)
            scored_sections.append((section, score))
            
        # Sort by score (descending)
        scored_sections.sort(key=lambda x: x[1], reverse=True)
        return scored_sections
    
    def _calculate_semantic_score(self, section: DocumentSection, persona: str, job: str) -> float:
        """Calculate semantic similarity score for a section."""
        # Content similarity to persona and job
        persona_content_sim = ScoringUtils.calculate_keyword_overlap(section.content, persona)
        job_content_sim = ScoringUtils.calculate_keyword_overlap(section.content, job)
        
        # Title similarity to persona and job
        persona_title_sim = ScoringUtils.calculate_keyword_overlap(section.section_title, persona)
        job_title_sim = ScoringUtils.calculate_keyword_overlap(section.section_title, job)
        
        # Combine scores with weights
        content_score = (
            self.persona_weight * persona_content_sim + 
            self.job_weight * job_content_sim
        )
        
        title_score = (
            self.persona_weight * persona_title_sim + 
            self.job_weight * job_title_sim
        )
        
        # Weight title higher than content for relevance
        final_score = 0.3 * title_score + 0.7 * content_score
        
        return final_score

class HybridRanker:
    """Hybrid ranker combining multiple ranking strategies."""
    
    def __init__(self):
        self.tfidf_ranker = TFIDFRanker()
        self.semantic_ranker = SemanticRanker()
        
    def rank_sections(self, sections: List[DocumentSection], persona: str, job: str,
                     weights: Dict[str, float] = None) -> List[Tuple[DocumentSection, float]]:
        """
        Rank sections using hybrid approach combining multiple strategies.
        
        Args:
            sections: List of document sections
            persona: User persona description
            job: Job to be done description
            weights: Weights for different scoring components
            
        Returns:
            List of (section, score) tuples sorted by relevance
        """
        if not sections:
            return []
            
        if weights is None:
            weights = {
                'tfidf': 0.3,
                'semantic': 0.3,
                'composite': 0.4
            }
        
        # Get TF-IDF scores
        tfidf_scores = dict(self.tfidf_ranker.compute_tf_idf_scores(sections, persona, job))
        
        # Get semantic scores  
        semantic_scores = dict(self.semantic_ranker.compute_semantic_scores(sections, persona, job))
        
        # Get composite scores
        total_pages = max(section.page_number for section in sections) if sections else 1
        composite_scores = {}
        for section in sections:
            composite_scores[section] = ScoringUtils.calculate_composite_score(
                section, persona, job, total_pages=total_pages
            )
        
        # Normalize scores to [0, 1] range
        tfidf_max = max(tfidf_scores.values()) if tfidf_scores.values() else 1.0
        semantic_max = max(semantic_scores.values()) if semantic_scores.values() else 1.0  
        composite_max = max(composite_scores.values()) if composite_scores.values() else 1.0
        
        # Combine scores
        final_scores = []
        for section in sections:
            tfidf_norm = tfidf_scores.get(section, 0) / tfidf_max if tfidf_max > 0 else 0
            semantic_norm = semantic_scores.get(section, 0) / semantic_max if semantic_max > 0 else 0
            composite_norm = composite_scores.get(section, 0) / composite_max if composite_max > 0 else 0
            
            final_score = (
                weights['tfidf'] * tfidf_norm +
                weights['semantic'] * semantic_norm +
                weights['composite'] * composite_norm
            )
            
            final_scores.append((section, final_score))
        
        # Sort by final score (descending)
        final_scores.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Ranked {len(final_scores)} sections")
        return final_scores

class RelevanceFilter:
    """Filter sections based on relevance thresholds and quality metrics."""
    
    def __init__(self, min_score_threshold: float = 0.1, min_content_length: int = 50):
        self.min_score_threshold = min_score_threshold
        self.min_content_length = min_content_length
        
    def filter_sections(self, scored_sections: List[Tuple[DocumentSection, float]]) -> List[Tuple[DocumentSection, float]]:
        """
        Filter sections based on relevance and quality criteria.
        
        Args:
            scored_sections: List of (section, score) tuples
            
        Returns:
            Filtered list of relevant sections
        """
        filtered = []
        
        for section, score in scored_sections:
            # Apply score threshold
            if score < self.min_score_threshold:
                continue
                
            # Apply content length threshold
            if len(section.content.strip()) < self.min_content_length:
                continue
                
            # Additional quality checks
            if not self._is_meaningful_content(section.content):
                continue
                
            filtered.append((section, score))
        
        logger.info(f"Filtered {len(scored_sections)} sections to {len(filtered)} relevant sections")
        return filtered
    
    def _is_meaningful_content(self, content: str) -> bool:
        """Check if content is meaningful (not just headers, page numbers, etc.)."""
        content = content.strip()
        
        # Too short
        if len(content) < 20:
            return False
            
        # Only digits and common separators (likely page numbers, etc.)
        if re.match(r'^[\d\s\-\.\,]+$', content):
            return False
            
        # Must contain some alphabetic content
        if not re.search(r'[a-zA-Z]', content):
            return False
            
        # Extract words
        words = re.findall(r'\b[a-zA-Z]+\b', content)
        
        # Must have sufficient word count
        if len(words) < 5:
            return False
            
        return True 