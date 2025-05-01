import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def render_risk_assessment(data_service):
    """Render the Market Risk Assessment - Risk On / Risk Off Dashboard Summary"""
    st.header("🎯 Market Risk Assessment")
    
    # Create a more eye-catching and informative header section
    st.markdown("""
    <div style="background: linear-gradient(to right, #003366, #004080, #0059b3, #0073e6); 
                color: white; 
                padding: 15px; 
                border-radius: 10px; 
                margin-bottom: 20px;">
        <h3 style="margin: 0; color: white;">Risk-On / Risk-Off Market Verdict</h3>
        <p style="margin: 5px 0 0 0;">
            This dashboard aggregates signals across multiple market components to determine whether the 
            current environment favors <span style="color: #4CAF50; font-weight: bold;">risk-taking</span> or
            <span style="color: #F44336; font-weight: bold;">defensive positioning</span>.
        </p>
    </div>
    """
    , unsafe_allow_html=True)
    
    # Create columns for the gauge and summary
    col1, col2 = st.columns([1, 2])
    
    # Calculate the aggregate risk score from all components
    # This would be calculated by combining signals from all dashboard components
    risk_factors = [
        # Treasury Curve component factors
        {"name": "2Y-10Y Yield Curve", "score": calculate_yield_curve_score(data_service), "weight": 2.0},
        {"name": "Fed Policy Stance", "score": calculate_fed_policy_score(data_service), "weight": 2.0},
        {"name": "Market Breadth", "score": calculate_market_breadth_score(data_service), "weight": 1.5},
        {"name": "Volatility Metrics", "score": calculate_volatility_score(data_service), "weight": 1.5},
        {"name": "Gold/Dollar Dynamics", "score": calculate_gold_dollar_score(data_service), "weight": 1.0},
        {"name": "Pre-Market Futures", "score": calculate_premarket_score(data_service), "weight": 1.0},
    ]
    
    # Calculate weighted average score
    total_weight = sum(factor["weight"] for factor in risk_factors)
    weighted_score = sum(factor["score"] * factor["weight"] for factor in risk_factors) / total_weight
    
    with col1:
        # Create gauge chart to display the risk score
        fig = create_risk_gauge(weighted_score)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display the overall risk status with prominent styling
        risk_status = get_risk_status(weighted_score)
        status_color = get_status_color(weighted_score)
        
        # Create risk status HTML separately to avoid f-string rendering issues
        bg_color = f"background-color: {status_color}20"
        border_style = f"border: 2px solid {status_color}"
        text_color = f"color: {status_color}"
        
        risk_status_html = f"""
        <div style="{bg_color}; 
                    padding: 15px; 
                    border-radius: 10px; 
                    text-align: center;
                    {border_style};">
            <h2 style="{text_color}; margin: 0;">{risk_status}</h2>
        </div>
        """
        
        st.markdown(risk_status_html, unsafe_allow_html=True)
    
    with col2:
        # Create a table showing all the factors and their individual signals
        st.markdown("### Component-Level Risk Factors")
        
        # Create a DataFrame for display
        display_data = []
        
        for factor in risk_factors:
            signal = "NEUTRAL"
            if factor["score"] >= 60:
                signal = "RISK-ON"
            elif factor["score"] <= 40:
                signal = "RISK-OFF"
                
            display_data.append({
                "Component": factor["name"],
                "Signal": signal,
                "Score": f"{factor['score']:.0f}/100",
                "Weight": f"{factor['weight']:.1f}x"
            })
            
        display_df = pd.DataFrame(display_data)
        
        # Function to highlight the status column
        def highlight_assessment(val):
            if val == "RISK-ON":
                return 'background-color: rgba(40, 167, 69, 0.2); color: #28a745;'
            elif val == "RISK-OFF":
                return 'background-color: rgba(220, 53, 69, 0.2); color: #dc3545;'
            else:
                return 'background-color: rgba(255, 193, 7, 0.2); color: #fd7e14;'
        
        styled_df = display_df.style.map(highlight_assessment, subset=['Signal'])
        st.dataframe(styled_df, hide_index=True, use_container_width=True)
    
    # Aggregate data from all dashboard components to generate dynamic recommendations
    st.subheader("Market Positioning Recommendations")
    
    # Get component-specific risk signals
    # These will be dynamically pulled from actual component data instead of being hardcoded
    
    # Extract volatility metrics from market breadth data
    volatility_data = data_service.get_market_breadth()
    vix_level = volatility_data.get("vix", 20) if volatility_data else 20
    realized_vol = volatility_data.get("realized_vol", 15) if volatility_data else 15
    vol_risk_premium = vix_level - realized_vol  # VRP > 0 means fear premium (risk-off), VRP < 0 means complacency
    
    # Interpret volatility signals
    vol_signal = "NEUTRAL"
    if vix_level > 30 and vol_risk_premium > 5:
        vol_signal = "STRONG RISK-OFF"  # High VIX with high risk premium = fear
    elif vix_level > 25:
        vol_signal = "RISK-OFF"  # Elevated VIX = caution
    elif vix_level < 15 and vol_risk_premium < -2:
        vol_signal = "RISK-ON w/CAUTION"  # Very low VIX with negative risk premium = complacency (potentially contrarian)
    elif vix_level < 18:
        vol_signal = "RISK-ON"  # Low VIX = risk appetite
        
    # Get yield curve data
    treasury_data = data_service.get_treasury_yields()
    current_yields = treasury_data.get('current', {}) if treasury_data else {}
    
    # Calculate key yield spreads
    spread_2y_10y = (current_yields.get("10Y_yield", 0) - current_yields.get("2Y_yield", 0))
    spread_5y_30y = (current_yields.get("30Y_yield", 0) - current_yields.get("5Y_yield", 0))
    
    # Interpret yield curve signals
    curve_signal = "NEUTRAL"
    if spread_2y_10y < -0.2:  # Inverted curve
        curve_signal = "RISK-OFF"
    elif spread_2y_10y < 0:  # Slight inversion
        curve_signal = "SLIGHT RISK-OFF"
    elif spread_2y_10y > 1.0:  # Steep curve
        curve_signal = "RISK-ON"
    elif spread_2y_10y > 0.5:  # Moderately steep
        curve_signal = "SLIGHT RISK-ON"
        
    # Get Fed policy data
    fed_data = data_service.get_fed_funds_futures()
    
    # Interpret Fed policy signals
    fed_signal = "NEUTRAL"
    
    # Extract current effective rate, future expectations, and real rate
    current_rate = None
    future_rate = None
    real_rate = None
    inflation_rate = None
    
    if fed_data and "DFF" in fed_data:
        current_rate = fed_data["DFF"].get("implied_rate")
        real_rate = fed_data["DFF"].get("real_rate")
        inflation_rate = fed_data["DFF"].get("inflation_rate")
        
    futures_data = {k: v for k, v in fed_data.items() if v.get('type') == 'future'} if fed_data else {}
    if futures_data:
        # Sort and get the nearest future
        sorted_futures = sorted(
            futures_data.items(),
            key=lambda x: (x[1].get('contract', '').split()[-1], x[1].get('contract', '').split()[0])
        )
        if sorted_futures:
            future_rate = sorted_futures[0][1].get('implied_rate')
    
    # Display the real rate calculation prominently
    if real_rate is not None:
        # Show a callout box highlighting the real rate calculation
        real_rate_color = "green" if real_rate < -0.5 else "red" if real_rate > 1.0 else "orange"
        real_rate_status = "Stimulative (Bullish)" if real_rate < -0.5 else "Restrictive (Bearish)" if real_rate > 1.0 else "Neutral"
        
        # Create the real rates explanation with detailed calculation
        if inflation_rate is not None:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; border-left: 5px solid {real_rate_color}; 
                        padding: 15px; margin: 20px 0; border-radius: 5px;">
                <h4 style="margin-top: 0; color: {real_rate_color};">Real Fed Funds Rate: {real_rate:.2f}% ({real_rate_status})</h4>
                <p><b>Calculation:</b> Nominal Rate ({current_rate:.2f}%) - Inflation Rate ({inflation_rate:.2f}%)</p>
                <p><b>Market Impact:</b> {
                    "Deeply negative real rates typically support risk assets as cash loses purchasing power." if real_rate < -1.0 else
                    "Moderately negative real rates generally favor risk-on positioning." if real_rate < 0 else
                    "Positive real rates often pressure risk assets and favor defensive positioning." if real_rate > 0.5 else
                    "Near-zero real rates have a relatively neutral impact on markets."
                }</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; border-left: 5px solid {real_rate_color}; 
                        padding: 15px; margin: 20px 0; border-radius: 5px;">
                <h4 style="margin-top: 0; color: {real_rate_color};">Real Fed Funds Rate: {real_rate:.2f}% ({real_rate_status})</h4>
                <p><b>Market Impact:</b> {
                    "Deeply negative real rates typically support risk assets as cash loses purchasing power." if real_rate < -1.0 else
                    "Moderately negative real rates generally favor risk-on positioning." if real_rate < 0 else
                    "Positive real rates often pressure risk assets and favor defensive positioning." if real_rate > 0.5 else
                    "Near-zero real rates have a relatively neutral impact on markets."
                }</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Calculate rate expectations (positive means rates expected to rise, negative means fall)
    rate_expectation = 0
    if current_rate is not None and future_rate is not None:
        rate_expectation = future_rate - current_rate
        
        # First consider rate direction expectations
        if rate_expectation < -0.5:  # Significant cuts expected
            fed_signal = "RISK-ON"
        elif rate_expectation < -0.25:  # Modest cuts expected
            fed_signal = "SLIGHT RISK-ON"
        elif rate_expectation > 0.5:  # Significant hikes expected
            fed_signal = "RISK-OFF"
        elif rate_expectation > 0.25:  # Modest hikes expected
            fed_signal = "SLIGHT RISK-OFF"
        
        # Then factor in real rates to refine the signal
        if real_rate is not None:
            if real_rate < -1.0:  # Deeply negative real rates are stimulative
                if fed_signal != "RISK-OFF" and fed_signal != "SLIGHT RISK-OFF":
                    fed_signal = "RISK-ON"  # Upgrade to RISK-ON if not already RISK-OFF
            elif real_rate > 1.5:  # Significantly positive real rates are restrictive
                if fed_signal != "RISK-ON" and fed_signal != "SLIGHT RISK-ON":
                    fed_signal = "RISK-OFF"  # Downgrade to RISK-OFF if not already RISK-ON
    
    # Get market open signals (gold, dollar, etc.)
    market_signals = data_service.get_market_open_signals()
    
    # Extract gold and dollar movement
    gold_data = market_signals.get('gold', {}) if market_signals else {}
    dollar_data = market_signals.get('dollar', {}) if market_signals else {}
    
    gold_change = gold_data.get('change_pct', 0)
    dollar_change = dollar_data.get('change_pct', 0)
    
    # Gold up + Dollar down is typically risk-on; Gold down + Dollar up is typically risk-off
    gold_dollar_signal = "NEUTRAL"
    combined_change = gold_change - dollar_change
    
    if combined_change > 1.0:
        gold_dollar_signal = "STRONG RISK-ON"
    elif combined_change > 0.5:
        gold_dollar_signal = "RISK-ON"
    elif combined_change < -1.0:
        gold_dollar_signal = "STRONG RISK-OFF"
    elif combined_change < -0.5:
        gold_dollar_signal = "RISK-OFF"
    
    # Get futures data for pre-market sentiment
    futures_data = data_service.get_futures_fair_value()
    es_change = futures_data.get('es_change_pct', 0) if futures_data else 0
    
    # Interpret futures signals
    futures_signal = "NEUTRAL"
    if es_change > 1.0:
        futures_signal = "STRONG RISK-ON"
    elif es_change > 0.5:
        futures_signal = "RISK-ON"
    elif es_change < -1.0:
        futures_signal = "STRONG RISK-OFF"
    elif es_change < -0.5:
        futures_signal = "RISK-OFF"
    
    # Get Fed Funds data for real rate info
    ff_data = data_service.get_fed_funds_futures()
    
    # Get real rate info if available
    real_rate = None
    real_rate_signal = "NEUTRAL"
    if ff_data and "DFF" in ff_data and "real_rate" in ff_data["DFF"]:
        real_rate = ff_data["DFF"].get("real_rate")
        
        if real_rate is not None:
            if real_rate <= -2.0:
                real_rate_signal = "STRONG RISK-ON"
            elif real_rate <= -1.0:
                real_rate_signal = "RISK-ON"
            elif real_rate <= 0.0:
                real_rate_signal = "SLIGHT RISK-ON"
            elif real_rate <= 1.0:
                real_rate_signal = "NEUTRAL"
            elif real_rate <= 2.0:
                real_rate_signal = "SLIGHT RISK-OFF"
            elif real_rate <= 3.0:
                real_rate_signal = "RISK-OFF"
            else:
                real_rate_signal = "STRONG RISK-OFF"
                
    # Create a summary of all signals for display
    signals_summary = [
        {"Component": "Volatility (VIX/VRP)", "Signal": vol_signal, "Importance": "High"},
        {"Component": "Yield Curve", "Signal": curve_signal, "Importance": "High"},
        {"Component": "Fed Policy", "Signal": fed_signal, "Importance": "High"}
    ]
    
    # Add real rate signal if available
    if real_rate is not None:
        signals_summary.append({"Component": f"Real Rate ({real_rate:.2f}%)", "Signal": real_rate_signal, "Importance": "High"})
        
    # Add remaining signals
    signals_summary.extend([
        {"Component": "Gold/Dollar", "Signal": gold_dollar_signal, "Importance": "Medium"},
        {"Component": "Equity Futures", "Signal": futures_signal, "Importance": "Medium"}
    ])
    
    # Display the signals summary
    st.markdown("### Component Signals Summary")
    signals_df = pd.DataFrame(signals_summary)
    
    # Style the dataframe for better visualization
    def style_signal(val):
        if "STRONG RISK-ON" in val:
            return 'background-color: rgba(40, 167, 69, 0.3); color: #28a745; font-weight: bold;'
        elif "RISK-ON" in val:
            return 'background-color: rgba(40, 167, 69, 0.2); color: #28a745;'
        elif "STRONG RISK-OFF" in val:
            return 'background-color: rgba(220, 53, 69, 0.3); color: #dc3545; font-weight: bold;'
        elif "RISK-OFF" in val:
            return 'background-color: rgba(220, 53, 69, 0.2); color: #dc3545;'
        else:  # NEUTRAL
            return 'background-color: rgba(255, 193, 7, 0.2); color: #fd7e14;'
    
    styled_signals = signals_df.style.map(style_signal, subset=['Signal'])
    st.dataframe(styled_signals, use_container_width=True)
    
    # Generate dynamic recommendations based on aggregated signals
    # First, convert signals to numerical scores
    signal_scores = {
        "STRONG RISK-ON": 100,
        "RISK-ON": 80, 
        "RISK-ON w/CAUTION": 65,
        "SLIGHT RISK-ON": 60,
        "NEUTRAL": 50,
        "SLIGHT RISK-OFF": 40,
        "RISK-OFF": 20,
        "STRONG RISK-OFF": 0
    }
    
    # Importance weights
    importance_weights = {
        "High": 2.0,
        "Medium": 1.0,
        "Low": 0.5
    }
    
    # Calculate weighted average of all signal scores
    total_weight = sum(importance_weights[row["Importance"]] for row in signals_summary)
    total_score = sum(signal_scores.get(row["Signal"], 50) * importance_weights[row["Importance"]] for row in signals_summary)
    
    aggregate_score = total_score / total_weight if total_weight > 0 else 50
    
    # Determine overall risk environment
    if aggregate_score >= 65:
        risk_status = "RISK-ON"
        risk_color = "#28a745"  # Green
        
        # Generate dynamic recommendations for risk-on environment
        equity_rec = "Overweight equities with focus on growth and cyclical sectors"
        
        if real_rate is not None and real_rate < 0:
            fixed_income_rec = "Significantly underweight duration as negative real rates are bearish for bonds"
            gold_rec = "Consider overweight gold as negative real rates are historically supportive"
        else:
            fixed_income_rec = "Underweight duration in fixed income, consider credit risk for higher yield"
            gold_rec = "Neutral to underweight gold, monitor real yields closely"
            
        cash_rec = "Minimal cash allocation, deploy to risk assets"
        
        # Product-specific recommendations
        spy_rec = "LONG SPY/QQQ - Growth stocks typically outperform in risk-on environments"
        
        # Determine gold recommendation based on real rates and dollar strength
        if spread_2y_10y > 0.5 and dollar_change < -0.2:
            gold_prod_rec = "NEUTRAL GOLD - Despite risk-on environment, dollar weakness may provide support"
        else:
            gold_prod_rec = "UNDERWEIGHT GOLD - Typically underperforms in risk-on environments with rising real rates"
            
        # Eurodollar recommendation based on rate expectations
        if rate_expectation < -0.25:
            euro_rec = "LONG EURODOLLAR FUTURES - Position for potential rate cuts"
        else:
            euro_rec = "NEUTRAL EURODOLLAR FUTURES - Monitor Fed policy signals closely"
            
        # Set portfolio strategy for risk-on environment
        portfolio_strategy = "Focus on growth-oriented sectors like Technology, Consumer Discretionary, and Financials. Consider reducing defensive positions in Utilities and Consumer Staples. Maintain disciplined risk management despite bullish outlook."
            
    elif aggregate_score <= 35:
        risk_status = "RISK-OFF"
        risk_color = "#dc3545"  # Red
        
        # Generate dynamic recommendations for risk-off environment
        equity_rec = "Underweight equities with focus on defensive sectors and quality factors"
        
        if real_rate is not None:
            if real_rate > 1.0:
                fixed_income_rec = "Strongly overweight duration as positive real rates are bullish for quality bonds"
                gold_rec = "Underweight gold as positive real rates create opportunity cost for holding non-yielding assets"
            else:
                fixed_income_rec = "Overweight duration, focus on high-quality government and investment grade bonds"
                gold_rec = "Overweight gold as a safe haven asset, especially with low/negative real rates"
        else:
            fixed_income_rec = "Overweight duration, focus on high-quality government and investment grade bonds"
            gold_rec = "Overweight gold as a safe haven asset"
            
        cash_rec = "Increased cash allocation for capital preservation and future opportunities"
        
        # Product-specific recommendations
        spy_rec = "SHORT/UNDERWEIGHT SPY/QQQ - Consider reducing equity exposure or using hedges"
        
        # Determine gold recommendation based on real rates
        if spread_2y_10y < 0 or dollar_change > 0.2:
            gold_prod_rec = "LONG GOLD - Typically performs well in risk-off environments with declining real rates"
        else:
            gold_prod_rec = "OVERWEIGHT GOLD - Safe haven demand increases in risk-off environments"
            
        # Eurodollar recommendation based on rate expectations
        if rate_expectation > 0.25:
            euro_rec = "SHORT EURODOLLAR FUTURES - Position for potential rate hikes amid inflation concerns"
        else:
            euro_rec = "LONG EURODOLLAR FUTURES - Potential flight to safety increases demand"
            
        # Set portfolio strategy for risk-off environment
        portfolio_strategy = "Prioritize defensive sectors like Utilities, Consumer Staples, and Healthcare. Consider reducing exposure to high-beta sectors. Implement appropriate hedging strategies and maintain higher cash reserves."
            
    else:
        risk_status = "NEUTRAL"
        risk_color = "#fd7e14"  # Orange
        
        # Generate dynamic recommendations for neutral environment
        equity_rec = "Neutral weight equities, balanced between growth and defensive sectors"
        
        if real_rate is not None:
            real_rate_msg = f"current real rate: {real_rate:.2f}%"
            if real_rate < -0.5:
                fixed_income_rec = f"Underweight long-duration bonds due to negative real rates ({real_rate_msg})"
                gold_rec = f"Slight overweight to gold supported by negative real rates ({real_rate_msg})"
            elif real_rate > 0.5:
                fixed_income_rec = f"Slight overweight to medium-duration bonds with positive real rates ({real_rate_msg})"
                gold_rec = f"Slight underweight to gold with positive real rates ({real_rate_msg})"
            else:
                fixed_income_rec = "Barbell approach with both short and long duration exposure"
                gold_rec = "Neutral allocation to gold, monitor for developing trends"
        else:
            fixed_income_rec = "Barbell approach with both short and long duration exposure"
            gold_rec = "Neutral allocation to gold, monitor for developing trends"
            
        cash_rec = "Moderate cash allocation for flexibility and opportunistic deployment"
        
        # Product-specific recommendations
        spy_rec = "NEUTRAL SPY/QQQ - Maintain strategic allocation without tactical tilts"
        gold_prod_rec = "NEUTRAL GOLD - Monitor changes in real yields and dollar strength"
        euro_rec = "NEUTRAL EURODOLLAR FUTURES - Position based on specific Fed policy indicators"
        
        # Set proprietary portfolio strategy for neutral environment
        portfolio_strategy = "Maintain balanced sector exposure with quality focus. Consider barbell approach with both defensive and growth positions. Monitor market breadth indicators for directional signals while preserving tactical flexibility."
    
    # Instead of using one large HTML block, let's break it down into smaller, more manageable pieces
    
    # 1. First display the header section with risk status
    st.markdown(
        f"""
        <div style="background-color: {risk_color}20; padding: 15px; border-radius: 10px; 
                   border-left: 5px solid {risk_color}; margin-bottom: 15px;">
            <div style="display: flex; align-items: center;">
                <div style="background-color: {risk_color}; color: white; padding: 10px 15px; 
                           border-radius: 50px; margin-right: 15px; font-weight: bold;">
                    {risk_status}
                </div>
                <div>
                    <h3 style="color: {risk_color}; margin: 0;">{risk_status} Environment</h3>
                    <p style="margin: 5px 0 0 0;">Based on the aggregation of multiple market signals and indicators</p>
                </div>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # 2. Create a two-column layout using Streamlit's columns instead of HTML grid
    col_alloc, col_trade = st.columns(2)
    
    # 3. Display the Asset Allocation section
    with col_alloc:
        st.markdown(
            f"""
            <div style="background-color: rgba(255,255,255,0.7); padding: 15px; 
                       border-radius: 10px; border: 1px solid #ddd; height: 100%;">
                <h4 style="margin-top: 0; border-bottom: 2px solid {risk_color}; 
                          padding-bottom: 8px; color: {risk_color};">
                    <span style="font-size: 1.2em;">📊</span> Asset Allocation
                </h4>
                <div style="display: flex; margin-bottom: 10px;">
                    <div style="min-width: 100px; font-weight: bold;">Equities:</div>
                    <div>{equity_rec}</div>
                </div>
                <div style="display: flex; margin-bottom: 10px;">
                    <div style="min-width: 100px; font-weight: bold;">Fixed Income:</div>
                    <div>{fixed_income_rec}</div>
                </div>
                <div style="display: flex; margin-bottom: 10px;">
                    <div style="min-width: 100px; font-weight: bold;">Gold:</div>
                    <div>{gold_rec}</div>
                </div>
                <div style="display: flex; margin-bottom: 0px;">
                    <div style="min-width: 100px; font-weight: bold;">Cash:</div>
                    <div>{cash_rec}</div>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # 4. Display the Trading Recommendations section
    with col_trade:
        # Determine background colors for trading recommendations based on content
        spy_bg_color = '#e8f5e9' if 'LONG' in spy_rec else '#ffebee' if 'SHORT' in spy_rec else '#e3f2fd'
        gold_bg_color = '#e8f5e9' if 'LONG' in gold_prod_rec else '#ffebee' if 'UNDER' in gold_prod_rec else '#e3f2fd'
        euro_bg_color = '#e8f5e9' if 'LONG' in euro_rec else '#ffebee' if 'SHORT' in euro_rec else '#e3f2fd'
        
        st.markdown(
            f"""
            <div style="background-color: rgba(255,255,255,0.7); padding: 15px; 
                       border-radius: 10px; border: 1px solid #ddd; height: 100%;">
                <h4 style="margin-top: 0; border-bottom: 2px solid {risk_color}; 
                          padding-bottom: 8px; color: {risk_color};">
                    <span style="font-size: 1.2em;">🎯</span> Trading Recommendations
                </h4>
                <div style="background-color: {spy_bg_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <div style="font-weight: bold; margin-bottom: 2px;">SPY/QQQ:</div>
                    <div>{spy_rec}</div>
                </div>
                <div style="background-color: {gold_bg_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <div style="font-weight: bold; margin-bottom: 2px;">Gold:</div>
                    <div>{gold_prod_rec}</div>
                </div>
                <div style="background-color: {euro_bg_color}; padding: 10px; border-radius: 5px; margin-bottom: 0px;">
                    <div style="font-weight: bold; margin-bottom: 2px;">Eurodollar Futures:</div>
                    <div>{euro_rec}</div>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # 5. Display the Portfolio Strategy section
    st.markdown(
        f"""
        <div style="background-color: rgba(255,255,255,0.7); padding: 15px; 
                   border-radius: 10px; border: 1px solid #ddd; margin-top: 15px;">
            <h4 style="margin-top: 0; border-bottom: 2px solid {risk_color}; 
                      padding-bottom: 8px; color: {risk_color};">
                <span style="font-size: 1.2em;">💼</span> Portfolio Strategy
            </h4>
            <p>
                {portfolio_strategy}
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Add methodology explanation
    with st.expander("Risk Assessment Methodology"):
        st.markdown("""
        ### Methodology
        
        The Risk-On/Risk-Off assessment aggregates signals from multiple market components:
        
        1. **Yield Curve Analysis:** Evaluates the shape and recent changes in the Treasury yield curve
        2. **Fed Policy Stance:** Assesses the Federal Reserve's current policy and future expectations
        3. **Real Interest Rates:** Factors the real Fed Funds rate (nominal rate minus inflation) as a key driver of asset prices
        4. **Market Breadth:** Analyzes technical indicators of market participation and health
        5. **Volatility Metrics:** Measures market stress through VIX and realized volatility spreads
        6. **Gold/Dollar Dynamics:** Evaluates the interplay between gold prices and USD strength
        7. **Pre-Market Futures:** Incorporates overnight and pre-market futures pricing
        
        Each factor receives a score from 0-100:
        - **0-40:** Risk-Off Signal
        - **40-60:** Neutral Signal
        - **60-100:** Risk-On Signal
        
        Factors are weighted according to their historical predictive power, with yield curve, Fed policy, and real rates carrying the highest weights.
        
        #### Real Rate Analysis
        
        **Real interest rates** (nominal rate minus inflation) are particularly significant for risk asset performance:
        
        - **Deeply negative real rates** (<-2%) are typically very supportive for risk assets and gold
        - **Moderately negative real rates** (-2% to 0%) tend to be supportive for equities but less so for fixed income
        - **Low positive real rates** (0% to 1%) generally neutral for risk assets
        - **High positive real rates** (>1%) tend to be restrictive for risk assets and challenging for gold
        
        Real rates provide insight into the true cost of capital and monetary conditions beyond what nominal rates indicate.
        """)

def create_risk_gauge(risk_score):
    """Create a more compact gauge chart for the risk score"""
    # Define color scale from red (0) to orange/yellow (50) to green (100)
    colors = [
        "#dc3545",  # Red (0-20: Strong Risk-Off)
        "#de6e35",  # Red-Orange (20-30: Risk-Off)
        "#fd7e14",  # Orange (30-45: Slight Risk-Off)
        "#ffc107",  # Yellow (45-55: Neutral)
        "#9fce66",  # Light green (55-70: Slight Risk-On)
        "#70b65c",  # Medium green (70-85: Risk-On)
        "#28a745",  # Green (85-100: Strong Risk-On)
    ]
    
    # Create the gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "#333333"},
            'bar': {'color': "#555555", 'thickness': 0.25},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#333333",
            'steps': [
                {'range': [0, 20], 'color': colors[0]},
                {'range': [20, 30], 'color': colors[1]},
                {'range': [30, 45], 'color': colors[2]},
                {'range': [45, 55], 'color': colors[3]},
                {'range': [55, 70], 'color': colors[4]},
                {'range': [70, 85], 'color': colors[5]},
                {'range': [85, 100], 'color': colors[6]}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 5},
                'thickness': 0.8,
                'value': risk_score
            }
        },
        number={
            'suffix': "%",
            'font': {'size': 28, 'color': get_status_color(risk_score)}
        },
        title={
            'text': "Risk Sentiment Score",
            'font': {'size': 18, 'color': "#333333"}
        }
    ))
    
    # Add markers for Risk-Off, Neutral, and Risk-On
    fig.add_annotation(x=0.25, y=0.1, text="Risk-Off", showarrow=False, font=dict(size=14, color="#dc3545"))
    fig.add_annotation(x=0.5, y=0.1, text="Neutral", showarrow=False, font=dict(size=14, color="#fd7e14"))
    fig.add_annotation(x=0.8, y=0.1, text="Risk-On", showarrow=False, font=dict(size=14, color="#28a745"))
    
    # Customize layout
    fig.update_layout(
        height=300,
        margin=dict(l=30, r=30, t=50, b=30),
        paper_bgcolor="white",
        plot_bgcolor="white"
    )
    
    return fig

