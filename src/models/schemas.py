from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field
from enum import Enum

class BiasType(str, Enum):
    SOURCE_BIAS = "source_bias"
    STATISTICAL_MISUSE = "statistical_misuse"
    LOGICAL_FALLACY = "logical_fallacy"
    SELECTION_BIAS = "selection_bias"
    FRAMING_BIAS = "framing_bias"
    EMOTIONAL_MANIPULATION = "emotional_manipulation"

class SeverityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class EvidenceQuality(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NONE = "none"

class ToneType(str, Enum):
    NEUTRAL = "neutral"
    PERSUASIVE = "persuasive"
    EMOTIONAL = "emotional"
    INFLAMMATORY = "inflammatory"

class ArticleContent(BaseModel):
    """Extracted article content with metadata"""
    url: str
    title: Optional[str] = None
    content: str
    author: Optional[str] = None
    publish_date: Optional[str] = None
    domain: str
    language: Optional[str] = None
    quality_score: float = Field(ge=0.0, le=1.0)
    extraction_method: str

class Entity(BaseModel):
    """Named entity with context"""
    text: str
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    context: Optional[str] = None

class Claim(BaseModel):
    """Individual factual claim"""
    claim: str
    evidence_quality: EvidenceQuality
    verifiable: bool
    context: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)

class RedFlag(BaseModel):
    """Potential bias or credibility issue"""
    type: BiasType
    description: str
    severity: SeverityLevel
    evidence: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)

class LanguageAnalysis(BaseModel):
    """Language and tone analysis"""
    tone: ToneType
    bias_indicators: List[str]
    loaded_language: List[str]
    emotional_words: List[str]
    persuasive_techniques: List[str]

class SourceMetrics(BaseModel):
    """Source credibility metrics"""
    domain_authority: Optional[float] = None
    bias_rating: Optional[str] = None
    factual_reporting: Optional[str] = None
    funding_transparency: Optional[str] = None

class VerificationQuestion(BaseModel):
    """Specific question for fact-checking"""
    question: str
    category: str
    priority: int = Field(ge=1, le=5)
    research_tips: List[str] = []

class CounterNarrative(BaseModel):
    """Alternative perspective analysis"""
    opposing_viewpoint: str
    alternative_explanations: List[str]
    missing_context: List[str]
    potential_rebuttals: List[str]

class AnalysisResult(BaseModel):
    """Complete analysis result"""
    article: ArticleContent
    core_claims: List[Claim]
    language_analysis: LanguageAnalysis
    red_flags: List[RedFlag]
    verification_questions: List[VerificationQuestion]
    entities: List[Entity]
    source_metrics: Optional[SourceMetrics] = None
    counter_narrative: Optional[CounterNarrative] = None
    bias_confidence: float = Field(ge=0.0, le=1.0)
    overall_credibility: float = Field(ge=0.0, le=1.0)

class AnalysisRequest(BaseModel):
    """Request model for analysis"""
    url: HttpUrl
    include_counter_narrative: bool = True
    include_entity_analysis: bool = True
    include_source_check: bool = True 
