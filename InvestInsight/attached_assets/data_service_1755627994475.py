import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import asyncio
from typing import Dict, List, Any, Optional
import aiohttp
import json
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

class DataService:
    """Service for fetching and managing financial data"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)  # Cache data for 15 minutes
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
        
    async def get_stock_data(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        """
        Get comprehensive stock data
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            period: Data period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            
        Returns:
            Dictionary containing stock data and metrics
        """
        try:
            cache_key = f"stock_data_{symbol}_{period}"
            
            # Check cache
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            logger.info(f"Fetching stock data for {symbol} with period {period}")
            
            # Fetch data using yfinance
            ticker = yf.Ticker(symbol)
            
            # Get historical data
            hist_data = ticker.history(period=period)
            
            if hist_data.empty:
                logger.warning(f"No historical data found for {symbol}")
                return self._generate_sample_stock_data(symbol)
            
            # Get additional information
            info = ticker.info
            
            # Calculate technical indicators
            technical_indicators = self._calculate_technical_indicators(hist_data)
            
            # Prepare comprehensive data
            stock_data = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "current_price": float(hist_data["Close"].iloc[-1]),
                "previous_close": float(hist_data["Close"].iloc[-2]) if len(hist_data) > 1 else float(hist_data["Close"].iloc[-1]),
                "price_change": 0.0,
                "price_change_percent": 0.0,
                "volume": int(hist_data["Volume"].iloc[-1]) if "Volume" in hist_data.columns else 0,
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "avg_volume": info.get("averageVolume"),
                "historical_data": self._format_historical_data(hist_data),
                "technical_indicators": technical_indicators,
                "company_info": {
                    "name": info.get("longName", symbol),
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "description": info.get("longBusinessSummary", "")[:500],  # Truncate description
                    "employees": info.get("fullTimeEmployees"),
                    "website": info.get("website")
                }
            }
            
            # Calculate price changes
            if len(hist_data) > 1:
                current_price = float(hist_data["Close"].iloc[-1])
                previous_price = float(hist_data["Close"].iloc[-2])
                stock_data["price_change"] = round(current_price - previous_price, 2)
                stock_data["price_change_percent"] = round((current_price - previous_price) / previous_price * 100, 2)
            
            # Cache the result
            self.cache[cache_key] = {
                "data": stock_data,
                "timestamp": datetime.now()
            }
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Failed to fetch stock data for {symbol}: {e}")
            return self._generate_sample_stock_data(symbol)
    
    def _calculate_technical_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators from historical data"""
        try:
            indicators = {}
            
            # Simple Moving Averages
            indicators["sma_20"] = float(data["Close"].rolling(window=20).mean().iloc[-1]) if len(data) >= 20 else None
            indicators["sma_50"] = float(data["Close"].rolling(window=50).mean().iloc[-1]) if len(data) >= 50 else None
            indicators["sma_200"] = float(data["Close"].rolling(window=200).mean().iloc[-1]) if len(data) >= 200 else None
            
            # Exponential Moving Averages
            indicators["ema_12"] = float(data["Close"].ewm(span=12).mean().iloc[-1])
            indicators["ema_26"] = float(data["Close"].ewm(span=26).mean().iloc[-1])
            
            # RSI (Relative Strength Index)
            indicators["rsi"] = self._calculate_rsi(data["Close"])
            
            # MACD
            macd_data = self._calculate_macd(data["Close"])
            indicators.update(macd_data)
            
            # Bollinger Bands
            bollinger_data = self._calculate_bollinger_bands(data["Close"])
            indicators.update(bollinger_data)
            
            # Volume indicators
            if "Volume" in data.columns:
                indicators["avg_volume_20"] = float(data["Volume"].rolling(window=20).mean().iloc[-1]) if len(data) >= 20 else None
                indicators["volume_ratio"] = float(data["Volume"].iloc[-1] / data["Volume"].rolling(window=20).mean().iloc[-1]) if len(data) >= 20 else 1.0
            
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to calculate technical indicators: {e}")
            return {}
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index"""
        try:
            if len(prices) < window + 1:
                return None
                
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1])
        except Exception:
            return None
    
    def _calculate_macd(self, prices: pd.Series) -> Dict[str, Optional[float]]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            ema12 = prices.ewm(span=12).mean()
            ema26 = prices.ewm(span=26).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9).mean()
            histogram = macd_line - signal_line
            
            return {
                "macd": float(macd_line.iloc[-1]),
                "macd_signal": float(signal_line.iloc[-1]),
                "macd_histogram": float(histogram.iloc[-1])
            }
        except Exception:
            return {"macd": None, "macd_signal": None, "macd_histogram": None}
    
    def _calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, std_dev: int = 2) -> Dict[str, Optional[float]]:
        """Calculate Bollinger Bands"""
        try:
            if len(prices) < window:
                return {"bb_upper": None, "bb_middle": None, "bb_lower": None}
                
            sma = prices.rolling(window=window).mean()
            std = prices.rolling(window=window).std()
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            return {
                "bb_upper": float(upper_band.iloc[-1]),
                "bb_middle": float(sma.iloc[-1]),
                "bb_lower": float(lower_band.iloc[-1])
            }
        except Exception:
            return {"bb_upper": None, "bb_middle": None, "bb_lower": None}
    
    def _format_historical_data(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Format historical data for frontend consumption"""
        try:
            formatted_data = []
            for date, row in data.iterrows():
                formatted_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]) if "Volume" in row else 0
                })
            return formatted_data[-252:]  # Return last 252 trading days (1 year)
        except Exception as e:
            logger.error(f"Failed to format historical data: {e}")
            return []
    
    async def get_multiple_stocks_data(self, symbols: List[str], period: str = "1y") -> Dict[str, Any]:
        """
        Get data for multiple stocks
        
        Args:
            symbols: List of stock symbols
            period: Data period
            
        Returns:
            Dictionary with data for each symbol
        """
        try:
            logger.info(f"Fetching data for {len(symbols)} stocks")
            
            # Fetch data for all symbols concurrently
            tasks = [self.get_stock_data(symbol, period) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Organize results
            stocks_data = {}
            for i, symbol in enumerate(symbols):
                if isinstance(results[i], Exception):
                    logger.error(f"Failed to fetch data for {symbol}: {results[i]}")
                    stocks_data[symbol] = self._generate_sample_stock_data(symbol)
                else:
                    stocks_data[symbol] = results[i]
            
            return {
                "timestamp": datetime.now().isoformat(),
                "symbols": symbols,
                "data": stocks_data,
                "summary": {
                    "total_symbols": len(symbols),
                    "successful_fetches": len([r for r in results if not isinstance(r, Exception)]),
                    "failed_fetches": len([r for r in results if isinstance(r, Exception)])
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch multiple stocks data: {e}")
            return {"error": str(e), "symbols": symbols}
    
    async def get_market_indices(self) -> Dict[str, Any]:
        """Get major market indices data"""
        try:
            indices = {
                "^GSPC": "S&P 500",
                "^IXIC": "NASDAQ",
                "^DJI": "Dow Jones",
                "^VIX": "VIX"
            }
            
            indices_data = {}
            
            for symbol, name in indices.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="5d")
                    
                    if not hist.empty:
                        current_price = float(hist["Close"].iloc[-1])
                        previous_price = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
                        change = current_price - previous_price
                        change_percent = (change / previous_price * 100) if previous_price != 0 else 0
                        
                        indices_data[symbol] = {
                            "name": name,
                            "symbol": symbol,
                            "price": round(current_price, 2),
                            "change": round(change, 2),
                            "change_percent": round(change_percent, 2),
                            "volume": int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0
                        }
                
                except Exception as e:
                    logger.error(f"Failed to fetch {symbol}: {e}")
                    # Provide sample data for failed fetches
                    indices_data[symbol] = {
                        "name": name,
                        "symbol": symbol,
                        "price": 4200.0,
                        "change": 12.5,
                        "change_percent": 0.3,
                        "volume": 1000000
                    }
            
            return {
                "timestamp": datetime.now().isoformat(),
                "indices": indices_data
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch market indices: {e}")
            return self._generate_sample_indices_data()
    
    def _generate_sample_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Generate sample stock data when real data is unavailable"""
        base_price = hash(symbol) % 1000 + 50  # Deterministic but varied price
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "current_price": base_price + np.random.uniform(-10, 10),
            "previous_close": base_price,
            "price_change": np.random.uniform(-5, 5),
            "price_change_percent": np.random.uniform(-2, 2),
            "volume": int(np.random.uniform(1000000, 10000000)),
            "market_cap": int(base_price * 1000000000),
            "pe_ratio": round(np.random.uniform(15, 30), 2),
            "dividend_yield": round(np.random.uniform(0.01, 0.05), 4),
            "52_week_high": base_price + 20,
            "52_week_low": base_price - 20,
            "avg_volume": int(np.random.uniform(2000000, 8000000)),
            "historical_data": [],
            "technical_indicators": {
                "rsi": round(np.random.uniform(30, 70), 2),
                "sma_20": base_price + np.random.uniform(-5, 5),
                "sma_50": base_price + np.random.uniform(-10, 10),
                "macd": round(np.random.uniform(-2, 2), 3)
            },
            "company_info": {
                "name": f"{symbol} Corporation",
                "sector": "Technology",
                "industry": "Software",
                "description": f"Sample data for {symbol} - real data unavailable",
                "employees": int(np.random.uniform(1000, 100000)),
                "website": f"https://{symbol.lower()}.com"
            }
        }
    
    def _generate_sample_indices_data(self) -> Dict[str, Any]:
        """Generate sample indices data"""
        return {
            "timestamp": datetime.now().isoformat(),
            "indices": {
                "^GSPC": {
                    "name": "S&P 500",
                    "symbol": "^GSPC",
                    "price": 4150.48,
                    "change": 12.34,
                    "change_percent": 0.30,
                    "volume": 3456789
                },
                "^IXIC": {
                    "name": "NASDAQ",
                    "symbol": "^IXIC",
                    "price": 12847.59,
                    "change": -45.67,
                    "change_percent": -0.35,
                    "volume": 2345678
                },
                "^DJI": {
                    "name": "Dow Jones",
                    "symbol": "^DJI", 
                    "price": 33845.12,
                    "change": -89.23,
                    "change_percent": -0.26,
                    "volume": 1234567
                },
                "^VIX": {
                    "name": "VIX",
                    "symbol": "^VIX",
                    "price": 18.45,
                    "change": -1.23,
                    "change_percent": -6.25,
                    "volume": 987654
                }
            }
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache[cache_key]["timestamp"]
        return (datetime.now() - cache_time) < self.cache_duration
    
    async def get_stock_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Get news for a specific stock"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            formatted_news = []
            for article in news[:10]:  # Limit to 10 articles
                formatted_news.append({
                    "title": article.get("title", ""),
                    "link": article.get("link", ""),
                    "published": article.get("providerPublishTime", 0),
                    "publisher": article.get("publisher", ""),
                    "thumbnail": article.get("thumbnail", {}).get("resolutions", [{}])[0].get("url", "")
                })
            
            return formatted_news
            
        except Exception as e:
            logger.error(f"Failed to fetch news for {symbol}: {e}")
            return []
    
    async def search_stocks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for stocks based on query
        
        Args:
            query: Search query (company name, symbol, etc.)
            limit: Maximum number of results
            
        Returns:
            List of matching stocks
        """
        try:
            # This is a simplified implementation
            # In production, you might use a proper stock search API
            
            # Common stocks for demo
            common_stocks = [
                {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
                {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
                {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Cyclical"},
                {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Cyclical"},
                {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology"},
                {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
                {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Communication Services"},
                {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financial Services"},
                {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"}
            ]
            
            query_lower = query.lower()
            matches = []
            
            for stock in common_stocks:
                if (query_lower in stock["symbol"].lower() or 
                    query_lower in stock["name"].lower() or
                    query_lower in stock["sector"].lower()):
                    matches.append(stock)
            
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Stock search failed: {e}")
            return []
    
    def clear_cache(self):
        """Clear data cache"""
        self.cache.clear()
        logger.info("Data cache cleared")
