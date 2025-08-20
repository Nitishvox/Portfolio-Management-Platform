# OpenPort AI - Portfolio Management Platform

## Overview

OpenPort AI is an AI-powered financial portfolio management platform built with Streamlit. The application provides comprehensive portfolio analysis, optimization, and financial research capabilities using local Large Language Models (LLMs) through Ollama. The platform integrates multiple AI agents for different financial tasks, including portfolio optimization, stock analysis, news gathering, and intelligent search functionality.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The application uses **Streamlit** as the web framework, providing a clean and interactive user interface with multiple components:
- **Dashboard Component**: Portfolio overview with key metrics and performance visualization
- **Portfolio View**: Current holdings, optimization tools, performance tracking, and settings
- **Search Interface**: AI-powered financial search with natural language queries
- **Chat Interface**: Conversational AI assistant for financial guidance

The UI leverages **Plotly** for interactive financial charts and data visualizations, with custom CSS styling for enhanced user experience.

### Backend Architecture
The system follows a modular service-oriented architecture with clear separation of concerns:

**Core Services Layer**:
- **LLM Service**: Manages local Large Language Model inference through Ollama API, supporting multiple models like Llama 3.1:8b and Qwen 2.5:7b
- **Data Service**: Handles financial data fetching using yfinance and other data sources, with intelligent caching mechanisms
- **Portfolio Service**: Provides portfolio optimization using PyPortfolioOpt library for modern portfolio theory implementation

**AI Agent Layer**:
- **Analysis Agent**: Performs comprehensive stock analysis including technical, fundamental, and sentiment analysis
- **Search Agent**: Intelligent financial search with web scraping capabilities using browser automation
- **Portfolio Agent**: Portfolio management and optimization recommendations
- **News Agent**: Financial news aggregation with sentiment analysis

**Utility Layer**:
- **Chart Utils**: Financial visualization utilities for various chart types
- **Web Scraper**: Advanced web scraping using trafilatura for content extraction

### Data Management
The application uses **SQLite** (via aiosqlite) as the primary database for portfolio persistence, storing:
- Portfolio configurations and metadata
- Position data and historical performance
- User preferences and optimization parameters

All database operations are asynchronous to maintain responsive user experience.

### AI/ML Integration
The platform integrates with **Ollama** for local LLM inference, providing:
- Natural language financial analysis
- Intelligent search capabilities
- Portfolio optimization insights
- Market sentiment analysis

The system supports model ensemble approaches, using multiple LLMs for enhanced accuracy and reliability.

## External Dependencies

### Financial Data Sources
- **yfinance**: Primary source for stock market data, historical prices, and financial statements
- **Alpha Vantage API**: Alternative data source for financial information (API key configurable)

### AI/ML Services
- **Ollama**: Local LLM inference server for AI-powered analysis and chat functionality
- **PyPortfolioOpt**: Modern portfolio optimization library for risk-return analysis

### Web Technologies
- **Streamlit**: Web application framework for the user interface
- **Plotly**: Interactive data visualization and charting
- **aiohttp**: Asynchronous HTTP client for web scraping and API calls

### Data Processing
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing for portfolio calculations
- **trafilatura**: Web content extraction for news and research

### Database
- **SQLite/aiosqlite**: Local database for portfolio data persistence with async support

### Development Tools
- **python-dotenv**: Environment variable management
- **BeautifulSoup4**: HTML parsing for web scraping
- **requests**: HTTP library for API interactions

The application is designed to work primarily with local resources and APIs, minimizing external service dependencies while providing comprehensive financial analysis capabilities.