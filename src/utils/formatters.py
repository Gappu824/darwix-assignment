"""Markdown report formatting utilities"""

from typing import List
from datetime import datetime
from ..models.schemas import AnalysisResult, Claim, RedFlag, VerificationQuestion, BiasType, SeverityLevel

class MarkdownFormatter:
    """Formats analysis results into professional Markdown reports"""
    
    @staticmethod
    def format_analysis_report(analysis: AnalysisResult) -> str:
        """Generate complete markdown report"""
        
        # Build report sections
        sections = [
            MarkdownFormatter._format_header(analysis),
            MarkdownFormatter._format_core_claims(analysis.core_claims),
            MarkdownFormatter._format_language_analysis(analysis.language_analysis),
            MarkdownFormatter._format_red_flags(analysis.red_flags),
            MarkdownFormatter._format_verification_questions(analysis.verification_questions),
        ]
        
        # Add optional sections
        if analysis.entities:
            sections.append(MarkdownFormatter._format_entities(analysis.entities))
        
        if analysis.counter_narrative:
            sections.append(MarkdownFormatter._format_counter_narrative(analysis.counter_narrative))
        
        if analysis.source_metrics:
            sections.append(MarkdownFormatter._format_source_metrics(analysis.source_metrics))
        
        sections.append(MarkdownFormatter._format_summary(analysis))
        sections.append(MarkdownFormatter._format_footer())
        
        return "\n\n".join(sections)
    
    @staticmethod
    def _format_header(analysis: AnalysisResult) -> str:
        """Format report header"""
        article = analysis.article
        return f"""# Critical Analysis Report

**Article:** {article.title or "Unknown Title"}  
**URL:** {article.url}  
**Domain:** {article.domain}  
**Author:** {article.author or "Unknown"}  
**Publication Date:** {article.publish_date or "Unknown"}  
**Analysis Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  

---"""
    
    @staticmethod
    def _format_core_claims(claims: List[Claim]) -> str:
        """Format core claims section"""
        if not claims:
            return "### Core Claims\n\n*No major factual claims identified.*"
        
        section = "### Core Claims\n\n"
        
        for i, claim in enumerate(claims, 1):
            evidence_emoji = {
                "strong": "✅",
                "moderate": "⚠️",
                "weak": "❌",
                "none": "🚫"
            }
            
            verifiable_text = "✓ Verifiable" if claim.verifiable else "✗ Not easily verifiable"
            
            section += f"""**{i}.** {claim.claim}

- **Evidence Quality:** {evidence_emoji.get(claim.evidence_quality.value, '❓')} {claim.evidence_quality.value.title()}
- **Verifiable:** {verifiable_text}
- **Confidence:** {claim.confidence:.1%}
{f"- **Context:** {claim.context}" if claim.context else ""}

"""
        
        return section.rstrip()
    
    @staticmethod
    def _format_language_analysis(language: any) -> str:
        """Format language and tone analysis"""
        section = f"""### Language & Tone Analysis

**Overall Tone:** {language.tone.value.title()}

"""
        
        if language.bias_indicators:
            section += "**Bias Indicators:**\n"
            for indicator in language.bias_indicators:
                section += f"- {indicator}\n"
            section += "\n"
        
        if language.loaded_language:
            section += "**Loaded Language:**\n"
            for term in language.loaded_language:
                section += f"- \"{term}\"\n"
            section += "\n"
        
        if language.emotional_words:
            section += "**Emotional Language:**\n"
            for word in language.emotional_words:
                section += f"- \"{word}\"\n"
            section += "\n"
        
        if language.persuasive_techniques:
            section += "**Persuasive Techniques:**\n"
            for technique in language.persuasive_techniques:
                section += f"- {technique}\n"
        
        return section.rstrip()
    
    @staticmethod
    def _format_red_flags(red_flags: List[RedFlag]) -> str:
        """Format potential red flags section"""
        if not red_flags:
            return "### Potential Red Flags\n\n*No significant red flags identified.*"
        
        section = "### Potential Red Flags\n\n"
        
        severity_emoji = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢"
        }
        
        # Sort by severity (high to low)
        sorted_flags = sorted(red_flags, key=lambda x: {"high": 3, "medium": 2, "low": 1}[x.severity.value], reverse=True)
        
        for flag in sorted_flags:
            emoji = severity_emoji.get(flag.severity.value, "⚪")
            
            section += f"""**{emoji} {flag.type.value.replace('_', ' ').title()}** ({flag.severity.value.upper()})

{flag.description}

{f"**Evidence:** {flag.evidence}" if flag.evidence else ""}
**Confidence:** {flag.confidence:.1%}

---

"""
        
        return section.rstrip()
    
    @staticmethod
    def _format_verification_questions(questions: List[VerificationQuestion]) -> str:
        """Format verification questions section"""
        if not questions:
            return "### Verification Questions\n\n*No specific verification questions generated.*"
        
        section = "### Verification Questions\n\n"
        
        # Sort by priority (highest first)
        sorted_questions = sorted(questions, key=lambda x: x.priority, reverse=True)
        
        for i, question in enumerate(sorted_questions, 1):
            priority_indicator = "🔥" * question.priority
            
            section += f"""**{i}.** {question.question}

- **Priority:** {priority_indicator} ({question.priority}/5)
- **Category:** {question.category.title()}
"""
            
            if question.research_tips:
                section += "- **Research Tips:**\n"
                for tip in question.research_tips:
                    section += f"  - {tip}\n"
            
            section += "\n"
        
        return section.rstrip()
    
    @staticmethod
    def _format_entities(entities: List[any]) -> str:
        """Format key entities section"""
        if not entities:
            return ""
        
        section = "### Key Entities\n\n"
        
        # Group by entity type
        entity_groups = {}
        for entity in entities:
            if entity.label not in entity_groups:
                entity_groups[entity.label] = []
            entity_groups[entity.label].append(entity)
        
        for label, group_entities in entity_groups.items():
            section += f"**{label}:**\n"
            for entity in group_entities:
                section += f"- {entity.text}"
                if entity.context:
                    section += f" _{entity.context}_"
                section += f" (confidence: {entity.confidence:.1%})\n"
            section += "\n"
        
        return section.rstrip()
    
    @staticmethod
    def _format_counter_narrative(counter: any) -> str:
        """Format counter-narrative section"""
        section = """### Alternative Perspectives

**Opposing Viewpoint:**
{opposing_viewpoint}

""".format(opposing_viewpoint=counter.opposing_viewpoint)
        
        if counter.alternative_explanations:
            section += "**Alternative Explanations:**\n"
            for explanation in counter.alternative_explanations:
                section += f"- {explanation}\n"
            section += "\n"
        
        if counter.missing_context:
            section += "**Missing Context:**\n"
            for context in counter.missing_context:
                section += f"- {context}\n"
            section += "\n"
        
        if counter.potential_rebuttals:
            section += "**Potential Rebuttals:**\n"
            for rebuttal in counter.potential_rebuttals:
                section += f"- {rebuttal}\n"
        
        return section.rstrip()
    
    @staticmethod
    def _format_source_metrics(metrics: any) -> str:
        """Format source credibility metrics"""
        section = "### Source Analysis\n\n"
        
        if metrics.domain_authority:
            section += f"**Domain Authority:** {metrics.domain_authority}/100\n"
        
        if metrics.bias_rating:
            section += f"**Bias Rating:** {metrics.bias_rating}\n"
        
        if metrics.factual_reporting:
            section += f"**Factual Reporting:** {metrics.factual_reporting}\n"
        
        if metrics.funding_transparency:
            section += f"**Funding Transparency:** {metrics.funding_transparency}\n"
        
        return section.rstrip()
    
    @staticmethod
    def _format_summary(analysis: AnalysisResult) -> str:
        """Format analysis summary"""
        
        # Determine overall assessment
        credibility = analysis.overall_credibility
        bias_level = analysis.bias_confidence
        
        if credibility >= 0.8:
            credibility_label = "High"
            credibility_emoji = "✅"
        elif credibility >= 0.6:
            credibility_label = "Moderate"
            credibility_emoji = "⚠️"
        else:
            credibility_label = "Low"
            credibility_emoji = "❌"
        
        if bias_level <= 0.3:
            bias_label = "Low"
            bias_emoji = "✅"
        elif bias_level <= 0.6:
            bias_label = "Moderate"
            bias_emoji = "⚠️"
        else:
            bias_label = "High"
            bias_emoji = "❌"
        
        high_severity_flags = len([f for f in analysis.red_flags if f.severity.value == "high"])
        strong_claims = len([c for c in analysis.core_claims if c.evidence_quality.value == "strong"])
        
        return f"""### Summary

**Overall Assessment:**
- **Credibility:** {credibility_emoji} {credibility_label} ({credibility:.1%})
- **Bias Level:** {bias_emoji} {bias_label} ({bias_level:.1%})
- **Strong Claims:** {strong_claims}/{len(analysis.core_claims)}
- **High-Severity Issues:** {high_severity_flags}

**Recommendation:** {"Exercise caution when sharing or citing this article" if credibility < 0.6 or bias_level > 0.6 else "Article appears relatively credible but verify key claims independently"}.

**Key Action Items:**
- Verify the {len(analysis.verification_questions)} questions listed above
- Cross-reference claims with other reputable sources
- Consider the source's potential biases and motivations
- Look for missing perspectives or context"""
    
    @staticmethod
    def _format_footer() -> str:
        """Format report footer"""
        return """

---

**Disclaimer:** This analysis is generated by AI and should not be considered the final word on article credibility. Always verify important information through multiple independent sources and apply critical thinking when consuming news media.

*Report generated by Digital Skeptic AI - Empowering Critical Thinking in an Age of Information Overload*"""

# Global formatter instance
formatter = MarkdownFormatter()