import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from plotly.subplots import make_subplots
import numpy as np
from utils import interpret_yield_curve, color_by_value, format_percentage

def render_treasury_spreads(data_service):
    """Render the Treasury Curve Spread Monitoring component"""
    st.header("2. Treasury Yield Curve Analysis")
    
    with st.spinner("Loading Treasury yield data..."):
        # Get Treasury Yield data
        treasury_data = data_service.get_treasury_yields()
        
        if not treasury_data:
            st.error("Unable to fetch Treasury yield data. Please check API connections.")
            return
    
    # Create columns for key spreads
    col1, col2 = st.columns(2)
    
    # 2Y-10Y Spread
    with col1:
        # Make sure we get the data by trying different key formats used in the data
        spread_2y_10y = None
        for key in ["2Y_10Y_spread", "spread_2y_10y", "2Y-10Y"]:
            if key in treasury_data.get('current', {}):
                spread_2y_10y = treasury_data['current'][key]
                break
            
        # If we still can't find the spread directly, calculate it
        if spread_2y_10y is None:
            # Try to get yields using different key formats
            yield_2y = None
            for key in ["2Y", "2Y_yield", "yield_2y"]:
                if key in treasury_data.get('current', {}):
                    yield_2y = treasury_data['current'][key]
                    break
                    
            yield_10y = None
            for key in ["10Y", "10Y_yield", "yield_10y"]:
                if key in treasury_data.get('current', {}):
                    yield_10y = treasury_data['current'][key]
                    break
                    
            # Calculate the spread if we have both yields
            if yield_2y is not None and yield_10y is not None:
                spread_2y_10y = yield_10y - yield_2y
        else:
            # If we found the spread directly, still try to get individual yields for display
            yield_2y = None
            for key in ["2Y", "2Y_yield", "yield_2y"]:
                if key in treasury_data.get('current', {}):
                    yield_2y = treasury_data['current'][key]
                    break
                    
            yield_10y = None
            for key in ["10Y", "10Y_yield", "yield_10y"]:
                if key in treasury_data.get('current', {}):
                    yield_10y = treasury_data['current'][key]
                    break
        
        # Calculate change from previous day for spread and individual yields
        spread_change_2y_10y = None
        yield_2y_change = None
        yield_10y_change = None
        
        try:
            # Get yesterday's data from database
            yesterday = datetime.now() - timedelta(days=1)
            historical_treasury = data_service.db.get_treasury_yield_data(yesterday, datetime.now())
            
            if historical_treasury and len(historical_treasury) >= 2:
                # Get the most recent spread before today
                today_ts = pd.to_datetime(datetime.now().date())
                prev_data = [item for item in historical_treasury 
                            if pd.to_datetime(item["timestamp"]).date() < today_ts.date()]
                
                if prev_data:
                    # Sort by timestamp in descending order and get the most recent
                    prev_data.sort(key=lambda x: x["timestamp"], reverse=True)
                    prev_spread = prev_data[0]["spread_2y_10y"]
                    prev_2y = prev_data[0]["yield_2y"]
                    prev_10y = prev_data[0]["yield_10y"]
                    
                    if prev_spread is not None and spread_2y_10y is not None:
                        spread_change_2y_10y = spread_2y_10y - prev_spread
                    
                    if prev_2y is not None and yield_2y is not None:
                        yield_2y_change = yield_2y - prev_2y
                        
                    if prev_10y is not None and yield_10y is not None:
                        yield_10y_change = yield_10y - prev_10y
        except Exception as e:
            print(f"Error calculating spread change: {e}")
        
        # Enhanced display with more information
        if spread_2y_10y is not None:
            # Create a card-like container for 2Y-10Y info
            st.markdown("""
            <style>
            .spread-card {
                background-color: #f9f9f9;
                border-radius: 10px;
                padding: 15px;
                border-left: 5px solid #3366ff;
                margin-bottom: 10px;
            }
            .yield-detail {
                font-size: 0.9em;
                color: #555;
                margin-top: 5px;
            }
            .up-change {
                color: #28a745;
                font-weight: bold;
            }
            .down-change {
                color: #dc3545;
                font-weight: bold;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Main metric display
            status_color = "#dc3545" if spread_2y_10y < 0 else "#fd7e14" if spread_2y_10y < 0.5 else "#28a745"
            
            st.markdown(f"""
            <div class="spread-card">
                <h3 style="margin-top:0; color: {status_color};">2Y-10Y Spread: {spread_2y_10y:.2f}%</h3>
                <p>Daily Change: <span class="{'up-change' if spread_change_2y_10y is not None and spread_change_2y_10y > 0 else 'down-change'}">
                    {f"{spread_change_2y_10y:+.3f}%" if spread_change_2y_10y is not None else "N/A"}
                </span></p>
                
                <div class="yield-detail">
                    <p>2Y Yield: {yield_2y:.2f}% 
                        <span class="{'up-change' if yield_2y_change is not None and yield_2y_change > 0 else 'down-change'}">
                            {f"{yield_2y_change:+.3f}%" if yield_2y_change is not None else ""}
                        </span>
                    </p>
                    <p>10Y Yield: {yield_10y:.2f}% 
                        <span class="{'up-change' if yield_10y_change is not None and yield_10y_change > 0 else 'down-change'}">
                            {f"{yield_10y_change:+.3f}%" if yield_10y_change is not None else ""}
                        </span>
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show inversion warning if applicable
            if spread_2y_10y < 0:
                st.warning("⚠️ Yield curve is inverted - potential recession signal")
            elif spread_2y_10y < 0.5:
                st.info("ℹ️ Yield curve is relatively flat")
                
            # Add interpretation of daily change
            if spread_change_2y_10y is not None:
                if spread_change_2y_10y < -0.05:
                    st.markdown("🔴 **Significant flattening/inversion** since yesterday")
                elif spread_change_2y_10y > 0.05:
                    st.markdown("🟢 **Significant steepening** since yesterday")
                elif spread_change_2y_10y < 0:
                    st.markdown("⚠️ **Slight flattening** since yesterday")
                elif spread_change_2y_10y > 0:
                    st.markdown("✅ **Slight steepening** since yesterday")
    
    # 2Y-5Y Spread
    with col2:
        # Make sure we get the data by trying different key formats used in the data
        spread_2y_5y = None
        for key in ["2Y_5Y_spread", "spread_2y_5y", "2Y-5Y"]:
            if key in treasury_data.get('current', {}):
                spread_2y_5y = treasury_data['current'][key]
                break
            
        # If we still can't find the spread directly, calculate it
        if spread_2y_5y is None:
            # Try to get yields using different key formats
            yield_2y = None
            for key in ["2Y", "2Y_yield", "yield_2y"]:
                if key in treasury_data.get('current', {}):
                    yield_2y = treasury_data['current'][key]
                    break
                    
            yield_5y = None
            for key in ["5Y", "5Y_yield", "yield_5y"]:
                if key in treasury_data.get('current', {}):
                    yield_5y = treasury_data['current'][key]
                    break
                    
            # Calculate the spread if we have both yields
            if yield_2y is not None and yield_5y is not None:
                spread_2y_5y = yield_5y - yield_2y
        else:
            # If we found the spread directly, still try to get individual yields for display
            yield_2y = None
            for key in ["2Y", "2Y_yield", "yield_2y"]:
                if key in treasury_data.get('current', {}):
                    yield_2y = treasury_data['current'][key]
                    break
                    
            yield_5y = None
            for key in ["5Y", "5Y_yield", "yield_5y"]:
                if key in treasury_data.get('current', {}):
                    yield_5y = treasury_data['current'][key]
                    break
        
        # Calculate change from previous day for spread and individual yields
        spread_change_2y_5y = None
        yield_2y_change = None
        yield_5y_change = None
        
        try:
            # Get yesterday's data from database
            yesterday = datetime.now() - timedelta(days=1)
            historical_treasury = data_service.db.get_treasury_yield_data(yesterday, datetime.now())
            
            if historical_treasury and len(historical_treasury) >= 2:
                # Get the most recent spread before today
                today_ts = pd.to_datetime(datetime.now().date())
                prev_data = [item for item in historical_treasury 
                            if pd.to_datetime(item["timestamp"]).date() < today_ts.date()]
                
                if prev_data:
                    # Sort by timestamp in descending order and get the most recent
                    prev_data.sort(key=lambda x: x["timestamp"], reverse=True)
                    prev_spread = prev_data[0]["spread_2y_5y"]
                    prev_2y = prev_data[0]["yield_2y"]
                    prev_5y = prev_data[0]["yield_5y"]
                    
                    if prev_spread is not None and spread_2y_5y is not None:
                        spread_change_2y_5y = spread_2y_5y - prev_spread
                    
                    if prev_2y is not None and yield_2y is not None:
                        yield_2y_change = yield_2y - prev_2y
                        
                    if prev_5y is not None and yield_5y is not None:
                        yield_5y_change = yield_5y - prev_5y
        except Exception as e:
            print(f"Error calculating 2Y-5Y spread change: {e}")
        
        # Enhanced display with more information
        if spread_2y_5y is not None:
            # Main metric display
            status_color = "#dc3545" if spread_2y_5y < 0 else "#fd7e14" if spread_2y_5y < 0.25 else "#28a745"
            
            st.markdown(f"""
            <div class="spread-card" style="border-left: 5px solid #9467bd;">
                <h3 style="margin-top:0; color: {status_color};">2Y-5Y Spread: {spread_2y_5y:.2f}%</h3>
                <p>Daily Change: <span class="{'up-change' if spread_change_2y_5y is not None and spread_change_2y_5y > 0 else 'down-change'}">
                    {f"{spread_change_2y_5y:+.3f}%" if spread_change_2y_5y is not None else "N/A"}
                </span></p>
                
                <div class="yield-detail">
                    <p>2Y Yield: {yield_2y:.2f}% 
                        <span class="{'up-change' if yield_2y_change is not None and yield_2y_change > 0 else 'down-change'}">
                            {f"{yield_2y_change:+.3f}%" if yield_2y_change is not None else ""}
                        </span>
                    </p>
                    <p>5Y Yield: {yield_5y:.2f}% 
                        <span class="{'up-change' if yield_5y_change is not None and yield_5y_change > 0 else 'down-change'}">
                            {f"{yield_5y_change:+.3f}%" if yield_5y_change is not None else ""}
                        </span>
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show inversion warning if applicable
            if spread_2y_5y < 0:
                st.warning("⚠️ Front-end inversion - economic stress signal")
            elif spread_2y_5y < 0.25:
                st.info("ℹ️ Front-end flattening - potential policy shift ahead")
                
            # Add interpretation of daily change
            if spread_change_2y_5y is not None:
                if spread_change_2y_5y < -0.05:
                    st.markdown("🔴 **Significant front-end flattening** since yesterday")
                elif spread_change_2y_5y > 0.05:
                    st.markdown("🟢 **Significant front-end steepening** since yesterday")
                elif spread_change_2y_5y < 0:
                    st.markdown("⚠️ **Slight front-end flattening** since yesterday")
                elif spread_change_2y_5y > 0:
                    st.markdown("✅ **Slight front-end steepening** since yesterday")
    
    # Yield values display - Improved visual presentation
    st.subheader("Current Treasury Yields & Curve")
    
    # Create a visual yield curve
    maturities = [("2Y", "2-Year"), ("5Y", "5-Year"), ("10Y", "10-Year"), ("30Y", "30-Year")]
    maturities_values = [2, 5, 10, 30]  # Actual year values for x-axis
    
    # Get yield values in order
    current_yields = []
    for key, _ in maturities:
        # Try to find the value using multiple possible key formats
        value = None
        key_formats = [key, f"{key}_yield", f"yield_{key.lower()}"]
        
        for key_format in key_formats:
            # Try in treasury_data directly
            if key_format in treasury_data:
                value = treasury_data[key_format]
                break
            # Try in treasury_data['current']
            elif 'current' in treasury_data and key_format in treasury_data['current']:
                value = treasury_data['current'][key_format]
                break
        
        # Default to 0 if not found (will be visible in the chart)
        current_yields.append(value if value is not None else 0)
        # Store yield values silently, no debug printing needed
    
    # Create yield curve plot
    fig_curve = go.Figure()
    
    # Current yield curve
    fig_curve.add_trace(
        go.Scatter(
            x=maturities_values,
            y=current_yields,
            mode='lines+markers',
            name='Current Yields',
            line=dict(color='blue', width=3),
            marker=dict(size=10, color='blue')
        )
    )
    
    # Get previous yield data for comparison if available
    prev_yields = {}
    prev_yield_values = []
    try:
        yesterday = datetime.now() - timedelta(days=1)
        historical_treasury = data_service.db.get_treasury_yield_data(yesterday, datetime.now())
        
        if historical_treasury:
            # Get the most recent yields before today
            today_ts = pd.to_datetime(datetime.now().date())
            prev_data = [item for item in historical_treasury 
                       if pd.to_datetime(item["timestamp"]).date() < today_ts.date()]
            
            if prev_data:
                # Sort by timestamp in descending order and get the most recent
                prev_data.sort(key=lambda x: x["timestamp"], reverse=True)
                prev_yields = {
                    "2Y": prev_data[0]["yield_2y"],
                    "5Y": prev_data[0]["yield_5y"],
                    "10Y": prev_data[0]["yield_10y"],
                    "30Y": prev_data[0]["yield_30y"]
                }
                
                # Previous yield curve values
                for key, _ in maturities:
                    prev_value = prev_yields.get(key)
                    prev_yield_values.append(prev_value if prev_value is not None else 0)
                
                # Add previous yield curve for comparison
                fig_curve.add_trace(
                    go.Scatter(
                        x=maturities_values,
                        y=prev_yield_values,
                        mode='lines+markers',
                        name='Previous Day',
                        line=dict(color='gray', width=2, dash='dash'),
                        marker=dict(size=8, color='gray')
                    )
                )
    except Exception as e:
        print(f"Error fetching previous yield data: {e}")
    
    # Update layout for yield curve
    fig_curve.update_layout(
        title="Treasury Yield Curve",
        xaxis_title="Maturity (Years)",
        yaxis_title="Yield (%)",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=300,
        margin=dict(l=10, r=10, t=50, b=30),
        xaxis=dict(
            tickmode='array',
            tickvals=maturities_values,
            ticktext=[label for _, label in maturities]
        )
    )
    
    # Add horizontal guides for reference
    for i in range(1, 6):
        fig_curve.add_hline(y=i, line_width=0.5, line_dash="dot", line_color="lightgray")
    
    # Display the yield curve
    st.plotly_chart(fig_curve, use_container_width=True)
    
    # Display metrics in a cleaner layout with more context
    cols = st.columns(4)
    
    # Add yield values with improved presentation
    for i, (key, label) in enumerate(maturities):
        with cols[i]:
            # Try to find the value using multiple possible key formats
            value = None
            key_formats = [key, f"{key}_yield", f"yield_{key.lower()}"]
            
            for key_format in key_formats:
                # Try in treasury_data directly
                if key_format in treasury_data:
                    value = treasury_data[key_format]
                    break
                # Try in treasury_data['current']
                elif 'current' in treasury_data and key_format in treasury_data['current']:
                    value = treasury_data['current'][key_format]
                    break
            
            if value is not None:
                # Calculate daily change if we have previous data
                daily_change = None
                if key in prev_yields and prev_yields[key] is not None:
                    daily_change = value - prev_yields[key]
                
                st.metric(
                    label, 
                    f"{value:.2f}%", 
                    delta=f"{daily_change:.3f}%" if daily_change is not None else None,
                    delta_color="inverse" if daily_change is not None and daily_change < 0 else "normal"
                )
                
                # Add colored background for significant values
                if daily_change is not None:
                    bg_color = "transparent"
                    text_color = "black"
                    move_text = ""
                    
                    if abs(daily_change) >= 0.1:
                        bg_color = "#ffcccb" if daily_change > 0 else "#ceffcc"
                        text_color = "#880000" if daily_change > 0 else "#008800"
                        move_type = "increase" if daily_change > 0 else "decrease"
                        move_text = f"Large {move_type}"
                    elif abs(daily_change) >= 0.05:
                        bg_color = "#ffe6e6" if daily_change > 0 else "#e6ffe6"
                        text_color = "#aa5555" if daily_change > 0 else "#55aa55"
                        move_type = "increase" if daily_change > 0 else "decrease"
                        move_text = f"Notable {move_type}"
                    
                    if move_text:
                        st.markdown(
                            f"""<div style="background-color:{bg_color}; color:{text_color}; 
                            padding:4px; border-radius:5px; text-align:center; margin-top:5px;">
                            {move_text}
                            </div>""", 
                            unsafe_allow_html=True
                        )
            else:
                st.metric(label, "N/A", delta=None)
    
    # Historical spread chart - Enhanced visualizations
    st.subheader("Historical Yield Spreads")
    
    # Get data from database (last 90 days) - shared between both charts
    try:
        start_date = datetime.now() - timedelta(days=90)
        historical_treasury = data_service.db.get_treasury_yield_data(start_date, datetime.now())
    except Exception as e:
        st.error(f"Error fetching historical treasury data: {e}")
        historical_treasury = []
    
    # Create tabs for different spread combinations
    tab1, tab2, tab3 = st.tabs(["2Y-10Y Spread", "2Y-5Y Spread", "Full Yield Curve History"])
    
    with tab1:
        try:
            if historical_treasury:
                # Create spread visualization in a more understandable format
                # Using a split visualization to highlight spread vs. absolute values
                
                # Filter out any records with None values in critical fields
                valid_data = []
                for item in historical_treasury:
                    if (item["yield_2y"] is not None and 
                        item["yield_10y"] is not None and 
                        item["spread_2y_10y"] is not None):
                        valid_data.append(item)
                
                if not valid_data:
                    st.info("Not enough valid data points available for the chart yet. Data will appear as it's collected.")
                    return
                
                # Create two subplot figures: one for yields and one for spread
                fig = make_subplots(
                    rows=2, cols=1, 
                    shared_xaxes=True,
                    vertical_spacing=0.08,
                    row_heights=[0.7, 0.3],
                    subplot_titles=("2Y and 10Y Yields", "2Y-10Y Spread (Recession Indicator)")
                )
                
                # Format timestamps and sort data chronologically
                timestamps = [pd.to_datetime(item["timestamp"]) for item in valid_data]
                yield_2y = [item["yield_2y"] for item in valid_data]
                yield_10y = [item["yield_10y"] for item in valid_data]
                spread_2y_10y = [item["spread_2y_10y"] for item in valid_data]
                
                # Add 2Y yield trace to top plot
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=yield_2y,
                        mode='lines',
                        name='2Y Yield',
                        line=dict(color='#1f77b4', width=2)
                    ),
                    row=1, col=1
                )
                
                # Add 10Y yield trace to top plot
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=yield_10y,
                        mode='lines',
                        name='10Y Yield',
                        line=dict(color='#d62728', width=2)
                    ),
                    row=1, col=1
                )
                
                # Add spread to bottom plot with color shading
                # Create fill color to highlight inversion
                pos_spreads = []
                neg_spreads = []
                for spread in spread_2y_10y:
                    if spread is not None and spread >= 0:
                        pos_spreads.append(spread)
                        neg_spreads.append(None)
                    elif spread is not None:
                        pos_spreads.append(None)
                        neg_spreads.append(spread)
                    else:
                        # Handle None values
                        pos_spreads.append(None)
                        neg_spreads.append(None)
                        
                # Add positive spread area (normal)
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=pos_spreads,
                        mode='lines',
                        name='Normal Curve',
                        line=dict(color='green', width=0),
                        fill='tozeroy',
                        fillcolor='rgba(0, 176, 80, 0.2)'
                    ),
                    row=2, col=1
                )
                
                # Add negative spread area (inverted - recession signal)
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=neg_spreads,
                        mode='lines',
                        name='Inverted Curve',
                        line=dict(color='red', width=0),
                        fill='tozeroy',
                        fillcolor='rgba(255, 80, 80, 0.3)'
                    ),
                    row=2, col=1
                )
                
                # Add spread line
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=spread_2y_10y,
                        mode='lines',
                        name='2Y-10Y Spread',
                        line=dict(color='black', width=1.5)
                    ),
                    row=2, col=1
                )
                
                # Add zero reference line to bottom plot
                fig.add_hline(
                    y=0, 
                    line_width=1.5, 
                    line_dash="dash", 
                    line_color="gray",
                    row=2, col=1,
                    annotation_text="Inversion Threshold",
                    annotation_position="bottom right"
                )
                
                # Add recession probability zones to bottom plot
                fig.add_hrect(
                    y0=-0.5, y1=0, 
                    fillcolor="rgba(255, 0, 0, 0.1)", 
                    line_width=0, 
                    row=2, col=1,
                    annotation_text="High Recession Risk",
                    annotation_position="bottom left"
                )
                
                # Update layout with improved styling
                fig.update_layout(
                    template="plotly_white",
                    height=550,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=10, r=10, t=60, b=10)
                )
                
                # Update axes labels and styles
                fig.update_yaxes(title_text="Yield (%)", row=1, col=1, gridcolor='rgba(0,0,0,0.1)')
                fig.update_yaxes(title_text="Spread (%)", row=2, col=1, gridcolor='rgba(0,0,0,0.1)')
                fig.update_xaxes(title_text="", row=1, col=1, showgrid=False)
                fig.update_xaxes(title_text="Date", row=2, col=1, gridcolor='rgba(0,0,0,0.1)')
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add interpretation with visually distinct explanation
                if len(historical_treasury) >= 2 and spread_2y_10y[-1] is not None and spread_2y_10y[-2] is not None:
                    spread_change = spread_2y_10y[-1] - spread_2y_10y[-2]
                    interpretation = interpret_yield_curve(spread_2y_10y[-1], spread_change)
                    
                    latest_spread = spread_2y_10y[-1]
                    
                    # Create a visually informative block with curve status
                    status_color = "red" if latest_spread < 0 else "orange" if latest_spread < 0.5 else "green"
                    status_text = "INVERTED" if latest_spread < 0 else "FLAT" if latest_spread < 0.5 else "NORMAL"
                    
                    # Determine if yield curve is risk-on or risk-off
                    risk_status = "RISK-OFF"
                    risk_color = "#dc3545"
                    risk_explanation = "Inverted yield curve typically signals economic caution."
                    recommendation_text = "Consider defensive positioning with increased allocation to short-term Treasuries and reduced equity exposure."
                    
                    if latest_spread >= 0.5:
                        risk_status = "RISK-ON"
                        risk_color = "#28a745"
                        risk_explanation = "Normal yield curve suggests economic growth ahead."
                        recommendation_text = "Consider increasing allocation to SPY and growth stocks while reducing Treasury exposure."
                    elif latest_spread >= 0:
                        risk_status = "NEUTRAL"
                        risk_color = "#fd7e14"
                        risk_explanation = "Flat yield curve suggests economic uncertainty."
                        recommendation_text = "Maintain balanced portfolio with both growth and defensive assets."
                        
                    # Determine curve description based on trend
                    curve_description = "stable"
                    if spread_change > 0.05:
                        curve_description = "steepening (yields spreading apart)"
                    elif spread_change < -0.05:
                        curve_description = "flattening/inverting (yields converging)"
                        
                    # Create text for bullish/bearish for gold
                    gold_impact_text = '✅ Current yield curve positioning is typically bullish for gold' if interpretation["bullish_for_gold"] else '❌ Current yield curve positioning is typically not bullish for gold'
                    
                    # Create main container background and border styles
                    main_bg_color = f"background-color: {status_color}20"
                    main_border = f"border-left: 5px solid {status_color}"
                    main_title_color = f"color: {status_color}"
                    
                    # Create risk signal background and text styles
                    risk_bg_color = f"background-color: {risk_color}20"
                    risk_title_color = f"color: {risk_color}"
                    
                    # Display the interpretation directly with Streamlit elements
                    # Instead of using raw HTML, use Streamlit's native components
                    
                    with st.container():
                        # Use a custom style for the container
                        st.markdown(f"""
                        <div style="{main_bg_color}; padding: 15px; border-radius: 5px; {main_border};">
                            <h4 style="{main_title_color}; margin-top: 0;">Yield Curve Status: {status_text}</h4>
                            <p>{interpretation["message"]}</p>
                            <p>{gold_impact_text}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Create a separate container for the risk signal
                        st.markdown(f"""
                        <div style="margin-top: 15px; padding: 10px; {risk_bg_color}; border-radius: 5px;">
                            <h4 style="{risk_title_color}; margin-top: 0;">SIGNAL: {risk_status}</h4>
                            <p>The yield curve is currently <b>{curve_description}</b>. {risk_explanation}</p>
                            <p><b>Recommendation:</b> {recommendation_text}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No historical data available yet. Data will appear as it's collected.")
        except Exception as e:
            st.error(f"Error creating 2Y-10Y spread chart: {e}")
    
    with tab2:
        try:
            if historical_treasury:
                # Create a similar visualization approach for 2Y-5Y spread
                
                # Filter out any records with None values in critical fields
                valid_data = []
                for item in historical_treasury:
                    if (item["yield_2y"] is not None and 
                        item["yield_5y"] is not None and 
                        item["spread_2y_5y"] is not None):
                        valid_data.append(item)
                
                if not valid_data:
                    st.info("Not enough valid data points available for the chart yet. Data will appear as it's collected.")
                    return
                
                fig = make_subplots(
                    rows=2, cols=1, 
                    shared_xaxes=True,
                    vertical_spacing=0.08,
                    row_heights=[0.7, 0.3],
                    subplot_titles=("2Y and 5Y Yields", "2Y-5Y Spread (Front-End Indicator)")
                )
                
                timestamps = [pd.to_datetime(item["timestamp"]) for item in valid_data]
                yield_2y = [item["yield_2y"] for item in valid_data]
                yield_5y = [item["yield_5y"] for item in valid_data]
                spread_2y_5y = [item["spread_2y_5y"] for item in valid_data]
                
                # Add 2Y yield trace to top plot
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=yield_2y,
                        mode='lines',
                        name='2Y Yield',
                        line=dict(color='#1f77b4', width=2)
                    ),
                    row=1, col=1
                )
                
                # Add 5Y yield trace to top plot
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=yield_5y,
                        mode='lines',
                        name='5Y Yield',
                        line=dict(color='#9467bd', width=2)
                    ),
                    row=1, col=1
                )
                
                # Create fill color to highlight inversion for spread
                pos_spreads = []
                neg_spreads = []
                for spread in spread_2y_5y:
                    if spread is not None and spread >= 0:
                        pos_spreads.append(spread)
                        neg_spreads.append(None)
                    elif spread is not None:
                        pos_spreads.append(None)
                        neg_spreads.append(spread)
                    else:
                        # Handle None values
                        pos_spreads.append(None)
                        neg_spreads.append(None)
                        
                # Add positive spread area (normal)
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=pos_spreads,
                        mode='lines',
                        name='Normal Front-End',
                        line=dict(color='green', width=0),
                        fill='tozeroy',
                        fillcolor='rgba(0, 176, 80, 0.2)'
                    ),
                    row=2, col=1
                )
                
                # Add negative spread area (inverted - stress signal)
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=neg_spreads,
                        mode='lines',
                        name='Inverted Front-End',
                        line=dict(color='red', width=0),
                        fill='tozeroy',
                        fillcolor='rgba(255, 80, 80, 0.3)'
                    ),
                    row=2, col=1
                )
                
                # Add spread line
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=spread_2y_5y,
                        mode='lines',
                        name='2Y-5Y Spread',
                        line=dict(color='black', width=1.5)
                    ),
                    row=2, col=1
                )
                
                # Add zero reference line
                fig.add_hline(
                    y=0, 
                    line_width=1.5, 
                    line_dash="dash", 
                    line_color="gray",
                    row=2, col=1,
                    annotation_text="Inversion Threshold",
                    annotation_position="bottom right"
                )
                
                # Update layout
                fig.update_layout(
                    template="plotly_white",
                    height=550,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=10, r=10, t=60, b=10)
                )
                
                # Update axes labels
                fig.update_yaxes(title_text="Yield (%)", row=1, col=1, gridcolor='rgba(0,0,0,0.1)')
                fig.update_yaxes(title_text="Spread (%)", row=2, col=1, gridcolor='rgba(0,0,0,0.1)')
                fig.update_xaxes(title_text="", row=1, col=1, showgrid=False)
                fig.update_xaxes(title_text="Date", row=2, col=1, gridcolor='rgba(0,0,0,0.1)')
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add front-end interpretation
                latest_spread = spread_2y_5y[-1] if spread_2y_5y and spread_2y_5y[-1] is not None else 0
                spread_change = spread_2y_5y[-1] - spread_2y_5y[-2] if len(spread_2y_5y) >= 2 and spread_2y_5y[-1] is not None and spread_2y_5y[-2] is not None else 0
                
                status_color = "red" if latest_spread < 0 else "orange" if latest_spread < 0.25 else "green"
                status_text = "INVERTED" if latest_spread < 0 else "FLATTENING" if latest_spread < 0.25 else "NORMAL"
                
                message = ""
                if latest_spread < 0:
                    message = "The front-end of the yield curve is inverted, suggesting significant economic stress and potential aggressive Fed rate cuts ahead."
                elif latest_spread < 0.25:
                    message = "The front-end of the yield curve is flattening, indicating potential policy shifts ahead as markets anticipate Fed action."
                else:
                    message = "The front-end of the yield curve shows a healthy spread, suggesting markets expect stable or increasing rates ahead."
                
                # Determine spread direction text
                spread_direction_text = '📈 Front-end spread steepening' if spread_change > 0 else '📉 Front-end spread flattening'
                spread_change_text = f"{abs(spread_change):.3f}% change since previous measurement"
                
                # Create styles
                bg_color = f"background-color: {status_color}20"
                border_left = f"border-left: 5px solid {status_color}"
                title_color = f"color: {status_color}"
                
                # Use a container with Streamlit's native components
                with st.container():
                    # Apply custom styling with markdown
                    st.markdown(f"""
                    <div style="{bg_color}; padding: 15px; border-radius: 5px; {border_left};">
                        <h4 style="{title_color}; margin-top: 0;">Front-End Status: {status_text}</h4>
                        <p>{message}</p>
                        <p>{spread_direction_text}: {spread_change_text}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No historical data available yet. Data will appear as it's collected.")
        except Exception as e:
            st.error(f"Error creating 2Y-5Y spread chart: {e}")
            
    with tab3:
        try:
            if historical_treasury:
                # Time series of full yield curve evolution
                # Create animation-style visualization showing yield curve changes over time
                
                # Get weekly data points for clearer visualization
                all_dates = sorted(set([pd.to_datetime(item["timestamp"]).date() for item in historical_treasury]))
                
                # Sample dates to avoid overcrowding (approximately weekly)
                sampled_dates = []
                last_week = -1
                for date in all_dates:
                    week = date.isocalendar()[1]  # Get ISO week number
                    if week != last_week:
                        sampled_dates.append(date)
                        last_week = week
                
                # Create a 3D visualization of yield curve evolving over time
                fig = go.Figure()
                
                # Get yield curve for each sampled date
                for date in sampled_dates[-8:]:  # Show last 8 weeks for clarity
                    # Filter data for this date
                    date_data = [item for item in historical_treasury 
                                if pd.to_datetime(item["timestamp"]).date() == date]
                    
                    if date_data:
                        # Use most recent data point for that date
                        date_data.sort(key=lambda x: x["timestamp"], reverse=True)
                        data_point = date_data[0]
                        
                        # Get yield values
                        y_values = [
                            data_point["yield_2y"] if data_point["yield_2y"] is not None else 0,
                            data_point["yield_5y"] if data_point["yield_5y"] is not None else 0,
                            data_point["yield_10y"] if data_point["yield_10y"] is not None else 0,
                            data_point["yield_30y"] if data_point["yield_30y"] is not None else 0
                        ]
                        
                        # Normalize date for color gradient (newer dates are darker)
                        date_normalize = (date - min(sampled_dates)).days / max(1, (max(sampled_dates) - min(sampled_dates)).days)
                        color_intensity = int(date_normalize * 200)
                        
                        # Add line for this date's yield curve
                        fig.add_trace(
                            go.Scatter(
                                x=maturities_values,
                                y=y_values,
                                mode='lines+markers',
                                name=date.strftime('%Y-%m-%d'),
                                line=dict(
                                    width=2 + date_normalize * 3,  # Wider line for newer dates
                                    color=f'rgba({color_intensity}, {50 + color_intensity}, 255, {0.3 + 0.7 * date_normalize})'
                                ),
                                marker=dict(size=6 + date_normalize * 4)
                            )
                        )
                
                fig.update_layout(
                    title="Yield Curve Evolution (Recent Weeks)",
                    xaxis_title="Maturity (Years)",
                    yaxis_title="Yield (%)",
                    template="plotly_white",
                    height=450,
                    margin=dict(l=10, r=10, t=50, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(
                        tickmode='array',
                        tickvals=maturities_values,
                        ticktext=[label for _, label in maturities]
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add explanation of what this visualization shows
                st.markdown("""
                <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; border-left: 5px solid #1e90ff;">
                    <h4 style="color: #1e90ff; margin-top: 0;">About Yield Curve Evolution</h4>
                    <p>This visualization shows how the yield curve shape has changed over recent weeks. 
                    Darker/thicker lines represent more recent dates.</p>
                    <p>Watch for:</p>
                    <ul>
                        <li><strong>Flattening curves:</strong> When long and short rates converge</li>
                        <li><strong>Steepening curves:</strong> When the spread between long and short rates increases</li>
                        <li><strong>Inversions:</strong> When short-term yields exceed long-term yields</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No historical data available yet. Data will appear as it's collected.")
        except Exception as e:
            st.error(f"Error creating yield curve evolution chart: {e}")
    
    # Treasury Curve explanation - Enhanced with visual educational elements
    with st.expander("Understanding Treasury Yields & Market Implications"):
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("""
            ## Treasury Yield Curve: Market's Crystal Ball
            
            The Treasury yield curve plots interest rates across different maturities, revealing market expectations about future economic conditions and Federal Reserve policy.
            
            ### Key Curve Shapes
            
            **Normal Curve (Positive Spread)** 📈
            - Longer-term bonds have higher yields than shorter-term bonds
            - Indicates expectations of economic growth and/or inflation
            - Usually present in healthy economic environments
            
            **Flat Curve (Small/Zero Spread)** ↔️
            - Short and long-term yields are similar
            - Suggests economic uncertainty or transition
            - Often occurs during shifts in monetary policy
            
            **Inverted Curve (Negative Spread)** 📉
            - Short-term yields exceed long-term yields
            - Strong recession signal (preceded 7 out of last 8 recessions)
            - Typically appears 6-18 months before economic downturns
            
            ### Key Spread Relationships
            
            **2Y-10Y Spread**: Most widely watched recession indicator
            
            **2Y-5Y Spread**: Front-end indicator showing near-term policy expectations
            
            **3M-10Y Spread**: Fed's preferred recession indicator
            """)
            
        with col2:
            # Create a visual explanation of yield curve shapes
            fig = go.Figure()
            
            # X-axis values representing maturities
            x = [0.25, 2, 5, 10, 30]
            x_labels = ["3M", "2Y", "5Y", "10Y", "30Y"]
            
            # Normal curve
            normal_y = [1.0, 2.0, 2.8, 3.5, 4.0]
            fig.add_trace(go.Scatter(
                x=x, y=normal_y, mode='lines+markers', name='Normal Curve',
                line=dict(color='green', width=3), marker=dict(size=8)
            ))
            
            # Flat curve
            flat_y = [3.0, 3.0, 3.0, 3.1, 3.2]
            fig.add_trace(go.Scatter(
                x=x, y=flat_y, mode='lines+markers', name='Flat Curve',
                line=dict(color='orange', width=3), marker=dict(size=8)
            ))
            
            # Inverted curve
            inverted_y = [4.0, 3.8, 3.5, 3.2, 3.0]
            fig.add_trace(go.Scatter(
                x=x, y=inverted_y, mode='lines+markers', name='Inverted Curve',
                line=dict(color='red', width=3), marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="Typical Yield Curve Shapes",
                xaxis_title="Maturity",
                yaxis_title="Yield (%)",
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=300,
                margin=dict(l=10, r=10, t=40, b=10),
                xaxis=dict(
                    tickmode='array',
                    tickvals=x,
                    ticktext=x_labels
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Market implications section
        st.markdown("""
        ## Market Implications of Yield Curve Movements
        
        | Curve Movement | Typical Market Impact | Asset Class Performance |
        |----------------|------------------------|-------------------------|
        | **Steepening** (long-end yields rise faster) | Economic growth expectations increase | Bullish for equities, bearish for bonds |
        | **Flattening** (short-end yields rise faster) | Fed tightening, growth concerns | Neutral for equities, bearish for bonds |
        | **Inversion** (short-end yields exceed long-end) | Strong recession signal | Bearish for equities, bullish for bonds & gold |
        | **Bull steepening** (short-end falls faster than long-end) | Fed easing, growth recovery | Very bullish for equities & gold |
        | **Bear flattening** (short-end rises faster than long-end) | Fed tightening amid inflation | Bearish for equities & gold |
        
        ### Gold Relationship
        
        Gold typically performs exceptionally well during periods of:
        1. 📉 **Yield curve flattening/inversion** - signals economic uncertainty
        2. 📉 **Negative real interest rates** - reduces opportunity cost of holding gold
        3. 📈 **Monetary policy accommodation** - devalues currencies relative to gold
        
        A narrowing 2Y-10Y spread moving towards inversion is historically one of the strongest bullish signals for gold prices.
        """)
        
        # Interactive explanations that respond to current market conditions
        current_spread = treasury_data.get("2Y_10Y_spread", 0)
        if current_spread is not None:
            if current_spread < 0:
                highlight_color = "#ffcccb"
                # Create styled HTML content
                html_content = f"""
                <div style="background-color:{highlight_color}; padding:10px; border-radius:5px; margin:10px 0;">
                <strong>Current Alert:</strong> The yield curve is currently inverted, which historically suggests heightened recession risk 
                and may warrant defensive positioning in portfolios.
                </div>
                """
                
                # Render the content properly
                st.markdown(html_content, unsafe_allow_html=True)
            elif current_spread < 0.5:
                highlight_color = "#ffffcc"
                # Create styled HTML content
                html_content = f"""
                <div style="background-color:{highlight_color}; padding:10px; border-radius:5px; margin:10px 0;">
                <strong>Current Alert:</strong> The yield curve is relatively flat, suggesting economic uncertainty 
                and potential transition in monetary policy.
                </div>
                """
                
                # Render the content properly
                st.markdown(html_content, unsafe_allow_html=True)