def get_risk_status(risk_score):
    """Get risk status text based on score"""
    if risk_score >= 85:
        return "STRONG RISK-ON"
    elif risk_score >= 60:
        return "RISK-ON"
    elif risk_score >= 55:
        return "SLIGHT RISK-ON"
    elif risk_score >= 45:
        return "NEUTRAL"
    elif risk_score >= 30:
        return "SLIGHT RISK-OFF"
    elif risk_score >= 15:
        return "RISK-OFF"
    else:
        return "STRONG RISK-OFF"

def get_status_color(risk_score):
    """Get color for risk status text"""
    if risk_score >= 60:
        return "#28a745"  # Green for Risk-On
    elif risk_score <= 40:
        return "#dc3545"  # Red for Risk-Off
    else:
        return "#fd7e14"  # Orange for Neutral

# Helper functions to calculate risk scores from different dashboard components
def calculate_yield_curve_score(data_service):
    """Calculate risk score from Treasury yield curve data"""
    try:
        # Get Treasury yield data from the service
        treasury_data = data_service.get_treasury_yields()
        
        if not treasury_data or "historical" not in treasury_data:
            return 50  # Neutral default if no data
            
        historical = treasury_data["historical"]
        
        if not historical or len(historical) == 0:
            return 50
            
        # Get latest spread data
        latest = historical[-1]
        spread_2y_10y = latest.get("spread_2y_10y", 0)
        
        # Calculate a score based on the spread
        # Inverted yield curve (negative spread) is Risk-Off
        # Steep yield curve (high positive spread) is Risk-On
        if spread_2y_10y <= -0.5:
            return 20  # Strong Risk-Off
        elif spread_2y_10y < 0:
            return 30  # Risk-Off
        elif spread_2y_10y < 0.25:
            return 45  # Slight Risk-Off
        elif spread_2y_10y < 0.5:
            return 55  # Neutral
        elif spread_2y_10y < 1.0:
            return 65  # Slight Risk-On
        elif spread_2y_10y < 1.5:
            return 75  # Risk-On
        else:
            return 85  # Strong Risk-On
    except Exception:
        return 50  # Default to neutral on error

