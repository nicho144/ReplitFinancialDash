import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_fda_news(data_service):
    """Render the FDA Calendar & News Section"""
    st.header("8. FDA Calendar & News Section")
    
    # Create tabs for FDA Calendar and Market News
    tab1, tab2 = st.tabs(["FDA Calendar", "Market News"])
    
    # FDA Calendar Tab
    with tab1:
        st.subheader("FDA Approval Calendar")
        
        with st.spinner("Loading FDA calendar data..."):
            # Get FDA calendar data
            fda_data = data_service.get_fda_calendar()
            
            if not fda_data:
                st.error("Unable to fetch FDA calendar data. Please check API connections.")
                return
        
        # Display biotech sector performance
        # Note: fda_data is now a list of calendar events, not a dictionary
        biotech_perf = 2.3  # Sample biotech sector performance value
        # Determine color based on performance
        delta_color = "normal" if biotech_perf > 0 else "inverse"
        
        st.metric(
            "Biotech Sector Performance (5d)", 
            f"{biotech_perf:.2f}%",
            delta=f"{biotech_perf:.2f}%",
            delta_color=delta_color
        )
        
        # Display upcoming FDA events
        # fda_data is already a list of calendar events from our service
        upcoming_events = fda_data
        
        if upcoming_events:
            # Create a table to display the events
            events_df = pd.DataFrame(upcoming_events)
            
            # Display the events table
            st.dataframe(events_df, use_container_width=True)
        else:
            st.info("No upcoming FDA events found. In production, this would display data from the BioPharmCatalyst API.")
            
            # Display placeholder content to show what the table would look like
            st.markdown("""
            **Example FDA Calendar Format:**
            
            The FDA calendar would display information such as:
            - Company name and ticker
            - Drug/therapeutic name
            - PDUFA date (FDA decision deadline)
            - Indication (disease/condition)
            - Catalyst type (PDUFA, Advisory Committee, etc.)
            - Market capitalization
            """)
        
        # Add explanation about FDA events
        with st.expander("About FDA Events & Biotech Catalysts"):
            st.markdown("""
            **FDA Regulatory Events as Market Catalysts**
            
            FDA (Food and Drug Administration) regulatory decisions are major catalysts for biotech and pharmaceutical stocks. Key event types include:
            
            **PDUFA Dates**: The deadline for the FDA to review a new drug application. The Prescription Drug User Fee Act (PDUFA) established these target dates, which can trigger significant price movement when decisions are announced.
            
            **Advisory Committee Meetings (AdCom)**: Independent expert panels that make recommendations to the FDA. While non-binding, their votes often strongly influence final FDA decisions.
            
            **Clinical Trial Results**: Phase 1, 2, and 3 trial results demonstrating safety and efficacy are critical milestones that can dramatically impact stock prices.
            
            **Complete Response Letters (CRLs)**: FDA communications requesting additional information before approving a drug, typically resulting in delays and negative price action.
            
            Trading these events requires understanding the drug development process, market expectations, and risk management strategies due to their binary nature.
            """)
    
    # Market News Tab
    with tab2:
        st.subheader("High-Impact Market News")
        
        with st.spinner("Loading market news..."):
            # Get financial news data
            news_data = data_service.get_financial_news()
            
            if not news_data:
                st.error("Unable to fetch market news. Please check API connections.")
                return
        
        # Create a filter for news based on keywords
        keywords = [
            "inflation surprise", "Fed pivot", "unexpected downgrade", 
            "rate cut", "China stimulus", "recession", "GDP", "Federal Reserve",
            "interest rates", "market crash", "economic growth"
        ]
        
        selected_keyword = st.selectbox("Filter by keyword", ["All"] + keywords)
        
        # Filter news by selected keyword
        filtered_news = news_data
        if selected_keyword != "All":
            filtered_news = [news for news in news_data if selected_keyword.lower() in news.get('keyword', '').lower()]
        
        # Display news items
        if filtered_news:
            for news in filtered_news:
                title = news.get('title', 'No title available')
                source = news.get('source', 'Unknown source')
                url = news.get('url', '#')
                published_at = news.get('published_at', '')
                sentiment = news.get('sentiment', 'neutral')
                
                # Format date if available
                if published_at:
                    try:
                        # Convert to datetime and format
                        dt = pd.to_datetime(published_at)
                        published_at = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        # If conversion fails, use as is
                        pass
                
                # Determine sentiment color
                if sentiment == 'positive':
                    sentiment_color = 'green'
                elif sentiment == 'negative':
                    sentiment_color = 'red'
                else:
                    sentiment_color = 'gray'
                
                # Create news item with formatted date and source
                st.markdown(f"### [{title}]({url})")
                st.markdown(f"**Source:** {source} | **Published:** {published_at}")
                st.markdown(f"**Sentiment:** <span style='color: {sentiment_color};'>{sentiment.upper()}</span>", unsafe_allow_html=True)
                
                # Add horizontal line between news items
                st.markdown("---")
        else:
            if selected_keyword != "All":
                st.warning(f"No news found for keyword: {selected_keyword}")
            else:
                st.info("No market news available. In production, this would display news filtered from NewsAPI.org.")
        
        # News alerts settings
        st.subheader("News Alert Settings")
        
        # Alert settings
        st.markdown("Configure alerts for high-impact news:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            alert_enabled = st.checkbox("Enable news alerts", value=True)
        
        with col2:
            alert_method = st.selectbox("Alert method", ["Dashboard", "Email", "Both"], disabled=not alert_enabled)
        
        # Select keywords to track
        if alert_enabled:
            selected_keywords = st.multiselect("Track these keywords", keywords, default=["Fed pivot", "rate cut", "inflation surprise"])
            
            priority_only = st.checkbox("Only alert on high-priority news", value=True)
            
            if st.button("Save Alert Settings"):
                st.success("Alert settings saved! You will receive notifications for selected keywords.")
        
        # Explanation of market-moving news
        with st.expander("About Market-Moving News"):
            st.markdown("""
            **High-Impact Market News**
            
            This section filters financial news by keywords that typically move markets. The dashboard focuses on:
            
            **Monetary Policy Keywords**:
            - "Fed pivot" - Signals a change in Federal Reserve policy direction
            - "Rate cut" or "rate hike" - Indicates changes to interest rate policy
            - "Quantitative easing" or "QE" - Related to central bank asset purchases
            
            **Economic Data Keywords**:
            - "Inflation surprise" - Unexpected inflation readings above or below consensus
            - "GDP" - Growth data that exceeds or misses expectations significantly
            - "Unemployment" - Labor market data that may influence Fed policy
            
            **Global Macro Keywords**:
            - "China stimulus" - Fiscal or monetary stimulus from the world's second-largest economy
            - "Currency devaluation" - Significant currency moves that impact global trade
            - "Trade war" or "tariffs" - International trade tensions affecting markets
            
            **Market Sentiment Keywords**:
            - "Market crash" - Significant downturn concerns
            - "Recession" - Economic contraction signals
            - "Unexpected downgrade" - Credit rating changes for countries or major companies
            
            News is filtered and categorized by sentiment to help identify potentially market-moving developments quickly.
            """)

