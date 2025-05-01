import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.subplots as sp
import yfinance as yf
from datetime import datetime, timedelta

def render_market_volatility(data_service):
    """Render a comprehensive market volatility and breadth analysis section with professional indicators"""
    st.header("Market Volatility & VIX Analysis")
    
    with st.spinner("Loading volatility data..."):
        # Get market breadth data from data service
        volatility_data = data_service.get_market_breadth()
        
        if not volatility_data:
            st.error("Unable to fetch volatility data. Please check API connections.")
            return
    
    # Create tabs for different volatility analyses
    tab1, tab2, tab3 = st.tabs(["VIX Analysis", "Market Breadth", "Expected Move"])
    
    with tab1:
        render_vix_analysis(volatility_data)
        
    with tab2:
        render_market_breadth_indicators(volatility_data)
        
    with tab3:
        render_expected_move_analysis(volatility_data)

def render_vix_analysis(volatility_data):
    """Render VIX analysis with VIX term structure and skew"""
    st.subheader("VIX & Volatility Metrics")
    
    # Current VIX and related metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        vix_value = volatility_data.get('vix', 21.5)
        vix_change = volatility_data.get('vix_change', 0.75)
        delta_color = "normal" if vix_change < 0 else "inverse"
        st.metric(
            "VIX", 
            f"{vix_value:.2f}", 
            f"{vix_change:+.2f}",
            delta_color=delta_color
        )
    
    with col2:
        vxn_value = volatility_data.get('vxn', 23.8)
        vxn_premium = vxn_value - volatility_data.get('vix', 21.5)
        st.metric(
            "VXN (Nasdaq VIX)", 
            f"{vxn_value:.2f}", 
            f"Premium: {vxn_premium:+.2f}"
        )
    
    with col3:
        vix3m_value = volatility_data.get('vix3m', 22.3)
        contango = vix3m_value - volatility_data.get('vix', 21.5)
        contango_pct = (contango / volatility_data.get('vix', 21.5)) * 100
        contango_status = "Contango" if contango > 0 else "Backwardation"
        st.metric(
            "VIX 3M", 
            f"{vix3m_value:.2f}", 
            f"{contango_status}: {contango_pct:+.1f}%"
        )
    
    with col4:
        vvix_value = volatility_data.get('vvix', 85.5)
        st.metric(
            "VVIX (Vol of Vol)", 
            f"{vvix_value:.2f}", 
            "Elevated" if vvix_value > 100 else "Normal"
        )
    
    # Volatility Risk Premium (VRP) - The difference between implied and realized volatility
    col1, col2, col3 = st.columns(3)
    
    with col1:
        realized_vol = volatility_data.get('realized_vol', 18.2)
        st.metric(
            "Realized Volatility (21d)", 
            f"{realized_vol:.2f}"
        )
    
    with col2:
        vrp = volatility_data.get('vrp', 3.3)
        st.metric(
            "Volatility Risk Premium", 
            f"{vrp:+.2f}", 
            "Overpriced" if vrp > 4 else "Fair" if vrp > 0 else "Underpriced"
        )
    
    with col3:
        skew_value = volatility_data.get('skew', 130)
        skew_status = "High" if skew_value > 135 else "Normal" if skew_value > 120 else "Low"
        st.metric(
            "SKEW Index", 
            f"{skew_value:.1f}", 
            f"{skew_status} Tail Risk"
        )
    
    # VIX term structure chart (illustrative)
    st.subheader("VIX Term Structure")
    
    # Create simulated VIX term structure data
    vix_spot = volatility_data.get('vix', 21.5)
    vix_structure = {
        'tenors': ['Spot', '1W', '1M', '2M', '3M', '4M', '5M', '6M'],
        'values': [
            vix_spot,
            vix_spot * (1 + np.random.uniform(-0.05, 0.08)),
            vix_spot * (1 + np.random.uniform(0, 0.1)),
            volatility_data.get('vix3m', 22.3) * 0.9,
            volatility_data.get('vix3m', 22.3),
            volatility_data.get('vix3m', 22.3) * 1.05,
            volatility_data.get('vix3m', 22.3) * 1.1,
            volatility_data.get('vix3m', 22.3) * 1.15
        ]
    }
    
    # Create term structure chart
    fig = go.Figure()
    
    # Current term structure
    fig.add_trace(go.Scatter(
        x=vix_structure['tenors'],
        y=vix_structure['values'],
        mode='lines+markers',
        name='Current',
        line=dict(color='blue', width=2),
        marker=dict(size=8)
    ))
    
    # Previous day's term structure (shifted slightly for illustration)
    fig.add_trace(go.Scatter(
        x=vix_structure['tenors'],
        y=[v * (1 + np.random.uniform(-0.1, 0.1)) for v in vix_structure['values']],
        mode='lines+markers',
        name='Previous Day',
        line=dict(color='gray', width=2, dash='dash'),
        marker=dict(size=6)
    ))
    
    # Add horizontal reference line at current VIX level
    fig.add_shape(
        type="line",
        x0=vix_structure['tenors'][0],
        y0=vix_spot,
        x1=vix_structure['tenors'][-1],
        y1=vix_spot,
        line=dict(color="red", width=1, dash="dot"),
    )
    
    # Update layout
    fig.update_layout(
        title='VIX Term Structure (Futures Curve)',
        xaxis_title='Expiration',
        yaxis_title='VIX Value',
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add VIX interpretation and trading implications
    with st.expander("VIX Analysis & Market Implications"):
        # Create a more visual and educational display
        vix_status = "Elevated volatility" if vix_value > 20 else "Low volatility"
        term_structure = "contango" if contango > 0 else "backwardation"
        term_structure_meaning = "market expects volatility to decrease" if contango > 0 else "market expects volatility to increase"
        vrp_status = "Options appear overpriced" if vrp > 4 else "Options fairly priced" if vrp > 0 else "Options appear underpriced"
        skew_status = "Heightened concern about tail risk" if skew_value > 135 else "Normal tail risk perception" if skew_value > 120 else "Low concern about tail risk"
        
        market_implications = "Current volatility conditions suggest a cautious approach to risk assets" if vix_value > 25 or contango < 0 else \
                             "Volatility environment is conducive to risk-taking" if vix_value < 15 and contango > 0 else \
                             "Neutral volatility environment with balanced risk/reward"
                             
        options_strategy = "Consider volatility-selling strategies like iron condors or credit spreads" if vrp > 4 and contango > 0 else \
                          "Consider long volatility strategies like straddles or strangles" if vrp < 0 or contango < 0 else \
                          "Balanced approach with spreads that have defined risk/reward"
        
        # Display in a more visual format
        st.markdown(f"""
        <h3 style="text-align: center; color: #1E88E5;">VIX Interpretation Guide</h3>
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <table style="width: 100%;">
                <tr>
                    <td style="width: 40%; font-weight: bold;">Current VIX Reading:</td>
                    <td>{vix_value:.2f} - <span style="color: {'#FF5722' if vix_value > 20 else '#4CAF50'}">{vix_status}</span></td>
                </tr>
                <tr>
                    <td style="width: 40%; font-weight: bold;">Term Structure:</td>
                    <td>Currently in <b>{term_structure}</b> - {term_structure_meaning}</td>
                </tr>
                <tr>
                    <td style="width: 40%; font-weight: bold;">Volatility Risk Premium:</td>
                    <td>{vrp:.2f} - {vrp_status}</td>
                </tr>
                <tr>
                    <td style="width: 40%; font-weight: bold;">SKEW Index:</td>
                    <td>{skew_value:.1f} - {skew_status}</td>
                </tr>
            </table>
        </div>
        
        <div style="background-color: #FAFAFA; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <h4 style="color: #1E88E5; margin-bottom: 10px;">Market Implications</h4>
            <p>{market_implications}</p>
            
            <h4 style="color: #1E88E5; margin-top: 15px; margin-bottom: 10px;">Options Trading Strategy</h4>
            <p>{options_strategy}</p>
        </div>
        
        <div style="background-color: #FFF8E1; padding: 15px; border-radius: 10px;">
            <h4 style="color: #FB8C00; margin-bottom: 10px;">Education Corner: VIX Explained</h4>
            <p>The VIX (CBOE Volatility Index) measures the market's expectation of 30-day forward-looking volatility. Often called the "fear gauge," it represents the market's estimate of future volatility based on S&P 500 options.</p>
            
            <p><b>Key VIX levels to watch:</b></p>
            <ul>
                <li><b>Below 15</b>: Low volatility, market complacency</li>
                <li><b>15-20</b>: Normal volatility conditions</li>
                <li><b>20-30</b>: Elevated volatility, increasing uncertainty</li>
                <li><b>Above 30</b>: High volatility, significant market fear</li>
                <li><b>Above 40</b>: Extreme volatility, potential market crisis</li>
            </ul>
            
            <p><b>VIX Term Structure:</b> When longer-dated VIX futures trade higher than near-term (contango), it indicates market expects volatility to decrease. When near-term futures trade higher (backwardation), it signals market expects volatility to increase.</p>
        </div>
        """, unsafe_allow_html=True)

def render_market_breadth_indicators(volatility_data):
    """Render market breadth indicators including TICK, TRIN, and advance-decline metrics"""
    st.subheader("Market Breadth Indicators")
    
    # TICK and TRIN
    col1, col2 = st.columns(2)
    
    with col1:
        tick_value = volatility_data.get('tick', 250)
        tick_status = "Strongly Positive" if tick_value > 700 else \
                      "Positive" if tick_value > 300 else \
                      "Neutral" if tick_value > -300 else \
                      "Negative" if tick_value > -700 else "Strongly Negative"
        
        st.metric(
            "NYSE TICK", 
            f"{tick_value:+d}", 
            tick_status
        )
        
        # Get the interpretation text
        tick_interpretation = "Strong buying pressure across majority of NYSE stocks" if tick_value > 700 else \
                             "Moderate buying pressure" if tick_value > 300 else \
                             "Balanced buying/selling pressure" if tick_value > -300 else \
                             "Moderate selling pressure" if tick_value > -700 else \
                             "Strong selling pressure across majority of NYSE stocks"
        
        # Determine color based on status
        tick_color = "#4CAF50" if tick_value > 300 else \
                    "#90CAF9" if tick_value > -300 else \
                    "#F44336"
        
        # Create styled interpretation display
        st.markdown(f"""
        <div style="background-color: {tick_color}25; padding: 10px; border-radius: 5px; border-left: 5px solid {tick_color};">
            <span style="font-weight: bold;">TICK Interpretation:</span> {tick_interpretation}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        trin_value = volatility_data.get('trin', 0.92)
        trin_status = "Strongly Bullish" if trin_value < 0.7 else \
                      "Bullish" if trin_value < 0.9 else \
                      "Neutral" if trin_value < 1.1 else \
                      "Bearish" if trin_value < 1.3 else "Strongly Bearish"
        
        st.metric(
            "TRIN (Arms Index)", 
            f"{trin_value:.2f}", 
            trin_status,
            delta_color="inverse" if trin_value > 1.0 else "normal"
        )
        
        # Get the interpretation text
        trin_interpretation = "Strong volume flowing into advancing stocks" if trin_value < 0.7 else \
                             "More volume going to advancing than declining stocks" if trin_value < 0.9 else \
                             "Balanced volume between advancing and declining stocks" if trin_value < 1.1 else \
                             "More volume going to declining than advancing stocks" if trin_value < 1.3 else \
                             "Strong volume flowing into declining stocks"
        
        # Determine color based on status
        trin_color = "#4CAF50" if trin_value < 0.9 else \
                    "#2196F3" if trin_value < 1.1 else \
                    "#F44336"
        
        # Create styled interpretation display
        st.markdown(f"""
        <div style="background-color: {trin_color}25; padding: 10px; border-radius: 5px; border-left: 5px solid {trin_color};">
            <span style="font-weight: bold;">TRIN Interpretation:</span> {trin_interpretation}
        </div>
        """, unsafe_allow_html=True)
    
    # Advance/Decline Metrics
    st.subheader("Advance/Decline Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        adv_issues = volatility_data.get('advancers', 320)
        dec_issues = volatility_data.get('decliners', 180)
        
        # Calculate percentages
        total_issues = adv_issues + dec_issues
        adv_pct = (adv_issues / total_issues) * 100 if total_issues > 0 else 0
        dec_pct = (dec_issues / total_issues) * 100 if total_issues > 0 else 0
        
        st.metric(
            "Advancing Issues", 
            f"{adv_issues}",
            f"{adv_pct:.1f}% of total"
        )
        
        st.metric(
            "Declining Issues", 
            f"{dec_issues}",
            f"{dec_pct:.1f}% of total"
        )
    
    with col2:
        adv_vol = volatility_data.get('advancing_volume', 1200000000)
        dec_vol = volatility_data.get('declining_volume', 800000000)
        
        # Format volume for display (in millions)
        adv_vol_display = adv_vol / 1000000
        dec_vol_display = dec_vol / 1000000
        
        # Calculate percentages
        total_vol = adv_vol + dec_vol
        adv_vol_pct = (adv_vol / total_vol) * 100 if total_vol > 0 else 0
        dec_vol_pct = (dec_vol / total_vol) * 100 if total_vol > 0 else 0
        
        st.metric(
            "Advancing Volume", 
            f"{adv_vol_display:.0f}M",
            f"{adv_vol_pct:.1f}% of total"
        )
        
        st.metric(
            "Declining Volume", 
            f"{dec_vol_display:.0f}M",
            f"{dec_vol_pct:.1f}% of total"
        )
    
    with col3:
        ad_ratio = volatility_data.get('adv_dec_ratio', 1.78)
        adv_vol_ratio = adv_vol / dec_vol if dec_vol > 0 else float('inf')
        
        st.metric(
            "Adv/Dec Ratio", 
            f"{ad_ratio:.2f}",
            "Bullish" if ad_ratio > 1.5 else "Neutral" if ad_ratio > 0.8 else "Bearish"
        )
        
        st.metric(
            "Adv/Dec Volume Ratio", 
            f"{adv_vol_ratio:.2f}",
            "Bullish" if adv_vol_ratio > 1.5 else "Neutral" if adv_vol_ratio > 0.8 else "Bearish"
        )
    
    # Market internals interpretation
    st.subheader("Market Breadth Analysis")
    
    # Determine overall breadth signal
    if tick_value > 300 and trin_value < 0.9 and ad_ratio > 1.5:
        breadth_signal = "Strong"
        signal_color = "green"
    elif tick_value > 0 and trin_value < 1.1 and ad_ratio > 1.0:
        breadth_signal = "Positive"
        signal_color = "lightgreen"
    elif tick_value < -300 and trin_value > 1.1 and ad_ratio < 0.8:
        breadth_signal = "Weak"
        signal_color = "red"
    elif tick_value < 0 and trin_value > 1.0 and ad_ratio < 1.0:
        breadth_signal = "Negative"
        signal_color = "orange"
    else:
        breadth_signal = "Mixed"
        signal_color = "gray"
    
    st.markdown(f"""
    <div style="padding: 10px; border-radius: 5px; background-color: {signal_color}; color: white;">
        <h3 style="margin:0;">Market Breadth Signal: {breadth_signal}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a visual interpretation with icons and colored sections
    
    if breadth_signal == "Strong":
        icon = "📈"
        color = "#4CAF50"
        title = "Strong market breadth indicates:"
        bullets = [
            "Broad participation across stocks and sectors",
            "Healthy bull market with solid momentum",
            "Low probability of near-term reversal",
            "Favorable environment for long positions"
        ]
    elif breadth_signal == "Positive":
        icon = "👍"
        color = "#8BC34A"
        title = "Positive market breadth indicates:"
        bullets = [
            "Good participation, though not universal",
            "Bull market likely to continue",
            "Some sectors may be lagging",
            "Still favorable for long positions with sector selectivity"
        ]
    elif breadth_signal == "Mixed":
        icon = "⚖️"
        color = "#9E9E9E"
        title = "Mixed market breadth indicates:"
        bullets = [
            "Unclear market direction",
            "Some divergences between price and internals",
            "Rotation between sectors likely occurring",
            "Suggest caution and balanced positioning"
        ]
    elif breadth_signal == "Negative":
        icon = "👎"
        color = "#FF9800"
        title = "Negative market breadth indicates:"
        bullets = [
            "Narrow leadership in the market",
            "Signs of distribution under the surface",
            "Increased risk of pullbacks",
            "Consider reducing long exposure or implementing hedges"
        ]
    else:  # Weak
        icon = "📉"
        color = "#F44336"
        title = "Weak market breadth indicates:"
        bullets = [
            "Widespread selling pressure",
            "Bear market conditions or correction in progress",
            "High probability of continued downside",
            "Consider defensive positioning or short exposure"
        ]
    
    # Build bullet list HTML
    bullet_html = ""
    for bullet in bullets:
        bullet_html += f"<li>{bullet}</li>"
    
    # Display the styled interpretation
    st.markdown(f"""
    <div style="background-color: {color}15; padding: 20px; border-radius: 10px; margin-top: 15px; border: 1px solid {color};">
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <div style="font-size: 2em; margin-right: 10px;">{icon}</div>
            <h4 style="margin: 0; color: {color};">{title}</h4>
        </div>
        <ul style="margin-bottom: 0;">
            {bullet_html}
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Add more detailed explanation
    with st.expander("Understanding Market Breadth Metrics"):
        st.markdown("""
        ### Market Breadth Indicators Explained
        
        **NYSE TICK**
        - Measures the number of NYSE stocks trading on an uptick minus those trading on a downtick
        - Extreme readings (+1000/-1000) often mark short-term exhaustion points
        - Persistent positive/negative readings throughout the day indicate strong buying/selling pressure
        
        **TRIN (Arms Index)**
        - Formula: (Advancing Issues/Declining Issues) / (Advancing Volume/Declining Volume)
        - Values below 1.0 are bullish (more volume going to advancers)
        - Values above 1.0 are bearish (more volume going to decliners)
        - Extreme readings (below 0.5 or above 1.5) often signal short-term overbought/oversold conditions
        
        **Advance/Decline Data**
        - Measures the breadth of market participation
        - Helps identify if market moves are broad-based or concentrated in a few stocks
        - Divergences between price action and A/D statistics often precede market turning points
        
        **Trading Application**
        - Strong breadth confirms trend strength and usually precedes further movement in that direction
        - Weak breadth during rallies suggests caution and potential trend exhaustion
        - Breadth extremes can be used to identify overbought/oversold conditions
        """)

def render_expected_move_analysis(volatility_data):
    """Render expected move analysis based on options-implied volatility and credit spreads"""
    st.subheader("Expected Move Analysis")
    
    # Current market data
    spy_price = 498.50  # Sample current SPY price
    vix_value = volatility_data.get('vix', 21.5)
    realized_vol = volatility_data.get('realized_vol', 18.2)
    
    # Calculate expected move
    days_to_expiry = [1, 5, 10, 20, 30]
    expected_moves = []
    
    for days in days_to_expiry:
        # Formula: S * IV * sqrt(T)
        # Where S is price, IV is implied vol as decimal, T is time in years
        iv_decimal = vix_value / 100
        time_in_years = days / 365
        
        expected_move = spy_price * iv_decimal * np.sqrt(time_in_years)
        expected_move_pct = (expected_move / spy_price) * 100
        
        expected_moves.append({
            'days': days,
            'period': f"{days} {'day' if days == 1 else 'days'}",
            'move_pts': expected_move,
            'move_pct': expected_move_pct
        })
    
    # Create expected move table
    move_df = pd.DataFrame(expected_moves)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display table of expected moves
        st.markdown("### SPY Expected Move by Timeframe")
        
        # Format table for display
        display_df = move_df.copy()
        display_df['Range (Points)'] = display_df['move_pts'].apply(lambda x: f"±{x:.2f}")
        display_df['Range (%)'] = display_df['move_pct'].apply(lambda x: f"±{x:.2f}%")
        display_df['Price Range'] = display_df['move_pts'].apply(lambda x: f"${spy_price-x:.2f} - ${spy_price+x:.2f}")
        
        # Display only relevant columns
        st.dataframe(display_df[['period', 'Range (Points)', 'Range (%)', 'Price Range']], use_container_width=True)
    
    with col2:
        # Key statistics
        st.markdown("### Volatility Statistics")
        
        st.metric(
            "SPY Current Price", 
            f"${spy_price:.2f}"
        )
        
        st.metric(
            "Implied Volatility (VIX)", 
            f"{vix_value:.2f}%"
        )
        
        st.metric(
            "Realized Volatility (21d)", 
            f"{realized_vol:.2f}%",
            f"{vix_value - realized_vol:+.2f}% vs. Implied"
        )
    
    # Probability distribution chart
    st.subheader("SPY Price Probability Distribution (30 Days)")
    
    # Generate normal distribution based on expected move
    thirty_day_move = move_df[move_df['days'] == 30]['move_pts'].values[0]
    std_dev = thirty_day_move / 1.645  # 1.645 is the z-score for 90% confidence interval
    
    # Generate price range and probability density
    price_range = np.linspace(spy_price - 3*std_dev, spy_price + 3*std_dev, 100)
    density = np.exp(-0.5 * ((price_range - spy_price) / std_dev) ** 2) / (std_dev * np.sqrt(2 * np.pi))
    
    # Create probability distribution chart
    fig = go.Figure()
    
    # Add density curve
    fig.add_trace(go.Scatter(
        x=price_range,
        y=density,
        mode='lines',
        line=dict(color='blue', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 100, 255, 0.2)',
        name='Probability Density'
    ))
    
    # Add vertical line for current price
    fig.add_shape(
        type="line",
        x0=spy_price,
        y0=0,
        x1=spy_price,
        y1=max(density),
        line=dict(color="red", width=2, dash="solid"),
    )
    
    # Add lines for 1-standard deviation move
    fig.add_shape(
        type="line",
        x0=spy_price - std_dev,
        y0=0,
        x1=spy_price - std_dev,
        y1=max(density) * 0.6,
        line=dict(color="green", width=2, dash="dash"),
    )
    
    fig.add_shape(
        type="line",
        x0=spy_price + std_dev,
        y0=0,
        x1=spy_price + std_dev,
        y1=max(density) * 0.6,
        line=dict(color="green", width=2, dash="dash"),
    )
    
    # Add annotations
    fig.add_annotation(
        x=spy_price,
        y=max(density) * 1.05,
        text=f"Current: ${spy_price:.2f}",
        showarrow=False,
        font=dict(size=12, color="red")
    )
    
    fig.add_annotation(
        x=spy_price - std_dev,
        y=max(density) * 0.65,
        text=f"${(spy_price - std_dev):.2f} (-1σ)",
        showarrow=False,
        font=dict(size=12, color="green")
    )
    
    fig.add_annotation(
        x=spy_price + std_dev,
        y=max(density) * 0.65,
        text=f"${(spy_price + std_dev):.2f} (+1σ)",
        showarrow=False,
        font=dict(size=12, color="green")
    )
    
    # Update layout
    fig.update_layout(
        title='SPY 30-Day Price Probability Distribution',
        xaxis_title='Price',
        yaxis_title='Probability Density',
        height=400,
        yaxis=dict(showticklabels=False),
        xaxis=dict(tickformat="$.2f"),
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add probability statistics
    one_std_prob = 68.2
    two_std_prob = 95.4
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Probability Analysis (30 Days):**
        - **68% Chance**: SPY between ${spy_price - std_dev:.2f} and ${spy_price + std_dev:.2f}
        - **95% Chance**: SPY between ${spy_price - 2*std_dev:.2f} and ${spy_price + 2*std_dev:.2f}
        - **99% Chance**: SPY between ${spy_price - 3*std_dev:.2f} and ${spy_price + 3*std_dev:.2f}
        """)
    
    with col2:
        st.markdown(f"""
        **Key Levels:**
        - **Expected High**: ${spy_price + thirty_day_move:.2f} (+{thirty_day_move/spy_price*100:.2f}%)
        - **Expected Low**: ${spy_price - thirty_day_move:.2f} (-{thirty_day_move/spy_price*100:.2f}%)
        - **Current Skew Bias**: {"Downside Protection" if volatility_data.get('skew', 130) > 125 else "Balanced"}
        """)
    
    # Add options strategy suggestions based on the volatility environment
    with st.expander("Options Strategy Suggestions"):
        
        # Determine if IV is high or low compared to realized vol
        iv_vs_rv = vix_value - realized_vol
        iv_percentile = 65  # Sample IV percentile (would be calculated based on historical data)
        
        # Generate strategy suggestions
        if iv_vs_rv > 4 and iv_percentile > 70:
            st.markdown("""
            ### High Implied Volatility Environment
            
            **Implied volatility is currently elevated compared to historical realized volatility, suggesting options are expensive.**
            
            **Potential strategies:**
            
            **1. Short Volatility Strategies**
            - **Iron Condors**: Sell OTM call and put spreads to capitalize on elevated IV and time decay
            - **Credit Spreads**: Sell vertical spreads in the direction contrary to expected movement
            - **Covered Calls**: For existing stock positions, sell calls to generate income
            
            **2. Calendar Spreads**
            - Sell near-term options and buy longer-term options to benefit from term structure
            
            **3. Ratio Spreads**
            - Sell more options than you buy to create positive theta positions
            
            **Risk Management:**
            - Size positions smaller due to elevated implied volatility
            - Consider using defined-risk strategies only
            - Place stops based on volatility-adjusted levels rather than fixed prices
            """)
        
        elif iv_vs_rv < -2 or iv_percentile < 30:
            st.markdown("""
            ### Low Implied Volatility Environment
            
            **Implied volatility is currently depressed compared to historical realized volatility, suggesting options are relatively cheap.**
            
            **Potential strategies:**
            
            **1. Long Volatility Strategies**
            - **Long Straddles/Strangles**: Buy ATM calls and puts to profit from movements in either direction
            - **Directional Debit Spreads**: Buy vertical spreads in the direction of expected movement
            - **Butterflies**: Use long butterfly spreads for defined-risk, high-reward setups
            
            **2. Diagonal Spreads**
            - Buy longer-dated options while selling shorter-dated options in anticipation of volatility expansion
            
            **3. Long Calls/Puts**
            - Consider outright long options positions if directional conviction is high
            
            **Risk Management:**
            - Position sizing can be larger due to reduced option costs
            - Consider layering into positions rather than deploying all capital at once
            - Time exits based on expected move timeframes
            """)
        
        else:
            st.markdown("""
            ### Neutral Volatility Environment
            
            **Implied volatility is currently in line with historical realized volatility, suggesting options are fairly priced.**
            
            **Potential strategies:**
            
            **1. Balanced Strategies**
            - **Broken-Wing Butterflies**: Asymmetric risk/reward with manageable risk
            - **Iron Condors with Skew Adjustment**: Adjust width of spreads based on market skew
            - **Vertical Spreads**: Use debit or credit spreads based on directional bias
            
            **2. Risk-Defined Strategies**
            - Prefer defined-risk strategies in this environment
            - Consider option replacement strategies (using long calls/puts instead of stock)
            
            **3. Stock-Option Combinations**
            - Collar strategies to protect existing positions
            - Cash-secured puts for potential stock entry at lower prices
            
            **Risk Management:**
            - Balance premium collection and debit positions
            - Consider both volatility expansion and contraction scenarios
            - Set profit targets based on expected move metrics
            """)
        
        # Add educational information about expected move
        st.markdown("""
        ### Understanding Expected Move
        
        The expected move is calculated based on options-implied volatility, which represents the market's forecast of future price movement. The formula used is:
        
        **Expected Move = Current Price × Implied Volatility × Square Root(Time in Years)**
        
        Key points:
        - This provides a one standard deviation (1σ) expected range (68% probability)
        - Larger moves have decreasing probability (95% within 2σ, 99% within 3σ)
        - Actual price movements may exceed these ranges in cases of significant market events
        - The calculation assumes a normal distribution, which doesn't always match market behavior
        
        Traders use expected move calculations to:
        1. Set appropriate stop-loss and take-profit levels
        2. Size positions based on potential volatility
        3. Select option strikes for various strategies
        4. Gauge whether market expectations align with their own forecasts
        """)