def calculate_fed_policy_score(data_service):
    """Calculate risk score from Fed policy data, incorporating real rates"""
    try:
        # Get Fed Funds data from the service
        ff_data = data_service.get_fed_funds_futures()
        
        if not ff_data:
            return 50  # Neutral default if no data
            
        # Get current effective rate and real rate
        current_rate = None
        real_rate = None
        
        if "DFF" in ff_data:
            current_rate = ff_data["DFF"].get("implied_rate")
            real_rate = ff_data["DFF"].get("real_rate")
        
        if current_rate is None:
            return 50
            
        # Get futures expectations
        futures_data = {k: v for k, v in ff_data.items() if v.get('type') == 'future'}
        
        if not futures_data:
            return 50
            
        # Sort and get the nearest future
        sorted_futures = sorted(
            futures_data.items(),
            key=lambda x: (x[1].get('contract', '').split()[-1], x[1].get('contract', '').split()[0])
        )
        
        if not sorted_futures:
            return 50
            
        # Get implied rate from the nearest future
        future_rate = sorted_futures[0][1].get('implied_rate')
        future_real_rate = sorted_futures[0][1].get('real_rate')
        
        if future_rate is None:
            return 50
            
        # Calculate the future expectation (positive means rates expected to rise, negative means fall)
        future_expectation = future_rate - current_rate
        
        # Calculate initial score based on the rate expectation
        rate_expectation_score = 0
        # Rising rates (positive expectation) is Risk-Off
        # Falling rates (negative expectation) is Risk-On
        if future_expectation <= -1.0:
            rate_expectation_score = 85  # Strong Risk-On
        elif future_expectation <= -0.5:
            rate_expectation_score = 75  # Risk-On
        elif future_expectation <= -0.25:
            rate_expectation_score = 65  # Slight Risk-On
        elif future_expectation <= 0.25:
            rate_expectation_score = 50  # Neutral
        elif future_expectation <= 0.5:
            rate_expectation_score = 35  # Slight Risk-Off
        elif future_expectation <= 1.0:
            rate_expectation_score = 25  # Risk-Off
        else:
            rate_expectation_score = 15  # Strong Risk-Off
        
        # If real rate is available, factor it into the score
        if real_rate is not None:
            real_rate_score = 0
            
            # Strongly negative real rates tend to be supportive for risk assets
            # Strongly positive real rates tend to be restrictive
            if real_rate <= -2.0:  # Deeply negative real rates
                real_rate_score = 85  # Very Risk-On - stimulative for asset prices
            elif real_rate <= -1.0:  # Moderately negative real rates
                real_rate_score = 70  # Risk-On 
            elif real_rate <= 0.0:  # Slightly negative real rates
                real_rate_score = 60  # Slightly Risk-On
            elif real_rate <= 1.0:  # Low positive real rates
                real_rate_score = 45  # Slightly Neutral
            elif real_rate <= 2.0:  # Moderate positive real rates
                real_rate_score = 35  # Slightly Risk-Off
            elif real_rate <= 3.0:  # High positive real rates
                real_rate_score = 25  # Risk-Off
            else:  # Very high positive real rates
                real_rate_score = 15  # Very Risk-Off - restrictive
            
            # Combine scores - weight real rates a bit higher as they directly impact asset prices
            return int(0.4 * rate_expectation_score + 0.6 * real_rate_score)
        
        # If real rate not available, just use the rate expectation score
        return rate_expectation_score
            
    except Exception as e:
        print(f"Error calculating Fed policy score: {e}")
        return 50  # Default to neutral on error

