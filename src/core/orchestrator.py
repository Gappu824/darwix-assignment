"""Main analysis orchestrator - coordinates all analysis components"""

import asyncio
import time
from typing import Optional

# Assuming these imports are in a parent directory or the path is configured
from ..models.schemas import (AnalysisResult, AnalysisRequest, ArticleContent,
                             Claim, RedFlag, LanguageAnalysis, VerificationQuestion,
                             Entity, SourceMetrics, CounterNarrative)
from ..models.response_models import AnalysisResponse
from .scraper import scraper
from .analyzer import analyzer
from ..extraction.entity_extractor import entity_extractor
from ..extraction.metadata_extractor import metadata_extractor
from ..analysis.bias_detector import bias_detector
from ..analysis.claim_extractor import claim_extractor
from ..analysis.counter_narrative import counter_narrative_generator
from ..analysis.verification_generator import verification_generator
from ..utils.formatters import formatter

class AnalysisOrchestrator:
    """Coordinates the complete analysis pipeline"""

    def __init__(self):
        self.scraper = scraper
        self.analyzer = analyzer
        self.entity_extractor = entity_extractor
        self.metadata_extractor = metadata_extractor
        self.bias_detector = bias_detector
        self.claim_extractor = claim_extractor
        self.counter_narrative_generator = counter_narrative_generator
        self.verification_generator = verification_generator
        self.formatter = formatter

    async def analyze_article(self, request: AnalysisRequest) -> AnalysisResponse:
        """Execute complete article analysis pipeline"""

        start_time = time.time()

        try:
            print(f"Starting analysis of: {request.url}")

            # Step 1: Scrape article content
            print("📄 Extracting article content...")
            article_content = await self.scraper.scrape_article(str(request.url))

            # Step 2: Extract entities (if requested)
            entities = []
            if request.include_entity_analysis:
                print("🏷️  Extracting named entities...")
                entities = await self.entity_extractor.extract_entities(
                    article_content.content,
                    article_content.title
                )

            # Step 3: Extract source metrics (if requested)
            source_metrics = None
            if request.include_source_check:
                print("🔍 Analyzing source credibility...")
                source_metrics = await self.metadata_extractor.extract_source_metrics(
                    article_content.domain,
                    str(request.url)
                )

            # Step 4: Extract claims using traditional analysis
            print("📊 Extracting factual claims...")
            traditional_claims = self.claim_extractor.extract_claims(
                article_content.content,
                article_content.title
            )

            # Step 5: Detect bias using traditional analysis
            print("⚖️  Analyzing language bias...")
            traditional_language_analysis = self.bias_detector.detect_language_bias(
                article_content.content,
                article_content.title
            )

            traditional_red_flags = self.bias_detector.detect_structural_bias(
                article_content.content
            )

            # Step 6: Main AI analysis with Gemini
            print("🤖 Performing AI analysis...")
            ai_analysis_data = await self.analyzer.analyze_article(
                content=article_content.content,
                url=str(request.url),
                title=article_content.title,
                author=article_content.author,
                domain=article_content.domain,
                publish_date=article_content.publish_date
            )

            # Step 7: Parse AI analysis and merge with traditional analysis
            print("🔄 Merging analysis results...")
            parsed_ai = self.analyzer.parse_analysis_to_models(ai_analysis_data)

            # Merge traditional and AI analysis
            all_claims = self._merge_claims(traditional_claims, parsed_ai['claims'])
            all_red_flags = self._merge_red_flags(traditional_red_flags, parsed_ai['red_flags'])
            final_language_analysis = self._merge_language_analysis(
                traditional_language_analysis,
                parsed_ai['language_analysis']
            )

            # Step 8: Generate verification questions
            print("❓ Generating verification questions...")
            verification_questions = self.verification_generator.generate_verification_questions(
                all_claims, entities, article_content.content, article_content.domain
            )

            # Step 9: Generate counter-narrative (if requested)
            counter_narrative = None
            if request.include_counter_narrative:
                print("🔄 Generating counter-narrative...")

                # Create analysis result for counter-narrative generation
                temp_analysis_result = AnalysisResult(
                    article=article_content,
                    core_claims=all_claims,
                    language_analysis=final_language_analysis,
                    red_flags=all_red_flags,
                    verification_questions=verification_questions,
                    entities=entities,
                    source_metrics=source_metrics,
                    counter_narrative=None,  # Will be filled
                    bias_confidence=parsed_ai['bias_confidence'],
                    overall_credibility=parsed_ai['overall_credibility']
                )

                counter_narrative = self.counter_narrative_generator.generate_counter_narrative(temp_analysis_result)

            # Step 10: Create final analysis result
            analysis_result = AnalysisResult(
                article=article_content,
                core_claims=all_claims,
                language_analysis=final_language_analysis,
                red_flags=all_red_flags,
                verification_questions=verification_questions,
                entities=entities,
                source_metrics=source_metrics,
                counter_narrative=counter_narrative,
                bias_confidence=parsed_ai['bias_confidence'],
                overall_credibility=parsed_ai['overall_credibility']
            )

            # Step 11: Generate markdown report
            print("📝 Generating markdown report...")
            markdown_report = self.formatter.format_analysis_report(analysis_result)

            processing_time = time.time() - start_time
            print(f"✅ Analysis completed in {processing_time:.2f} seconds")

            return AnalysisResponse(
                success=True,
                result=analysis_result,
                markdown_report=markdown_report,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Analysis failed: {str(e)}"
            print(f"❌ {error_msg}")

            return AnalysisResponse(
                success=False,
                error=error_msg,
                processing_time=processing_time
            )

    def _merge_claims(self, traditional_claims: list[Claim], ai_claims: list[Claim]) -> list[Claim]:
        """Merge claims from traditional and AI analysis"""
        all_claims = traditional_claims + ai_claims
        unique_claims = []
        seen_claims = set()

        for claim in all_claims:
            simplified = ' '.join(claim.claim.lower().split())
            is_duplicate = False
            for seen in seen_claims:
                if self._claims_similar(simplified, seen):
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_claims.append(claim)
                seen_claims.add(simplified)
        
        # Sort by confidence and return top claims
        return sorted(unique_claims, key=lambda x: x.confidence, reverse=True)[:8]

    def _merge_red_flags(self, traditional_flags: list[RedFlag], ai_flags: list[RedFlag]) -> list[RedFlag]:
        """Merge red flags from traditional and AI analysis"""
        all_flags = traditional_flags + ai_flags
        unique_flags = []
        seen_descriptions = set()

        for flag in all_flags:
            simplified_desc = ' '.join(flag.description.lower().split())
            if simplified_desc not in seen_descriptions:
                unique_flags.append(flag)
                seen_descriptions.add(simplified_desc)

        # Sort by severity and confidence
        severity_order = {'high': 3, 'medium': 2, 'low': 1}
        return sorted(unique_flags,
                      key=lambda x: (severity_order.get(x.severity.value, 0), x.confidence),
                      reverse=True)[:10]

    def _merge_language_analysis(self, traditional_analysis: LanguageAnalysis, ai_analysis: LanguageAnalysis) -> LanguageAnalysis:
        """Merge language analysis from traditional and AI methods"""
        merged_bias_indicators = list(ai_analysis.bias_indicators)
        merged_loaded_language = list(ai_analysis.loaded_language)
        merged_emotional_words = list(ai_analysis.emotional_words)
        merged_persuasive_techniques = list(ai_analysis.persuasive_techniques)

        # Add unique items from traditional analysis
        for indicator in traditional_analysis.bias_indicators:
            if indicator not in merged_bias_indicators:
                merged_bias_indicators.append(indicator)

        for term in traditional_analysis.loaded_language:
            if term not in merged_loaded_language:
                merged_loaded_language.append(term)

        for word in traditional_analysis.emotional_words:
            if word not in merged_emotional_words:
                merged_emotional_words.append(word)
        
        for technique in traditional_analysis.persuasive_techniques:
            if technique not in merged_persuasive_techniques:
                merged_persuasive_techniques.append(technique)

        # Create new merged analysis
        return LanguageAnalysis(
            tone=ai_analysis.tone,  # Use AI analysis tone
            bias_indicators=merged_bias_indicators[:15],
            loaded_language=merged_loaded_language[:15],
            emotional_words=merged_emotional_words[:15],
            persuasive_techniques=merged_persuasive_techniques[:10]
        )

    def _claims_similar(self, claim1: str, claim2: str) -> bool:
        """Check if two claims are similar using Jaccard similarity"""
        words1 = set(claim1.split())
        words2 = set(claim2.split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        
        return similarity > 0.6  # 60% similarity threshold

    async def quick_preview(self, url: str) -> dict:
        """Get a quick preview of what would be analyzed"""
        try:
            preview = await self.scraper.get_extraction_preview(url)
            return preview
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'accessible': False
            }

    async def test_url(self, url: str) -> dict:
        """Test URL accessibility and provide diagnostics"""
        return await self.scraper.test_url_accessibility(url)

# Global orchestrator instance
orchestrator = AnalysisOrchestrator()