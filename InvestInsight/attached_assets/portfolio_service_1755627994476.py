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
                    historical_data = stocks_data["data"][symbol].get("historical_data", [])
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
                    "value_at_risk_95": round(-estimated_volatility * 1.65 * 100, 3),
                    "maximum_drawdown": round(-estimated_volatility * 2 * 100, 3),
                    "portfolio_beta": 1.0
                },
                "optimization_success": True,
                "method_used": "fallback",
                "note": "Simplified optimization used - install PyPortfolioOpt for advanced optimization"
            }
            
        except Exception as e:
            logger.error(f"Fallback optimization failed: {e}")
            return {
                "error": str(e),
                "optimization_success": False,
                "timestamp": datetime.now().isoformat()
            }
    
    async def backtest_portfolio(self, allocations: Dict[str, float], start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Backtest portfolio performance
        
        Args:
            allocations: Portfolio allocations (symbol -> weight)
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
            
        Returns:
            Backtest results with performance metrics
        """
        try:
            logger.info(f"Backtesting portfolio from {start_date} to {end_date}")
            
            symbols = list(allocations.keys())
            
            # Get historical data for backtest period
            historical_data = await self._get_backtest_data(symbols, start_date, end_date)
            
            if historical_data.empty:
                logger.error("No data available for backtest period")
                return {"error": "No data available for backtest period"}
            
            # Calculate portfolio returns
            returns = historical_data.pct_change().dropna()
            portfolio_returns = (returns * pd.Series(allocations)).sum(axis=1)
            
            # Calculate cumulative returns
            cumulative_returns = (1 + portfolio_returns).cumprod()
            
            # Performance metrics
            total_return = cumulative_returns.iloc[-1] - 1
            annual_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
            annual_volatility = portfolio_returns.std() * np.sqrt(252)
            sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
            
            # Maximum drawdown
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # Prepare daily performance data
            performance_data = []
            for date, cum_return in cumulative_returns.items():
                performance_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "cumulative_return": round((cum_return - 1) * 100, 3),
                    "daily_return": round(portfolio_returns.loc[date] * 100, 3) if date in portfolio_returns.index else 0
                })
            
            backtest_result = {
                "start_date": start_date,
                "end_date": end_date,
                "allocations": allocations,
                "performance_metrics": {
                    "total_return": round(total_return * 100, 2),
                    "annual_return": round(annual_return * 100, 2),
                    "annual_volatility": round(annual_volatility * 100, 2),
                    "sharpe_ratio": round(sharpe_ratio, 3),
                    "maximum_drawdown": round(max_drawdown * 100, 2),
                    "trading_days": len(portfolio_returns)
                },
                "daily_performance": performance_data,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
            
            return backtest_result
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return {
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_backtest_data(self, symbols: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """Get historical data for backtesting"""
        try:
            # For demo purposes, we'll use the existing data service
            # In production, you'd want to fetch data for the specific date range
            historical_data = await self._get_historical_data(symbols, period="2y")
            
            # Filter by date range if data is available
            if not historical_data.empty:
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                
                # Filter data within date range
                mask = (historical_data.index >= start_dt) & (historical_data.index <= end_dt)
                filtered_data = historical_data.loc[mask]
                
                return filtered_data
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Failed to get backtest data: {e}")
            return pd.DataFrame()
    
    async def rebalance_recommendations(self, current_portfolio: Dict[str, float], target_allocations: Dict[str, float], threshold: float = 0.05) -> Dict[str, Any]:
        """
        Generate rebalancing recommendations
        
        Args:
            current_portfolio: Current portfolio values (symbol -> value)
            target_allocations: Target allocations (symbol -> weight)
            threshold: Rebalancing threshold (default 5%)
            
        Returns:
            Rebalancing recommendations
        """
        try:
            total_value = sum(current_portfolio.values())
            
            if total_value == 0:
                return {"error": "Portfolio has no value", "rebalancing_needed": False}
            
            # Calculate current weights
            current_weights = {symbol: value / total_value for symbol, value in current_portfolio.items()}
            
            # Find deviations
            rebalancing_actions = []
            
            for symbol in target_allocations:
                current_weight = current_weights.get(symbol, 0.0)
                target_weight = target_allocations[symbol]
                deviation = abs(target_weight - current_weight)
                
                if deviation > threshold:
                    if target_weight > current_weight:
                        action = "buy"
                        amount = (target_weight - current_weight) * total_value
                    else:
                        action = "sell"
                        amount = (current_weight - target_weight) * total_value
                    
                    rebalancing_actions.append({
                        "symbol": symbol,
                        "action": action,
                        "current_weight": round(current_weight, 4),
                        "target_weight": round(target_weight, 4),
                        "deviation": round(deviation, 4),
                        "amount": round(amount, 2)
                    })
            
            # Check for symbols to remove (not in target)
            for symbol in current_weights:
                if symbol not in target_allocations and current_weights[symbol] > 0.01:  # > 1%
                    rebalancing_actions.append({
                        "symbol": symbol,
                        "action": "sell",
                        "current_weight": round(current_weights[symbol], 4),
                        "target_weight": 0.0,
                        "deviation": round(current_weights[symbol], 4),
                        "amount": round(current_portfolio[symbol], 2)
                    })
            
            return {
                "timestamp": datetime.now().isoformat(),
                "rebalancing_needed": len(rebalancing_actions) > 0,
                "threshold_used": threshold,
                "total_portfolio_value": round(total_value, 2),
                "actions": rebalancing_actions,
                "estimated_trades": len(rebalancing_actions),
                "estimated_costs": round(len(rebalancing_actions) * 7.0, 2)  # Assume $7 per trade
            }
            
        except Exception as e:
            logger.error(f"Rebalancing calculation failed: {e}")
            return {
                "error": str(e),
                "rebalancing_needed": False,
                "timestamp": datetime.now().isoformat()
            }
    
    def calculate_portfolio_metrics(self, positions: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Calculate current portfolio metrics
        
        Args:
            positions: Portfolio positions {symbol: {"shares": N, "avg_cost": X, "current_price": Y}}
            
        Returns:
            Portfolio metrics
        """
        try:
            total_value = 0
            total_cost = 0
            total_unrealized_pnl = 0
            
            position_details = {}
            
            for symbol, position in positions.items():
                shares = position.get("shares", 0)
                avg_cost = position.get("avg_cost", 0)
                current_price = position.get("current_price", 0)
                
                current_value = shares * current_price
                cost_basis = shares * avg_cost
                unrealized_pnl = current_value - cost_basis
                
                total_value += current_value
                total_cost += cost_basis
                total_unrealized_pnl += unrealized_pnl
                
                position_details[symbol] = {
                    "shares": shares,
                    "avg_cost": round(avg_cost, 2),
                    "current_price": round(current_price, 2),
                    "current_value": round(current_value, 2),
                    "cost_basis": round(cost_basis, 2),
                    "unrealized_pnl": round(unrealized_pnl, 2),
                    "unrealized_pnl_percent": round((unrealized_pnl / cost_basis * 100), 2) if cost_basis > 0 else 0,
                    "weight": round((current_value / total_value * 100), 2) if total_value > 0 else 0
                }
            
            overall_return_percent = (total_unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
            
            return {
                "timestamp": datetime.now().isoformat(),
                "total_value": round(total_value, 2),
                "total_cost": round(total_cost, 2),
                "total_unrealized_pnl": round(total_unrealized_pnl, 2),
                "total_return_percent": round(overall_return_percent, 2),
                "number_of_positions": len(positions),
                "positions": position_details
            }
            
        except Exception as e:
            logger.error(f"Portfolio metrics calculation failed: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
