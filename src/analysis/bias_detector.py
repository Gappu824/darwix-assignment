"""Advanced bias detection and analysis"""

import re
from typing import List, Dict, Any, Tuple
from collections import Counter

from ..models.schemas import RedFlag, LanguageAnalysis, BiasType, SeverityLevel, ToneType

class BiasDetector:
    """Detect various types of bias in article content"""
    
    def __init__(self):
        # Emotional language indicators
        self.emotional_positive = [
            'amazing', 'fantastic', 'incredible', 'outstanding', 'remarkable',
            'wonderful', 'excellent', 'brilliant', 'spectacular', 'magnificent'
        ]
        
        self.emotional_negative = [
            'terrible', 'awful', 'horrible', 'devastating', 'catastrophic',
            'disastrous', 'shocking', 'outrageous', 'appalling', 'disgusting'
        ]
        
        # Loaded/biased language
        self.loaded_terms = [
            'regime', 'puppet', 'thugs', 'terrorists', 'extremists',
            'fanatics', 'radicals', 'militants', 'cronies', 'lackeys'
        ]
        
        # Persuasive techniques indicators
        self.appeal_to_emotion = [
            'you should be afraid', 'this threatens', 'dangerous consequences',
            'shocking truth', 'hidden agenda', 'they don\'t want you to know'
        ]
        
        self.false_dichotomy = [
            'either...or', 'only two choices', 'must choose between',
            'no middle ground', 'black and white'
        ]
    
    def detect_language_bias(self, content: str, title: str = None) -> LanguageAnalysis:
        """Comprehensive language bias analysis"""
        
        full_text = f"{title}\n{content}" if title else content
        full_text_lower = full_text.lower()
        
        # Detect overall tone
        tone = self._detect_tone(full_text_lower)
        
        # Find bias indicators
        bias_indicators = self._find_bias_indicators(full_text_lower)
        
        # Find loaded language
        loaded_language = self._find_loaded_language(full_text_lower)
        
        # Find emotional words
        emotional_words = self._find_emotional_words(full_text_lower)
        
        # Detect persuasive techniques
        persuasive_techniques = self._detect_persuasive_techniques(full_text_lower)
        
        return LanguageAnalysis(
            tone=tone,
            bias_indicators=bias_indicators,
            loaded_language=loaded_language,
            emotional_words=emotional_words,
            persuasive_techniques=persuasive_techniques
        )
    
    def detect_structural_bias(self, content: str) -> List[RedFlag]:
        """Detect structural and logical bias patterns"""
        
        red_flags = []
        
        # Check for source bias
        source_flags = self._check_source_bias(content)
        red_flags.extend(source_flags)
        
        # Check for statistical misuse
        stat_flags = self._check_statistical_misuse(content)
        red_flags.extend(stat_flags)
        
        # Check for logical fallacies
        logic_flags = self._check_logical_fallacies(content)
        red_flags.extend(logic_flags)
        
        # Check for selection bias
        selection_flags = self._check_selection_bias(content)
        red_flags.extend(selection_flags)
        
        return red_flags
    
    def _detect_tone(self, text: str) -> ToneType:
        """Detect overall tone of the article"""
        
        # Count emotional indicators
        positive_count = sum(1 for word in self.emotional_positive if word in text)
        negative_count = sum(1 for word in self.emotional_negative if word in text)
        loaded_count = sum(1 for term in self.loaded_terms if term in text)
        
        # Count persuasive language
        persuasive_count = sum(1 for phrase in self.appeal_to_emotion if phrase in text)
        
        total_words = len(text.split())
        
        # Calculate ratios
        emotional_ratio = (positive_count + negative_count) / max(total_words / 100, 1)
        loaded_ratio = loaded_count / max(total_words / 100, 1)
        persuasive_ratio = persuasive_count / max(total_words / 100, 1)
        
        # Determine tone based on ratios
        if loaded_ratio > 2 or persuasive_ratio > 1:
            return ToneType.INFLAMMATORY
        elif emotional_ratio > 3 or (negative_count > positive_count * 2):
            return ToneType.EMOTIONAL
        elif persuasive_ratio > 0.5 or emotional_ratio > 1.5:
            return ToneType.PERSUASIVE
        else:
            return ToneType.NEUTRAL
    
    def _find_bias_indicators(self, text: str) -> List[str]:
        """Find specific examples of biased language"""
        
        indicators = []
        
        # Absolute statements
        absolute_patterns = [
            r'\b(always|never|all|none|every|completely|totally|absolutely)\b',
            r'\b(everyone knows|it\'s obvious|clearly|undoubtedly)\b'
        ]
        
        for pattern in absolute_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            indicators.extend([f"Absolute statement: '{match}'" for match in matches])
        
        # Unsubstantiated claims
        claim_patterns = [
            r'(sources say|reports suggest|it is believed|allegedly)',
            r'(many people think|most experts agree|studies show)'
        ]
        
        for pattern in claim_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            indicators.extend([f"Unsubstantiated claim: '{match}'" for match in matches])
        
        # Loaded qualifiers
        loaded_qualifiers = [
            'so-called', 'alleged', 'claimed', 'supposed', 'purported'
        ]
        
        for qualifier in loaded_qualifiers:
            if qualifier in text:
                indicators.append(f"Loaded qualifier: '{qualifier}'")
        
        return indicators[:10]  # Limit to top 10
    
    def _find_loaded_language(self, text: str) -> List[str]:
        """Find emotionally charged or loaded language"""
        
        found_terms = []
        
        # Check predefined loaded terms
        for term in self.loaded_terms:
            if term in text:
                found_terms.append(term)
        
        # Find inflammatory adjectives
        inflammatory_patterns = [
            r'\b(radical|extremist|rogue|reckless|dangerous|toxic|corrupt)\s+\w+',
            r'\b(failed|broken|devastating|crushing|shocking)\s+\w+'
        ]
        
        for pattern in inflammatory_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_terms.extend(matches)
        
        return list(set(found_terms))[:15]  # Unique terms, limit to 15
    
    def _find_emotional_words(self, text: str) -> List[str]:
        """Find emotionally manipulative words"""
        
        emotional_words = []
        
        all_emotional = self.emotional_positive + self.emotional_negative
        
        for word in all_emotional:
            if word in text:
                emotional_words.append(word)
        
        # Additional emotional indicators
        fear_words = ['threat', 'danger', 'risk', 'fear', 'terror', 'crisis', 'emergency']
        anger_words = ['outrage', 'fury', 'anger', 'rage', 'disgusting', 'appalling']
        
        for word in fear_words + anger_words:
            if word in text:
                emotional_words.append(word)
        
        return list(set(emotional_words))[:10]
    
    def _detect_persuasive_techniques(self, text: str) -> List[str]:
        """Detect persuasive techniques and propaganda methods"""
        
        techniques = []
        
        # Appeal to emotion
        for phrase in self.appeal_to_emotion:
            if phrase in text:
                techniques.append(f"Appeal to emotion: {phrase}")
        
        # False dichotomy
        for phrase in self.false_dichotomy:
            if phrase in text:
                techniques.append(f"False dichotomy: {phrase}")
        
        # Bandwagon appeal
        bandwagon_patterns = [
            r'everyone is doing',
            r'most people believe',
            r'join the movement',
            r'don\'t be left behind'
        ]
        
        for pattern in bandwagon_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                techniques.append(f"Bandwagon appeal: {pattern}")
        
        # Authority appeal without credentials
        authority_patterns = [
            r'experts say',
            r'authorities claim',
            r'officials state'
        ]
        
        for pattern in authority_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                techniques.append(f"Vague authority appeal: {pattern}")
        
        return techniques[:8]
    
    def _check_source_bias(self, content: str) -> List[RedFlag]:
        """Check for source-related bias issues"""
        
        flags = []
        
        # Anonymous sources
        anonymous_patterns = [
            r'anonymous sources?',
            r'sources close to',
            r'insider[s]?\s+say',
            r'unnamed official[s]?'
        ]
        
        anonymous_count = 0
        for pattern in anonymous_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            anonymous_count += len(matches)
        
        if anonymous_count > 3:
            flags.append(RedFlag(
                type=BiasType.SOURCE_BIAS,
                description=f"Heavy reliance on anonymous sources ({anonymous_count} instances)",
                severity=SeverityLevel.HIGH,
                evidence="Multiple unnamed sources without verification",
                confidence=0.8
            ))
        elif anonymous_count > 1:
            flags.append(RedFlag(
                type=BiasType.SOURCE_BIAS,
                description=f"Multiple anonymous sources ({anonymous_count} instances)",
                severity=SeverityLevel.MEDIUM,
                evidence="Some unnamed sources present",
                confidence=0.6
            ))
        
        # Single source dependency
        source_diversity = self._analyze_source_diversity(content)
        if source_diversity < 0.3:
            flags.append(RedFlag(
                type=BiasType.SOURCE_BIAS,
                description="Limited source diversity - potential echo chamber",
                severity=SeverityLevel.MEDIUM,
                evidence="Most information comes from similar sources",
                confidence=0.7
            ))
        
        return flags
    
    def _check_statistical_misuse(self, content: str) -> List[RedFlag]:
        """Check for statistical manipulation or misuse"""
        
        flags = []
        
        # Numbers without context
        number_patterns = [
            r'\d+%\s+(?:increase|decrease|rise|fall)',
            r'\$[\d,]+\s+(?:million|billion)',
            r'\d+\s+times\s+(?:more|less|higher|lower)'
        ]
        
        stats_found = 0
        context_found = 0
        
        for pattern in number_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            stats_found += len(matches)
        
        # Check for context indicators
        context_patterns = [
            r'compared to',
            r'baseline',
            r'previous year',
            r'same period',
            r'methodology'
        ]
        
        for pattern in context_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                context_found += 1
        
        if stats_found > 2 and context_found == 0:
            flags.append(RedFlag(
                type=BiasType.STATISTICAL_MISUSE,
                description="Statistics presented without proper context or comparison",
                severity=SeverityLevel.MEDIUM,
                evidence=f"Found {stats_found} statistical claims with minimal context",
                confidence=0.7
            ))
        
        # Cherry-picking indicators
        cherry_pick_patterns = [
            r'record high',
            r'unprecedented',
            r'never before seen',
            r'highest ever'
        ]
        
        cherry_pick_count = 0
        for pattern in cherry_pick_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                cherry_pick_count += 1
        
        if cherry_pick_count > 2:
            flags.append(RedFlag(
                type=BiasType.STATISTICAL_MISUSE,
                description="Potential cherry-picking of extreme statistics",
                severity=SeverityLevel.MEDIUM,
                evidence=f"Multiple 'record' or 'unprecedented' claims ({cherry_pick_count})",
                confidence=0.6
            ))
        
        return flags
    
    def _check_logical_fallacies(self, content: str) -> List[RedFlag]:
        """Check for logical fallacies"""
        
        flags = []
        
        # Ad hominem attacks
        ad_hominem_patterns = [
            r'critics of \w+ are',
            r'only \w+ would',
            r'anyone who believes',
            r'supporters are just'
        ]
        
        for pattern in ad_hominem_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                flags.append(RedFlag(
                    type=BiasType.LOGICAL_FALLACY,
                    description="Potential ad hominem attack - attacking the person rather than the argument",
                    severity=SeverityLevel.MEDIUM,
                    evidence=f"Pattern found: {pattern}",
                    confidence=0.6
                ))
                break
        
        # Straw man arguments
        straw_man_patterns = [
            r'they want to',
            r'their real agenda',
            r'what they really mean'
        ]
        
        for pattern in straw_man_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                flags.append(RedFlag(
                    type=BiasType.LOGICAL_FALLACY,
                    description="Potential straw man argument - misrepresenting opposing views",
                    severity=SeverityLevel.MEDIUM,
                    evidence=f"Pattern found: {pattern}",
                    confidence=0.5
                ))
                break
        
        return flags
    
    def _check_selection_bias(self, content: str) -> List[RedFlag]:
        """Check for selection bias in coverage"""
        
        flags = []
        
        # Missing opposing viewpoints
        opposing_indicators = [
            'however', 'but', 'on the other hand', 'critics argue',
            'opposing view', 'alternative perspective', 'others believe'
        ]
        
        balance_score = sum(1 for indicator in opposing_indicators if indicator in content.lower())
        
        if len(content) > 1000 and balance_score == 0:
            flags.append(RedFlag(
                type=BiasType.SELECTION_BIAS,
                description="No opposing viewpoints or alternative perspectives presented",
                severity=SeverityLevel.HIGH,
                evidence="Article lacks balance in perspective",
                confidence=0.8
            ))
        elif len(content) > 500 and balance_score < 2:
            flags.append(RedFlag(
                type=BiasType.SELECTION_BIAS,
                description="Limited opposing viewpoints presented",
                severity=SeverityLevel.MEDIUM,
                evidence="Minimal alternative perspectives",
                confidence=0.6
            ))
        
        return flags
    
    def _analyze_source_diversity(self, content: str) -> float:
        """Analyze diversity of sources quoted"""
        
        # Simple heuristic based on different source types
        source_types = {
            'government': ['official', 'spokesperson', 'administration', 'department'],
            'expert': ['professor', 'researcher', 'analyst', 'expert'],
            'industry': ['executive', 'company', 'corporation', 'business'],
            'advocacy': ['activist', 'advocate', 'group', 'organization']
        }
        
        found_types = set()
        content_lower = content.lower()
        
        for source_type, keywords in source_types.items():
            if any(keyword in content_lower for keyword in keywords):
                found_types.add(source_type)
        
        return len(found_types) / len(source_types)

# Global bias detector instance
bias_detector = BiasDetector() 
