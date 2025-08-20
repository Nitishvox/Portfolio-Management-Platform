# OpenPort AI - Dependencies Documentation

## Core Dependencies Used in the Project

### Web Framework
- **streamlit** >= 1.28.0 - Main web application framework

### Data Analysis and Visualization  
- **pandas** >= 2.0.0 - Data manipulation and analysis
- **numpy** >= 1.24.0 - Numerical computing
- **plotly** >= 5.15.0 - Interactive data visualization

### Financial Data and Analysis
- **yfinance** >= 0.2.65 - Yahoo Finance data fetching
- **PyPortfolioOpt** >= 1.5.0 - Portfolio optimization using modern portfolio theory

### AI and Machine Learning
- **ollama-python** >= 0.1.2 - Local LLM integration for AI features

### Async Programming
- **asyncio** >= 3.4.3 - Asynchronous programming support
- **aiohttp** >= 3.8.0 - Async HTTP client for web scraping
- **aiosqlite** >= 0.19.0 - Async SQLite database operations

### Web Scraping and HTTP
- **requests** >= 2.31.0 - HTTP library for API calls
- **beautifulsoup4** >= 4.12.0 - HTML parsing for web scraping
- **trafilatura** >= 1.6.0 - Advanced web content extraction

### Configuration and Utilities
- **python-dotenv** >= 1.0.0 - Environment variable management

### Development Tools (Optional)
- **pytest** >= 7.4.0 - Testing framework

## Installation Commands

All dependencies are already installed in this project using uv. If you need to install them elsewhere, use:

```bash
# Using pip
pip install streamlit pandas numpy plotly yfinance PyPortfolioOpt ollama-python asyncio aiohttp aiosqlite requests beautifulsoup4 trafilatura python-dotenv

# Using uv (recommended for Replit)
uv add streamlit pandas numpy plotly yfinance PyPortfolioOpt ollama-python asyncio aiohttp aiosqlite requests beautifulsoup4 trafilatura python-dotenv
```

## Project Structure Dependencies

- **Components**: Use streamlit for UI rendering
- **Services**: Use pandas, numpy for data processing; aiohttp for async operations
- **Agents**: Use ollama-python for AI functionality; requests for web data
- **Utils**: Use plotly for charting; trafilatura for web scraping

## External Services (Optional)

- **Ollama Server**: Required for local LLM functionality (can run without it)
- **Yahoo Finance**: Accessed through yfinance library
- **Various Financial News Sites**: Scraped using trafilatura and requests

All core functionality works without external API keys, using free public data sources.