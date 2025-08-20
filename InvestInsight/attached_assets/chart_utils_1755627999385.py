import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ChartUtils:
    """Utility class for creating financial charts and visualizations"""
    
    @staticmethod
    def create_portfolio_allocation_chart(allocations: Dict[str, float], title: str = "Portfolio Allocation") -> go.Figure:
        """Create a pie chart for portfolio allocation"""
        try:
            symbols = list(allocations.keys())
            weights = list(allocations.values())
            
            # Create color palette
            colors = px.colors.qualitative.Set3[:len(symbols)]
            
            fig = go.Figure(data=[go.Pie(
                labels=symbols,
                values=weights,
                hole=0.4,  # Donut chart
                marker=dict(colors=colors, line=dict(color='#000000', width=2)),
                textinfo='label+percent',
                textposition='outside',
                hovertemplate='<b>%{label}</b><br>Allocation: %{percent}<br>Weight: %{value:.4f}<extra></extra>'
            )])
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=20)),
                font=dict(size=12, color='white'),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=80, b=20, l=20, r=20),
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05
                )
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create allocation chart: {e}")
            return go.Figure()
    
    @staticmethod
    def create_price_chart(symbol: str, historical_data: List[Dict[str, Any]], 
                          indicators: Dict[str, Any] = None, 
                          chart_type: str = "candlestick") -> go.Figure:
        """Create a stock price chart with technical indicators"""
        try:
            if not historical_data:
                return go.Figure()
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            
            # Create subplots
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=(f'{symbol} Stock Price', 'Volume', 'Technical Indicators'),
                vertical_spacing=0.05,
                row_width=[0.6, 0.2, 0.2],
                specs=[[{"secondary_y": False}],
                      [{"secondary_y": False}], 
                      [{"secondary_y": True}]]
            )
            
            # Price chart
            if chart_type == "candlestick":
                fig.add_trace(
                    go.Candlestick(
                        x=df['date'],
                        open=df['open'],
                        high=df['high'],
                        low=df['low'],
                        close=df['close'],
                        name=symbol,
                        increasing_line_color='#00cc96',
                        decreasing_line_color='#ef553b'
                    ),
                    row=1, col=1
                )
            else:  # Line chart
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=df['close'],
                        mode='lines',
                        name=f'{symbol} Close',
                        line=dict(color='#636efa', width=2)
                    ),
                    row=1, col=1
                )
            
            # Add moving averages if available
            if indicators:
                if indicators.get('sma_20'):
                    sma_20_data = [indicators['sma_20']] * len(df)
                    fig.add_trace(
                        go.Scatter(
                            x=df['date'],
                            y=sma_20_data,
                            mode='lines',
                            name='SMA 20',
                            line=dict(color='orange', width=1, dash='dot')
                        ),
                        row=1, col=1
                    )
                
                if indicators.get('sma_50'):
                    sma_50_data = [indicators['sma_50']] * len(df)
                    fig.add_trace(
                        go.Scatter(
                            x=df['date'],
                            y=sma_50_data,
                            mode='lines',
                            name='SMA 50',
                            line=dict(color='red', width=1, dash='dash')
                        ),
                        row=1, col=1
                    )
            
            # Volume chart
            fig.add_trace(
                go.Bar(
                    x=df['date'],
                    y=df['volume'],
                    name='Volume',
                    marker_color='rgba(99, 110, 250, 0.6)'
                ),
                row=2, col=1
            )
            
            # Technical indicators
            if indicators:
                # RSI
                if indicators.get('rsi'):
                    rsi_data = [indicators['rsi']] * len(df)
                    fig.add_trace(
                        go.Scatter(
                            x=df['date'],
                            y=rsi_data,
                            mode='lines',
                            name='RSI',
                            line=dict(color='purple', width=2),
                            yaxis='y3'
                        ),
                        row=3, col=1
                    )
                    
                    # RSI overbought/oversold levels
                    fig.add_hline(y=70, line_dash="dash", line_color="red", 
                                annotation_text="Overbought (70)", row=3, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="green", 
                                annotation_text="Oversold (30)", row=3, col=1)
            
            # Update layout
            fig.update_layout(
                title=dict(text=f"{symbol} Technical Analysis", x=0.5, font=dict(size=20)),
                xaxis_rangeslider_visible=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=700,
                margin=dict(t=80, b=40, l=40, r=40)
            )
            
            # Update y-axes
            fig.update_yaxes(title_text="Price ($)", row=1, col=1)
            fig.update_yaxes(title_text="Volume", row=2, col=1)
            fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create price chart: {e}")
            return go.Figure()
    
    @staticmethod
    def create_portfolio_performance_chart(performance_data: List[Dict[str, Any]], 
                                         benchmark_data: List[Dict[str, Any]] = None,
                                         title: str = "Portfolio Performance") -> go.Figure:
        """Create portfolio performance chart with optional benchmark"""
        try:
            if not performance_data:
                return go.Figure()
            
            # Convert to DataFrame
            df = pd.DataFrame(performance_data)
            df['date'] = pd.to_datetime(df['date'])
            
            fig = go.Figure()
            
            # Portfolio performance
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['cumulative_return'],
                    mode='lines',
                    name='Portfolio',
                    line=dict(color='#636efa', width=3),
                    hovertemplate='<b>Portfolio</b><br>Date: %{x}<br>Return: %{y:.2f}%<extra></extra>'
                )
            )
            
            # Add benchmark if provided
            if benchmark_data:
                bench_df = pd.DataFrame(benchmark_data)
                bench_df['date'] = pd.to_datetime(bench_df['date'])
                
                fig.add_trace(
                    go.Scatter(
                        x=bench_df['date'],
                        y=bench_df['cumulative_return'],
                        mode='lines',
                        name='Benchmark',
                        line=dict(color='orange', width=2, dash='dot'),
                        hovertemplate='<b>Benchmark</b><br>Date: %{x}<br>Return: %{y:.2f}%<extra></extra>'
                    )
                )
            
            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=20)),
                xaxis_title="Date",
                yaxis_title="Cumulative Return (%)",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=400,
                margin=dict(t=80, b=40, l=40, r=40),
                hovermode='x unified'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create performance chart: {e}")
            return go.Figure()
    
    @staticmethod
    def create_risk_metrics_chart(risk_data: Dict[str, float], title: str = "Risk Metrics") -> go.Figure:
        """Create a bar chart for risk metrics"""
        try:
            metrics = list(risk_data.keys())
            values = list(risk_data.values())
            
            # Color code based on risk level
            colors = []
            for value in values:
                if abs(value) > 20:  # High risk
                    colors.append('#ef553b')
                elif abs(value) > 10:  # Medium risk
                    colors.append('#ffa500')
                else:  # Low risk
                    colors.append('#00cc96')
            
            fig = go.Figure(data=[
                go.Bar(
                    x=metrics,
                    y=values,
                    marker_color=colors,
                    text=[f'{v:.2f}%' for v in values],
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Value: %{y:.2f}%<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=20)),
                xaxis_title="Risk Metrics",
                yaxis_title="Value (%)",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=400,
                margin=dict(t=80, b=40, l=40, r=40)
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create risk metrics chart: {e}")
            return go.Figure()
    
    @staticmethod
    def create_efficient_frontier_chart(frontier_data: Dict[str, List[float]], 
                                      current_portfolio: Tuple[float, float] = None,
                                      title: str = "Efficient Frontier") -> go.Figure:
        """Create efficient frontier chart"""
        try:
            fig = go.Figure()
            
            # Efficient frontier curve
            if 'volatility' in frontier_data and 'returns' in frontier_data:
                fig.add_trace(
                    go.Scatter(
                        x=frontier_data['volatility'],
                        y=frontier_data['returns'],
                        mode='lines',
                        name='Efficient Frontier',
                        line=dict(color='#636efa', width=3),
                        hovertemplate='<b>Efficient Frontier</b><br>Volatility: %{x:.2f}%<br>Return: %{y:.2f}%<extra></extra>'
                    )
                )
            
            # Current portfolio point
            if current_portfolio:
                fig.add_trace(
                    go.Scatter(
                        x=[current_portfolio[1]],  # volatility
                        y=[current_portfolio[0]],  # return
                        mode='markers',
                        name='Current Portfolio',
                        marker=dict(color='red', size=12, symbol='star'),
                        hovertemplate='<b>Current Portfolio</b><br>Volatility: %{x:.2f}%<br>Return: %{y:.2f}%<extra></extra>'
                    )
                )
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=20)),
                xaxis_title="Volatility (%)",
                yaxis_title="Expected Return (%)",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=500,
                margin=dict(t=80, b=40, l=40, r=40)
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create efficient frontier chart: {e}")
            return go.Figure()
    
    @staticmethod
    def create_correlation_heatmap(correlation_matrix: pd.DataFrame, 
                                 title: str = "Asset Correlation Matrix") -> go.Figure:
        """Create correlation heatmap"""
        try:
            fig = go.Figure(data=go.Heatmap(
                z=correlation_matrix.values,
                x=correlation_matrix.columns,
                y=correlation_matrix.index,
                colorscale='RdBu',
                zmid=0,
                text=correlation_matrix.round(2).values,
                texttemplate='%{text}',
                textfont={"size": 10},
                hovertemplate='<b>%{y} vs %{x}</b><br>Correlation: %{z:.3f}<extra></extra>'
            ))
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=20)),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=500,
                margin=dict(t=80, b=40, l=40, r=40)
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create correlation heatmap: {e}")
            return go.Figure()
    
    @staticmethod
    def create_sector_allocation_chart(sector_data: Dict[str, float], 
                                     title: str = "Sector Allocation") -> go.Figure:
        """Create sector allocation chart"""
        try:
            sectors = list(sector_data.keys())
            allocations = list(sector_data.values())
            
            # Define sector colors
            sector_colors = {
                'Technology': '#636efa',
                'Healthcare': '#EF553B',
                'Financial': '#00cc96',
                'Consumer': '#ab63fa',
                'Industrial': '#FFA15A',
                'Energy': '#19d3f3',
                'Materials': '#FF6692',
                'Utilities': '#B6E880',
                'Real Estate': '#FF97FF',
                'Communication': '#FECB52'
            }
            
            colors = [sector_colors.get(sector, '#gray') for sector in sectors]
            
            fig = go.Figure(data=[go.Bar(
                x=sectors,
                y=allocations,
                marker_color=colors,
                text=[f'{a:.1f}%' for a in allocations],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Allocation: %{y:.2f}%<extra></extra>'
            )])
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=20)),
                xaxis_title="Sectors",
                yaxis_title="Allocation (%)",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=400,
                margin=dict(t=80, b=40, l=40, r=40),
                xaxis_tickangle=-45
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create sector allocation chart: {e}")
            return go.Figure()
    
    @staticmethod
    def create_drawdown_chart(performance_data: List[Dict[str, Any]], 
                            title: str = "Portfolio Drawdown") -> go.Figure:
        """Create drawdown chart"""
        try:
            if not performance_data:
                return go.Figure()
            
            # Convert to DataFrame and calculate drawdown
            df = pd.DataFrame(performance_data)
            df['date'] = pd.to_datetime(df['date'])
            df['cumulative_value'] = (1 + df['daily_return'] / 100).cumprod()
            
            # Calculate running maximum and drawdown
            df['running_max'] = df['cumulative_value'].expanding().max()
            df['drawdown'] = (df['cumulative_value'] - df['running_max']) / df['running_max'] * 100
            
            fig = go.Figure()
            
            # Drawdown area chart
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['drawdown'],
                    mode='lines',
                    name='Drawdown',
                    fill='tonexty',
                    line=dict(color='red', width=0),
                    fillcolor='rgba(255, 0, 0, 0.3)',
                    hovertemplate='<b>Drawdown</b><br>Date: %{x}<br>Drawdown: %{y:.2f}%<extra></extra>'
                )
            )
            
            # Zero line
            fig.add_hline(y=0, line_color="gray", line_width=1)
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=20)),
                xaxis_title="Date",
                yaxis_title="Drawdown (%)",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=400,
                margin=dict(t=80, b=40, l=40, r=40),
                yaxis=dict(range=[df['drawdown'].min() * 1.1, 5])  # Set y-axis range
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create drawdown chart: {e}")
            return go.Figure()
    
    @staticmethod
    def create_sentiment_timeline_chart(sentiment_data: List[Dict[str, Any]], 
                                      title: str = "Market Sentiment Timeline") -> go.Figure:
        """Create market sentiment timeline chart"""
        try:
            if not sentiment_data:
                return go.Figure()
            
            df = pd.DataFrame(sentiment_data)
            df['date'] = pd.to_datetime(df['date'])
            
            # Color based on sentiment
            colors = ['red' if s < -0.1 else 'green' if s > 0.1 else 'gray' 
                     for s in df['sentiment_score']]
            
            fig = go.Figure()
            
            # Sentiment line
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['sentiment_score'],
                    mode='lines+markers',
                    name='Sentiment Score',
                    line=dict(color='blue', width=2),
                    marker=dict(color=colors, size=8),
                    hovertemplate='<b>Sentiment</b><br>Date: %{x}<br>Score: %{y:.3f}<extra></extra>'
                )
            )
            
            # Sentiment zones
            fig.add_hline(y=0.1, line_dash="dash", line_color="green", 
                        annotation_text="Positive Threshold", opacity=0.7)
            fig.add_hline(y=-0.1, line_dash="dash", line_color="red", 
                        annotation_text="Negative Threshold", opacity=0.7)
            fig.add_hline(y=0, line_color="gray", line_width=1, opacity=0.5)
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=20)),
                xaxis_title="Date",
                yaxis_title="Sentiment Score",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=400,
                margin=dict(t=80, b=40, l=40, r=40),
                yaxis=dict(range=[-1, 1])
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create sentiment timeline: {e}")
            return go.Figure()

def format_currency(value: float, currency: str = "USD") -> str:
    """Format currency values for display"""
    if currency == "USD":
        if abs(value) >= 1e9:
            return f"${value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"${value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"${value/1e3:.2f}K"
        else:
            return f"${value:.2f}"
    else:
        return f"{value:.2f} {currency}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage values for display"""
    return f"{value:.{decimals}f}%"

def calculate_color_based_on_change(change: float) -> str:
    """Get color based on positive/negative change"""
    if change > 0:
        return "#00cc96"  # Green
    elif change < 0:
        return "#ef553b"  # Red
    else:
        return "#636efa"  # Blue (neutral)
