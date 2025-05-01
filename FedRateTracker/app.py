import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# Import components
from components.risk_assessment import render_risk_assessment
from components.fed_funds_rate import render_fed_funds_module
from components.treasury_spreads import render_treasury_spreads
from components.enhanced_treasury_curve import render_enhanced_treasury_curve, render_unusual_options_activity
from components.market_open_signals import render_market_signals
from components.market_breadth import render_market_breadth
from components.market_volatility import render_market_volatility
from components.futures_fair_value import render_futures_fair_value
from components.macro_interpretation import render_macro_interpretation
from components.flow_direction import render_flow_direction
from components.fda_news import render_fda_news
from components.market_snapshot import render_market_snapshot
from components.notifications import render_notifications
from components.spy_expected_range import render_spy_range_chart
from components.gold_analysis import render_gold_analysis

# Import data and database services
from data_service import DataService
from database import Database

# Set page configuration for better presentation and scrolling
st.set_page_config(
    page_title="Financial Markets Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",  # Make more space for content
    menu_items={
        'About': 'Financial Markets Analysis Dashboard with live data connections'
    }
)

# Initialize services
db = Database()
# Force table creation
db.create_tables()

# Create some initial notifications for testing
from datetime import datetime, timedelta

# Sample news items with high-impact keywords for testing
sample_notifications = [
    {
        "timestamp": datetime.now(),
        "title": "FDA grants fast track designation to XYZ Pharma (XYZP) for cancer drug",
        "source": "MarketWatch",
        "url": "https://example.com/news/1",
        "keywords": ["fast track", "FDA approval"],
        "sentiment": "positive",
        "market_cap_category": "Mid Cap",
        "stock_symbol": "XYZP",
        "priority": 2
    },
    {
        "timestamp": datetime.now() - timedelta(hours=3),
        "title": "Analyst initiates coverage of ABC Biotech with strong buy rating",
        "source": "Benzinga",
        "url": "https://example.com/news/2",
        "keywords": ["initiates coverage", "strong buy"],
        "sentiment": "positive", 
        "market_cap_category": "Mid Cap",
        "stock_symbol": "ABCB",
        "priority": 2
    },
    {
        "timestamp": datetime.now() - timedelta(hours=5),
        "title": "DEF Industries announces strategic alternatives review",
        "source": "CNBC",
        "url": "https://example.com/news/3",
        "keywords": ["strategic alternatives"],
        "sentiment": "neutral",
        "market_cap_category": "Mid Cap", 
        "stock_symbol": "DEFI",
        "priority": 1
    },
    {
        "timestamp": datetime.now() - timedelta(days=1),
        "title": "GHI Corp reports earnings surprise, revenue beat expectations",
        "source": "Bloomberg",
        "url": "https://example.com/news/4",
        "keywords": ["earnings surprise", "revenue beat"],
        "sentiment": "positive",
        "market_cap_category": "Mid Cap",
        "stock_symbol": "GHIC",
        "priority": 2
    }
]

for notification in sample_notifications:
    db.store_notification(
        notification["timestamp"],
        notification["title"],
        notification["source"],
        notification["url"],
        notification["keywords"],
        notification["sentiment"],
        notification["market_cap_category"],
        notification["stock_symbol"],
        notification["priority"]
    )

data_service = DataService(db)

# Process real-time news and generate market alerts when the app starts
if 'initial_data_processed' not in st.session_state:
    try:
        # Fetch real financial news using NewsAPI
        st.toast('Fetching latest financial news...', icon='📰')
        news_data = data_service.get_financial_news()
        
        # Process news for notifications based on high-impact keywords
        st.toast('Processing market news for alerts...', icon='🔍')
        data_service.process_notifications()
        
        # Generate market alerts based on current conditions
        st.toast('Analyzing market conditions for alerts...', icon='📊')
        alerts = data_service.generate_market_alerts()
        
        # Mark initial data processing as complete
        st.session_state.initial_data_processed = True
        st.toast('Financial data processing complete!', icon='✅')
    except Exception as e:
        st.error(f"Error processing initial financial data: {e}")

# Sidebar for settings and controls
with st.sidebar:
    st.title("Financial Dashboard")
    st.subheader("Real-time Market Analysis")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=True)
    
    # Date range selector for historical data
    st.subheader("Historical Data Range")
    date_range = st.date_input(
        "Select date range",
        value=(
            pd.to_datetime(datetime.now().date()) - pd.Timedelta(days=30),
            pd.to_datetime(datetime.now().date())
        ),
        max_value=datetime.now().date()
    )
    
    # Force refresh button
    if st.button("Force Refresh Data"):
        data_service.refresh_all_data()
        st.success("Data refreshed!")
    
    # About section
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This dashboard provides real-time financial market data and analysis tools for 
    trading insights. It connects to live market data and performs calculations to help
    with market interpretation.
    """)

# Main dashboard layout with streamlined presentation
st.title("Financial Markets Dashboard")
st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Risk Assessment - full width at the top (summary view)
render_risk_assessment(data_service)

# Add a divider for visual separation
st.markdown("---")

# Create tabs for better organization and scrolling
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏦 Fed & Rates", 
    "📊 Market Metrics", 
    "📈 Technical Analysis", 
    "🌡️ Yield Curve", 
    "🥇 Gold Analysis",
    "📰 News & Events"
])

# Tab 1: Fed Funds Rate and Treasury Spreads
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        render_fed_funds_module(data_service)
    with col2:
        render_treasury_spreads(data_service)

# Tab 2: Market Signals, Volatility and Market Breadth
with tab2:
    # First add the VIX and Volatility Analysis section (full width)
    render_market_volatility(data_service)
    
    # Add divider
    st.markdown("---")
    
    # Then add Market Signals and Market Breadth in two columns
    col1, col2 = st.columns(2)
    with col1:
        render_market_signals(data_service)
    with col2:
        render_market_breadth(data_service)

# Tab 3: Futures Fair Value, SPY Chart, Options Activity and Macro Interpretation
with tab3:
    # First add the SPY chart with expected range - full width for better visualization
    render_spy_range_chart(data_service)
    
    # Add the Unusual Options Activity component
    st.markdown("---")
    render_unusual_options_activity()
    
    # Divider
    st.markdown("---")
    
    # Then add the other components in two columns
    col1, col2 = st.columns(2)
    with col1:
        render_futures_fair_value(data_service)
    with col2:
        render_macro_interpretation(data_service)

# Tab 4: Enhanced Treasury Yield Curve Analysis
with tab4:
    # Render the enhanced treasury yield curve component
    render_enhanced_treasury_curve(data_service)

# Tab 5: Gold Analysis Section
with tab5:
    # Render the gold analysis component
    render_gold_analysis(data_service)

# Tab 6: Flow Direction, Notifications, and FDA/News Section
with tab6:
    # Add notifications component at the top of the News tab
    render_notifications(data_service)
    
    st.markdown("---")  # Divider
    
    # Original flow direction and FDA news components
    col1, col2 = st.columns(2)
    with col1:
        render_flow_direction(data_service)
    with col2:
        render_fda_news(data_service)

# Add a divider for visual separation
st.markdown("---")

# Add Market Snapshot at the bottom of the page
# This component provides a comprehensive visual summary of key market metrics
render_market_snapshot(data_service)

# Auto-refresh logic
if auto_refresh:
    time.sleep(2)  # Small delay to prevent hammering the server
    st.empty()
    st.rerun()

# End of the application
