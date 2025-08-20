import streamlit as st
from datetime import datetime
import time

def render_chat_interface():
    """Render the AI assistant chat interface"""
    
    st.header("💬 AI Financial Assistant")
    
    # Initialize chat history if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "👋 Hello! I'm your AI Financial Assistant. I can help you with:\n\n• 📊 Portfolio analysis and optimization\n• 📈 Stock research and technical analysis\n• 📰 Market news and sentiment analysis\n• 💡 Investment recommendations\n• 🎯 Risk assessment and management\n\nWhat would you like to know about today?",
                "timestamp": datetime.now()
            }
        ]
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Add timestamp for assistant messages
                if message["role"] == "assistant":
                    st.caption(f"🕒 {message['timestamp'].strftime('%H:%M:%S')}")
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about finance, investments, or markets..."):
        # Add user message to chat history
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now()
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                response = generate_ai_response(prompt)
                
                # Stream the response for better UX
                message_placeholder = st.empty()
                full_response = ""
                
                for chunk in response.split():
                    full_response += chunk + " "
                    time.sleep(0.05)  # Simulate streaming
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
            
            # Add timestamp
            st.caption(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
        
        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "timestamp": datetime.now()
        })
    
    # Sidebar with quick actions
    with st.sidebar:
        st.subheader("🚀 Quick Actions")
        
        quick_questions = [
            "📊 Analyze my portfolio performance",
            "📈 What are today's top stock movers?",
            "💰 Find undervalued dividend stocks",
            "🎯 Suggest portfolio rebalancing",
            "📰 Latest market news summary",
            "🔍 Research a specific stock",
            "⚡ Generate trading signals",
            "📉 Market risk assessment"
        ]
        
        for question in quick_questions:
            if st.button(question, key=f"quick_{question}"):
                # Add the quick question as a user message
                st.session_state.messages.append({
                    "role": "user",
                    "content": question,
                    "timestamp": datetime.now()
                })
                
                # Generate response
                response = generate_ai_response(question)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now()
                })
                
                st.rerun()
        
        # Clear chat button
        st.markdown("---")
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "👋 Hello! I'm your AI Financial Assistant. How can I help you today?",
                    "timestamp": datetime.now()
                }
            ]
            st.rerun()
        
        # Chat statistics
        st.markdown("---")
        st.subheader("📊 Chat Stats")
        total_messages = len(st.session_state.messages)
        user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
        
        st.metric("Total Messages", total_messages)
        st.metric("Your Questions", user_messages)

def generate_ai_response(prompt: str) -> str:
    """Generate AI response based on the user prompt"""
    
    prompt_lower = prompt.lower()
    
    # Portfolio-related queries
    if any(word in prompt_lower for word in ["portfolio", "allocation", "balance", "optimize"]):
        return generate_portfolio_response(prompt)
    
    # Stock analysis queries
    elif any(word in prompt_lower for word in ["stock", "analyze", "research", "price", "performance"]):
        return generate_stock_response(prompt)
    
    # Market news queries
    elif any(word in prompt_lower for word in ["news", "market", "sentiment", "today", "latest"]):
        return generate_news_response(prompt)
    
    # Investment recommendations
    elif any(word in prompt_lower for word in ["recommend", "suggest", "invest", "buy", "sell"]):
        return generate_recommendation_response(prompt)
    
    # Risk assessment
    elif any(word in prompt_lower for word in ["risk", "volatility", "drawdown", "var"]):
        return generate_risk_response(prompt)
    
    # Default response
    else:
        return generate_general_response(prompt)

