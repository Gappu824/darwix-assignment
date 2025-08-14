"""Extract metadata and assess source credibility"""

import aiohttp
import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import re
from datetime import datetime

from ..models.schemas import SourceMetrics
from ..utils.config import config

class MetadataExtractor:
    """Extract metadata and assess source credibility"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def extract_source_metrics(self, domain: str, url: str = None) -> Optional[SourceMetrics]:
        """Extract comprehensive source credibility metrics"""
        
        try:
            # Gather all metrics
            domain_authority = await self._assess_domain_authority(domain)
            bias_rating = await self._check_media_bias(domain)
            factual_reporting = await self._assess_factual_reporting(domain)
            funding_transparency = await self._check_funding_transparency(domain)
            
            return SourceMetrics(
                domain_authority=domain_authority,
                bias_rating=bias_rating,
                factual_reporting=factual_reporting,
                funding_transparency=funding_transparency
            )
            
        except Exception as e:
            print(f"Error extracting source metrics: {e}")
            return None
    
    async def _assess_domain_authority(self, domain: str) -> Optional[float]:
        """Assess domain authority and reputation"""
        
        # Known high-authority domains (simplified scoring)
        high_authority_domains = {
            'reuters.com': 95,
            'ap.org': 95,
            'bbc.com': 90,
            'nytimes.com': 90,
            'washingtonpost.com': 88,
            'wsj.com': 88,
            'npr.org': 85,
            'cnn.com': 82,
            'bloomberg.com': 85,
            'theguardian.com': 83,
            'politico.com': 80,
            'axios.com': 78,
            'vox.com': 75,
            'slate.com': 72,
        }
        
        # Check if it's a known domain
        if domain in high_authority_domains:
            return float(high_authority_domains[domain])
        
        # Basic heuristics for unknown domains
        authority_score = 50.0  # Baseline
        
        # Government domains
        if domain.endswith('.gov'):
            authority_score += 30
        
        # Educational domains
        elif domain.endswith('.edu'):
            authority_score += 25
        
        # Established news indicators
        news_indicators = ['news', 'times', 'post', 'herald', 'tribune', 'journal']
        if any(indicator in domain for indicator in news_indicators):
            authority_score += 10
        
        # Suspicious indicators
        suspicious_indicators = ['blog', 'wordpress', 'blogspot', 'medium.com']
        if any(indicator in domain for indicator in suspicious_indicators):
            authority_score -= 15
        
        # Very new or suspicious domains
        if len(domain.split('.')) > 3 or any(char.isdigit() for char in domain):
            authority_score -= 10
        
        return min(100.0, max(0.0, authority_score))
    
    async def _check_media_bias(self, domain: str) -> Optional[str]:
        """Check media bias rating"""
        
        # Simplified bias ratings based on known sources
        bias_ratings = {
            # Center/Least Biased
            'reuters.com': 'Least Biased',
            'ap.org': 'Least Biased',
            'bbc.com': 'Least Biased',
            'npr.org': 'Least Biased',
            'bloomberg.com': 'Least Biased',
            
            # Left-Center
            'nytimes.com': 'Left-Center',
            'washingtonpost.com': 'Left-Center',
            'theguardian.com': 'Left-Center',
            'cnn.com': 'Left-Center',
            'vox.com': 'Left',
            'slate.com': 'Left',
            
            # Right-Center
            'wsj.com': 'Right-Center',
            'politico.com': 'Left-Center',
            'axios.com': 'Least Biased',
            
            # Government sources
            '*.gov': 'Least Biased',
        }
        
        # Check exact domain match
        if domain in bias_ratings:
            return bias_ratings[domain]
        
        # Check for government domains
        if domain.endswith('.gov'):
            return 'Least Biased'
        
        # Default for unknown sources
        return 'Unknown'
    
    async def _assess_factual_reporting(self, domain: str) -> Optional[str]:
        """Assess factual reporting quality"""
        
        factual_ratings = {
            # Very High
            'reuters.com': 'Very High',
            'ap.org': 'Very High',
            'bbc.com': 'Very High',
            'npr.org': 'Very High',
            
            # High
            'nytimes.com': 'High',
            'washingtonpost.com': 'High',
            'wsj.com': 'High',
            'bloomberg.com': 'High',
            'theguardian.com': 'High',
            'politico.com': 'High',
            
            # Mostly Factual
            'cnn.com': 'Mostly Factual',
            'vox.com': 'Mostly Factual',
            'axios.com': 'High',
            'slate.com': 'Mostly Factual',
        }
        
        if domain in factual_ratings:
            return factual_ratings[domain]
        
        # Government and educational domains
        if domain.endswith('.gov') or domain.endswith('.edu'):
            return 'High'
        
        return 'Unknown'
    
    async def _check_funding_transparency(self, domain: str) -> Optional[str]:
        """Check funding transparency and ownership"""
        
        transparency_info = {
            'reuters.com': 'Thomson Reuters Corporation (Publicly Traded)',
            'ap.org': 'Member-funded cooperative',
            'bbc.com': 'Publicly funded (UK)',
            'npr.org': 'Public radio (donations, grants)',
            'nytimes.com': 'The New York Times Company (Publicly Traded)',
            'washingtonpost.com': 'Nash Holdings (Jeff Bezos)',
            'wsj.com': 'News Corp (Rupert Murdoch)',
            'cnn.com': 'Warner Bros. Discovery',
            'bloomberg.com': 'Bloomberg L.P. (Michael Bloomberg)',
            'theguardian.com': 'Scott Trust Limited',
            'politico.com': 'Axel Springer SE',
            'vox.com': 'Vox Media',
            'axios.com': 'Axios Media',
            'slate.com': 'The Slate Group'
        }
        
        if domain in transparency_info:
            return transparency_info[domain]
        
        if domain.endswith('.gov'):
            return 'Government funded'
        
        if domain.endswith('.edu'):
            return 'Educational institution'
        
        return 'Unknown ownership'
    
    async def extract_article_metadata(self, url: str, html: str = None) -> Dict[str, Any]:
        """Extract detailed article metadata"""
        
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc.replace('www.', ''),
            'publication_date': None,
            'author': None,
            'title': None,
            'description': None,
            'keywords': None,
            'article_type': None,
            'word_count': None,
            'reading_time': None
        }
        
        if not html:
            try:
                async with aiohttp.ClientSession(headers=self.headers) as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)) as response:
                        if response.status == 200:
                            html = await response.text()
            except Exception as e:
                print(f"Failed to fetch HTML for metadata extraction: {e}")
                return metadata
        
        if html:
            metadata.update(self._parse_html_metadata(html))
        
        return metadata
    
    def _parse_html_metadata(self, html: str) -> Dict[str, Any]:
        """Parse metadata from HTML"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {}
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.text.strip()
        
        # Meta tags
        meta_tags = soup.find_all('meta')
        
        for meta in meta_tags:
            # Author
            if meta.get('name') in ['author', 'article:author']:
                metadata['author'] = meta.get('content', '').strip()
            
            # Description
            elif meta.get('name') == 'description' or meta.get('property') == 'og:description':
                metadata['description'] = meta.get('content', '').strip()
            
            # Keywords
            elif meta.get('name') == 'keywords':
                metadata['keywords'] = meta.get('content', '').strip()
            
            # Publication date
            elif meta.get('name') in ['article:published_time', 'pubdate'] or meta.get('property') == 'article:published_time':
                metadata['publication_date'] = meta.get('content', '').strip()
        
        # JSON-LD structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get('@type') == 'NewsArticle' or data.get('@type') == 'Article':
                        if not metadata.get('author') and data.get('author'):
                            author_info = data['author']
                            if isinstance(author_info, dict):
                                metadata['author'] = author_info.get('name', '')
                            elif isinstance(author_info, list) and author_info:
                                metadata['author'] = author_info[0].get('name', '') if isinstance(author_info[0], dict) else str(author_info[0])
                        
                        if not metadata.get('publication_date') and data.get('datePublished'):
                            metadata['publication_date'] = data['datePublished']
                        
                        if not metadata.get('title') and data.get('headline'):
                            metadata['title'] = data['headline']
            except:
                continue
        
        # Calculate word count and reading time
        article_text = soup.get_text()
        if article_text:
            words = len(article_text.split())
            metadata['word_count'] = words
            metadata['reading_time'] = max(1, round(words / 200))  # Assuming 200 words per minute
        
        return metadata
    
    def analyze_url_structure(self, url: str) -> Dict[str, Any]:
        """Analyze URL structure for credibility indicators"""
        
        parsed = urlparse(url)
        analysis = {
            'domain': parsed.netloc.replace('www.', ''),
            'path_depth': len([p for p in parsed.path.split('/') if p]),
            'has_date_in_path': bool(re.search(r'/\d{4}/', parsed.path)),
            'has_suspicious_params': bool(re.search(r'[?&](utm_|ref=|source=)', parsed.query)),
            'is_subdomain': len(parsed.netloc.split('.')) > 2,
            'tld': parsed.netloc.split('.')[-1] if '.' in parsed.netloc else None
        }
        
        # Credibility scoring based on URL structure
        credibility_score = 50  # Baseline
        
        # Positive indicators
        if analysis['has_date_in_path']:
            credibility_score += 10
        
        if analysis['tld'] in ['com', 'org', 'gov', 'edu']:
            credibility_score += 5
        
        # Negative indicators
        if analysis['is_subdomain'] and not analysis['domain'].startswith('www'):
            credibility_score -= 10
        
        if analysis['path_depth'] > 5:
            credibility_score -= 5
        
        if analysis['tld'] in ['tk', 'ml', 'ga', 'cf']:  # Free TLDs often used by suspicious sites
            credibility_score -= 20
        
        analysis['url_credibility_score'] = max(0, min(100, credibility_score))
        
        return analysis
    
    async def check_domain_age(self, domain: str) -> Optional[Dict[str, Any]]:
        """Check domain registration age (simplified version)"""
        
        # Known established domains (simplified)
        established_domains = {
            'reuters.com': {'age_years': 30, 'established': '1990s'},
            'nytimes.com': {'age_years': 25, 'established': '1996'},
            'bbc.com': {'age_years': 25, 'established': '1997'},
            'cnn.com': {'age_years': 25, 'established': '1995'},
            'washingtonpost.com': {'age_years': 25, 'established': '1996'},
        }
        
        if domain in established_domains:
            return established_domains[domain]
        
        # For unknown domains, we'd normally use WHOIS data
        # This is a simplified placeholder
        return {'age_years': None, 'established': 'Unknown'}

# Global metadata extractor instance
metadata_extractor = MetadataExtractor() 
