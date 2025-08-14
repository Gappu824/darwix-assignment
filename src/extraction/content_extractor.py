"""Multi-strategy content extraction from web articles"""

import asyncio
import aiohttp
from typing import Optional
from urllib.parse import urlparse
import trafilatura
from newspaper import Article
from bs4 import BeautifulSoup
import html2text
import re

# Optional imports with fallbacks
try:
    from readability import Document
except ImportError:
    Document = None

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from ..models.schemas import ArticleContent
from ..utils.validators import validator
from ..utils.config import config

class ContentExtractor:
    """Multi-strategy content extraction with fallback methods"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Store metadata from last successful extraction
        self._last_title = None
        self._last_author = None
        self._last_date = None
    
    async def extract_content(self, url: str) -> ArticleContent:
        """Extract content using multiple strategies with fallbacks"""
        
        # Validate URL first
        if not validator.validate_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        domain = validator.extract_domain(url)
        
        # Reset metadata
        self._last_title = None
        self._last_author = None
        self._last_date = None
        
        # Try extraction methods in order of preference
        extractors = [
            ("trafilatura", self._extract_with_trafilatura),
            ("newspaper3k", self._extract_with_newspaper),
            ("beautifulsoup", self._extract_with_beautifulsoup),
            ("simple_requests", self._extract_with_simple_requests),  # New fallback
        ]
        
        # Add optional extractors if available
        if Document:
            extractors.insert(2, ("readability", self._extract_with_readability))
        
        if SELENIUM_AVAILABLE:
            extractors.append(("selenium", self._extract_with_selenium))
        
        last_error = None
        
        for method_name, extractor in extractors:
            try:
                print(f"Attempting extraction with {method_name}...")
                content = await extractor(url)
                
                if content and len(content) > 100:  # Basic content check
                    # Validate extraction quality
                    is_valid, reason, quality_score = validator.validate_extraction_result(
                        content, url, method_name
                    )
                    
                    if is_valid:
                        return ArticleContent(
                            url=url,
                            title=self._last_title,
                            content=validator.clean_content(content),
                            author=self._last_author,
                            publish_date=self._last_date,
                            domain=domain,
                            language=validator.detect_language(content),
                            quality_score=quality_score,
                            extraction_method=method_name
                        )
                    else:
                        print(f"{method_name} extraction failed validation: {reason}")
                        continue
                        
            except Exception as e:
                print(f"{method_name} extraction failed: {str(e)}")
                last_error = e
                continue
        
        # If all methods failed
        raise Exception(f"All extraction methods failed. Last error: {last_error}")
    
    async def _extract_with_trafilatura(self, url: str) -> Optional[str]:
        """Extract content using trafilatura (fastest and cleanest)"""
        try:
            # Download page with better error handling
            timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
            async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
                async with session.get(url, allow_redirects=True) as response:
                    if response.status != 200:
                        print(f"HTTP {response.status} for {url}")
                        return None
                    html = await response.text()
            
            if not html or len(html) < 100:
                print("Empty or too short HTML content")
                return None
            
            # Extract with trafilatura - more robust settings
            content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_formatting=False,
                target_language='en',
                favor_precision=True,
                favor_recall=False
            )
            
            if content and len(content) > 100:
                return content
            else:
                print(f"Trafilatura extracted insufficient content: {len(content) if content else 0} chars")
                return None
            
        except Exception as e:
            print(f"Trafilatura extraction error: {e}")
            return None
    
    async def _extract_with_newspaper(self, url: str) -> Optional[str]:
        """Extract content using newspaper3k"""
        try:
            # Create article with config directly in constructor
            from newspaper import Config
            
            config_obj = Config()
            config_obj.browser_user_agent = self.headers['User-Agent']
            config_obj.request_timeout = config.REQUEST_TIMEOUT
            
            article = Article(url, config=config_obj)
            
            # Download and parse
            article.download()
            article.parse()
            
            # Store metadata for later use
            self._last_title = article.title
            self._last_author = ", ".join(article.authors) if article.authors else None
            self._last_date = article.publish_date.isoformat() if article.publish_date else None
            
            return article.text
            
        except Exception as e:
            print(f"Newspaper3k extraction error: {e}")
            return None
    
    async def _extract_with_readability(self, url: str) -> Optional[str]:
        """Extract content using readability-lxml"""
        if not Document:
            return None
            
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
            
            doc = Document(html)
            
            # Convert HTML to text
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            
            content = h.handle(doc.summary())
            
            return content
            
        except Exception as e:
            print(f"Readability extraction error: {e}")
            return None
    
    async def _extract_with_beautifulsoup(self, url: str) -> Optional[str]:
        """Extract content using BeautifulSoup (custom logic)"""
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title if not already found
            if not self._last_title:
                title_tag = soup.find('title')
                if title_tag:
                    self._last_title = title_tag.text.strip()
            
            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Try common article selectors
            content_selectors = [
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content',
                '#content',
                '.story-body',
                '.article-body',
                '[data-testid="article-body"]'
            ]
            
            content = None
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join([elem.get_text().strip() for elem in elements])
                    break
            
            # Fallback: extract from main content areas
            if not content:
                main_content = soup.find('main') or soup.find('body')
                if main_content:
                    # Remove navigation and sidebar elements
                    for elem in main_content.find_all(['nav', 'aside', '.sidebar', '.menu']):
                        elem.decompose()
                    content = main_content.get_text()
            
            if content:
                # Clean up whitespace
                content = re.sub(r'\s+', ' ', content).strip()
                
            return content
            
        except Exception as e:
            print(f"BeautifulSoup extraction error: {e}")
            return None
    
    async def _extract_with_selenium(self, url: str) -> Optional[str]:
        """Extract content using Selenium (last resort for JS-heavy sites)"""
        if not SELENIUM_AVAILABLE:
            return None
            
        try:
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
            
            # Create driver
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Wait a bit more for dynamic content
                await asyncio.sleep(3)
                
                # Extract title if not found
                if not self._last_title:
                    try:
                        title_element = driver.find_element(By.TAG_NAME, "title")
                        self._last_title = title_element.get_attribute("text")
                    except:
                        pass
                
                # Try to find article content
                article_selectors = [
                    'article',
                    '[role="main"]',
                    '.article-content',
                    '.post-content',
                    '.entry-content',
                    '.story-body'
                ]
                
                content = None
                for selector in article_selectors:
                    try:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        content = element.text
                        break
                    except:
                        continue
                
                # Fallback to body content
                if not content:
                    body = driver.find_element(By.TAG_NAME, "body")
                    content = body.text
                
                return content
                
            finally:
                driver.quit()
                
        except Exception as e:
            print(f"Selenium extraction error: {e}")
            return None

    async def _extract_with_simple_requests(self, url: str) -> Optional[str]:
        """Simple fallback extraction using just requests and basic text cleaning"""
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)) as session:
                async with session.get(url, allow_redirects=True) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
            
            if not html:
                return None
            
            # Very basic HTML cleaning
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Get text and clean it
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Basic validation
            if len(text) > 200:
                return text
            else:
                return None
                
        except Exception as e:
            print(f"Simple requests extraction error: {e}")
            return None

# Global extractor instance
extractor = ContentExtractor()
"""Multi-strategy content extraction from web articles"""

import asyncio
import aiohttp
from typing import Optional
from urllib.parse import urlparse
import trafilatura
from newspaper import Article
from bs4 import BeautifulSoup
import html2text
import re

# Optional imports with fallbacks
try:
    from readability import Document
except ImportError:
    Document = None

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from ..models.schemas import ArticleContent
from ..utils.validators import validator
from ..utils.config import config

class ContentExtractor:
    """Multi-strategy content extraction with fallback methods"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def extract_content(self, url: str) -> ArticleContent:
        """Extract content using multiple strategies with fallbacks"""
        
        # Validate URL first
        if not validator.validate_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        domain = validator.extract_domain(url)
        
        # Try extraction methods in order of preference
        extractors = [
            ("trafilatura", self._extract_with_trafilatura),
            ("newspaper3k", self._extract_with_newspaper),
            ("beautifulsoup", self._extract_with_beautifulsoup),
        ]
        
        # Add optional extractors if available
        if Document:
            extractors.insert(2, ("readability", self._extract_with_readability))
        
        if SELENIUM_AVAILABLE:
            extractors.append(("selenium", self._extract_with_selenium))
        
        last_error = None
        
        for method_name, extractor in extractors:
            try:
                print(f"Attempting extraction with {method_name}...")
                content = await extractor(url)
                
                if content and len(content) > 100:  # Basic content check
                    # Validate extraction quality
                    is_valid, reason, quality_score = validator.validate_extraction_result(
                        content, url, method_name
                    )
                    
                    if is_valid:
                        return ArticleContent(
                            url=url,
                            title=getattr(self, '_last_title', None),
                            content=validator.clean_content(content),
                            author=getattr(self, '_last_author', None),
                            publish_date=getattr(self, '_last_date', None),
                            domain=domain,
                            language=validator.detect_language(content),
                            quality_score=quality_score,
                            extraction_method=method_name
                        )
                    else:
                        print(f"{method_name} extraction failed validation: {reason}")
                        continue
                        
            except Exception as e:
                print(f"{method_name} extraction failed: {str(e)}")
                last_error = e
                continue
        
        # If all methods failed
        raise Exception(f"All extraction methods failed. Last error: {last_error}")
    
    async def _extract_with_trafilatura(self, url: str) -> Optional[str]:
        """Extract content using trafilatura (fastest and cleanest)"""
        try:
            # Download page
            async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
            
            # Extract with trafilatura
            content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_formatting=False,
                target_language='en'
            )
            
            return content
            
        except Exception as e:
            print(f"Trafilatura extraction error: {e}")
            return None
    
    async def _extract_with_newspaper(self, url: str) -> Optional[str]:
        """Extract content using newspaper3k"""
        try:
            article = Article(url)
            article.set_config({
                'browser_user_agent': self.headers['User-Agent'],
                'request_timeout': config.REQUEST_TIMEOUT
            })
            
            # Download and parse
            article.download()
            article.parse()
            
            # Store metadata for later use
            self._last_title = article.title
            self._last_author = ", ".join(article.authors) if article.authors else None
            self._last_date = article.publish_date.isoformat() if article.publish_date else None
            
            return article.text
            
        except Exception as e:
            print(f"Newspaper3k extraction error: {e}")
            return None
    
    async def _extract_with_readability(self, url: str) -> Optional[str]:
        """Extract content using readability-lxml"""
        if not Document:
            return None
            
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
            
            doc = Document(html)
            
            # Convert HTML to text
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            
            content = h.handle(doc.summary())
            
            return content
            
        except Exception as e:
            print(f"Readability extraction error: {e}")
            return None
    
    async def _extract_with_beautifulsoup(self, url: str) -> Optional[str]:
        """Extract content using BeautifulSoup (custom logic)"""
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Try common article selectors
            content_selectors = [
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content',
                '#content',
                '.story-body',
                '.article-body',
                '[data-testid="article-body"]'
            ]
            
            content = None
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join([elem.get_text().strip() for elem in elements])
                    break
            
            # Fallback: extract from main content areas
            if not content:
                main_content = soup.find('main') or soup.find('body')
                if main_content:
                    # Remove navigation and sidebar elements
                    for elem in main_content.find_all(['nav', 'aside', '.sidebar', '.menu']):
                        elem.decompose()
                    content = main_content.get_text()
            
            if content:
                # Clean up whitespace
                content = re.sub(r'\s+', ' ', content).strip()
                
            return content
            
        except Exception as e:
            print(f"BeautifulSoup extraction error: {e}")
            return None
    
    async def _extract_with_selenium(self, url: str) -> Optional[str]:
        """Extract content using Selenium (last resort for JS-heavy sites)"""
        if not SELENIUM_AVAILABLE:
            return None
            
        try:
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
            
            # Create driver
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Wait a bit more for dynamic content
                await asyncio.sleep(3)
                
                # Try to find article content
                article_selectors = [
                    'article',
                    '[role="main"]',
                    '.article-content',
                    '.post-content',
                    '.entry-content',
                    '.story-body'
                ]
                
                content = None
                for selector in article_selectors:
                    try:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        content = element.text
                        break
                    except:
                        continue
                
                # Fallback to body content
                if not content:
                    body = driver.find_element(By.TAG_NAME, "body")
                    content = body.text
                
                return content
                
            finally:
                driver.quit()
                
        except Exception as e:
            print(f"Selenium extraction error: {e}")
            return None

