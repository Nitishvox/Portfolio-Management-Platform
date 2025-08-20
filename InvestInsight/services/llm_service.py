import os
import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
import requests
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMService:
    """Service for local LLM inference using Ollama"""
    
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.default_model = os.getenv("DEFAULT_LLM_MODEL", "llama3.1:8b")
        self.available_models = []
        self.model_status = {}
        
    async def initialize(self):
        """Initialize LLM service and check available models"""
        try:
            await self._check_ollama_status()
            await self._list_available_models()
            await self._ensure_models_available()
            logger.info("LLM service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            # Continue with fallback capabilities
    
    async def _check_ollama_status(self):
        """Check if Ollama is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags", timeout=5) as response:
                    if response.status == 200:
                        logger.info("Ollama service is running")
                        return True
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False
    
    async def _list_available_models(self):
        """Get list of available models from Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.available_models = [model["name"] for model in data.get("models", [])]
                        logger.info(f"Available models: {self.available_models}")
        except Exception as e:
            logger.error(f"Failed to list available models: {e}")
            self.available_models = []
    
    async def _ensure_models_available(self):
        """Ensure required models are available, pull if necessary"""
        required_models = ["llama3.1:8b", "qwen2.5:7b"]
        
        for model in required_models:
            if model not in self.available_models:
                logger.info(f"Pulling model: {model}")
                await self._pull_model(model)
    
    async def _pull_model(self, model_name: str):
        """Pull a model from Ollama registry"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/pull",
                    json={"name": model_name},
                    timeout=300  # 5 minutes timeout for model pulling
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully pulled model: {model_name}")
                        self.available_models.append(model_name)
                    else:
                        logger.error(f"Failed to pull model {model_name}: {response.status}")
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
    
    async def generate_response(self, 
                              prompt: str, 
                              model: str = None,
                              max_tokens: int = 1000,
                              temperature: float = 0.7,
                              system_message: str = None) -> str:
        """
        Generate response using local LLM
        
        Args:
            prompt: The input prompt
            model: Model name to use (defaults to configured model)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_message: System message for context
            
        Returns:
            Generated response text
        """
        try:
            model = model or self.default_model
            
            # Prepare the request
            request_data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                }
            }
            
            if system_message:
                request_data["system"] = system_message
            
            # Make request to Ollama
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=request_data,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "No response generated")
                    else:
                        logger.error(f"LLM request failed: {response.status}")
                        return await self._fallback_response(prompt)
        
        except asyncio.TimeoutError:
            logger.error("LLM request timeout")
            return await self._fallback_response(prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return await self._fallback_response(prompt)
    
    async def chat_completion(self, 
                            messages: List[Dict[str, str]], 
                            model: str = None,
                            max_tokens: int = 1000,
                            temperature: float = 0.7) -> str:
        """
        Generate chat completion using local LLM
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated response text
        """
        try:
            model = model or self.default_model
            
            request_data = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/chat",
                    json=request_data,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("message", {}).get("content", "No response generated")
                    else:
                        logger.error(f"Chat completion failed: {response.status}")
                        return await self._fallback_chat_response(messages)
        
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return await self._fallback_chat_response(messages)
    
    async def analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text using LLM
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis results
        """
        try:
            prompt = f"""
            Analyze the sentiment of the following text and provide a structured response:
            
            Text: "{text}"
            
            Please provide:
            1. Sentiment score (-1 to +1, where -1 is very negative, 0 is neutral, +1 is very positive)
            2. Confidence level (0 to 1)
            3. Key emotional indicators
            4. Overall sentiment classification (positive/negative/neutral)
            
            Format as JSON:
            {{
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "emotional_indicators": ["indicator1", "indicator2"],
                "classification": "neutral"
            }}
            """
            
            response = await self.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=300
            )
            
            return self._parse_sentiment_response(response)
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                "sentiment_score": 0.0,
                "confidence": 0.3,
                "emotional_indicators": ["analysis_unavailable"],
                "classification": "neutral"
            }
    
    def _parse_sentiment_response(self, response: str) -> Dict[str, Any]:
        """Parse sentiment analysis response"""
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
            sentiment = {
                "sentiment_score": 0.0,
                "confidence": 0.5,
                "emotional_indicators": [],
                "classification": "neutral"
            }
            
            # Extract sentiment score
            response_lower = response.lower()
            if "positive" in response_lower:
                sentiment["sentiment_score"] = 0.5
                sentiment["classification"] = "positive"
            elif "negative" in response_lower:
                sentiment["sentiment_score"] = -0.5
                sentiment["classification"] = "negative"
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Failed to parse sentiment response: {e}")
            return {
                "sentiment_score": 0.0,
                "confidence": 0.3,
                "emotional_indicators": ["parsing_error"],
                "classification": "neutral"
            }
    
    async def summarize_text(self, text: str, max_length: int = 150) -> str:
        """
        Summarize text using LLM
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            
        Returns:
            Summary text
        """
        try:
            prompt = f"""
            Please provide a concise summary of the following text in approximately {max_length} words:
            
            {text}
            
            Summary:
            """
            
            response = await self.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=max_length + 50
            )
            
            # Clean up the response
            summary = response.strip()
            if summary.startswith("Summary:"):
                summary = summary[8:].strip()
            
            return summary
            
        except Exception as e:
            logger.error(f"Text summarization failed: {e}")
            return "Summary unavailable due to processing error."
    
    async def extract_key_points(self, text: str) -> List[str]:
        """
        Extract key points from text using LLM
        
        Args:
            text: Text to analyze
            
        Returns:
            List of key points
        """
        try:
            prompt = f"""
            Extract the key points from the following text. Provide them as a numbered list:
            
            {text}
            
            Key points:
            """
            
            response = await self.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse the response to extract points
            key_points = []
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                    # Clean up the line
                    clean_line = line.lstrip('0123456789.-* ').strip()
                    if clean_line:
                        key_points.append(clean_line)
            
            return key_points[:10]  # Limit to top 10 points
            
        except Exception as e:
            logger.error(f"Key point extraction failed: {e}")
            return ["Key point extraction unavailable due to processing error."]
    
    async def _fallback_response(self, prompt: str) -> str:
        """Generate fallback response when LLM is unavailable"""
        return "I apologize, but I'm currently unable to process your request due to LLM service unavailability. Please check your Ollama installation and ensure the required models are available."
    
    async def _fallback_chat_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate fallback chat response when LLM is unavailable"""
        return "I'm currently unable to respond due to LLM service issues. Please ensure Ollama is running and the required models are installed."
