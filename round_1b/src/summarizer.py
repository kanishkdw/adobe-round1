"""
Summarizer module for Round 1B: Multi-PDF relevance extraction.
Implements extractive summarization techniques for document sections.
"""

import re
import logging
from typing import List, Dict, Any, Tuple
from collections import Counter
import math

from utils import DocumentSection, TextProcessor

logger = logging.getLogger(__name__)

class SentenceExtractor:
    """Extract and score sentences for summarization."""
    
    def __init__(self):
        self.sentence_separators = r'[.!?]+'
        
    def extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        # Split by sentence separators
        sentences = re.split(self.sentence_separators, text)
        
        # Clean and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and self._is_valid_sentence(sentence):
                cleaned_sentences.append(sentence)
                
        return cleaned_sentences
    
    def _is_valid_sentence(self, sentence: str) -> bool:
        """Check if a sentence is valid for summarization."""
        # Must contain alphabetic characters
        if not re.search(r'[a-zA-Z]', sentence):
            return False
            
        # Must have reasonable length
        if len(sentence) < 10 or len(sentence) > 500:
            return False
            
        # Must not be mostly numbers or symbols
        alpha_ratio = len(re.findall(r'[a-zA-Z]', sentence)) / len(sentence)
        if alpha_ratio < 0.5:
            return False
            
        return True

class TextRankSummarizer:
    """TextRank-based extractive summarization."""
    
    def __init__(self, damping_factor: float = 0.85, max_iterations: int = 50, 
                 convergence_threshold: float = 0.001):
        self.damping_factor = damping_factor
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.sentence_extractor = SentenceExtractor()
        
    def summarize_section(self, section: DocumentSection, 
                         max_sentences: int = 3) -> str:
        """
        Summarize a document section using TextRank algorithm.
        
        Args:
            section: Document section to summarize
            max_sentences: Maximum number of sentences in summary
            
        Returns:
            Summarized text
        """
        sentences = self.sentence_extractor.extract_sentences(section.content)
        
        if len(sentences) <= max_sentences:
            return section.content  # No need to summarize
            
        # Calculate sentence similarities
        similarity_matrix = self._build_similarity_matrix(sentences)
        
        # Apply TextRank algorithm
        sentence_scores = self._textrank(similarity_matrix)
        
        # Select top sentences
        top_indices = sorted(range(len(sentence_scores)), 
                           key=lambda i: sentence_scores[i], reverse=True)[:max_sentences]
        
        # Maintain original order
        top_indices.sort()
        
        summary_sentences = [sentences[i] for i in top_indices]
        return '. '.join(summary_sentences) + '.'
    
    def _build_similarity_matrix(self, sentences: List[str]) -> List[List[float]]:
        """Build similarity matrix between sentences."""
        n = len(sentences)
        similarity_matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    similarity_matrix[i][j] = self._sentence_similarity(
                        sentences[i], sentences[j]
                    )
                    
        return similarity_matrix
    
    def _sentence_similarity(self, sent1: str, sent2: str) -> float:
        """Calculate similarity between two sentences using word overlap."""
        words1 = set(TextProcessor.extract_keywords(sent1.lower()))
        words2 = set(TextProcessor.extract_keywords(sent2.lower()))
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _textrank(self, similarity_matrix: List[List[float]]) -> List[float]:
        """Apply TextRank algorithm to similarity matrix."""
        n = len(similarity_matrix)
        if n == 0:
            return []
            
        # Initialize scores
        scores = [1.0] * n
        
        for iteration in range(self.max_iterations):
            new_scores = [0.0] * n
            
            for i in range(n):
                for j in range(n):
                    if similarity_matrix[i][j] > 0:
                        # Sum of similarities from node j
                        sum_similarities = sum(similarity_matrix[j])
                        if sum_similarities > 0:
                            new_scores[i] += (similarity_matrix[i][j] / sum_similarities) * scores[j]
                
                new_scores[i] = (1 - self.damping_factor) + self.damping_factor * new_scores[i]
            
            # Check convergence
            if self._has_converged(scores, new_scores):
                break
                
            scores = new_scores[:]
            
        return scores
    
    def _has_converged(self, old_scores: List[float], new_scores: List[float]) -> bool:
        """Check if TextRank has converged."""
        if len(old_scores) != len(new_scores):
            return False
            
        for old, new in zip(old_scores, new_scores):
            if abs(old - new) > self.convergence_threshold:
                return False
                
        return True

class FrequencyBasedSummarizer:
    """Simple frequency-based extractive summarization."""
    
    def __init__(self):
        self.sentence_extractor = SentenceExtractor()
        
    def summarize_section(self, section: DocumentSection, 
                         max_sentences: int = 3) -> str:
        """
        Summarize section using word frequency scoring.
        
        Args:
            section: Document section to summarize
            max_sentences: Maximum number of sentences in summary
            
        Returns:
            Summarized text
        """
        sentences = self.sentence_extractor.extract_sentences(section.content)
        
        if len(sentences) <= max_sentences:
            return section.content
            
        # Calculate word frequencies
        all_words = []
        for sentence in sentences:
            all_words.extend(TextProcessor.extract_keywords(sentence.lower()))
            
        word_freq = Counter(all_words)
        
        # Score sentences based on word frequencies
        sentence_scores = []
        for sentence in sentences:
            words = TextProcessor.extract_keywords(sentence.lower())
            if words:
                score = sum(word_freq[word] for word in words) / len(words)
            else:
                score = 0.0
            sentence_scores.append(score)
        
        # Select top sentences
        top_indices = sorted(range(len(sentence_scores)), 
                           key=lambda i: sentence_scores[i], reverse=True)[:max_sentences]
        
        # Maintain original order
        top_indices.sort()
        
        summary_sentences = [sentences[i] for i in top_indices]
        return '. '.join(summary_sentences) + '.'