def calculate_market_breadth_score(data_service):
    """Calculate risk score from market breadth data"""
    try:
        # For simplicity, use a placeholder with random but biased score
        # In a real implementation, this would analyze actual market breadth data
        # such as advance/decline line, TICK, TRIN, etc.
        
        breadth_data = data_service.get_market_breadth()
        
        if not breadth_data:
            return np.random.normal(50, 10)  # Random neutral score if no data
        
        # Analyze VIX vs Realized Volatility (VRP)
        # Positive VRP (VIX > Realized) typically indicates risk-off or fear
        # Negative VRP (Realized > VIX) typically indicates risk-on or complacency
        vix = breadth_data.get("vix", 20)
        realized_vol = breadth_data.get("realized_vol", 20)
        vrp = vix - realized_vol
        
        # Calculate a score based on VRP
        vrp_score = 0
        if vrp > 5:
            vrp_score = 30  # High VRP (fear premium) is Risk-Off
        elif vrp > 2:
            vrp_score = 40
        elif vrp > -2:
            vrp_score = 50  # Neutral
        elif vrp > -5:
            vrp_score = 60
        else:
            vrp_score = 70  # Low VRP (complacency) is Risk-On
        
        # Use other breadth indicators if available
        tick = breadth_data.get("tick", 0)
        tick_score = 0
        if tick < -500:
            tick_score = 30  # Strong selling pressure is Risk-Off
        elif tick < -200:
            tick_score = 40
        elif tick < 200:
            tick_score = 50  # Neutral
        elif tick < 500:
            tick_score = 60
        else:
            tick_score = 70  # Strong buying pressure is Risk-On
        
        # Combine scores with appropriate weights
        return 0.7 * vrp_score + 0.3 * tick_score
    except Exception:
        return 50  # Default to neutral on error

