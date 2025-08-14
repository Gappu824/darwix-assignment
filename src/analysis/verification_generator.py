"""Generate verification questions for fact-checking"""

import re
from typing import List, Dict, Any
from ..models.schemas import VerificationQuestion, Claim, Entity

class VerificationQuestionGenerator:
    """Generate specific, actionable verification questions"""
    
    def __init__(self):
        # Question templates for different types of claims
        self.question_templates = {
            'statistical': [
                "What is the original source of the {statistic} statistic?",
                "How was the {statistic} data collected and by whom?",
                "What time period does the {statistic} figure cover?",
                "Are there other credible sources that confirm this {statistic}?"
            ],
            'quote': [
                "Can this quote be verified from the original source?",
                "What was the full context of this statement?",
                "When and where was this statement made?",
                "Has the speaker clarified or modified this statement since?"
            ],
            'factual': [
                "What independent sources confirm this claim?",
                "What evidence supports this assertion?",
                "Are there credible sources that contradict this claim?",
                "What additional context might change how this fact is interpreted?"
            ],
            'causal': [
                "What evidence supports this causal relationship?",
                "What alternative explanations might account for this outcome?",
                "What experts in this field say about this relationship?",
                "What prior research exists on this causal claim?"
            ],
            'source_credibility': [
                "What are this source's credentials and potential biases?",
                "What is this organization's funding source and agenda?",
                "What is this person's expertise in this specific area?",
                "What conflicts of interest might this source have?"
            ]
        }
        
        # Research tip templates
        self.research_tips = {
            'fact_checking': [
                "Check fact-checking sites like Snopes, FactCheck.org, or PolitiFact",
                "Search for the original source document or statement",
                "Look for peer-reviewed research on the topic",
                "Check multiple news sources with different editorial perspectives"
            ],
            'statistical': [
                "Find the original study or survey methodology",
                "Check if the data has been peer-reviewed",
                "Look for sample size and margin of error information",
                "Verify if the statistic is being used in proper context"
            ],
            'source_verification': [
                "Research the organization's funding sources",
                "Check the expert's publication history and credentials",
                "Look for disclosure of conflicts of interest",
                "Verify quotes by finding the original context"
            ]
        }

    def generate_verification_questions(self, claims: List[Claim], entities: List[Entity], 
                                      content: str, domain: str) -> List[VerificationQuestion]:
        """Generate comprehensive verification questions"""
        
        questions = []
        
        # Generate questions for claims
        for claim in claims[:5]:  # Focus on top 5 claims
            claim_questions = self._generate_claim_questions(claim)
            questions.extend(claim_questions)
        
        # Generate questions for key entities
        entity_questions = self._generate_entity_questions(entities[:10])
        questions.extend(entity_questions)
        
        # Generate source-specific questions
        source_questions = self._generate_source_questions(domain, content)
        questions.extend(source_questions)
        
        # Generate context questions
        context_questions = self._generate_context_questions(content)
        questions.extend(context_questions)
        
        # Remove duplicates and rank by priority
        unique_questions = self._deduplicate_questions(questions)
        ranked_questions = self._rank_questions(unique_questions)
        
        return ranked_questions[:8]  # Return top 8 questions
    
    def _generate_claim_questions(self, claim: Claim) -> List[VerificationQuestion]:
        """Generate questions specific to a claim"""
        
        questions = []
        claim_text = claim.claim.lower()
        
        # Identify claim type and generate appropriate questions
        if re.search(r'\d+%|\$[\d,]+|\d+ (?:people|percent)', claim.claim):
            # Statistical claim
            statistic = self._extract_statistic(claim.claim)
            questions.extend(self._create_statistical_questions(statistic, claim))
        
        elif '"' in claim.claim or 'said' in claim_text:
            # Quote or statement
            questions.extend(self._create_quote_questions(claim))
        
        elif any(word in claim_text for word in ['cause', 'because', 'due to', 'result']):
            # Causal claim
            questions.extend(self._create_causal_questions(claim))
        
        else:
            # General factual claim
            questions.extend(self._create_factual_questions(claim))
        
        return questions
    
    def _create_statistical_questions(self, statistic: str, claim: Claim) -> List[VerificationQuestion]:
        """Create questions for statistical claims"""
        
        questions = []
        
        base_questions = [
            f"What is the source of the '{statistic}' statistic mentioned?",
            f"How was the data for '{statistic}' collected and verified?",
            f"What time period and sample size does the '{statistic}' represent?",
            f"Do other credible sources report similar figures for '{statistic}'?"
        ]
        
        for i, q_text in enumerate(base_questions):
            questions.append(VerificationQuestion(
                question=q_text,
                category="statistical",
                priority=4 if i < 2 else 3,
                research_tips=self.research_tips['statistical'][:2]
            ))
        
        return questions
    
    def _create_quote_questions(self, claim: Claim) -> List[VerificationQuestion]:
        """Create questions for quotes and statements"""
        
        questions = []
        
        # Extract the speaker if possible
        speaker = self._extract_speaker(claim.claim)
        
        base_questions = [
            f"Can this quote from {speaker or 'the source'} be verified in its original context?",
            f"When and in what forum did {speaker or 'this person'} make this statement?",
            f"Has {speaker or 'the speaker'} made any clarifications about this statement?",
            "What was the full context surrounding this quote?"
        ]
        
        for i, q_text in enumerate(base_questions):
            questions.append(VerificationQuestion(
                question=q_text,
                category="quote",
                priority=5 if i == 0 else 3,
                research_tips=["Search for the original speech, interview, or document", 
                             "Check the speaker's official statements or social media"]
            ))
        
        return questions
    
    def _create_causal_questions(self, claim: Claim) -> List[VerificationQuestion]:
        """Create questions for causal claims"""
        
        questions = []
        
        cause_effect = self._extract_cause_effect(claim.claim)
        
        base_questions = [
            f"What evidence supports the claim that {cause_effect['cause']} causes {cause_effect['effect']}?",
            f"What alternative explanations exist for {cause_effect['effect']}?",
            f"What do experts say about the relationship between {cause_effect['cause']} and {cause_effect['effect']}?",
            "What prior research exists on this causal relationship?"
        ]
        
        for i, q_text in enumerate(base_questions):
            questions.append(VerificationQuestion(
                question=q_text,
                category="causal",
                priority=4 if i < 2 else 3,
                research_tips=["Look for peer-reviewed studies on causation",
                             "Check for correlation vs. causation discussion"]
            ))
        
        return questions
    
    def _create_factual_questions(self, claim: Claim) -> List[VerificationQuestion]:
        """Create questions for general factual claims"""
        
        questions = []
        
        key_subject = self._extract_key_subject(claim.claim)
        
        base_questions = [
            f"What independent sources can verify the claims about {key_subject}?",
            f"What additional context about {key_subject} might be relevant?",
            f"Are there credible sources that present different information about {key_subject}?",
            f"What experts or authorities have commented on {key_subject}?"
        ]
        
        for i, q_text in enumerate(base_questions):
            questions.append(VerificationQuestion(
                question=q_text,
                category="factual",
                priority=3,
                research_tips=self.research_tips['fact_checking'][:2]
            ))
        
        return questions
    
    def _generate_entity_questions(self, entities: List[Entity]) -> List[VerificationQuestion]:
        """Generate questions about key entities"""
        
        questions = []
        
        # Focus on organizations and people
        key_entities = [e for e in entities if e.label in ['PERSON', 'ORG']][:5]
        
        for entity in key_entities:
            if entity.label == 'ORG':
                questions.append(VerificationQuestion(
                    question=f"What is {entity.text}'s funding source, ownership, and potential biases?",
                    category="source",
                    priority=4,
                    research_tips=["Check the organization's website for funding information",
                                 "Look up the organization's history and leadership"]
                ))
            
            elif entity.label == 'PERSON':
                questions.append(VerificationQuestion(
                    question=f"What are {entity.text}'s credentials and potential conflicts of interest on this topic?",
                    category="source",
                    priority=3,
                    research_tips=["Research the person's background and expertise",
                                 "Check for disclosed conflicts of interest"]
                ))
        
        return questions
    
    def _generate_source_questions(self, domain: str, content: str) -> List[VerificationQuestion]:
        """Generate questions about the source publication"""
        
        questions = []
        
        # General source credibility questions
        questions.append(VerificationQuestion(
            question=f"What is {domain}'s editorial stance, ownership, and funding sources?",
            category="source",
            priority=4,
            research_tips=["Check media bias rating sites",
                         "Research the publication's ownership structure"]
        ))
        
        # Article-specific questions
        if 'study' in content.lower() or 'research' in content.lower():
            questions.append(VerificationQuestion(
                question="Can the studies or research mentioned be independently verified?",
                category="methodology",
                priority=5,
                research_tips=["Find the original study publication",
                             "Check if the study was peer-reviewed"]
            ))
        
        return questions
    
    def _generate_context_questions(self, content: str) -> List[VerificationQuestion]:
        """Generate questions about missing context"""
        
        questions = []
        content_lower = content.lower()
        
        # Check for missing historical context
        if not any(term in content_lower for term in ['historical', 'previously', 'past']):
            questions.append(VerificationQuestion(
                question="What historical context or trends might provide perspective on this issue?",
                category="context",
                priority=2,
                research_tips=["Research the historical background of this issue",
                             "Look for long-term trend data"]
            ))
        
        # Check for missing comparative context
        if not any(term in content_lower for term in ['compared', 'other countries', 'similar']):
            questions.append(VerificationQuestion(
                question="How does this situation compare to similar cases in other contexts?",
                category="context",
                priority=2,
                research_tips=["Look for international comparisons",
                             "Research similar cases in other jurisdictions"]
            ))
        
        return questions
    
    def _extract_statistic(self, text: str) -> str:
        """Extract the main statistic from a claim"""
        
        # Look for percentages, dollar amounts, or numbers with units
        patterns = [
            r'\d+%',
            r'\$[\d,]+(?:\s+(?:million|billion|trillion))?',
            r'\d+\s+(?:people|percent|times|years|months|days)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        
        return "the statistic"
    
    def _extract_speaker(self, text: str) -> str:
        """Extract the speaker from a quote"""
        
        # Look for patterns like "John Smith said" or "according to Jane Doe"
        patterns = [
            r'([A-Z][a-z]+ [A-Z][a-z]+)\s+(?:said|stated|told|announced)',
            r'according to ([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+(?:a|the)?\s*\w+,?\s+(?:said|stated)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_cause_effect(self, text: str) -> Dict[str, str]:
        """Extract cause and effect from causal claims"""
        
        # Simple extraction based on causal keywords
        if 'because' in text.lower():
            parts = text.lower().split('because')
            return {'effect': parts[0].strip(), 'cause': parts[1].strip()}
        
        elif 'due to' in text.lower():
            parts = text.lower().split('due to')
            return {'effect': parts[0].strip(), 'cause': parts[1].strip()}
        
        else:
            return {'cause': 'the stated cause', 'effect': 'the stated effect'}
    
    def _extract_key_subject(self, text: str) -> str:
        """Extract the main subject of a claim"""
        
        # Look for proper nouns or key terms
        words = text.split()
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word and clean_word[0].isupper() and len(clean_word) > 3:
                return clean_word.lower()
        
        # Fallback to common important terms
        important_terms = ['government', 'economy', 'policy', 'study', 'report', 'data']
        for term in important_terms:
            if term in text.lower():
                return term
        
        return 'this topic'
    
    def _deduplicate_questions(self, questions: List[VerificationQuestion]) -> List[VerificationQuestion]:
        """Remove duplicate questions"""
        
        seen_questions = set()
        unique_questions = []
        
        for question in questions:
            # Create a normalized version for comparison
            normalized = ' '.join(question.question.lower().split())
            
            if normalized not in seen_questions:
                seen_questions.add(normalized)
                unique_questions.append(question)
        
        return unique_questions
    
    def _rank_questions(self, questions: List[VerificationQuestion]) -> List[VerificationQuestion]:
        """Rank questions by priority and importance"""
        
        return sorted(questions, key=lambda q: (q.priority, len(q.research_tips)), reverse=True)

# Global verification question generator instance
verification_generator = VerificationQuestionGenerator()