# Market Intelligence Dashboard

A sophisticated financial markets intelligence platform leveraging advanced data processing and predictive analytics to provide comprehensive market insights for traders and investors.

## Features

- Real-time Treasury Yield Curve analysis with 2Y-10Y and 2Y-5Y spread tracking
- Fed Funds Rate monitoring with implied rate forecasting
- Market breadth and volatility analysis including VIX and SKEW indicators
- Gold price analysis relative to Treasury yields
- Risk assessment dashboard with comprehensive market signals
- Financial news feed with keyword-based notifications
- Push notifications for market-moving news

## Deployment Instructions

### How to Deploy to a New Domain (Preserving Your Current Deployment)

1. **Fork this Repl**: Create a fork/copy of this project to have a separate instance
   - Go to the Replit dashboard
   - Create a new repl and import from this repository

2. **Configure Your New Deployment**:
   - Go to the "Deployment" tab in your new Replit project
   - Click on "Deploy"
   - Choose "Create New Deployment"
   - Give your deployment a unique name
   - Select domain settings:
     - Use a Replit subdomain or connect a custom domain
     - This will create a new deployment without affecting your existing one

3. **Environment Variables**:
   - Ensure all necessary environment variables (API keys) are set in the Secrets section
   - Required keys include:
     - `FRED_API_KEY` - For Federal Reserve economic data
     - `NEWSAPI_KEY` - For accessing financial news

4. **Database Connection**:
   - The application uses the built-in PostgreSQL database
   - No additional configuration needed as this is handled automatically by Replit

## Workflow Structure

- The application runs on Streamlit with server port 5000
- Data is refreshed automatically at appropriate intervals
- The PostgreSQL database stores historical data and notifications

## Technology Stack

- Python-driven data analysis
- Streamlit web application framework
- PostgreSQL database for data persistence
- Integration with financial data sources (FRED, Yahoo Finance)
- Real-time news integration via NewsAPI