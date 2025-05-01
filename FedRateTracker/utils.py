import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

def format_number(value, decimals=2, prefix='', suffix=''):
    """Format a number with specified decimals and optional prefix/suffix"""
    if value is None:
        return "N/A"
    
    try:
        formatted = f"{prefix}{value:.{decimals}f}{suffix}"
        return formatted
    except:
        return "N/A"

def format_percentage(value, decimals=2):
    """Format a value as a percentage"""
    return format_number(value, decimals, suffix='%')

def color_by_value(value, positive_is_good=True):
    """Return color based on value (positive/negative)"""
    if value is None:
        return "gray"
    
    if (value > 0 and positive_is_good) or (value < 0 and not positive_is_good):
        return "green"
    elif (value < 0 and positive_is_good) or (value > 0 and not positive_is_good):
        return "red"
    else:
        return "gray"

def create_time_series_chart(data, title, y_label, x_key='timestamp', y_key='value', color='blue'):
    """Create a time series chart using Plotly"""
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=[item[x_key] for item in data],
            y=[item[y_key] for item in data],
            mode='lines',
            name=y_label,
            line=dict(color=color, width=2)
        )
    )
    
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title=y_label,
        template='plotly_white',
        height=400,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

def create_spread_chart(data, title, y1_label, y2_label, spread_label, 
                       x_key='timestamp', y1_key='y1', y2_key='y2', spread_key='spread'):
    """Create a chart showing two yields and their spread"""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add traces for first yield
    fig.add_trace(
        go.Scatter(
            x=[item[x_key] for item in data],
            y=[item[y1_key] for item in data],
            mode='lines',
            name=y1_label,
            line=dict(color='blue', width=2)
        ),
        secondary_y=False
    )
    
    # Add traces for second yield
    fig.add_trace(
        go.Scatter(
            x=[item[x_key] for item in data],
            y=[item[y2_key] for item in data],
            mode='lines',
            name=y2_label,
            line=dict(color='red', width=2)
        ),
        secondary_y=False
    )
    
    # Add trace for spread
    fig.add_trace(
        go.Scatter(
            x=[item[x_key] for item in data],
            y=[item[spread_key] for item in data],
            mode='lines',
            name=spread_label,
            line=dict(color='green', width=2, dash='dot')
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        template='plotly_white',
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    fig.update_yaxes(title_text="Yield (%)", secondary_y=False)
    fig.update_yaxes(title_text="Spread (bp)", secondary_y=True)
    
    return fig

def create_heatmap(data, x_labels, y_labels, z_values, title):
    """Create a heatmap for visualizing matrices of data"""
    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=x_labels,
        y=y_labels,
        colorscale='RdYlGn',
        colorbar=dict(title="Value")
    ))
    
    fig.update_layout(
        title=title,
        template='plotly_white',
        height=400,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

def interpret_yield_curve(spread_2y_10y, spread_change):
    """Interpret the yield curve shape and its implications"""
    status = "normal"
    message = ""
    bullish_for_gold = False
    
    if spread_2y_10y < 0:
        status = "inverted"
        message = "Yield curve is inverted (2Y > 10Y), historically signaling recession risk."
        if spread_change < 0:
            message += " Inversion is deepening, suggesting increasing economic concerns."
            bullish_for_gold = True
        else:
            message += " Inversion is lessening, potentially signaling easing recession fears."
            bullish_for_gold = False
    else:
        if spread_2y_10y < 0.5:
            status = "flat"
            message = "Yield curve is relatively flat, suggesting economic uncertainty."
            if spread_change < 0:
                message += " Curve is flattening further, which may indicate slowing growth."
                bullish_for_gold = True
            else:
                message += " Curve is steepening from flat levels, potentially indicating improving growth."
                bullish_for_gold = False
        else:
            status = "steep"
            message = "Yield curve is steep, typically suggesting economic growth."
            if spread_change > 0:
                message += " Curve is steepening further, potentially indicating stronger growth expectations."
                bullish_for_gold = False
            else:
                message += " Curve is flattening from steep levels, which may indicate moderating growth."
                bullish_for_gold = True
    
    return {
        "status": status,
        "message": message,
        "bullish_for_gold": bullish_for_gold
    }

def interpret_volatility(vix, realized_vol, vrp):
    """Interpret volatility metrics and their implications for the market"""
    interpretation = ""
    options_status = ""
    
    if vix is None or realized_vol is None or vrp is None:
        return "Insufficient volatility data available"
    
    if vrp > 1.3:
        options_status = "Very Expensive"
        interpretation = "Options appear significantly overpriced relative to realized volatility. This often occurs during fear-driven markets but may present selling opportunities."
    elif vrp > 1.1:
        options_status = "Expensive"
        interpretation = "Options are trading at a premium to realized volatility. Markets may be pricing in future uncertainty."
    elif vrp < 0.9:
        options_status = "Cheap"
        interpretation = "Options appear underpriced relative to realized volatility. This might present buying opportunities if volatility increases."
    elif vrp < 0.7:
        options_status = "Very Cheap"
        interpretation = "Options are significantly underpriced relative to historical patterns. This can occur in complacent markets but presents potential value for options buyers."
    else:
        options_status = "Fair Value"
        interpretation = "Options are priced in line with realized volatility, suggesting balanced risk perception in the market."
    
    if vix > 30:
        interpretation += " High VIX levels indicate significant market fear and uncertainty."
    elif vix < 15:
        interpretation += " Low VIX levels suggest market complacency and potentially higher risk of unexpected moves."
    
    return f"{options_status}: {interpretation}"

def determine_capital_flow(real_rates, yield_curve_status, breadth_indicators, fed_posture):
    """Determine likely capital flow direction based on multiple indicators"""
    # This is a simplified version of what would be a more complex model in production
    
    # Initialize scores (higher = more favorable)
    gold_score = 0
    bonds_score = 0
    equities_score = 0
    
    # Real rates impact (lower real rates typically favor gold)
    if real_rates < 0:
        gold_score += 2
        equities_score += 1
    elif real_rates < 1:
        gold_score += 1
        equities_score += 1
    else:
        bonds_score += 1
    
    # Yield curve impact
    if yield_curve_status == "inverted":
        bonds_score += 2
        gold_score += 1
        equities_score -= 1
    elif yield_curve_status == "flat":
        bonds_score += 1
        gold_score += 1
    elif yield_curve_status == "steep":
        equities_score += 1
    
    # Market breadth impact
    if breadth_indicators == "positive":
        equities_score += 2
    elif breadth_indicators == "negative":
        bonds_score += 1
        gold_score += 1
    
    # Fed posture impact
    if fed_posture == "hawkish":
        bonds_score += 1
        equities_score -= 1
    elif fed_posture == "dovish":
        gold_score += 1
        equities_score += 1
    
    # Determine highest scoring asset
    scores = {
        "Gold": gold_score,
        "Bonds": bonds_score,
        "Equities": equities_score
    }
    
    # Sort by score (descending)
    sorted_assets = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "primary_flow": sorted_assets[0][0],
        "secondary_flow": sorted_assets[1][0],
        "scores": scores
    }
