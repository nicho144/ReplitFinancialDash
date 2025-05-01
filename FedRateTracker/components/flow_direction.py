import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from utils import determine_capital_flow

def render_flow_direction(data_service):
    """Render the Flow Direction Table"""
    st.header("Capital Flow Direction Dashboard")
    
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
        This dashboard analyzes capital flow direction across asset classes and sectors to determine whether markets are in 
        <span style="font-weight: bold; color: #4CAF50;">Risk-On</span> or 
        <span style="font-weight: bold; color: #F44336;">Risk-Off</span> mode.
    </div>
    """, unsafe_allow_html=True)
    
    # Get various data for flow analysis
    with st.spinner("Loading data for flow analysis..."):
        try:
            # Get Fed Funds data for real rates
            fed_funds_data = data_service.get_fed_funds_futures()
            
            # Get Treasury data for yield curve
            treasury_data = data_service.get_treasury_yields()
            
            # Get market breadth data
            market_breadth = data_service.get_market_breadth()
            
            # Get futures data for risk assessment
            futures_data = data_service.get_futures_fair_value()
            
            # Check if we have the necessary data
            if not all([fed_funds_data, treasury_data, market_breadth, futures_data]):
                st.error("Insufficient data for flow direction analysis. Check data connections.")
                return
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return
    
    # Extract key metrics for flow analysis
    try:
        # Extract real rate (use first contract)
        real_rate = None
        if fed_funds_data:
            for ticker, data in fed_funds_data.items():
                if 'real_rate' in data:
                    real_rate = data['real_rate']
                    break
        
        # Determine yield curve status
        yield_curve_status = "normal"
        if treasury_data:
            spread_2y_10y = treasury_data.get("2Y_10Y_spread")
            if spread_2y_10y is not None:
                if spread_2y_10y < 0:
                    yield_curve_status = "inverted"
                elif spread_2y_10y < 0.5:
                    yield_curve_status = "flat"
                else:
                    yield_curve_status = "steep"
        
        # Determine market breadth
        breadth_status = "neutral"
        if market_breadth:
            tick = market_breadth.get("TICK", {}).get("current") if isinstance(market_breadth.get("TICK"), dict) else None
            trin = market_breadth.get("TRIN")
            
            if tick is not None and trin is not None:
                if tick > 500 and trin < 0.8:
                    breadth_status = "positive"
                elif tick < -500 and trin > 1.2:
                    breadth_status = "negative"
        
        # Determine Fed posture based on real rates
        fed_posture = "neutral"
        if real_rate is not None:
            if real_rate > 1:
                fed_posture = "hawkish"
            elif real_rate < 0:
                fed_posture = "dovish"
    except Exception as e:
        st.error(f"Error extracting metrics: {e}")
        return
    
    # Create a table to display the inputs
    st.subheader("Flow Analysis Inputs")
    
    # Create input metrics display with visual indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        real_rate_text = f"{real_rate:.2f}%" if real_rate is not None else "N/A"
        real_rate_color = "#F44336" if real_rate is not None and real_rate < 0 else "#4CAF50" if real_rate is not None and real_rate > 1 else "#2196F3"
        real_rate_delta = "Risk-On Signal" if real_rate is not None and real_rate < 0 else "Risk-Off Signal" if real_rate is not None and real_rate > 1 else "Neutral"
        
        st.metric(
            "Real Interest Rate", 
            real_rate_text,
            delta=real_rate_delta,
            delta_color="normal" if real_rate is not None and real_rate < 0 else "inverse" if real_rate is not None and real_rate > 1 else "off"
        )
        
        # Add indicator explanation
        st.markdown(f"""
        <div style="background-color: {real_rate_color}15; padding: 5px; border-radius: 5px; font-size: 0.8em;">
            <span style="color: {real_rate_color}; font-weight: bold;">Impact:</span> {
            "Negative real rates support risk assets" if real_rate is not None and real_rate < 0 else 
            "Positive real rates pressure valuations" if real_rate is not None and real_rate > 1 else 
            "Neutral impact on markets"}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        yield_curve_icon = "📉" if yield_curve_status == "inverted" else "➖" if yield_curve_status == "flat" else "📈"
        yield_curve_color = "#F44336" if yield_curve_status == "inverted" else "#FF9800" if yield_curve_status == "flat" else "#4CAF50"
        yield_curve_delta = "Risk-Off Signal" if yield_curve_status == "inverted" else "Caution Signal" if yield_curve_status == "flat" else "Risk-On Signal"
        
        st.metric(
            f"{yield_curve_icon} Yield Curve", 
            yield_curve_status.title(),
            delta=yield_curve_delta,
            delta_color="inverse" if yield_curve_status == "inverted" else "off" if yield_curve_status == "flat" else "normal"
        )
        
        # Add indicator explanation
        st.markdown(f"""
        <div style="background-color: {yield_curve_color}15; padding: 5px; border-radius: 5px; font-size: 0.8em;">
            <span style="color: {yield_curve_color}; font-weight: bold;">Impact:</span> {
            "Recession risk rising, defensive positioning warranted" if yield_curve_status == "inverted" else 
            "Economic slowdown likely, monitor carefully" if yield_curve_status == "flat" else 
            "Healthy economic growth expected"}
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        breadth_icon = "🔝" if breadth_status == "positive" else "⬇️" if breadth_status == "negative" else "↔️"
        breadth_color = "#4CAF50" if breadth_status == "positive" else "#F44336" if breadth_status == "negative" else "#2196F3"
        breadth_delta = "Risk-On Signal" if breadth_status == "positive" else "Risk-Off Signal" if breadth_status == "negative" else "Neutral"
        
        st.metric(
            f"{breadth_icon} Market Breadth", 
            breadth_status.title(),
            delta=breadth_delta,
            delta_color="normal" if breadth_status == "positive" else "inverse" if breadth_status == "negative" else "off"
        )
        
        # Add indicator explanation
        st.markdown(f"""
        <div style="background-color: {breadth_color}15; padding: 5px; border-radius: 5px; font-size: 0.8em;">
            <span style="color: {breadth_color}; font-weight: bold;">Impact:</span> {
            "Strong market participation supports further upside" if breadth_status == "positive" else 
            "Deteriorating internals suggest caution" if breadth_status == "negative" else 
            "Mixed signals - watch for developing trends"}
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        fed_icon = "🕊️" if fed_posture == "dovish" else "🦅" if fed_posture == "hawkish" else "⚖️"
        fed_color = "#4CAF50" if fed_posture == "dovish" else "#F44336" if fed_posture == "hawkish" else "#2196F3"
        fed_delta = "Risk-On Signal" if fed_posture == "dovish" else "Risk-Off Signal" if fed_posture == "hawkish" else "Neutral"
        
        st.metric(
            f"{fed_icon} Fed Posture", 
            fed_posture.title(),
            delta=fed_delta,
            delta_color="normal" if fed_posture == "dovish" else "inverse" if fed_posture == "hawkish" else "off"
        )
        
        # Add indicator explanation
        st.markdown(f"""
        <div style="background-color: {fed_color}15; padding: 5px; border-radius: 5px; font-size: 0.8em;">
            <span style="color: {fed_color}; font-weight: bold;">Impact:</span> {
            "Accommodative policy supports asset prices" if fed_posture == "dovish" else 
            "Restrictive policy may pressure valuations" if fed_posture == "hawkish" else 
            "Policy balanced between growth and inflation concerns"}
        </div>
        """, unsafe_allow_html=True)
    
    # Generate flow direction analysis
    flow_analysis = determine_capital_flow(
        real_rate if real_rate is not None else 0,
        yield_curve_status,
        breadth_status,
        fed_posture
    )
    
    primary_flow = flow_analysis.get("primary_flow")
    secondary_flow = flow_analysis.get("secondary_flow")
    scores = flow_analysis.get("scores", {})
    
    # Display flow direction results
    st.subheader("Capital Flow Direction")
    
    # Create a bar chart of scores
    if scores:
        # Sort assets by score
        sorted_assets = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        assets = [item[0] for item in sorted_assets]
        score_values = [item[1] for item in sorted_assets]
        
        # Create color map
        colors = ['#2E8B57' if asset == primary_flow else 
                 '#6495ED' if asset == secondary_flow else 
                 '#A9A9A9' for asset in assets]
        
        # Create the bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=assets,
                y=score_values,
                marker_color=colors
            )
        ])
        
        fig.update_layout(
            title="Asset Flow Score (Higher = More Favorable)",
            xaxis_title="Asset Class",
            yaxis_title="Score",
            template="plotly_white",
            height=300,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Display flow direction conclusions
    if primary_flow and secondary_flow:
        # Primary flow box
        st.markdown(
            f"""
            <div style="background-color: #CCFFCC; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
                <h3 style="color: #006600; margin: 0;">PRIMARY FLOW: {primary_flow.upper()}</h3>
                <p>Based on current market conditions, capital is most likely to flow toward {primary_flow.lower()}.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Secondary flow box
        st.markdown(
            f"""
            <div style="background-color: #CCCCFF; padding: 15px; border-radius: 5px;">
                <h3 style="color: #000066; margin: 0;">SECONDARY FLOW: {secondary_flow.upper()}</h3>
                <p>Secondary capital flows are likely to favor {secondary_flow.lower()}.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Generate specific trading implications
    st.subheader("Trading Implications")
    
    implications = []
    
    if primary_flow == "Gold":
        implications.append("• Consider long positions in gold, gold miners (GDX, GDXJ), or gold royalty companies")
        implications.append("• Watch for supporting moves in silver and other precious metals")
        implications.append("• Dollar weakness may accompany gold strength")
    elif primary_flow == "Bonds":
        implications.append("• Treasury yields likely to decline (prices rise)")
        implications.append("• Consider TLT, IEF for bond exposure")
        implications.append("• Rate-sensitive equities may outperform (utilities, REITs)")
        implications.append("• Watch for economic growth concerns driving the bond rally")
    elif primary_flow == "Equities":
        implications.append("• Risk-on environment favors equities over safe havens")
        implications.append("• Growth stocks and cyclicals likely to outperform defensive sectors")
        implications.append("• Watch for confirming signs in credit spreads and small caps")
        implications.append("• Consider higher equity allocation or reduced hedging")
    
    # Add implications for secondary flow
    if secondary_flow == "Gold" and primary_flow != "Gold":
        implications.append("• Gold may serve as an effective portfolio hedge")
    elif secondary_flow == "Bonds" and primary_flow != "Bonds":
        implications.append("• Consider barbell approach with both risk assets and bond exposure")
    elif secondary_flow == "Equities" and primary_flow != "Equities":
        implications.append("• Selective equity exposure still warranted despite primary flows elsewhere")
    
    # Add specific cross-asset implications
    if primary_flow == "Gold" and secondary_flow == "Bonds":
        implications.append("• Classic risk-off environment – consider reducing equity exposure")
        implications.append("• Dollar likely to weaken in this scenario")
    elif primary_flow == "Equities" and secondary_flow == "Gold":
        implications.append("• Inflationary growth scenario – commodities broadly may perform well")
    
    # Display implications
    for implication in implications:
        st.markdown(implication)
    
    # Explanation section
    with st.expander("About Flow Direction Analysis"):
        st.markdown("""
        **Flow Direction Analysis Methodology**
        
        This analysis uses a scoring system to determine the likely direction of capital flows among major asset classes based on four key factors:
        
        **1. Real Rates:**
        - Negative real rates typically favor gold and equities
        - Positive real rates typically favor bonds (especially when rising)
        
        **2. Yield Curve Positioning:**
        - Inverted curves often signal recession risk, favoring bonds and gold
        - Steep curves typically suggest economic growth, favoring equities
        
        **3. Market Breadth:**
        - Positive breadth favors equities
        - Negative breadth favors defensive assets like bonds and gold
        
        **4. Fed Posture:**
        - Dovish Fed typically supports gold and equities
        - Hawkish Fed typically pressures valuations but can support bonds long-term
        
        The system assigns points to each asset class based on these factors, then ranks them to determine primary and secondary flow directions. This helps identify which assets are most likely to attract capital in the current environment.
        
        This analysis should be combined with traditional fundamental and technical analysis for best results.
        """)
