import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
import json
from push_notifications import generate_push_notification_html

def render_notifications(data_service):
    """Render the Notifications Panel for Stock Alerts & High-Impact Keywords"""
    st.header("🔔 Market Alerts & Notifications")
    
    # Get notifications from database
    notifications = data_service.get_notifications(limit=50)
    
    # Define high-impact keywords for mid-cap stocks (for display in empty state)
    # Enhanced with market impact indicators
    MARKET_MOVING_KEYWORDS = {
        # Fed policy and macro keywords - Very high impact
        "rate hike": {"market_impact": "very high", "category": "Fed Policy", "typical_move": "±1-2%"},
        "rate cut": {"market_impact": "very high", "category": "Fed Policy", "typical_move": "±1-2%"},
        "quantitative tightening": {"market_impact": "very high", "category": "Fed Policy", "typical_move": "±0.5-1%"},
        "quantitative easing": {"market_impact": "very high", "category": "Fed Policy", "typical_move": "±0.5-1%"},
        "hawkish": {"market_impact": "high", "category": "Fed Policy", "typical_move": "±0.5-1%"},
        "dovish": {"market_impact": "high", "category": "Fed Policy", "typical_move": "±0.5-1%"},
        "inflation data": {"market_impact": "high", "category": "Economic Data", "typical_move": "±0.5-1%"},
        "CPI report": {"market_impact": "very high", "category": "Economic Data", "typical_move": "±1-2%"},
        "unemployment report": {"market_impact": "high", "category": "Economic Data", "typical_move": "±0.5-1%"},
        "GDP growth": {"market_impact": "high", "category": "Economic Data", "typical_move": "±0.3-0.8%"},
        
        # Geopolitical events - High impact
        "trade war": {"market_impact": "high", "category": "Geopolitical", "typical_move": "±1-2%"},
        "military conflict": {"market_impact": "high", "category": "Geopolitical", "typical_move": "±1-3%"},
        "sanctions": {"market_impact": "medium", "category": "Geopolitical", "typical_move": "±0.5-1%"},
        "oil supply": {"market_impact": "high", "category": "Commodities", "typical_move": "±1-2%"},
        
        # FDA/regulatory keywords - Company specific but can move sectors
        "FDA approval": {"market_impact": "very high", "category": "Healthcare", "typical_move": "±15-30%"},
        "phase 3": {"market_impact": "high", "category": "Healthcare", "typical_move": "±10-20%"},
        "breakthrough designation": {"market_impact": "high", "category": "Healthcare", "typical_move": "±5-15%"},
        "fast track": {"market_impact": "medium", "category": "Healthcare", "typical_move": "±5-10%"},
        "orphan drug": {"market_impact": "medium", "category": "Healthcare", "typical_move": "±3-8%"},
        "clinical trial results": {"market_impact": "very high", "category": "Healthcare", "typical_move": "±10-40%"},
        "regulatory submission": {"market_impact": "medium", "category": "Healthcare", "typical_move": "±3-8%"},
        
        # Business/financial keywords - Company specific high impact
        "acquisition target": {"market_impact": "very high", "category": "M&A", "typical_move": "±15-30%"},
        "takeover bid": {"market_impact": "very high", "category": "M&A", "typical_move": "±15-30%"},
        "buyout": {"market_impact": "very high", "category": "M&A", "typical_move": "±20-40%"},
        "activist investor": {"market_impact": "high", "category": "Corporate", "typical_move": "±5-15%"},
        "strategic alternatives": {"market_impact": "high", "category": "Corporate", "typical_move": "±5-15%"},
        "special dividend": {"market_impact": "medium", "category": "Corporate", "typical_move": "±3-8%"},
        "stock buyback": {"market_impact": "medium", "category": "Corporate", "typical_move": "±2-5%"},
        "earnings surprise": {"market_impact": "high", "category": "Earnings", "typical_move": "±5-15%"},
        "revenue beat": {"market_impact": "medium", "category": "Earnings", "typical_move": "±3-10%"},
        "guidance raised": {"market_impact": "high", "category": "Earnings", "typical_move": "±5-10%"},
        "guidance lowered": {"market_impact": "high", "category": "Earnings", "typical_move": "±5-15%"},
        "missed expectations": {"market_impact": "high", "category": "Earnings", "typical_move": "±5-15%"},
        
        # Industry-specific keywords
        "patent approval": {"market_impact": "medium", "category": "Intellectual Property", "typical_move": "±3-8%"},
        "patent litigation": {"market_impact": "high", "category": "Legal", "typical_move": "±5-15%"},
        "major contract": {"market_impact": "high", "category": "Business", "typical_move": "±5-10%"},
        "new partnership": {"market_impact": "medium", "category": "Business", "typical_move": "±3-8%"},
        "exclusive deal": {"market_impact": "medium", "category": "Business", "typical_move": "±3-8%"},
        "supply agreement": {"market_impact": "medium", "category": "Business", "typical_move": "±2-5%"},
        
        # Analyst actions
        "rating upgrade": {"market_impact": "medium", "category": "Analyst", "typical_move": "±2-5%"},
        "price target raised": {"market_impact": "low", "category": "Analyst", "typical_move": "±1-3%"},
        "initiates coverage": {"market_impact": "low", "category": "Analyst", "typical_move": "±1-3%"},
        "strong buy": {"market_impact": "medium", "category": "Analyst", "typical_move": "±2-5%"},
        "outperform": {"market_impact": "low", "category": "Analyst", "typical_move": "±1-3%"},
        "sector outperformer": {"market_impact": "low", "category": "Analyst", "typical_move": "±1-3%"},
        "downgrade": {"market_impact": "medium", "category": "Analyst", "typical_move": "±2-6%"},
        "sell rating": {"market_impact": "medium", "category": "Analyst", "typical_move": "±3-8%"}
    }
    
    # Extract categories from keywords for filtering
    categories = list(set([v["category"] for k, v in MARKET_MOVING_KEYWORDS.items()]))
    categories.sort()
    
    # Extract impact levels for filtering
    impact_levels = ["very high", "high", "medium", "low"]
    
    # Process notifications from the database
    data_service.process_notifications()
    
    # Display high-impact notifications in a prominent section
    st.subheader("📢 Market-Moving Alerts")
    
    # Create a more detailed filtering section
    with st.expander("Advanced Filtering Options", expanded=True):
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            show_unread_only = st.checkbox("Unread only", value=True)
            selected_categories = st.multiselect("Filter by category:", 
                                               categories, 
                                               default=["Fed Policy", "M&A", "Earnings", "Healthcare"])
        
        with col2:
            selected_impacts = st.multiselect("Market impact level:", 
                                            impact_levels, 
                                            default=["very high", "high"])
            
            date_range = st.radio("Time period:", 
                                ["Today", "Last 3 days", "Last week", "All"], 
                                horizontal=True,
                                index=1)
        
        with col3:
            sort_options = ["Newest first", "Market impact", "Priority (high to low)"]
            sort_by = st.radio("Sort by:", sort_options, horizontal=True)
            
            keyword_search = st.text_input("Search alerts:", placeholder="Enter keywords...")
    
    # Get filtered notifications based on user selections
    if notifications:
        # Apply filters based on user selections
        filtered_notifications = []
        
        # Time period filter
        now = datetime.now()
        if date_range == "Today":
            time_limit = now - timedelta(days=1)
        elif date_range == "Last 3 days":
            time_limit = now - timedelta(days=3)
        elif date_range == "Last week":
            time_limit = now - timedelta(days=7)
        else:  # All
            time_limit = now - timedelta(days=365)  # Just a large value
        
        # Apply all filters
        for alert in notifications:
            # Apply read/unread filter
            if show_unread_only and alert.get("read", False):
                continue
                
            # Apply time filter
            alert_time = alert.get("timestamp", now)
            if isinstance(alert_time, str):
                try:
                    alert_time = pd.to_datetime(alert_time)
                except:
                    alert_time = now
                    
            if alert_time < time_limit:
                continue
                
            # Get keywords to determine category and impact
            alert_keywords = alert.get("keywords", [])
            if isinstance(alert_keywords, str):
                try:
                    alert_keywords = json.loads(alert_keywords.replace("'", '"'))
                except:
                    alert_keywords = [alert_keywords]
            
            if not isinstance(alert_keywords, list):
                alert_keywords = []
                
            # Find highest impact and categories for this alert
            highest_impact = "low"
            alert_categories = []
            
            for keyword in alert_keywords:
                if keyword in MARKET_MOVING_KEYWORDS:
                    keyword_data = MARKET_MOVING_KEYWORDS[keyword]
                    keyword_impact = keyword_data["market_impact"]
                    keyword_category = keyword_data["category"]
                    
                    # Check impact level filter
                    if keyword_impact not in selected_impacts:
                        continue
                        
                    # Track highest impact level
                    impact_levels_order = {"very high": 4, "high": 3, "medium": 2, "low": 1}
                    if impact_levels_order.get(keyword_impact, 0) > impact_levels_order.get(highest_impact, 0):
                        highest_impact = keyword_impact
                    
                    # Track categories
                    if keyword_category not in alert_categories:
                        alert_categories.append(keyword_category)
            
            # Check if any categories match filters
            if selected_categories and not any(cat in selected_categories for cat in alert_categories):
                continue
                
            # Add impact and category data to alert for display
            alert["impact_level"] = highest_impact
            alert["categories"] = alert_categories
            
            # Apply keyword search filter if provided
            if keyword_search and keyword_search.lower() not in alert.get("title", "").lower():
                continue
                
            # Alert passed all filters
            filtered_notifications.append(alert)
            
        # Sort appropriately based on user selection
        if sort_by == "Newest first":
            filtered_notifications.sort(key=lambda x: x.get("timestamp", datetime.now()), reverse=True)
        elif sort_by == "Market impact":
            # Sort by impact level (very high -> high -> medium -> low)
            impact_order = {"very high": 4, "high": 3, "medium": 2, "low": 1, None: 0}
            filtered_notifications.sort(key=lambda x: (impact_order.get(x.get("impact_level"), 0), 
                                                     x.get("timestamp", datetime.now())), 
                                      reverse=True)
        else:  # Priority high to low
            filtered_notifications.sort(key=lambda x: (x.get("priority", 0), 
                                                     x.get("timestamp", datetime.now())), 
                                      reverse=True)
        
        # Create a notification bell with count
        unread_count = sum(1 for alert in filtered_notifications if not alert.get("read", False))
        total_count = len(filtered_notifications)
        
        if total_count > 0:
            st.markdown(f"### 🔔 {unread_count} Unread Alerts ({total_count} Total)")
        else:
            st.info("No alerts match your current filter settings.")
            st.markdown("Try adjusting your filters or expanding the time range.")
            return
        
        # Create containers for the alerts
        for idx, alert in enumerate(filtered_notifications):
            with st.container():
                # Format the time
                timestamp = alert.get("timestamp")
                if timestamp:
                    try:
                        time_str = pd.to_datetime(timestamp).strftime("%Y-%m-%d %H:%M")
                    except:
                        time_str = str(timestamp)
                else:
                    time_str = "N/A"
                
                # Get impact level and styling
                impact_level = alert.get("impact_level", "low")
                impact_colors = {
                    "very high": "#8B0000",  # dark red
                    "high": "#FF4500",       # orange red
                    "medium": "#FF8C00",     # dark orange
                    "low": "#A0A0A0"         # grey
                }
                impact_color = impact_colors.get(impact_level, "#A0A0A0")
                
                # Create columns for alert content and action buttons
                alert_cols = st.columns([4, 1])
                
                with alert_cols[0]:
                    # Display the alert with appropriate styling
                    # Add a visual indicator for unread notifications
                    read_status = "🔵 " if not alert.get("read", False) else ""
                    
                    # Get alert categories for display
                    categories = alert.get("categories", [])
                    category_badges = ""
                    
                    for cat in categories:
                        category_badges += f'<span style="background-color: #f0f0f0; padding: 2px 6px; border-radius: 10px; font-size: 0.8em; margin-right: 5px;">{cat}</span>'
                    
                    # Show alert with styling based on sentiment
                    if alert.get("sentiment") == "positive":
                        st.success(f"{read_status}**{alert.get('title')}**")
                    elif alert.get("sentiment") == "negative":
                        st.error(f"{read_status}**{alert.get('title')}**")
                    else:
                        st.info(f"{read_status}**{alert.get('title')}**")
                    
                    # Display impact level with appropriate styling
                    impact_badge = f'<span style="color: white; background-color: {impact_color}; padding: 2px 6px; border-radius: 10px; font-size: 0.8em; font-weight: bold;">IMPACT: {impact_level.upper()}</span>'
                    
                    # Show categories and impact
                    st.markdown(f"{category_badges} {impact_badge}", unsafe_allow_html=True)
                    
                    # Show stock symbol if available
                    if alert.get("stock_symbol"):
                        st.caption(f"Symbol: **{alert.get('stock_symbol')}** | Market Cap: {alert.get('market_cap_category', 'Mid Cap')}")
                    
                    # Show matched keywords with potential market impact
                    keyword_list = alert.get("keywords", [])
                    if keyword_list:
                        keyword_impacts = []
                        for k in keyword_list:
                            if k in MARKET_MOVING_KEYWORDS:
                                typical_move = MARKET_MOVING_KEYWORDS[k]["typical_move"]
                                keyword_impacts.append(f"**{k}** ({typical_move} typical move)")
                            else:
                                keyword_impacts.append(f"**{k}**")
                                
                        keyword_str = ", ".join(keyword_impacts)
                        st.caption(f"Market-Moving Keywords: {keyword_str}")
                    
                    # Show source and timestamp
                    st.caption(f"Source: {alert.get('source', 'Unknown')} | Time: {time_str}")
                
                with alert_cols[1]:
                    # Add action buttons - Mark as read
                    if not alert.get("read", False):
                        btn_key = f"mark_read_{alert.get('id', idx)}"
                        if st.button("Mark Read", key=btn_key):
                            if alert.get("id"):
                                data_service.mark_notification_as_read(alert.get("id"))
                                st.rerun()  # Refresh the page
                
                # Add separator between alerts
                if idx < len(filtered_notifications) - 1:
                    st.markdown("---")
    else:
        st.info("No notifications at this time.")
        st.caption("Alerts will appear here when news containing keywords like 'FDA approval', 'acquisition target', 'earnings surprise' are detected.")
    
    # Add a push notification settings section
    with st.expander("Push Notifications"):
        st.markdown("### 📱 Push Notification Settings")
        
        # Check if Firebase Cloud Messaging is available
        fcm_available = data_service.notification_manager.is_fcm_available()
        
        if fcm_available:
            st.success("Firebase Cloud Messaging is configured and ready to use.")
            
            # Allow users to enable/disable different types of notifications
            st.markdown("#### Enable notifications for:")
            
            enable_market_alerts = st.checkbox("Market alerts (FDA approvals, earnings surprises, etc.)", value=True)
            enable_price_alerts = st.checkbox("Price alerts (when stocks cross price thresholds)", value=True)
            enable_market_opens = st.checkbox("Market open signals (pre-market indicators)", value=False)
            
            # Allow users to set priority thresholds
            st.markdown("#### Notification priority:")
            priority_threshold = st.slider("Minimum priority level", 1, 5, 2, 
                                         help="Only send push notifications for alerts at or above this priority level")
            
            # Let users subscribe to push notifications
            st.markdown("#### Receive notifications on your device:")
            
            # Inject the HTML/JS needed for web push notifications
            push_notification_html = generate_push_notification_html()
            st.components.v1.html(push_notification_html, height=100)
            
            # Save settings button
            if st.button("Save Notification Settings"):
                st.success("Push notification settings saved!")
        else:
            st.warning("Firebase Cloud Messaging is not configured. Push notifications are disabled.")
            st.markdown("""
            To enable push notifications, you'll need to:
            1. Set up a Firebase project
            2. Add the FCM_SERVER_KEY to the environment variables
            """)
            
            # Request the FCM Server Key
            if st.button("Configure Firebase Cloud Messaging"):
                st.info("Contact your administrator to set up Firebase Cloud Messaging integration.")
    
    # Add a settings section for configuring alerts
    with st.expander("Market-Moving Alert Settings"):
        st.markdown("### Configure Market-Moving Event Detection")
        
        # Create a two-column layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### Market Impact Levels")
            st.caption("Select the minimum level of market impact to monitor:")
            
            # Let users select impact levels
            very_high_impact = st.checkbox("Very High Impact Events (±10-40% moves)", value=True, 
                                         help="Major events like M&A, FDA approvals, clinical trial results")
            high_impact = st.checkbox("High Impact Events (±5-15% moves)", value=True,
                                    help="Important events like earnings surprises, guidance changes, patent litigation")
            medium_impact = st.checkbox("Medium Impact Events (±2-8% moves)", value=True,
                                      help="Notable events like stock buybacks, rating changes, partnership announcements")
            low_impact = st.checkbox("Low Impact Events (±1-3% moves)", value=False,
                                   help="Minor events like analyst commentary, small contract wins")
            
            # Market categories to monitor
            st.markdown("#### Market Categories")
            st.caption("Select which market event categories to monitor:")
            
            # Dynamically generate checkboxes from the MARKET_MOVING_KEYWORDS dictionary
            unique_categories = list(set(item["category"] for item in MARKET_MOVING_KEYWORDS.values()))
            unique_categories.sort()
            
            # Display as a grid of checkboxes
            for i in range(0, len(unique_categories), 2):
                checkbox_cols = st.columns(2)
                with checkbox_cols[0]:
                    if i < len(unique_categories):
                        st.checkbox(unique_categories[i], value=True, key=f"cat_{unique_categories[i]}")
                with checkbox_cols[1]:
                    if i+1 < len(unique_categories):
                        st.checkbox(unique_categories[i+1], value=True, key=f"cat_{unique_categories[i+1]}")
        
        with col2:
            # Market cap filter
            st.markdown("#### Company Size Filter")
            st.caption("Select which market cap ranges to monitor:")
            
            market_cap_options = {
                "Large Cap (>$10B)": "Companies with market cap over $10 billion. More stability, lower volatility.",
                "Mid Cap ($2B-$10B)": "Companies with market cap between $2-10 billion. Balance of growth and stability.",
                "Small Cap (<$2B)": "Companies with market cap under $2 billion. Higher growth potential but more volatile."
            }
            
            for cap, description in market_cap_options.items():
                st.checkbox(cap, value=True if "Mid Cap" in cap else False, help=description)
            
            # Add custom keywords section
            st.markdown("#### Custom Keywords")
            st.caption("Add your own market-moving keywords to monitor:")
            
            custom_keyword = st.text_input("Enter keyword or phrase:", 
                                         placeholder="e.g., restructuring, share offering")
            
            impact_options = {"very high": "Very High (±10-40%)", 
                             "high": "High (±5-15%)", 
                             "medium": "Medium (±2-8%)", 
                             "low": "Low (±1-3%)"}
            
            custom_impact = st.selectbox("Expected market impact:", 
                                       options=list(impact_options.values()),
                                       index=1)
            
            # Select a category for this keyword
            custom_category = st.selectbox("Keyword category:", 
                                         options=unique_categories,
                                         index=0)
            
            # Add button
            if st.button("Add Custom Keyword", key="add_custom_keyword_btn") and custom_keyword:
                st.success(f"Added keyword '{custom_keyword}' with {custom_impact.split(' ')[0].lower()} impact in {custom_category} category")
        
        # Educational section
        st.markdown("---")
        st.markdown("#### 🔍 Understanding Market-Moving Events")
        st.markdown("""
        ### How Events Move Markets
        
        Different types of news and events can cause varying degrees of price movement:
        
        | Event Type | Typical Move | Time Frame | Example |
        |------------|--------------|------------|---------|
        | **Very High Impact** | ±10-40% | Immediate | M&A announcements, FDA approvals, clinical trial results |
        | **High Impact** | ±5-15% | 1-2 days | Earnings surprises, guidance changes, patent litigation |
        | **Medium Impact** | ±2-8% | 1-3 days | Stock buybacks, significant partnerships, major contracts |
        | **Low Impact** | ±1-3% | Variable | Analyst ratings, minor operational updates |
        
        ### Most Significant Market-Moving Events
        
        1. **Fed Policy Changes** - Interest rate decisions, quantitative easing/tightening announcements
        2. **Economic Data Surprises** - Unexpected inflation, employment, or GDP growth numbers
        3. **M&A Activity** - Acquisitions, takeovers, and buyout offers
        4. **FDA Approvals** - Particularly for biotech and pharmaceutical companies
        5. **Major Earnings Surprises** - Especially when accompanied by guidance changes
        6. **Geopolitical Events** - Trade wars, military conflicts, sanctions
        """)
        
        # Save settings button with more professional styling
        if st.button("Save Notification Settings", key="save_alert_settings_btn", type="primary"):
            st.success("Market-moving alert settings saved successfully!")
            st.caption("Your notification preferences have been updated. You will now receive alerts based on your selected criteria.")
    
    # Show historical alerts
    with st.expander("Alert History"):
        st.markdown("### Previous Alerts")
        
        # Get all notifications including read ones
        all_notifications = data_service.get_notifications(limit=50, unread_only=False)
        
        if all_notifications:
            # Convert to dataframe for easier display
            alert_data = []
            for alert in all_notifications:
                keywords_str = ", ".join(alert.get("keywords", [])) if isinstance(alert.get("keywords"), list) else str(alert.get("keywords", ""))
                alert_data.append({
                    "Date": pd.to_datetime(alert.get("timestamp")).strftime("%Y-%m-%d") if alert.get("timestamp") else "N/A",
                    "Title": alert.get("title", ""),
                    "Source": alert.get("source", ""),
                    "Keywords": keywords_str,
                    "Status": "Read" if alert.get("read") else "Unread",
                    "Priority": "High" if alert.get("priority", 0) > 1 else "Normal"
                })
            
            if alert_data:
                df = pd.DataFrame(alert_data)
                st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.info("No historical alerts yet. They will appear here once notifications are processed.")