def generate_portfolio_response(prompt: str) -> str:
    """Generate portfolio-related responses"""
    
    responses = [
        """📊 **Portfolio Analysis Complete**

Based on your current holdings, here's what I found:

• **Performance**: Your portfolio is up 15.7% YTD, outperforming the S&P 500 by 3.2%
• **Risk Level**: Moderate-High (Beta: 1.15)
• **Diversification**: 65% Tech concentration - consider rebalancing
• **Top Performers**: NVDA (+45%), TSLA (+28%), AAPL (+15%)

💡 **Recommendations**:
1. Reduce tech exposure to 40-45%
2. Add defensive sectors (Healthcare, Utilities)
3. Consider international diversification
4. Rebalance quarterly to maintain target allocation

Would you like me to run a detailed optimization analysis?""",

        """🎯 **Portfolio Optimization Insights**

I've analyzed your portfolio allocation and here are the key findings:

• **Current Sharpe Ratio**: 1.42 (Excellent)
• **Expected Annual Return**: 12.5%
• **Volatility**: 16.8%
• **Maximum Drawdown**: -8.4%

⚖️ **Optimal Allocation Suggestions**:
- Technology: 35% (Currently 45%)
- Healthcare: 15% (Currently 8%)
- Financial: 12% (Currently 5%)
- Consumer Staples: 10% (Currently 3%)
- International: 15% (Currently 5%)
- Bonds/Cash: 13% (Currently 12%)

This rebalancing could improve your risk-adjusted returns by 8-12%."""
    ]
    
    import random
    return random.choice(responses)

def generate_stock_response(prompt: str) -> str:
    """Generate stock analysis responses"""
    
    # Extract potential stock symbol from prompt
    words = prompt.upper().split()
    potential_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN", "META"]
    mentioned_symbol = None
    
    for word in words:
        if word in potential_symbols:
            mentioned_symbol = word
            break
    
    if mentioned_symbol:
        return f"""📈 **{mentioned_symbol} Stock Analysis**

**Current Price**: $182.52 (+2.1% today)
**Market Cap**: $2.85T
**P/E Ratio**: 28.4
**52-Week Range**: $124.17 - $199.62

🔍 **Technical Analysis**:
• **Trend**: Bullish (above 20-day & 50-day MA)
• **RSI**: 58.3 (Neutral territory)
• **MACD**: Bullish crossover signal
• **Volume**: Above average (+15%)
• **Support**: $175.00
• **Resistance**: $190.00

📊 **Fundamental Highlights**:
• Revenue Growth: 8.2% YoY
• Profit Margin: 23.7%
• ROE: 34.2%
• Debt-to-Equity: 0.63

💡 **Analyst Consensus**: BUY
**Price Target**: $195.00 (+6.8% upside)

The stock shows strong momentum with solid fundamentals. Consider entry on any dips below $178."""
    
    else:
        return """📈 **Stock Research Assistant**

I'd be happy to analyze any stock for you! Here's what I can provide:

🔍 **Analysis Types**:
• Technical indicators (RSI, MACD, Moving Averages)
• Fundamental metrics (P/E, ROE, Growth rates)
• Analyst ratings and price targets
• Risk assessment and volatility analysis
• Peer comparison and sector analysis

💡 **Popular Stocks to Analyze**:
• **FAANG**: Facebook, Apple, Amazon, Netflix, Google
• **EV Leaders**: Tesla, Rivian, Lucid Motors
• **AI Plays**: NVIDIA, AMD, Palantir
• **Cloud Giants**: Microsoft, Amazon Web Services
• **Dividend Kings**: Johnson & Johnson, Coca-Cola

Just mention any stock symbol (e.g., "Analyze AAPL" or "What's your take on Tesla?") and I'll provide a comprehensive analysis!"""

def generate_news_response(prompt: str) -> str:
    """Generate market news and sentiment responses"""
    
    return """📰 **Latest Market News & Sentiment**

🔥 **Top Stories Today**:

1. **Fed Signals Pause in Rate Hikes** 📉
   • Market rally on dovish comments
   • Tech stocks surge 2-3%
   • Bond yields fall to 4.8%

2. **AI Chip Demand Surges** 🚀
   • NVIDIA reports record quarter
   • Datacenter revenue up 206%
   • AI infrastructure spending accelerates

3. **Energy Transition Continues** 🌱
   • Clean energy investments hit $1.8T
   • Solar/wind costs reach new lows
   • ESG funds see massive inflows

📊 **Market Sentiment Analysis**:
• **Overall Sentiment**: 📈 Bullish (72% positive)
• **Fear & Greed Index**: 68 (Greed territory)
• **VIX**: 18.4 (Low volatility)
• **Put/Call Ratio**: 0.85 (Optimistic)

🎯 **Sector Rotation Trends**:
• **Outperforming**: Technology, Communication, Energy
• **Underperforming**: Utilities, Real Estate, Materials
• **Defensive Rotation**: Limited defensive positioning

💡 The market is showing risk-on behavior with strong momentum in growth sectors. Consider taking some profits if heavily concentrated in tech."""

