"""Named entity recognition and analysis"""

import re
from collections import defaultdict
from typing import List, Dict

# Optional spaCy import with fallback
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# Assuming this import is in a parent directory or the path is configured
from ..models.schemas import Entity

class EntityExtractor:
    """Extracts and analyzes named entities from article content."""

    def __init__(self):
        """Initializes the entity extractor, loading spaCy if available."""
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                # Load the small English model for NER
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("Warning: spaCy 'en_core_web_sm' model not found. Run 'python -m spacy download en_core_web_sm'. Using regex fallback.")
                self.nlp = None

    async def extract_entities(self, content: str, title: str = None) -> List[Entity]:
        """
        Extracts named entities from content using the best available method.
        """
        if self.nlp:
            return self._extract_with_spacy(content, title)
        else:
            return self._extract_with_regex(content, title)

    def _extract_with_spacy(self, content: str, title: str = None) -> List[Entity]:
        """Extracts entities using the more accurate spaCy library."""
        full_text = f"{title}\n\n{content}" if title else content
        # Limit text length to prevent performance issues with very large articles
        doc = self.nlp(full_text[:100000])

        entities = []
        entity_counts = defaultdict(int)
        
        # Define the entity types we are interested in
        relevant_labels = {'PERSON', 'ORG', 'GPE', 'EVENT', 'LAW', 'PRODUCT', 'WORK_OF_ART'}

        for ent in doc.ents:
            if ent.label_ in relevant_labels:
                clean_text = self._clean_entity_text(ent.text)
                
                if len(clean_text) > 2 and len(clean_text.split()) < 6:  # Filter out noise
                    entity_counts[clean_text] += 1
                    context = self._get_entity_context_spacy(ent)
                    
                    # Simple confidence score based on mention frequency
                    confidence = min(1.0, 0.4 + (entity_counts[clean_text] * 0.15))
                    
                    entities.append(Entity(
                        text=clean_text,
                        label=ent.label_,
                        confidence=confidence,
                        context=context
                    ))

        unique_entities = self._deduplicate_entities(entities)
        # Sort by confidence and then by text length for relevance
        sorted_entities = sorted(unique_entities, key=lambda x: (x.confidence, len(x.text)), reverse=True)
        return sorted_entities[:20] # Return top 20

    def _extract_with_regex(self, content: str, title: str = None) -> List[Entity]:
        """Fallback entity extraction using basic regular expressions."""
        full_text = f"{title}\n\n{content}" if title else content
        entities = []
        
        patterns = {
            'PERSON': [r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'],
            'ORG': [r'\b[A-Z][a-z]+ (?:Corporation|Corp|Company|Inc|LLC|Ltd)\b', r'\b[A-Z]{3,5}\b'],
            'GPE': [r'\b(?:United States|USA|UK|China|India|Russia|Germany|France)\b']
        }

        for label, pattern_list in patterns.items():
            for pattern in pattern_list:
                for match in re.finditer(pattern, full_text):
                    entity_text = self._clean_entity_text(match.group())
                    if len(entity_text) > 2:
                        entities.append(Entity(
                            text=entity_text,
                            label=label,
                            confidence=0.5,  # Fixed lower confidence for regex
                            context=self._get_entity_context_regex(entity_text, full_text)
                        ))

        unique_entities = self._deduplicate_entities(entities)
        return sorted(unique_entities, key=lambda x: len(x.text), reverse=True)[:15]

    def _clean_entity_text(self, text: str) -> str:
        """Cleans and normalizes entity text."""
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove common titles and suffixes
        text = re.sub(r'^(Mr|Mrs|Ms|Dr|Prof)\.\s+', '', text)
        text = re.sub(r'\s+((Inc|Corp|Ltd|LLC)\.?)$', '', text)
        return text

    def _get_entity_context_spacy(self, entity) -> str:
        """Gets the sentence containing the entity from its spaCy object."""
        context = entity.sent.text.strip().replace("\n", " ")
        return (context[:250] + '...') if len(context) > 250 else context

    def _get_entity_context_regex(self, entity_text: str, full_text: str) -> str:
        """Finds the sentence containing the entity text using regex."""
        # A simple sentence splitter
        sentences = re.split(r'(?<=[.!?])\s+', full_text)
        for sentence in sentences:
            if entity_text in sentence:
                context = sentence.strip().replace("\n", " ")
                return (context[:250] + '...') if len(context) > 250 else context
        return ""

    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Removes duplicate or substantially similar entities."""
        merged_entities = {}
        for entity in entities:
            # Normalize for merging (e.g., "U.S." and "United States")
            key = entity.text.lower().strip()
            
            if key not in merged_entities:
                merged_entities[key] = entity
            else:
                # Merge: keep the one with higher confidence
                if entity.confidence > merged_entities[key].confidence:
                    merged_entities[key] = entity
        
        return list(merged_entities.values())

    def analyze_entity_roles(self, entities: List[Entity], content: str) -> Dict[str, List[str]]:
        """Analyzes the roles of entities (e.g., source, subject) in the text."""
        roles = defaultdict(list)
        content_lower = content.lower()

        for entity in entities:
            entity_lower = entity.text.lower()
            
            # Check if entity is cited as a source
            source_indicators = [f"{entity_lower} said", f"according to {entity_lower}", f"{entity_lower} stated"]
            if any(indicator in content_lower for indicator in source_indicators):
                roles['sources'].append(entity.text)
            
            # Categorize by label
            if entity.label == 'ORG' and entity.text not in roles['sources']:
                roles['organizations'].append(entity.text)
            elif entity.label == 'GPE':
                roles['locations'].append(entity.text)
            elif entity.label == 'PERSON' and entity.text not in roles['sources']:
                roles['subjects'].append(entity.text)
        
        return dict(roles)

# Global singleton instance for use in other parts of the application
entity_extractor = EntityExtractor()