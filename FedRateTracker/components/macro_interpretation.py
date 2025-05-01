import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

def render_macro_interpretation(data_service):
    """Render the Macro Interpretation & Skew section"""
    st.header("6. Macro Interpretation & Skew")
    
    # Create tabs for different sections
    tab1, tab2 = st.tabs(["Macro News Interpretation", "Options Skew Analysis"])
    
    # Macro News Interpretation Tab
    with tab1:
        st.subheader("Recent Financial News")
        
        with st.spinner("Loading financial news..."):
            # Get financial news data
            news_data = data_service.get_financial_news()
            
            if not news_data:
                st.warning("No financial news available. Check API connections.")
            else:
                # Display recent news with sentiment analysis
                for i, news in enumerate(news_data[:5]):  # Display top 5 news items
                    title = news.get('title', 'No title available')
                    source = news.get('source', 'Unknown source')
                    url = news.get('url', '#')
                    sentiment = news.get('sentiment', 'neutral')
                    keyword = news.get('keyword', '')
                    
                    # Determine sentiment color
                    if sentiment == 'positive':
                        sentiment_color = 'green'
                        sentiment_icon = '📈'
                    elif sentiment == 'negative':
                        sentiment_color = 'red'
                        sentiment_icon = '📉'
                    else:
                        sentiment_color = 'gray'
                        sentiment_icon = '📊'
                    
                    # Create expandable news item
                    with st.expander(f"{sentiment_icon} {title}"):
                        st.markdown(f"**Source:** {source}")
                        st.markdown(f"**Matched Keyword:** {keyword}")
                        st.markdown(f"**Sentiment:** <span style='color: {sentiment_color};'>{sentiment.upper()}</span>", unsafe_allow_html=True)
                        st.markdown(f"[Read full article]({url})")
                        
                        # Add description if available
                        description = news.get('description', '')
                        if description:
                            st.markdown("---")
                            st.markdown(description)
        
        # AI-powered market interpretation
        st.subheader("AI Market Interpretation")
        
        # Simulate AI interpretation based on available data
        try:
            # Get various data points to form an interpretation
            treasury_data = data_service.get_treasury_yields()
            market_breadth = data_service.get_market_breadth()
            futures_data = data_service.get_futures_fair_value()
            
            # Check if we have enough data for an interpretation
            if treasury_data and market_breadth and futures_data:
                # Extract key metrics
                spread_2y_10y = treasury_data.get("2Y_10Y_spread")
                vix = market_breadth.get("VIX")
                options_status = market_breadth.get("Options_Status")
                premium_discount = futures_data.get("Premium_Discount")
                risk_status = futures_data.get("Risk_Status")
                
                # Generate AI interpretation
                interpretation = ""
                
                # Yield curve interpretation
                if spread_2y_10y is not None:
                    if spread_2y_10y < 0:
                        interpretation += "The yield curve remains inverted (2Y > 10Y), historically a recession signal. "
                        interpretation += "This environment typically favors defensive positioning. "
                    elif spread_2y_10y < 0.5:
                        interpretation += "The yield curve is relatively flat, suggesting economic uncertainty. "
                        interpretation += "Markets may be anticipating a slowdown in growth. "
                    else:
                        interpretation += "The yield curve has a positive slope, generally indicating healthy economic expectations. "
                
                # Volatility interpretation
                if vix is not None:
                    if vix > 30:
                        interpretation += "Elevated VIX levels indicate significant market fear and uncertainty. "
                        interpretation += "Historically, such periods eventually present buying opportunities, though timing is crucial. "
                    elif vix < 15:
                        interpretation += "Low VIX readings suggest market complacency. "
                        interpretation += "Historically, this can precede market corrections when combined with stretched valuations. "
                    else:
                        interpretation += "VIX is at moderate levels, suggesting balanced market sentiment. "
                
                # Options pricing interpretation
                if options_status:
                    if options_status == "Expensive":
                        interpretation += "Options appear overpriced relative to historical volatility, "
                        interpretation += "potentially favoring option selling strategies for income generation. "
                    elif options_status == "Cheap":
                        interpretation += "Options appear underpriced relative to historical volatility, "
                        interpretation += "potentially favoring option buying strategies to capture anticipated moves. "
                
                # Risk status interpretation
                if risk_status:
                    if risk_status == "Risk-On":
                        interpretation += "Overall market signals indicate risk appetite, potentially favoring equities and risk assets. "
                    elif risk_status == "Risk-Off":
                        interpretation += "Overall market signals indicate risk aversion, potentially favoring safer assets like bonds and gold. "
                    else:
                        interpretation += "Market signals are mixed, with no clear risk bias evident. "
                
                # Display interpretation
                st.info(interpretation)
                
                # Sentiment gauge
                sentiment_score = 0
                
                # Calculate sentiment score based on available metrics
                if spread_2y_10y is not None:
                    sentiment_score += (0.5 if spread_2y_10y > 0 else -0.5)
                
                if vix is not None:
                    sentiment_score += (0.5 if vix < 20 else -0.5)
                
                if options_status:
                    sentiment_score += (0.5 if options_status == "Cheap" else (-0.5 if options_status == "Expensive" else 0))
                
                if risk_status:
                    sentiment_score += (1 if risk_status == "Risk-On" else (-1 if risk_status == "Risk-Off" else 0))
                
                # Normalize to range [-100, 100]
                normalized_score = min(max(sentiment_score * 33, -100), 100)
                
                # Create a gauge chart for sentiment
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=normalized_score,
                    title={"text": "Market Sentiment Index"},
                    gauge={
                        "axis": {"range": [-100, 100]},
                        "bar": {"color": "darkblue"},
                        "steps": [
                            {"range": [-100, -60], "color": "red"},
                            {"range": [-60, -20], "color": "orange"},
                            {"range": [-20, 20], "color": "lightgray"},
                            {"range": [20, 60], "color": "lightgreen"},
                            {"range": [60, 100], "color": "green"}
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
                st.warning("Insufficient data for market interpretation. Check data connections.")
        except Exception as e:
            st.error(f"Error generating market interpretation: {e}")
    
    # Options Skew Analysis Tab
    with tab2:
        st.subheader("Options Skew Analysis")
        
        # Get market breadth data for skew analysis
        market_breadth = data_service.get_market_breadth()
        
        if not market_breadth:
            st.error("Unable to fetch market data for skew analysis. Check API connections.")
        else:
            # Get SKEW index
            skew = market_breadth.get("SKEW")
            
            if skew is not None:
                # Display SKEW index
                st.metric("CBOE SKEW Index", f"{skew:.2f}")
                
                # Create a visual representation of the skew
                # This is a simplified visualization - in production would use actual options data
                st.subheader("Visualized Put/Call Skew")
                
                # Create a normal distribution
                strikes = np.linspace(3500, 4500, 100)  # Example strike range
                
                # Create a skewed distribution based on SKEW value
                # Higher SKEW = more weight on the left tail (puts)
                skew_factor = (skew - 100) / 50  # Normalize to a usable factor
                
                # Base option prices (conceptual, not actual)
                atm_strike = 4000  # Example ATM strike
                
                # Generate option prices with skew
                call_prices = []
                put_prices = []
                
                for strike in strikes:
                    # Distance from ATM
                    distance = (strike - atm_strike) / atm_strike
                    
                    # Call prices decrease as strikes increase
                    # Put prices increase as strikes decrease
                    if distance < 0:  # Put side
                        # Puts get more expensive with higher skew
                        put_skew_adj = 1 + (abs(distance) * skew_factor)
                        put_prices.append(max(0, 50 * (abs(distance) * put_skew_adj)))
                        call_prices.append(max(0, 50 * (1 - abs(distance))))
                    else:  # Call side
                        put_prices.append(max(0, 50 * abs(distance)))
                        # Calls get less expensive with higher skew (relatively)
                        call_skew_adj = 1 - (distance * skew_factor * 0.5)  # Less impact than puts
                        call_prices.append(max(0, 50 * (1 - distance) * call_skew_adj))
                
                # Create the chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=strikes,
                    y=put_prices,
                    mode='lines',
                    name='Put Prices',
                    line=dict(color='red', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=strikes,
                    y=call_prices,
                    mode='lines',
                    name='Call Prices',
                    line=dict(color='green', width=2)
                ))
                
                # Add vertical line at ATM strike
                fig.add_vline(
                    x=atm_strike, 
                    line_width=1, 
                    line_dash="dash", 
                    line_color="black",
                    annotation_text="ATM Strike"
                )
                
                fig.update_layout(
                    title="Conceptual Options Pricing Skew",
                    xaxis_title="Strike Price",
                    yaxis_title="Option Premium",
                    template="plotly_white",
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=10, r=10, t=40, b=10)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Skew interpretation
                st.subheader("Skew Interpretation")
                
                if skew > 150:
                    st.markdown("""
                    <div style="background-color: #FFCCCC; padding: 10px; border-radius: 5px;">
                        <strong style="color: #990000;">EXTREMELY ELEVATED SKEW</strong>
                        <p>The options market is pricing in significant tail risk (black swan events). 
                        Out-of-the-money puts are unusually expensive relative to calls, indicating 
                        strong demand for downside protection.</p>
                    </div>
                    """, unsafe_allow_html=True)
                elif skew > 135:
                    st.markdown("""
                    <div style="background-color: #FFEECC; padding: 10px; border-radius: 5px;">
                        <strong style="color: #CC6600;">ELEVATED SKEW</strong>
                        <p>The options market is showing increased concern about downside risk. 
                        Out-of-the-money puts are trading at a premium, reflecting hedging demand.</p>
                    </div>
                    """, unsafe_allow_html=True)
                elif skew > 120:
                    st.markdown("""
                    <div style="background-color: #EEEEFF; padding: 10px; border-radius: 5px;">
                        <strong style="color: #000099;">NORMAL SKEW</strong>
                        <p>The options market is showing typical levels of put premium relative to calls, 
                        indicating balanced sentiment about tail risks.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background-color: #CCFFCC; padding: 10px; border-radius: 5px;">
                        <strong style="color: #009900;">LOW SKEW</strong>
                        <p>The options market is showing unusually low concern about downside risk. 
                        Out-of-the-money puts are relatively inexpensive, potentially indicating complacency.</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.error("SKEW data unavailable")
    
    # Explanation section
    with st.expander("About Macro Interpretation & Skew Analysis"):
        st.markdown("""
        **Macro News Interpretation**
        
        This section uses natural language processing to analyze financial news headlines and extract market sentiment. 
        The system focuses on high-impact keywords related to monetary policy, economic data, and market events.
        
        News items are categorized by sentiment (positive, negative, or neutral) based on keyword analysis and contextual understanding.
        
        **Options Skew Analysis**
        
        Options skew refers to the difference in implied volatility (IV) between out-of-the-money (OTM) puts and calls:
        
        - **Normal Skew**: OTM puts have higher IV than OTM calls, reflecting the typical market concern about downside protection
        - **Elevated Skew**: Unusually high premium for downside protection, indicating heightened fear
        - **Low Skew**: Minimal difference between put and call IV, potentially indicating complacency
        
        The CBOE SKEW Index quantifies this relationship, with readings above 150 indicating extreme tail risk concerns.
        
        **Market Sentiment Index**
        
        This gauge combines multiple market indicators to present an overall market sentiment reading:
        
        - Yield curve positioning
        - Volatility levels
        - Options pricing
        - Risk appetite measures
        
        Positive readings indicate bullish sentiment, while negative readings suggest bearish sentiment.
        """)
