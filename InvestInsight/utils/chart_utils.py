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