# Global extractor instance
extractor = ContentExtractor()
"""Multi-strategy content extraction from web articles"""

import asyncio
import aiohttp
import requests
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import trafilatura
import newspaper
from newspaper import Article
from bs4 import BeautifulSoup
from readability import Document
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import html2text
from datetime import datetime
import re

from ..models.schemas import ArticleContent
from ..utils.validators import validator
from ..utils.config import config

class ContentExtractor:
    """Multi-strategy content extraction with fallback methods"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def extract_content(self, url: str) -> ArticleContent:
        """Extract content using multiple strategies with fallbacks"""
        
        # Validate URL first
        if not validator.validate_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        domain = validator.extract_domain(url)
        
        # Try extraction methods in order of preference
        extractors = [
            ("trafilatura", self._extract_with_trafilatura),
            ("newspaper3k", self._extract_with_newspaper),
            ("readability", self._extract_with_readability),
            ("beautifulsoup", self._extract_with_beautifulsoup),
            ("selenium", self._extract_with_selenium)
        ]
        
        last_error = None
        
        for method_name, extractor in extractors:
            try:
                print(f"Attempting extraction with {method_name}...")
                content = await extractor(url)
                
                if content:
                    # Validate extraction quality
                    is_valid, reason, quality_score = validator.validate_extraction_result(
                        content, url, method_name
                    )
                    
                    if is_valid:
                        return ArticleContent(
                            url=url,
                            title=self._extract_title(url, method_name),
                            content=validator.clean_content(content),
                            author=self._extract_author(url, method_name),
                            publish_date=self._extract_date(url, method_name),
                            domain=domain,
                            language=validator.detect_language(content),
                            quality_score=quality_score,
                            extraction_method=method_name
                        )
                    else:
                        print(f"{method_name} extraction failed validation: {reason}")
                        continue
                        
            except Exception as e:
                print(f"{method_name} extraction failed: {str(e)}")
                last_error = e
                continue
        
        # If all methods failed
        raise Exception(f"All extraction methods failed. Last error: {last_error}")
    
    async def _extract_with_trafilatura(self, url: str) -> Optional[str]:
        """Extract content using trafilatura (fastest and cleanest)"""
        try:
            # Download page
            async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
            
            # Extract with trafilatura
            content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_formatting=False,
                target_language='en'
            )
            
            return content
            
        except Exception as e:
            print(f"Trafilatura extraction error: {e}")
            return None
    
    async def _extract_with_newspaper(self, url: str) -> Optional[str]:
        """Extract content using newspaper3k"""
        try:
            article = Article(url)
            article.set_config({
                'browser_user_agent': self.headers['User-Agent'],
                'request_timeout': config.REQUEST_TIMEOUT
            })
            
            # Download and parse
            article.download()
            article.parse()
            
            # Store metadata for later use
            self._last_newspaper_article = article
            
            return article.text
            
        except Exception as e:
            print(f"Newspaper3k extraction error: {e}")
            return None
    
    async def _extract_with_readability(self, url: str) -> Optional[str]:
        """Extract content using readability-lxml"""
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
            
            doc = Document(html)
            
            # Convert HTML to text
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            
            content = h.handle(doc.summary())
            
            return content
            
        except Exception as e:
            print(f"Readability extraction error: {e}")
            return None
    
    async def _extract_with_beautifulsoup(self, url: str) -> Optional[str]:
        """Extract content using BeautifulSoup (custom logic)"""
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Try common article selectors
            content_selectors = [
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content',
                '#content',
                '.story-body',
                '.article-body',
                '[data-testid="article-body"]'
            ]
            
            content = None
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join([elem.get_text().strip() for elem in elements])
                    break
            
            # Fallback: extract from main content areas
            if not content:
                main_content = soup.find('main') or soup.find('body')
                if main_content:
                    # Remove navigation and sidebar elements
                    for elem in main_content.find_all(['nav', 'aside', '.sidebar', '.menu']):
                        elem.decompose()
                    content = main_content.get_text()
            
            if content:
                # Clean up whitespace
                content = re.sub(r'\s+', ' ', content).strip()
                
            return content
            
        except Exception as e:
            print(f"BeautifulSoup extraction error: {e}")
            return None
    
    async def _extract_with_selenium(self, url: str) -> Optional[str]:
        """Extract content using Selenium (last resort for JS-heavy sites)"""
        try:
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
            
            # Create driver
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Wait a bit more for dynamic content
                await asyncio.sleep(3)
                
                # Try to find article content
                article_selectors = [
                    'article',
                    '[role="main"]',
                    '.article-content',
                    '.post-content',
                    '.entry-content',
                    '.story-body'
                ]
                
                content = None
                for selector in article_selectors:
                    try:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        content = element.text
                        break
                    except:
                        continue
                
                # Fallback to body content
                if not content:
                    body = driver.find_element(By.TAG_NAME, "body")
                    content = body.text
                
                return content
                
            finally:
                driver.quit()
                
        except Exception as e:
            print(f"Selenium extraction error: {e}")
            return None
    
    def _extract_title(self, url: str, method: str) -> Optional[str]:
        """Extract article title (method-specific logic)"""
        if method == "newspaper3k" and hasattr(self, '_last_newspaper_article'):
            return self._last_newspaper_article.title
        # Add other method-specific title extraction
        return None
    
    def _extract_author(self, url: str, method: str) -> Optional[str]:
        """Extract article author (method-specific logic)"""
        if method == "newspaper3k" and hasattr(self, '_last_newspaper_article'):
            authors = self._last_newspaper_article.authors
            return ", ".join(authors) if authors else None
        # Add other method-specific author extraction
        return None
    
    def _extract_date(self, url: str, method: str) -> Optional[str]:
        """Extract publication date (method-specific logic)"""
        if method == "newspaper3k" and hasattr(self, '_last_newspaper_article'):
            pub_date = self._last_newspaper_article.publish_date
            return pub_date.isoformat() if pub_date else None
        # Add other method-specific date extraction
        return None
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

# Global extractor instance
extractor = ContentExtractor()