class PositionalSummarizer:
    """Summarization that considers sentence position."""
    
    def __init__(self):
        self.sentence_extractor = SentenceExtractor()
        
    def summarize_section(self, section: DocumentSection, 
                         max_sentences: int = 3) -> str:
        """
        Summarize section considering sentence position and frequency.
        
        Args:
            section: Document section to summarize
            max_sentences: Maximum number of sentences in summary
            
        Returns:
            Summarized text
        """
        sentences = self.sentence_extractor.extract_sentences(section.content)
        
        if len(sentences) <= max_sentences:
            return section.content
            
        sentence_scores = []
        total_sentences = len(sentences)
        
        # Calculate word frequencies
        all_words = []
        for sentence in sentences:
            all_words.extend(TextProcessor.extract_keywords(sentence.lower()))
        word_freq = Counter(all_words)
        
        for i, sentence in enumerate(sentences):
            # Frequency score
            words = TextProcessor.extract_keywords(sentence.lower())
            if words:
                freq_score = sum(word_freq[word] for word in words) / len(words)
            else:
                freq_score = 0.0
            
            # Position score (first and last sentences are often important)
            if i == 0:
                position_score = 1.0  # First sentence
            elif i == total_sentences - 1:
                position_score = 0.8  # Last sentence
            elif i < total_sentences * 0.3:
                position_score = 0.7  # Early sentences
            else:
                position_score = 0.5  # Middle sentences
            
            # Combine scores
            final_score = 0.7 * freq_score + 0.3 * position_score
            sentence_scores.append(final_score)
        
        # Select top sentences
        top_indices = sorted(range(len(sentence_scores)), 
                           key=lambda i: sentence_scores[i], reverse=True)[:max_sentences]
        
        # Maintain original order
        top_indices.sort()
        
        summary_sentences = [sentences[i] for i in top_indices]
        return '. '.join(summary_sentences) + '.'

class HybridSummarizer:
    """Hybrid summarizer combining multiple techniques."""
    
    def __init__(self):
        self.textrank_summarizer = TextRankSummarizer()
        self.frequency_summarizer = FrequencyBasedSummarizer()
        self.positional_summarizer = PositionalSummarizer()
        
    def summarize_section(self, section: DocumentSection, 
                         max_sentences: int = 3, 
                         method: str = 'hybrid') -> str:
        """
        Summarize section using specified method or hybrid approach.
        
        Args:
            section: Document section to summarize
            max_sentences: Maximum number of sentences in summary
            method: Summarization method ('textrank', 'frequency', 'positional', 'hybrid')
            
        Returns:
            Summarized text
        """
        if not section.content.strip():
            return section.content
            
        if method == 'textrank':
            return self.textrank_summarizer.summarize_section(section, max_sentences)
        elif method == 'frequency':
            return self.frequency_summarizer.summarize_section(section, max_sentences)
        elif method == 'positional':
            return self.positional_summarizer.summarize_section(section, max_sentences)
        elif method == 'hybrid':
            return self._hybrid_summarize(section, max_sentences)
        else:
            logger.warning(f"Unknown summarization method: {method}, using hybrid")
            return self._hybrid_summarize(section, max_sentences)
    
    def _hybrid_summarize(self, section: DocumentSection, max_sentences: int) -> str:
        """Hybrid summarization combining multiple methods."""
        # For short content, return as-is
        sentences = self.textrank_summarizer.sentence_extractor.extract_sentences(section.content)
        if len(sentences) <= max_sentences:
            return section.content
        
        # Try different methods and combine results
        textrank_summary = self.textrank_summarizer.summarize_section(section, max_sentences)
        positional_summary = self.positional_summarizer.summarize_section(section, max_sentences)
        
        # Extract sentences from both summaries
        textrank_sentences = set(self.textrank_summarizer.sentence_extractor.extract_sentences(textrank_summary))
        positional_sentences = set(self.textrank_summarizer.sentence_extractor.extract_sentences(positional_summary))
        
        # Combine unique sentences, prioritizing those that appear in both
        combined_sentences = []
        
        # First, add sentences that appear in both methods
        common_sentences = textrank_sentences.intersection(positional_sentences)
        combined_sentences.extend(list(common_sentences))
        
        # Then add unique sentences from each method
        remaining_slots = max_sentences - len(combined_sentences)
        if remaining_slots > 0:
            unique_textrank = textrank_sentences - positional_sentences
            unique_positional = positional_sentences - textrank_sentences
            
            # Alternate between methods
            all_unique = list(unique_textrank) + list(unique_positional)
            combined_sentences.extend(all_unique[:remaining_slots])
        
        # Maintain original order by finding sentences in original text
        original_sentences = sentences
        ordered_summary = []
        
        for orig_sent in original_sentences:
            for summary_sent in combined_sentences:
                if orig_sent.strip() == summary_sent.strip():
                    ordered_summary.append(orig_sent)
                    break
            if len(ordered_summary) >= max_sentences:
                break
        
        return '. '.join(ordered_summary) + '.' if ordered_summary else section.content 