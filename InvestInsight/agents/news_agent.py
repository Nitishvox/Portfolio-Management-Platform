import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class NewsAgent:
    """AI agent for financial news gathering and sentiment analysis"""
    
    def __init__(self):
        self.news_cache = {}
        self.sentiment_cache = {}
        
    async def gather_news(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Gather relevant financial news based on query
        
        Args:
            query: Search query for news
            limit: Maximum number of articles to return
            
        Returns:
            List of news articles with metadata and sentiment
        """
        try:
            logger.info(f"Gathering news for query: {query}")
            
            # Check cache
            cache_key = f"{query}_{limit}"
            if cache_key in self.news_cache:
                return self.news_cache[cache_key]
            
            # Simulate news gathering
            await asyncio.sleep(1.0)
            
            news_articles = self._generate_mock_news(query, limit)
            
            # Analyze sentiment for each article
            for article in news_articles:
                article["sentiment_analysis"] = await self._analyze_article_sentiment(article["content"])
            
            # Cache results
            self.news_cache[cache_key] = news_articles
            
            return news_articles
            
        except Exception as e:
            logger.error(f"News gathering failed: {e}")
            return []
    
    def _generate_mock_news(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Generate mock news articles for demonstration"""
        
        base_articles = [
            {
                "title": "Federal Reserve Signals Potential Pause in Rate Hikes",
                "source": "Reuters",
                "url": "https://reuters.com/fed-rate-pause",
                "content": "Federal Reserve officials indicated they may pause interest rate increases as inflation shows signs of cooling. The central bank's latest meeting minutes revealed growing concerns about economic growth...",
                "published_at": datetime.now() - timedelta(hours=2),
                "relevance_score": 0.92,
                "category": "Monetary Policy"
            },
            {
                "title": "Tech Giants Report Strong Q3 Earnings Beat Expectations",
                "source": "Bloomberg",
                "url": "https://bloomberg.com/tech-earnings-q3",
                "content": "Major technology companies including Apple, Microsoft, and Google parent Alphabet reported quarterly earnings that exceeded analyst expectations, driven by strong demand for AI services...",
                "published_at": datetime.now() - timedelta(hours=4),
                "relevance_score": 0.89,
                "category": "Earnings"
            },
            {
                "title": "Oil Prices Surge on Middle East Tensions",
                "source": "MarketWatch",
                "url": "https://marketwatch.com/oil-prices-surge",
                "content": "Crude oil futures jumped 3.5% in early trading as geopolitical tensions in the Middle East raised concerns about supply disruptions. Brent crude touched $95 per barrel...",
                "published_at": datetime.now() - timedelta(hours=6),
                "relevance_score": 0.78,
                "category": "Commodities"
            },
            {
                "title": "AI Chip Demand Drives Semiconductor Rally",
                "source": "CNBC",
                "url": "https://cnbc.com/ai-chip-demand",
                "content": "Semiconductor stocks rallied as demand for AI chips continues to surge. NVIDIA and AMD led gains as data center investments accelerate globally...",
                "published_at": datetime.now() - timedelta(hours=8),
                "relevance_score": 0.85,
                "category": "Technology"
            },
            {
                "title": "Consumer Confidence Hits 6-Month High",
                "source": "Yahoo Finance",
                "url": "https://finance.yahoo.com/consumer-confidence",
                "content": "Consumer confidence jumped to its highest level in six months, supported by a strong job market and easing inflation pressures. The Conference Board index rose to 108.7...",
                "published_at": datetime.now() - timedelta(hours=12),
                "relevance_score": 0.76,
                "category": "Economic Data"
            }
        ]
        
        # Filter and customize based on query
        relevant_articles = []
        for article in base_articles:
            if any(word.lower() in article["title"].lower() or word.lower() in article["content"].lower() 
                   for word in query.split()):
                relevant_articles.append(article)
        
        # If no relevant articles found, return all articles
        if not relevant_articles:
            relevant_articles = base_articles
        
        return relevant_articles[:limit]
    
    async def _analyze_article_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment of a news article"""
        
        # Simulate sentiment analysis
        await asyncio.sleep(0.1)
        
        # Mock sentiment analysis based on keywords
        positive_keywords = ["beat", "surge", "rally", "strong", "growth", "gain", "positive", "bullish", "optimistic"]
        negative_keywords = ["fall", "decline", "crash", "concern", "weak", "loss", "negative", "bearish", "pessimistic"]
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_keywords if word in content_lower)
        negative_count = sum(1 for word in negative_keywords if word in content_lower)
        
        # Calculate sentiment score
        if positive_count > negative_count:
            sentiment_score = 0.3 + (positive_count - negative_count) * 0.1
        elif negative_count > positive_count:
            sentiment_score = -0.3 - (negative_count - positive_count) * 0.1
        else:
            sentiment_score = 0.0
        
        # Clamp between -1 and 1
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        return {
            "sentiment_score": sentiment_score,
            "sentiment_label": self._get_sentiment_label(sentiment_score),
            "confidence": abs(sentiment_score) * 0.8 + 0.2,
            "key_phrases": self._extract_key_phrases(content),
            "emotional_indicators": self._identify_emotional_indicators(content)
        }
    
    def _get_sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score >= 0.2:
            return "Positive"
        elif score <= -0.2:
            return "Negative"
        else:
            return "Neutral"
    
    def _extract_key_phrases(self, content: str) -> List[str]:
        """Extract key phrases from content"""
        # Simple keyword extraction
        financial_keywords = [
            "earnings", "revenue", "profit", "margin", "growth", "volatility",
            "market", "stock", "price", "investment", "economy", "inflation",
            "interest rate", "fed", "gdp", "unemployment"
        ]
        
        found_phrases = []
        content_lower = content.lower()
        for keyword in financial_keywords:
            if keyword in content_lower:
                found_phrases.append(keyword)
        
        return found_phrases[:5]  # Return top 5
    
    def _identify_emotional_indicators(self, content: str) -> List[str]:
        """Identify emotional indicators in content"""
        emotional_words = {
            "excitement": ["surge", "rally", "boom", "soar"],
            "concern": ["worry", "concern", "fear", "anxiety"],
            "optimism": ["positive", "bullish", "confident", "optimistic"],
            "pessimism": ["negative", "bearish", "doubt", "pessimistic"]
        }
        
        indicators = []
        content_lower = content.lower()
        
        for emotion, words in emotional_words.items():
            if any(word in content_lower for word in words):
                indicators.append(emotion)
        
        return indicators
    
    async def analyze_sentiment(self, query: str) -> Dict[str, Any]:
        """
        Analyze overall market sentiment for a specific topic or symbol
        
        Args:
            query: Topic or symbol to analyze sentiment for
            
        Returns:
            Comprehensive sentiment analysis results
        """
        try:
            logger.info(f"Analyzing sentiment for: {query}")
            
            # Gather news articles
            articles = await self.gather_news(query, limit=20)
            
            if not articles:
                return {
                    "query": query,
                    "error": "No articles found for sentiment analysis",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Aggregate sentiment scores
            sentiment_scores = [article["sentiment_analysis"]["sentiment_score"] 
                              for article in articles if "sentiment_analysis" in article]
            
            if not sentiment_scores:
                return {
                    "query": query,
                    "error": "No sentiment data available",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Calculate aggregate metrics
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            positive_articles = len([s for s in sentiment_scores if s > 0.1])
            negative_articles = len([s for s in sentiment_scores if s < -0.1])
            neutral_articles = len(sentiment_scores) - positive_articles - negative_articles
            
            # Generate sentiment distribution
            sentiment_distribution = {
                "positive": positive_articles / len(sentiment_scores) * 100,
                "negative": negative_articles / len(sentiment_scores) * 100,
                "neutral": neutral_articles / len(sentiment_scores) * 100
            }
            
            # Determine overall sentiment trend
            recent_scores = sentiment_scores[-5:] if len(sentiment_scores) >= 5 else sentiment_scores
            trend = "Improving" if recent_scores[-1] > recent_scores[0] else "Declining" if recent_scores[-1] < recent_scores[0] else "Stable"
            
            return {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "overall_sentiment": {
                    "score": avg_sentiment,
                    "label": self._get_sentiment_label(avg_sentiment),
                    "confidence": min(0.9, abs(avg_sentiment) + 0.5)
                },
                "sentiment_distribution": sentiment_distribution,
                "article_count": len(articles),
                "sentiment_trend": trend,
                "key_themes": self._extract_common_themes(articles),
                "most_influential_articles": self._get_most_influential_articles(articles, 3),
                "sentiment_timeline": self._create_sentiment_timeline(articles)
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_common_themes(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Extract common themes from articles"""
        all_phrases = []
        for article in articles:
            if "sentiment_analysis" in article:
                all_phrases.extend(article["sentiment_analysis"]["key_phrases"])
        
        # Count phrase frequency
        phrase_counts = {}
        for phrase in all_phrases:
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        
        # Return top themes
        sorted_phrases = sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)
        return [phrase for phrase, count in sorted_phrases[:5]]
    
    def _get_most_influential_articles(self, articles: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
        """Get most influential articles based on relevance and sentiment strength"""
        
        scored_articles = []
        for article in articles:
            if "sentiment_analysis" in article:
                influence_score = (article["relevance_score"] * 0.6 + 
                                 abs(article["sentiment_analysis"]["sentiment_score"]) * 0.4)
                scored_articles.append((influence_score, article))
        
        # Sort by influence score and return top articles
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [article for score, article in scored_articles[:count]]
    
    def _create_sentiment_timeline(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create timeline of sentiment changes"""
        
        timeline = []
        for article in sorted(articles, key=lambda x: x["published_at"]):
            if "sentiment_analysis" in article:
                timeline.append({
                    "timestamp": article["published_at"].isoformat(),
                    "sentiment_score": article["sentiment_analysis"]["sentiment_score"],
                    "title": article["title"][:50] + "..." if len(article["title"]) > 50 else article["title"]
                })
        
        return timeline[-10:]  # Return last 10 data points
    
    async def get_market_moving_news(self) -> List[Dict[str, Any]]:
        """Get news that could significantly impact markets"""
        
        market_moving_categories = [
            "Federal Reserve", "Interest Rates", "Inflation", "GDP",
            "Employment", "Earnings", "Geopolitical", "Trade"
        ]
        
        news_articles = []
        for category in market_moving_categories[:3]:  # Limit for demo
            articles = await self.gather_news(category, limit=2)
            news_articles.extend(articles)
        
        # Sort by relevance and potential market impact
        news_articles.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return news_articles[:10]
    
    async def monitor_breaking_news(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Monitor for breaking news that might affect specific symbols or markets"""
        
        monitoring_result = {
            "timestamp": datetime.now().isoformat(),
            "monitored_symbols": symbols or ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL"],
            "breaking_news_count": 0,
            "alerts": [],
            "market_impact_assessment": "Low"
        }
        
        # Simulate breaking news monitoring
        if symbols:
            for symbol in symbols[:3]:  # Limit for demo
                articles = await self.gather_news(symbol, limit=1)
                if articles:
                    alert = {
                        "symbol": symbol,
                        "headline": articles[0]["title"],
                        "impact_level": "Medium",
                        "sentiment": articles[0].get("sentiment_analysis", {}).get("sentiment_label", "Neutral"),
                        "recommendation": "Monitor closely"
                    }
                    monitoring_result["alerts"].append(alert)
                    monitoring_result["breaking_news_count"] += 1
        
        return monitoring_result
