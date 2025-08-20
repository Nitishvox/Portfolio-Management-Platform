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
                            "summary": summary[:500],  # Limit summary length
                            "source": "Yahoo Finance",
                            "timestamp": datetime.now().isoformat(),
                            "sentiment": 0.0  # To be calculated later
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
                        "summary": summary[:500] or title,
                        "source": "MarketWatch",
                        "timestamp": datetime.now().isoformat(),
                        "sentiment": 0.0
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
                        "summary": title,  # Bloomberg often doesn't have summary on listing pages
                        "source": "Bloomberg",
                        "timestamp": datetime.now().isoformat(),
                        "sentiment": 0.0
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
                        "summary": title,
                        "source": urlparse(base_url).netloc,
                        "timestamp": datetime.now().isoformat(),
                        "sentiment": 0.0
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
                '[class*="byline"]'
            ]
            
            for pattern in author_patterns:
                author_elem = soup.select_one(pattern)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    break
            
            return {
                "url": article_url,
                "title": title,
                "content": content,
                "author": author,
                "published_date": pub_date,
                "word_count": len(content.split()),
                "extracted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to extract article content from {article_url}: {e}")
            return {"error": str(e), "url": article_url}
    
    async def scrape_stock_data_from_finviz(self, symbol: str) -> Dict[str, Any]:
        """
        Scrape stock data from Finviz
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock data and metrics
        """
        try:
            url = f"https://finviz.com/quote.ashx?t={symbol}"
            
            await self.create_session()
            
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    return {"error": f"Failed to fetch data for {symbol}"}
                
                html_content = await response.text()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract stock data from Finviz table
            stock_data = {"symbol": symbol, "source": "Finviz"}
            
            # Find the main data table
            table = soup.find('table', class_='snapshot-table2')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    for i in range(0, len(cells), 2):
                        if i + 1 < len(cells):
                            key = cells[i].get_text(strip=True)
                            value = cells[i + 1].get_text(strip=True)
                            stock_data[key.lower().replace(' ', '_')] = value
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Failed to scrape Finviz data for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}
    
    async def search_financial_news(self, query: str, sources: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for financial news across multiple sources
        
        Args:
            query: Search query
            sources: List of source URLs to search
            
        Returns:
            Aggregated news results
        """
        if not sources:
            sources = [
                "https://finance.yahoo.com/news",
                "https://www.marketwatch.com/latest-news",
                "https://www.cnbc.com/world/?region=world"
            ]
        
        all_articles = []
        
        # Search each source
        for source in sources:
            try:
                articles = await self.scrape_financial_news(source)
                
                # Filter articles by query relevance
                relevant_articles = []
                query_words = query.lower().split()
                
                for article in articles:
                    title_lower = article.get("title", "").lower()
                    summary_lower = article.get("summary", "").lower()
                    
                    # Check if any query words are in title or summary
                    relevance_score = 0
                    for word in query_words:
                        if word in title_lower:
                            relevance_score += 2
                        if word in summary_lower:
                            relevance_score += 1
                    
                    if relevance_score > 0:
                        article["relevance_score"] = relevance_score
                        relevant_articles.append(article)
                
                all_articles.extend(relevant_articles)
                
            except Exception as e:
                logger.error(f"Failed to search {source}: {e}")
        
        # Sort by relevance and remove duplicates
        all_articles.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        # Remove duplicates based on title similarity
        unique_articles = []
        seen_titles = set()
        
        for article in all_articles:
            title = article.get("title", "").lower()
            title_words = set(title.split())
            
            # Check for similar titles
            is_duplicate = False
            for seen_title in seen_titles:
                seen_words = set(seen_title.split())
                if len(title_words & seen_words) / len(title_words | seen_words) > 0.7:  # 70% similarity
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
                seen_titles.add(title)
        
        return unique_articles[:20]  # Return top 20 unique articles

# Utility functions for specific financial sites
def scrape_yahoo_finance_quote(symbol: str) -> Dict[str, Any]:
    """Scrape basic quote data from Yahoo Finance"""
    try:
        url = f"https://finance.yahoo.com/quote/{symbol}"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return {"error": "Failed to fetch data"}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract basic quote data
        quote_data = {"symbol": symbol}
        
        # Current price
        price_elem = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
        if price_elem:
            quote_data["current_price"] = price_elem.get_text(strip=True)
        
        # Change
        change_elem = soup.find('fin-streamer', {'data-field': 'regularMarketChange'})
        if change_elem:
            quote_data["change"] = change_elem.get_text(strip=True)
        
        # Change percent
        change_pct_elem = soup.find('fin-streamer', {'data-field': 'regularMarketChangePercent'})
        if change_pct_elem:
            quote_data["change_percent"] = change_pct_elem.get_text(strip=True)
        
        return quote_data
        
    except Exception as e:
        logger.error(f"Failed to scrape Yahoo Finance quote for {symbol}: {e}")
        return {"error": str(e), "symbol": symbol}

def extract_earnings_data(company_name: str) -> Dict[str, Any]:
    """Extract earnings data from financial news sites"""
    try:
        # This is a simplified implementation
        # In production, you'd want to search multiple sources for earnings data
        
        search_query = f"{company_name} earnings report"
        
        # Use Google search to find recent earnings reports
        search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract search results (simplified)
            results = []
            for result in soup.find_all('div', class_='g')[:5]:
                title_elem = result.find('h3')
                link_elem = result.find('a')
                
                if title_elem and link_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "url": link_elem.get('href'),
                        "source": "Google Search Results"
                    })
            
            return {
                "company": company_name,
                "search_results": results,
                "timestamp": datetime.now().isoformat()
            }
        
        return {"error": "Failed to search for earnings data"}
        
    except Exception as e:
        logger.error(f"Failed to extract earnings data for {company_name}: {e}")
        return {"error": str(e), "company": company_name}
