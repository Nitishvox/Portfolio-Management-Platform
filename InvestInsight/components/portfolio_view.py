import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import asyncio

def render_portfolio_view():
    """Render the portfolio management interface"""
    
    st.header("💼 Portfolio Management")
    
    # Portfolio tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Current Portfolio", "🎯 Optimization", "📈 Performance", "⚙️ Settings"])
    
    with tab1:
        render_current_portfolio()
    
    with tab2:
        render_portfolio_optimization()
    
    with tab3:
        render_portfolio_performance()
    
    with tab4:
        render_portfolio_settings()

def render_current_portfolio():
    """Render current portfolio holdings"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🏆 Current Holdings")
        
        # Sample portfolio data
        portfolio_data = [
            {"Symbol": "AAPL", "Shares": 50, "Price": "$182.52", "Value": "$9,126", "Weight": "15.2%", "P&L": "+$1,234", "P&L%": "+15.7%"},
            {"Symbol": "MSFT", "Shares": 40, "Price": "$378.85", "Value": "$15,154", "Weight": "12.8%", "P&L": "+$987", "P&L%": "+7.0%"},
            {"Symbol": "GOOGL", "Shares": 25, "Price": "$142.09", "Value": "$3,552", "Weight": "10.5%", "P&L": "+$456", "P&L%": "+14.7%"},
            {"Symbol": "TSLA", "Shares": 30, "Price": "$248.42", "Value": "$7,453", "Weight": "8.9%", "P&L": "+$789", "P&L%": "+11.9%"},
            {"Symbol": "AMZN", "Shares": 15, "Price": "$145.86", "Value": "$2,188", "Weight": "7.3%", "P&L": "-$123", "P&L%": "-5.3%"},
        ]
        
        df = pd.DataFrame(portfolio_data)
        
        # Style the dataframe
        def highlight_pnl(val):
            if isinstance(val, str) and val.startswith('+'):
                return 'color: green'
            elif isinstance(val, str) and val.startswith('-'):
                return 'color: red'
            return ''
        
        styled_df = df.style.applymap(highlight_pnl, subset=['P&L', 'P&L%'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Add/Remove positions
        st.subheader("➕ Manage Positions")
        
        col_add, col_remove = st.columns(2)
        
        with col_add:
            with st.expander("🆕 Add New Position"):
                new_symbol = st.text_input("Stock Symbol", placeholder="e.g., NVDA")
                new_shares = st.number_input("Number of Shares", min_value=1, value=10)
                if st.button("Add Position", type="primary"):
                    if new_symbol:
                        st.success(f"Added {new_shares} shares of {new_symbol}")
        
        with col_remove:
            with st.expander("❌ Remove Position"):
                symbols_to_remove = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
                symbol_to_remove = st.selectbox("Select Symbol", symbols_to_remove)
                if st.button("Remove Position", type="secondary"):
                    st.warning(f"Removed position in {symbol_to_remove}")
    
    with col2:
        st.subheader("📊 Portfolio Allocation")
        
        # Pie chart for allocation
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "Others"]
        weights = [15.2, 12.8, 10.5, 8.9, 7.3, 45.3]
        
        fig = px.pie(
            values=weights,
            names=symbols,
            title="Current Allocation",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Portfolio metrics
        st.subheader("📈 Key Metrics")
        
        metrics = [
            ("Total Value", "$125,847", "+2.3%"),
            ("Cash", "$8,423", "6.7%"),
            ("Dividend Yield", "2.1%", "Annual"),
            ("Beta", "1.15", "vs S&P 500"),
            ("Expense Ratio", "0.03%", "Weighted Avg")
        ]
        
        for metric, value, change in metrics:
            st.markdown(f"""
            <div style="background: #2d3142; padding: 0.8rem; border-radius: 8px; margin: 0.5rem 0;">
                <strong>{metric}</strong><br>
                <span style="font-size: 1.2em;">{value}</span><br>
                <small style="color: #888;">{change}</small>
            </div>
            """, unsafe_allow_html=True)

def render_portfolio_optimization():
    """Render portfolio optimization interface"""
    
    st.subheader("🎯 Portfolio Optimization")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Optimization Parameters")
        
        # Optimization settings
        optimization_method = st.selectbox(
            "Optimization Method",
            ["Maximum Sharpe Ratio", "Minimum Volatility", "Maximum Quadratic Utility", "Equal Weight"]
        )
        
        investment_amount = st.number_input(
            "Total Investment Amount ($)",
            min_value=1000,
            value=100000,
            step=1000
        )
        
        risk_tolerance = st.slider(
            "Risk Tolerance",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="0 = Conservative, 1 = Aggressive"
        )
        
        # Stock selection
        st.markdown("### Select Stocks for Optimization")
        
        available_stocks = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "NVDA", "META", "NFLX", "CRM", "ADBE"]
        selected_stocks = st.multiselect(
            "Choose stocks to include:",
            available_stocks,
            default=["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
        )
        
        if st.button("🚀 Optimize Portfolio", type="primary"):
            if selected_stocks:
                with st.spinner("🤖 AI optimizing your portfolio..."):
                    # Simulate optimization process
                    import time
                    time.sleep(2)
                    
                    st.success("✅ Portfolio optimization completed!")
                    
                    # Display optimization results
                    st.subheader("📊 Optimization Results")
                    
                    # Sample optimized weights
                    optimized_weights = {
                        "AAPL": 0.25,
                        "MSFT": 0.20,
                        "GOOGL": 0.18,
                        "TSLA": 0.15,
                        "AMZN": 0.12,
                        "NVDA": 0.10
                    }
                    
                    # Create allocation chart
                    fig = px.pie(
                        values=list(optimized_weights.values()),
                        names=list(optimized_weights.keys()),
                        title="Optimized Allocation"
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white')
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Performance metrics
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Expected Return", "12.5%", "2.3%")
                    with col_b:
                        st.metric("Volatility", "15.8%", "-1.2%")
                    with col_c:
                        st.metric("Sharpe Ratio", "1.42", "0.18")
            else:
                st.error("Please select at least one stock for optimization.")
    
    with col2:
        st.subheader("🔍 Optimization Insights")
        
        st.markdown("""
        <div class="search-container">
            <h4>💡 AI Recommendations</h4>
            <ul>
                <li>🎯 Current allocation shows high tech concentration</li>
                <li>📊 Consider adding defensive sectors</li>
                <li>🌟 International diversification opportunity</li>
                <li>⚡ Risk-adjusted returns can be improved</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("📈 Risk Metrics")
        
        risk_metrics = [
            ("Value at Risk (95%)", "-2.5%"),
            ("Maximum Drawdown", "-12.3%"),
            ("Beta", "1.15"),
            ("Correlation w/ Market", "0.89")
        ]
        
        for metric, value in risk_metrics:
            st.markdown(f"""
            <div style="background: #2d3142; padding: 0.8rem; border-radius: 8px; margin: 0.5rem 0;">
                <strong>{metric}</strong><br>
                <span style="font-size: 1.2em; color: #ff6b6b;">{value}</span>
            </div>
            """, unsafe_allow_html=True)

