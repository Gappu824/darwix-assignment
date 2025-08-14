"""Content validation utilities"""

import re
import validators
from typing import Optional, Tuple
from urllib.parse import urlparse
import langdetect
from langdetect.lang_detect_exception import LangDetectException


class ContentValidator:
    """Validates extracted content quality and characteristics"""
    
    MIN_CONTENT_LENGTH = 500
    MAX_CONTENT_LENGTH = 100000
    MIN_PARAGRAPHS = 3
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format and accessibility"""
        try:
            return validators.url(url) is True
        except Exception:
            return False
    
    @staticmethod
    def is_news_domain(domain: str) -> bool:
        """Check if domain is likely a news source"""
        news_indicators = [
            'news', 'times', 'post', 'herald', 'tribune', 'journal',
            'guardian', 'telegraph', 'reuters', 'ap', 'bbc', 'cnn',
            'npr', 'wsj', 'nytimes', 'washingtonpost', 'bloomberg',
            'politico', 'axios', 'vox', 'slate', 'salon', 'dailybeast'
        ]
        
        domain_lower = domain.lower()
        return any(indicator in domain_lower for indicator in news_indicators)
    
    @staticmethod
    def calculate_content_quality(content: str, title: str = None) -> float:
        """Calculate content quality score (0.0 to 1.0)"""
        if not content:
            return 0.0
        
        score = 0.0
        
        # Length check (0-0.3)
        length = len(content)
        if length >= ContentValidator.MIN_CONTENT_LENGTH:
            score += min(0.3, length / 10000 * 0.3)
        
        # Structure check (0-0.3)
        paragraphs = content.count('\n\n') + content.count('\n \n')
        if paragraphs >= ContentValidator.MIN_PARAGRAPHS:
            score += min(0.3, paragraphs / 10 * 0.3)
        
        # Sentence structure (0-0.2)
        sentences = content.count('.') + content.count('!') + content.count('?')
        avg_sentence_length = length / max(sentences, 1)
        if 10 <= avg_sentence_length <= 100:  # Reasonable sentence length
            score += 0.2
        
        # Title presence (0-0.1)
        if title and len(title) > 10:
            score += 0.1
        
        # Language coherence (0-0.1)
        try:
            detected_lang = langdetect.detect(content)
            if detected_lang == 'en':
                score += 0.1
        except LangDetectException:
            pass
        
        return min(1.0, score)
    
    @staticmethod
    def detect_language(content: str) -> Optional[str]:
        """Detect content language"""
        try:
            return langdetect.detect(content)
        except LangDetectException:
            return None
    
    @staticmethod
    def clean_content(content: str) -> str:
        """Clean and normalize content"""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common web artifacts
        artifacts = [
            r'Cookie Policy',
            r'Privacy Policy',
            r'Terms of Service',
            r'Subscribe to newsletter',
            r'Follow us on',
            r'Share this article',
            r'Advertisement',
            r'\[Advertisement\]'
        ]
        
        for artifact in artifacts:
            content = re.sub(artifact, '', content, flags=re.IGNORECASE)
        
        # Clean up line breaks
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content.strip()
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().replace('www.', '')
        except Exception:
            return ""
    
    @staticmethod
    def is_article_content(content: str) -> bool:
        """Check if content appears to be a news article"""
        if not content or len(content) < ContentValidator.MIN_CONTENT_LENGTH:
            return False
        
        # Check for article-like characteristics
        has_paragraphs = content.count('\n\n') >= ContentValidator.MIN_PARAGRAPHS
        has_sentences = content.count('.') >= 5
        
        # Check for common non-article indicators
        non_article_indicators = [
            '404 not found',
            'page not found',
            'access denied',
            'login required',
            'subscribe to continue',
            'paywall',
            'premium content'
        ]
        
        content_lower = content.lower()
        has_non_article = any(indicator in content_lower 
                             for indicator in non_article_indicators)
        
        return has_paragraphs and has_sentences and not has_non_article
    
    @staticmethod
    def validate_extraction_result(content: str, url: str, method: str) -> Tuple[bool, str, float]:
        """
        Validate extraction result
        Returns: (is_valid, reason, quality_score)
        """
        if not content:
            return False, "No content extracted", 0.0
        
        if not ContentValidator.is_article_content(content):
            return False, "Content does not appear to be an article", 0.0
        
        quality_score = ContentValidator.calculate_content_quality(content)
        
        if quality_score < 0.3:
            return False, f"Content quality too low: {quality_score:.2f}", quality_score
        
        return True, f"Valid article content extracted via {method}", quality_score

# Global validator instance
validator = ContentValidator() 