def generate_recommendation_response(prompt: str) -> str:
    """Generate investment recommendation responses"""
    
    return """💡 **AI Investment Recommendations**

Based on current market conditions and analysis:

🚀 **Growth Opportunities** (High Risk/High Reward):
• **NVIDIA (NVDA)**: AI semiconductor leader
• **Tesla (TSLA)**: EV and energy storage
• **Palantir (PLTR)**: Enterprise AI solutions
• **Target**: 15-20% portfolio allocation

💎 **Value Plays** (Moderate Risk/Steady Returns):
• **Berkshire Hathaway (BRK.B)**: Diversified conglomerate
• **Johnson & Johnson (JNJ)**: Healthcare stability
• **Procter & Gamble (PG)**: Consumer staples
• **Target**: 25-30% portfolio allocation

🛡️ **Defensive Positions** (Low Risk/Income Focus):
• **Utilities ETF (XLU)**: Dividend stability
• **Real Estate (VNQ)**: REIT exposure
• **Treasury Bonds (TLT)**: Safe haven
• **Target**: 20-25% portfolio allocation

🌍 **International Diversification**:
• **Emerging Markets (VWO)**: Growth exposure
• **Developed Markets (VEA)**: Stability
• **Target**: 10-15% portfolio allocation

⚠️ **Risk Management**:
• Keep 5-10% cash for opportunities
• Set stop-losses at -15% for individual positions
• Rebalance quarterly to maintain targets

Would you like me to dive deeper into any of these recommendations?"""

def generate_risk_response(prompt: str) -> str:
    """Generate risk assessment responses"""
    
    return """⚠️ **Portfolio Risk Assessment**

📊 **Current Risk Profile**:
• **Portfolio Beta**: 1.15 (15% more volatile than market)
• **Sharpe Ratio**: 1.42 (Excellent risk-adjusted returns)
• **Value at Risk (95%)**: -2.5% daily
• **Maximum Drawdown**: -8.4% (vs -12% market average)

🎯 **Risk Concentration Analysis**:
• **Single Stock Risk**: AAPL (15.2% allocation) - Consider capping at 10%
• **Sector Risk**: Technology (45%) - High concentration risk
• **Geographic Risk**: US-heavy (85%) - Add international exposure
• **Currency Risk**: USD-focused - Consider hedged positions

📈 **Volatility Metrics**:
• **Annualized Volatility**: 16.8%
• **Downside Deviation**: 11.2%
• **Calmar Ratio**: 1.87 (Strong)
• **Sortino Ratio**: 2.14 (Excellent)

🛡️ **Risk Mitigation Strategies**:

1. **Diversification**:
   • Reduce tech to 35-40%
   • Add healthcare and utilities
   • Increase international exposure to 20%

2. **Hedging Options**:
   • Protective puts on large positions
   • VIX calls for market insurance
   • Sector rotation based on momentum

3. **Position Sizing**:
   • Maximum 10% in any single stock
   • Gradual entry/exit for large positions
   • Regular rebalancing schedule

💡 **Recommendation**: Your portfolio shows good risk-adjusted returns but could benefit from better diversification. Consider reducing tech concentration gradually."""

def generate_general_response(prompt: str) -> str:
    """Generate general financial assistant responses"""
    
    return """🤖 **AI Financial Assistant**

I'm here to help with all your financial and investment needs! Here's what I can assist you with:

📊 **Portfolio Management**:
• Performance analysis and optimization
• Risk assessment and diversification
• Rebalancing recommendations
• Asset allocation strategies

📈 **Stock Research**:
• Technical and fundamental analysis
• Earnings predictions and impact
• Sector comparisons and trends
• Price target analysis

📰 **Market Intelligence**:
• Real-time news and sentiment analysis
• Economic indicator interpretation
• Market trend identification
• Event-driven opportunities

💡 **Investment Planning**:
• Goal-based investing strategies
• Retirement planning optimization
• Tax-efficient investment structures
• ESG and sustainable investing

🎯 **Trading Support**:
• Entry and exit point identification
• Risk management strategies
• Option strategies and hedging
• Market timing insights

Just ask me specific questions like:
• "Analyze my portfolio performance"
• "What's the outlook for tech stocks?"
• "Find undervalued dividend stocks"
• "How should I hedge my positions?"

What would you like to explore today?"""