def render_portfolio_performance():
    """Render portfolio performance analysis"""
    
    st.subheader("📈 Performance Analysis")
    
    # Performance chart
    dates = pd.date_range(start=datetime.now() - timedelta(days=365), end=datetime.now(), freq='D')
    
    # Generate sample data for portfolio and benchmark
    portfolio_returns = []
    benchmark_returns = []
    
    for i in range(len(dates)):
        port_ret = 1 + (0.12 / 365) + (0.02 * (i % 10 - 5) / 100)
        bench_ret = 1 + (0.10 / 365) + (0.015 * (i % 8 - 4) / 100)
        
        if i == 0:
            portfolio_returns.append(100)
            benchmark_returns.append(100)
        else:
            portfolio_returns.append(portfolio_returns[-1] * port_ret)
            benchmark_returns.append(benchmark_returns[-1] * bench_ret)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=portfolio_returns,
        mode='lines',
        name='Portfolio',
        line=dict(color='#1f77b4', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=benchmark_returns,
        mode='lines',
        name='S&P 500',
        line=dict(color='orange', width=2, dash='dot')
    ))
    
    fig.update_layout(
        title="1-Year Performance vs Benchmark",
        xaxis_title="Date",
        yaxis_title="Normalized Value",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("1-Year Return", "15.7%", "5.7% vs S&P")
    with col2:
        st.metric("YTD Return", "8.9%", "2.1% vs S&P")
    with col3:
        st.metric("Volatility", "16.2%", "-1.8% vs S&P")
    with col4:
        st.metric("Max Drawdown", "-8.4%", "Better by 3.2%")

def render_portfolio_settings():
    """Render portfolio settings and preferences"""
    
    st.subheader("⚙️ Portfolio Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Investment Preferences")
        
        investment_style = st.selectbox(
            "Investment Style",
            ["Growth", "Value", "Blend", "Income", "Speculative"]
        )
        
        sector_preferences = st.multiselect(
            "Preferred Sectors",
            ["Technology", "Healthcare", "Financial", "Consumer", "Energy", "Materials", "Utilities"],
            default=["Technology", "Healthcare"]
        )
        
        esg_preference = st.checkbox("ESG/Sustainable Investing", value=True)
        dividend_focus = st.checkbox("Dividend Focus", value=False)
        
        rebalancing_frequency = st.selectbox(
            "Rebalancing Frequency",
            ["Monthly", "Quarterly", "Semi-annually", "Annually", "Manual"]
        )
    
    with col2:
        st.markdown("### 🔔 Alerts & Notifications")
        
        price_alerts = st.checkbox("Price Movement Alerts", value=True)
        news_alerts = st.checkbox("News & Earnings Alerts", value=True)
        rebalancing_alerts = st.checkbox("Rebalancing Notifications", value=True)
        
        alert_threshold = st.slider(
            "Price Alert Threshold (%)",
            min_value=1.0,
            max_value=10.0,
            value=5.0,
            step=0.5
        )
        
        st.markdown("### 💰 Risk Management")
        
        stop_loss = st.number_input(
            "Stop Loss (%)",
            min_value=0.0,
            max_value=50.0,
            value=15.0,
            step=1.0
        )
        
        position_limit = st.number_input(
            "Max Position Size (%)",
            min_value=1.0,
            max_value=100.0,
            value=20.0,
            step=1.0
        )
    
    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved successfully!")
