import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

def render_market_snapshot(data_service):
    """Render a comprehensive market snapshot with key metrics"""
    st.header("📊 Market Snapshot & Risk Monitor")
    
    # Add descriptive banner
    st.markdown("""
    <div style="background: linear-gradient(to right, #1a237e, #283593, #3949ab, #5c6bc0); 
                color: white; 
                padding: 20px; 
                border-radius: 10px; 
                margin-bottom: 20px;
                text-align: center;">
        <h2 style="margin: 0; padding: 0; color: white;">Market Intelligence Dashboard</h2>
        <p style="margin: 5px 0 0 0;">Comprehensive market data analysis to inform risk-on/risk-off decisions</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch required data from various sources
    fed_funds_data = data_service.get_fed_funds_futures()
    treasury_data = data_service.get_treasury_yields()
    breadth_data = data_service.get_market_breadth()
    market_signals = data_service.get_market_open_signals()
    
    # Create tabs for different market snapshot views
    tab1, tab2, tab3 = st.tabs(["Key Metrics Dashboard", "Visual Market Pulse", "Premarket Activity"])
    
    with tab1:
        # Create a grid layout for key metrics
        col1, col2, col3 = st.columns(3)
        
        # Column 1: Fed Funds Rate & Treasury Spreads
        with col1:
            st.subheader("Interest Rates")
            
            # Get current effective fed funds rate
            effective_rate = None
            if "DFF" in fed_funds_data:
                effective_rate = fed_funds_data["DFF"].get("implied_rate")
                
            if effective_rate is not None:
                # Display effective rate with appropriate styling
                st.metric(
                    "Fed Funds Rate",
                    f"{effective_rate:.2f}%",
                    delta=None
                )
                
                # Display real rate if available
                real_rate = fed_funds_data["DFF"].get("real_rate")
                if real_rate is not None:
                    st.metric(
                        "Real Rate",
                        f"{real_rate:.2f}%",
                        delta=None
                    )
            
            # Get treasury spreads
            spread_2y_10y = treasury_data.get("2Y_10Y_spread")
            spread_2y_5y = treasury_data.get("2Y_5Y_spread")
            
            if spread_2y_10y is not None:
                st.metric(
                    "2Y-10Y Spread",
                    f"{spread_2y_10y:.2f}%",
                    delta=None
                )
                
                # Add interpretation of yield curve inversion
                if spread_2y_10y < 0:
                    st.markdown("🚨 **Inverted yield curve**")
                elif spread_2y_10y < 0.5:
                    st.markdown("⚠️ **Flattening yield curve**")
                else:
                    st.markdown("✅ **Normal yield curve**")
        
        # Column 2: VIX & Volatility Metrics
        with col2:
            st.subheader("Volatility")
            
            # Get VIX and realized volatility data
            vix = breadth_data.get("VIX")
            realized_vol = breadth_data.get("Realized_Vol")
            vix_premium = breadth_data.get("VIX_Premium")
            
            if vix is not None:
                st.metric(
                    "VIX Index",
                    f"{vix:.2f}",
                    delta=None
                )
                
                # Add interpretation of VIX levels
                if vix > 30:
                    st.markdown("🚨 **High fear** - extreme volatility")
                elif vix > 20:
                    st.markdown("⚠️ **Elevated fear** - above avg volatility")
                else:
                    st.markdown("✅ **Low fear** - calm market")
            
            if vix is not None and realized_vol is not None and vix_premium is not None:
                st.metric(
                    "VIX Premium",
                    f"{vix_premium:.2f}",
                    delta=f"{vix_premium:.2f}"
                )
                
                # Add interpretation of VIX premium
                if vix_premium > 4:
                    st.markdown("📈 **High premium** - potential vol mean reversion")
                elif vix_premium < -2:
                    st.markdown("📉 **Negative premium** - unusual volatility pattern")
                else:
                    st.markdown("⚖️ **Normal premium** - volatility fairly priced")
        
        # Column 3: Expected Ranges for SPY/Market
        with col3:
            st.subheader("Expected Ranges")
            
            # Get expected range data
            daily_range = breadth_data.get("ATM_Expected_Daily_Range")
            weekly_range = breadth_data.get("ATM_Expected_Weekly_Range")
            daily_pct = breadth_data.get("ATM_Expected_Daily_Pct")
            weekly_pct = breadth_data.get("ATM_Expected_Weekly_Pct")
            
            if daily_range is not None and daily_pct is not None:
                st.metric(
                    "Expected Daily Range",
                    f"±{daily_range:.2f}",
                    delta=None
                )
                st.caption(f"±{daily_pct:.2f}% daily move implied by options")
            
            if weekly_range is not None and weekly_pct is not None:
                st.metric(
                    "Expected Weekly Range",
                    f"±{weekly_range:.2f}",
                    delta=None
                )
                st.caption(f"±{weekly_pct:.2f}% weekly move implied by options")
            
            # Display options status
            options_status = breadth_data.get("Options_Status")
            if options_status is not None:
                # Display with appropriate styling
                if options_status == "Expensive":
                    st.markdown("🔴 **Options Status: EXPENSIVE**")
                    st.caption("Consider option selling strategies")
                elif options_status == "Cheap":
                    st.markdown("🟢 **Options Status: CHEAP**")
                    st.caption("Consider option buying strategies")
                else:
                    st.markdown("⚪ **Options Status: FAIR VALUE**")
                    st.caption("Options fairly priced to historical vol")
    
    with tab2:
        # Create multi-panel visual dashboard with plotly
        try:
            # Create multiplot figure
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    "Fed Funds Rate vs 10Y Treasury", 
                    "VIX vs Realized Volatility",
                    "Treasury Yield Curve",
                    "Expected Price Ranges (SPY)"
                ),
                vertical_spacing=0.1,
                horizontal_spacing=0.05,
            )
            
            # Plot 1: Fed Funds Rate vs 10Y Treasury (shows monetary policy vs market reality)
            effective_rate = None
            if "DFF" in fed_funds_data:
                effective_rate = fed_funds_data["DFF"].get("implied_rate")
                
            treasury_10y = treasury_data.get("10Y")
            
            if effective_rate is not None and treasury_10y is not None:
                # Add FF rate as a horizontal line
                fig.add_trace(
                    go.Scatter(
                        x=[0, 30],  # x range
                        y=[effective_rate, effective_rate],
                        mode="lines",
                        name="Fed Funds Rate",
                        line=dict(color="red", width=2)
                    ),
                    row=1, col=1
                )
                
                # Add 10Y Treasury yield as a horizontal line
                fig.add_trace(
                    go.Scatter(
                        x=[0, 30],  # x range
                        y=[treasury_10y, treasury_10y],
                        mode="lines",
                        name="10Y Treasury Yield",
                        line=dict(color="blue", width=2)
                    ),
                    row=1, col=1
                )
                
                # Calculate spread
                spread = treasury_10y - effective_rate
                
                # Add spread as annotation
                fig.add_annotation(
                    x=15, y=max(effective_rate, treasury_10y) + 0.5,
                    text=f"Spread: {spread:.2f}%",
                    showarrow=False,
                    font=dict(size=14),
                    row=1, col=1
                )
            
            # Plot 2: VIX vs Realized Volatility
            vix = breadth_data.get("VIX")
            realized_vol = breadth_data.get("Realized_Vol")
            
            if vix is not None and realized_vol is not None:
                # Add VIX as a horizontal line
                fig.add_trace(
                    go.Scatter(
                        x=[0, 30],  # x range
                        y=[vix, vix],
                        mode="lines",
                        name="VIX (Implied Vol)",
                        line=dict(color="purple", width=2)
                    ),
                    row=1, col=2
                )
                
                # Add Realized Vol as a horizontal line
                fig.add_trace(
                    go.Scatter(
                        x=[0, 30],  # x range
                        y=[realized_vol, realized_vol],
                        mode="lines",
                        name="20-Day Realized Vol",
                        line=dict(color="green", width=2, dash="dash")
                    ),
                    row=1, col=2
                )
                
                # Calculate premium
                premium = vix - realized_vol
                
                # Add premium as annotation
                fig.add_annotation(
                    x=15, y=max(vix, realized_vol) + 2,
                    text=f"Premium: {premium:.2f}",
                    showarrow=False,
                    font=dict(size=14),
                    row=1, col=2
                )
            
            # Plot 3: Treasury Yield Curve
            maturities = ["13W", "2Y", "5Y", "10Y", "30Y"]
            yields = []
            
            for maturity in maturities:
                if maturity in treasury_data:
                    yields.append(treasury_data[maturity])
                else:
                    yields.append(None)
            
            if not all(y is None for y in yields):
                # Create x-axis labels for maturities
                x_values = list(range(len(maturities)))
                
                # Add yield curve line
                fig.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=yields,
                        mode="lines+markers",
                        name="Yield Curve",
                        line=dict(color="blue", width=3),
                        marker=dict(size=8)
                    ),
                    row=2, col=1
                )
                
                # Update x-axis ticks to show maturities
                fig.update_xaxes(
                    tickvals=x_values,
                    ticktext=maturities,
                    row=2, col=1
                )
            
            # Plot 4: Expected price ranges for SPY
            # Create a bar chart showing daily and weekly expected ranges
            daily_pct = breadth_data.get("ATM_Expected_Daily_Pct")
            weekly_pct = breadth_data.get("ATM_Expected_Weekly_Pct")
            
            if daily_pct is not None and weekly_pct is not None:
                # Create bars for both range types
                fig.add_trace(
                    go.Bar(
                        x=["Daily", "Weekly"],
                        y=[daily_pct, weekly_pct],
                        name="Expected Move (%)",
                        marker_color=["rgba(0, 128, 255, 0.7)", "rgba(255, 128, 0, 0.7)"]
                    ),
                    row=2, col=2
                )
                
                # Add text annotations on the bars
                fig.add_annotation(
                    x="Daily", y=daily_pct + 0.2,
                    text=f"±{daily_pct:.2f}%",
                    showarrow=False,
                    font=dict(size=14),
                    row=2, col=2
                )
                
                fig.add_annotation(
                    x="Weekly", y=weekly_pct + 0.2,
                    text=f"±{weekly_pct:.2f}%",
                    showarrow=False,
                    font=dict(size=14),
                    row=2, col=2
                )
            
            # Update layout for all subplots
            fig.update_layout(
                height=600,
                template="plotly_white",
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(l=10, r=10, t=60, b=10)
            )
            
            # Render the figure
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error creating market snapshot visualizations: {e}")
    
    with tab3:
        st.subheader("📈 Premarket Activity & Open Signals")
        
        # Check if we have market open signals data
        if market_signals:
            # Create a dataframe-style display of premarket moves
            st.markdown("### Key Assets - Premarket Changes")
            
            # Create columns for organizing the premarket data
            col1, col2 = st.columns(2)
            
            with col1:
                # Extract data for key instruments we care about
                instruments = ["Gold Futures", "VIX", "US Dollar Index", "30Y Bond Futures"]
                
                # Create a table showing the open direction and % change
                for instrument in instruments:
                    if instrument in market_signals:
                        data = market_signals[instrument]
                        direction = data.get("direction")
                        change_pct = data.get("change_pct")
                        
                        # Display with appropriate coloring based on direction
                        if direction == "up":
                            st.markdown(f"**{instrument}**: 🟢 **UP** {change_pct:.2f}%")
                        else:
                            st.markdown(f"**{instrument}**: 🔴 **DOWN** {change_pct:.2f}%")
                    else:
                        st.markdown(f"**{instrument}**: ⚪ Data unavailable")
                
                # Check if Fed Funds Futures values have changed
                ff_changed = market_signals.get("Fed Funds Changed", False)
                if ff_changed:
                    st.markdown("**Fed Funds Futures**: 🔵 **CHANGED**")
                    st.caption("Market has repriced Fed policy expectations")
                else:
                    st.markdown("**Fed Funds Futures**: ⚪ No significant change")
                    st.caption("No change in Fed policy expectations")
            
            with col2:
                # Create a visual representation of premarket changes
                try:
                    # Extract data for plotting
                    instruments = []
                    changes = []
                    colors = []
                    
                    for instrument in ["Gold Futures", "VIX", "US Dollar Index", "30Y Bond Futures"]:
                        if instrument in market_signals:
                            data = market_signals[instrument]
                            change_pct = data.get("change_pct")
                            direction = data.get("direction")
                            
                            instruments.append(instrument)
                            changes.append(change_pct)
                            colors.append("rgba(76, 175, 80, 0.7)" if direction == "up" else "rgba(244, 67, 54, 0.7)")
                    
                    # Create a horizontal bar chart
                    if instruments and changes:
                        fig = go.Figure()
                        
                        fig.add_trace(go.Bar(
                            y=instruments,
                            x=changes,
                            orientation='h',
                            marker_color=colors,
                            text=[f"{abs(c):.2f}%" for c in changes],
                            textposition='auto'
                        ))
                        
                        fig.update_layout(
                            title="Premarket Changes (%)",
                            xaxis_title="% Change from Previous Close",
                            template="plotly_white",
                            height=300,
                            margin=dict(l=10, r=10, t=40, b=10)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating premarket visualization: {e}")
            
            # Show VIX levels and implied market range
            st.markdown("### Implied Volatility & Expected Move")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # VIX level and interpretation
                vix = breadth_data.get("VIX")
                if vix is not None:
                    st.metric("VIX Open", f"{vix:.2f}")
                    
                    # Add color-coded interpretation
                    if vix > 30:
                        st.markdown("🔴 **High Volatility Environment**")
                    elif vix > 20:
                        st.markdown("🟠 **Elevated Volatility Environment**")
                    else:
                        st.markdown("🟢 **Low Volatility Environment**")
            
            with col2:
                # Expected daily move (SPY/S&P 500)
                daily_pct = breadth_data.get("ATM_Expected_Daily_Pct")
                daily_range = breadth_data.get("ATM_Expected_Daily_Range")
                
                if daily_pct is not None and daily_range is not None:
                    st.metric("Expected Daily Range", f"±{daily_range:.2f}")
                    st.markdown(f"**±{daily_pct:.2f}%** of current price")
                    st.caption("Based on options implied volatility")
            
            with col3:
                # Expected weekly move
                weekly_pct = breadth_data.get("ATM_Expected_Weekly_Pct")
                weekly_range = breadth_data.get("ATM_Expected_Weekly_Range")
                
                if weekly_pct is not None and weekly_range is not None:
                    st.metric("Expected Weekly Range", f"±{weekly_range:.2f}")
                    st.markdown(f"**±{weekly_pct:.2f}%** of current price")
                    st.caption("Based on options implied volatility")
            
            # Create a visual representation of the expected price ranges
            try:
                # Only create if we have the data
                if all(x is not None for x in [daily_range, weekly_range]):
                    # Calculate starting price (approximate S&P 500)
                    spy_price = 450  # A reasonable S&P 500 ETF price
                    
                    # Create price range chart
                    fig = go.Figure()
                    
                    # Add current price line
                    fig.add_shape(
                        type="line",
                        x0=0, y0=spy_price,
                        x1=3, y1=spy_price,
                        line=dict(color="black", width=2)
                    )
                    
                    # Add daily range
                    fig.add_shape(
                        type="rect",
                        x0=0.5, y0=spy_price - daily_range,
                        x1=1.5, y1=spy_price + daily_range,
                        fillcolor="rgba(0, 128, 255, 0.2)",
                        line=dict(color="blue", width=1)
                    )
                    
                    # Add weekly range
                    fig.add_shape(
                        type="rect",
                        x0=1.5, y0=spy_price - weekly_range,
                        x1=2.5, y1=spy_price + weekly_range,
                        fillcolor="rgba(255, 128, 0, 0.2)",
                        line=dict(color="orange", width=1)
                    )
                    
                    # Add annotations
                    fig.add_annotation(
                        x=1, y=spy_price,
                        text=f"Daily: ±{daily_range:.2f} (±{daily_pct:.2f}%)",
                        showarrow=False,
                        yshift=30
                    )
                    
                    fig.add_annotation(
                        x=2, y=spy_price,
                        text=f"Weekly: ±{weekly_range:.2f} (±{weekly_pct:.2f}%)",
                        showarrow=False,
                        yshift=40
                    )
                    
                    # Update layout
                    fig.update_layout(
                        title="Expected Price Ranges for SPY/S&P 500",
                        xaxis=dict(
                            showticklabels=False,
                            showgrid=False,
                            zeroline=False
                        ),
                        yaxis_title="Price",
                        template="plotly_white",
                        height=300,
                        margin=dict(l=10, r=10, t=40, b=10)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating price range visualization: {e}")
                
        else:
            st.warning("Premarket data unavailable. Please check data connections.")
    
    # Add explanations for the metrics
    with st.expander("Understanding the Market Snapshot Metrics"):
        st.markdown("""
        ### Interpreting Key Market Metrics
        
        **Fed Funds Rate vs 10Y Treasury**
        - When the 10Y yield is significantly above the Fed Funds Rate, the market expects economic growth and possible inflation
        - When the 10Y yield is below the Fed Funds Rate (inversion), it often signals economic slowdown concerns
        
        **VIX vs Realized Volatility**
        - VIX represents the market's expectation of 30-day forward-looking volatility
        - Realized Vol shows actual historical price movement
        - The premium (VIX - Realized Vol) indicates whether options are expensive or cheap
        
        **Treasury Yield Curve**
        - Normal curve: Longer maturities have higher yields
        - Flat curve: Similar yields across maturities
        - Inverted curve: Shorter maturities have higher yields (recession signal)
        
        **Expected Price Ranges**
        - Derived from options implied volatility
        - Shows market's expectation for potential price movements
        - Higher values indicate greater expected volatility
        
        ### Premarket Activity Signals
        
        **Gold Futures (GC=F)**
        - Rising in premarket often signals inflation concerns or risk-off sentiment
        - Falling in premarket may indicate risk-on sentiment or reduced inflation concerns
        
        **VIX Index**
        - Rising in premarket suggests increasing fear/uncertainty
        - Falling in premarket indicates decreasing fear/uncertainty
        
        **US Dollar Index (DXY)**
        - Strengthening dollar often pressures commodities and emerging markets
        - Weakening dollar typically benefits commodities and emerging markets
        
        **30Y Bond Futures**
        - Rising bond prices (falling yields) suggest flight to safety or decreasing inflation expectations
        - Falling bond prices (rising yields) indicate improving growth outlook or increasing inflation concerns
        
        **VIX Premium (VIX - Realized Vol)**
        - Positive premium: Options are expensive relative to actual market movement
        - Negative premium: Options are cheap relative to actual market movement
        - Large positive premium may indicate excessive fear and potential for mean reversion
        """)