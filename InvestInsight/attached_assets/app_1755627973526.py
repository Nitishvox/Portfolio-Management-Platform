import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Import our custom modules
try:
    from components.dashboard import render_dashboard
    from components.portfolio_view import render_portfolio_view  
    from components.search_interface import render_search_interface
    from components.chat_interface import render_chat_interface
    # Temporarily comment out problematic services until they're fixed
    # from services.llm_service import LLMService
    # from services.data_service import DataService
    # from services.portfolio_service import PortfolioService
    # from agents.search_agent import SearchAgent
    # from agents.analysis_agent import AnalysisAgent
    # from agents.portfolio_agent import PortfolioAgent
    # from agents.news_agent import NewsAgent
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Some components are still being configured. Basic functionality available.")

# Page configuration
st.set_page_config(
    page_title="OpenPort AI - Portfolio Management",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
    }
    
    .search-container {
        background: #262730;
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #1f77b4;
        margin: 1rem 0;
    }
    
    .portfolio-card {
        background: linear-gradient(135deg, #134e5e 0%, #71b280 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }
    
    .news-item {
        background: #2d3142;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    
    .agent-status {
        background: #1a1a1a;
        padding: 0.8rem;
        border-radius: 8px;
        border: 1px solid #333;
        margin: 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
try:
    # Temporarily disabled until services are fully fixed
    # if 'llm_service' not in st.session_state:
    #     st.session_state.llm_service = LLMService()
    # if 'data_service' not in st.session_state:
    #     st.session_state.data_service = DataService()
    # if 'portfolio_service' not in st.session_state:
    #     st.session_state.portfolio_service = PortfolioService()
    # if 'search_agent' not in st.session_state:
    #     st.session_state.search_agent = SearchAgent()
    # if 'analysis_agent' not in st.session_state:
    #     st.session_state.analysis_agent = AnalysisAgent()
    # if 'portfolio_agent' not in st.session_state:
    #     st.session_state.portfolio_agent = PortfolioAgent()
    # if 'news_agent' not in st.session_state:
    #     st.session_state.news_agent = NewsAgent()
    pass
except Exception as e:
    st.error(f"Service initialization error: {e}")
if 'portfolio_data' not in st.session_state:
    st.session_state.portfolio_data = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def main():
    # Main header
    st.markdown('<h1 class="main-header">🚀 OpenPort AI</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #888;">Advanced AI-Powered Portfolio Management System</p>', unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/1f77b4/ffffff?text=OpenPort+AI", width=200)
        
        st.markdown("---")
        page = st.selectbox(
            "🧭 Navigate",
            ["📊 Dashboard", "💼 Portfolio", "🔍 AI Search", "💬 AI Assistant", "📰 News Analysis"],
            index=0
        )
        
        st.markdown("---")
        st.subheader("🤖 AI Agents Status")
        
        # Agent status indicators
        agents_status = {
            "🕸️ Browser Search Agent": "🟢 Ready",
            "🧠 Analysis Agent": "🟢 Ready", 
            "📊 Portfolio Agent": "🟢 Ready",
            "📰 News Agent": "🟢 Ready"
        }
        
        for agent, status in agents_status.items():
            st.markdown(f'<div class="agent-status"><strong>{agent}</strong><br>{status}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("⚙️ Settings")
        
        # Model selection
        selected_model = st.selectbox(
            "🤖 Primary LLM Model",
            ["llama3.1:8b", "qwen2.5:7b", "deepseek-coder", "llama3.1:70b"],
            index=0
        )
        
        # Risk tolerance
        risk_tolerance = st.slider("📈 Risk Tolerance", 0.0, 1.0, 0.5, 0.1)
        
        # Update session state
        st.session_state.selected_model = selected_model
        st.session_state.risk_tolerance = risk_tolerance

    # Main content area
    if page == "📊 Dashboard":
        render_dashboard()
    elif page == "💼 Portfolio":
        render_portfolio_view()
    elif page == "🔍 AI Search":
        render_search_interface()
    elif page == "💬 AI Assistant":
        render_chat_interface()
    elif page == "📰 News Analysis":
        render_news_analysis()

def render_news_analysis():
    st.header("📰 AI-Powered News Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔍 Search Financial News")
        search_query = st.text_input("Enter topic, company, or market sector:", placeholder="e.g., Apple earnings, semiconductor market, renewable energy stocks")
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("🚀 AI Search", type="primary"):
                if search_query:
                    with st.spinner("🤖 AI agents gathering news..."):
                        # Simulate news gathering
                        news_results = st.session_state.news_agent.gather_news(search_query)
                        st.session_state.news_results = news_results
        
        with col_btn2:
            if st.button("📊 Market Sentiment"):
                if search_query:
                    with st.spinner("Analyzing market sentiment..."):
                        sentiment_data = st.session_state.news_agent.analyze_sentiment(search_query)
                        st.session_state.sentiment_data = sentiment_data
        
        with col_btn3:
            if st.button("🎯 Trading Signals"):
                if search_query:
                    with st.spinner("Generating trading signals..."):
                        signals = st.session_state.analysis_agent.generate_trading_signals(search_query)
                        st.session_state.trading_signals = signals
    
    with col2:
        st.subheader("📈 Market Overview")
        
        # Market indices
        indices_data = {
            "S&P 500": {"value": 4150.48, "change": "+1.2%", "color": "green"},
            "NASDAQ": {"value": 12847.59, "change": "+0.8%", "color": "green"},
            "DOW": {"value": 33845.12, "change": "-0.3%", "color": "red"},
            "VIX": {"value": 18.45, "change": "-2.1%", "color": "green"}
        }
        
        for index, data in indices_data.items():
            color = "🟢" if data["color"] == "green" else "🔴"
            st.markdown(f"""
            <div class="metric-card">
                <h4>{color} {index}</h4>
                <h3>{data['value']}</h3>
                <p style="color: {data['color']}">{data['change']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Display news results
    if hasattr(st.session_state, 'news_results') and st.session_state.news_results:
        st.subheader("📰 Latest News & Analysis")
        
        for news_item in st.session_state.news_results[:5]:
            st.markdown(f"""
            <div class="news-item">
                <h4>📄 {news_item.get('title', 'News Article')}</h4>
                <p><strong>Source:</strong> {news_item.get('source', 'AI Research')}</p>
                <p><strong>Sentiment:</strong> 
                    {'🟢 Positive' if news_item.get('sentiment', 0) > 0.1 
                     else '🔴 Negative' if news_item.get('sentiment', 0) < -0.1 
                     else '⚪ Neutral'}
                </p>
                <p>{news_item.get('summary', 'AI-generated summary of market impact and key insights.')}</p>
                <small>📅 {news_item.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M'))}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Sentiment analysis visualization
    if hasattr(st.session_state, 'sentiment_data'):
        st.subheader("📊 Sentiment Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment pie chart
            sentiment_labels = ['Positive', 'Negative', 'Neutral']
            sentiment_values = [45, 25, 30]  # Sample data
            
            fig = px.pie(
                values=sentiment_values, 
                names=sentiment_labels,
                title="Market Sentiment Distribution",
                color_discrete_sequence=['#00cc96', '#ef553b', '#636efa']
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Sentiment timeline
            dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='D')
            sentiment_scores = [0.2, -0.1, 0.3, 0.1, -0.2, 0.4, 0.2]  # Sample data
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=sentiment_scores,
                mode='lines+markers',
                name='Sentiment Score',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            fig.update_layout(
                title="Sentiment Timeline",
                xaxis_title="Date",
                yaxis_title="Sentiment Score",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
