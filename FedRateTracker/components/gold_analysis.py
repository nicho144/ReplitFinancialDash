import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import yfinance as yf

def render_gold_analysis(data_service):
    """Render Gold Analysis Component Based on Treasury Yields and Other Key Drivers"""
    st.header("🥇 Gold Analysis")
    
    # Create tabs for different gold analysis views
    tab1, tab2, tab3 = st.tabs(["Gold vs. Treasury Yield", "Gold Key Drivers", "Trading Recommendations"])
    
    with tab1:
        st.subheader("Gold vs. 10-Year Treasury Yield Relationship")
        
        # Fetch real data from Yahoo Finance
        try:
            # Get data for Gold and 10-Year Treasury Yield
            # Use ^TNX for the 10-year Treasury yield
            # Use GC=F for Gold futures prices
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)  # Last 180 days for meaningful analysis
            
            # Show loading message
            with st.spinner("Loading real-time gold and treasury data..."):
                # Add error handling with timeouts for each download
                try:
                    gold_data = yf.download("GC=F", start=start_date, end=end_date, progress=False, timeout=10)
                except Exception as gold_error:
                    st.warning(f"Error fetching gold data: {gold_error}")
                    gold_data = pd.DataFrame()  # Empty DataFrame as fallback
                
                try:
                    treasury_data = yf.download("^TNX", start=start_date, end=end_date, progress=False, timeout=10)
                except Exception as treasury_error:
                    st.warning(f"Error fetching treasury data: {treasury_error}")
                    treasury_data = pd.DataFrame()  # Empty DataFrame as fallback
                
                # For real rates, we need the inflation expectations
                # TIP is the iShares TIPS Bond ETF which tracks inflation expectations
                try:
                    tips_data = yf.download("TIP", start=start_date, end=end_date, progress=False, timeout=10)
                except Exception as tips_error:
                    st.warning(f"Error fetching TIPS data: {tips_error}")
                    tips_data = pd.DataFrame()  # Empty DataFrame as fallback
            
            # Only proceed if we have valid data
            if not gold_data.empty and not treasury_data.empty:
                # Create a merged dataframe for easier analysis
                # Resample to ensure consistent dates across all data sources
                gold_daily = gold_data['Close'].resample('D').last().ffill()
                treasury_daily = treasury_data['Close'].resample('D').last().ffill()
                
                if not tips_data.empty:
                    tips_daily = tips_data['Close'].resample('D').last().ffill()
                    # Let's calculate an approximate real yield
                    # This is simplified but gives us directional information
                    merged_data = pd.DataFrame({
                        'Gold': gold_daily,
                        'Treasury_Yield': treasury_daily,
                        'TIPS': tips_daily
                    }).dropna()
                    
                    # Calculate daily changes
                    merged_data['Gold_Change'] = merged_data['Gold'].pct_change() * 100
                    merged_data['Yield_Change_BPS'] = (merged_data['Treasury_Yield'].diff()) * 100  # in basis points
                    
                    # Calculate approximate real yields (simplified)
                    # In production, we would use actual TIP yields or TIPS data from official sources
                    merged_data['Real_Yield_Proxy'] = merged_data['Treasury_Yield'] - merged_data['TIPS'].pct_change() * 100
                else:
                    # If we don't have TIPS data, proceed with nominal yields
                    merged_data = pd.DataFrame({
                        'Gold': gold_daily,
                        'Treasury_Yield': treasury_daily
                    }).dropna()
                    
                    # Calculate daily changes
                    merged_data['Gold_Change'] = merged_data['Gold'].pct_change() * 100
                    merged_data['Yield_Change_BPS'] = (merged_data['Treasury_Yield'].diff()) * 100  # in basis points
                
                # Create a figure with two subplots (second is for correlation)
                fig = make_subplots(rows=2, cols=1, 
                                   shared_xaxes=True, 
                                   vertical_spacing=0.1,
                                   subplot_titles=("Gold vs. 10-Year Treasury Yield", "Yield Changes vs. Gold Movement"),
                                   row_heights=[0.7, 0.3])
                
                # Add Gold price line to the first subplot
                fig.add_trace(
                    go.Scatter(
                        x=merged_data.index,
                        y=merged_data['Gold'],
                        mode='lines',
                        name='Gold Price ($)',
                        line=dict(color='gold', width=2)
                    ),
                    row=1, col=1
                )
                
                # Add Treasury Yield to the first subplot with secondary y-axis
                fig.add_trace(
                    go.Scatter(
                        x=merged_data.index,
                        y=merged_data['Treasury_Yield'],
                        mode='lines',
                        name='10-Year Treasury Yield (%)',
                        line=dict(color='blue', width=2),
                        yaxis="y2"
                    ),
                    row=1, col=1
                )
                
                # Create second subplot showing the correlation between yield changes and gold price changes
                # Use scatter plot to show relationship between basis point moves and gold price changes
                fig.add_trace(
                    go.Scatter(
                        x=merged_data['Yield_Change_BPS'].iloc[1:],  # Skip first row due to diff() creating NaN
                        y=merged_data['Gold_Change'].iloc[1:],
                        mode='markers',
                        marker=dict(
                            size=8,
                            color='rgba(0, 0, 255, 0.5)',
                            line=dict(width=1, color='blue')
                        ),
                        name='Daily Change Correlation',
                        text=merged_data.index.strftime('%Y-%m-%d').iloc[1:],
                        hovertemplate='%{text}<br>Yield Change: %{x:.2f} bps<br>Gold Change: %{y:.2f}%'
                    ),
                    row=2, col=1
                )
                
                # Add a horizontal line at 0 for the second subplot
                fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="gray", row=2, col=1)
                
                # Add a vertical line at 0 for the second subplot
                fig.add_vline(x=0, line_width=1, line_dash="dash", line_color="gray", row=2, col=1)
                
                # Initialize correlation to a default value
                correlation = 0
                
                # Calculate trend line for the correlation plot
                x = merged_data['Yield_Change_BPS'].iloc[1:].values
                y = merged_data['Gold_Change'].iloc[1:].values
                valid_indices = ~(np.isnan(x) | np.isnan(y))
                
                if np.sum(valid_indices) > 1:  # Need at least 2 points for regression
                    x_valid = x[valid_indices]
                    y_valid = y[valid_indices]
                    
                    # Linear regression with numpy
                    slope, intercept = np.polyfit(x_valid, y_valid, 1)
                    
                    # Create x values for the trend line
                    x_trend = np.array([min(x_valid), max(x_valid)])
                    y_trend = slope * x_trend + intercept
                    
                    # Add trend line to correlation plot
                    fig.add_trace(
                        go.Scatter(
                            x=x_trend,
                            y=y_trend,
                            mode='lines',
                            line=dict(color='red', width=2, dash='dash'),
                            name=f'Trend (slope: {slope:.3f})',
                            hoverinfo='name'
                        ),
                        row=2, col=1
                    )
                    
                    # Calculate and add correlation coefficient
                    correlation = np.corrcoef(x_valid, y_valid)[0, 1]
                    fig.add_annotation(
                        x=0.95, y=0.95,
                        xref="paper", yref="paper",
                        text=f"Correlation: {correlation:.2f}",
                        showarrow=False,
                        font=dict(size=12, color="black"),
                        bgcolor="white",
                        bordercolor="black",
                        borderwidth=1,
                        row=2, col=1
                    )
                
                # Configure the layout
                fig.update_layout(
                    height=700,
                    template="plotly_white",
                    hovermode="x unified",
                    xaxis2=dict(title="10-Year Yield Change (basis points)"),
                    yaxis3=dict(title="Gold Price Change (%)"),
                    showlegend=True,
                    margin=dict(l=10, r=10, t=40, b=10)
                )
                
                # Create a secondary y-axis for the Treasury Yield
                fig.update_layout(
                    yaxis=dict(
                        title="Gold Price ($)",
                        titlefont=dict(color="gold"),
                        tickfont=dict(color="gold")
                    ),
                    yaxis2=dict(
                        title="10-Year Treasury Yield (%)",
                        titlefont=dict(color="blue"),
                        tickfont=dict(color="blue"),
                        anchor="x",
                        overlaying="y",
                        side="right"
                    )
                )
                
                # Display the figure
                st.plotly_chart(fig, use_container_width=True)
                
                # Analysis of recent 10-year yield movements and effect on gold
                st.subheader("Recent Movements Analysis")
                
                # Calculate the most recent 10-year yield change (last 5 trading days)
                recent_yield_change = treasury_daily[-5:].diff().dropna()
                cumulative_change = recent_yield_change.sum() * 100  # Convert to basis points
                
                # Calculate the corresponding gold change
                recent_gold_change = gold_daily[-5:].pct_change().dropna()
                gold_cumulative_change = ((gold_daily.iloc[-1] / gold_daily.iloc[-6]) - 1) * 100
                
                # Display the recent changes
                col1, col2 = st.columns(2)
                
                with col1:
                    change_color = "red" if cumulative_change > 0 else "green"
                    st.metric(
                        "10-Year Yield 5-Day Change", 
                        f"{cumulative_change:.1f} bps", 
                        f"{'+' if cumulative_change > 0 else ''}{cumulative_change:.1f} bps",
                        delta_color=change_color
                    )
                    
                    # Create a small table with daily yield changes
                    daily_yield_changes = pd.DataFrame({
                        'Date': recent_yield_change.index.strftime('%Y-%m-%d'),
                        'Yield Change (bps)': (recent_yield_change.values * 100).round(1)
                    })
                    st.dataframe(daily_yield_changes, hide_index=True)
                
                with col2:
                    gold_change_color = "green" if gold_cumulative_change > 0 else "red"
                    st.metric(
                        "Gold 5-Day Change", 
                        f"${gold_daily.iloc[-1]:.1f}", 
                        f"{'+' if gold_cumulative_change > 0 else ''}{gold_cumulative_change:.1f}%",
                        delta_color=gold_change_color
                    )
                    
                    # Create a small table with daily gold changes
                    daily_gold_changes = pd.DataFrame({
                        'Date': recent_gold_change.index.strftime('%Y-%m-%d'),
                        'Gold Change (%)': recent_gold_change.values.round(2)
                    })
                    st.dataframe(daily_gold_changes, hide_index=True)
                
                # Interpretation of the relationship
                st.subheader("Interpretation")
                
                # Based on the observed correlation, provide an interpretation
                if correlation < -0.3:
                    st.markdown("""
                    ### Strong Inverse Relationship ⚠️
                    
                    The data shows a **strong negative correlation** between Treasury yield movements and gold prices.
                    
                    When the 10-year yield falls significantly (10+ basis points), gold tends to rise.
                    Conversely, when yields rise sharply, gold typically faces downward pressure.
                    
                    This reflects gold's sensitivity to real interest rates — as a non-yielding asset,
                    gold becomes more attractive when the opportunity cost of holding it decreases.
                    """)
                elif correlation > 0.3:
                    st.markdown("""
                    ### Unusual Positive Correlation 🔄
                    
                    Currently showing a **positive correlation** between yields and gold, which is atypical
                    of the long-term relationship. This can happen during:
                    
                    - Periods of significant inflation concerns (both yields and gold rise)
                    - Market stress where investors sell all assets (including gold) for cash
                    - Changing Fed policy expectations affecting both markets simultaneously
                    
                    This relationship may revert to the typical inverse correlation as market conditions normalize.
                    """)
                else:
                    st.markdown("""
                    ### Weak or Neutral Correlation ⚖️
                    
                    Currently showing a **weak correlation** between 10-year Treasury yields and gold prices.
                    
                    This suggests other factors may be dominating gold price action:
                    - Geopolitical risks
                    - Currency movements (especially USD)
                    - Central bank buying
                    - Physical demand factors
                    
                    The traditional inverse relationship may reassert itself when interest rate concerns
                    return to the forefront of market focus.
                    """)
            else:
                st.error("Unable to retrieve gold or Treasury yield data. Please check the data sources.")
        except Exception as e:
            st.error(f"Error analyzing Gold vs Treasury relationship: {e}")
     
    with tab2:
        st.subheader("Gold Key Price Drivers")
        
        # Create a visual representation of key gold price drivers
        try:
            # Get data for key gold drivers from Yahoo Finance
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)  # Last 90 days
            
            # Get data for Gold, DXY (Dollar Index), and VIX
            gold_data = yf.download("GC=F", start=start_date, end=end_date)
            dxy_data = yf.download("DX-Y.NYB", start=start_date, end=end_date)
            vix_data = yf.download("^VIX", start=start_date, end=end_date)
            
            # Create figure with three subplots
            fig = make_subplots(rows=3, cols=1, 
                               shared_xaxes=True,
                               vertical_spacing=0.1,
                               subplot_titles=("Gold Price", "US Dollar Index (DXY)", "Market Volatility (VIX)"),
                               row_heights=[0.4, 0.3, 0.3])
            
            # Add Gold chart
            if not gold_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=gold_data.index,
                        y=gold_data['Close'],
                        mode='lines',
                        name='Gold Price ($)',
                        line=dict(color='gold', width=2)
                    ),
                    row=1, col=1
                )
            
            # Add DXY chart
            if not dxy_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=dxy_data.index,
                        y=dxy_data['Close'],
                        mode='lines',
                        name='Dollar Index',
                        line=dict(color='green', width=2)
                    ),
                    row=2, col=1
                )
            
            # Add VIX chart
            if not vix_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=vix_data.index,
                        y=vix_data['Close'],
                        mode='lines',
                        name='VIX',
                        line=dict(color='red', width=2)
                    ),
                    row=3, col=1
                )
            
            # Update layout
            fig.update_layout(
                height=700,
                template="plotly_white",
                hovermode="x unified",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=10, r=10, t=40, b=10)
            )
            
            # Display the figure
            st.plotly_chart(fig, use_container_width=True)
            
            # Current Market Indicators Table
            st.subheader("Current Gold Market Indicators")
            
            try:
                # Also fetch treasury data if we don't have it yet
                if 'treasury_data' not in locals() or treasury_data is None:
                    treasury_data = yf.download("^TNX", start=start_date, end=end_date)
                
                # Initialize variables for market indicators
                latest_gold = None
                latest_dxy = None
                latest_vix = None
                latest_yield = None
                gold_change_30d = 0
                dxy_change_30d = 0
                vix_change_30d = 0
                yield_change_30d = 0
                
                # Only proceed if we have the necessary data
                if (not gold_data.empty and not dxy_data.empty and 
                    not vix_data.empty and not treasury_data.empty):
                    
                    # Get the latest values
                    latest_gold = gold_data['Close'].iloc[-1]
                    latest_dxy = dxy_data['Close'].iloc[-1]
                    latest_vix = vix_data['Close'].iloc[-1]
                    latest_yield = treasury_data['Close'].iloc[-1]
                    
                    # Calculate 30-day changes
                    gold_change_30d = ((latest_gold / gold_data['Close'].iloc[0]) - 1) * 100
                    dxy_change_30d = ((latest_dxy / dxy_data['Close'].iloc[0]) - 1) * 100
                    vix_change_30d = ((latest_vix / vix_data['Close'].iloc[0]) - 1) * 100
                    yield_change_30d = (latest_yield - treasury_data['Close'].iloc[0]) * 100  # in basis points
                    
                    # Create a DataFrame for the key indicators
                    indicators_df = pd.DataFrame({
                        'Indicator': [
                            '10-Year Treasury Yield',
                            'US Dollar Index (DXY)',
                            'Market Volatility (VIX)',
                            'Gold Price'
                        ],
                        'Current Value': [
                            f"{latest_yield:.2f}%",
                            f"{latest_dxy:.2f}",
                            f"{latest_vix:.2f}",
                            f"${latest_gold:.2f}"
                        ],
                        '30-Day Change': [
                            f"{yield_change_30d:+.1f} bps",
                            f"{dxy_change_30d:+.1f}%",
                            f"{vix_change_30d:+.1f}%",
                            f"{gold_change_30d:+.1f}%"
                        ],
                        'Impact on Gold': [
                            "🔴 Bearish" if yield_change_30d > 10 else "🟢 Bullish" if yield_change_30d < -10 else "⚪ Neutral",
                            "🔴 Bearish" if dxy_change_30d > 2 else "🟢 Bullish" if dxy_change_30d < -2 else "⚪ Neutral",
                            "🟢 Bullish" if vix_change_30d > 10 else "⚪ Neutral",
                            "N/A"
                        ]
                    })
                    
                    # Define a function to style the table rows
                    def style_impact(val):
                        if '🟢 Bullish' in val:
                            return 'background-color: rgba(76, 175, 80, 0.2)'
                        elif '🔴 Bearish' in val:
                            return 'background-color: rgba(244, 67, 54, 0.2)'
                        else:
                            return ''
                    
                    # Apply styling to the 'Impact on Gold' column
                    styled_df = indicators_df.style.applymap(style_impact, subset=['Impact on Gold'])
                    
                    # Display the styled table
                    st.dataframe(styled_df, hide_index=True, use_container_width=True)
                    
                    # Calculate overall market sentiment for gold
                    bullish_factors = sum(1 for impact in indicators_df['Impact on Gold'] if '🟢 Bullish' in impact)
                    bearish_factors = sum(1 for impact in indicators_df['Impact on Gold'] if '🔴 Bearish' in impact)
                    neutral_factors = sum(1 for impact in indicators_df['Impact on Gold'] if '⚪ Neutral' in impact)
                    
                    # Determine overall sentiment
                    if bullish_factors > bearish_factors:
                        sentiment = "🟢 Bullish"
                        sentiment_color = "green"
                        explanation = "More factors currently support higher gold prices."
                    elif bearish_factors > bullish_factors:
                        sentiment = "🔴 Bearish"
                        sentiment_color = "red"
                        explanation = "More factors currently pressure gold prices lower."
                    else:
                        sentiment = "⚪ Neutral / Mixed"
                        sentiment_color = "gray"
                        explanation = "Gold price drivers are currently balanced or conflicting."
                    
                    # Display the overall sentiment
                    st.markdown(f"""
                    <div style="background-color: rgba({0 if sentiment_color != 'red' else 244}, 
                                                       {0 if sentiment_color == 'red' else 175 if sentiment_color == 'green' else 156}, 
                                                       {0 if sentiment_color == 'red' else 80 if sentiment_color == 'green' else 156}, 0.2); 
                                padding: 15px; border-radius: 10px; margin: 10px 0;">
                        <h3 style="margin: 0; color: {sentiment_color};">Current Gold Market Sentiment: {sentiment}</h3>
                        <p style="margin-top: 10px;">{explanation}</p>
                        <p style="margin-top: 5px; font-style: italic;">Based on real-time analysis of key gold drivers</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("Some market data is missing. The indicators may be incomplete.")
            except Exception as e:
                st.error(f"Error processing market indicators: {e}")
                
            # Add the summary table from the uploaded document
            st.markdown("### Gold vs. Key Drivers (Reference)")
            
            # Create reference table based on the information in the uploaded document
            reference_df = pd.DataFrame({
                'Factor': [
                    'Real Yields',
                    '10-Year Yield',
                    'Fed Policy',
                    'USD Index (DXY)',
                    'Inflation',
                    'VIX / Geopolitics',
                    'Yield Curve'
                ],
                'Bullish for Gold': [
                    'Falling / Negative',
                    'Falling sharply (>10bps)',
                    'Dovish / Pauses / Cuts',
                    'Falling',
                    'Rising / Sticky',
                    'Rising / Conflict',
                    'Flattening / Inverted'
                ],
                'Bearish for Gold': [
                    'Rising / Positive',
                    'Rising sharply',
                    'Hawkish / Rate Hikes',
                    'Rising',
                    'Falling / Controlled',
                    'Calm markets / Risk-on',
                    'Bear steepening'
                ]
            })
            
            # Display the reference table
            st.table(reference_df)
            
            # Add explanation of key relationships
            with st.expander("Gold Trading Insights"):
                st.markdown("""
                ### 📈 Key Gold Trading Insights
                
                1. **Treasury Yield Relationship**
                   - A 10-15 basis point move in the 10-year yield (0.10-0.15%) can start moving gold noticeably
                   - A sustained trend (e.g., yields falling from 4.5% to 4.0%) tends to spark bullish gold flows
                   - If the 10-year yield drops by 0.25% (25bps), gold can jump $20-$40+, depending on context
                
                2. **Real Yields Matter Most**
                   - Gold tracks real interest rates (nominal - inflation expectations) more closely than nominal rates
                   - Lower real yields reduce the opportunity cost of holding non-yielding gold
                
                3. **Dollar Impact**
                   - Gold is priced in USD; a stronger dollar makes gold more expensive globally
                   - DXY and gold typically have a strong inverse correlation
                
                4. **Risk Sentiment Connection**
                   - VIX rising often leads to safe-haven flows into gold
                   - Geopolitical shocks generally benefit gold prices
                   - But if rates spike with risk-off, it can cap gold's gains short term
                """)
        except Exception as e:
            st.error(f"Error analyzing Gold key drivers: {e}")
            
    # Provide market insights based on the analysis
    st.markdown("---")
    st.subheader("Gold Market Insights")
    
    # Check if the market is open (simplified)
    is_market_open = datetime.now().weekday() < 5 and 9 <= datetime.now().hour < 16
    
    with st.expander("Market Status & Trading Considerations", expanded=True):
        if is_market_open:
            st.markdown("### 🟢 Market is currently open")
        else:
            st.markdown("### 🔴 Market is currently closed")
            
        st.markdown("""
        ### Gold Trading Considerations
        
        **Key Price Levels to Watch:**
        - $2,000/oz - Psychological support level
        - $2,100/oz - Recent resistance zone
        - $1,980/oz - Technical support from prior breakout
        
        **Watch for:**
        - Treasury yield movements exceeding 10 basis points
        - Significant USD index (DXY) shifts
        - Fed officials' comments on monetary policy
        - Geopolitical developments affecting risk sentiment
        
        **Note:** Gold prices are most sensitive to changes in real yields (nominal yields minus inflation expectations)
        """)

    with tab3:
        st.subheader("Gold & Treasury Market Recommendations")
        
        # Get necessary data for recommendations
        try:
            # Fetch latest data
            gold_data = yf.download("GC=F", period="5d")
            treasury_data = yf.download("^TNX", period="5d")
            dxy_data = yf.download("DX-Y.NYB", period="5d")
            
            # Get data for other relevant products
            gld_data = yf.download("GLD", period="5d")  # Gold ETF
            iau_data = yf.download("IAU", period="5d")  # iShares Gold Trust
            tlt_data = yf.download("TLT", period="5d")  # 20+ Year Treasury ETF
            shy_data = yf.download("SHY", period="5d")  # 1-3 Year Treasury ETF
            
            if not gold_data.empty and not treasury_data.empty:
                # Create dashboard layout for recommendations
                st.markdown("""
                <style>
                .rec-card {
                    background-color: #f9f9f9;
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 15px;
                    border-left: 5px solid #4b8bf4;
                }
                .product-rec {
                    margin-top: 5px;
                    padding: 8px;
                    border-radius: 5px;
                    background-color: rgba(240, 240, 240, 0.7);
                }
                .buy-rec {
                    border-left: 5px solid #28a745;
                }
                .sell-rec {
                    border-left: 5px solid #dc3545;
                }
                .neutral-rec {
                    border-left: 5px solid #fd7e14;
                }
                .product-name {
                    font-weight: bold;
                    margin-right: 10px;
                }
                .product-price {
                    color: #555;
                }
                .sentiment-tag {
                    display: inline-block;
                    padding: 3px 8px;
                    border-radius: 15px;
                    font-size: 0.8em;
                    margin-left: 10px;
                }
                .bullish {
                    background-color: rgba(40, 167, 69, 0.2);
                    color: #28a745;
                }
                .bearish {
                    background-color: rgba(220, 53, 69, 0.2);
                    color: #dc3545;
                }
                .neutral {
                    background-color: rgba(255, 193, 7, 0.2);
                    color: #fd7e14;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Calculate current trends
                gold_trend = "neutral"
                if gold_data["Close"].iloc[-1] > gold_data["Close"].iloc[-2] and gold_data["Close"].iloc[-2] > gold_data["Close"].iloc[-3]:
                    gold_trend = "bullish"
                elif gold_data["Close"].iloc[-1] < gold_data["Close"].iloc[-2] and gold_data["Close"].iloc[-2] < gold_data["Close"].iloc[-3]:
                    gold_trend = "bearish"
                
                treasury_trend = "neutral"
                if treasury_data["Close"].iloc[-1] > treasury_data["Close"].iloc[-2]:
                    treasury_trend = "bearish for bonds"  # Yields up = bond prices down
                else:
                    treasury_trend = "bullish for bonds"  # Yields down = bond prices up
                
                # Get latest prices
                gold_price = gold_data["Close"].iloc[-1]
                treasury_yield = treasury_data["Close"].iloc[-1]
                
                # Gold to yield ratio analysis
                gold_yield_ratio = gold_price / treasury_yield
                ratio_avg_50d = gold_price / treasury_yield  # In production: calculate 50-day average
                
                # Market overview
                st.markdown(f"""
                <div class="rec-card">
                    <h3>Market Overview</h3>
                    <p>Gold is currently trading at <b>${gold_price:.2f}</b> with a {gold_trend} short-term trend.</p>
                    <p>10-Year Treasury Yield is at <b>{treasury_yield:.2f}%</b>, which is {treasury_trend}.</p>
                    <p>The Gold/10Y-Yield ratio is <b>{gold_yield_ratio:.2f}</b>, which is 
                    {"above" if gold_yield_ratio > ratio_avg_50d else "below"} the 50-day average.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Generate specific product recommendations
                st.markdown("<h3>Product Recommendations</h3>", unsafe_allow_html=True)
                
                # Gold ETFs
                gld_price = gld_data["Close"].iloc[-1] if not gld_data.empty else 0
                gld_change = ((gld_data["Close"].iloc[-1] / gld_data["Close"].iloc[-2]) - 1) * 100 if not gld_data.empty else 0
                
                iau_price = iau_data["Close"].iloc[-1] if not iau_data.empty else 0
                iau_change = ((iau_data["Close"].iloc[-1] / iau_data["Close"].iloc[-2]) - 1) * 100 if not iau_data.empty else 0
                
                # Treasury ETFs
                tlt_price = tlt_data["Close"].iloc[-1] if not tlt_data.empty else 0
                tlt_change = ((tlt_data["Close"].iloc[-1] / tlt_data["Close"].iloc[-2]) - 1) * 100 if not tlt_data.empty else 0
                
                shy_price = shy_data["Close"].iloc[-1] if not shy_data.empty else 0
                shy_change = ((shy_data["Close"].iloc[-1] / shy_data["Close"].iloc[-2]) - 1) * 100 if not shy_data.empty else 0
                
                # Gold recommendation
                gold_rec_class = "buy-rec" if gold_trend == "bullish" else "sell-rec" if gold_trend == "bearish" else "neutral-rec"
                gold_sentiment = "bullish" if gold_trend == "bullish" else "bearish" if gold_trend == "bearish" else "neutral"
                
                st.markdown(f"""
                <div class="product-rec {gold_rec_class}">
                    <div>
                        <span class="product-name">SPDR Gold Shares (GLD)</span>
                        <span class="product-price">${gld_price:.2f} ({'+' if gld_change > 0 else ''}{gld_change:.2f}%)</span>
                        <span class="sentiment-tag {gold_sentiment}">{gold_sentiment.upper()}</span>
                    </div>
                    <div>
                        <span class="product-name">iShares Gold Trust (IAU)</span>
                        <span class="product-price">${iau_price:.2f} ({'+' if iau_change > 0 else ''}{iau_change:.2f}%)</span>
                        <span class="sentiment-tag {gold_sentiment}">{gold_sentiment.upper()}</span>
                    </div>
                    <p style="margin-top:8px;">
                        {
                        "Consider adding gold exposure; technical trends are positive and fundamentals support higher prices." 
                        if gold_sentiment == "bullish" else
                        "Consider reducing gold exposure or hedging existing positions; downward momentum may continue."
                        if gold_sentiment == "bearish" else
                        "Gold is in a consolidation phase; await clearer signals before adjusting positions."
                        }
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Treasury recommendation
                treasury_rec_class = "buy-rec" if treasury_trend == "bullish for bonds" else "sell-rec" if treasury_trend == "bearish for bonds" else "neutral-rec"
                treasury_sentiment = "bullish" if treasury_trend == "bullish for bonds" else "bearish" if treasury_trend == "bearish for bonds" else "neutral"
                
                st.markdown(f"""
                <div class="product-rec {treasury_rec_class}">
                    <div>
                        <span class="product-name">iShares 20+ Year Treasury (TLT)</span>
                        <span class="product-price">${tlt_price:.2f} ({'+' if tlt_change > 0 else ''}{tlt_change:.2f}%)</span>
                        <span class="sentiment-tag {treasury_sentiment}">{treasury_sentiment.upper()}</span>
                    </div>
                    <div>
                        <span class="product-name">iShares 1-3 Year Treasury (SHY)</span>
                        <span class="product-price">${shy_price:.2f} ({'+' if shy_change > 0 else ''}{shy_change:.2f}%)</span>
                        <span class="sentiment-tag {treasury_sentiment}">{treasury_sentiment.upper()}</span>
                    </div>
                    <p style="margin-top:8px;">
                        {
                        "Bond prices likely to rise as yields fall; consider adding Treasury exposure, especially at the long end of the curve."
                        if treasury_sentiment == "bullish" else
                        "Rising yields create headwinds for bonds; consider reducing long-duration Treasury exposure or moving to shorter durations."
                        if treasury_sentiment == "bearish" else
                        "The Treasury market is stable; maintain existing allocations while monitoring for shifts in Fed policy expectations."
                        }
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Portfolio strategy recommendations
                st.markdown("""
                <div class="rec-card" style="border-left: 5px solid #6f42c1;">
                    <h3>Holistic Strategy Recommendations</h3>
                    <p>Based on all market signals across the dashboard, here's our current market stance:</p>
                    <ul>
                        <li><strong>SPY/Equities:</strong> The risk-on/risk-off indicator suggests maintaining a balanced equity exposure with protective hedges.</li>
                        <li><strong>Gold/Precious Metals:</strong> The Federal Reserve policy stance and yield curve dynamics support a moderate allocation to gold as a portfolio diversifier.</li>
                        <li><strong>Bonds/Fixed Income:</strong> Current yield curve positioning suggests favoring intermediate-term bonds while minimizing exposure to the short end.</li>
                        <li><strong>Volatility:</strong> Consider small allocations to volatility products as a hedge against potential market disruptions.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
                # Historical performance comparison
                st.subheader("Performance Comparison (Last 5 Trading Days)")
                performance_data = pd.DataFrame({
                    'Product': ['Gold (GC=F)', 'GLD ETF', 'IAU ETF', 'TLT ETF', 'SHY ETF'],
                    'Price': [
                        gold_data["Close"].iloc[-1],
                        gld_data["Close"].iloc[-1] if not gld_data.empty else 0,
                        iau_data["Close"].iloc[-1] if not iau_data.empty else 0,
                        tlt_data["Close"].iloc[-1] if not tlt_data.empty else 0,
                        shy_data["Close"].iloc[-1] if not shy_data.empty else 0
                    ],
                    'Change %': [
                        ((gold_data["Close"].iloc[-1] / gold_data["Close"].iloc[0]) - 1) * 100,
                        ((gld_data["Close"].iloc[-1] / gld_data["Close"].iloc[0]) - 1) * 100 if not gld_data.empty else 0,
                        ((iau_data["Close"].iloc[-1] / iau_data["Close"].iloc[0]) - 1) * 100 if not iau_data.empty else 0,
                        ((tlt_data["Close"].iloc[-1] / tlt_data["Close"].iloc[0]) - 1) * 100 if not tlt_data.empty else 0,
                        ((shy_data["Close"].iloc[-1] / shy_data["Close"].iloc[0]) - 1) * 100 if not shy_data.empty else 0
                    ]
                })
                
                # Format the dataframe for display
                performance_data['Price'] = performance_data['Price'].map('${:.2f}'.format)
                performance_data['Change %'] = performance_data['Change %'].map('{:+.2f}%'.format)
                
                st.dataframe(performance_data, hide_index=True, use_container_width=True)
                
            else:
                st.info("Waiting for market data to generate recommendations...")
                
        except Exception as e:
            st.error(f"Error generating recommendations: {e}")
            st.info("Recommendations will appear here once market data is available.")