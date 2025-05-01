import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_futures_fair_value(data_service):
    """Render the Futures Fair Value Section"""
    st.header("5. Futures Fair Value")
    
    with st.spinner("Loading futures fair value data..."):
        # Get futures fair value data
        futures_data = data_service.get_futures_fair_value()
        
        if not futures_data:
            st.error("Unable to fetch futures fair value data. Please check API connections.")
            return
    
    # Display ES Futures vs Fair Value
    es_futures = futures_data.get("ES_Futures")
    spx = futures_data.get("SPX")
    fair_value = futures_data.get("Fair_Value")
    premium_discount = futures_data.get("Premium_Discount")
    premium_discount_pct = futures_data.get("Premium_Discount_Pct")
    premium_discount_label = futures_data.get("Premium_Discount_Label")
    
    if es_futures is not None and fair_value is not None:
        # Create columns for the metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("ES Futures", f"{es_futures:.2f}")
        
        with col2:
            st.metric("Fair Value", f"{fair_value:.2f}")
        
        with col3:
            if premium_discount is not None:
                # Determine color based on premium/discount
                delta_color = "normal"
                if premium_discount_label == "Premium":
                    delta_color = "normal"  # Green
                else:
                    delta_color = "inverse"  # Red
                
                st.metric(
                    premium_discount_label, 
                    f"{abs(premium_discount):.2f}",
                    delta=f"{premium_discount_pct:.2f}%" if premium_discount_pct is not None else None,
                    delta_color=delta_color
                )
        
        # Display a visual indicator of premium/discount
        if premium_discount is not None:
            # Create a gauge chart to show premium/discount
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=premium_discount,
                title={"text": "Futures Premium/Discount"},
                gauge={
                    "axis": {"range": [-10, 10]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [-10, -5], "color": "red"},
                        {"range": [-5, -1], "color": "orange"},
                        {"range": [-1, 1], "color": "lightgray"},
                        {"range": [1, 5], "color": "lightgreen"},
                        {"range": [5, 10], "color": "green"}
                    ],
                    "threshold": {
                        "line": {"color": "black", "width": 2},
                        "thickness": 0.75,
                        "value": 0
                    }
                }
            ))
            
            fig.update_layout(
                height=300,
                margin=dict(l=10, r=10, t=30, b=10)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Futures fair value data unavailable")
    
    # Display risk assessment based on real yield and futures premium/discount
    st.subheader("Market Risk Assessment")
    
    real_yield = futures_data.get("Real_Yield_5Y")
    risk_status = futures_data.get("Risk_Status")
    
    if real_yield is not None and risk_status is not None:
        # Display real yield
        st.metric("5-Year Real Yield", f"{real_yield:.2f}%")
        
        # Display risk status with appropriate styling
        if risk_status == "Risk-On":
            st.markdown(
                """
                <div style="background-color: #CCFFCC; padding: 10px; border-radius: 5px;">
                    <strong style="color: #009900; font-size: 1.2em;">RISK-ON</strong>
                    <p>Market signals indicate risk appetite. Positive real yields combined with futures premium 
                    suggest investors are favoring risk assets.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        elif risk_status == "Risk-Off":
            st.markdown(
                """
                <div style="background-color: #FFCCCC; padding: 10px; border-radius: 5px;">
                    <strong style="color: #990000; font-size: 1.2em;">RISK-OFF</strong>
                    <p>Market signals indicate risk aversion. Negative real yields combined with futures discount 
                    suggest investors are moving toward safer assets.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style="background-color: #CCCCFF; padding: 10px; border-radius: 5px;">
                    <strong style="color: #000099; font-size: 1.2em;">NEUTRAL</strong>
                    <p>Market signals are mixed, with no clear risk-on or risk-off bias evident.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.warning("Risk assessment data unavailable")
    
    # Daily premium/discount comparison
    st.subheader("Daily Premium/Discount")
    
    try:
        # Get data from database - only yesterday and today
        start_date = datetime.now() - timedelta(days=2)
        historical_ffv = data_service.db.get_futures_fair_value_data(start_date, datetime.now())
        
        if historical_ffv and len(historical_ffv) >= 1:
            # Sort data by timestamp
            historical_ffv = sorted(historical_ffv, key=lambda x: x["timestamp"])
            
            # Create a bar chart for today and yesterday (if available)
            fig = go.Figure()
            
            # If we have multiple data points, use most recent and second most recent
            if len(historical_ffv) >= 2:
                today_data = historical_ffv[-1]
                yesterday_data = historical_ffv[-2]
                
                # Add bars for today and yesterday
                fig.add_trace(
                    go.Bar(
                        x=["Yesterday", "Today"],
                        y=[yesterday_data["premium_discount"], today_data["premium_discount"]],
                        marker_color=["lightblue", "blue"],
                        text=[f"{yesterday_data['premium_discount']:.2f}", f"{today_data['premium_discount']:.2f}"],
                        textposition='auto'
                    )
                )
                
                # Add day-over-day change annotation
                change = today_data["premium_discount"] - yesterday_data["premium_discount"]
                change_pct = (change / abs(yesterday_data["premium_discount"])) * 100 if yesterday_data["premium_discount"] != 0 else 0
                change_text = f"Day-over-Day Change: {change:.2f} ({change_pct:.1f}%)"
                change_color = "green" if change > 0 else "red"
                
                fig.add_annotation(
                    x=1.5,
                    y=max(yesterday_data["premium_discount"], today_data["premium_discount"]) * 1.2,
                    text=change_text,
                    showarrow=False,
                    font=dict(color=change_color)
                )
            else:
                # Just one data point
                today_data = historical_ffv[0]
                fig.add_trace(
                    go.Bar(
                        x=["Today"],
                        y=[today_data["premium_discount"]],
                        marker_color=["blue"],
                        text=[f"{today_data['premium_discount']:.2f}"],
                        textposition='auto'
                    )
                )
            
            # Add reference line at zero
            fig.add_hline(
                y=0, 
                line_width=1, 
                line_dash="dash", 
                line_color="gray"
            )
            
            fig.update_layout(
                title="ES Futures Premium/Discount Comparison",
                yaxis_title="Premium/Discount",
                template="plotly_white",
                height=300,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add interpretation
            latest_pd = historical_ffv[-1]["premium_discount"]
            if latest_pd > 0:
                st.markdown(f"**Current Status:** <span style='color:green'>Premium of {latest_pd:.2f}</span> indicates **bullish sentiment**", unsafe_allow_html=True)
            elif latest_pd < 0:
                st.markdown(f"**Current Status:** <span style='color:red'>Discount of {abs(latest_pd):.2f}</span> indicates **bearish sentiment**", unsafe_allow_html=True)
            else:
                st.markdown("**Current Status:** Fair value is aligned with futures, indicating neutral market sentiment")
        else:
            st.info("No premium/discount data available yet. Data will appear as it's collected.")
    except Exception as e:
        st.error(f"Error creating premium/discount comparison: {e}")
    
    # Explanation of futures fair value
    with st.expander("About Futures Fair Value"):
        st.markdown("""
        **Futures Fair Value Calculation**
        
        The fair value of futures contracts represents the theoretical price at which futures should trade, based on the underlying index value, interest rates, and dividend yields.
        
        **Formula (simplified):**
        ```
        Fair Value = Index Price × (1 + (Risk-Free Rate - Dividend Yield) × (Days to Expiration / 365))
        ```
        
        **Premium/Discount Analysis:**
        
        When futures trade above fair value (premium), it typically indicates bullish market sentiment.
        When futures trade below fair value (discount), it often signals bearish market sentiment.
        
        Combining this premium/discount with real yield data provides additional context for risk-on or risk-off market conditions.
        """)
        