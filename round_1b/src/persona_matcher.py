"""
Persona matcher module for Round 1B: Multi-PDF relevance extraction.
Handles persona-job matching and context analysis for relevance scoring.
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Set
from collections import defaultdict

from utils import DocumentSection, TextProcessor, ScoringUtils

logger = logging.getLogger(__name__)

class PersonaAnalyzer:
    """Analyze persona descriptions to extract key characteristics and interests."""
    
    def __init__(self):
        # Common persona categories and their associated keywords
        self.persona_patterns = {
            'profession': {
                'contractor': ['contractor', 'construction', 'building', 'renovation'],
                'chef': ['chef', 'cook', 'culinary', 'kitchen', 'recipe', 'food'],
                'teacher': ['teacher', 'educator', 'instruction', 'student', 'learning'],
                'manager': ['manager', 'management', 'leadership', 'team', 'supervisor'],
                'developer': ['developer', 'programmer', 'software', 'code', 'programming'],
                'designer': ['designer', 'design', 'creative', 'visual', 'graphic'],
                'nurse': ['nurse', 'medical', 'healthcare', 'patient', 'clinical'],
                'consultant': ['consultant', 'consulting', 'advisory', 'expert', 'specialist']
            },
            'domain': {
                'food': ['food', 'cooking', 'nutrition', 'ingredient', 'meal', 'diet'],
                'technology': ['technology', 'software', 'digital', 'computer', 'system'],
                'healthcare': ['health', 'medical', 'wellness', 'treatment', 'care'],
                'education': ['education', 'learning', 'teaching', 'academic', 'training'],
                'business': ['business', 'finance', 'marketing', 'sales', 'strategy'],
                'construction': ['construction', 'building', 'architecture', 'engineering']
            },
            'specialization': {
                'vegetarian': ['vegetarian', 'vegan', 'plant-based', 'meatless'],
                'gluten-free': ['gluten-free', 'celiac', 'wheat-free', 'gluten'],
                'organic': ['organic', 'natural', 'sustainable', 'eco-friendly'],
                'budget': ['budget', 'cost-effective', 'affordable', 'economical'],
                'premium': ['premium', 'luxury', 'high-end', 'quality', 'expensive']
            }
        }
        
    def analyze_persona(self, persona: str) -> Dict[str, List[str]]:
        """
        Analyze persona description to extract key characteristics.
        
        Args:
            persona: Persona description string
            
        Returns:
            Dictionary with categorized persona characteristics
        """
        persona_lower = persona.lower()
        analysis = defaultdict(list)
        
        # Extract keywords from persona
        persona_keywords = TextProcessor.extract_keywords(persona_lower)
        
        # Match against known patterns
        for category, subcategories in self.persona_patterns.items():
            for subcat, keywords in subcategories.items():
                # Check for direct keyword matches
                matches = set(persona_keywords).intersection(set(keywords))
                if matches:
                    analysis[category].append(subcat)
                    
                # Check for phrase matches
                for keyword in keywords:
                    if keyword in persona_lower:
                        if subcat not in analysis[category]:
                            analysis[category].append(subcat)
        
        # Extract custom keywords that might be important
        custom_keywords = [word for word in persona_keywords 
                          if len(word) > 4 and word not in self._get_all_pattern_keywords()]
        if custom_keywords:
            analysis['custom_keywords'] = custom_keywords
            
        return dict(analysis)
    
    def _get_all_pattern_keywords(self) -> Set[str]:
        """Get all keywords from predefined patterns."""
        all_keywords = set()
        for category in self.persona_patterns.values():
            for keywords in category.values():
                all_keywords.update(keywords)
        return all_keywords

class JobAnalyzer:
    """Analyze job descriptions to extract tasks, requirements, and objectives."""
    
    def __init__(self):
        # Common job task patterns
        self.task_patterns = {
            'action_verbs': ['create', 'develop', 'design', 'build', 'make', 'plan', 
                           'organize', 'manage', 'implement', 'execute', 'deliver'],
            'deliverables': ['report', 'plan', 'system', 'program', 'menu', 'strategy', 
                           'solution', 'framework', 'process', 'workflow'],
            'requirements': ['requirement', 'specification', 'criteria', 'standard', 
                           'guideline', 'constraint', 'limitation'],
            'outcomes': ['outcome', 'result', 'goal', 'objective', 'target', 'success']
        }
        
    def analyze_job(self, job: str) -> Dict[str, List[str]]:
        """
        Analyze job description to extract tasks and requirements.
        
        Args:
            job: Job description string
            
        Returns:
            Dictionary with categorized job elements
        """
        job_lower = job.lower()
        analysis = defaultdict(list)
        
        job_keywords = TextProcessor.extract_keywords(job_lower)
        
        # Extract action verbs and tasks
        for category, patterns in self.task_patterns.items():
            matches = set(job_keywords).intersection(set(patterns))
            if matches:
                analysis[category].extend(list(matches))
                
        # Extract specific requirements using regex patterns
        requirements = self._extract_requirements(job)
        if requirements:
            analysis['specific_requirements'].extend(requirements)
            
        # Extract deliverable types
        deliverables = self._extract_deliverables(job)
        if deliverables:
            analysis['deliverable_types'].extend(deliverables)
            
        return dict(analysis)
    
    def _extract_requirements(self, job: str) -> List[str]:
        """Extract specific requirements from job description."""
        requirements = []
        
        # Pattern for requirements with specific attributes
        patterns = [
            r'with ([a-zA-Z\-\s]+) items',  # "with gluten-free items"
            r'for ([a-zA-Z\-\s]+) people',  # "for 50 people"
            r'using ([a-zA-Z\-\s]+) ingredients',  # "using organic ingredients"
            r'(\w+)-free',  # "gluten-free", "dairy-free"
            r'vegetarian|vegan',  # dietary requirements
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, job, re.IGNORECASE)
            requirements.extend([match.strip() for match in matches if isinstance(match, str)])
            
        return requirements
    
    def _extract_deliverables(self, job: str) -> List[str]:
        """Extract deliverable types from job description."""
        deliverables = []
        
        # Common deliverable patterns
        patterns = [
            r'create a ([a-zA-Z\s]+)',
            r'develop ([a-zA-Z\s]+)',
            r'build ([a-zA-Z\s]+)',
            r'design ([a-zA-Z\s]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, job, re.IGNORECASE)
            deliverables.extend([match.strip() for match in matches])
            
        return deliverables

class PersonaJobMatcher:
    """Match personas with jobs and score document relevance."""
    
    def __init__(self):
        self.persona_analyzer = PersonaAnalyzer()
        self.job_analyzer = JobAnalyzer()
        
    def analyze_context(self, persona: str, job: str) -> Dict[str, Any]:
        """
        Analyze persona and job context for matching.
        
        Args:
            persona: Persona description
            job: Job description
            
        Returns:
            Combined context analysis
        """
        persona_analysis = self.persona_analyzer.analyze_persona(persona)
        job_analysis = self.job_analyzer.analyze_job(job)
        
        return {
            'persona': persona_analysis,
            'job': job_analysis,
            'combined_keywords': self._extract_combined_keywords(persona, job),
            'matching_score': self._calculate_persona_job_match(persona_analysis, job_analysis)
        }
    
    def _extract_combined_keywords(self, persona: str, job: str) -> List[str]:
        """Extract and combine keywords from persona and job."""
        persona_keywords = set(TextProcessor.extract_keywords(persona.lower()))
        job_keywords = set(TextProcessor.extract_keywords(job.lower()))
        
        # Prioritize overlapping keywords
        overlap = persona_keywords.intersection(job_keywords)
        unique_persona = persona_keywords - job_keywords
        unique_job = job_keywords - persona_keywords
        
        # Return in priority order
        return list(overlap) + list(unique_persona) + list(unique_job)
    
    def _calculate_persona_job_match(self, persona_analysis: Dict, job_analysis: Dict) -> float:
        """Calculate how well persona matches with job requirements."""
        # Simple matching based on keyword overlap
        persona_terms = set()
        for terms in persona_analysis.values():
            if isinstance(terms, list):
                persona_terms.update(terms)
                
        job_terms = set()
        for terms in job_analysis.values():
            if isinstance(terms, list):
                job_terms.update(terms)
        
        if not persona_terms or not job_terms:
            return 0.0
            
        overlap = len(persona_terms.intersection(job_terms))
        total = len(persona_terms.union(job_terms))
        
        return overlap / total if total > 0 else 0.0
    
    def score_section_relevance(self, section: DocumentSection, 
                               persona: str, job: str,
                               context_analysis: Dict[str, Any] = None) -> float:
        """
        Score how relevant a document section is to the persona and job.
        
        Args:
            section: Document section to score
            persona: Persona description
            job: Job description
            context_analysis: Pre-computed context analysis (optional)
            
        Returns:
            Relevance score between 0 and 1
        """
        if context_analysis is None:
            context_analysis = self.analyze_context(persona, job)
            
        # Extract section keywords
        section_keywords = set(TextProcessor.extract_keywords(section.content.lower()))
        section_title_keywords = set(TextProcessor.extract_keywords(section.section_title.lower()))
        
        # Get priority keywords from context
        priority_keywords = set(context_analysis['combined_keywords'][:10])  # Top 10
        
        # Calculate different types of relevance
        scores = {
            'keyword_overlap': self._calculate_keyword_relevance(
                section_keywords, priority_keywords
            ),
            'title_relevance': self._calculate_keyword_relevance(
                section_title_keywords, priority_keywords
            ),
            'persona_specific': self._calculate_persona_specific_relevance(
                section, context_analysis['persona']
            ),
            'job_specific': self._calculate_job_specific_relevance(
                section, context_analysis['job']
            )
        }
        
        # Weighted combination
        weights = {
            'keyword_overlap': 0.3,
            'title_relevance': 0.2,
            'persona_specific': 0.25,
            'job_specific': 0.25
        }
        
        final_score = sum(weights[key] * score for key, score in scores.items())
        return min(final_score, 1.0)  # Cap at 1.0
    
    def _calculate_keyword_relevance(self, section_keywords: Set[str], 
                                   priority_keywords: Set[str]) -> float:
        """Calculate relevance based on keyword overlap."""
        if not priority_keywords:
            return 0.0
            
        overlap = len(section_keywords.intersection(priority_keywords))
        return overlap / len(priority_keywords)
    
    def _calculate_persona_specific_relevance(self, section: DocumentSection, 
                                            persona_analysis: Dict) -> float:
        """Calculate relevance specific to persona characteristics."""
        content_lower = section.content.lower()
        title_lower = section.section_title.lower()
        combined_text = f"{title_lower} {content_lower}"
        
        relevance_score = 0.0
        total_categories = 0
        
        for category, items in persona_analysis.items():
            if not isinstance(items, list):
                continue
                
            total_categories += 1
            category_score = 0.0
            
            for item in items:
                if isinstance(item, str) and item.lower() in combined_text:
                    category_score += 1.0
                    
            if items:  # Avoid division by zero
                relevance_score += category_score / len(items)
        
        return relevance_score / total_categories if total_categories > 0 else 0.0
    
    def _calculate_job_specific_relevance(self, section: DocumentSection, 
                                        job_analysis: Dict) -> float:
        """Calculate relevance specific to job requirements."""
        content_lower = section.content.lower()
        title_lower = section.section_title.lower()
        combined_text = f"{title_lower} {content_lower}"
        
        relevance_score = 0.0
        total_weight = 0.0
        
        # Weight different job aspects differently
        weights = {
            'action_verbs': 0.2,
            'deliverables': 0.3,
            'specific_requirements': 0.4,
            'deliverable_types': 0.1
        }
        
        for category, items in job_analysis.items():
            if not isinstance(items, list) or category not in weights:
                continue
                
            weight = weights[category]
            total_weight += weight
            
            category_score = 0.0
            for item in items:
                if isinstance(item, str) and item.lower() in combined_text:
                    category_score += 1.0
                    
            if items:  # Avoid division by zero
                relevance_score += weight * (category_score / len(items))
        
        return relevance_score / total_weight if total_weight > 0 else 0.0 