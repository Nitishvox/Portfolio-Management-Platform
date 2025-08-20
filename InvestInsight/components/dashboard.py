import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import asyncio

def render_dashboard():
    """Render the main dashboard with portfolio overview and market data"""
    
    st.header("📊 Portfolio Dashboard")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>💰 Portfolio Value</h4>
            <h2>$125,847</h2>
            <p style="color: green">+$2,847 (+2.3%)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>📈 Today's P&L</h4>
            <h2>+$1,234</h2>
            <p style="color: green">+0.98%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>🎯 Total Return</h4>
            <h2>+15.7%</h2>
            <p style="color: green">Since inception</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h4>📊 Sharpe Ratio</h4>
            <h2>1.42</h2>
            <p style="color: green">Risk-adjusted</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Portfolio Performance")
        
        # Generate sample performance data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        portfolio_values = []
        initial_value = 123000
        
        for i, date in enumerate(dates):
            # Simulate portfolio growth with some volatility
            growth = 1 + (0.15 / 365) + (0.02 * (i % 7 - 3) / 100)
            if i == 0:
                portfolio_values.append(initial_value)
            else:
                portfolio_values.append(portfolio_values[-1] * growth)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=portfolio_values,
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=3),
            fill='tonexty',
            fillcolor='rgba(31, 119, 180, 0.2)'
        ))
        
        fig.update_layout(
            title="30-Day Portfolio Performance",
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏆 Top Holdings")
        
        # Sample holdings data
        holdings_data = [
            {"symbol": "AAPL", "weight": 15.2, "value": "$19,129", "change": "+2.1%"},
            {"symbol": "MSFT", "weight": 12.8, "value": "$16,108", "change": "+1.5%"},
            {"symbol": "GOOGL", "weight": 10.5, "value": "$13,214", "change": "+0.8%"},
            {"symbol": "TSLA", "weight": 8.9, "value": "$11,201", "change": "+3.2%"},
            {"symbol": "AMZN", "weight": 7.3, "value": "$9,187", "change": "-0.5%"}
        ]
        
        for holding in holdings_data:
            color = "green" if holding["change"].startswith("+") else "red"
            st.markdown(f"""
            <div style="background: #2d3142; padding: 0.8rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #1f77b4;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{holding['symbol']}</strong><br>
                        <small>{holding['weight']}% • {holding['value']}</small>
                    </div>
                    <div style="color: {color}; font-weight: bold;">
                        {holding['change']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Market overview section
    st.subheader("🌍 Market Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    market_data = [
        ("S&P 500", "4,150.48", "+1.2%", "green"),
        ("NASDAQ", "12,847.59", "+0.8%", "green"),
        ("DOW", "33,845.12", "-0.3%", "red"),
        ("VIX", "18.45", "-2.1%", "green")
    ]
    
    for i, (index, value, change, color) in enumerate(market_data):
        with [col1, col2, col3, col4][i]:
            icon = "🟢" if color == "green" else "🔴"
            st.markdown(f"""
            <div class="metric-card">
                <h4>{icon} {index}</h4>
                <h3>{value}</h3>
                <p style="color: {color}">{change}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # AI Insights section
    st.subheader("🤖 AI Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="search-container">
            <h4>💡 Portfolio Recommendations</h4>
            <ul>
                <li>🎯 Consider rebalancing - Technology sector is overweight (45%)</li>
                <li>📊 Add defensive positions - Healthcare ETFs showing strength</li>
                <li>🌟 ESG opportunities - Clean energy stocks trending upward</li>
                <li>⚡ Volatility alert - VIX below 20, consider protective puts</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="search-container">
            <h4>📰 Market Sentiment</h4>
            <ul>
                <li>😊 Overall sentiment: <strong style="color: green">Bullish</strong></li>
                <li>📈 Tech earnings season driving optimism</li>
                <li>🏛️ Fed policy uncertainty remains</li>
                <li>🌍 Global growth concerns persist</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Rebalance Portfolio", type="primary"):
            st.success("Portfolio rebalancing initiated!")
    
    with col2:
        if st.button("📊 Run Analysis"):
            st.info("AI analysis in progress...")
    
    with col3:
        if st.button("🎯 Optimize"):
            st.info("Portfolio optimization started...")
    
    with col4:
        if st.button("📰 Latest News"):
            st.info("Fetching latest market news...")
