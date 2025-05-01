import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils import interpret_volatility

def render_market_breadth(data_service):
    """Render the Market Breadth and Volatility Analysis section"""
    st.header("4. Market Breadth & Volatility Analysis")
    
    with st.spinner("Loading market breadth and volatility data..."):
        # Get market breadth data
        breadth_data = data_service.get_market_breadth()
        
        if not breadth_data:
            st.error("Unable to fetch market breadth data. Please check API connections.")
            return
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Market Breadth", "Volatility Analysis", "Options Pricing"])
    
    # Market Breadth Tab
    with tab1:
        st.subheader("Market Breadth Indicators")
        
        # Create columns for TICK and TRIN
        col1, col2 = st.columns(2)
        
        with col1:
            # Display TICK data
            tick_data = breadth_data.get("TICK")
            if tick_data is not None:
                tick_current = tick_data.get("current")
                tick_high = tick_data.get("high")
                tick_low = tick_data.get("low")
                
                st.metric("NYSE TICK", f"{tick_current:.0f}" if tick_current is not None else "N/A")
                
                # Display min/max values
                if tick_high is not None and tick_low is not None:
                    st.caption(f"Daily Range: {tick_low:.0f} to {tick_high:.0f}")
                
                # Interpretation
                if tick_current is not None:
                    if tick_current > 500:
                        st.success("Strong buying pressure")
                    elif tick_current < -500:
                        st.error("Strong selling pressure")
                    else:
                        st.info("Neutral market breadth")
            else:
                st.error("TICK data unavailable")
        
        with col2:
            # Display TRIN data
            trin = breadth_data.get("TRIN")
            if trin is not None:
                st.metric("NYSE TRIN (Arms Index)", f"{trin:.2f}")
                
                # Interpretation
                if trin < 0.8:
                    st.success("Bullish (strong buying)")
                elif trin > 1.2:
                    st.error("Bearish (strong selling)")
                else:
                    st.info("Neutral")
            else:
                st.error("TRIN data unavailable")
        
        # Display SKEW index
        st.subheader("CBOE SKEW Index")
        skew = breadth_data.get("SKEW")
        if skew is not None:
            st.metric("SKEW", f"{skew:.2f}")
            
            # Interpretation
            if skew > 150:
                st.error("Very high SKEW - heightened tail risk concerns")
            elif skew > 135:
                st.warning("Elevated SKEW - increased tail risk concerns")
            elif skew > 120:
                st.info("Moderate SKEW - normal tail risk perception")
            else:
                st.success("Low SKEW - minimal tail risk concerns")
            
            # Explanation of SKEW
            st.caption("""
            The SKEW index measures perceived tail risk in the S&P 500. 
            Higher values indicate greater concerns about potential extreme market moves.
            """)
        else:
            st.error("SKEW data unavailable")
    
    # Volatility Analysis Tab
    with tab2:
        st.subheader("Volatility Metrics: VIX, VXX, and Realized Volatility")
        
        # Get VIX, VXX, and realized volatility data
        vix = breadth_data.get("VIX")
        vix_change = breadth_data.get("VIX_Change")
        vix_change_pct = breadth_data.get("VIX_Change_Pct")
        
        vxx = breadth_data.get("VXX")  # VXX futures ETN
        vxx_change = breadth_data.get("VXX_Change")
        vxx_change_pct = breadth_data.get("VXX_Change_Pct")
        
        realized_vol = breadth_data.get("Realized_Vol")
        vix_premium = breadth_data.get("VIX_Premium")
        vrp = breadth_data.get("VRP")
        term_structure = breadth_data.get("Vol_Term_Structure")
        
        if vix is not None:
            # Display metrics in a 2x2 grid layout
            col1, col2 = st.columns(2)
            
            with col1:
                # VIX with change since yesterday
                delta_color = "inverse" if vix_change is not None and vix_change < 0 else "normal"
                st.metric(
                    "VIX Index (Current)", 
                    f"{vix:.2f}%", 
                    delta=f"{vix_change:.2f}% ({vix_change_pct:.2f}%)" if vix_change is not None else None,
                    delta_color=delta_color
                )
                
                if realized_vol is not None:
                    st.metric(
                        "20-Day Realized Volatility", 
                        f"{realized_vol:.2f}%"
                    )
            
            with col2:
                # VXX with change since yesterday
                if vxx is not None and vxx_change is not None:
                    delta_color = "inverse" if vxx_change < 0 else "normal"
                    st.metric(
                        "VXX Volatility ETN", 
                        f"{vxx:.2f}", 
                        delta=f"{vxx_change:.2f} ({vxx_change_pct:.2f}%)",
                        delta_color=delta_color
                    )
                else:
                    st.metric("VXX Volatility ETN", "N/A")
                
                if vix_premium is not None:
                    st.metric(
                        "VIX Premium vs Realized", 
                        f"{vix_premium:.2f}%", 
                        delta=f"{vix_premium:.2f}%"
                    )
            
            # VIX term structure (VXX/VIX relationship)
            if term_structure is not None:
                # Create colored visual indicator for term structure
                term_colors = {
                    "Contango": "#4CAF50",     # Green (bullish)
                    "Neutral": "#FFC107",      # Yellow (neutral)
                    "Backwardation": "#F44336" # Red (bearish)
                }
                
                term_descriptions = {
                    "Contango": "VIX futures trading higher than spot VIX - market expects volatility to increase (bullish)",
                    "Neutral": "VIX futures and spot VIX at similar levels - market uncertainty about future volatility",
                    "Backwardation": "VIX futures trading below spot VIX - market expects volatility to decrease (bearish)"
                }
                
                color = term_colors.get(term_structure, "#9E9E9E")
                description = term_descriptions.get(term_structure, "")
                
                st.markdown(f"""
                <div style="background-color: {color}20; padding: 10px; border-radius: 5px; 
                            border-left: 5px solid {color}; margin-top: 15px;">
                    <h4 style="color: {color}; margin: 0;">VIX Term Structure: {term_structure}</h4>
                    <p style="margin-top: 5px;">{description}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Create a chart comparing VIX and Realized Vol
            try:
                # Create a placeholder chart (in production would use historical data)
                # Get historical VIX data for context
                import yfinance as yf
                
                vix_ticker = yf.Ticker("^VIX")
                vix_hist = vix_ticker.history(period="30d")
                
                if not vix_hist.empty:
                    # Create a chart
                    fig = go.Figure()
                    
                    # Add VIX trace
                    fig.add_trace(
                        go.Scatter(
                            x=vix_hist.index,
                            y=vix_hist['Close'],
                            mode='lines',
                            name='VIX',
                            line=dict(color='red', width=2)
                        )
                    )
                    
                    # Add a horizontal line for realized vol
                    fig.add_hline(
                        y=realized_vol, 
                        line_width=2, 
                        line_dash="dash", 
                        line_color="blue", 
                        annotation_text=f"Realized Vol: {realized_vol:.2f}%"
                    )
                    
                    fig.update_layout(
                        title="VIX vs Realized Volatility",
                        xaxis_title="Date",
                        yaxis_title="Volatility (%)",
                        template="plotly_white",
                        height=400,
                        margin=dict(l=10, r=10, t=40, b=10)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not load VIX chart: {e}")
            
            # Display Volatility Risk Premium
            st.subheader("Volatility Risk Premium (VRP)")
            
            if vrp is not None:
                st.metric("VRP Ratio", f"{vrp:.2f}x")
                
                # Interpretation
                interpretation = interpret_volatility(vix, realized_vol, vrp)
                st.info(interpretation)
            else:
                st.error("VRP data unavailable")
        else:
            st.error("Volatility data unavailable")
    
    # Options Pricing Tab
    with tab3:
        st.subheader("ATM Strangle Expected Range")
        
        # Get expected range data
        daily_range = breadth_data.get("ATM_Expected_Daily_Range")
        weekly_range = breadth_data.get("ATM_Expected_Weekly_Range")
        daily_pct = breadth_data.get("ATM_Expected_Daily_Pct")
        weekly_pct = breadth_data.get("ATM_Expected_Weekly_Pct")
        
        if daily_range is not None and weekly_range is not None:
            # Display metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Expected Daily Range", f"±{daily_range:.2f}")
                st.caption(f"±{daily_pct:.2f}% of current price")
            
            with col2:
                st.metric("Expected Weekly Range", f"±{weekly_range:.2f}")
                st.caption(f"±{weekly_pct:.2f}% of current price")
            
            # Explain the calculation
            st.markdown("""
            **Expected Range Calculation:**
            
            The expected range is calculated using the current at-the-money (ATM) implied 
            volatility for both calls and puts. This represents the market's expectation 
            for potential price movement within the given timeframe.
            
            Formula: `Expected Range = Current Price × ATM IV × √(Days/252)`
            """)
        else:
            st.error("Expected range data unavailable")
        
        # Options Status (cheap or expensive)
        st.subheader("Options Pricing Status")
        
        options_status = breadth_data.get("Options_Status")
        if options_status is not None:
            # Display options status with appropriate color
            if options_status == "Expensive":
                st.markdown(
                    """
                    <div style="background-color: #FFCCCC; padding: 10px; border-radius: 5px;">
                        <strong style="color: #990000;">Options Status: EXPENSIVE</strong>
                        <p>Options are trading at a premium to historical realized volatility. 
                        This may present opportunities for option selling strategies.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            elif options_status == "Cheap":
                st.markdown(
                    """
                    <div style="background-color: #CCFFCC; padding: 10px; border-radius: 5px;">
                        <strong style="color: #009900;">Options Status: CHEAP</strong>
                        <p>Options are trading at a discount to historical realized volatility. 
                        This may present opportunities for option buying strategies.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div style="background-color: #CCCCFF; padding: 10px; border-radius: 5px;">
                        <strong style="color: #000099;">Options Status: FAIR VALUE</strong>
                        <p>Options are trading in line with historical realized volatility.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.error("Options status data unavailable")
    
    # Add Risk Sentiment Verdict Section
    st.header("Risk Sentiment Verdict")
    
    # Gather risk factors from various components
    futures_data = data_service.get_futures_fair_value()
    news_data = data_service.get_financial_news()
    treasury_data = data_service.get_treasury_yields()
    
    # 1. Get risk factors from market data
    risk_factors = {
        # Breadth indicators
        "tick": breadth_data.get("TICK", {}).get("current"),
        "trin": breadth_data.get("TRIN"),
        "skew": breadth_data.get("SKEW"),
        
        # Volatility indicators
        "vix": breadth_data.get("VIX"),
        "vix_change": breadth_data.get("VIX_Change"),
        "vix_term_structure": breadth_data.get("Vol_Term_Structure"),
        
        # Futures indicators
        "futures_fair_value": futures_data.get("Premium_Discount_Label") if futures_data else None,
        "futures_fair_value_pct": futures_data.get("Premium_Discount_Pct") if futures_data else None,
        
        # Treasury indicators
        "yield_curve_2y10y": treasury_data.get("2Y_10Y_spread") if treasury_data else None,
        "real_yield": futures_data.get("Real_Yield_5Y") if futures_data else None
    }
    
    # 2. Get risk factors from news analysis
    news_risk_status = None
    if news_data:
        for item in news_data:
            if isinstance(item, dict) and "headline_sentiment_summary" in item:
                summary = item["headline_sentiment_summary"]
                news_risk_status = summary.get("news_risk_status")
                risk_on_count = summary.get("risk_on_count", 0)
                risk_off_count = summary.get("risk_off_count", 0)
                break
    
    # 3. Calculate risk verdict
    total_score = 0
    total_factors = 0
    factor_weights = {
        "vix": 2,
        "vix_change": 1,
        "vix_term_structure": 2,
        "tick": 1,
        "trin": 1,
        "skew": 1,
        "yield_curve_2y10y": 3,
        "futures_fair_value": 2,
        "news_sentiment": 3,
        "real_yield": 2
    }
    
    # Process each factor and calculate weighted score
    factor_details = []
    
    # VIX level
    if risk_factors["vix"] is not None:
        if risk_factors["vix"] > 30:
            factor_details.append({"name": "VIX Level", "status": "Risk-Off", "value": f"{risk_factors['vix']:.2f}%", "weight": factor_weights["vix"]})
            total_score -= factor_weights["vix"]
        elif risk_factors["vix"] < 15:
            factor_details.append({"name": "VIX Level", "status": "Risk-On", "value": f"{risk_factors['vix']:.2f}%", "weight": factor_weights["vix"]})
            total_score += factor_weights["vix"]
        else:
            factor_details.append({"name": "VIX Level", "status": "Neutral", "value": f"{risk_factors['vix']:.2f}%", "weight": factor_weights["vix"]})
        total_factors += factor_weights["vix"]
    
    # VIX change
    if risk_factors["vix_change"] is not None:
        if risk_factors["vix_change"] > 1.0:
            factor_details.append({"name": "VIX Change", "status": "Risk-Off", "value": f"{risk_factors['vix_change']:.2f}%", "weight": factor_weights["vix_change"]})
            total_score -= factor_weights["vix_change"]
        elif risk_factors["vix_change"] < -1.0:
            factor_details.append({"name": "VIX Change", "status": "Risk-On", "value": f"{risk_factors['vix_change']:.2f}%", "weight": factor_weights["vix_change"]})
            total_score += factor_weights["vix_change"]
        else:
            factor_details.append({"name": "VIX Change", "status": "Neutral", "value": f"{risk_factors['vix_change']:.2f}%", "weight": factor_weights["vix_change"]})
        total_factors += factor_weights["vix_change"]
    
    # VIX term structure
    if risk_factors["vix_term_structure"] is not None:
        if risk_factors["vix_term_structure"] == "Backwardation":
            factor_details.append({"name": "VIX Term Structure", "status": "Risk-Off", "value": risk_factors["vix_term_structure"], "weight": factor_weights["vix_term_structure"]})
            total_score -= factor_weights["vix_term_structure"]
        elif risk_factors["vix_term_structure"] == "Contango":
            factor_details.append({"name": "VIX Term Structure", "status": "Risk-On", "value": risk_factors["vix_term_structure"], "weight": factor_weights["vix_term_structure"]})
            total_score += factor_weights["vix_term_structure"]
        else:
            factor_details.append({"name": "VIX Term Structure", "status": "Neutral", "value": risk_factors["vix_term_structure"], "weight": factor_weights["vix_term_structure"]})
        total_factors += factor_weights["vix_term_structure"]
    
    # TICK
    if risk_factors["tick"] is not None:
        if risk_factors["tick"] > 500:
            factor_details.append({"name": "NYSE TICK", "status": "Risk-On", "value": f"{risk_factors['tick']:.0f}", "weight": factor_weights["tick"]})
            total_score += factor_weights["tick"]
        elif risk_factors["tick"] < -500:
            factor_details.append({"name": "NYSE TICK", "status": "Risk-Off", "value": f"{risk_factors['tick']:.0f}", "weight": factor_weights["tick"]})
            total_score -= factor_weights["tick"]
        else:
            factor_details.append({"name": "NYSE TICK", "status": "Neutral", "value": f"{risk_factors['tick']:.0f}", "weight": factor_weights["tick"]})
        total_factors += factor_weights["tick"]
    
    # TRIN
    if risk_factors["trin"] is not None:
        if risk_factors["trin"] < 0.8:
            factor_details.append({"name": "NYSE TRIN", "status": "Risk-On", "value": f"{risk_factors['trin']:.2f}", "weight": factor_weights["trin"]})
            total_score += factor_weights["trin"]
        elif risk_factors["trin"] > 1.2:
            factor_details.append({"name": "NYSE TRIN", "status": "Risk-Off", "value": f"{risk_factors['trin']:.2f}", "weight": factor_weights["trin"]})
            total_score -= factor_weights["trin"]
        else:
            factor_details.append({"name": "NYSE TRIN", "status": "Neutral", "value": f"{risk_factors['trin']:.2f}", "weight": factor_weights["trin"]})
        total_factors += factor_weights["trin"]
    
    # SKEW
    if risk_factors["skew"] is not None:
        if risk_factors["skew"] > 140:
            factor_details.append({"name": "CBOE SKEW", "status": "Risk-Off", "value": f"{risk_factors['skew']:.2f}", "weight": factor_weights["skew"]})
            total_score -= factor_weights["skew"]
        elif risk_factors["skew"] < 120:
            factor_details.append({"name": "CBOE SKEW", "status": "Risk-On", "value": f"{risk_factors['skew']:.2f}", "weight": factor_weights["skew"]})
            total_score += factor_weights["skew"]
        else:
            factor_details.append({"name": "CBOE SKEW", "status": "Neutral", "value": f"{risk_factors['skew']:.2f}", "weight": factor_weights["skew"]})
        total_factors += factor_weights["skew"]
    
    # Yield curve
    if risk_factors["yield_curve_2y10y"] is not None:
        if risk_factors["yield_curve_2y10y"] < 0:
            factor_details.append({"name": "2Y-10Y Yield Curve", "status": "Risk-Off", "value": f"{risk_factors['yield_curve_2y10y']:.2f}%", "weight": factor_weights["yield_curve_2y10y"]})
            total_score -= factor_weights["yield_curve_2y10y"]
        elif risk_factors["yield_curve_2y10y"] > 0.5:
            factor_details.append({"name": "2Y-10Y Yield Curve", "status": "Risk-On", "value": f"{risk_factors['yield_curve_2y10y']:.2f}%", "weight": factor_weights["yield_curve_2y10y"]})
            total_score += factor_weights["yield_curve_2y10y"]
        else:
            factor_details.append({"name": "2Y-10Y Yield Curve", "status": "Neutral", "value": f"{risk_factors['yield_curve_2y10y']:.2f}%", "weight": factor_weights["yield_curve_2y10y"]})
        total_factors += factor_weights["yield_curve_2y10y"]
    
    # Futures fair value
    if risk_factors["futures_fair_value"] is not None and risk_factors["futures_fair_value_pct"] is not None:
        if risk_factors["futures_fair_value"] == "Premium" and risk_factors["futures_fair_value_pct"] > 0.1:
            factor_details.append({"name": "ES/Fair Value", "status": "Risk-On", "value": f"{risk_factors['futures_fair_value']} ({risk_factors['futures_fair_value_pct']:.2f}%)", "weight": factor_weights["futures_fair_value"]})
            total_score += factor_weights["futures_fair_value"]
        elif risk_factors["futures_fair_value"] == "Discount" and risk_factors["futures_fair_value_pct"] < -0.1:
            factor_details.append({"name": "ES/Fair Value", "status": "Risk-Off", "value": f"{risk_factors['futures_fair_value']} ({risk_factors['futures_fair_value_pct']:.2f}%)", "weight": factor_weights["futures_fair_value"]})
            total_score -= factor_weights["futures_fair_value"]
        else:
            factor_details.append({"name": "ES/Fair Value", "status": "Neutral", "value": f"{risk_factors['futures_fair_value']} ({risk_factors['futures_fair_value_pct']:.2f}%)", "weight": factor_weights["futures_fair_value"]})
        total_factors += factor_weights["futures_fair_value"]
    
    # Real yield
    if risk_factors["real_yield"] is not None:
        if risk_factors["real_yield"] > 1.0:
            factor_details.append({"name": "5Y Real Yield", "status": "Risk-On", "value": f"{risk_factors['real_yield']:.2f}%", "weight": factor_weights["real_yield"]})
            total_score += factor_weights["real_yield"]
        elif risk_factors["real_yield"] < 0:
            factor_details.append({"name": "5Y Real Yield", "status": "Risk-Off", "value": f"{risk_factors['real_yield']:.2f}%", "weight": factor_weights["real_yield"]})
            total_score -= factor_weights["real_yield"]
        else:
            factor_details.append({"name": "5Y Real Yield", "status": "Neutral", "value": f"{risk_factors['real_yield']:.2f}%", "weight": factor_weights["real_yield"]})
        total_factors += factor_weights["real_yield"]
    
    # News sentiment
    if news_risk_status is not None:
        if news_risk_status == "Risk-On":
            factor_details.append({"name": "News Headlines", "status": "Risk-On", "value": news_risk_status, "weight": factor_weights["news_sentiment"]})
            total_score += factor_weights["news_sentiment"]
        elif news_risk_status == "Risk-Off":
            factor_details.append({"name": "News Headlines", "status": "Risk-Off", "value": news_risk_status, "weight": factor_weights["news_sentiment"]})
            total_score -= factor_weights["news_sentiment"]
        else:
            factor_details.append({"name": "News Headlines", "status": "Neutral", "value": news_risk_status, "weight": factor_weights["news_sentiment"]})
        total_factors += factor_weights["news_sentiment"]
    
    # Normalize score to -100 to +100 scale
    normalized_score = 0
    if total_factors > 0:
        normalized_score = (total_score / total_factors) * 100
    
    # Determine overall risk verdict
    if normalized_score > 30:
        risk_verdict = "RISK-ON"
        verdict_color = "#4CAF50"  # Green
        verdict_description = "Risk appetite is high. Market indicators suggest a bullish environment favorable for risk assets."
    elif normalized_score < -30:
        risk_verdict = "RISK-OFF"
        verdict_color = "#F44336"  # Red
        verdict_description = "Risk aversion is high. Market indicators suggest a bearish environment favoring defensive assets."
    else:
        risk_verdict = "NEUTRAL"
        verdict_color = "#FFC107"  # Yellow
        verdict_description = "Mixed signals with no clear risk bias. Market indicators suggest a balanced approach."
    
    # Display the risk verdict
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Create a gauge-like indicator for risk sentiment
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = normalized_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Risk Sentiment"},
            delta = {'reference': 0},
            gauge = {
                'axis': {'range': [-100, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': verdict_color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [-100, -30], 'color': 'rgba(244, 67, 54, 0.3)'},  # Risk-Off zone
                    {'range': [-30, 30], 'color': 'rgba(255, 193, 7, 0.3)'},    # Neutral zone
                    {'range': [30, 100], 'color': 'rgba(76, 175, 80, 0.3)'}     # Risk-On zone
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 3},
                    'thickness': 0.75,
                    'value': normalized_score
                }
            }
        ))
        
        fig.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=50, b=10),
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Display the verdict with explanation
        st.markdown(f"""
        <div style="background-color: {verdict_color}20; padding: 15px; border-radius: 10px; 
                    border-left: 8px solid {verdict_color}; height: 220px;">
            <h1 style="color: {verdict_color}; margin: 0; font-size: 32px;">{risk_verdict}</h1>
            <p style="margin-top: 15px; font-size: 16px;">{verdict_description}</p>
            <p style="margin-top: 15px; font-size: 16px;">
                <strong>Composite Score:</strong> {normalized_score:.1f} 
                (based on {len(factor_details)} market indicators)
            </p>
            <p style="font-size: 14px; margin-top: 20px; color: gray;">
                Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Display the factor details in a table
    st.subheader("Risk Factor Analysis")
    
    # Convert to DataFrame for display
    import pandas as pd
    df = pd.DataFrame(factor_details)
    
    if not df.empty:
        # Define a function to apply color to status cells
        def highlight_status(val):
            color = "white"
            if val == "Risk-On":
                color = "#e6ffe6"  # Light green
            elif val == "Risk-Off":
                color = "#ffe6e6"  # Light red
            elif val == "Neutral":
                color = "#fffde6"  # Light yellow
            return f'background-color: {color}'
        
        # Apply styling
        styled_df = df.style.map(highlight_status, subset=['status'])
        
        # Display table
        st.dataframe(styled_df, use_container_width=True)
        
        # Display CNBC headlines that contributed to sentiment
        if news_data:
            st.subheader("CNBC Headlines (Sentiment Confirmation)")
            
            # Filter for CNBC headlines only
            cnbc_headlines = [item for item in news_data if isinstance(item, dict) and 
                             item.get('source') == 'CNBC' and
                             item.get('is_headline', False)]
            
            if cnbc_headlines:
                for headline in cnbc_headlines[:5]:  # Show top 5 headlines
                    sentiment = headline.get('risk_sentiment', 'neutral')
                    title = headline.get('title', '')
                    
                    sentiment_color = "#FFC107"  # Yellow/neutral default
                    if sentiment == 'risk-on':
                        sentiment_color = "#4CAF50"  # Green
                    elif sentiment == 'risk-off':
                        sentiment_color = "#F44336"  # Red
                    
                    st.markdown(f"""
                    <div style="padding: 8px 15px; margin-bottom: 8px; border-radius: 5px; 
                                border-left: 5px solid {sentiment_color};">
                        {title}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No CNBC headlines available to confirm sentiment")
    else:
        st.info("Market risk factor data not available")
    
    # Explanations
    with st.expander("About Market Breadth & Volatility Metrics"):
        st.markdown("""
        **Market Breadth Indicators**
        
        **TICK**: Measures the number of stocks trading on an uptick minus the number trading on a downtick. 
        Extreme readings indicate strong buying or selling pressure.
        
        **TRIN (Arms Index)**: Ratio of advancing/declining volume to advancing/declining issues. 
        Values below 1.0 indicate bullish sentiment, while values above 1.0 indicate bearish sentiment.
        
        **SKEW Index**: Measures perceived tail risk in S&P 500 options. Higher values indicate greater 
        concern about potential black swan events.
        
        **Volatility Metrics**
        
        **VIX**: Market's expectation of 30-day forward-looking volatility derived from S&P 500 option prices.
        
        **VXX**: VIX futures ETN tracking short-term VIX futures, showing market expectation for future volatility.
        
        **Realized Volatility**: Historical volatility measured from actual price movements.
        
        **VIX Premium**: Difference between VIX and Realized Volatility, indicates whether the market is 
        overpricing or underpricing future volatility.
        
        **Volatility Risk Premium (VRP)**: Ratio of implied to realized volatility. Values above 1.0 indicate 
        options are expensive relative to historical movement.
        
        **ATM Strangle Expected Range**: The market-implied price range based on current implied volatility, 
        useful for setting price targets and stop levels.
        
        **VIX Term Structure**: The relationship between spot VIX and futures (measured by VXX). Contango (VXX > VIX) 
        is typically bullish, while backwardation (VIX > VXX) is typically bearish.
        """)
