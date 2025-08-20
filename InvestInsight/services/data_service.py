import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)

class DataService:
    """Service for fetching and managing financial data"""
    
    def __init__(self):
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 300  # 5 minutes
        
    async def get_stock_data(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        """
        Get comprehensive stock data including price, fundamentals, and technical indicators
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            period: Data period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            
        Returns:
            Dictionary containing stock data
        """
        try:
            cache_key = f"{symbol}_{period}"
            
            # Check cache
            if self._is_cached(cache_key):
                logger.info(f"Returning cached data for {symbol}")
                return self.cache[cache_key]
            
            logger.info(f"Fetching stock data for {symbol}")
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Get stock info
            info = ticker.info
            
            # Get historical data
            hist = ticker.history(period=period)
            
            # Get financial data
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            cashflow = ticker.cashflow
            
            # Process historical data
            historical_data = []
            if not hist.empty:
                for date, row in hist.iterrows():
                    historical_data.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"])
                    })
            
            # Calculate technical indicators
            technical_indicators = self._calculate_technical_indicators(hist)
            
            # Compile result
            stock_data = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "current_price": info.get("currentPrice", hist["Close"].iloc[-1] if not hist.empty else 0),
                "previous_close": info.get("previousClose", 0),
                "change": 0,
                "change_percent": 0,
                "company_info": {
                    "name": info.get("longName", symbol),
                    "sector": info.get("sector", "Unknown"),
                    "industry": info.get("industry", "Unknown"),
                    "market_cap": info.get("marketCap", 0),
                    "employees": info.get("fullTimeEmployees", 0),
                    "website": info.get("website", ""),
                    "description": info.get("longBusinessSummary", "")
                },
                "valuation_metrics": {
                    "pe_ratio": info.get("forwardPE", info.get("trailingPE", 0)),
                    "peg_ratio": info.get("pegRatio", 0),
                    "price_to_book": info.get("priceToBook", 0),
                    "price_to_sales": info.get("priceToSalesTrailing12Months", 0),
                    "enterprise_value": info.get("enterpriseValue", 0),
                    "ev_to_revenue": info.get("enterpriseToRevenue", 0),
                    "ev_to_ebitda": info.get("enterpriseToEbitda", 0)
                },
                "financial_metrics": {
                    "revenue": info.get("totalRevenue", 0),
                    "gross_profit": info.get("grossProfits", 0),
                    "operating_income": info.get("operatingCashflow", 0),
                    "net_income": info.get("netIncomeToCommon", 0),
                    "total_cash": info.get("totalCash", 0),
                    "total_debt": info.get("totalDebt", 0),
                    "free_cashflow": info.get("freeCashflow", 0),
                    "return_on_equity": info.get("returnOnEquity", 0),
                    "return_on_assets": info.get("returnOnAssets", 0)
                },
                "dividend_info": {
                    "dividend_yield": info.get("dividendYield", 0),
                    "dividend_rate": info.get("dividendRate", 0),
                    "payout_ratio": info.get("payoutRatio", 0),
                    "ex_dividend_date": str(info.get("exDividendDate", "")),
                    "five_year_avg_dividend_yield": info.get("fiveYearAvgDividendYield", 0)
                },
                "trading_info": {
                    "volume": info.get("volume", 0),
                    "avg_volume": info.get("averageVolume", 0),
                    "day_high": info.get("dayHigh", 0),
                    "day_low": info.get("dayLow", 0),
                    "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0),
                    "fifty_two_week_low": info.get("fiftyTwoWeekLow", 0),
                    "beta": info.get("beta", 1.0)
                },
                "technical_indicators": technical_indicators,
                "historical_data": historical_data,
                "analyst_info": {
                    "recommendation": info.get("recommendationKey", "hold"),
                    "target_price": info.get("targetMeanPrice", 0),
                    "number_of_analysts": info.get("numberOfAnalystOpinions", 0)
                }
            }
            
            # Calculate change and change percent
            if stock_data["current_price"] and stock_data["previous_close"]:
                stock_data["change"] = stock_data["current_price"] - stock_data["previous_close"]
                stock_data["change_percent"] = (stock_data["change"] / stock_data["previous_close"]) * 100
            
            # Cache the result
            self._cache_data(cache_key, stock_data)
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Failed to fetch stock data for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_technical_indicators(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators from historical data"""
        
        if hist.empty:
            return {}
        
        try:
            # Moving averages
            sma_20 = hist["Close"].rolling(window=20).mean().iloc[-1] if len(hist) >= 20 else None
            sma_50 = hist["Close"].rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else None
            ema_12 = hist["Close"].ewm(span=12).mean().iloc[-1] if len(hist) >= 12 else None
            ema_26 = hist["Close"].ewm(span=26).mean().iloc[-1] if len(hist) >= 26 else None
            
            # RSI calculation
            rsi = self._calculate_rsi(hist["Close"]) if len(hist) >= 14 else None
            
            # MACD calculation
            macd_line = None
            signal_line = None
            if ema_12 is not None and ema_26 is not None:
                macd_line = ema_12 - ema_26
                signal_line = hist["Close"].ewm(span=9).mean().iloc[-1] if len(hist) >= 9 else None
            
            # Bollinger Bands
            bb_middle = sma_20
            bb_std = hist["Close"].rolling(window=20).std().iloc[-1] if len(hist) >= 20 else None
            bb_upper = (bb_middle + 2 * bb_std) if bb_middle is not None and bb_std is not None else None
            bb_lower = (bb_middle - 2 * bb_std) if bb_middle is not None and bb_std is not None else None
            
            return {
                "sma_20": float(sma_20) if sma_20 is not None else None,
                "sma_50": float(sma_50) if sma_50 is not None else None,
                "ema_12": float(ema_12) if ema_12 is not None else None,
                "ema_26": float(ema_26) if ema_26 is not None else None,
                "rsi": float(rsi) if rsi is not None else None,
                "macd": float(macd_line) if macd_line is not None else None,
                "signal": float(signal_line) if signal_line is not None else None,
                "bollinger_upper": float(bb_upper) if bb_upper is not None else None,
                "bollinger_middle": float(bb_middle) if bb_middle is not None else None,
                "bollinger_lower": float(bb_lower) if bb_lower is not None else None
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate technical indicators: {e}")
            return {}
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> Optional[float]:
        """Calculate RSI (Relative Strength Index)"""
        
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not rsi.empty else None
            
        except Exception as e:
            logger.error(f"Failed to calculate RSI: {e}")
            return None
    
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
            logger.info(f"Fetching data for {len(symbols)} symbols")
            
            tasks = [self.get_stock_data(symbol, period) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            stock_data = {}
            for symbol, result in zip(symbols, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to fetch data for {symbol}: {result}")
                    stock_data[symbol] = {"error": str(result)}
                else:
                    stock_data[symbol] = result
            
            return {
                "timestamp": datetime.now().isoformat(),
                "symbols": symbols,
                "data": stock_data
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch multiple stocks data: {e}")
            return {"error": str(e)}
    
    async def get_market_indices(self) -> Dict[str, Any]:
        """Get major market indices data"""
        
        indices = {
            "^GSPC": "S&P 500",
            "^IXIC": "NASDAQ",
            "^DJI": "Dow Jones",
            "^VIX": "VIX"
        }
        
        indices_data = {}
        
        for symbol, name in indices.items():
            try:
                data = await self.get_stock_data(symbol, "5d")
                indices_data[symbol] = {
                    "name": name,
                    "current_price": data.get("current_price", 0),
                    "change": data.get("change", 0),
                    "change_percent": data.get("change_percent", 0)
                }
            except Exception as e:
                logger.error(f"Failed to fetch {name} data: {e}")
                indices_data[symbol] = {"name": name, "error": str(e)}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "indices": indices_data
        }
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if data is cached and not expired"""
        
        if cache_key not in self.cache:
            return False
        
        if cache_key not in self.cache_expiry:
            return False
        
        return datetime.now() < self.cache_expiry[cache_key]
    
    def _cache_data(self, cache_key: str, data: Any):
        """Cache data with expiry time"""
        
        self.cache[cache_key] = data
        self.cache_expiry[cache_key] = datetime.now() + timedelta(seconds=self.cache_duration)
    
    async def clear_cache(self):
        """Clear all cached data"""
        
        self.cache.clear()
        self.cache_expiry.clear()
        logger.info("Data cache cleared")
    
    async def search_stocks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for stocks based on company name or symbol
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching stocks
        """
        try:
            # This is a simplified implementation
            # In a real application, you would use a proper stock search API
            
            common_stocks = [
                {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
                {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Communication"},
                {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary"},
                {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Discretionary"},
                {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
                {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Communication"},
                {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Communication"},
                {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
                {"symbol": "V", "name": "Visa Inc.", "sector": "Financial Services"}
            ]
            
            # Filter based on query
            query_lower = query.lower()
            matching_stocks = []
            
            for stock in common_stocks:
                if (query_lower in stock["symbol"].lower() or 
                    query_lower in stock["name"].lower() or
                    query_lower in stock["sector"].lower()):
                    matching_stocks.append(stock)
            
            return matching_stocks[:limit]
            
        except Exception as e:
            logger.error(f"Stock search failed: {e}")
            return []