def calculate_volatility_score(data_service):
    """Calculate risk score from volatility metrics"""
    try:
        # Get volatility data from the market breadth component
        volatility_data = data_service.get_market_breadth()
        
        if not volatility_data:
            return 50  # Neutral default if no data
        
        # Get VIX value
        vix = volatility_data.get("vix", 20)
        
        # Calculate a score based on VIX level
        # High VIX is typically Risk-Off, low VIX is typically Risk-On
        # However, extremes can indicate turning points (contrarian)
        if vix >= 35:
            return 30  # High volatility is Risk-Off
        elif vix >= 25:
            return 40
        elif vix >= 15:
            return 50  # Neutral
        elif vix >= 10:
            return 70
        else:
            return 80  # Very low volatility is Risk-On (but can be complacent)
    except Exception:
        return 50  # Default to neutral on error

def calculate_gold_dollar_score(data_service):
    """Calculate risk score from gold and dollar data"""
    try:
        # Get market signals data which includes gold and dollar movement
        signals_data = data_service.get_market_open_signals()
        
        if not signals_data:
            return 50  # Neutral default if no data
        
        # Get gold and dollar data (daily change)
        gold_change = signals_data.get("gold", {}).get("change_pct", 0)
        dollar_change = signals_data.get("dollar", {}).get("change_pct", 0)
        
        # Calculate a combined score
        # Gold up + Dollar down = Risk-On
        # Gold down + Dollar up = Risk-Off
        combined_change = gold_change - dollar_change
        
        if combined_change > 1.5:
            return 80  # Strong Risk-On signal
        elif combined_change > 0.75:
            return 70
        elif combined_change > 0.25:
            return 60
        elif combined_change > -0.25:
            return 50  # Neutral
        elif combined_change > -0.75:
            return 40
        elif combined_change > -1.5:
            return 30
        else:
            return 20  # Strong Risk-Off signal
    except Exception:
        return 50  # Default to neutral on error

def calculate_premarket_score(data_service):
    """Calculate risk score from pre-market futures"""
    try:
        # Get futures fair value data
        futures_data = data_service.get_futures_fair_value()
        
        if not futures_data:
            return 50  # Neutral default if no data
        
        # Get ES (S&P 500) futures change
        es_change = futures_data.get("es_change_pct", 0)
        
        # Calculate a score based on futures movement
        # Strong positive futures = Risk-On
        # Strong negative futures = Risk-Off
        if es_change > 1.0:
            return 90  # Strong Risk-On
        elif es_change > 0.5:
            return 75
        elif es_change > 0.2:
            return 65
        elif es_change > -0.2:
            return 50  # Neutral
        elif es_change > -0.5:
            return 35
        elif es_change > -1.0:
            return 25
        else:
            return 10  # Strong Risk-Off
    except Exception:
        return 50  # Default to neutral on error