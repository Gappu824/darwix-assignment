"""Sophisticated prompt templates for Gemini 1.5 Pro analysis"""

class PromptTemplates:
    
    MAIN_ANALYSIS_PROMPT = """
You are an expert media analyst and fact-checker with deep expertise in identifying bias, misinformation, and journalistic quality. Analyze the following article systematically and thoroughly.

ARTICLE CONTENT:
{content}

ARTICLE METADATA:
- URL: {url}
- Title: {title}
- Author: {author}
- Domain: {domain}
- Publication Date: {publish_date}

Provide a comprehensive analysis in this exact JSON structure:

{{
    "core_claims": [
        {{
            "claim": "specific factual claim from the article",
            "evidence_quality": "strong|moderate|weak|none",
            "verifiable": true/false,
            "context": "surrounding context for this claim",
            "confidence": 0.0-1.0
        }}
    ],
    "language_analysis": {{
        "tone": "neutral|persuasive|emotional|inflammatory",
        "bias_indicators": ["specific examples of biased language"],
        "loaded_language": ["emotionally charged words/phrases"],
        "emotional_words": ["words designed to provoke emotional response"],
        "persuasive_techniques": ["techniques used to influence reader"]
    }},
    "red_flags": [
        {{
            "type": "source_bias|statistical_misuse|logical_fallacy|selection_bias|framing_bias|emotional_manipulation",
            "description": "detailed description of the issue",
            "severity": "high|medium|low",
            "evidence": "specific evidence from the text",
            "confidence": 0.0-1.0
        }}
    ],
    "verification_questions": [
        {{
            "question": "specific, actionable verification question",
            "category": "factual|source|methodology|context",
            "priority": 1-5,
            "research_tips": ["specific tips for researching this question"]
        }}
    ],
    "bias_confidence": 0.0-1.0,
    "overall_credibility": 0.0-1.0
}}

ANALYSIS GUIDELINES:
1. CORE CLAIMS: Identify 3-5 major factual assertions. Assess evidence quality based on sources cited, data provided, and verifiability.

2. LANGUAGE ANALYSIS: Look for:
   - Emotional manipulation (fear, anger, excitement)
   - Loaded terminology that frames issues
   - Absolute statements vs. nuanced language
   - Appeals to emotion vs. logic

3. RED FLAGS: Identify:
   - Anonymous sources for major claims
   - Statistical manipulation or cherry-picking
   - False dichotomies or straw man arguments
   - Missing context or alternative viewpoints
   - Conflicts of interest

4. VERIFICATION QUESTIONS: Create specific, actionable questions that readers should research to verify claims.

Be thorough, objective, and provide specific evidence for all assessments.
"""

    COUNTER_NARRATIVE_PROMPT = """
Based on the analysis of this article, generate a counter-narrative from an opposing ideological perspective.

ORIGINAL ARTICLE ANALYSIS:
{analysis_summary}

MAIN CLAIMS:
{main_claims}

Generate a counter-narrative that includes:

{{
    "opposing_viewpoint": "How someone with opposite political/ideological views might interpret the same facts",
    "alternative_explanations": ["plausible alternative explanations for events described"],
    "missing_context": ["important context or perspectives that might be missing"],
    "potential_rebuttals": ["how critics might respond to the main arguments"]
}}

Guidelines:
1. Be fair and intellectually honest
2. Focus on legitimate alternative interpretations
3. Highlight potential blind spots or missing perspectives
4. Don't create strawman arguments
5. Stick to plausible counter-arguments that reasonable people might make
"""

    ENTITY_ANALYSIS_PROMPT = """
Extract and analyze the key entities (people, organizations, locations) mentioned in this article.

ARTICLE CONTENT:
{content}

For each significant entity, provide:

{{
    "entities": [
        {{
            "text": "entity name",
            "label": "PERSON|ORG|GPE|EVENT|PRODUCT",
            "confidence": 0.0-1.0,
            "context": "how this entity is presented in the article"
        }}
    ]
}}

Focus on entities that are:
1. Central to the main claims
2. Sources of information
3. Organizations with potential bias
4. Key decision-makers or influencers

Provide context about how each entity is framed in the article.
"""

    SOURCE_ANALYSIS_PROMPT = """
Analyze the credibility and potential bias of this news source.

DOMAIN: {domain}
ARTICLE TITLE: {title}
AUTHOR: {author}

Research and provide assessment:

{{
    "source_assessment": {{
        "domain_reputation": "assessment of overall domain credibility",
        "editorial_stance": "known political/ideological leanings",
        "funding_sources": "known funding or ownership influences",
        "journalistic_standards": "assessment of fact-checking and correction policies",
        "author_background": "relevant author expertise and potential conflicts"
    }}
}}

Base assessment on known information about media outlets, but be conservative about claims you cannot verify.
"""

    def format_main_analysis(self, content: str, url: str, title: str = None, 
                           author: str = None, domain: str = None, 
                           publish_date: str = None) -> str:
        """Format the main analysis prompt with article data"""
        return self.MAIN_ANALYSIS_PROMPT.format(
            content=content,
            url=url,
            title=title or "Unknown",
            author=author or "Unknown",
            domain=domain or "Unknown",
            publish_date=publish_date or "Unknown"
        )
    
    def format_counter_narrative(self, analysis_summary: str, main_claims: str) -> str:
        """Format the counter-narrative prompt"""
        return self.COUNTER_NARRATIVE_PROMPT.format(
            analysis_summary=analysis_summary,
            main_claims=main_claims
        )
    
    def format_entity_analysis(self, content: str) -> str:
        """Format the entity analysis prompt"""
        return self.ENTITY_ANALYSIS_PROMPT.format(content=content)
    
    def format_source_analysis(self, domain: str, title: str = None, 
                              author: str = None) -> str:
        """Format the source analysis prompt"""
        return self.SOURCE_ANALYSIS_PROMPT.format(
            domain=domain,
            title=title or "Unknown",
            author=author or "Unknown"
        )

# Global instance
prompts = PromptTemplates() 
