"""Extract and analyze factual claims from articles"""

import re
from typing import List, Dict, Any, Tuple
from ..models.schemas import Claim, EvidenceQuality

class ClaimExtractor:
    """Extract and analyze factual claims from article content"""
    
    def __init__(self):
        # Patterns that indicate factual claims
        self.factual_indicators = [
            r'according to \w+',
            r'data shows?',
            r'statistics reveal',
            r'study found',
            r'research indicates',
            r'report states',
            r'officials? said',
            r'spokesperson said',
            r'\d+% of',
            r'\$[\d,]+ (?:million|billion)',
            r'\d+ people',
            r'increased by \d+',
            r'decreased by \d+'
        ]
        
        # Evidence quality indicators
        self.strong_evidence = [
            'peer-reviewed', 'published study', 'government data',
            'official statistics', 'verified by', 'confirmed by',
            'documented evidence', 'multiple sources'
        ]
        
        self.moderate_evidence = [
            'study shows', 'research indicates', 'data suggests',
            'report found', 'analysis shows', 'experts say'
        ]
        
        self.weak_evidence = [
            'sources say', 'allegedly', 'reportedly', 'claims',
            'appears to', 'seems to', 'suggests that'
        ]
        
        self.no_evidence = [
            'believes', 'thinks', 'feels', 'opinion', 'speculation',
            'rumors', 'unconfirmed', 'without evidence'
        ]
    
    def extract_claims(self, content: str, title: str = None) -> List[Claim]:
        """Extract factual claims from article content"""
        
        full_text = f"{title}\n{content}" if title else content
        
        # Split into sentences
        sentences = self._split_into_sentences(full_text)
        
        claims = []
        
        for sentence in sentences:
            # Check if sentence contains factual claims
            if self._contains_factual_claim(sentence):
                claim = self._analyze_claim(sentence)
                if claim and len(claim.claim.strip()) > 20:  # Filter very short claims
                    claims.append(claim)
        
        # Remove duplicates and rank by importance
        unique_claims = self._deduplicate_claims(claims)
        ranked_claims = self._rank_claims(unique_claims)
        
        return ranked_claims[:8]  # Return top 8 claims
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences intelligently"""
        
        # Simple sentence splitting (can be improved with spaCy)
        sentences = re.split(r'[.!?]+', text)
        
        # Clean and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and not sentence.startswith(('http', 'www')):
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _contains_factual_claim(self, sentence: str) -> bool:
        """Check if sentence contains a factual claim"""
        
        sentence_lower = sentence.lower()
        
        # Check for factual indicators
        for pattern in self.factual_indicators:
            if re.search(pattern, sentence_lower):
                return True
        
        # Check for numbers/statistics
        if re.search(r'\d+', sentence) and len(sentence) > 30:
            return True
        
        # Check for definitive statements
        definitive_patterns = [
            r'will \w+',
            r'has \w+ed',
            r'have \w+ed',
            r'is \w+ing',
            r'are \w+ing'
        ]
        
        for pattern in definitive_patterns:
            if re.search(pattern, sentence_lower):
                return True
        
        return False
    
    def _analyze_claim(self, sentence: str) -> Claim:
        """Analyze a single claim for evidence quality and verifiability"""
        
        sentence_lower = sentence.lower()
        
        # Assess evidence quality
        evidence_quality = self._assess_evidence_quality(sentence_lower)
        
        # Assess verifiability
        verifiable = self._assess_verifiability(sentence_lower)
        
        # Calculate confidence based on multiple factors
        confidence = self._calculate_claim_confidence(sentence_lower, evidence_quality, verifiable)
        
        # Extract context (surrounding information)
        context = self._extract_claim_context(sentence)
        
        return Claim(
            claim=sentence.strip(),
            evidence_quality=evidence_quality,
            verifiable=verifiable,
            context=context,
            confidence=confidence
        )
    
    def _assess_evidence_quality(self, sentence: str) -> EvidenceQuality:
        """Assess the quality of evidence supporting a claim"""
        
        # Check for strong evidence indicators
        for indicator in self.strong_evidence:
            if indicator in sentence:
                return EvidenceQuality.STRONG
        
        # Check for moderate evidence indicators
        for indicator in self.moderate_evidence:
            if indicator in sentence:
                return EvidenceQuality.MODERATE
        
        # Check for weak evidence indicators
        for indicator in self.weak_evidence:
            if indicator in sentence:
                return EvidenceQuality.WEAK
        
        # Check for no evidence indicators
        for indicator in self.no_evidence:
            if indicator in sentence:
                return EvidenceQuality.NONE
        
        # Default assessment based on structure
        if re.search(r'according to|data|study|research', sentence):
            return EvidenceQuality.MODERATE
        elif re.search(r'said|stated|announced', sentence):
            return EvidenceQuality.WEAK
        else:
            return EvidenceQuality.NONE
    
    def _assess_verifiability(self, sentence: str) -> bool:
        """Assess whether a claim is verifiable"""
        
        # Verifiable indicators
        verifiable_patterns = [
            r'\d+%',  # Percentages
            r'\$[\d,]+',  # Money amounts
            r'\d+ (?:people|cases|instances)',  # Counts
            r'(?:january|february|march|april|may|june|july|august|september|october|november|december)',  # Dates
            r'\d{4}',  # Years
            r'government data',
            r'official statistics',
            r'public records'
        ]
        
        for pattern in verifiable_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                return True
        
        # Non-verifiable indicators
        non_verifiable = [
            'believes', 'thinks', 'feels', 'opinion', 'speculation',
            'rumors', 'allegedly', 'reportedly', 'sources say'
        ]
        
        for indicator in non_verifiable:
            if indicator in sentence:
                return False
        
        # Default: assume moderately verifiable if it contains specific nouns
        if re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', sentence):  # Proper nouns
            return True
        
        return False
    
    def _calculate_claim_confidence(self, sentence: str, evidence_quality: EvidenceQuality, verifiable: bool) -> float:
        """Calculate confidence score for a claim"""
        
        base_confidence = 0.3
        
        # Evidence quality contribution
        evidence_scores = {
            EvidenceQuality.STRONG: 0.4,
            EvidenceQuality.MODERATE: 0.25,
            EvidenceQuality.WEAK: 0.1,
            EvidenceQuality.NONE: 0.0
        }
        
        base_confidence += evidence_scores[evidence_quality]
        
        # Verifiability contribution
        if verifiable:
            base_confidence += 0.2
        
        # Specificity bonus
        if re.search(r'\d+', sentence):  # Contains numbers
            base_confidence += 0.1
        
        if re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', sentence):  # Proper nouns
            base_confidence += 0.05
        
        # Uncertainty penalty
        uncertainty_indicators = ['might', 'could', 'may', 'possibly', 'perhaps', 'allegedly']
        for indicator in uncertainty_indicators:
            if indicator in sentence:
                base_confidence -= 0.1
                break
        
        return min(1.0, max(0.0, base_confidence))
    
    def _extract_claim_context(self, sentence: str) -> str:
        """Extract relevant context for a claim"""
        
        # For now, return a cleaned version of the sentence
        # In a more sophisticated version, this would include surrounding sentences
        
        context = sentence.strip()
        
        # Remove common prefixes that don't add context
        context = re.sub(r'^(However,|But,|And,|So,|Then,)\s*', '', context)
        
        # Truncate if too long
        if len(context) > 200:
            context = context[:197] + "..."
        
        return context
    
    def _deduplicate_claims(self, claims: List[Claim]) -> List[Claim]:
        """Remove duplicate or very similar claims"""
        
        unique_claims = []
        seen_claims = set()
        
        for claim in claims:
            # Create a simplified version for comparison
            simplified = re.sub(r'[^\w\s]', '', claim.claim.lower())
            simplified = ' '.join(simplified.split())
            
            # Check for similarity with existing claims
            is_duplicate = False
            for seen in seen_claims:
                if self._claims_similar(simplified, seen):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_claims.append(claim)
                seen_claims.add(simplified)
        
        return unique_claims
    
    def _claims_similar(self, claim1: str, claim2: str) -> bool:
        """Check if two claims are similar"""
        
        words1 = set(claim1.split())
        words2 = set(claim2.split())
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        
        return similarity > 0.7  # 70% similarity threshold
    
    def _rank_claims(self, claims: List[Claim]) -> List[Claim]:
        """Rank claims by importance and credibility"""
        
        def claim_score(claim: Claim) -> float:
            score = claim.confidence
            
            # Boost claims with strong evidence
            if claim.evidence_quality == EvidenceQuality.STRONG:
                score += 0.3
            elif claim.evidence_quality == EvidenceQuality.MODERATE:
                score += 0.1
            
            # Boost verifiable claims
            if claim.verifiable:
                score += 0.2
            
            # Boost claims with numbers/statistics
            if re.search(r'\d+', claim.claim):
                score += 0.1
            
            # Boost longer, more detailed claims
            if len(claim.claim) > 100:
                score += 0.05
            
            return score
        
        return sorted(claims, key=claim_score, reverse=True)
    
    def analyze_claim_patterns(self, claims: List[Claim]) -> Dict[str, Any]:
        """Analyze patterns in the extracted claims"""
        
        analysis = {
            'total_claims': len(claims),
            'verifiable_claims': sum(1 for claim in claims if claim.verifiable),
            'evidence_distribution': {
                'strong': sum(1 for claim in claims if claim.evidence_quality == EvidenceQuality.STRONG),
                'moderate': sum(1 for claim in claims if claim.evidence_quality == EvidenceQuality.MODERATE),
                'weak': sum(1 for claim in claims if claim.evidence_quality == EvidenceQuality.WEAK),
                'none': sum(1 for claim in claims if claim.evidence_quality == EvidenceQuality.NONE)
            },
            'average_confidence': sum(claim.confidence for claim in claims) / len(claims) if claims else 0,
            'statistical_claims': sum(1 for claim in claims if re.search(r'\d+', claim.claim)),
            'high_confidence_claims': sum(1 for claim in claims if claim.confidence > 0.7)
        }
        
        return analysis

# Global claim extractor instance
claim_extractor = ClaimExtractor() 
