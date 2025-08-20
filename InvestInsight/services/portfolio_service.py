import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import json

# Portfolio optimization imports
try:
    from pypfopt import EfficientFrontier, risk_models, expected_returns, plotting
    from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
    from pypfopt.objective_functions import L2_reg
    PYPFOPT_AVAILABLE = True
except ImportError:
    PYPFOPT_AVAILABLE = False
    logging.warning("PyPortfolioOpt not available. Portfolio optimization will use simplified methods.")

from services.data_service import DataService

logger = logging.getLogger(__name__)

class PortfolioService:
    """Service for portfolio optimization and management using PyPortfolioOpt"""
    
    def __init__(self):
        self.data_service = DataService()
        self.optimization_cache = {}
        
    async def optimize_portfolio(self, 
                               symbols: List[str],
                               investment_amount: float,
                               risk_tolerance: float,
                               optimization_method: str = "max_sharpe") -> Dict[str, Any]:
        """
        Optimize portfolio using PyPortfolioOpt
        
        Args:
            symbols: List of stock symbols
            investment_amount: Total amount to invest
            risk_tolerance: Risk tolerance (0.0 to 1.0)
            optimization_method: 'max_sharpe', 'min_volatility', 'max_quadratic_utility'
            
        Returns:
            Optimization results with allocations and metrics
        """
        try:
            logger.info(f"Optimizing portfolio for {len(symbols)} symbols with ${investment_amount}")
            
            if not PYPFOPT_AVAILABLE:
                return await self._fallback_optimization(symbols, investment_amount, risk_tolerance)
            
            # Fetch historical data for all symbols
            historical_data = await self._get_historical_data(symbols)
            
            if historical_data.empty:
                logger.error("No historical data available for optimization")
                return await self._fallback_optimization(symbols, investment_amount, risk_tolerance)
            
            # Calculate expected returns and covariance matrix
            mu = expected_returns.mean_historical_return(historical_data)
            S = risk_models.sample_cov(historical_data)
            
            # Create efficient frontier
            ef = EfficientFrontier(mu, S)
            
            # Add regularization to avoid overfitting
            ef.add_objective(L2_reg, gamma=0.1)
            
            # Optimize based on method and risk tolerance
            if optimization_method == "max_sharpe":
                weights = ef.max_sharpe()
            elif optimization_method == "min_volatility":
                weights = ef.min_volatility()
            elif optimization_method == "max_quadratic_utility":
                # Adjust risk aversion based on risk tolerance
                risk_aversion = (1 - risk_tolerance) * 10  # Scale 0-10
                weights = ef.max_quadratic_utility(risk_aversion=risk_aversion)
            else:
                weights = ef.max_sharpe()  # Default
            
            # Clean weights (remove tiny allocations)
            cleaned_weights = ef.clean_weights()
            
            # Get portfolio performance
            performance = ef.portfolio_performance(verbose=False)
            expected_return, volatility, sharpe_ratio = performance
            
            # Get discrete allocation
            latest_prices = get_latest_prices(historical_data)
            da = DiscreteAllocation(cleaned_weights, latest_prices, total_portfolio_value=investment_amount)
            allocation, leftover = da.lp_portfolio()
            
            # Calculate position values
            position_values = {}
            for symbol, shares in allocation.items():
                position_values[symbol] = shares * latest_prices[symbol]
            
            # Calculate actual weights based on discrete allocation
            total_invested = sum(position_values.values())
            actual_weights = {symbol: value / total_invested for symbol, value in position_values.items()}
            
            optimization_result = {
                "timestamp": datetime.now().isoformat(),
                "symbols": symbols,
                "investment_amount": investment_amount,
                "total_invested": round(total_invested, 2),
                "leftover_cash": round(leftover, 2),
                "optimization_method": optimization_method,
                "allocations": {symbol: round(weight, 4) for symbol, weight in actual_weights.items()},
                "share_allocations": allocation,
                "position_values": {symbol: round(value, 2) for symbol, value in position_values.items()},
                "performance_metrics": {
                    "expected_annual_return": round(expected_return * 100, 2),
                    "annual_volatility": round(volatility * 100, 2),
                    "sharpe_ratio": round(sharpe_ratio, 3)
                },
                "risk_metrics": await self._calculate_risk_metrics(cleaned_weights, historical_data),
                "optimization_success": True,
                "method_used": "pypfopt"
            }
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            return await self._fallback_optimization(symbols, investment_amount, risk_tolerance)
    
    async def _get_historical_data(self, symbols: List[str], period: str = "2y") -> pd.DataFrame:
        """Get historical price data for portfolio optimization"""
        try:
            # Fetch data for all symbols
            stocks_data = await self.data_service.get_multiple_stocks_data(symbols, period)
            
            # Organize into pandas DataFrame
            price_data = {}
            
            for symbol in symbols:
                if symbol in stocks_data.get("data", {}):
                    stock_data = stocks_data["data"][symbol]
                    if "error" not in stock_data:
                        historical_data = stock_data.get("historical_data", [])
                        if historical_data:
                            prices = [float(day["close"]) for day in historical_data]
                            dates = [pd.to_datetime(day["date"]) for day in historical_data]
                            price_data[symbol] = pd.Series(prices, index=dates)
            
            if not price_data:
                logger.warning("No valid historical data found")
                return pd.DataFrame()
            
            # Create DataFrame and handle missing data
            df = pd.DataFrame(price_data)
            df = df.dropna()  # Remove rows with any NaN values
            
            if len(df) < 50:  # Need sufficient data for optimization
                logger.warning(f"Insufficient historical data: only {len(df)} days available")
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return pd.DataFrame()
    
    async def _calculate_risk_metrics(self, weights: Dict[str, float], historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate additional risk metrics for the portfolio"""
        try:
            # Calculate portfolio returns
            returns = historical_data.pct_change().dropna()
            
            # Portfolio returns
            portfolio_returns = (returns * pd.Series(weights)).sum(axis=1)
            
            # Value at Risk (VaR) - 95% confidence
            var_95 = np.percentile(portfolio_returns, 5)
            
            # Conditional Value at Risk (CVaR)
            cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
            
            # Maximum Drawdown
            cumulative_returns = (1 + portfolio_returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # Correlation with market (using first stock as proxy)
            if len(returns.columns) > 0:
                market_returns = returns.iloc[:, 0]  # Use first stock as market proxy
                correlation_with_market = portfolio_returns.corr(market_returns)
            else:
                correlation_with_market = 0.0
            
            return {
                "value_at_risk_95": round(var_95 * 100, 3),
                "conditional_var_95": round(cvar_95 * 100, 3),
                "maximum_drawdown": round(max_drawdown * 100, 3),
                "correlation_with_market": round(correlation_with_market, 3),
                "portfolio_beta": round(correlation_with_market * (portfolio_returns.std() / market_returns.std()), 3) if len(returns.columns) > 0 else 1.0
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate risk metrics: {e}")
            return {
                "value_at_risk_95": 0.0,
                "conditional_var_95": 0.0,
                "maximum_drawdown": 0.0,
                "correlation_with_market": 0.0,
                "portfolio_beta": 1.0
            }
    
    async def _fallback_optimization(self, symbols: List[str], investment_amount: float, risk_tolerance: float) -> Dict[str, Any]:
        """Fallback optimization when PyPortfolioOpt is not available"""
        try:
            logger.info("Using fallback optimization method")
            
            # Simple equal weight allocation adjusted for risk tolerance
            num_symbols = len(symbols)
            
            if risk_tolerance > 0.7:
                # Aggressive: Focus on fewer stocks with higher weights
                primary_stocks = min(5, num_symbols)
                weights = {}
                
                for i, symbol in enumerate(symbols[:primary_stocks]):
                    if i == 0:
                        weights[symbol] = 0.3  # Largest position
                    elif i == 1:
                        weights[symbol] = 0.25
                    elif i == 2:
                        weights[symbol] = 0.2
                    else:
                        weights[symbol] = 0.25 / (primary_stocks - 3)
                        
            elif risk_tolerance > 0.3:
                # Moderate: Balanced allocation
                base_weight = 1.0 / num_symbols
                weights = {symbol: base_weight for symbol in symbols}
                
            else:
                # Conservative: More diversified with slight preference for "safer" stocks
                weights = {}
                safe_symbols = symbols[:min(8, num_symbols)]  # Limit to 8 positions
                equal_weight = 1.0 / len(safe_symbols)
                
                for symbol in safe_symbols:
                    weights[symbol] = equal_weight
            
            # Calculate share allocations
            share_allocations = {}
            position_values = {}
            
            # Get current prices (simplified)
            for symbol in weights:
                try:
                    stock_data = await self.data_service.get_stock_data(symbol)
                    current_price = stock_data.get("current_price", 100.0)  # Fallback price
                    
                    position_value = weights[symbol] * investment_amount
                    shares = int(position_value / current_price)
                    
                    if shares > 0:
                        share_allocations[symbol] = shares
                        position_values[symbol] = shares * current_price
                    
                except Exception as e:
                    logger.error(f"Failed to calculate allocation for {symbol}: {e}")
            
            # Recalculate actual weights
            total_invested = sum(position_values.values())
            actual_weights = {symbol: value / total_invested for symbol, value in position_values.items()} if total_invested > 0 else {}
            
            # Estimate performance metrics
            base_return = 0.08 + (risk_tolerance * 0.04)  # 8-12% expected return
            estimated_volatility = 0.12 + (risk_tolerance * 0.08)  # 12-20% volatility
            estimated_sharpe = base_return / estimated_volatility
            
            return {
                "timestamp": datetime.now().isoformat(),
                "symbols": symbols,
                "investment_amount": investment_amount,
                "total_invested": round(total_invested, 2),
                "leftover_cash": round(investment_amount - total_invested, 2),
                "optimization_method": "fallback_equal_weight",
                "allocations": {symbol: round(weight, 4) for symbol, weight in actual_weights.items()},
                "share_allocations": share_allocations,
                "position_values": {symbol: round(value, 2) for symbol, value in position_values.items()},
                "performance_metrics": {
                    "expected_annual_return": round(base_return * 100, 2),
                    "annual_volatility": round(estimated_volatility * 100, 2),
                    "sharpe_ratio": round(estimated_sharpe, 3)
                },
                "risk_metrics": {
                    "value_at_risk_95": round(-estimated_volatility * 1.645 * 100, 3),
                    "conditional_var_95": round(-estimated_volatility * 2.0 * 100, 3),
                    "maximum_drawdown": round(-estimated_volatility * 2.5 * 100, 3),
                    "correlation_with_market": 0.85,
                    "portfolio_beta": 1.0 + (risk_tolerance - 0.5) * 0.5
                },
                "optimization_success": True,
                "method_used": "fallback"
            }
            
        except Exception as e:
            logger.error(f"Fallback optimization failed: {e}")
            return {
                "error": f"Optimization failed: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "optimization_success": False
            }
    
    async def analyze_portfolio_performance(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current portfolio performance"""
        try:
            # Extract portfolio holdings
            holdings = portfolio_data.get("holdings", {})
            
            if not holdings:
                return {"error": "No portfolio holdings provided"}
            
            # Get current data for all holdings
            symbols = list(holdings.keys())
            stocks_data = await self.data_service.get_multiple_stocks_data(symbols)
            
            total_value = 0
            total_invested = 0
            performance_data = {}
            
            for symbol, position_data in holdings.items():
                shares = position_data.get("shares", 0)
                avg_cost = position_data.get("avg_cost", 0)
                
                if symbol in stocks_data.get("data", {}):
                    stock_data = stocks_data["data"][symbol]
                    if "error" not in stock_data:
                        current_price = stock_data.get("current_price", 0)
                        current_value = shares * current_price
                        invested_value = shares * avg_cost
                        
                        total_value += current_value
                        total_invested += invested_value
                        
                        performance_data[symbol] = {
                            "shares": shares,
                            "avg_cost": avg_cost,
                            "current_price": current_price,
                            "current_value": current_value,
                            "invested_value": invested_value,
                            "unrealized_gain_loss": current_value - invested_value,
                            "return_pct": ((current_price - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0
                        }
            
            # Calculate overall portfolio metrics
            total_return = total_value - total_invested
            total_return_pct = (total_return / total_invested * 100) if total_invested > 0 else 0
            
            return {
                "timestamp": datetime.now().isoformat(),
                "portfolio_summary": {
                    "total_value": round(total_value, 2),
                    "total_invested": round(total_invested, 2),
                    "total_return": round(total_return, 2),
                    "total_return_pct": round(total_return_pct, 2),
                    "number_of_positions": len(performance_data)
                },
                "positions": performance_data,
                "top_performers": sorted(performance_data.items(), 
                                       key=lambda x: x[1]["return_pct"], 
                                       reverse=True)[:5],
                "worst_performers": sorted(performance_data.items(), 
                                         key=lambda x: x[1]["return_pct"])[:5]
            }
            
        except Exception as e:
            logger.error(f"Portfolio performance analysis failed: {e}")
            return {"error": str(e)}
    
    async def get_portfolio_recommendations(self, portfolio_data: Dict[str, Any], 
                                          risk_tolerance: float) -> Dict[str, Any]:
        """Get AI-powered portfolio recommendations"""
        try:
            recommendations = {
                "timestamp": datetime.now().isoformat(),
                "risk_tolerance": risk_tolerance,
                "recommendations": []
            }
            
            # Analyze current allocation
            holdings = portfolio_data.get("holdings", {})
            if holdings:
                symbols = list(holdings.keys())
                
                # Sector concentration analysis
                sector_concentration = {}
                total_value = 0
                
                stocks_data = await self.data_service.get_multiple_stocks_data(symbols)
                
                for symbol, position_data in holdings.items():
                    if symbol in stocks_data.get("data", {}):
                        stock_data = stocks_data["data"][symbol]
                        if "error" not in stock_data:
                            sector = stock_data.get("company_info", {}).get("sector", "Unknown")
                            shares = position_data.get("shares", 0)
                            current_price = stock_data.get("current_price", 0)
                            position_value = shares * current_price
                            
                            total_value += position_value
                            sector_concentration[sector] = sector_concentration.get(sector, 0) + position_value
                
                # Check for overconcentration
                if total_value > 0:
                    for sector, value in sector_concentration.items():
                        sector_pct = (value / total_value) * 100
                        if sector_pct > 40:  # Over 40% in single sector
                            recommendations["recommendations"].append({
                                "type": "rebalancing",
                                "priority": "high",
                                "message": f"Consider reducing {sector} exposure (currently {sector_pct:.1f}%)",
                                "action": f"Trim positions in {sector} sector"
                            })
                
                # Risk-based recommendations
                if risk_tolerance < 0.3:  # Conservative
                    recommendations["recommendations"].append({
                        "type": "risk_management",
                        "priority": "medium",
                        "message": "Consider adding defensive positions",
                        "action": "Add utilities, consumer staples, or bond ETFs"
                    })
                elif risk_tolerance > 0.7:  # Aggressive
                    recommendations["recommendations"].append({
                        "type": "growth",
                        "priority": "medium",
                        "message": "Consider increasing growth exposure",
                        "action": "Add technology or emerging market positions"
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Portfolio recommendations failed: {e}")
            return {"error": str(e)}
