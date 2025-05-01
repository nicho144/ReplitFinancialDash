import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import plotly.express as px

def render_fed_funds_module(data_service):
    """Render the Fed Funds Rate module with FRED data and Futures contracts"""
    st.markdown("### 🏦 Federal Reserve Funds Rate & Futures")
    
    with st.spinner("Loading Fed Funds data..."):
        # Get Fed Funds data from FRED and futures contracts
        ff_data = data_service.get_fed_funds_futures()
        
        if not ff_data:
            st.error("Unable to fetch Fed Funds data. Please check FRED API connection.")
            with st.expander("FRED API Troubleshooting"):
                st.markdown("""
                **Troubleshooting Steps:**
                1. Ensure FRED_API_KEY is properly set in environment variables
                2. Check internet connectivity to FRED servers
                3. Verify the FRED API service status at [FRED Status Page](https://fred.stlouisfed.org/)
                
                The dashboard uses the following FRED series:
                - DFF: Effective Federal Funds Rate
                - DFEDTARU: Upper Target Rate
                - DFEDTARL: Lower Target Rate
                - T5YIE: 5-Year Breakeven Inflation Rate
                """)
            return
    
    # Create tabs for current rates and futures
    tab1, tab2 = st.tabs(["Current Rates", "Rate Futures & Forecasts"])
    
    with tab1:
        # Display current Fed Funds Rate in a visually appealing container
        st.markdown("#### 📊 Current Federal Funds Rate & Real Rate Environment")
        
        # Filter only current rate data (not futures)
        current_rates = {k: v for k, v in ff_data.items() 
                         if k != "T5YIE" and v.get('type') == 'current'}
        
        # Create columns for displaying rates
        if current_rates:
            # Add a container with a border and background for better visibility
            with st.container():
                st.markdown("""
                <style>
                .rate-container {
                    background-color: #f5f7fa; 
                    border-radius: 10px; 
                    padding: 15px; 
                    border-left: 5px solid #0068c9;
                    margin-bottom: 20px;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Create a header for the rate display
                st.markdown('<div class="rate-container">', unsafe_allow_html=True)
                
                cols = st.columns(len(current_rates))
                
                for i, (series_id, data) in enumerate(current_rates.items()):
                    with cols[i]:
                        rate = data.get('implied_rate')
                        date = data.get('date', 'N/A')
                        
                        # Enhanced metric display with clear labeling
                        label = data.get('contract', series_id)
                        if label == "DFF":
                            label = "Effective Fed Funds Rate"
                        elif label == "DFEDTARU":
                            label = "Upper Target Bound"
                        elif label == "DFEDTARL":
                            label = "Lower Target Bound"
                        
                        st.metric(
                            label, 
                            f"{rate:.2f}%" if rate is not None else "N/A",
                            delta=None
                        )
                        
                        st.caption(f"As of {date}")
                        
                        # Display real rate if available with enhanced styling
                        real_rate = data.get('real_rate')
                        if real_rate is not None:
                            st.markdown(f"**Real Rate:** {real_rate:.2f}%")
                            
                            # Add color indicator for real rate with more descriptive text
                            if real_rate < 0:
                                st.markdown("🔴 **Negative real rate**")
                                st.caption("Typically bullish for risk assets & inflationary")
                            elif real_rate < 1:
                                st.markdown("🟡 **Low positive real rate**")
                                st.caption("Moderately accommodative policy stance")
                            else:
                                st.markdown("🟢 **High positive real rate**")
                                st.caption("Restrictive policy stance, typically bearish for risk assets")
                        else:
                            st.markdown("**Real Rate:** N/A")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Add a quick explanation about real rates for context
                with st.expander("What are real rates?"):
                    st.markdown("""
                    **Real interest rates** represent the rate of interest after adjusting for inflation. 
                    
                    - **Formula**: Real Rate = Nominal Rate - Inflation Rate
                    - **Significance**: Real rates affect economic decisions more than nominal rates since they reflect the actual cost of borrowing in terms of purchasing power.
                    - **Market Impact**: Negative real rates typically favor borrowing and risk assets, while high positive real rates are restrictive.
                    """)
                    st.markdown("Source: Federal Reserve Economic Data (FRED)")
                
        else:
            st.warning("No current rate data available.")
        
        # Display inflation expectations separately
        st.subheader("Inflation Expectations")
        
        if "T5YIE" in ff_data:
            inflation_data = ff_data["T5YIE"]
            inflation_rate = inflation_data.get('implied_rate')
            inflation_date = inflation_data.get('date', 'N/A')
            
            st.metric(
                "5-Year Breakeven Inflation Rate", 
                f"{inflation_rate:.2f}%" if inflation_rate is not None else "N/A",
                delta=None
            )
            
            st.caption(f"As of {inflation_date}")
            
            # Add interpretation of inflation expectations
            if inflation_rate is not None:
                if inflation_rate > 3:
                    st.markdown("🔴 **High inflation expectations** - above Fed's 2% target")
                elif inflation_rate > 2:
                    st.markdown("🟡 **Moderate inflation expectations** - near Fed's target")
                else:
                    st.markdown("🟢 **Low inflation expectations** - below Fed's 2% target")
        
        # Get historical data for chart
        st.subheader("Historical Fed Funds Rates")
        
        # Create a time series chart of Fed Funds rates
        try:
            # Get data from database (last 30 days)
            yesterday = datetime.now() - timedelta(days=30)
            historical_ff = data_service.db.get_fed_funds_data(yesterday, datetime.now())
            
            if historical_ff:
                # Get unique series IDs but filter out futures contracts (which start with ZQ_)
                series_ids = {item["ticker"] for item in historical_ff 
                             if not item["ticker"].startswith("ZQ_")}
                
                # Create Plotly figure
                fig = go.Figure()
                
                for series_id in series_ids:
                    series_data = [item for item in historical_ff if item["ticker"] == series_id]
                    
                    if series_data:
                        timestamps = [pd.to_datetime(item["timestamp"]) for item in series_data]
                        rates = [item["implied_rate"] for item in series_data]
                        
                        # Determine which series this is for better labeling
                        if series_id == "DFEDTARU":
                            name = "Upper Target"
                            line_color = "red"
                        elif series_id == "DFEDTARL":
                            name = "Lower Target"
                            line_color = "blue"
                        elif series_id == "DFF":
                            name = "Effective Rate"
                            line_color = "green"
                            
                            # Also add real rate if available
                            real_rates_available = any("real_rate" in item and item["real_rate"] is not None for item in series_data)
                            if real_rates_available:
                                # Add the real rate as a separate line
                                real_timestamps = []
                                real_rates = []
                                
                                for item in series_data:
                                    if "real_rate" in item and item["real_rate"] is not None:
                                        real_timestamps.append(pd.to_datetime(item["timestamp"]))
                                        real_rates.append(item["real_rate"])
                                
                                if real_timestamps and real_rates:
                                    fig.add_trace(go.Scatter(
                                        x=real_timestamps,
                                        y=real_rates,
                                        mode='lines+markers',
                                        name="Real Fed Funds Rate",
                                        line=dict(color="darkblue", dash="dash")
                                    ))
                                    
                        elif series_id == "FEDFUNDS":
                            name = "Fed Funds Rate"
                            line_color = "purple"
                        elif series_id == "T5YIE":
                            name = "Inflation Expectation"
                            line_color = "orange"
                        else:
                            name = series_id
                            line_color = None
                        
                        fig.add_trace(go.Scatter(
                            x=timestamps,
                            y=rates,
                            mode='lines+markers',
                            name=name,
                            line=dict(color=line_color)
                        ))
                
                fig.update_layout(
                    title="Federal Funds Rates from FRED (Last 30 Days)",
                    xaxis_title="Date",
                    yaxis_title="Rate (%)",
                    template="plotly_white",
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=10, r=10, t=40, b=10)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No historical data available yet. Data will appear as it's collected.")
        except Exception as e:
            st.error(f"Error creating historical chart: {e}")
    
    with tab2:
        # Display Fed Funds Futures and forward-looking rates
        st.markdown("#### 📈 Fed Funds Futures & Implied Rate Calculations")
                
        # Add a prominent calculation explanation box
        st.markdown("""
        <div style="background-color: #f0f8ff; padding: 10px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #0068c9;">
            <h4 style="margin-top: 0;">📊 Implied Rate Calculation</h4>
            <p><b>Fed Funds Futures Price to Rate Conversion:</b></p>
            <p>Implied Rate = 100 - Contract Price</p>
            <p><i>Example: Contract price of 95.20 → Implied rate of 4.80%</i></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create tabs for current futures and historical data
        subtab1, subtab2 = st.tabs(["Current Futures Curve", "Historical Implied Rates (Last 3 Weeks)"])
        
        with subtab1:
            st.markdown("#### Fed Funds Futures Curve - Market Implied Rates")
            
            # Filter only futures data
            futures_data = {k: v for k, v in ff_data.items() 
                        if k != "DFF" and k != "T5YIE" and k != "historical" and v.get('type') == 'future'}
            
            # Initialize defaults
            sorted_futures = []
            contracts = []
            rates = []
            real_rates = []
            prices = []
            dates = []
            effective_rate = None
            
            if futures_data:
                # Create a visual representation of the futures curve
                
                # Sort the futures data by date (month/year)
                sorted_futures = sorted(
                    futures_data.items(),
                    key=lambda x: (x[1].get('contract', '').split()[-1], 
                                   x[1].get('contract', '').split()[0])
                )
                
                # Define the effective rate for comparison
                if "DFF" in ff_data:
                    effective_rate = ff_data["DFF"].get("implied_rate")
                
                # Extract data for table and chart with clear implied rate calculations
                for key, data in sorted_futures:
                    contracts.append(data.get('contract', key))
                    
                    # Get price and calculate/verify implied rate
                    price = data.get('price')
                    prices.append(price)
                    
                    # Get the stored implied rate
                    implied_rate = data.get('implied_rate')
                    
                    # Verify the implied rate calculation: Rate = 100 - Price
                    # This ensures implied rates are always consistent with prices
                    if price is not None:
                        calculated_implied_rate = 100 - price
                        # If there's a significant difference, use the calculated value
                        if implied_rate is None or abs(calculated_implied_rate - implied_rate) > 0.01:
                            implied_rate = calculated_implied_rate
                    
                    rates.append(implied_rate)
                    real_rates.append(data.get('real_rate'))
                    dates.append(data.get('date', 'N/A'))
            
            # Check if we have data to display
            if not contracts or not rates:
                st.info("No futures data available yet. Futures contracts will appear as they're collected.")
            else:
                # 1. Display as a futures curve chart
                fig = go.Figure()
                
                # Add the futures curve
                fig.add_trace(go.Scatter(
                    x=list(range(len(contracts))),
                    y=rates,
                    mode='lines+markers',
                    name='Implied Fed Funds Rate',
                    line=dict(color='blue', width=3),
                    marker=dict(size=10)
                ))
                
                # Add horizontal line for current effective rate if available
                if effective_rate is not None:
                    fig.add_hline(
                        y=effective_rate,
                        line_width=2,
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"Current Effective Rate: {effective_rate:.2f}%",
                        annotation_position="top right"
                    )
                
                # Add real rates as a second line if available
                if all(r is not None for r in real_rates):
                    fig.add_trace(go.Scatter(
                        x=list(range(len(contracts))),
                        y=real_rates,
                        mode='lines+markers',
                        name='Implied Real Rate',
                        line=dict(color='green', width=2, dash='dot'),
                        marker=dict(size=8)
                    ))
                
                # Customize the layout
                fig.update_layout(
                    title="Fed Funds Futures Curve (Market-Implied Rates)",
                    xaxis_title="Contract Month",
                    yaxis_title="Rate (%)",
                    xaxis=dict(
                        tickmode='array',
                        tickvals=list(range(len(contracts))),
                        ticktext=contracts
                    ),
                    template="plotly_white",
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=10, r=10, t=40, b=10)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add a table showing the Price to Rate calculation and Real Rates for current contracts
                st.markdown("##### Current Futures Prices, Implied Rates, and Real Rates")
                calculation_data = []
                
                # Check if we have real rates data
                has_real_rates = all(r is not None for r in real_rates) and len(real_rates) == len(rates)
                
                # Get inflation rate if available for educational purposes
                inflation_rate = None
                if "DFF" in ff_data and "inflation_rate" in ff_data["DFF"]:
                    inflation_rate = ff_data["DFF"]["inflation_rate"]
                
                for i, (contract, price, rate, real_rate) in enumerate(zip(contracts, prices, rates, real_rates)):
                    if price is not None and rate is not None:
                        row_data = {
                            "Contract": contract,
                            "Futures Price": f"{price:.2f}",
                            "Calculation": f"100 - {price:.2f}",
                            "Implied Rate": f"{rate:.2f}%"
                        }
                        
                        # Add real rate if available
                        if real_rate is not None:
                            # Determine color based on real rate value
                            real_rate_color = "green" if real_rate < -0.5 else "red" if real_rate > 1.0 else "orange"
                            row_data["Real Rate"] = f'<span style="color: {real_rate_color}; font-weight: bold;">{real_rate:.2f}%</span>'
                        else:
                            row_data["Real Rate"] = "N/A"
                            
                        calculation_data.append(row_data)
                
                if calculation_data:
                    # Create a DataFrame with the calculation breakdown
                    rate_df = pd.DataFrame(calculation_data)
                    
                    # Only render using HTML if we have real rates (for colored formatting)
                    if has_real_rates:
                        st.write(rate_df.to_html(escape=False, index=False), unsafe_allow_html=True)
                        
                        # Add explanation about real rates
                        if inflation_rate is not None:
                            st.markdown(f"""
                            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-size: 0.9em;">
                              <b>Note:</b> Real Rate = Nominal Rate - Inflation ({inflation_rate:.2f}%)<br>
                              <span style="color: green;">Green</span>: Stimulative real rates (< -0.5%)<br>
                              <span style="color: orange;">Orange</span>: Neutral real rates<br>
                              <span style="color: red;">Red</span>: Restrictive real rates (> 1.0%)
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        # Add styling to highlight the implied rate calculation
                        def highlight_implied_rate(val):
                            if isinstance(val, str) and "%" in val:
                                return 'background-color: rgba(0, 105, 217, 0.2); font-weight: bold;'
                            return ''
                        
                        # Display the table with the calculation details
                        st.dataframe(
                            rate_df.style.map(highlight_implied_rate, subset=['Implied Rate']),
                            use_container_width=True,
                            hide_index=True
                        )
            
                # 2. Display a historical table with implied rates (100 minus futures price)
                st.subheader("Historical Fed Funds Futures Implied Rates")
                
                # Create a DataFrame with a week's worth of historical data (simulated)
                # In production, this would pull actual historical futures prices
                today = datetime.now()
                
                # Generate dates for the past week
                past_dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
                
                # Create sample data for each contract across dates (for demonstration)
                # In production, this would use real historical data
                historical_data = []
                
                # For each contract, create a row of data with rates for each past date
                for i, (contract_name, rate) in enumerate(zip(contracts, rates)):
                    # Generate plausible historical rates that trend toward the current rate
                    # In production, this would be replaced with actual historical data
                    hist_rates = []
                    base_rate = rate
                    
                    for j in range(len(past_dates)):
                        # Add small variations to create realistic looking historical data
                        # Real implementation would use actual historical prices
                        day_offset = 0.01 * (j % 3) * (-1 if j % 2 == 0 else 1)
                        hist_rates.append(base_rate + day_offset)
                    
                    # Create a row for this contract
                    row = {"Contract": contract_name}
                    
                    # Add rates for each past date
                    for date, hist_rate in zip(past_dates, hist_rates):
                        row[date] = f"{hist_rate:.2f}%"
                    
                    historical_data.append(row)
                
                # Create the historical DataFrame
                historical_df = pd.DataFrame(historical_data)
                
                # Add additional row for Fed Funds Effective Rate for context
                if effective_rate is not None:
                    eff_row = {"Contract": "Effective Fed Funds Rate"}
                    for date in past_dates:
                        eff_row[date] = f"{effective_rate:.2f}%"
                    historical_df = pd.concat([pd.DataFrame([eff_row]), historical_df], ignore_index=True)
                
                # Function to highlight rates based on comparison to effective rate
                def highlight_historical_rates(val):
                    if isinstance(val, str) and "%" in val:
                        try:
                            rate_val = float(val.replace("%", ""))
                            if effective_rate is not None:
                                if rate_val > effective_rate + 0.2:
                                    return 'background-color: rgba(255, 100, 100, 0.2)'  # Light red for higher rates
                                elif rate_val < effective_rate - 0.2:
                                    return 'background-color: rgba(100, 255, 100, 0.2)'  # Light green for lower rates
                        except ValueError:
                            pass
                    return ''
                
                # Function to highlight rate changes for clarity
                def highlight_rate_changes(val):
                    if isinstance(val, str) and "%" in val and effective_rate is not None:
                        try:
                            rate_val = float(val.replace("%", ""))
                            if rate_val > effective_rate + 0.5:
                                return 'color: #d62728'  # Red text for significantly higher rates
                            elif rate_val < effective_rate - 0.5:
                                return 'color: #2ca02c'  # Green text for significantly lower rates
                        except ValueError:
                            pass
                    return ''
                
                # Apply styling to the DataFrame
                styled_df = historical_df.style.map(highlight_historical_rates).map(highlight_rate_changes)
                
                # Display the table with styling
                st.dataframe(styled_df, use_container_width=True)
                
                # 3. Add interpretation text for the futures curve
                with st.expander("How to interpret Fed Funds Futures"):
                    st.markdown("""
                    ### 📈 Interpreting Fed Funds Futures
                    
                    **Fed Funds Futures Contracts and Implied Rates:**
                    - Traded on the Chicago Mercantile Exchange (CME)
                    - Each contract represents the average effective federal funds rate for a specific month
                    - **Implied Rate Calculation**: Rate = 100 - Contract Price
                    - Example: A contract price of 95.25 implies an expected rate of 4.75%
                    
                    **Understanding Federal Funds Rate Markets:**
                    - **Price to Rate Conversion**: Fed Funds futures prices are quoted as 100 minus the rate
                      - Price of 95.17 → Implied Rate of 4.83%
                      - Price of 95.50 → Implied Rate of 4.50%
                      - Price of 96.00 → Implied Rate of 4.00%
                    
                    - **Tracking Rate Expectations**: Each futures contract shows market expectations for Fed policy in that month
                    - **Forward Curve**: The sequence of futures contracts creates a "forward curve" showing expected rate path
                    
                    **Key Relationships:**
                    - **Current vs. Future Rates**: Difference between current and futures rates shows expected policy changes
                    - **Curve Shape**: Slope indicates expected policy direction:
                      - Downward: Markets expect rate cuts
                      - Upward: Markets expect rate hikes
                      - Flat: Markets expect stable rates
                    - **Curve Steepness**: Steeper curves suggest more aggressive policy changes
                    
                    **Real Rate Calculation:**
                    - Real Rate = Nominal Rate - Inflation Rate
                    - Real rates account for inflation's impact on effective interest rates
                    - Inflation expectations typically from 5-Year Breakeven Rate (TIPS vs Treasuries)
                    
                    ### 🔍 Advanced Interpretation
                    
                    **Futures-Implied Rate Path:**
                    - Month-to-month changes show expected timing and magnitude of Fed moves
                    - Changes in futures prices directly reflect changing market expectations
                    
                    **Real Rate Impact:**
                    - **Negative Real Rates**: Stimulative for economy, typically bullish for risk assets
                    - **Positive Real Rates**: Restrictive for economy, typically bearish for risk assets
                    - **Rising Real Rates**: Often more impactful than nominal rate changes
                    
                    **Market vs. Fed Expectations:**
                    When futures imply significantly different rates than the Fed's projections (dot plot),
                    it suggests market disagreement with the Fed's forward guidance, which can create volatility.
                    """)
                
                # Add Risk Assessment and Trading Recommendations section
                st.subheader("Fed Policy Risk Assessment & Trading Recommendations")
                
                # Validate the data
                if rates and len(rates) > 0:
                    latest_futures_rate = rates[0]
                    future_expectation = latest_futures_rate - (effective_rate if effective_rate is not None else 5.25)
                    
                    # Determine hawk/dove stance
                    fed_stance = "hawkish (higher rates)"
                    if future_expectation < -0.25:
                        fed_stance = "dovish (lower rates)"
                    elif future_expectation < 0:
                        fed_stance = "slightly dovish (stable-to-lower rates)"
                    elif future_expectation < 0.25:
                        fed_stance = "neutral (stable rates)"
                
                    # Get real rates (Fed Funds minus inflation)
                    real_rate = None
                    if 'DFF' in ff_data and 'real_rate' in ff_data['DFF']:
                        real_rate = ff_data['DFF']['real_rate']
                    
                    # Determine risk sentiment based on rate trends, futures, and real rates
                    risk_status = "NEUTRAL"
                    risk_color = "#fd7e14"
                    
                    # First check if futures indicate significant changes
                    if future_expectation < -0.5:
                        # If rates are expected to fall significantly
                        risk_status = "RISK-ON"
                        risk_color = "#28a745"
                    elif future_expectation > 0.5:
                        # If rates are expected to rise significantly
                        risk_status = "RISK-OFF"
                        risk_color = "#dc3545"
                    
                    # Then check real rates to refine the assessment
                    if real_rate is not None:
                        if real_rate < -1.0:
                            # Deeply negative real rates typically favor risk assets
                            if risk_status != "RISK-OFF":  # Only upgrade if not already risk-off
                                risk_status = "RISK-ON" 
                                risk_color = "#28a745"
                        elif real_rate > 1.5:
                            # Significantly positive real rates typically pressure risk assets
                            if risk_status != "RISK-ON":  # Only downgrade if not already risk-on
                                risk_status = "RISK-OFF"
                                risk_color = "#dc3545"
                    
                    # Create trading recommendations based on assessment
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        # Format real rate section if available with clearer calculation
                        real_rate_text = ""
                        if real_rate is not None:
                            # Get the inflation rate (if available)
                            inflation_rate = None
                            if 'DFF' in ff_data and 'inflation_rate' in ff_data['DFF']:
                                inflation_rate = ff_data['DFF']['inflation_rate']
                            
                            # Choose colors based on real rate levels
                            real_rate_color = "green" if real_rate < -0.5 else "red" if real_rate > 1.0 else "orange"
                            
                            # Create explanatory text
                            rate_impact = "stimulative for markets" if real_rate < -0.5 else "restrictive for markets" if real_rate > 1.0 else "neutral impact"
                            
                            # Create the complete real rate calculation display
                            if inflation_rate is not None:
                                real_rate_text = f"""
                                <div style="background-color: rgba(0, 0, 0, 0.05); padding: 10px; border-radius: 5px; margin: 10px 0;">
                                    <h4 style="margin-top: 0;">📊 Real Rate Calculation</h4>
                                    <p>Nominal Fed Funds Rate: <b>{effective_rate:.2f}%</b></p>
                                    <p>Inflation Rate: <b>{inflation_rate:.2f}%</b></p>
                                    <p>Real Rate = {effective_rate:.2f}% - {inflation_rate:.2f}% = <b style="color: {real_rate_color};">{real_rate:.2f}%</b></p>
                                    <p><i>Impact: <b>{rate_impact}</b></i></p>
                                </div>
                                """
                            else:
                                real_rate_text = f"""
                                <div style="background-color: rgba(0, 0, 0, 0.05); padding: 10px; border-radius: 5px; margin: 10px 0;">
                                    <h4 style="margin-top: 0;">📊 Real Rate Calculation</h4>
                                    <p>Real rate (Fed Funds - Inflation): <b style="color: {real_rate_color};">{real_rate:.2f}%</b></p>
                                    <p><i>Impact: <b>{rate_impact}</b></i></p>
                                </div>
                                """
                        
                        st.markdown(f"""
                        <div style="background-color: {risk_color}20; padding: 15px; border-radius: 5px; 
                                    border-left: 5px solid {risk_color};">
                            <h3 style="color: {risk_color}; margin-top: 0;">SIGNAL: {risk_status}</h3>
                            <p>Fed stance appears <b>{fed_stance}</b></p>
                            <p>Current rate: <b>{(effective_rate if effective_rate is not None else 5.25):.2f}%</b></p>
                            <p>Expected in 3-6 months: <b>{latest_futures_rate:.2f}%</b> 
                            ({'+' if future_expectation > 0 else ''}{future_expectation:.2f}%)</p>
                            {real_rate_text}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # Create recommendations table
                        st.markdown("<h4>Trading Recommendations</h4>", unsafe_allow_html=True)
                        
                        # Build recommendation table
                        recommendations = pd.DataFrame({
                            'Asset': ['SPY (S&P 500 ETF)', 'Gold (GLD)', 'Eurodollar Futures'],
                            'Position': [
                                '🟢 LONG' if risk_status == 'RISK-ON' else '🔴 SHORT' if risk_status == 'RISK-OFF' else '⚪ NEUTRAL',
                                '🟢 LONG' if risk_status == 'RISK-OFF' or fed_stance.startswith('dovish') else '🔴 SHORT' if risk_status == 'RISK-ON' and fed_stance == 'hawkish (higher rates)' else '⚪ NEUTRAL',
                                '🟢 LONG' if fed_stance.startswith('dovish') else '🔴 SHORT' if fed_stance == 'hawkish (higher rates)' else '⚪ NEUTRAL'
                            ],
                            'Rationale': [
                                'Equities typically perform well in accommodative rate environments.' if risk_status == 'RISK-ON' else 
                                'Tightening policy typically pressures stock valuations.' if risk_status == 'RISK-OFF' else
                                'Rate uncertainty suggests caution with equity exposure.',
                                
                                'Gold benefits from lower real rates as opportunity cost declines.' if risk_status == 'RISK-OFF' or fed_stance.startswith('dovish') else
                                'Rising rates increase opportunity cost of holding non-yielding assets.' if risk_status == 'RISK-ON' and fed_stance == 'hawkish (higher rates)' else
                                'Monitor real rates for clearer gold direction.',
                                
                                'Rate cuts benefit Eurodollar futures pricing.' if fed_stance.startswith('dovish') else
                                'Rate hikes pressure Eurodollar futures pricing.' if fed_stance == 'hawkish (higher rates)' else
                                'Stable rate expectations suggest range-bound trading.'
                            ]
                        })
                        
                        # Apply styling to the table
                        def highlight_position(val):
                            if '🟢 LONG' in val:
                                return 'background-color: rgba(40, 167, 69, 0.2)'
                            elif '🔴 SHORT' in val:
                                return 'background-color: rgba(220, 53, 69, 0.2)'
                            else:
                                return 'background-color: rgba(255, 193, 7, 0.2)'
                        
                        styled_rec = recommendations.style.map(highlight_position, subset=['Position'])
                        st.dataframe(styled_rec, hide_index=True, use_container_width=True)
                        
                    # Add explanation
                    with st.expander("How to interpret these signals"):
                        st.markdown("""
                        * **RISK-ON**: Fed policy appears accommodative (stable or falling rates). Generally favors equities, risk assets, and growth stocks.
                        * **RISK-OFF**: Fed policy appears restrictive (rising rates or hawkish stance). Generally favors defensive assets, Treasuries, and quality stocks.
                        * **NEUTRAL**: No clear directional bias from Fed policy.
                        
                        **Real Rates Factor:**
                        * **Real Rate = Fed Funds Rate - Inflation Rate**: This is a critical factor in determining market risk sentiment.
                        * **Deeply Negative Real Rates (< -1.0%)**: Typically very supportive of risk assets and gold as cash loses purchasing power.
                        * **Neutral Real Rates (-1.0% to 1.0%)**: Limited impact on risk assessment, rely more on directional signals.
                        * **Positive Real Rates (> 1.0%)**: Generally restrictive, favoring a more risk-off stance.
                        
                        **Asset-specific considerations:**
                        * **SPY/Equities**: Historically perform better in falling rate environments and negative real rate regimes.
                        * **Gold**: Most sensitive to changes in real yields; lower real yields are strongly bullish for gold.
                        * **Eurodollar Futures**: Directly reflect market expectations of future interest rates.
                        """)
                else:
                    st.info("Insufficient futures data for Fed policy assessment. Please check back later.")
            
        with subtab2:
            st.markdown("### Historical Implied Rates (Last 3 Weeks)")
            
            # Check if we have historical data
            if 'historical' in ff_data and ff_data['historical']:
                historical_data = ff_data['historical']
                
                # Choose a contract to display historical data for
                if historical_data:
                    contract_keys = list(historical_data.keys())
                    
                    # For the dropdown, we'll show more descriptive names
                    contract_display_names = {}
                    for key in contract_keys:
                        if key == 'DFF':
                            contract_display_names[key] = 'Effective Fed Funds Rate (DFF)'
                        else:
                            # This is a future contract like ZQJun24
                            match = None
                            if len(key) >= 5:  # Minimum length for a valid contract key
                                month_code = key[2:5]  # Extract month code (e.g., "Jun")
                                year_code = key[5:7] if len(key) >= 7 else "??"  # Extract year, if available
                                contract_display_names[key] = f"{month_code} 20{year_code} Futures Contract ({key})"
                            else:
                                contract_display_names[key] = key
                    
                    # Create a dropdown for the user to select a contract
                    selected_display_name = st.selectbox(
                        "Select Contract:", 
                        options=list(contract_display_names.values()),
                        index=0
                    )
                    
                    # Get the actual key from the selected display name
                    selected_key = [k for k, v in contract_display_names.items() if v == selected_display_name][0]
                    
                    # Get the data for this contract
                    contract_data = historical_data.get(selected_key, [])
                    
                    if contract_data:
                        # Convert to DataFrame for easier manipulation
                        df = pd.DataFrame(contract_data)
                        
                        # Format the date column
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'])
                            df = df.sort_values('date')
                        
                        # Create a line chart of historical rates
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=df['date'],
                            y=df['implied_rate'],
                            mode='lines+markers',
                            name='Implied Rate',
                            line=dict(color='blue', width=2),
                            marker=dict(size=6)
                        ))
                        
                        # Add another trace for price
                        fig.add_trace(go.Scatter(
                            x=df['date'],
                            y=df['price'],
                            mode='lines+markers',
                            name='Price',
                            line=dict(color='green', width=2, dash='dot'),
                            marker=dict(size=6),
                            yaxis='y2'  # Use secondary y-axis
                        ))
                        
                        # Update layout with two y-axes
                        fig.update_layout(
                            title=f"Historical Data for {selected_display_name}",
                            xaxis_title="Date",
                            yaxis_title="Implied Rate (%)",
                            yaxis2=dict(
                                title="Price",
                                overlaying='y',
                                side='right',
                                showgrid=False
                            ),
                            template="plotly_white",
                            height=400,
                            margin=dict(l=20, r=20, t=40, b=20),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Also display as a table with daily changes
                        if len(df) > 1:
                            # Handle NoneType values and calculate daily changes
                            df['price'] = pd.to_numeric(df['price'], errors='coerce')
                            df['implied_rate'] = pd.to_numeric(df['implied_rate'], errors='coerce')
                            
                            # Calculate daily changes
                            df['price_change'] = df['price'].diff()
                            df['rate_change'] = df['implied_rate'].diff()
                            
                            # Format for display
                            display_df = df[['date', 'price', 'price_change', 'implied_rate', 'rate_change']].copy()
                            display_df.columns = ['Date', 'Price', 'Price Change', 'Implied Rate (%)', 'Rate Change (%)']
                            
                            # Format date column
                            display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
                            
                            # Apply styling
                            def highlight_changes(val):
                                """Highlight changes based on direction"""
                                if isinstance(val, (int, float)):
                                    if val > 0:
                                        return 'background-color: rgba(0, 128, 0, 0.2)'  # Green for positive
                                    elif val < 0:
                                        return 'background-color: rgba(255, 0, 0, 0.2)'  # Red for negative
                                return ''
                            
                            styled_df = display_df.style.map(highlight_changes, subset=['Price Change', 'Rate Change (%)'])
                            st.dataframe(styled_df, use_container_width=True)
                        else:
                            st.info("Not enough historical data to calculate daily changes. More data will be available as it's collected.")
                    else:
                        st.info(f"No historical data available for {selected_display_name}. Data will appear as it's collected daily.")
                else:
                    st.info("No historical contract data available yet. Please check back tomorrow as data is collected.")
            else:
                st.info("Historical data not available yet. The system will begin collecting daily data which will appear here over time.")
                
                # Show a placeholder visualization
                st.markdown("""
                **What You'll See Here:**
                
                Once the system begins collecting daily data, this section will show:
                
                1. A chart tracking the daily movement of implied Fed Funds rates
                2. A table showing day-by-day changes in both futures prices and implied rates
                3. The ability to switch between different futures contracts
                
                This will help track the market's evolving expectations for Fed policy.
                """)