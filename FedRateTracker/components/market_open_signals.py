import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_market_signals(data_service):
    """Render the Market Open Signal Summary Panel"""
    st.header("3. Market Open Signal Summary")
    
    with st.spinner("Loading market open data..."):
        # Get market open signal data
        market_data = data_service.get_market_open_signals()
        
        if not market_data:
            st.error("Unable to fetch market open signal data. Please check API connections.")
            return
    
    # Create a summary panel with checkmarks
    market_assets = ["Gold Futures", "VIX", "US Dollar Index", "30Y Bond Futures"]
    
    # Create a styled dataframe to display the signals
    signal_data = []
    
    # Process each asset
    for asset in market_assets:
        if asset in market_data:
            direction = market_data[asset]["direction"]
            change_pct = market_data[asset].get("change_pct")
            
            # Format the percent change
            change_str = f"{change_pct:.2f}%" if change_pct is not None else "N/A"
            
            # Create signal row
            signal_data.append({
                "Asset": asset,
                "Direction": "✅ UP" if direction == "up" else "❌ DOWN",
                "Change": change_str
            })
    
    # Add Fed Funds row
    ff_changed = market_data.get("Fed Funds Changed", False)
    signal_data.append({
        "Asset": "Fed Funds Changed",
        "Direction": "✅ YES" if ff_changed else "❌ NO",
        "Change": "N/A"
    })
    
    # Display the signals in a table
    st.table(pd.DataFrame(signal_data))
    
    # Display color-coded summary boxes
    st.subheader("Visual Summary")
    
    cols = st.columns(len(signal_data))
    
    for i, signal in enumerate(signal_data):
        with cols[i]:
            asset = signal["Asset"]
            direction = signal["Direction"]
            
            # Determine color based on direction
            if "UP" in direction or "YES" in direction:
                color = "green"
            else:
                color = "red"
            
            # Display colored box with asset name
            st.markdown(
                f"""
                <div style="background-color: {color}; padding: 10px; border-radius: 5px; color: white; text-align: center;">
                    <strong>{asset}</strong>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Display detailed asset information
    st.subheader("Detailed Asset Performance")
    
    # Create tabs for each asset
    tabs = st.tabs([asset for asset in market_assets])
    
    for i, asset in enumerate(market_assets):
        with tabs[i]:
            if asset in market_data:
                data = market_data[asset]
                
                # Display metrics
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Previous Close", f"{data['prev_close']:.2f}")
                    
                with col2:
                    direction = "+" if data['direction'] == "up" else "-"
                    change_pct = data.get("change_pct")
                    change_str = f"{direction}{abs(change_pct):.2f}%" if change_pct is not None else "N/A"
                    
                    st.metric(
                        "Open", 
                        f"{data['open']:.2f}", 
                        delta=change_str
                    )
                
                # Display a mini chart if we have historical data
                try:
                    # Fetch a bit of historical data for context
                    ticker = data.get("ticker")
                    if ticker:
                        import yfinance as yf
                        
                        t = yf.Ticker(ticker)
                        hist = t.history(period="5d", interval="1h")
                        
                        if not hist.empty:
                            # Create a mini chart
                            fig = go.Figure()
                            
                            fig.add_trace(
                                go.Scatter(
                                    x=hist.index,
                                    y=hist['Close'],
                                    mode='lines',
                                    name='Price',
                                    line=dict(color='blue', width=2)
                                )
                            )
                            
                            fig.update_layout(
                                title=f"{asset} - Last 5 Days (Hourly)",
                                xaxis_title="Date",
                                yaxis_title="Price",
                                template="plotly_white",
                                height=300,
                                margin=dict(l=10, r=10, t=40, b=10)
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not load chart data: {e}")
            else:
                st.error(f"No data available for {asset}")
    
    # Display the Fed Funds Change information
    if "Fed Funds Changed" in market_data:
        with st.expander("Fed Funds Futures Details"):
            if market_data["Fed Funds Changed"]:
                st.success("Fed Funds Futures values have changed since yesterday, indicating a shift in interest rate expectations.")
            else:
                st.info("Fed Funds Futures values have not significantly changed since yesterday.")
    
    # Explanation of the signals
    with st.expander("About Market Open Signals"):
        st.markdown("""
        **Market Open Signal Summary**
        
        This panel shows whether key market indicators opened up or down compared to the previous day's close. These signals can provide early insights into market sentiment and potential trends:
        
        - **Gold Futures**: Often a barometer for inflation expectations and risk sentiment
        - **VIX (Volatility Index)**: Rising VIX indicates increased market uncertainty
        - **US Dollar Index**: Dollar strength affects global trade and commodity prices
        - **Bond Futures**: Treasury bond prices reflect interest rate expectations
        - **Fed Funds Changed**: Indicates whether market expectations for Federal Reserve policy have shifted
        
        The color-coded summary provides a quick visual reference of market conditions at open:
        - Green = Up/Yes
        - Red = Down/No
        
        These indicators are most useful when viewed together as a systemic snapshot of market conditions rather than in isolation.
        """)
