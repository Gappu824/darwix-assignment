"""Gemini 1.5 Pro integration for article analysis"""

import google.generativeai as genai
import json
import asyncio
from typing import Dict, Any, Optional, List
import re

from ..models.schemas import (
    AnalysisResult, Claim, RedFlag, LanguageAnalysis, VerificationQuestion, 
    CounterNarrative, BiasType, SeverityLevel, EvidenceQuality, ToneType
)
from ..utils.prompts import prompts
from ..utils.config import config

class GeminiAnalyzer:
    """Gemini 1.5 Pro integration for sophisticated article analysis"""
    
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # Initialize model with safety settings
        generation_config = {
            "temperature": 0.1,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-latest",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
    
    async def analyze_article(self, content: str, url: str, title: str = None, 
                            author: str = None, domain: str = None, 
                            publish_date: str = None) -> Dict[str, Any]:
        """Perform comprehensive article analysis using Gemini"""
        
        try:
            # Format the main analysis prompt
            prompt = prompts.format_main_analysis(
                content=content,
                url=url,
                title=title,
                author=author,
                domain=domain,
                publish_date=publish_date
            )
            
            # Generate analysis
            response = await self._generate_with_retry(prompt)
            
            # Parse JSON response
            analysis_data = self._parse_json_response(response.text)
            
            if not analysis_data:
                raise ValueError("Failed to parse analysis response")
            
            return analysis_data
            
        except Exception as e:
            print(f"Error in Gemini analysis: {e}")
            raise
    
    async def generate_counter_narrative(self, analysis_summary: str, main_claims: str) -> Optional[Dict[str, Any]]:
        """Generate counter-narrative using Gemini"""
        
        try:
            prompt = prompts.format_counter_narrative(analysis_summary, main_claims)
            response = await self._generate_with_retry(prompt)
            
            return self._parse_json_response(response.text)
            
        except Exception as e:
            print(f"Error generating counter-narrative: {e}")
            return None
    
    async def analyze_entities_with_context(self, content: str, entities: List[str]) -> Dict[str, Any]:
        """Analyze entities with contextual information"""
        
        try:
            entity_list = ", ".join(entities[:10])  # Limit to top 10 entities
            
            prompt = f"""
Analyze how these key entities are portrayed in the article:

ENTITIES: {entity_list}

ARTICLE CONTENT:
{content[:8000]}  # Limit content to avoid token limits

For each entity, provide analysis in JSON format:
{{
    "entity_analysis": {{
        "entity_name": {{
            "portrayal": "positive|negative|neutral",
            "role_in_story": "description of role",
            "credibility_indicators": ["list of credibility indicators"],
            "potential_bias": "description of potential bias in coverage"
        }}
    }}
}}
"""
            
            response = await self._generate_with_retry(prompt)
            return self._parse_json_response(response.text)
            
        except Exception as e:
            print(f"Error in entity analysis: {e}")
            return {}
    
    async def assess_source_credibility(self, domain: str, content: str, title: str = None) -> Dict[str, Any]:
        """Assess source credibility using Gemini's knowledge"""
        
        try:
            prompt = f"""
Assess the credibility of this news source and article:

DOMAIN: {domain}
TITLE: {title or "Unknown"}
CONTENT SAMPLE: {content[:2000]}

Provide assessment in JSON format:
{{
    "source_credibility": {{
        "overall_rating": "high|medium|low",
        "reputation_notes": "what you know about this source",
        "content_quality": "assessment of this specific article",
        "red_flags": ["any credibility concerns"],
        "strengths": ["credibility strengths"]
    }}
}}
"""
            
            response = await self._generate_with_retry(prompt)
            return self._parse_json_response(response.text)
            
        except Exception as e:
            print(f"Error in source credibility assessment: {e}")
            return {}
    
    async def _generate_with_retry(self, prompt: str, max_retries: int = 3) -> Any:
        """Generate content with retry logic"""
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                
                if response.text:
                    return response
                else:
                    print(f"Empty response on attempt {attempt + 1}")
                    
            except Exception as e:
                print(f"Generation attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        
        raise Exception("All generation attempts failed")
    
    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from Gemini response, handling markdown formatting"""
        
        try:
            # Remove markdown code blocks if present
            cleaned_text = re.sub(r'```json\s*\n', '', response_text)
            cleaned_text = re.sub(r'\n\s*```', '', cleaned_text)
            cleaned_text = cleaned_text.strip()
            
            # Try direct JSON parsing
            return json.loads(cleaned_text)
            
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            print(f"Failed to parse JSON response: {response_text[:500]}...")
            return None
    
    def parse_analysis_to_models(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert analysis data to Pydantic models"""
        
        try:
            # Parse core claims
            claims = []
            for claim_data in analysis_data.get('core_claims', []):
                claims.append(Claim(
                    claim=claim_data.get('claim', ''),
                    evidence_quality=EvidenceQuality(claim_data.get('evidence_quality', 'none')),
                    verifiable=claim_data.get('verifiable', False),
                    context=claim_data.get('context'),
                    confidence=claim_data.get('confidence', 0.0)
                ))
            
            # Parse language analysis
            lang_data = analysis_data.get('language_analysis', {})
            language_analysis = LanguageAnalysis(
                tone=ToneType(lang_data.get('tone', 'neutral')),
                bias_indicators=lang_data.get('bias_indicators', []),
                loaded_language=lang_data.get('loaded_language', []),
                emotional_words=lang_data.get('emotional_words', []),
                persuasive_techniques=lang_data.get('persuasive_techniques', [])
            )
            
            # Parse red flags
            red_flags = []
            for flag_data in analysis_data.get('red_flags', []):
                red_flags.append(RedFlag(
                    type=BiasType(flag_data.get('type', 'source_bias')),
                    description=flag_data.get('description', ''),
                    severity=SeverityLevel(flag_data.get('severity', 'low')),
                    evidence=flag_data.get('evidence'),
                    confidence=flag_data.get('confidence', 0.0)
                ))
            
            # Parse verification questions
            verification_questions = []
            for q_data in analysis_data.get('verification_questions', []):
                verification_questions.append(VerificationQuestion(
                    question=q_data.get('question', ''),
                    category=q_data.get('category', 'factual'),
                    priority=q_data.get('priority', 1),
                    research_tips=q_data.get('research_tips', [])
                ))
            
            return {
                'claims': claims,
                'language_analysis': language_analysis,
                'red_flags': red_flags,
                'verification_questions': verification_questions,
                'bias_confidence': analysis_data.get('bias_confidence', 0.0),
                'overall_credibility': analysis_data.get('overall_credibility', 0.5)
            }
            
        except Exception as e:
            print(f"Error parsing analysis to models: {e}")
            raise
    
    def create_counter_narrative_model(self, counter_data: Dict[str, Any]) -> Optional[CounterNarrative]:
        """Create CounterNarrative model from parsed data"""
        
        try:
            if not counter_data:
                return None
            
            return CounterNarrative(
                opposing_viewpoint=counter_data.get('opposing_viewpoint', ''),
                alternative_explanations=counter_data.get('alternative_explanations', []),
                missing_context=counter_data.get('missing_context', []),
                potential_rebuttals=counter_data.get('potential_rebuttals', [])
            )
            
        except Exception as e:
            print(f"Error creating counter-narrative model: {e}")
            return None

# Global analyzer instance
analyzer = GeminiAnalyzer() 
