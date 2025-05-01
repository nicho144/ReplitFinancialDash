# Deployment Guide - Creating a New Domain

This guide explains how to deploy your Market Intelligence Dashboard to a new domain while preserving your existing deployment.

## Step-by-Step Instructions

### 1. Fork the Project

1. Go to your Replit dashboard
2. Click "Create" or "+" button
3. Select "Import from GitHub" or use the template feature
4. Import this project to create a new copy

### 2. Configure Environment

Make sure all required environment variables are set:

1. Go to the "Secrets" tab in your Replit project
2. Add the following secrets:
   - `FRED_API_KEY` - For accessing Federal Reserve economic data
   - `NEWSAPI_KEY` - For accessing financial news API

### 3. Deploy to a New Domain

1. Go to the "Deployment" tab in your new Replit project
2. Click "Deploy"
3. Choose "Create new deployment" (this is the key step to preserve your existing deployment)
4. Configure your deployment:
   - Name: Choose a descriptive name (e.g., "market-intelligence-prod")
   - Domain: Either use the provided Replit subdomain or connect a custom domain
   - Environment: Choose "Production"

### 4. Domain Management

If you want to use a custom domain:

1. In the deployment settings, click "Connect custom domain"
2. Enter your domain name (e.g., market-intel.yourdomain.com)
3. Follow the DNS configuration instructions to point your domain to Replit

### 5. Verify Database Connection

The application automatically uses the Replit PostgreSQL database. After deployment:

1. The app will create all necessary tables on first run
2. No manual database configuration is needed
3. Data will be stored in this new deployment's database (separate from your original deployment)

### 6. Post-Deployment Verification

After deployment is complete:

1. Visit your new domain
2. Ensure all components load correctly
3. Verify that API connections are working (Treasury data, news feeds, etc.)
4. Check that notifications are being processed

## Maintaining Multiple Deployments

You can maintain multiple deployments (e.g., development, staging, production) by:

1. Creating branches in your repository
2. Deploying different branches to different domains
3. Using environment variables to control behavior based on deployment environment

## Troubleshooting

If you encounter issues:

1. Check the Replit logs for any error messages
2. Verify all required API keys are set correctly in Secrets
3. Ensure the Streamlit server is running on port 5000
4. Check for any network or API rate limiting issues

Need help? Contact support at example@domain.com