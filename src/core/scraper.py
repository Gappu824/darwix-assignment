"""High-level web scraping orchestrator"""

import asyncio
from typing import Optional
from urllib.parse import urlparse
import requests

from ..models.schemas import ArticleContent
from ..extraction.content_extractor import extractor
from ..extraction.metadata_extractor import metadata_extractor
from ..utils.validators import validator

class WebScraper:
    """High-level web scraping orchestrator with intelligent fallbacks"""
    
    def __init__(self):
        self.extractor = extractor
        self.metadata_extractor = metadata_extractor
        self.validator = validator
    
    async def scrape_article(self, url: str) -> ArticleContent:
        """Scrape article with comprehensive metadata extraction"""
        
        # Validate URL
        if not self.validator.validate_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        try:
            # Extract main content
            print(f"Scraping article from: {url}")
            article_content = await self.extractor.extract_content(url)
            
            # Enhance with additional metadata if needed
            if not article_content.title or not article_content.author:
                print("Enhancing metadata...")
                additional_metadata = await self.metadata_extractor.extract_article_metadata(url)
                
                # Update missing fields
                if not article_content.title and additional_metadata.get('title'):
                    article_content.title = additional_metadata['title']
                
                if not article_content.author and additional_metadata.get('author'):
                    article_content.author = additional_metadata['author']
                
                if not article_content.publish_date and additional_metadata.get('publication_date'):
                    article_content.publish_date = additional_metadata['publication_date']
            
            print(f"Successfully scraped article ({len(article_content.content)} chars)")
            return article_content
            
        except Exception as e:
            print(f"Failed to scrape article: {e}")
            raise
    
    async def test_url_accessibility(self, url: str) -> dict:
        """Test URL accessibility and provide diagnostics"""
        
        diagnostics = {
            'url': url,
            'accessible': False,
            'status_code': None,
            'error': None,
            'content_type': None,
            'content_length': None,
            'is_news_site': False,
            'recommendations': []
        }
        
        try:
            # Basic URL validation
            if not self.validator.validate_url(url):
                diagnostics['error'] = "Invalid URL format"
                diagnostics['recommendations'].append("Check URL format and try again")
                return diagnostics
            
            # Check if it looks like a news domain
            domain = self.validator.extract_domain(url)
            diagnostics['is_news_site'] = self.validator.is_news_domain(domain)
            
            if not diagnostics['is_news_site']:
                diagnostics['recommendations'].append("URL may not be from a news source")
            
            # Test basic connectivity
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    diagnostics['accessible'] = True
                    diagnostics['status_code'] = response.status
                    diagnostics['content_type'] = response.headers.get('content-type', '')
                    diagnostics['content_length'] = response.headers.get('content-length')
                    
                    if response.status != 200:
                        diagnostics['recommendations'].append(f"HTTP status {response.status} - page may not be accessible")
                    
                    if 'text/html' not in diagnostics['content_type']:
                        diagnostics['recommendations'].append("Content may not be HTML")
        
        except Exception as e:
            diagnostics['error'] = str(e)
            diagnostics['recommendations'].append("Check internet connection and URL accessibility")
        
        return diagnostics
    
    async def get_extraction_preview(self, url: str) -> dict:
        """Get a preview of what would be extracted without full processing"""
        
        preview = {
            'url': url,
            'title': None,
            'content_preview': None,
            'estimated_length': 0,
            'extraction_method': None,
            'quality_score': 0.0,
            'issues': []
        }
        
        try:
            # Try quick extraction
            article = await self.scrape_article(url)
            
            preview.update({
                'title': article.title,
                'content_preview': article.content[:500] + "..." if len(article.content) > 500 else article.content,
                'estimated_length': len(article.content),
                'extraction_method': article.extraction_method,
                'quality_score': article.quality_score,
                'author': article.author,
                'domain': article.domain,
                'publish_date': article.publish_date
            })
            
            # Quality checks
            if article.quality_score < 0.5:
                preview['issues'].append("Low content quality detected")
            
            if len(article.content) < 1000:
                preview['issues'].append("Article may be too short for meaningful analysis")
            
            if not article.title:
                preview['issues'].append("No title found")
            
            if not article.author:
                preview['issues'].append("No author information found")
        
        except Exception as e:
            preview['issues'].append(f"Extraction failed: {str(e)}")
        
        return preview

# Global scraper instance
scraper = WebScraper() 
