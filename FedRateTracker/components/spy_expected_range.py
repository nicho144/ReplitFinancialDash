import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yfinance as yf

def render_spy_range_chart(data_service):
    """Render a SPY chart with expected range visualization based on options-implied volatility"""
    st.header("📊 SPY Chart with Expected Range")
    
    # Fetch market breadth data which includes expected ranges
    breadth_data = data_service.get_market_breadth()
    futures_data = data_service.get_futures_fair_value()
    
    # Create tabs for different timeframes
    tab1, tab2 = st.tabs(["Daily View", "Weekly View"])
    
    # Get expected range data
    daily_range = breadth_data.get("ATM_Expected_Daily_Range")
    weekly_range = breadth_data.get("ATM_Expected_Weekly_Range")
    daily_pct = breadth_data.get("ATM_Expected_Daily_Pct")
    weekly_pct = breadth_data.get("ATM_Expected_Weekly_Pct")
    
    # CNBC Premarket Implied Open status
    premarket_status = futures_data.get("Premium_Discount_Label") if futures_data else None
    premarket_pct = futures_data.get("Premium_Discount_Pct") if futures_data else None
    
    with tab1:
        st.subheader("SPY Daily Chart with Expected Range")
        
        try:
            # Get SPY data
            spy = yf.Ticker("SPY")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # Last 30 days for context
            spy_hist = spy.history(start=start_date, end=end_date)
            
            if not spy_hist.empty:
                # Get last price
                last_close = spy_hist['Close'].iloc[-1]
                
                # Calculate expected range bands if available
                if daily_range is not None:
                    upper_band = last_close + daily_range
                    lower_band = last_close - daily_range
                    
                    # Create figure
                    fig = go.Figure()
                    
                    # Add SPY price
                    fig.add_trace(
                        go.Scatter(
                            x=spy_hist.index,
                            y=spy_hist['Close'],
                            mode='lines',
                            name='SPY',
                            line=dict(color='blue', width=2)
                        )
                    )
                    
                    # Add expected range zone for today
                    today = spy_hist.index[-1]
                    tomorrow = today + pd.Timedelta(days=1)
                    
                    # Create a shaded area for expected range
                    fig.add_trace(
                        go.Scatter(
                            x=[today, today, tomorrow, tomorrow],
                            y=[lower_band, upper_band, upper_band, lower_band],
                            fill="toself",
                            fillcolor="rgba(0, 128, 255, 0.2)",
                            line=dict(color="rgba(0, 128, 255, 0.5)"),
                            name=f"Expected Range (±{daily_range:.2f})",
                            hoverinfo="text",
                            text=f"Expected Range: {lower_band:.2f} to {upper_band:.2f}"
                        )
                    )
                    
                    # Add horizontal lines for the range
                    fig.add_hline(
                        y=upper_band,
                        line_width=1,
                        line_dash="dash",
                        line_color="rgba(0, 128, 255, 0.8)",
                        annotation_text=f"Upper Expected: {upper_band:.2f}",
                        annotation_position="right"
                    )
                    
                    fig.add_hline(
                        y=lower_band,
                        line_width=1,
                        line_dash="dash",
                        line_color="rgba(0, 128, 255, 0.8)",
                        annotation_text=f"Lower Expected: {lower_band:.2f}",
                        annotation_position="right"
                    )
                    
                    # Add CNBC premarket implied open indicator if available
                    if premarket_status and premarket_pct is not None:
                        implied_open = last_close * (1 + premarket_pct/100)
                        
                        # Determine color based on whether it's above or below yesterday's close
                        arrow_color = "green" if implied_open > last_close else "red"
                        
                        # Add an arrow annotation for the implied open
                        fig.add_annotation(
                            x=tomorrow,
                            y=implied_open,
                            ax=0,
                            ay=-40 if implied_open > last_close else 40,
                            xref="x",
                            yref="y",
                            text=f"Implied Open: {implied_open:.2f}",
                            showarrow=True,
                            arrowhead=2,
                            arrowsize=1,
                            arrowwidth=2,
                            arrowcolor=arrow_color
                        )
                    
                    # Update layout
                    fig.update_layout(
                        title=f"SPY Daily with Expected Range (±{daily_pct:.2f}%)",
                        xaxis_title="Date",
                        yaxis_title="Price ($)",
                        template="plotly_white",
                        height=500,
                        hovermode="x unified",
                        margin=dict(l=10, r=10, t=40, b=10)
                    )
                    
                    # Show the chart
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display premarket indicator
                    if premarket_status and premarket_pct is not None:
                        # Determine risk status based on premarket premium/discount
                        if premarket_status == "Premium" and premarket_pct > 0.1:
                            risk_status = "RISK-ON"
                            status_color = "#4CAF50"  # Green
                            description = "Futures trading at a premium to fair value indicates bullish sentiment"
                        elif premarket_status == "Discount" and premarket_pct < -0.1:
                            risk_status = "RISK-OFF"
                            status_color = "#F44336"  # Red
                            description = "Futures trading at a discount to fair value indicates bearish sentiment"
                        else:
                            risk_status = "NEUTRAL"
                            status_color = "#FFC107"  # Yellow
                            description = "Futures trading near fair value indicates neutral sentiment"
                        
                        # Create a visual indicator for CNBC premarket status
                        st.markdown(f"""
                        <div style="background-color: {status_color}20; padding: 15px; border-radius: 10px; 
                                  border-left: 8px solid {status_color}; margin: 10px 0;">
                            <h3 style="color: {status_color}; margin: 0;">CNBC Premarket Status: {risk_status}</h3>
                            <p style="margin-top: 10px;">
                                <strong>Implied Open:</strong> {premarket_status} to Fair Value ({premarket_pct:+.2f}%)
                            </p>
                            <p style="margin-top: 5px;">{description}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error("Expected range data not available")
            else:
                st.error("Unable to retrieve SPY data")
                
        except Exception as e:
            st.error(f"Error creating SPY chart: {e}")
    
    with tab2:
        st.subheader("SPY Weekly Chart with Expected Range")
        
        try:
            # Get SPY data - wider timeframe for weekly view
            spy = yf.Ticker("SPY")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)  # Last 90 days for context
            spy_hist = spy.history(start=start_date, end=end_date)
            
            if not spy_hist.empty:
                # Get last price
                last_close = spy_hist['Close'].iloc[-1]
                
                # Calculate expected range bands if available
                if weekly_range is not None:
                    upper_band = last_close + weekly_range
                    lower_band = last_close - weekly_range
                    
                    # Calculate Bollinger Bands (20, 2) for context
                    spy_hist['SMA20'] = spy_hist['Close'].rolling(window=20).mean()
                    spy_hist['STD20'] = spy_hist['Close'].rolling(window=20).std()
                    spy_hist['Upper_BB'] = spy_hist['SMA20'] + (spy_hist['STD20'] * 2)
                    spy_hist['Lower_BB'] = spy_hist['SMA20'] - (spy_hist['STD20'] * 2)
                    
                    # Create figure
                    fig = go.Figure()
                    
                    # Add SPY price
                    fig.add_trace(
                        go.Scatter(
                            x=spy_hist.index,
                            y=spy_hist['Close'],
                            mode='lines',
                            name='SPY',
                            line=dict(color='blue', width=2)
                        )
                    )
                    
                    # Add Bollinger Bands
                    fig.add_trace(
                        go.Scatter(
                            x=spy_hist.index,
                            y=spy_hist['Upper_BB'],
                            mode='lines',
                            name='Upper BB (20,2)',
                            line=dict(color='rgba(150, 150, 150, 0.7)', width=1, dash='dash')
                        )
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=spy_hist.index,
                            y=spy_hist['SMA20'],
                            mode='lines',
                            name='SMA 20',
                            line=dict(color='rgba(150, 150, 150, 0.7)', width=1)
                        )
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=spy_hist.index,
                            y=spy_hist['Lower_BB'],
                            mode='lines',
                            name='Lower BB (20,2)',
                            line=dict(color='rgba(150, 150, 150, 0.7)', width=1, dash='dash')
                        )
                    )
                    
                    # Add expected range zone for the week
                    today = spy_hist.index[-1]
                    end_of_week = today + pd.Timedelta(days=5)
                    
                    # Create a shaded area for expected range
                    fig.add_trace(
                        go.Scatter(
                            x=[today, today, end_of_week, end_of_week],
                            y=[lower_band, upper_band, upper_band, lower_band],
                            fill="toself",
                            fillcolor="rgba(0, 128, 255, 0.2)",
                            line=dict(color="rgba(0, 128, 255, 0.5)"),
                            name=f"Expected Range (±{weekly_range:.2f})",
                            hoverinfo="text",
                            text=f"Expected Range: {lower_band:.2f} to {upper_band:.2f}"
                        )
                    )
                    
                    # Add horizontal lines for the range
                    fig.add_hline(
                        y=upper_band,
                        line_width=1,
                        line_dash="dash",
                        line_color="rgba(0, 128, 255, 0.8)",
                        annotation_text=f"Upper Expected: {upper_band:.2f}",
                        annotation_position="right"
                    )
                    
                    fig.add_hline(
                        y=lower_band,
                        line_width=1,
                        line_dash="dash",
                        line_color="rgba(0, 128, 255, 0.8)",
                        annotation_text=f"Lower Expected: {lower_band:.2f}",
                        annotation_position="right"
                    )
                    
                    # Update layout
                    fig.update_layout(
                        title=f"SPY Weekly with Expected Range (±{weekly_pct:.2f}%)",
                        xaxis_title="Date",
                        yaxis_title="Price ($)",
                        template="plotly_white",
                        height=500,
                        hovermode="x unified",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        margin=dict(l=10, r=10, t=40, b=10)
                    )
                    
                    # Show the chart
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Add some explanatory text
                    st.markdown("""
                    **Chart Analysis:**
                    
                    The shaded blue area represents the expected trading range for SPY over the next week,
                    based on current options implied volatility. This range helps traders to:
                    
                    1. **Set appropriate stop-loss levels** - Consider using the bottom of the expected range
                    2. **Establish profit targets** - Upper band can serve as a potential profit-taking area
                    3. **Choose option strikes** - Select strikes beyond the expected range for selling premium
                    4. **Assess market risk** - Wider expected ranges suggest higher market uncertainty
                    
                    Compare the expected range to the Bollinger Bands to get a sense of whether options are
                    pricing in more or less movement than recent historical volatility.
                    """)
                else:
                    st.error("Expected range data not available")
            else:
                st.error("Unable to retrieve SPY data")
                
        except Exception as e:
            st.error(f"Error creating SPY chart: {e}")