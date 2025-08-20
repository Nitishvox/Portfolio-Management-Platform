import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
from services.portfolio_service import PortfolioService
from services.llm_service import LLMService
from services.data_service import DataService

logger = logging.getLogger(__name__)

class PortfolioAgent:
    """AI agent for portfolio management and optimization"""
    
    def __init__(self):
        self.portfolio_service = PortfolioService()
        self.llm_service = LLMService()
        self.data_service = DataService()
        self.optimization_cache = {}
        
    async def create_optimized_portfolio(self, 
                                       investment_amount: float,
                                       risk_tolerance: float,
                                       investment_horizon: str,
                                       sectors: List[str] = None,
                                       exclude_symbols: List[str] = None) -> Dict[str, Any]:
        """
        Create an optimized portfolio based on user preferences
        
        Args:
            investment_amount: Total amount to invest
            risk_tolerance: Risk level (0.0 = conservative, 1.0 = aggressive)
            investment_horizon: 'short', 'medium', 'long'
            sectors: Preferred sectors (optional)
            exclude_symbols: Symbols to exclude (optional)
            
        Returns:
            Optimized portfolio with allocations and analysis
        """
        try:
            # Generate cache key
            cache_key = f"{investment_amount}_{risk_tolerance}_{investment_horizon}_{'-'.join(sectors or [])}_{datetime.now().strftime('%Y-%m-%d')}"
            
            if cache_key in self.optimization_cache:
                return self.optimization_cache[cache_key]
            
            logger.info(f"Creating optimized portfolio: ${investment_amount}, risk: {risk_tolerance}, horizon: {investment_horizon}")
            
            # Get universe of stocks based on preferences
            stock_universe = await self._get_stock_universe(sectors, exclude_symbols)
            
            # Generate AI-driven stock selection
            selected_stocks = await self._ai_stock_selection(stock_universe, risk_tolerance, investment_horizon)
            
            # Optimize portfolio using PyPortfolioOpt
            optimization_result = await self.portfolio_service.optimize_portfolio(
                symbols=selected_stocks,
                investment_amount=investment_amount,
                risk_tolerance=risk_tolerance
            )
            
            # Enhanced portfolio analysis
            portfolio_analysis = await self._analyze_portfolio_composition(optimization_result, risk_tolerance)
            
            # Generate AI insights and recommendations
            ai_insights = await self._generate_portfolio_insights(optimization_result, portfolio_analysis)
            
            final_portfolio = {
                "created_at": datetime.now().isoformat(),
                "investment_amount": investment_amount,
                "risk_tolerance": risk_tolerance,
                "investment_horizon": investment_horizon,
                "preferred_sectors": sectors or [],
                "optimization_result": optimization_result,
                "portfolio_analysis": portfolio_analysis,
                "ai_insights": ai_insights,
                "rebalancing_schedule": self._generate_rebalancing_schedule(investment_horizon),
                "monitoring_metrics": self._define_monitoring_metrics(),
                "performance_benchmarks": self._set_performance_benchmarks(risk_tolerance)
            }
            
            # Cache the result
            self.optimization_cache[cache_key] = final_portfolio
            
            return final_portfolio
            
        except Exception as e:
            logger.error(f"Failed to create optimized portfolio: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
    
    async def _get_stock_universe(self, sectors: List[str] = None, exclude_symbols: List[str] = None) -> List[str]:
        """Get universe of stocks for portfolio construction"""
        try:
            # Default stock universe (major stocks across sectors)
            default_universe = [
                # Technology
                "AAPL", "MSFT", "GOOGL", "NVDA", "META", "TSLA", "NFLX", "ADBE",
                # Healthcare
                "JNJ", "PFE", "UNH", "ABBV", "MRK",
                # Financial
                "JPM", "BAC", "WFC", "GS", "MS",
                # Consumer
                "AMZN", "WMT", "PG", "KO", "PEP",
                # Industrial
                "CAT", "BA", "GE", "MMM",
                # Energy
                "XOM", "CVX", "COP",
                # Materials
                "LIN", "APD"
            ]
            
            if sectors:
                # Filter by sectors (simplified mapping)
                sector_mapping = {
                    "technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "TSLA", "NFLX", "ADBE"],
                    "healthcare": ["JNJ", "PFE", "UNH", "ABBV", "MRK"],
                    "financial": ["JPM", "BAC", "WFC", "GS", "MS"],
                    "consumer": ["AMZN", "WMT", "PG", "KO", "PEP"],
                    "energy": ["XOM", "CVX", "COP"],
                    "industrial": ["CAT", "BA", "GE", "MMM"]
                }
                
                universe = []
                for sector in sectors:
                    if sector.lower() in sector_mapping:
                        universe.extend(sector_mapping[sector.lower()])
                
                if not universe:  # Fallback to default if no valid sectors
                    universe = default_universe
            else:
                universe = default_universe
            
            # Remove excluded symbols
            if exclude_symbols:
                universe = [symbol for symbol in universe if symbol not in exclude_symbols]
            
            return universe[:20]  # Limit to 20 stocks for optimization
            
        except Exception as e:
            logger.error(f"Failed to get stock universe: {e}")
            return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]  # Fallback
    
    async def _ai_stock_selection(self, stock_universe: List[str], risk_tolerance: float, investment_horizon: str) -> List[str]:
        """Use AI to select best stocks from universe"""
        try:
            # Prepare prompt for AI stock selection
            prompt = f"""
            You are an expert portfolio manager. Select the best 8-12 stocks from this list for a portfolio with:
            - Risk tolerance: {risk_tolerance} (0.0 = conservative, 1.0 = aggressive)  
            - Investment horizon: {investment_horizon}
            - Available stocks: {', '.join(stock_universe)}
            
            Consider:
            1. Diversification across sectors
            2. Risk-return characteristics matching the risk tolerance
            3. Growth potential for the investment horizon
            4. Current market conditions
            5. Correlation between stocks
            
            Return only the selected stock symbols as a comma-separated list.
            Example: AAPL, MSFT, GOOGL, AMZN
            """
            
            # Get AI recommendation
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="llama3.1:8b",
                max_tokens=200,
                temperature=0.3
            )
            
            # Parse the response to extract stock symbols
            selected_stocks = self._parse_stock_selection(response, stock_universe)
            
            # Ensure we have at least 5 stocks
            if len(selected_stocks) < 5:
                # Add top performers from universe
                additional_stocks = [s for s in stock_universe[:10] if s not in selected_stocks]
                selected_stocks.extend(additional_stocks[:5-len(selected_stocks)])
            
            logger.info(f"AI selected {len(selected_stocks)} stocks: {selected_stocks}")
            return selected_stocks
            
        except Exception as e:
            logger.error(f"AI stock selection failed: {e}")
            # Fallback selection based on risk tolerance
            if risk_tolerance > 0.7:
                return stock_universe[:8]  # More aggressive selection
            elif risk_tolerance > 0.4:
                return stock_universe[2:10]  # Balanced selection
            else:
                return stock_universe[5:13]  # Conservative selection
    
    def _parse_stock_selection(self, response: str, universe: List[str]) -> List[str]:
        """Parse AI response to extract valid stock symbols"""
        try:
            # Extract symbols from response
            symbols = []
            response_upper = response.upper()
            
            for symbol in universe:
                if symbol in response_upper:
                    symbols.append(symbol)
            
            # If no valid symbols found, extract from text
            if not symbols:
                import re
                # Look for stock symbol patterns (3-4 uppercase letters)
                pattern = r'\b[A-Z]{3,4}\b'
                matches = re.findall(pattern, response_upper)
                symbols = [s for s in matches if s in universe]
            
            return symbols[:12]  # Limit to 12 stocks
            
        except Exception as e:
            logger.error(f"Failed to parse stock selection: {e}")
            return universe[:8]  # Fallback
    
    async def _analyze_portfolio_composition(self, optimization_result: Dict, risk_tolerance: float) -> Dict[str, Any]:
        """Analyze the composition of the optimized portfolio"""
        try:
            if "allocations" not in optimization_result:
                return {"error": "No allocations found in optimization result"}
            
            allocations = optimization_result["allocations"]
            
            analysis = {
                "total_positions": len(allocations),
                "concentration_analysis": {},
                "sector_distribution": {},
                "risk_characteristics": {},
                "expected_performance": {},
                "diversification_metrics": {}
            }
            
            # Concentration analysis
            weights = list(allocations.values())
            max_weight = max(weights) if weights else 0
            min_weight = min(weights) if weights else 0
            
            analysis["concentration_analysis"] = {
                "max_position_size": round(max_weight, 3),
                "min_position_size": round(min_weight, 3),
                "concentration_risk": "high" if max_weight > 0.25 else "moderate" if max_weight > 0.15 else "low",
                "number_of_positions": len(allocations)
            }
            
            # Risk characteristics
            analysis["risk_characteristics"] = {
                "portfolio_risk_level": "aggressive" if risk_tolerance > 0.7 else "moderate" if risk_tolerance > 0.3 else "conservative",
                "expected_volatility": "high" if risk_tolerance > 0.7 else "moderate" if risk_tolerance > 0.3 else "low",
                "risk_tolerance_match": "well-matched" if 0.4 <= risk_tolerance <= 0.6 else "aligned"
            }
            
            # Expected performance (simplified estimates)
            base_return = 0.08  # 8% base return
            risk_premium = risk_tolerance * 0.04  # Up to 4% additional return for higher risk
            
            analysis["expected_performance"] = {
                "expected_annual_return": round((base_return + risk_premium) * 100, 1),
                "expected_volatility": round((0.12 + risk_tolerance * 0.08) * 100, 1),
                "sharpe_ratio_estimate": round((base_return + risk_premium) / (0.12 + risk_tolerance * 0.08), 2)
            }
            
            # Diversification metrics
            analysis["diversification_metrics"] = {
                "diversification_score": min(1.0, len(allocations) / 10),  # Score based on number of positions
                "correlation_risk": "low" if len(allocations) >= 8 else "moderate" if len(allocations) >= 5 else "high",
                "sector_diversification": "good" if len(allocations) >= 6 else "moderate"
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze portfolio composition: {e}")
            return {"error": str(e)}
    
    async def _generate_portfolio_insights(self, optimization_result: Dict, portfolio_analysis: Dict) -> Dict[str, Any]:
        """Generate AI-driven insights about the portfolio"""
        try:
            # Prepare context for AI insights
            context = f"""
            Portfolio Optimization Results:
            - Total positions: {portfolio_analysis.get('total_positions', 0)}
            - Max position size: {portfolio_analysis.get('concentration_analysis', {}).get('max_position_size', 0)}
            - Expected return: {portfolio_analysis.get('expected_performance', {}).get('expected_annual_return', 0)}%
            - Risk level: {portfolio_analysis.get('risk_characteristics', {}).get('portfolio_risk_level', 'moderate')}
            - Sharpe ratio: {portfolio_analysis.get('expected_performance', {}).get('sharpe_ratio_estimate', 0)}
            """
            
            prompt = f"""
            As a portfolio management expert, provide insights and recommendations for this portfolio:
            
            {context}
            
            Please provide:
            1. Key strengths of this portfolio
            2. Potential areas for improvement
            3. Risk management recommendations
            4. Performance expectations
            5. Rebalancing considerations
            
            Keep your response concise and actionable.
            """
            
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="llama3.1:8b",
                max_tokens=1000,
                temperature=0.4
            )
            
            # Structure the insights
            insights = {
                "ai_analysis": response,
                "key_strengths": self._extract_strengths(response),
                "improvement_areas": self._extract_improvements(response),
                "risk_recommendations": self._extract_risk_recommendations(response),
                "action_items": self._extract_action_items(response),
                "confidence_score": 0.8  # High confidence in AI analysis
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate portfolio insights: {e}")
            return {
                "ai_analysis": "Unable to generate AI insights at this time",
                "error": str(e)
            }
    
    def _extract_strengths(self, text: str) -> List[str]:
        """Extract key strengths from AI response"""
        strengths = []
        sentences = text.split('.')
        
        strength_keywords = ['strength', 'advantage', 'benefit', 'good', 'strong', 'excellent', 'solid']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in strength_keywords):
                strengths.append(sentence.strip())
        
        return strengths[:3] if strengths else ["Well-diversified portfolio", "Risk-adjusted approach", "Professional optimization"]
    
    def _extract_improvements(self, text: str) -> List[str]:
        """Extract improvement areas from AI response"""
        improvements = []
        sentences = text.split('.')
        
        improvement_keywords = ['improve', 'consider', 'could', 'might', 'should', 'recommend', 'suggest']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in improvement_keywords):
                improvements.append(sentence.strip())
        
        return improvements[:3] if improvements else ["Monitor market conditions", "Regular rebalancing", "Performance review"]
    
    def _extract_risk_recommendations(self, text: str) -> List[str]:
        """Extract risk management recommendations"""
        recommendations = []
        sentences = text.split('.')
        
        risk_keywords = ['risk', 'hedge', 'protect', 'volatility', 'diversif']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in risk_keywords):
                recommendations.append(sentence.strip())
        
        return recommendations[:3] if recommendations else ["Regular risk assessment", "Diversification maintenance", "Stop-loss considerations"]
    
    def _extract_action_items(self, text: str) -> List[str]:
        """Extract actionable items from AI response"""
        actions = []
        sentences = text.split('.')
        
        action_keywords = ['monitor', 'review', 'rebalance', 'adjust', 'track', 'watch']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in action_keywords):
                actions.append(sentence.strip())
        
        return actions[:4] if actions else ["Monthly performance review", "Quarterly rebalancing", "Risk tolerance assessment", "Market condition monitoring"]
    
    def _generate_rebalancing_schedule(self, investment_horizon: str) -> Dict[str, Any]:
        """Generate rebalancing schedule based on investment horizon"""
        schedules = {
            "short": {
                "frequency": "monthly",
                "threshold": 0.05,  # 5% deviation
                "review_period": "2 weeks"
            },
            "medium": {
                "frequency": "quarterly", 
                "threshold": 0.10,  # 10% deviation
                "review_period": "1 month"
            },
            "long": {
                "frequency": "semi-annually",
                "threshold": 0.15,  # 15% deviation
                "review_period": "3 months"
            }
        }
        
        return schedules.get(investment_horizon, schedules["medium"])
    
    def _define_monitoring_metrics(self) -> Dict[str, str]:
        """Define key metrics to monitor"""
        return {
            "total_return": "Track overall portfolio performance",
            "volatility": "Monitor risk levels and volatility",
            "sharpe_ratio": "Risk-adjusted performance measurement",
            "max_drawdown": "Maximum peak-to-trough decline",
            "beta": "Portfolio sensitivity to market movements",
            "correlation": "Correlation with major indices",
            "sector_allocation": "Sector distribution maintenance",
            "individual_positions": "Individual stock performance tracking"
        }
    
    def _set_performance_benchmarks(self, risk_tolerance: float) -> Dict[str, Any]:
        """Set appropriate benchmarks based on risk tolerance"""
        if risk_tolerance > 0.7:
            return {
                "primary_benchmark": "NASDAQ-100",
                "secondary_benchmark": "S&P 500 Growth",
                "expected_outperformance": "+2-4% annually",
                "risk_metrics": "Higher volatility acceptable"
            }
        elif risk_tolerance > 0.3:
            return {
                "primary_benchmark": "S&P 500",
                "secondary_benchmark": "Total Stock Market Index",
                "expected_outperformance": "+1-2% annually",
                "risk_metrics": "Moderate volatility"
            }
        else:
            return {
                "primary_benchmark": "S&P 500",
                "secondary_benchmark": "Balanced Index Fund",
                "expected_outperformance": "+0-1% annually",
                "risk_metrics": "Lower volatility priority"
            }
    
    async def rebalance_portfolio(self, current_portfolio: Dict[str, float], target_allocations: Dict[str, float]) -> Dict[str, Any]:
        """Generate rebalancing recommendations"""
        try:
            rebalancing_actions = []
            total_value = sum(current_portfolio.values())
            
            for symbol in target_allocations:
                current_weight = current_portfolio.get(symbol, 0) / total_value if total_value > 0 else 0
                target_weight = target_allocations[symbol]
                difference = target_weight - current_weight
                
                if abs(difference) > 0.05:  # 5% threshold
                    action = "buy" if difference > 0 else "sell"
                    amount = abs(difference) * total_value
                    
                    rebalancing_actions.append({
                        "symbol": symbol,
                        "action": action,
                        "amount": round(amount, 2),
                        "current_weight": round(current_weight, 3),
                        "target_weight": round(target_weight, 3),
                        "difference": round(difference, 3)
                    })
            
            return {
                "rebalancing_needed": len(rebalancing_actions) > 0,
                "actions": rebalancing_actions,
                "total_trades": len(rebalancing_actions),
                "estimated_cost": len(rebalancing_actions) * 7.0,  # $7 per trade estimate
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Portfolio rebalancing calculation failed: {e}")
            return {"error": str(e), "rebalancing_needed": False}
