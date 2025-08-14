"""Generate counter-narratives and opposing viewpoints"""

from typing import List, Dict, Any, Optional
from ..models.schemas import CounterNarrative, Claim, AnalysisResult

class CounterNarrativeGenerator:
    """Generate opposing viewpoints and alternative perspectives"""
    
    def __init__(self):
        # Common opposing perspective patterns
        self.perspective_frameworks = {
            'economic': {
                'liberal': 'conservative economic perspective',
                'conservative': 'progressive economic perspective',
                'keywords': ['economy', 'jobs', 'business', 'market', 'trade']
            },
            'political': {
                'left': 'right-wing political perspective',
                'right': 'left-wing political perspective',
                'keywords': ['government', 'policy', 'politics', 'election', 'vote']
            },
            'social': {
                'progressive': 'traditional social perspective',
                'traditional': 'progressive social perspective',
                'keywords': ['social', 'community', 'rights', 'equality', 'justice']
            },
            'environmental': {
                'pro-environment': 'industry-focused perspective',
                'pro-industry': 'environmental protection perspective',
                'keywords': ['environment', 'climate', 'energy', 'pollution', 'green']
            }
        }
    
    def generate_counter_narrative(self, analysis_result: AnalysisResult) -> Optional[CounterNarrative]:
        """Generate a comprehensive counter-narrative"""
        
        content = analysis_result.article.content
        claims = analysis_result.core_claims
        
        # Identify the dominant perspective
        dominant_perspective = self._identify_dominant_perspective(content, claims)
        
        # Generate opposing viewpoint
        opposing_viewpoint = self._generate_opposing_viewpoint(content, dominant_perspective)
        
        # Generate alternative explanations
        alternative_explanations = self._generate_alternative_explanations(claims)
        
        # Identify missing context
        missing_context = self._identify_missing_context(content, claims)
        
        # Generate potential rebuttals
        potential_rebuttals = self._generate_rebuttals(claims)
        
        if opposing_viewpoint:
            return CounterNarrative(
                opposing_viewpoint=opposing_viewpoint,
                alternative_explanations=alternative_explanations,
                missing_context=missing_context,
                potential_rebuttals=potential_rebuttals
            )
        
        return None
    
    def _identify_dominant_perspective(self, content: str, claims: List[Claim]) -> Dict[str, Any]:
        """Identify the dominant ideological perspective in the article"""
        
        content_lower = content.lower()
        perspective_scores = {}
        
        # Analyze content for perspective indicators
        for framework_name, framework in self.perspective_frameworks.items():
            score = 0
            
            # Check for keywords
            for keyword in framework['keywords']:
                score += content_lower.count(keyword)
            
            perspective_scores[framework_name] = score
        
        # Determine dominant framework
        dominant_framework = max(perspective_scores, key=perspective_scores.get)
        
        # Analyze specific bias direction within framework
        bias_direction = self._analyze_bias_direction(content_lower, dominant_framework)
        
        return {
            'framework': dominant_framework,
            'direction': bias_direction,
            'confidence': perspective_scores[dominant_framework] / max(sum(perspective_scores.values()), 1)
        }
    
    def _analyze_bias_direction(self, content: str, framework: str) -> str:
        """Analyze the specific bias direction within a framework"""
        
        if framework == 'economic':
            pro_business = ['free market', 'competition', 'business', 'profit', 'growth']
            pro_regulation = ['regulation', 'worker rights', 'inequality', 'wealth gap']
            
            business_score = sum(1 for term in pro_business if term in content)
            regulation_score = sum(1 for term in pro_regulation if term in content)
            
            return 'pro-business' if business_score > regulation_score else 'pro-regulation'
        
        elif framework == 'political':
            conservative_terms = ['tradition', 'law and order', 'security', 'defense']
            liberal_terms = ['progress', 'reform', 'change', 'innovation']
            
            conservative_score = sum(1 for term in conservative_terms if term in content)
            liberal_score = sum(1 for term in liberal_terms if term in content)
            
            return 'conservative' if conservative_score > liberal_score else 'liberal'
        
        elif framework == 'environmental':
            pro_env = ['protect', 'sustainable', 'clean', 'renewable']
            pro_industry = ['jobs', 'economic impact', 'cost', 'practical']
            
            env_score = sum(1 for term in pro_env if term in content)
            industry_score = sum(1 for term in pro_industry if term in content)
            
            return 'pro-environment' if env_score > industry_score else 'pro-industry'
        
        return 'neutral'
    
    def _generate_opposing_viewpoint(self, content: str, perspective: Dict[str, Any]) -> str:
        """Generate an opposing viewpoint based on the identified perspective"""
        
        framework = perspective['framework']
        direction = perspective['direction']
        
        opposing_templates = {
            'economic_pro-business': "From a worker advocacy perspective, this article may overemphasize business interests while downplaying worker concerns, environmental costs, and social inequality. Alternative viewpoints might focus on living wages, worker protections, and sustainable business practices.",
            
            'economic_pro-regulation': "From a free-market perspective, this article may overstate the benefits of regulation while ignoring market efficiency, innovation incentives, and economic growth potential. Critics might argue for reduced government intervention and market-based solutions.",
            
            'political_conservative': "From a progressive perspective, this article may reflect traditional viewpoints that resist necessary social change. Alternative views might emphasize the need for reform, social justice, and addressing systemic inequalities.",
            
            'political_liberal': "From a conservative perspective, this article may promote rapid changes without considering traditional values, established institutions, and potential unintended consequences. Critics might advocate for measured, proven approaches.",
            
            'environmental_pro-environment': "From an industry perspective, this article may overstate environmental risks while underestimating economic impacts on jobs, communities, and global competitiveness. Critics might emphasize technological solutions and balanced approaches.",
            
            'environmental_pro-industry': "From an environmental perspective, this article may prioritize short-term economic gains over long-term sustainability and public health. Critics might emphasize climate urgency and the true cost of environmental damage."
        }
        
        template_key = f"{framework}_{direction}"
        return opposing_templates.get(template_key, "Alternative perspectives might challenge the assumptions and conclusions presented in this article.")
    
    def _generate_alternative_explanations(self, claims: List[Claim]) -> List[str]:
        """Generate alternative explanations for the main claims"""
        
        alternatives = []
        
        for claim in claims[:3]:  # Focus on top 3 claims
            claim_text = claim.claim.lower()
            
            # Economic claims
            if any(term in claim_text for term in ['economy', 'jobs', 'unemployment', 'growth']):
                alternatives.append("Economic trends may be influenced by multiple factors including global markets, technological changes, and cyclical patterns not addressed in the original analysis.")
            
            # Statistical claims
            if any(char.isdigit() for char in claim.claim) and '%' in claim.claim:
                alternatives.append("Statistical increases/decreases may reflect measurement changes, seasonal variations, or different baseline comparisons rather than fundamental trends.")
            
            # Policy claims
            if any(term in claim_text for term in ['policy', 'law', 'regulation', 'government']):
                alternatives.append("Policy impacts may vary significantly across different demographics, regions, or timeframes, with both intended and unintended consequences.")
            
            # Social claims
            if any(term in claim_text for term in ['people', 'community', 'social', 'public']):
                alternatives.append("Social phenomena often have complex, multifaceted causes that may not be fully captured in a single narrative or study.")
        
        # Remove duplicates and limit
        unique_alternatives = list(set(alternatives))
        return unique_alternatives[:4]
    
    def _identify_missing_context(self, content: str, claims: List[Claim]) -> List[str]:
        """Identify potentially missing context or perspectives"""
        
        missing_context = []
        content_lower = content.lower()
        
        # Check for missing temporal context
        if not any(term in content_lower for term in ['historical', 'previous', 'past', 'trend']):
            missing_context.append("Historical context and long-term trends that might provide perspective on current events")
        
        # Check for missing stakeholder perspectives
        stakeholder_groups = ['workers', 'consumers', 'businesses', 'communities', 'experts', 'critics']
        mentioned_stakeholders = [group for group in stakeholder_groups if group in content_lower]
        
        if len(mentioned_stakeholders) < 3:
            missing_context.append("Perspectives from additional stakeholder groups who may be affected by or have expertise on this issue")
        
        # Check for missing comparative context
        if not any(term in content_lower for term in ['compared to', 'similar', 'other countries', 'international']):
            missing_context.append("Comparative analysis with similar situations in other contexts or jurisdictions")
        
        # Check for missing uncertainty acknowledgment
        if not any(term in content_lower for term in ['uncertain', 'unclear', 'debate', 'controversy']):
            missing_context.append("Acknowledgment of uncertainties, limitations, or ongoing debates around this topic")
        
        # Check for missing cost-benefit analysis
        has_benefits = any(term in content_lower for term in ['benefit', 'advantage', 'positive', 'improvement'])
        has_costs = any(term in content_lower for term in ['cost', 'disadvantage', 'negative', 'problem'])
        
        if has_benefits and not has_costs:
            missing_context.append("Discussion of potential costs, risks, or negative consequences")
        elif has_costs and not has_benefits:
            missing_context.append("Discussion of potential benefits or positive outcomes")
        
        return missing_context[:5]
    
    def _generate_rebuttals(self, claims: List[Claim]) -> List[str]:
        """Generate potential rebuttals to the main claims"""
        
        rebuttals = []
        
        for claim in claims[:3]:  # Focus on top 3 claims
            claim_text = claim.claim.lower()
            
            # Challenge methodology
            if claim.evidence_quality.value in ['weak', 'none']:
                rebuttals.append(f"The claim about {self._extract_key_subject(claim.claim)} lacks sufficient evidence and could be challenged on methodological grounds.")
            
            # Challenge causation vs correlation
            if any(term in claim_text for term in ['cause', 'because', 'due to', 'result']):
                rebuttals.append("Critics might argue that correlation does not imply causation and that alternative causal explanations should be considered.")
            
            # Challenge sample size or scope
            if any(term in claim_text for term in ['study', 'survey', 'poll', 'research']):
                rebuttals.append("Questions could be raised about the study's sample size, methodology, or generalizability to broader populations.")
            
            # Challenge timing and context
            if any(term in claim_text for term in ['recent', 'new', 'latest', 'current']):
                rebuttals.append("Critics might argue that recent data points may not represent long-term trends or may be influenced by temporary factors.")
        
        # Add general rebuttals based on content analysis
        rebuttals.extend([
            "Alternative data sources or methodologies might yield different conclusions",
            "The framing of the issue may influence how the facts are interpreted"
        ])
        
        return list(set(rebuttals[:5]))  # Remove duplicates and limit
    
    def _extract_key_subject(self, claim: str) -> str:
        """Extract the key subject from a claim for rebuttal generation"""
        
        # Simple extraction of key nouns (can be improved with NLP)
        import re
        
        # Remove common words and extract potential subjects
        words = claim.split()
        
        # Look for capitalized words (proper nouns) or important keywords
        subjects = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if (clean_word and 
                (clean_word[0].isupper() or 
                 clean_word.lower() in ['economy', 'government', 'policy', 'people', 'study', 'report'])):
                subjects.append(clean_word.lower())
        
        return subjects[0] if subjects else 'the topic'
    
    def analyze_narrative_balance(self, content: str) -> Dict[str, Any]:
        """Analyze the balance of perspectives in the narrative"""
        
        content_lower = content.lower()
        
        # Count positive vs negative framing
        positive_words = ['success', 'improvement', 'benefit', 'progress', 'achievement', 'positive']
        negative_words = ['problem', 'crisis', 'failure', 'decline', 'negative', 'concern']
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        # Count different perspective indicators
        perspective_indicators = {
            'supporters': ['supporters', 'advocates', 'proponents', 'those who favor'],
            'critics': ['critics', 'opponents', 'those who oppose', 'skeptics'],
            'experts': ['experts', 'researchers', 'analysts', 'specialists'],
            'officials': ['officials', 'authorities', 'government', 'administration']
        }
        
        perspective_counts = {}
        for group, terms in perspective_indicators.items():
            perspective_counts[group] = sum(1 for term in terms if term in content_lower)
        
        return {
            'sentiment_balance': {
                'positive': positive_count,
                'negative': negative_count,
                'ratio': positive_count / max(negative_count, 1)
            },
            'perspective_diversity': perspective_counts,
            'total_perspectives': sum(1 for count in perspective_counts.values() if count > 0),
            'dominant_perspective': max(perspective_counts, key=perspective_counts.get) if perspective_counts else None
        }

# Global counter-narrative generator instance
counter_narrative_generator = CounterNarrativeGenerator() 
