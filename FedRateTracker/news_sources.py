"""
News sources integration for financial dashboard
Supports multiple providers:
- NewsAPI
- MarketAux
- Finnhub
"""

import os
import requests
from datetime import datetime, timedelta
import json

class NewsProvider:
    """Base class for news providers"""
    def __init__(self):
        self.name = "Base Provider"
        
    def get_news(self, **kwargs):
        """Get financial news"""
        raise NotImplementedError("Subclasses must implement this method")
        
    def is_available(self):
        """Check if the provider is configured and available"""
        return False

class NewsAPIProvider(NewsProvider):
    """NewsAPI integration"""
    def __init__(self):
        super().__init__()
        self.name = "NewsAPI"
        self.api_key = os.environ.get("NEWSAPI_KEY")
        self.base_url = "https://newsapi.org/v2/everything"
        
    def is_available(self):
        return self.api_key is not None
        
    def get_news(self, query="finance", days=3, limit=20, **kwargs):
        """Get financial news from NewsAPI"""
        if not self.is_available():
            return []
            
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        params = {
            "q": query,
            "apiKey": self.api_key,
            "from": from_date,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": limit
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                
                # Format the results
                news = []
                for article in articles:
                    news.append({
                        "title": article.get("title"),
                        "description": article.get("description"),
                        "source": article.get("source", {}).get("name", "Unknown"),
                        "url": article.get("url"),
                        "published_at": article.get("publishedAt"),
                        "sentiment": "neutral"  # Default sentiment
                    })
                return news
            else:
                print(f"NewsAPI error: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Error getting news from NewsAPI: {e}")
            return []

class MarketAuxProvider(NewsProvider):
    """MarketAux API integration"""
    def __init__(self):
        super().__init__()
        self.name = "MarketAux"
        self.api_key = os.environ.get("MARKETAUX_API_KEY")
        self.base_url = "https://api.marketaux.com/v1/news/all"
        
    def is_available(self):
        return self.api_key is not None
        
    def get_news(self, symbols="AAPL,MSFT,GOOGL", days=7, limit=20, **kwargs):
        """Get financial news from MarketAux"""
        if not self.is_available():
            return []
            
        params = {
            "api_token": self.api_key,
            "symbols": symbols,
            "limit": limit,
            "language": "en",
            "published_after": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                articles = data.get("data", [])
                
                # Format the results
                news = []
                for article in articles:
                    # Extract entities and sentiments
                    entities = article.get("entities", [])
                    keywords = []
                    sentiment = "neutral"
                    
                    for entity in entities:
                        if entity.get("highlight"):
                            keywords.append(entity.get("name"))
                        
                        # Use sentiment from the entity with highest relevance
                        if entity.get("sentiment_score") and abs(entity.get("sentiment_score", 0)) > 0.3:
                            score = entity.get("sentiment_score", 0)
                            if score > 0.3:
                                sentiment = "positive"
                            elif score < -0.3:
                                sentiment = "negative"
                    
                    news.append({
                        "title": article.get("title"),
                        "description": article.get("description"),
                        "source": article.get("source"),
                        "url": article.get("url"),
                        "published_at": article.get("published_at"),
                        "sentiment": sentiment,
                        "keywords": keywords
                    })
                return news
            else:
                print(f"MarketAux API error: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Error getting news from MarketAux: {e}")
            return []

class FinnhubProvider(NewsProvider):
    """Finnhub API integration"""
    def __init__(self):
        super().__init__()
        self.name = "Finnhub"
        self.api_key = os.environ.get("FINNHUB_API_KEY")
        self.base_url = "https://finnhub.io/api/v1/news"
        
    def is_available(self):
        return self.api_key is not None
        
    def get_news(self, category="general", days=3, limit=20, **kwargs):
        """Get financial news from Finnhub"""
        if not self.is_available():
            return []
            
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "category": category,
            "token": self.api_key,
            "from": from_date,
            "to": to_date
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            if response.status_code == 200:
                articles = response.json()
                
                # Format the results and limit to requested count
                news = []
                for article in articles[:limit]:
                    # Determine sentiment based on headline
                    headline = article.get("headline", "").lower()
                    
                    # Simple keyword-based sentiment analysis
                    positive_keywords = ['growth', 'increase', 'rise', 'higher', 'positive', 'boost']
                    negative_keywords = ['decline', 'fall', 'drop', 'lower', 'negative', 'risk', 'concern']
                    
                    sentiment = 'neutral'
                    positive_count = sum(1 for word in positive_keywords if word in headline)
                    negative_count = sum(1 for word in negative_keywords if word in headline)
                    
                    if positive_count > negative_count:
                        sentiment = 'positive'
                    elif negative_count > positive_count:
                        sentiment = 'negative'
                    
                    news.append({
                        "title": article.get("headline"),
                        "description": article.get("summary"),
                        "source": article.get("source"),
                        "url": article.get("url"),
                        "published_at": datetime.fromtimestamp(article.get("datetime", 0)).isoformat(),
                        "sentiment": sentiment
                    })
                return news
            else:
                print(f"Finnhub API error: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Error getting news from Finnhub: {e}")
            return []

class NewsManager:
    """Manager for handling multiple news sources with fallback"""
    def __init__(self):
        self.providers = [
            NewsAPIProvider(),
            MarketAuxProvider(),
            FinnhubProvider()
        ]
        
    def get_available_providers(self):
        """Get a list of available providers"""
        return [provider for provider in self.providers if provider.is_available()]
        
    def get_news(self, **kwargs):
        """Get news from the first available provider"""
        available_providers = self.get_available_providers()
        
        if not available_providers:
            print("No news providers available - all require API keys")
            return []
            
        # Try each provider in order
        for provider in available_providers:
            print(f"Getting news from {provider.name}")
            news = provider.get_news(**kwargs)
            if news:
                return news
        
        return []