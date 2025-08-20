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
    from services.llm_service import LLMService
    from services.data_service import DataService
    from services.portfolio_service import PortfolioService
    from agents.search_agent import SearchAgent
    from agents.analysis_agent import AnalysisAgent
    from agents.portfolio_agent import PortfolioAgent
    from agents.news_agent import NewsAgent
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

# Initialize session state and services
@st.cache_resource
def initialize_services():
    """Initialize all services once"""
    try:
        services = {
            'llm_service': LLMService(),
            'data_service': DataService(),
            'portfolio_service': PortfolioService(),
            'search_agent': SearchAgent(),
            'analysis_agent': AnalysisAgent(),
            'portfolio_agent': PortfolioAgent(),
            'news_agent': NewsAgent()
        }
        
        # Initialize LLM service asynchronously
        try:
            asyncio.create_task(services['llm_service'].initialize())
        except:
            pass  # Non-blocking if Ollama is not available
            
        return services
    except Exception as e:
        st.error(f"Service initialization error: {e}")
        return {}

# Initialize services
services = initialize_services()

# Store services in session state for access across components
for service_name, service_instance in services.items():
    if service_name not in st.session_state:
        st.session_state[service_name] = service_instance

# Initialize other session state variables
if 'portfolio_data' not in st.session_state:
    st.session_state.portfolio_data = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'news_results' not in st.session_state:
    st.session_state.news_results = []

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
        
        # Check agent status
        agents_status = {}
        for agent_name in ['search_agent', 'analysis_agent', 'portfolio_agent', 'news_agent']:
            if agent_name in st.session_state and st.session_state[agent_name] is not None:
                agents_status[agent_name] = "🟢 Ready"
            else:
                agents_status[agent_name] = "🔴 Offline"
        
        # Display agent status
        agent_display_names = {
            'search_agent': "🕸️ Browser Search Agent",
            'analysis_agent': "🧠 Analysis Agent",
            'portfolio_agent': "📊 Portfolio Agent",
            'news_agent': "📰 News Agent"
        }
        
        for agent_key, display_name in agent_display_names.items():
            status = agents_status.get(agent_key, "🔴 Offline")
            st.markdown(f'<div class="agent-status"><strong>{display_name}</strong><br>{status}</div>', unsafe_allow_html=True)
        
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
    try:
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
    except Exception as e:
        st.error(f"Error rendering page: {e}")
        st.error("Please check that all services are properly configured.")

def render_news_analysis():
    """Render news analysis page with working agents"""
    st.header("📰 AI-Powered News Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔍 Search Financial News")
        search_query = st.text_input("Enter topic, company, or market sector:", placeholder="e.g., Apple earnings, semiconductor market, renewable energy stocks")
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("🚀 AI Search", type="primary"):
                if search_query and 'news_agent' in st.session_state:
                    with st.spinner("🤖 AI agents gathering news..."):
                        # Use the actual news agent
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            news_results = loop.run_until_complete(
                                st.session_state.news_agent.gather_news(search_query)
                            )
                            st.session_state.news_results = news_results
                        except Exception as e:
                            st.error(f"News gathering failed: {e}")
                        finally:
                            loop.close()
        
        with col_btn2:
            if st.button("📊 Market Sentiment"):
                if search_query and 'news_agent' in st.session_state:
                    with st.spinner("Analyzing market sentiment..."):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            sentiment_data = loop.run_until_complete(
                                st.session_state.news_agent.analyze_sentiment(search_query)
                            )
                            st.session_state.sentiment_data = sentiment_data
                        except Exception as e:
                            st.error(f"Sentiment analysis failed: {e}")
                        finally:
                            loop.close()
        
        with col_btn3:
            if st.button("🎯 Trading Signals"):
                if search_query and 'analysis_agent' in st.session_state:
                    with st.spinner("Generating trading signals..."):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            signals = loop.run_until_complete(
                                st.session_state.analysis_agent.generate_trading_signals()
                            )
                            st.session_state.trading_signals = signals
                        except Exception as e:
                            st.error(f"Trading signal generation failed: {e}")
                        finally:
                            loop.close()
    
    with col2:
        st.subheader("📈 Market Overview")
        
        # Try to get real market data
        if 'data_service' in st.session_state:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                market_data = loop.run_until_complete(
                    st.session_state.data_service.get_market_indices()
                )
                loop.close()
                
                if 'indices' in market_data:
                    for symbol, data in market_data['indices'].items():
                        if 'error' not in data:
                            change_color = "green" if data.get('change', 0) >= 0 else "red"
                            change_icon = "🟢" if data.get('change', 0) >= 0 else "🔴"
                            st.markdown(f"""
                            <div class="metric-card">
                                <h4>{change_icon} {data['name']}</h4>
                                <h3>${data.get('current_price', 0):.2f}</h3>
                                <p style="color: {change_color}">{data.get('change_percent', 0):+.2f}%</p>
                            </div>
                            """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Failed to fetch market data: {e}")
        else:
            st.error("Data service not available")
    
    # Display news results
    if hasattr(st.session_state, 'news_results') and st.session_state.news_results:
        st.subheader("📰 Latest News & Analysis")
        
        for news_item in st.session_state.news_results[:5]:
            sentiment_analysis = news_item.get('sentiment_analysis', {})
            sentiment_score = sentiment_analysis.get('sentiment_score', 0)
            sentiment_label = sentiment_analysis.get('sentiment_label', 'Neutral')
            
            st.markdown(f"""
            <div class="news-item">
                <h4>📄 {news_item.get('title', 'News Article')}</h4>
                <p><strong>Source:</strong> {news_item.get('source', 'AI Research')}</p>
                <p><strong>Sentiment:</strong> 
                    {'🟢 ' + sentiment_label if sentiment_score > 0.1 
                     else '🔴 ' + sentiment_label if sentiment_score < -0.1 
                     else '⚪ ' + sentiment_label}
                </p>
                <p>{news_item.get('content', 'AI-generated summary of market impact and key insights.')[:200]}...</p>
                <small>📅 {news_item.get('published_at', datetime.now()).strftime('%Y-%m-%d %H:%M') if hasattr(news_item.get('published_at'), 'strftime') else str(news_item.get('published_at', datetime.now()))}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Sentiment analysis visualization
    if hasattr(st.session_state, 'sentiment_data') and st.session_state.sentiment_data:
        st.subheader("📊 Sentiment Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment pie chart
            sentiment_dist = st.session_state.sentiment_data.get('sentiment_distribution', {})
            if sentiment_dist:
                sentiment_labels = list(sentiment_dist.keys())
                sentiment_values = list(sentiment_dist.values())
                
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
            timeline_data = st.session_state.sentiment_data.get('sentiment_timeline', [])
            if timeline_data:
                dates = [pd.to_datetime(item['timestamp']) for item in timeline_data]
                scores = [item['sentiment_score'] for item in timeline_data]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=scores,
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
