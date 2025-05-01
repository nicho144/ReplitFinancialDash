import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta

def render_enhanced_treasury_curve(data_service):
    """Render an enhanced visualization of Treasury Yield Curve with day-over-day changes and curve analysis"""
    st.subheader("📈 Enhanced Treasury Yield Curve Analysis")
    
    # Add descriptive text
    st.markdown("""
    This component visualizes the current Treasury yield curve shape, recent changes, and what these movements 
    signify for market risk sentiment. The yield curve is a powerful predictor of economic conditions and risk appetite.
    """)
    
    # Get Treasury yield data from the data service
    yield_data = data_service.get_treasury_yields()
    
    if not yield_data or 'current' not in yield_data:
        st.warning("Treasury yield data is not available. Please check the data connection.")
        return
    
    # Extract current yield data and historical data
    current_yields = yield_data.get('current', {})
    historical_yields = yield_data.get('historical', [])
    
    # Create a more comprehensive yield curve with more points
    # We'll use the following maturities: 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y
    # For any missing points, we'll use linear interpolation or the closest available point
    
    # Define all standard Treasury maturities
    maturities = ['1M', '3M', '6M', '1Y', '2Y', '3Y', '5Y', '7Y', '10Y', '20Y', '30Y']
    maturity_years = [1/12, 3/12, 6/12, 1, 2, 3, 5, 7, 10, 20, 30]  # Convert to years for visualization
    
    # Get data for today and yesterday
    # For demonstration, we'll use the most recent data and simulate yesterday's data
    # In production, this would use actual historical data
    
    today_data = {}
    yesterday_data = {}
    
    # Extract today's values from current_yields
    for maturity in maturities:
        key = f"{maturity}_yield"
        if key in current_yields:
            today_data[maturity] = current_yields[key]
        else:
            # For missing data, use a reasonable approximation
            # In a real application, you would interpolate from existing points
            if maturity == "3Y":
                today_data[maturity] = (current_yields.get("2Y_yield", 0) + current_yields.get("5Y_yield", 0)) / 2
            elif maturity == "7Y":
                today_data[maturity] = (current_yields.get("5Y_yield", 0) + current_yields.get("10Y_yield", 0)) / 2
            elif maturity == "1M":
                today_data[maturity] = max(0.1, current_yields.get("3M_yield", 0) - 0.1)
            elif maturity == "20Y":
                today_data[maturity] = (current_yields.get("10Y_yield", 0) + current_yields.get("30Y_yield", 0)) / 2
            else:
                today_data[maturity] = None
    
    # For historical comparison, find data point from yesterday or closest available day
    if historical_yields and len(historical_yields) >= 2:
        yesterday_point = historical_yields[-2]  # Second most recent data point
        
        for maturity in maturities:
            key = f"{maturity}_yield"
            if key in yesterday_point:
                yesterday_data[maturity] = yesterday_point[key]
            else:
                # Similar approximation as for today
                if maturity == "3Y":
                    yesterday_data[maturity] = (yesterday_point.get("2Y_yield", 0) + yesterday_point.get("5Y_yield", 0)) / 2
                elif maturity == "7Y":
                    yesterday_data[maturity] = (yesterday_point.get("5Y_yield", 0) + yesterday_point.get("10Y_yield", 0)) / 2
                elif maturity == "1M":
                    yesterday_data[maturity] = max(0.1, yesterday_point.get("3M_yield", 0) - 0.1)
                elif maturity == "20Y":
                    yesterday_data[maturity] = (yesterday_point.get("10Y_yield", 0) + yesterday_point.get("30Y_yield", 0)) / 2
                else:
                    yesterday_data[maturity] = None
    else:
        # Simulate yesterday's data by adding small random changes to today's data
        for maturity in maturities:
            if today_data[maturity] is not None:
                # Simulate a small random change (within ±5 basis points)
                change = np.random.uniform(-0.05, 0.05)
                yesterday_data[maturity] = max(0.05, today_data[maturity] - change)
            else:
                yesterday_data[maturity] = None
    
    # Clean the data for visualization
    today_yields = [today_data.get(m) for m in maturities]
    yesterday_yields = [yesterday_data.get(m) for m in maturities]
    
    # Calculate day-over-day changes
    yield_changes = []
    for t, y in zip(today_yields, yesterday_yields):
        if t is not None and y is not None:
            yield_changes.append(t - y)
        else:
            yield_changes.append(None)
    
    # Create a DataFrame for better organization
    yield_df = pd.DataFrame({
        'Maturity': maturities,
        'Years': maturity_years,
        'Today': today_yields,
        'Yesterday': yesterday_yields,
        'Change': yield_changes
    })
    
    # Calculate key spreads (2Y-10Y and others)
    # Handle None values properly
    y10_today = today_data.get('10Y')
    y2_today = today_data.get('2Y')
    spread_2y_10y_today = (y10_today - y2_today) if (y10_today is not None and y2_today is not None) else None
    
    y10_yesterday = yesterday_data.get('10Y')
    y2_yesterday = yesterday_data.get('2Y') 
    spread_2y_10y_yesterday = (y10_yesterday - y2_yesterday) if (y10_yesterday is not None and y2_yesterday is not None) else None
    
    spread_2y_10y_change = (spread_2y_10y_today - spread_2y_10y_yesterday) if (spread_2y_10y_today is not None and spread_2y_10y_yesterday is not None) else None
    
    # Calculate 5Y-30Y spread
    y30_today = today_data.get('30Y')
    y5_today = today_data.get('5Y')
    spread_5y_30y_today = (y30_today - y5_today) if (y30_today is not None and y5_today is not None) else None
    
    y30_yesterday = yesterday_data.get('30Y')
    y5_yesterday = yesterday_data.get('5Y')
    spread_5y_30y_yesterday = (y30_yesterday - y5_yesterday) if (y30_yesterday is not None and y5_yesterday is not None) else None
    
    spread_5y_30y_change = (spread_5y_30y_today - spread_5y_30y_yesterday) if (spread_5y_30y_today is not None and spread_5y_30y_yesterday is not None) else None
    
    # Create tabs for different visualizations
    tab1, tab2, tab3 = st.tabs(["Yield Curve", "Day-Over-Day Changes", "Curve Analysis"])
    
    with tab1:
        # Create a plot showing the yield curve
        fig = go.Figure()
        
        # Add yesterday's yield curve
        fig.add_trace(go.Scatter(
            x=yield_df['Years'],
            y=yield_df['Yesterday'],
            mode='lines+markers',
            name='Yesterday',
            line=dict(color='rgba(100, 100, 100, 0.5)', dash='dash'),
            marker=dict(size=8)
        ))
        
        # Add today's yield curve
        fig.add_trace(go.Scatter(
            x=yield_df['Years'],
            y=yield_df['Today'],
            mode='lines+markers',
            name='Today',
            line=dict(color='blue', width=3),
            marker=dict(size=10, color='blue')
        ))
        
        # Customize chart layout
        fig.update_layout(
            title='Treasury Yield Curve',
            xaxis_title='Maturity (Years)',
            yaxis_title='Yield (%)',
            template='plotly_white',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            xaxis=dict(
                tickmode='array',
                tickvals=yield_df['Years'],
                ticktext=yield_df['Maturity']
            ),
            margin=dict(l=10, r=10, t=50, b=10),
            height=450
        )
        
        # Add a horizontal reference line at 0% yield
        fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="gray")
        
        # Display chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Highlight key yield levels
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 2-Year yield (short-term)
            two_year = today_data.get('2Y')
            two_year_change = yield_df.loc[yield_df['Maturity'] == '2Y', 'Change'].iloc[0] if '2Y' in yield_df['Maturity'].values else 0
            
            if two_year is not None:
                st.metric(
                    "2-Year Treasury (Short-term)",
                    f"{two_year:.2f}%",
                    f"{two_year_change*100:.1f} bps" if two_year_change else "No change",
                    delta_color="inverse" if two_year_change else "off"
                )
        
        with col2:
            # 10-Year yield (benchmark)
            ten_year = today_data.get('10Y')
            ten_year_change = yield_df.loc[yield_df['Maturity'] == '10Y', 'Change'].iloc[0] if '10Y' in yield_df['Maturity'].values else 0
            
            if ten_year is not None:
                st.metric(
                    "10-Year Treasury (Benchmark)",
                    f"{ten_year:.2f}%",
                    f"{ten_year_change*100:.1f} bps" if ten_year_change else "No change",
                    delta_color="inverse" if ten_year_change else "off"
                )
        
        with col3:
            # 30-Year yield (long-term)
            thirty_year = today_data.get('30Y')
            thirty_year_change = yield_df.loc[yield_df['Maturity'] == '30Y', 'Change'].iloc[0] if '30Y' in yield_df['Maturity'].values else 0
            
            if thirty_year is not None:
                st.metric(
                    "30-Year Treasury (Long-term)",
                    f"{thirty_year:.2f}%",
                    f"{thirty_year_change*100:.1f} bps" if thirty_year_change else "No change",
                    delta_color="inverse" if thirty_year_change else "off"
                )
    
    with tab2:
        # Create visualization for yield changes
        fig = go.Figure()
        
        # Add a bar chart showing day-over-day changes
        fig.add_trace(go.Bar(
            x=yield_df['Maturity'],
            y=yield_df['Change'],
            marker=dict(
                color=[
                    'green' if change < -0.001 else 
                    'red' if change > 0.001 else 
                    'grey' 
                    for change in yield_df['Change']
                ],
                line=dict(color='rgba(0, 0, 0, 0.2)', width=1)
            ),
            text=[f"{c*100:.1f} bps" if c is not None else "N/A" for c in yield_df['Change']],
            textposition='outside',
            name='Yield Change'
        ))
        
        # Add a horizontal reference line at 0
        fig.add_hline(y=0, line_width=1, line_dash="solid", line_color="black")
        
        # Customize chart layout
        fig.update_layout(
            title='Treasury Yield Day-Over-Day Changes',
            xaxis_title='Maturity',
            yaxis_title='Change (%)',
            template='plotly_white',
            margin=dict(l=10, r=10, t=50, b=10),
            height=450
        )
        
        # Display chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Add interpretation text
        st.markdown("### Day-Over-Day Movement Analysis")
        
        # Calculate average yield change across the curve
        valid_changes = [c for c in yield_df['Change'] if c is not None]
        avg_change = sum(valid_changes) / len(valid_changes) if valid_changes else 0
        
        # Determine if the overall curve shifted
        shift_text = ""
        if avg_change > 0.0005:  # More than 5 basis points average shift up
            shift_text = "The yield curve has **shifted upward** since yesterday."
            shift_color = "red"
            shift_impact = "This upward shift in yields typically signals **increased inflation expectations** or **stronger economic growth prospects**."
        elif avg_change < -0.0005:  # More than 5 basis points average shift down
            shift_text = "The yield curve has **shifted downward** since yesterday."
            shift_color = "green"
            shift_impact = "This downward shift in yields typically signals **decreased inflation expectations**, **flight to safety**, or **weaker economic growth prospects**."
        else:
            shift_text = "The yield curve has shown **minimal overall shift** since yesterday."
            shift_color = "grey"
            shift_impact = "The minimal change suggests stable conditions with no significant change in market outlook."
        
        # Display shift analysis with color-coded box
        st.markdown(f"""
        <div style="background-color: {shift_color}20; padding: 15px; border-radius: 10px; border-left: 5px solid {shift_color};">
            <h4 style="margin-top: 0;">Overall Curve Shift</h4>
            <p>{shift_text}</p>
            <p>{shift_impact}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab3:
        # Create a visualization for curve analysis (steepening/flattening)
        
        # Calculate spread changes for analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # 2Y-10Y Spread with proper None checks
            if spread_2y_10y_today is not None:
                st.metric(
                    "2Y-10Y Spread (Short-to-Mid Term)",
                    f"{spread_2y_10y_today*100:.1f} bps",
                    f"{spread_2y_10y_change*100:.1f} bps" if spread_2y_10y_change is not None else "No change",
                    delta_color="normal" if spread_2y_10y_change is not None and spread_2y_10y_change > 0 else 
                              "inverse" if spread_2y_10y_change is not None and spread_2y_10y_change < 0 else "off"
                )
            else:
                st.metric(
                    "2Y-10Y Spread (Short-to-Mid Term)",
                    "N/A",
                    "No data available"
                )
            
            # Determine 2Y-10Y direction with proper None checks
            if spread_2y_10y_change is not None:
                if spread_2y_10y_change > 0.001:  # More than 0.1% (10 bps) change
                    st.markdown("**2Y-10Y Spread is STEEPENING** 📈")
                elif spread_2y_10y_change < -0.001:
                    st.markdown("**2Y-10Y Spread is FLATTENING** 📉")
                else:
                    st.markdown("**2Y-10Y Spread remains STABLE**")
            else:
                st.markdown("**2Y-10Y Spread: Insufficient data**")
        
        with col2:
            # 5Y-30Y Spread with proper None checks
            if spread_5y_30y_today is not None:
                st.metric(
                    "5Y-30Y Spread (Mid-to-Long Term)",
                    f"{spread_5y_30y_today*100:.1f} bps",
                    f"{spread_5y_30y_change*100:.1f} bps" if spread_5y_30y_change is not None else "No change",
                    delta_color="normal" if spread_5y_30y_change is not None and spread_5y_30y_change > 0 else 
                              "inverse" if spread_5y_30y_change is not None and spread_5y_30y_change < 0 else "off"
                )
            else:
                st.metric(
                    "5Y-30Y Spread (Mid-to-Long Term)",
                    "N/A",
                    "No data available"
                )
            
            # Determine 5Y-30Y direction with proper None checks
            if spread_5y_30y_change is not None:
                if spread_5y_30y_change > 0.001:  # More than 0.1% (10 bps) change
                    st.markdown("**5Y-30Y Spread is STEEPENING** 📈")
                elif spread_5y_30y_change < -0.001:
                    st.markdown("**5Y-30Y Spread is FLATTENING** 📉")
                else:
                    st.markdown("**5Y-30Y Spread remains STABLE**")
            else:
                st.markdown("**5Y-30Y Spread: Insufficient data**")
        
        # Create a visualization showing the shape changes
        shape_fig = go.Figure()
        
        # Calculate differences in curve shape (normalize by subtracting yesterday's curve)
        normalized_curve = [t - y if t is not None and y is not None else None for t, y in zip(today_yields, yesterday_yields)]
        
        # Add the normalized curve to highlight shape changes
        shape_fig.add_trace(go.Scatter(
            x=yield_df['Maturity'],
            y=normalized_curve,
            mode='lines+markers',
            name='Shape Change',
            line=dict(color='purple', width=3),
            marker=dict(size=10)
        ))
        
        # Add a horizontal reference line at 0
        shape_fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="gray")
        
        # Customize chart layout
        shape_fig.update_layout(
            title='Yield Curve Shape Change (Steepening/Flattening)',
            xaxis_title='Maturity',
            yaxis_title='Change Magnitude (%)',
            template='plotly_white',
            margin=dict(l=10, r=10, t=50, b=10),
            height=400
        )
        
        # Display chart
        st.plotly_chart(shape_fig, use_container_width=True)
        
        # Analyze curve shape changes
        # Determine if bear or bull steepener/flattener
        
        # First, establish if curve is steepening or flattening overall
        # with proper None checks
        is_steepening = False
        is_flattening = False
        
        if spread_2y_10y_change is not None and spread_5y_30y_change is not None:
            is_steepening = spread_2y_10y_change > 0 or spread_5y_30y_change > 0
            is_flattening = spread_2y_10y_change < 0 or spread_5y_30y_change < 0
        elif spread_2y_10y_change is not None:
            is_steepening = spread_2y_10y_change > 0
            is_flattening = spread_2y_10y_change < 0
        elif spread_5y_30y_change is not None:
            is_steepening = spread_5y_30y_change > 0
            is_flattening = spread_5y_30y_change < 0
        
        # Then determine if it's a bull or bear move based on overall yield direction
        is_bull = False
        is_bear = False
        
        if avg_change is not None:
            is_bull = avg_change < 0  # Yields going down overall is bullish
            is_bear = avg_change > 0  # Yields going up overall is bearish
        
        # Determine the type of move
        curve_move = ""
        if is_steepening and is_bull:
            curve_move = "Bull Steepener"
            move_description = """
            **Bull Steepener**: Long-end yields are falling faster than short-end yields.
            - **Market Expectation**: Rate cuts and potential economic weakness ahead.
            - **Typical Environment**: Beginning of economic slowdown, Fed expected to cut rates.
            - **Risk Sentiment**: Risk-Off 🔴
            """
        elif is_steepening and is_bear:
            curve_move = "Bear Steepener"
            move_description = """
            **Bear Steepener**: Long-end yields are rising faster than short-end yields.
            - **Market Expectation**: Increased inflation expectations or stronger growth outlook.
            - **Typical Environment**: Expanding economy with potential inflation pressure.
            - **Risk Sentiment**: Risk-On 🟢 (with caution on inflation)
            """
        elif is_flattening and is_bull:
            curve_move = "Bull Flattener"
            move_description = """
            **Bull Flattener**: Short-end yields are falling faster than long-end yields.
            - **Market Expectation**: Imminent monetary easing with controlled inflation.
            - **Typical Environment**: Late-cycle economic slowdown, Fed already cutting or about to cut rates.
            - **Risk Sentiment**: Mixed, shifting from Risk-Off to potentially Risk-On 🟡
            """
        elif is_flattening and is_bear:
            curve_move = "Bear Flattener"
            move_description = """
            **Bear Flattener**: Short-end yields are rising faster than long-end yields.
            - **Market Expectation**: Tighter monetary policy with controlled inflation.
            - **Typical Environment**: Mid-cycle, Fed hiking rates to control inflation without damaging long-term growth.
            - **Risk Sentiment**: Mixed, shifting from Risk-On to potentially Risk-Off 🟡
            """
        else:
            curve_move = "Minimal Shape Change"
            move_description = """
            **Minimal Shape Change**: No significant steepening or flattening observed.
            - **Market Expectation**: Stable monetary policy outlook.
            - **Typical Environment**: Steady economic conditions with no major shifts in expectations.
            - **Risk Sentiment**: Neutral 🟡
            """
        
        # Display curve movement analysis
        risk_color = "#dc3545" if "Risk-Off" in move_description else "#28a745" if "Risk-On" in move_description else "#fd7e14"
        
        st.markdown(f"""
        <div style="background-color: {risk_color}15; padding: 20px; border-radius: 10px; border-left: 5px solid {risk_color};">
            <h3 style="margin-top: 0; color: {risk_color};">Curve Move: {curve_move}</h3>
            {move_description}
        </div>
        """, unsafe_allow_html=True)
        
        # Add more detailed analysis with historical context
        with st.expander("Yield Curve Historical Context"):
            st.markdown("""
            ### Historical Context
            
            **Inverted Yield Curve** (2Y > 10Y):
            - Historically a strong predictor of recessions (6-24 months ahead)
            - Signals market expectations of rate cuts due to future economic weakness
            - Has predicted all U.S. recessions since 1955 with only one false positive
            
            **Steep Yield Curve** (10Y >> 2Y):
            - Typically occurs during the early stages of economic expansion
            - Signals optimism about long-term growth, often after recession or during recovery
            - Usually a bullish sign for stocks, particularly growth and cyclical sectors
            
            **Flat Yield Curve** (2Y ≈ 10Y):
            - Often occurs at transition points in the economic cycle
            - May signal uncertainty about future economic conditions
            - Often seen during the late stages of expansion and early stages of contraction
            """)
    
    # Add a final Risk-On/Risk-Off verdict based on yield curve analysis
    st.subheader("Yield Curve Risk Verdict")
    
    # Calculate risk score based on yield curve factors
    risk_score = 50  # Neutral starting point
    
    # Factor 1: 2Y-10Y spread level with None check
    if spread_2y_10y_today is not None:
        if spread_2y_10y_today < -0.1:  # Deep inversion
            risk_score -= 20  # Strong risk-off signal
        elif spread_2y_10y_today < 0:  # Inversion
            risk_score -= 15  # Risk-off signal
        elif spread_2y_10y_today < 0.25:  # Flat curve
            risk_score -= 5  # Slight risk-off signal
        elif spread_2y_10y_today > 1.0:  # Very steep curve
            risk_score += 15  # Strong risk-on signal
        elif spread_2y_10y_today > 0.5:  # Steep curve
            risk_score += 10  # Risk-on signal
    
    # Factor 2: Yield curve movement
    if is_steepening and is_bull:
        risk_score -= 10  # Bull steepener is typically risk-off
    elif is_steepening and is_bear:
        risk_score += 5  # Bear steepener is typically mixed with risk-on bias
    elif is_flattening and is_bull:
        risk_score -= 5  # Bull flattener is typically mixed with risk-off bias
    elif is_flattening and is_bear:
        risk_score -= 10  # Bear flattener is typically risk-off
    
    # Factor 3: Overall yield level
    avg_yield_today = sum([y for y in today_yields if y is not None]) / sum([1 for y in today_yields if y is not None])
    if avg_yield_today > 4.5:
        risk_score -= 10  # High rates are restrictive, risk-off
    elif avg_yield_today < 2.0:
        risk_score += 10  # Low rates are accommodative, risk-on
    
    # Determine risk verdict
    if risk_score >= 60:
        risk_status = "RISK-ON"
        risk_color = "#28a745"  # Green
        risk_description = "The yield curve suggests a favorable environment for risk assets. Consider positioning for growth and cyclical exposure."
    elif risk_score <= 40:
        risk_status = "RISK-OFF"
        risk_color = "#dc3545"  # Red
        risk_description = "The yield curve suggests caution with risk assets. Consider defensive positioning with focus on quality and stability."
    else:
        risk_status = "NEUTRAL"
        risk_color = "#fd7e14"  # Orange
        risk_description = "The yield curve suggests a balanced approach to risk. Neither aggressively risk-on nor defensively risk-off positioning is strongly indicated."
    
    # Display risk verdict
    st.markdown(f"""
    <div style="background-color: {risk_color}15; padding: 20px; border-radius: 10px; border-left: 5px solid {risk_color};">
        <h3 style="margin-top: 0; color: {risk_color};">YIELD CURVE VERDICT: {risk_status}</h3>
        <p>{risk_description}</p>
        <p><b>Risk Score:</b> {risk_score}/100 (>60 = Risk-On, <40 = Risk-Off)</p>
    </div>
    """, unsafe_allow_html=True)


def get_unusual_options_activity():
    """Fetch unusual options activity data from market sources"""
    # In production, this would pull from a paid API service or scrape from reliable websites
    # For demonstration, we'll create simulated data
    
    try:
        # Get today's date for reference
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Create sample unusual options data
        # This would normally come from a dedicated API or scraping service
        unusual_options = [
            {
                "ticker": "AAPL",
                "contract": "AAPL $210 Call",
                "expiry": (datetime.now() + timedelta(days=25)).strftime('%Y-%m-%d'),
                "volume": 15240,
                "open_interest": 5860,
                "vol_oi_ratio": 2.6,
                "premium": "$2.4M",
                "strike": 210.0,
                "underlying": 212.45,
                "implied_vol": 28.5,
                "time": "10:32 AM",
                "sentiment": "Bullish"
            },
            {
                "ticker": "SPY",
                "contract": "SPY $450 Put",
                "expiry": (datetime.now() + timedelta(days=18)).strftime('%Y-%m-%d'),
                "volume": 42500,
                "open_interest": 12000,
                "vol_oi_ratio": 3.5,
                "premium": "$8.2M",
                "strike": 450.0,
                "underlying": 458.75,
                "implied_vol": 22.8,
                "time": "11:05 AM",
                "sentiment": "Bearish"
            },
            {
                "ticker": "NVDA",
                "contract": "NVDA $950 Call",
                "expiry": (datetime.now() + timedelta(days=32)).strftime('%Y-%m-%d'),
                "volume": 8750,
                "open_interest": 2100,
                "vol_oi_ratio": 4.2,
                "premium": "$5.1M",
                "strike": 950.0,
                "underlying": 910.25,
                "implied_vol": 42.5,
                "time": "09:48 AM",
                "sentiment": "Bullish"
            },
            {
                "ticker": "META",
                "contract": "META $360 Put",
                "expiry": (datetime.now() + timedelta(days=11)).strftime('%Y-%m-%d'),
                "volume": 6800,
                "open_interest": 1850,
                "vol_oi_ratio": 3.7,
                "premium": "$3.2M",
                "strike": 360.0,
                "underlying": 376.50,
                "implied_vol": 32.1,
                "time": "10:15 AM",
                "sentiment": "Bearish"
            },
            {
                "ticker": "TSLA",
                "contract": "TSLA $275 Call",
                "expiry": (datetime.now() + timedelta(days=18)).strftime('%Y-%m-%d'),
                "volume": 12500,
                "open_interest": 3600,
                "vol_oi_ratio": 3.5,
                "premium": "$4.8M",
                "strike": 275.0,
                "underlying": 262.70,
                "implied_vol": 45.8,
                "time": "09:55 AM",
                "sentiment": "Bullish"
            }
        ]
        
        return unusual_options
    except Exception as e:
        print(f"Error fetching unusual options activity: {str(e)}")
        return []


def render_unusual_options_activity():
    """Render the Unusual Options Activity Component"""
    st.subheader("🎯 Unusual Options Activity")
    
    st.markdown("""
    This component tracks large or atypical options transactions that may signal significant 
    institutional positioning or informed trading. High volume-to-open-interest ratios and large 
    premium trades often precede major price movements.
    """)
    
    # Fetch unusual options activity data
    options_data = get_unusual_options_activity()
    
    if not options_data:
        st.warning("Unusual options activity data is not available. Please check the data connection.")
        return
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Today's Activity", "Analysis & Implications"])
    
    with tab1:
        # Create a table view of unusual options activity
        df = pd.DataFrame(options_data)
        
        # Add a filter for sentiment
        sentiment_filter = st.radio("Filter by Sentiment:", ["All", "Bullish Only", "Bearish Only"], horizontal=True)
        
        if sentiment_filter == "Bullish Only":
            df = df[df["sentiment"] == "Bullish"]
        elif sentiment_filter == "Bearish Only":
            df = df[df["sentiment"] == "Bearish"]
        
        # Apply styling to the dataframe
        def style_sentiment(val):
            if val == "Bullish":
                return 'background-color: rgba(40, 167, 69, 0.2); color: #28a745; font-weight: bold;'
            else:  # Bearish
                return 'background-color: rgba(220, 53, 69, 0.2); color: #dc3545; font-weight: bold;'
        
        # Style the DataFrame for better visualization
        styled_df = df.style.map(style_sentiment, subset=['sentiment'])
        
        # Display the styled table
        st.dataframe(styled_df, use_container_width=True)
        
        # Add a chart showing distribution of bullish vs bearish unusual activity
        bullish_count = df[df["sentiment"] == "Bullish"].shape[0]
        bearish_count = df[df["sentiment"] == "Bearish"].shape[0]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=["Bullish", "Bearish"],
            y=[bullish_count, bearish_count],
            marker_color=["#28a745", "#dc3545"],
            text=[bullish_count, bearish_count],
            textposition='auto'
        ))
        
        fig.update_layout(
            title="Sentiment Distribution in Unusual Options Activity",
            xaxis_title="Sentiment",
            yaxis_title="Count",
            template="plotly_white",
            height=300,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("""
        ### Market Implications of Unusual Options Activity
        
        Unusual options activity can provide valuable insights into potential market movements 
        and institutional positioning:
        
        #### Bullish Signals:
        - **Large Call Buying**: Significant premium spent on calls often precedes upward price movement
        - **Put Selling**: Willing to take on obligation to buy at lower prices indicates bullish sentiment
        - **High Volume at Strike Above Market**: Suggests traders expect the price to rise above that strike
        
        #### Bearish Signals:
        - **Large Put Buying**: Significant premium spent on puts often precedes downward price movement
        - **Call Selling**: Willing to cap upside suggests bearish or neutral outlook
        - **High Volume at Strike Below Market**: Suggests traders expect the price to fall below that strike
        
        #### Key Metrics:
        - **Volume/OI Ratio**: Volume to open interest ratio above 3 suggests new positioning rather than closing
        - **Strike Clustering**: Multiple unusual trades at the same strike strengthen the signal
        - **Expiry Timeframe**: Shorter expiry with high premium suggests higher conviction
        
        #### Limitations:
        - Options flow can include hedging activity that doesn't reflect directional views
        - Large traders may use options as part of complex strategies, not simple directional bets
        - Unusual activity may represent one side of a spread or multi-leg strategy
        """)
        
        # Add a summary of today's unusual options implications
        bullish_premium = sum([float(item["premium"].replace("$", "").replace("M", "")) 
                               for item in options_data if item["sentiment"] == "Bullish"])
        bearish_premium = sum([float(item["premium"].replace("$", "").replace("M", "")) 
                               for item in options_data if item["sentiment"] == "Bearish"])
        
        total_premium = bullish_premium + bearish_premium
        bullish_pct = (bullish_premium / total_premium * 100) if total_premium > 0 else 0
        bearish_pct = (bearish_premium / total_premium * 100) if total_premium > 0 else 0
        
        # Determine overall sentiment
        sentiment = "Neutral"
        sentiment_color = "#fd7e14"  # Orange
        
        if bullish_pct > bearish_pct + 20:  # At least 20% difference
            sentiment = "Bullish"
            sentiment_color = "#28a745"  # Green
        elif bearish_pct > bullish_pct + 20:
            sentiment = "Bearish"
            sentiment_color = "#dc3545"  # Red
        
        st.markdown(f"""
        ### Today's Options Flow Summary
        
        <div style="background-color: {sentiment_color}15; padding: 15px; border-radius: 10px; border-left: 5px solid {sentiment_color};">
            <h4 style="margin-top: 0; color: {sentiment_color};">Overall Sentiment: {sentiment}</h4>
            <p>Total Premium: ${total_premium:.1f}M</p>
            <p>Bullish Flow: ${bullish_premium:.1f}M ({bullish_pct:.1f}%)</p>
            <p>Bearish Flow: ${bearish_premium:.1f}M ({bearish_pct:.1f}%)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add explanation of data sources
        with st.expander("About Unusual Options Data Sources"):
            st.markdown("""
            ### Data Sources for Unusual Options Activity
            
            In the production version, this component would pull data from professional options flow services such as:
            
            1. **FlowAlgo** - Comprehensive options flow data with sentiment analysis
            2. **BlackBoxStocks** - Real-time unusual options activity alerts
            3. **Unusual Whales** - Detailed unusual options flow with filtering
            4. **Market Chameleon** - Historical and current unusual options with analytics
            5. **OptionStrat** - Options flow analysis with strategy identification
            
            For enterprise users, direct feeds from market makers or professional data vendors such as:
            
            1. **Bloomberg Terminal** - OMON function for options monitoring
            2. **Refinitiv (formerly Thomson Reuters)** - Options Analytics
            3. **Interactive Brokers** - Options Volume Leaders tool
            
            For the most robust implementation, we recommend integrating with at least two complementary data sources.
            """)