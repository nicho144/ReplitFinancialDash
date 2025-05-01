import psycopg2
import os
import pandas as pd
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        # Connect to PostgreSQL using DATABASE_URL environment variable
        self.is_sqlite = False
        try:
            # First try with the DATABASE_URL environment variable
            database_url = os.environ.get('DATABASE_URL')
            if database_url:
                self.conn = psycopg2.connect(database_url)
            else:
                # Fallback to individual connection parameters
                self.conn = psycopg2.connect(
                    host=os.environ.get('PGHOST', ''),
                    port=os.environ.get('PGPORT', ''),
                    user=os.environ.get('PGUSER', ''),
                    password=os.environ.get('PGPASSWORD', ''),
                    database=os.environ.get('PGDATABASE', '')
                )
            print("Successfully connected to PostgreSQL database")
        except Exception as e:
            print(f"Error connecting to PostgreSQL database: {e}")
            # Create a fallback SQLite database for testing
            import sqlite3
            print("Using SQLite fallback database for testing")
            self.conn = sqlite3.connect('financial_data.db')
            self.is_sqlite = True
            print("Successfully connected to SQLite database")
        self.cursor = self.conn.cursor()
        
        # Auto-create tables on initialization
        self.create_tables()
    
    def __del__(self):
        """Close database connection when object is destroyed"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def tables_exist(self):
        """Check if required tables exist in the database"""
        required_tables = ['fed_funds_data', 'treasury_yield_data', 'notifications']
        
        if self.is_sqlite:
            # For SQLite, query the sqlite_master table
            self.cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
            """)
        else:
            # For PostgreSQL, use information_schema
            self.cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
        tables = [row[0] for row in self.cursor.fetchall()]
        
        # Debug tables in database
        missing_tables = [table for table in required_tables if table not in tables]
        if missing_tables:
            print(f"Missing tables: {missing_tables}")
            print(f"Found tables: {tables}")
            
        return all(table in tables for table in required_tables)
    
    def create_tables(self):
        """Create necessary database tables if they don't exist"""
        try:
            if self.is_sqlite:
                # SQLite version of tables
                
                # Fed Funds Futures data table
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS fed_funds_data (
                    timestamp TIMESTAMP,
                    ticker TEXT,
                    price FLOAT,
                    implied_rate FLOAT,
                    PRIMARY KEY (timestamp, ticker)
                )
                ''')
                
                # Treasury Yield data table
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS treasury_yield_data (
                    timestamp TIMESTAMP,
                    yield_2y FLOAT,
                    yield_5y FLOAT,
                    yield_10y FLOAT,
                    yield_30y FLOAT,
                    spread_2y_10y FLOAT,
                    spread_2y_5y FLOAT,
                    PRIMARY KEY (timestamp)
                )
                ''')
                
                # Market Breadth data table
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_breadth_data (
                    timestamp TIMESTAMP,
                    tick FLOAT,
                    trin FLOAT,
                    skew FLOAT,
                    vix FLOAT,
                    realized_vol FLOAT,
                    vrp FLOAT,
                    PRIMARY KEY (timestamp)
                )
                ''')
                
                # Futures Fair Value data table
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS futures_fair_value_data (
                    timestamp TIMESTAMP,
                    es_futures FLOAT,
                    spx FLOAT,
                    fair_value FLOAT,
                    premium_discount FLOAT,
                    PRIMARY KEY (timestamp)
                )
                ''')
                
                # Financial News table
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS financial_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    title TEXT,
                    source TEXT,
                    url TEXT UNIQUE,
                    sentiment TEXT
                )
                ''')
                
                # Notifications table for high-impact alerts - for SQLite we store keywords as regular text
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    title TEXT,
                    source TEXT,
                    url TEXT,
                    keywords TEXT,
                    sentiment TEXT,
                    read BOOLEAN DEFAULT 0,
                    market_cap_category TEXT,
                    stock_symbol TEXT,
                    priority INTEGER DEFAULT 1
                )
                ''')
            else:
                # PostgreSQL version of tables
                
                # Fed Funds Futures data table
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS fed_funds_data (
                    timestamp TIMESTAMP,
                    ticker TEXT,
                    price FLOAT,
                    implied_rate FLOAT,
                    PRIMARY KEY (timestamp, ticker)
                )
                ''')
                
                # Treasury Yield data table
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS treasury_yield_data (
                    timestamp TIMESTAMP,
                    yield_2y FLOAT,
                    yield_5y FLOAT,
                    yield_10y FLOAT,
                    yield_30y FLOAT,
                    spread_2y_10y FLOAT,
                    spread_2y_5y FLOAT,
                    PRIMARY KEY (timestamp)
                )
                ''')
                
                # Market Breadth data table
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_breadth_data (
                    timestamp TIMESTAMP,
                    tick FLOAT,
                    trin FLOAT,
                    skew FLOAT,
                    vix FLOAT,
                    realized_vol FLOAT,
                    vrp FLOAT,
                    PRIMARY KEY (timestamp)
                )
                ''')
                
                # Futures Fair Value data table
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS futures_fair_value_data (
                    timestamp TIMESTAMP,
                    es_futures FLOAT,
                    spx FLOAT,
                    fair_value FLOAT,
                    premium_discount FLOAT,
                    PRIMARY KEY (timestamp)
                )
                ''')
                
                # Financial News table
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS financial_news (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP,
                    title TEXT,
                    source TEXT,
                    url TEXT UNIQUE,
                    sentiment TEXT
                )
                ''')
                
                # Notifications table for high-impact alerts
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP,
                    title TEXT,
                    source TEXT,
                    url TEXT,
                    keywords TEXT[],
                    sentiment TEXT,
                    read BOOLEAN DEFAULT FALSE,
                    market_cap_category TEXT,
                    stock_symbol TEXT,
                    priority INTEGER DEFAULT 1
                )
                ''')
            
            self.conn.commit()
            print("Database tables created successfully")
            return True
        except Exception as e:
            print(f"Error creating tables: {e}")
            return False
    
    def store_fed_funds_data(self, timestamp, ticker, price, implied_rate, real_rate=None, inflation_rate=None):
        """Store Fed Funds Futures data in the database with real rate information
        
        Args:
            timestamp: When the data was collected
            ticker: The ticker symbol (e.g., 'DFF' for current rate, or contract symbols)
            price: The price of the futures contract
            implied_rate: The implied interest rate
            real_rate: Optional real rate (nominal rate - inflation)
            inflation_rate: Optional inflation rate used in real rate calculation
        """
        try:
            # Try to add real_rate and inflation_rate columns if they don't exist
            try:
                if self.is_sqlite:
                    self.cursor.execute("ALTER TABLE fed_funds_data ADD COLUMN real_rate FLOAT")
                    self.cursor.execute("ALTER TABLE fed_funds_data ADD COLUMN inflation_rate FLOAT")
                else:
                    self.cursor.execute("ALTER TABLE fed_funds_data ADD COLUMN IF NOT EXISTS real_rate FLOAT")
                    self.cursor.execute("ALTER TABLE fed_funds_data ADD COLUMN IF NOT EXISTS inflation_rate FLOAT")
            except Exception as e:
                # Column might already exist, which is fine
                pass
                
            if self.is_sqlite:
                # For SQLite, we need to use ? for placeholders and do a manual upsert
                self.cursor.execute('''
                INSERT OR REPLACE INTO fed_funds_data (timestamp, ticker, price, implied_rate, real_rate, inflation_rate)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (timestamp, ticker, price, implied_rate, real_rate, inflation_rate))
            else:
                # For PostgreSQL, use the standard upsert syntax
                self.cursor.execute('''
                INSERT INTO fed_funds_data (timestamp, ticker, price, implied_rate, real_rate, inflation_rate)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (timestamp, ticker) DO UPDATE 
                SET price = EXCLUDED.price, 
                    implied_rate = EXCLUDED.implied_rate,
                    real_rate = EXCLUDED.real_rate,
                    inflation_rate = EXCLUDED.inflation_rate
                ''', (timestamp, ticker, price, implied_rate, real_rate, inflation_rate))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error storing Fed Funds data: {e}")
            return False
    
    def store_treasury_yield_data(self, timestamp, yield_2y, yield_5y, yield_10y, yield_30y, spread_2y_10y, spread_2y_5y):
        """Store Treasury Yield data in the database"""
        try:
            if self.is_sqlite:
                # For SQLite, we need to use ? for placeholders and do a manual upsert
                self.cursor.execute('''
                INSERT OR REPLACE INTO treasury_yield_data 
                (timestamp, yield_2y, yield_5y, yield_10y, yield_30y, spread_2y_10y, spread_2y_5y)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (timestamp, yield_2y, yield_5y, yield_10y, yield_30y, spread_2y_10y, spread_2y_5y))
            else:
                # For PostgreSQL, use the standard upsert syntax
                self.cursor.execute('''
                INSERT INTO treasury_yield_data 
                (timestamp, yield_2y, yield_5y, yield_10y, yield_30y, spread_2y_10y, spread_2y_5y)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (timestamp) DO UPDATE 
                SET yield_2y = EXCLUDED.yield_2y,
                    yield_5y = EXCLUDED.yield_5y,
                    yield_10y = EXCLUDED.yield_10y,
                    yield_30y = EXCLUDED.yield_30y,
                    spread_2y_10y = EXCLUDED.spread_2y_10y,
                    spread_2y_5y = EXCLUDED.spread_2y_5y
                ''', (timestamp, yield_2y, yield_5y, yield_10y, yield_30y, spread_2y_10y, spread_2y_5y))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error storing Treasury Yield data: {e}")
            return False
    
    def store_market_breadth_data(self, timestamp, tick, trin, skew, vix, realized_vol, vrp):
        """Store Market Breadth data in the database"""
        try:
            if self.is_sqlite:
                # For SQLite, we need to use ? for placeholders and do a manual upsert
                self.cursor.execute('''
                INSERT OR REPLACE INTO market_breadth_data 
                (timestamp, tick, trin, skew, vix, realized_vol, vrp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (timestamp, tick, trin, skew, vix, realized_vol, vrp))
            else:
                # For PostgreSQL, use the standard upsert syntax
                self.cursor.execute('''
                INSERT INTO market_breadth_data 
                (timestamp, tick, trin, skew, vix, realized_vol, vrp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (timestamp) DO UPDATE 
                SET tick = EXCLUDED.tick,
                    trin = EXCLUDED.trin,
                    skew = EXCLUDED.skew,
                    vix = EXCLUDED.vix,
                    realized_vol = EXCLUDED.realized_vol,
                    vrp = EXCLUDED.vrp
                ''', (timestamp, tick, trin, skew, vix, realized_vol, vrp))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error storing Market Breadth data: {e}")
            return False
    
    def store_futures_fair_value_data(self, timestamp, es_futures, spx, fair_value, premium_discount):
        """Store Futures Fair Value data in the database"""
        try:
            if self.is_sqlite:
                # For SQLite, we need to use ? for placeholders and do a manual upsert
                self.cursor.execute('''
                INSERT OR REPLACE INTO futures_fair_value_data 
                (timestamp, es_futures, spx, fair_value, premium_discount)
                VALUES (?, ?, ?, ?, ?)
                ''', (timestamp, es_futures, spx, fair_value, premium_discount))
            else:
                # For PostgreSQL, use the standard upsert syntax
                self.cursor.execute('''
                INSERT INTO futures_fair_value_data 
                (timestamp, es_futures, spx, fair_value, premium_discount)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (timestamp) DO UPDATE 
                SET es_futures = EXCLUDED.es_futures,
                    spx = EXCLUDED.spx,
                    fair_value = EXCLUDED.fair_value,
                    premium_discount = EXCLUDED.premium_discount
                ''', (timestamp, es_futures, spx, fair_value, premium_discount))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error storing Futures Fair Value data: {e}")
            return False
    
    def store_financial_news(self, timestamp, title, source, url, sentiment):
        """Store Financial News data in the database"""
        try:
            if self.is_sqlite:
                # For SQLite, we need to check if the record exists first
                self.cursor.execute("SELECT url FROM financial_news WHERE url = ?", (url,))
                if not self.cursor.fetchone():
                    # Record doesn't exist, so insert it
                    self.cursor.execute('''
                    INSERT INTO financial_news 
                    (timestamp, title, source, url, sentiment)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (timestamp, title, source, url, sentiment))
            else:
                # For PostgreSQL, use the standard upsert syntax
                self.cursor.execute('''
                INSERT INTO financial_news 
                (timestamp, title, source, url, sentiment)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
                ''', (timestamp, title, source, url, sentiment))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error storing Financial News data: {e}")
            return False
    
    def get_fed_funds_data(self, start_date, end_date):
        """Get Fed Funds data for a date range"""
        try:
            # First check if the real_rate and inflation_rate columns exist
            has_real_rate = True
            try:
                if self.is_sqlite:
                    self.cursor.execute("SELECT real_rate FROM fed_funds_data LIMIT 1")
                else:
                    self.cursor.execute("SELECT real_rate FROM fed_funds_data LIMIT 1")
                self.cursor.fetchone()
            except Exception as e:
                has_real_rate = False
                
            # Query with appropriate columns
            if has_real_rate:
                if self.is_sqlite:
                    # SQLite uses ? for placeholders
                    self.cursor.execute('''
                    SELECT timestamp, ticker, price, implied_rate, real_rate, inflation_rate
                    FROM fed_funds_data
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp
                    ''', (start_date, end_date))
                else:
                    # PostgreSQL uses %s for placeholders
                    self.cursor.execute('''
                    SELECT timestamp, ticker, price, implied_rate, real_rate, inflation_rate
                    FROM fed_funds_data
                    WHERE timestamp BETWEEN %s AND %s
                    ORDER BY timestamp
                    ''', (start_date, end_date))
            else:
                if self.is_sqlite:
                    # SQLite uses ? for placeholders
                    self.cursor.execute('''
                    SELECT timestamp, ticker, price, implied_rate
                    FROM fed_funds_data
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp
                    ''', (start_date, end_date))
                else:
                    # PostgreSQL uses %s for placeholders
                    self.cursor.execute('''
                    SELECT timestamp, ticker, price, implied_rate
                    FROM fed_funds_data
                    WHERE timestamp BETWEEN %s AND %s
                    ORDER BY timestamp
                    ''', (start_date, end_date))
            
            result = self.cursor.fetchall()
            data = []
            for row in result:
                if has_real_rate and len(row) > 4:
                    data.append({
                        "timestamp": row[0],
                        "ticker": row[1],
                        "price": row[2],
                        "implied_rate": row[3],
                        "real_rate": row[4],
                        "inflation_rate": row[5]
                    })
                else:
                    data.append({
                        "timestamp": row[0],
                        "ticker": row[1],
                        "price": row[2],
                        "implied_rate": row[3]
                    })
            return data
        except Exception as e:
            print(f"Error getting Fed Funds data: {e}")
            return []
    
    def get_recent_fed_funds_data(self, days=21):
        """Get Fed Funds data for the last X days, grouped by ticker
        
        Args:
            days (int): Number of days to look back (default 21 days = 3 weeks)
            
        Returns:
            dict: Dictionary with tickers as keys and list of daily rates as values
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get all data for the period
            raw_data = self.get_fed_funds_data(start_date, end_date)
            
            # Group by ticker
            grouped_data = {}
            for item in raw_data:
                ticker = item["ticker"]
                if ticker not in grouped_data:
                    grouped_data[ticker] = []
                
                # Convert raw database entry to a daily rate entry
                daily_entry = {
                    "date": item["timestamp"].strftime('%Y-%m-%d') if hasattr(item["timestamp"], 'strftime') else item["timestamp"],
                    "price": item["price"],
                    "implied_rate": item["implied_rate"]
                }
                
                # Add real rate info if available
                if "real_rate" in item and item["real_rate"] is not None:
                    daily_entry["real_rate"] = item["real_rate"]
                if "inflation_rate" in item and item["inflation_rate"] is not None:
                    daily_entry["inflation_rate"] = item["inflation_rate"]
                    
                grouped_data[ticker].append(daily_entry)
            
            # Sort each group by date
            for ticker in grouped_data:
                grouped_data[ticker] = sorted(grouped_data[ticker], key=lambda x: x["date"])
            
            return grouped_data
        except Exception as e:
            print(f"Error getting recent Fed Funds data: {e}")
            return {}
    
    def get_treasury_yield_data(self, start_date, end_date):
        """Get Treasury Yield data for a date range"""
        try:
            if self.is_sqlite:
                # SQLite uses ? for placeholders
                self.cursor.execute('''
                SELECT timestamp, yield_2y, yield_5y, yield_10y, yield_30y, spread_2y_10y, spread_2y_5y
                FROM treasury_yield_data
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
                ''', (start_date, end_date))
            else:
                # PostgreSQL uses %s for placeholders
                self.cursor.execute('''
                SELECT timestamp, yield_2y, yield_5y, yield_10y, yield_30y, spread_2y_10y, spread_2y_5y
                FROM treasury_yield_data
                WHERE timestamp BETWEEN %s AND %s
                ORDER BY timestamp
                ''', (start_date, end_date))
            
            result = self.cursor.fetchall()
            data = []
            for row in result:
                data.append({
                    "timestamp": row[0],
                    "yield_2y": row[1],
                    "yield_5y": row[2],
                    "yield_10y": row[3],
                    "yield_30y": row[4],
                    "spread_2y_10y": row[5],
                    "spread_2y_5y": row[6]
                })
            return data
        except Exception as e:
            print(f"Error getting Treasury Yield data: {e}")
            return []
    
    def get_market_breadth_data(self, start_date, end_date):
        """Get Market Breadth data for a date range"""
        try:
            if self.is_sqlite:
                # SQLite uses ? for placeholders
                self.cursor.execute('''
                SELECT timestamp, tick, trin, skew, vix, realized_vol, vrp
                FROM market_breadth_data
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
                ''', (start_date, end_date))
            else:
                # PostgreSQL uses %s for placeholders
                self.cursor.execute('''
                SELECT timestamp, tick, trin, skew, vix, realized_vol, vrp
                FROM market_breadth_data
                WHERE timestamp BETWEEN %s AND %s
                ORDER BY timestamp
                ''', (start_date, end_date))
            
            result = self.cursor.fetchall()
            data = []
            for row in result:
                data.append({
                    "timestamp": row[0],
                    "tick": row[1],
                    "trin": row[2],
                    "skew": row[3],
                    "vix": row[4],
                    "realized_vol": row[5],
                    "vrp": row[6]
                })
            return data
        except Exception as e:
            print(f"Error getting Market Breadth data: {e}")
            return []
    
    def get_futures_fair_value_data(self, start_date, end_date):
        """Get Futures Fair Value data for a date range"""
        try:
            if self.is_sqlite:
                # SQLite uses ? for placeholders
                self.cursor.execute('''
                SELECT timestamp, es_futures, spx, fair_value, premium_discount
                FROM futures_fair_value_data
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
                ''', (start_date, end_date))
            else:
                # PostgreSQL uses %s for placeholders
                self.cursor.execute('''
                SELECT timestamp, es_futures, spx, fair_value, premium_discount
                FROM futures_fair_value_data
                WHERE timestamp BETWEEN %s AND %s
                ORDER BY timestamp
                ''', (start_date, end_date))
            
            result = self.cursor.fetchall()
            data = []
            for row in result:
                data.append({
                    "timestamp": row[0],
                    "es_futures": row[1],
                    "spx": row[2],
                    "fair_value": row[3],
                    "premium_discount": row[4]
                })
            return data
        except Exception as e:
            print(f"Error getting Futures Fair Value data: {e}")
            return []
    
    def get_financial_news(self, limit=10):
        """Get the latest financial news"""
        try:
            if self.is_sqlite:
                # SQLite uses ? for placeholders
                self.cursor.execute('''
                SELECT timestamp, title, source, url, sentiment
                FROM financial_news
                ORDER BY timestamp DESC
                LIMIT ?
                ''', (limit,))
            else:
                # PostgreSQL uses %s for placeholders
                self.cursor.execute('''
                SELECT timestamp, title, source, url, sentiment
                FROM financial_news
                ORDER BY timestamp DESC
                LIMIT %s
                ''', (limit,))
            
            result = self.cursor.fetchall()
            data = []
            for row in result:
                data.append({
                    "timestamp": row[0],
                    "title": row[1],
                    "source": row[2],
                    "url": row[3],
                    "sentiment": row[4]
                })
            return data
        except Exception as e:
            print(f"Error getting Financial News data: {e}")
            return []
            
    def store_notification(self, timestamp, title, source, url, keywords, sentiment, market_cap_category="Mid Cap", stock_symbol=None, priority=1):
        """Store a notification in the database"""
        try:
            # Validate inputs
            print(f"Storing notification: '{title}' from {source}")
            print(f"Keywords: {keywords}, Type: {type(keywords)}")
            
            # Process keywords based on database type
            if self.is_sqlite:
                # For SQLite, convert keywords list to a string with comma separation
                if isinstance(keywords, list):
                    keywords_array = ",".join(keywords)
                else:
                    # If not a list, just convert to string
                    keywords_array = str(keywords)
                
                # Check if URL exists
                self.cursor.execute('SELECT id FROM notifications WHERE url = ?', (url,))
                existing = self.cursor.fetchone()
                
                # Set parameters for SQLite
                params = (timestamp, title, source, url, keywords_array, sentiment, market_cap_category, stock_symbol, priority)
                
                if existing:
                    # Update existing notification with new information (SQLite syntax)
                    self.cursor.execute('''
                    UPDATE notifications
                    SET timestamp = ?,
                        title = ?,
                        source = ?,
                        keywords = ?, 
                        sentiment = ?,
                        market_cap_category = ?,
                        stock_symbol = ?,
                        priority = ?
                    WHERE url = ?
                    ''', (timestamp, title, source, keywords_array, sentiment, market_cap_category, stock_symbol, priority, url))
                else:
                    # Insert new notification (SQLite syntax with 0 for FALSE)
                    print("Inserting new notification in SQLite")
                    self.cursor.execute('''
                    INSERT INTO notifications 
                    (timestamp, title, source, url, keywords, sentiment, market_cap_category, stock_symbol, priority, read)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    ''', params)
            else:
                # PostgreSQL version - uses array syntax for keywords
                # Convert keywords list to Postgres array format
                if isinstance(keywords, list):
                    # Escape any quotes in the keywords
                    escaped_keywords = [k.replace('"', '""') for k in keywords]
                    keywords_array = '{' + ','.join(f'"{k}"' for k in escaped_keywords) + '}'
                else:
                    print(f"Warning: keywords is not a list, it's a {type(keywords)}")
                    # Convert to a list with a single item if it's a string
                    if isinstance(keywords, str):
                        keywords_array = '{' + f'"{keywords.replace("""", """"")}"' + '}'
                    else:
                        # Last resort, try to convert to string
                        keywords_array = '{' + f'"{str(keywords)}"' + '}'
                
                # Check if URL exists
                self.cursor.execute('SELECT id FROM notifications WHERE url = %s', (url,))
                existing = self.cursor.fetchone()
                
                # Set parameters for PostgreSQL
                params = (timestamp, title, source, url, keywords_array, sentiment, market_cap_category, stock_symbol, priority)
                
                if existing:
                    # Update existing notification with new information (PostgreSQL syntax)
                    self.cursor.execute('''
                    UPDATE notifications
                    SET timestamp = %s,
                        title = %s,
                        source = %s,
                        keywords = %s, 
                        sentiment = %s,
                        market_cap_category = %s,
                        stock_symbol = %s,
                        priority = %s
                    WHERE url = %s
                    ''', (timestamp, title, source, keywords_array, sentiment, market_cap_category, stock_symbol, priority, url))
                else:
                    # Insert new notification (PostgreSQL syntax with FALSE)
                    print("Inserting new notification in PostgreSQL")
                    self.cursor.execute('''
                    INSERT INTO notifications 
                    (timestamp, title, source, url, keywords, sentiment, market_cap_category, stock_symbol, priority, read)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                    ''', params)
            
            print(f"Keywords array: {keywords_array}")
            print(f"Parameters: {params}")
            
            self.conn.commit()
            print(f"Successfully saved notification for {title}")
            return True
        except Exception as e:
            print(f"Error storing notification: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_notifications(self, limit=20, unread_only=False):
        """Get the latest notifications"""
        try:
            if self.is_sqlite:
                # SQLite version
                if unread_only:
                    self.cursor.execute('''
                    SELECT id, timestamp, title, source, url, keywords, sentiment, read, market_cap_category, stock_symbol, priority
                    FROM notifications
                    WHERE read = 0
                    ORDER BY priority DESC, timestamp DESC
                    LIMIT ?
                    ''', (limit,))
                else:
                    self.cursor.execute('''
                    SELECT id, timestamp, title, source, url, keywords, sentiment, read, market_cap_category, stock_symbol, priority
                    FROM notifications
                    ORDER BY priority DESC, timestamp DESC
                    LIMIT ?
                    ''', (limit,))
            else:
                # PostgreSQL version
                if unread_only:
                    self.cursor.execute('''
                    SELECT id, timestamp, title, source, url, keywords, sentiment, read, market_cap_category, stock_symbol, priority
                    FROM notifications
                    WHERE read = FALSE
                    ORDER BY priority DESC, timestamp DESC
                    LIMIT %s
                    ''', (limit,))
                else:
                    self.cursor.execute('''
                    SELECT id, timestamp, title, source, url, keywords, sentiment, read, market_cap_category, stock_symbol, priority
                    FROM notifications
                    ORDER BY priority DESC, timestamp DESC
                    LIMIT %s
                    ''', (limit,))
            
            result = self.cursor.fetchall()
            data = []
            for row in result:
                # Process keywords based on database type
                if self.is_sqlite and isinstance(row[5], str):
                    # For SQLite, convert comma-separated string back to list
                    keywords = row[5].split(',') if row[5] else []
                else:
                    # For PostgreSQL, use as is (array type)
                    keywords = row[5]
                
                data.append({
                    "id": row[0],
                    "timestamp": row[1],
                    "title": row[2],
                    "source": row[3],
                    "url": row[4],
                    "keywords": keywords,
                    "sentiment": row[6],
                    "read": bool(row[7]),  # Convert to boolean, important for SQLite (0/1)
                    "market_cap_category": row[8],
                    "stock_symbol": row[9],
                    "priority": row[10]
                })
            return data
        except Exception as e:
            print(f"Error getting notification data: {e}")
            return []
    
    def mark_notification_as_read(self, notification_id):
        """Mark a notification as read"""
        try:
            if self.is_sqlite:
                # SQLite uses ? placeholders and 1 for TRUE
                self.cursor.execute('''
                UPDATE notifications
                SET read = 1
                WHERE id = ?
                ''', (notification_id,))
            else:
                # PostgreSQL uses %s placeholders and TRUE keyword
                self.cursor.execute('''
                UPDATE notifications
                SET read = TRUE
                WHERE id = %s
                ''', (notification_id,))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False
