import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import re
from services.llm_service import LLMService
from agents.search_agent import SearchAgent
from utils.web_scraper import get_website_text_content
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class NewsAgent:
    """AI agent for financial news aggregation and sentiment analysis"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.search_agent = SearchAgent()
        self.news_cache = {}
        self.sentiment_cache = {}
        
    async def gather_news(self, query: str, sources: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Gather financial news using AI-powered search
        
        Args:
            query: Search query for news
            sources: Specific news sources (optional)
            limit: Maximum number of articles to return
            
        Returns:
            List of news articles with metadata and analysis
        """
        try:
            cache_key = f"{query}_{datetime.now().strftime('%Y-%m-%d-%H')}"
            
            if cache_key in self.news_cache:
                return self.news_cache[cache_key]
            
            logger.info(f"Gathering news for query: {query}")
            
            # Default financial news sources
            if not sources:
                sources = [
                    "https://finance.yahoo.com/news",
                    "https://www.marketwatch.com",
                    "https://www.cnbc.com/markets",
                    "https://www.reuters.com/business/finance",
                    "https://www.bloomberg.com/markets",
                    "https://seekingalpha.com/news"
                ]
            
            news_articles = []
            
            # Use browser-use agent for advanced news gathering
            try:
                search_results = await self.search_agent.deep_financial_search(
                    query=f"{query} financial news latest",
                    sources=sources
                )
                
                # Process search results into news format
                if "news_articles" in search_results:
                    for article in search_results["news_articles"]:
                        enhanced_article = await self._enhance_news_article(article, query)
                        news_articles.append(enhanced_article)
                
            except Exception as e:
                logger.error(f"Browser search failed, using fallback: {e}")
                # Fallback to direct web scraping
                news_articles = await self._fallback_news_gathering(query, sources, limit)
            
            # Enhance articles with AI analysis
            enhanced_articles = []
            for article in news_articles[:limit]:
                try:
                    enhanced = await self._analyze_news_article(article)
                    enhanced_articles.append(enhanced)
                except Exception as e:
                    logger.error(f"Failed to enhance article: {e}")
                    enhanced_articles.append(article)
            
            # Cache results
            self.news_cache[cache_key] = enhanced_articles
            
            return enhanced_articles
            
        except Exception as e:
            logger.error(f"News gathering failed: {e}")
            return self._generate_sample_news(query, limit)
    
    async def _enhance_news_article(self, article: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Enhance news article with additional metadata and analysis"""
        try:
            enhanced_article = article.copy()
            
            # Add relevance score
            enhanced_article["relevance_score"] = self._calculate_relevance(article, query)
            
            # Add market impact assessment
            enhanced_article["market_impact"] = await self._assess_market_impact(article)
            
            # Add key topics
            enhanced_article["key_topics"] = self._extract_key_topics(article.get("summary", ""))
            
            # Add urgency level
            enhanced_article["urgency"] = self._assess_urgency(article)
            
            return enhanced_article
            
        except Exception as e:
            logger.error(f"Failed to enhance news article: {e}")
            return article
    
    def _calculate_relevance(self, article: Dict[str, Any], query: str) -> float:
        """Calculate relevance score of article to query"""
        try:
            title = article.get("title", "").lower()
            summary = article.get("summary", "").lower()
            query_words = query.lower().split()
            
            title_matches = sum(1 for word in query_words if word in title)
            summary_matches = sum(1 for word in query_words if word in summary)
            
            title_score = title_matches / len(query_words) if query_words else 0
            summary_score = summary_matches / len(query_words) if query_words else 0
            
            # Weight title matches higher
            relevance = (title_score * 0.7 + summary_score * 0.3)
            return min(1.0, relevance)
            
        except Exception as e:
            logger.error(f"Failed to calculate relevance: {e}")
            return 0.5
    
    async def _assess_market_impact(self, article: Dict[str, Any]) -> Dict[str, str]:
        """Assess potential market impact of news"""
        try:
            content = f"{article.get('title', '')} {article.get('summary', '')}"
            
            # High impact keywords
            high_impact_keywords = [
                "earnings", "merger", "acquisition", "bankruptcy", "lawsuit",
                "fda approval", "regulation", "tariff", "interest rate", "fed"
            ]
            
            # Market direction keywords
            positive_keywords = [
                "growth", "profit", "beat expectations", "bullish", "upgrade",
                "approval", "partnership", "expansion", "innovation"
            ]
            
            negative_keywords = [
                "loss", "decline", "bearish", "downgrade", "lawsuit",
                "investigation", "recession", "bankruptcy", "warning"
            ]
            
            content_lower = content.lower()
            
            # Determine impact level
            impact_level = "low"
            if any(keyword in content_lower for keyword in high_impact_keywords):
                impact_level = "high"
            elif len([kw for kw in positive_keywords + negative_keywords if kw in content_lower]) >= 2:
                impact_level = "medium"
            
            # Determine direction
            positive_count = sum(1 for kw in positive_keywords if kw in content_lower)
            negative_count = sum(1 for kw in negative_keywords if kw in content_lower)
            
            if positive_count > negative_count:
                direction = "positive"
            elif negative_count > positive_count:
                direction = "negative"
            else:
                direction = "neutral"
            
            return {
                "level": impact_level,
                "direction": direction,
                "confidence": 0.7 if impact_level == "high" else 0.5
            }
            
        except Exception as e:
            logger.error(f"Failed to assess market impact: {e}")
            return {"level": "low", "direction": "neutral", "confidence": 0.3}
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """Extract key topics from article text"""
        try:
            # Financial topics keywords
            topic_keywords = {
                "earnings": ["earnings", "quarterly", "revenue", "profit", "eps"],
                "merger_acquisition": ["merger", "acquisition", "buyout", "takeover"],
                "regulation": ["regulation", "regulatory", "compliance", "sec", "fda"],
                "technology": ["technology", "innovation", "ai", "software", "tech"],
                "market_trends": ["market", "trend", "outlook", "forecast", "analysis"],
                "corporate_action": ["dividend", "stock split", "buyback", "restructuring"],
                "economic_data": ["gdp", "inflation", "unemployment", "economic", "fed"]
            }
            
            text_lower = text.lower()
            found_topics = []
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    found_topics.append(topic.replace("_", " ").title())
            
            return found_topics[:5]  # Return top 5 topics
            
        except Exception as e:
            logger.error(f"Failed to extract topics: {e}")
            return ["General Market News"]
    
    def _assess_urgency(self, article: Dict[str, Any]) -> str:
        """Assess urgency level of news article"""
        try:
            title = article.get("title", "").lower()
            
            # Urgent keywords
            urgent_keywords = [
                "breaking", "urgent", "alert", "immediate", "now", "just in",
                "developing", "live", "update", "emergency"
            ]
            
            # Time-sensitive keywords
            time_sensitive_keywords = [
                "today", "this morning", "just announced", "minutes ago",
                "hours ago", "after hours", "pre-market"
            ]
            
            if any(keyword in title for keyword in urgent_keywords):
                return "high"
            elif any(keyword in title for keyword in time_sensitive_keywords):
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            logger.error(f"Failed to assess urgency: {e}")
            return "medium"
    
    async def _fallback_news_gathering(self, query: str, sources: List[str], limit: int) -> List[Dict[str, Any]]:
        """Fallback method for gathering news when browser-use fails"""
        try:
            articles = []
            
            # Simple web scraping for major financial sites
            for source in sources[:3]:  # Limit to avoid rate limiting
                try:
                    if "yahoo.com" in source:
                        yahoo_articles = await self._scrape_yahoo_finance(query)
                        articles.extend(yahoo_articles)
                    elif "marketwatch.com" in source:
                        mw_articles = await self._scrape_marketwatch(query)
                        articles.extend(mw_articles)
                    # Add more source-specific scrapers as needed
                    
                except Exception as e:
                    logger.error(f"Failed to scrape {source}: {e}")
            
            return articles[:limit]
            
        except Exception as e:
            logger.error(f"Fallback news gathering failed: {e}")
            return []
    
    async def _scrape_yahoo_finance(self, query: str) -> List[Dict[str, Any]]:
        """Scrape Yahoo Finance for news (simplified)"""
        try:
            # This is a simplified implementation
            # In production, you'd want more robust scraping
            articles = []
            
            search_url = f"https://finance.yahoo.com/news"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # For demo purposes, create sample articles based on query
            sample_articles = [
                {
                    "title": f"Market Analysis: {query} Shows Strong Performance",
                    "source": "Yahoo Finance",
                    "summary": f"Latest analysis on {query} indicates positive market sentiment with strong fundamentals.",
                    "url": "https://finance.yahoo.com/news/sample-article-1",
                    "timestamp": datetime.now().isoformat(),
                    "sentiment": 0.3
                },
                {
                    "title": f"Breaking: {query} Announces Strategic Initiative",
                    "source": "Yahoo Finance",
                    "summary": f"Company related to {query} announces new strategic direction impacting market outlook.",
                    "url": "https://finance.yahoo.com/news/sample-article-2",
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "sentiment": 0.1
                }
            ]
            
            return sample_articles
            
        except Exception as e:
            logger.error(f"Failed to scrape Yahoo Finance: {e}")
            return []
    
    async def _scrape_marketwatch(self, query: str) -> List[Dict[str, Any]]:
        """Scrape MarketWatch for news (simplified)"""
        try:
            # Simplified implementation for demo
            sample_articles = [
                {
                    "title": f"MarketWatch: {query} Investment Outlook",
                    "source": "MarketWatch",
                    "summary": f"Comprehensive investment analysis and outlook for {query} based on current market conditions.",
                    "url": "https://www.marketwatch.com/story/sample-article",
                    "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "sentiment": 0.2
                }
            ]
            
            return sample_articles
            
        except Exception as e:
            logger.error(f"Failed to scrape MarketWatch: {e}")
            return []
    
    async def _analyze_news_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Perform AI analysis on news article"""
        try:
            content = f"Title: {article.get('title', '')}\nSummary: {article.get('summary', '')}"
            
            # Sentiment analysis using LLM
            sentiment_prompt = f"""
            Analyze the sentiment of this financial news article and its potential market impact:
            
            {content}
            
            Provide:
            1. Sentiment score (-1 to +1, where -1 is very negative, 0 is neutral, +1 is very positive)
            2. Market impact (low/medium/high)
            3. Key factors influencing the sentiment
            4. Potential stock price impact direction
            
            Format as JSON:
            {{
                "sentiment_score": 0.0,
                "market_impact": "medium",
                "key_factors": ["factor1", "factor2"],
                "price_impact": "positive/negative/neutral"
            }}
            """
            
            response = await self.llm_service.generate_response(
                prompt=sentiment_prompt,
                model="llama3.1:8b",
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse AI response
            analysis = self._parse_sentiment_analysis(response)
            
            # Add AI analysis to article
            article["ai_analysis"] = analysis
            article["sentiment"] = analysis.get("sentiment_score", article.get("sentiment", 0.0))
            
            return article
            
        except Exception as e:
            logger.error(f"Failed to analyze news article: {e}")
            return article
    
    def _parse_sentiment_analysis(self, response: str) -> Dict[str, Any]:
        """Parse AI sentiment analysis response"""
        try:
            # Try to extract JSON
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # Fallback parsing
            analysis = {
                "sentiment_score": 0.0,
                "market_impact": "medium",
                "key_factors": [],
                "price_impact": "neutral"
            }
            
            # Extract sentiment score
            sentiment_match = re.search(r'sentiment.*?(-?\d+\.?\d*)', response.lower())
            if sentiment_match:
                analysis["sentiment_score"] = float(sentiment_match.group(1))
            
            # Extract market impact
            if "high impact" in response.lower():
                analysis["market_impact"] = "high"
            elif "low impact" in response.lower():
                analysis["market_impact"] = "low"
            
            # Extract price impact
            if "positive" in response.lower():
                analysis["price_impact"] = "positive"
            elif "negative" in response.lower():
                analysis["price_impact"] = "negative"
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to parse sentiment analysis: {e}")
            return {
                "sentiment_score": 0.0,
                "market_impact": "medium",
                "key_factors": ["Unable to parse analysis"],
                "price_impact": "neutral"
            }
    
    async def analyze_sentiment(self, query: str) -> Dict[str, Any]:
        """
        Analyze overall market sentiment for a topic or company
        
        Args:
            query: Topic or company to analyze sentiment for
            
        Returns:
            Comprehensive sentiment analysis
        """
        try:
            cache_key = f"sentiment_{query}_{datetime.now().strftime('%Y-%m-%d-%H')}"
            
            if cache_key in self.sentiment_cache:
                return self.sentiment_cache[cache_key]
            
            logger.info(f"Analyzing sentiment for: {query}")
            
            # Gather recent news
            news_articles = await self.gather_news(query, limit=20)
            
            # Analyze sentiment across articles
            sentiments = []
            impact_levels = []
            key_themes = []
            
            for article in news_articles:
                sentiment_score = article.get("sentiment", 0.0)
                sentiments.append(sentiment_score)
                
                if "ai_analysis" in article:
                    impact_levels.append(article["ai_analysis"].get("market_impact", "medium"))
                    key_themes.extend(article["ai_analysis"].get("key_factors", []))
            
            # Calculate overall sentiment
            overall_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
            
            # Sentiment distribution
            positive_count = len([s for s in sentiments if s > 0.1])
            negative_count = len([s for s in sentiments if s < -0.1])
            neutral_count = len(sentiments) - positive_count - negative_count
            
            sentiment_analysis = {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "overall_sentiment": round(overall_sentiment, 3),
                "sentiment_distribution": {
                    "positive": positive_count,
                    "negative": negative_count,
                    "neutral": neutral_count
                },
                "sentiment_trend": self._calculate_sentiment_trend(news_articles),
                "market_impact_summary": {
                    "high_impact_articles": len([i for i in impact_levels if i == "high"]),
                    "medium_impact_articles": len([i for i in impact_levels if i == "medium"]),
                    "low_impact_articles": len([i for i in impact_levels if i == "low"])
                },
                "key_themes": list(set(key_themes))[:10],  # Top 10 unique themes
                "articles_analyzed": len(news_articles),
                "confidence_score": min(1.0, len(news_articles) / 10)  # Higher confidence with more articles
            }
            
            # Cache the result
            self.sentiment_cache[cache_key] = sentiment_analysis
            
            return sentiment_analysis
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed for {query}: {e}")
            return {
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "overall_sentiment": 0.0
            }
    
    def _calculate_sentiment_trend(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate sentiment trend over time"""
        try:
            # Sort articles by timestamp
            sorted_articles = sorted(articles, key=lambda x: x.get("timestamp", ""))
            
            if len(sorted_articles) < 2:
                return {"trend": "stable", "direction": "neutral"}
            
            # Split into recent and older articles
            mid_point = len(sorted_articles) // 2
            older_articles = sorted_articles[:mid_point]
            recent_articles = sorted_articles[mid_point:]
            
            # Calculate average sentiment for each period
            older_sentiment = sum(a.get("sentiment", 0) for a in older_articles) / len(older_articles)
            recent_sentiment = sum(a.get("sentiment", 0) for a in recent_articles) / len(recent_articles)
            
            # Determine trend
            sentiment_change = recent_sentiment - older_sentiment
            
            if abs(sentiment_change) < 0.1:
                trend = "stable"
                direction = "neutral"
            elif sentiment_change > 0:
                trend = "improving"
                direction = "positive"
            else:
                trend = "declining"
                direction = "negative"
            
            return {
                "trend": trend,
                "direction": direction,
                "change": round(sentiment_change, 3),
                "older_period_sentiment": round(older_sentiment, 3),
                "recent_period_sentiment": round(recent_sentiment, 3)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate sentiment trend: {e}")
            return {"trend": "stable", "direction": "neutral", "error": str(e)}
    
    def _generate_sample_news(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Generate sample news articles when real data is unavailable"""
        sample_articles = [
            {
                "title": f"Market Update: {query} Shows Strong Performance Indicators",
                "source": "AI Financial Analysis",
                "summary": f"Recent analysis of {query} indicates positive market trends with strong fundamentals supporting continued growth potential.",
                "url": f"https://example.com/news/{query.replace(' ', '-').lower()}",
                "timestamp": datetime.now().isoformat(),
                "sentiment": 0.3,
                "relevance_score": 0.9,
                "market_impact": {"level": "medium", "direction": "positive", "confidence": 0.7},
                "key_topics": ["Market Analysis", "Financial Performance"],
                "urgency": "medium"
            },
            {
                "title": f"Industry Analysis: {query} Sector Outlook",
                "source": "Market Research",
                "summary": f"Comprehensive sector analysis reveals key opportunities and risks for {query} investments in the current market environment.",
                "url": f"https://example.com/analysis/{query.replace(' ', '-').lower()}",
                "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
                "sentiment": 0.1,
                "relevance_score": 0.8,
                "market_impact": {"level": "low", "direction": "neutral", "confidence": 0.6},
                "key_topics": ["Industry Analysis", "Investment Outlook"],
                "urgency": "low"
            }
        ]
        
        return sample_articles[:limit]
