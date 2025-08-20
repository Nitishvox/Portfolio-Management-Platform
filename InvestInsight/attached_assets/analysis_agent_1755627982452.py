import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from services.llm_service import LLMService
from utils.web_scraper import get_website_text_content

logger = logging.getLogger(__name__)

class AnalysisAgent:
    """AI agent for financial analysis using local LLM ensemble"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.analysis_cache = {}
        self.model_ensemble = ["llama3.1:8b", "qwen2.5:7b"]
        
    async def analyze_stock(self, symbol: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Comprehensive stock analysis using AI models
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            analysis_type: Type of analysis ('technical', 'fundamental', 'comprehensive')
            
        Returns:
            Detailed analysis results
        """
        try:
            cache_key = f"{symbol}_{analysis_type}_{datetime.now().strftime('%Y-%m-%d')}"
            
            if cache_key in self.analysis_cache:
                return self.analysis_cache[cache_key]
            
            analysis_result = {
                "symbol": symbol,
                "analysis_type": analysis_type,
                "timestamp": datetime.now().isoformat(),
                "models_used": self.model_ensemble,
                "technical_analysis": {},
                "fundamental_analysis": {},
                "ai_insights": {},
                "risk_assessment": {},
                "recommendation": {},
                "confidence_score": 0.0
            }
            
            # Multi-model analysis
            for model in self.model_ensemble:
                try:
                    model_analysis = await self._analyze_with_model(symbol, analysis_type, model)
                    analysis_result[f"{model}_analysis"] = model_analysis
                    logger.info(f"Completed analysis with {model} for {symbol}")
                except Exception as e:
                    logger.error(f"Analysis failed with {model} for {symbol}: {e}")
            
            # Aggregate results from multiple models
            analysis_result = await self._aggregate_model_results(analysis_result)
            
            # Cache the result
            self.analysis_cache[cache_key] = analysis_result
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Stock analysis failed for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
    
    async def _analyze_with_model(self, symbol: str, analysis_type: str, model: str) -> Dict[str, Any]:
        """Run analysis with a specific model"""
        
        # Prepare comprehensive prompt
        prompt = self._build_analysis_prompt(symbol, analysis_type)
        
        # Get analysis from LLM
        response = await self.llm_service.generate_response(
            prompt=prompt,
            model=model,
            max_tokens=2048,
            temperature=0.3
        )
        
        # Parse and structure the response
        return await self._parse_analysis_response(response, model)
    
    def _build_analysis_prompt(self, symbol: str, analysis_type: str) -> str:
        """Build comprehensive analysis prompt"""
        
        base_prompt = f"""
        You are an expert financial analyst. Provide a comprehensive analysis of {symbol} stock.
        
        Analysis Type: {analysis_type}
        
        Please analyze the following aspects:
        
        1. TECHNICAL ANALYSIS:
        - Current price trends and momentum
        - Support and resistance levels
        - Key technical indicators (RSI, MACD, moving averages)
        - Chart patterns and signals
        
        2. FUNDAMENTAL ANALYSIS:
        - Financial health and ratios
        - Revenue and earnings growth
        - Competitive position
        - Industry outlook
        
        3. RISK ASSESSMENT:
        - Market risks
        - Company-specific risks
        - Sector risks
        - Regulatory risks
        
        4. INVESTMENT RECOMMENDATION:
        - Buy/Hold/Sell recommendation
        - Price targets
        - Time horizon
        - Risk/reward ratio
        
        5. KEY INSIGHTS:
        - Most important factors affecting the stock
        - Catalysts for price movement
        - Long-term outlook
        
        Provide your analysis in a structured JSON format with clear explanations and confidence scores.
        """
        
        return base_prompt
    
    async def _parse_analysis_response(self, response: str, model: str) -> Dict[str, Any]:
        """Parse and structure the LLM response"""
        try:
            # Try to extract JSON if present
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                try:
                    parsed_data = json.loads(json_str)
                    return parsed_data
                except json.JSONDecodeError:
                    pass
            
            # Fallback: structure the text response
            return {
                "model": model,
                "raw_analysis": response,
                "technical_indicators": self._extract_technical_data(response),
                "fundamental_metrics": self._extract_fundamental_data(response),
                "recommendation": self._extract_recommendation(response),
                "risk_factors": self._extract_risk_factors(response),
                "confidence": self._calculate_confidence(response)
            }
            
        except Exception as e:
            logger.error(f"Failed to parse analysis response: {e}")
            return {
                "model": model,
                "raw_analysis": response,
                "parsing_error": str(e)
            }
    
    def _extract_technical_data(self, text: str) -> Dict[str, Any]:
        """Extract technical analysis data from text"""
        technical_data = {
            "trend": "neutral",
            "momentum": "neutral",
            "support_level": None,
            "resistance_level": None,
            "rsi": None,
            "recommendation": "hold"
        }
        
        text_lower = text.lower()
        
        # Extract trend
        if "bullish" in text_lower or "uptrend" in text_lower:
            technical_data["trend"] = "bullish"
        elif "bearish" in text_lower or "downtrend" in text_lower:
            technical_data["trend"] = "bearish"
        
        # Extract momentum
        if "strong momentum" in text_lower or "positive momentum" in text_lower:
            technical_data["momentum"] = "positive"
        elif "weak momentum" in text_lower or "negative momentum" in text_lower:
            technical_data["momentum"] = "negative"
        
        return technical_data
    
    def _extract_fundamental_data(self, text: str) -> Dict[str, Any]:
        """Extract fundamental analysis data from text"""
        fundamental_data = {
            "financial_health": "good",
            "growth_prospects": "moderate",
            "valuation": "fair",
            "competitive_position": "strong"
        }
        
        text_lower = text.lower()
        
        # Extract financial health indicators
        if "strong financials" in text_lower or "healthy balance sheet" in text_lower:
            fundamental_data["financial_health"] = "excellent"
        elif "weak financials" in text_lower or "debt concerns" in text_lower:
            fundamental_data["financial_health"] = "poor"
        
        # Extract growth prospects
        if "high growth" in text_lower or "strong growth" in text_lower:
            fundamental_data["growth_prospects"] = "high"
        elif "slow growth" in text_lower or "declining" in text_lower:
            fundamental_data["growth_prospects"] = "low"
        
        return fundamental_data
    
    def _extract_recommendation(self, text: str) -> Dict[str, Any]:
        """Extract investment recommendation from text"""
        text_lower = text.lower()
        
        if "strong buy" in text_lower or "buy" in text_lower:
            return {"action": "buy", "confidence": 0.8}
        elif "sell" in text_lower:
            return {"action": "sell", "confidence": 0.7}
        else:
            return {"action": "hold", "confidence": 0.6}
    
    def _extract_risk_factors(self, text: str) -> List[str]:
        """Extract risk factors from text"""
        risk_keywords = ["risk", "concern", "challenge", "uncertainty", "volatility"]
        risks = []
        
        sentences = text.split(".")
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in risk_keywords):
                risks.append(sentence.strip())
        
        return risks[:5]  # Top 5 risks
    
    def _calculate_confidence(self, text: str) -> float:
        """Calculate confidence score based on analysis text"""
        confidence_indicators = [
            "strong", "clear", "definitive", "certain", "confident",
            "solid", "robust", "consistent", "reliable", "stable"
        ]
        
        uncertainty_indicators = [
            "uncertain", "unclear", "volatile", "risky", "unpredictable",
            "challenging", "difficult", "complex", "mixed", "cautious"
        ]
        
        text_lower = text.lower()
        confidence_count = sum(1 for word in confidence_indicators if word in text_lower)
        uncertainty_count = sum(1 for word in uncertainty_indicators if word in text_lower)
        
        base_confidence = 0.5
        confidence_boost = confidence_count * 0.1
        confidence_penalty = uncertainty_count * 0.1
        
        final_confidence = max(0.1, min(0.9, base_confidence + confidence_boost - confidence_penalty))
        return round(final_confidence, 2)
    
    async def _aggregate_model_results(self, analysis_result: Dict) -> Dict[str, Any]:
        """Aggregate results from multiple models"""
        try:
            # Collect recommendations from all models
            recommendations = []
            confidence_scores = []
            
            for model in self.model_ensemble:
                model_key = f"{model}_analysis"
                if model_key in analysis_result:
                    model_data = analysis_result[model_key]
                    if "recommendation" in model_data:
                        recommendations.append(model_data["recommendation"])
                    if "confidence" in model_data:
                        confidence_scores.append(model_data["confidence"])
            
            # Aggregate recommendations
            if recommendations:
                # Simple majority vote for recommendations
                actions = [rec.get("action", "hold") for rec in recommendations if isinstance(rec, dict)]
                if actions:
                    from collections import Counter
                    most_common_action = Counter(actions).most_common(1)[0][0]
                    analysis_result["recommendation"] = {
                        "action": most_common_action,
                        "consensus": len([a for a in actions if a == most_common_action]) / len(actions),
                        "models_agreement": len(actions)
                    }
            
            # Average confidence score
            if confidence_scores:
                analysis_result["confidence_score"] = sum(confidence_scores) / len(confidence_scores)
            
            # Generate ensemble insights
            analysis_result["ai_insights"] = {
                "models_consensus": analysis_result["recommendation"].get("consensus", 0.5) if "recommendation" in analysis_result else 0.5,
                "analysis_quality": "high" if analysis_result.get("confidence_score", 0) > 0.7 else "moderate",
                "key_factors": ["Multi-model analysis completed", "Risk assessment integrated", "Market context considered"],
                "limitations": ["Analysis based on available data", "Market conditions may change", "Human verification recommended"]
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Failed to aggregate model results: {e}")
            return analysis_result
    
    async def generate_trading_signals(self, symbol: str) -> Dict[str, Any]:
        """Generate trading signals based on analysis"""
        try:
            analysis = await self.analyze_stock(symbol, "comprehensive")
            
            signals = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "signals": [],
                "overall_signal": "neutral",
                "confidence": 0.5,
                "timeframe": "1-3 months"
            }
            
            # Generate signals based on analysis
            if "recommendation" in analysis:
                action = analysis["recommendation"].get("action", "hold")
                confidence = analysis.get("confidence_score", 0.5)
                
                if action == "buy" and confidence > 0.7:
                    signals["overall_signal"] = "strong_buy"
                    signals["signals"].append("Strong fundamental and technical indicators")
                elif action == "buy":
                    signals["overall_signal"] = "buy"
                    signals["signals"].append("Positive outlook with moderate confidence")
                elif action == "sell" and confidence > 0.7:
                    signals["overall_signal"] = "strong_sell"
                    signals["signals"].append("Significant downside risks identified")
                elif action == "sell":
                    signals["overall_signal"] = "sell"
                    signals["signals"].append("Bearish indicators present")
                
                signals["confidence"] = confidence
            
            # Add specific signal types
            signals["signal_types"] = {
                "technical": "Based on chart patterns and indicators",
                "fundamental": "Based on financial health and ratios",
                "sentiment": "Based on market sentiment analysis",
                "risk": "Based on risk assessment"
            }
            
            return signals
            
        except Exception as e:
            logger.error(f"Failed to generate trading signals for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
    
    async def analyze_portfolio_risk(self, portfolio: Dict[str, float]) -> Dict[str, Any]:
        """Analyze portfolio-level risk"""
        try:
            risk_analysis = {
                "timestamp": datetime.now().isoformat(),
                "portfolio_symbols": list(portfolio.keys()),
                "total_positions": len(portfolio),
                "diversification_score": 0.0,
                "sector_concentration": {},
                "risk_metrics": {},
                "recommendations": []
            }
            
            # Calculate diversification score (simplified)
            weights = list(portfolio.values())
            if weights:
                # Higher scores for more even distribution
                weight_variance = np.var(weights)
                risk_analysis["diversification_score"] = max(0, 1 - weight_variance)
            
            # Generate recommendations
            if len(portfolio) < 5:
                risk_analysis["recommendations"].append("Consider adding more positions for better diversification")
            
            if max(weights) > 0.3:
                risk_analysis["recommendations"].append("Large position concentration detected - consider reducing exposure")
            
            risk_analysis["risk_metrics"] = {
                "concentration_risk": "high" if max(weights) > 0.3 else "moderate" if max(weights) > 0.2 else "low",
                "diversification_quality": "good" if len(portfolio) >= 10 else "moderate" if len(portfolio) >= 5 else "poor"
            }
            
            return risk_analysis
            
        except Exception as e:
            logger.error(f"Portfolio risk analysis failed: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
