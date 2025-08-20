import trafilatura
import requests
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

def get_website_text_content(url: str) -> str:
    """
    This function takes a url and returns the main text content of the website.
    The text content is extracted using trafilatura and easier to understand.
    The results is not directly readable, better to be summarized by LLM before consume
    by the user.

    Some common website to crawl information from:
    MLB scores: https://www.mlb.com/scores/YYYY-MM-DD
    """
    try:
        # Send a request to the website
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            logger.warning(f"Failed to download content from {url}")
            return ""
        
        # Extract text content
        text = trafilatura.extract(downloaded)
        return text or ""
        
    except Exception as e:
        logger.error(f"Failed to extract content from {url}: {e}")
        return ""

class AdvancedWebScraper:
    """Advanced web scraper for financial data and news"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def create_session(self):
        """Create aiohttp session for async requests"""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def scrape_financial_news(self, source_url: str) -> List[Dict[str, Any]]:
        """
        Scrape financial news from a given source
        
        Args:
            source_url: URL of the news source
            
        Returns:
            List of news articles with metadata
        """
        try:
            await self.create_session()
            
            async with self.session.get(source_url, timeout=10) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {source_url}: {response.status}")
                    return []
                
                html_content = await response.text()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract articles based on common news site structures
            articles = []
            
            # Yahoo Finance specific
            if "finance.yahoo.com" in source_url:
                articles = self._extract_yahoo_finance_articles(soup, source_url)
            
            # MarketWatch specific
            elif "marketwatch.com" in source_url:
                articles = self._extract_marketwatch_articles(soup, source_url)
            
            # Bloomberg specific
            elif "bloomberg.com" in source_url:
                articles = self._extract_bloomberg_articles(soup, source_url)
            
            # Generic extraction
            else:
                articles = self._extract_generic_articles(soup, source_url)
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to scrape financial news from {source_url}: {e}")
            return []
    
    def _extract_yahoo_finance_articles(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract articles from Yahoo Finance"""
        articles = []
        
        try:
            # Look for article containers
            article_containers = soup.find_all(['article', 'div'], class_=re.compile(r'.*article.*|.*story.*|.*news.*', re.I))
            
            for container in article_containers[:10]:  # Limit to 10 articles
                title_elem = container.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'.*title.*|.*headline.*', re.I))
                if not title_elem:
                    title_elem = container.find('a')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href') if title_elem.name == 'a' else title_elem.find('a')
                    
                    if link and isinstance(link, str):
                        if not link.startswith('http'):
                            link = urljoin(base_url, link)
                    elif hasattr(link, 'get'):
                        link = link.get('href', '')
                        if link and not link.startswith('http'):
                            link = urljoin(base_url, link)
                    else:
                        link = base_url
                    
                    # Extract summary
                    summary_elem = container.find(['p', 'div'], class_=re.compile(r'.*summary.*|.*description.*|.*excerpt.*', re.I))
                    summary = summary_elem.get_text(strip=True) if summary_elem else title
                    
                    if title and len(title) > 10:  # Valid title
                        articles.append({
                            "title": title,
                            "url": link,
                            "content": summary[:500],  # Limit summary length
                            "source": "Yahoo Finance",
                            "published_at": datetime.now(),
                            "relevance_score": 0.85
                        })
            
        except Exception as e:
            logger.error(f"Failed to extract Yahoo Finance articles: {e}")
        
        return articles
    
    def _extract_marketwatch_articles(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract articles from MarketWatch"""
        articles = []
        
        try:
            # Look for MarketWatch specific elements
            article_links = soup.find_all('a', href=re.compile(r'.*story.*|.*news.*'))
            
            for link in article_links[:10]:
                title = link.get_text(strip=True)
                url = link.get('href')
                
                if url and not url.startswith('http'):
                    url = urljoin(base_url, url)
                
                if title and len(title) > 10:
                    # Try to find summary in parent elements
                    parent = link.parent
                    summary = ""
                    
                    for _ in range(3):  # Look up to 3 levels up
                        if parent:
                            summary_elem = parent.find('p')
                            if summary_elem:
                                summary = summary_elem.get_text(strip=True)
                                break
                            parent = parent.parent
                    
                    articles.append({
                        "title": title,
                        "url": url,
                        "content": summary[:500] or title,
                        "source": "MarketWatch",
                        "published_at": datetime.now(),
                        "relevance_score": 0.82
                    })
        
        except Exception as e:
            logger.error(f"Failed to extract MarketWatch articles: {e}")
        
        return articles
    
    def _extract_bloomberg_articles(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract articles from Bloomberg"""
        articles = []
        
        try:
            # Bloomberg specific selectors
            story_links = soup.find_all('a', href=re.compile(r'.*news.*|.*articles.*'))
            
            for link in story_links[:10]:
                title = link.get_text(strip=True)
                url = link.get('href')
                
                if url and not url.startswith('http'):
                    url = urljoin(base_url, url)
                
                if title and len(title) > 10:
                    articles.append({
                        "title": title,
                        "url": url,
                        "content": title,  # Bloomberg often doesn't have summary on listing pages
                        "source": "Bloomberg",
                        "published_at": datetime.now(),
                        "relevance_score": 0.88
                    })
        
        except Exception as e:
            logger.error(f"Failed to extract Bloomberg articles: {e}")
        
        return articles
    
    def _extract_generic_articles(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Generic article extraction for unknown sites"""
        articles = []
        
        try:
            # Look for common article patterns
            potential_articles = soup.find_all(['article', 'div'], class_=re.compile(r'.*post.*|.*article.*|.*story.*|.*news.*', re.I))
            
            if not potential_articles:
                # Fallback: look for links with meaningful text
                potential_articles = soup.find_all('a', href=True)
            
            for element in potential_articles[:15]:
                if element.name == 'a':
                    title = element.get_text(strip=True)
                    url = element.get('href')
                else:
                    title_elem = element.find(['h1', 'h2', 'h3', 'h4'])
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    link_elem = element.find('a', href=True)
                    url = link_elem.get('href') if link_elem else ""
                
                if url and not url.startswith('http'):
                    url = urljoin(base_url, url)
                
                # Filter out navigation links and short titles
                if (title and len(title) > 15 and len(title) < 200 and 
                    not any(nav_word in title.lower() for nav_word in ['home', 'about', 'contact', 'subscribe', 'login'])):
                    
                    articles.append({
                        "title": title,
                        "url": url,
                        "content": title,
                        "source": urlparse(base_url).netloc,
                        "published_at": datetime.now(),
                        "relevance_score": 0.75
                    })
        
        except Exception as e:
            logger.error(f"Failed to extract generic articles: {e}")
        
        return articles
    
    async def extract_article_content(self, article_url: str) -> Dict[str, Any]:
        """
        Extract full content from an article URL
        
        Args:
            article_url: URL of the article
            
        Returns:
            Article content and metadata
        """
        try:
            # Use trafilatura for content extraction
            content = get_website_text_content(article_url)
            
            if not content:
                return {"error": "No content extracted", "url": article_url}
            
            # Extract metadata
            await self.create_session()
            
            async with self.session.get(article_url, timeout=10) as response:
                if response.status != 200:
                    return {"content": content, "url": article_url}
                
                html_content = await response.text()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = ""
            title_elem = soup.find('title')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Extract publication date
            pub_date = ""
            date_patterns = [
                'time[datetime]',
                '[property="article:published_time"]',
                '[name="date"]',
                '[class*="date"]'
            ]
            
            for pattern in date_patterns:
                date_elem = soup.select_one(pattern)
                if date_elem:
                    pub_date = date_elem.get('datetime') or date_elem.get('content') or date_elem.get_text(strip=True)
                    break
            
            # Extract author
            author = ""
            author_patterns = [
                '[rel="author"]',
                '[property="article:author"]',
                '[class*="author"]',
                '[name="author"]'
            ]
            
            for pattern in author_patterns:
                author_elem = soup.select_one(pattern)
                if author_elem:
                    author = author_elem.get('content') or author_elem.get_text(strip=True)
                    break
            
            return {
                "url": article_url,
                "title": title,
                "content": content,
                "author": author,
                "published_date": pub_date,
                "extraction_timestamp": datetime.now().isoformat(),
                "word_count": len(content.split()),
                "extraction_success": True
            }
            
        except Exception as e:
            logger.error(f"Failed to extract article content from {article_url}: {e}")
            return {
                "url": article_url,
                "error": str(e),
                "extraction_success": False
            }
