import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
import aiosqlite
import os

logger = logging.getLogger(__name__)

class DatabaseService:
    """SQLite database service for portfolio data persistence"""
    
    def __init__(self, db_path: str = "openport_ai.db"):
        self.db_path = db_path
        self.initialized = False
    
    async def initialize(self):
        """Initialize database with required tables"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Portfolios table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS portfolios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        risk_tolerance REAL,
                        investment_horizon TEXT,
                        total_value REAL,
                        created_at TEXT,
                        updated_at TEXT,
                        optimization_data TEXT,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
                
                # Portfolio positions table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS portfolio_positions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        portfolio_id INTEGER,
                        symbol TEXT NOT NULL,
                        shares REAL,
                        avg_cost REAL,
                        target_weight REAL,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                    )
                """)
                
                # Search history table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS search_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        search_type TEXT,
                        results_count INTEGER,
                        search_data TEXT,
                        created_at TEXT
                    )
                """)
                
                # Chat history table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        message_type TEXT,
                        content TEXT,
                        metadata TEXT,
                        created_at TEXT
                    )
                """)
                
                # News cache table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS news_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT,
                        news_data TEXT,
                        sentiment_score REAL,
                        relevance_score REAL,
                        created_at TEXT,
                        expires_at TEXT
                    )
                """)
                
                # User preferences table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        preference_key TEXT UNIQUE,
                        preference_value TEXT,
                        updated_at TEXT
                    )
                """)
                
                # Market data cache table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS market_data_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT,
                        data_type TEXT,
                        data_content TEXT,
                        created_at TEXT,
                        expires_at TEXT
                    )
                """)
                
                await db.commit()
                
            self.initialized = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def save_portfolio(self, portfolio_data: Dict[str, Any]) -> int:
        """Save portfolio to database"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                # Insert portfolio
                cursor = await db.execute("""
                    INSERT INTO portfolios (
                        name, description, risk_tolerance, investment_horizon,
                        total_value, created_at, updated_at, optimization_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    portfolio_data.get("name", "Portfolio"),
                    portfolio_data.get("description", ""),
                    portfolio_data.get("risk_tolerance", 0.5),
                    portfolio_data.get("investment_horizon", "medium"),
                    portfolio_data.get("investment_amount", 0.0),
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    json.dumps(portfolio_data.get("optimization_result", {}))
                ))
                
                portfolio_id = cursor.lastrowid
                
                # Insert positions
                allocations = portfolio_data.get("optimization_result", {}).get("allocations", {})
                share_allocations = portfolio_data.get("optimization_result", {}).get("share_allocations", {})
                
                for symbol, weight in allocations.items():
                    shares = share_allocations.get(symbol, 0)
                    await db.execute("""
                        INSERT INTO portfolio_positions (
                            portfolio_id, symbol, shares, target_weight, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        portfolio_id,
                        symbol,
                        shares,
                        weight,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                
                await db.commit()
                
            logger.info(f"Portfolio saved with ID: {portfolio_id}")
            return portfolio_id
            
        except Exception as e:
            logger.error(f"Failed to save portfolio: {e}")
            raise
    
    async def get_portfolio(self, portfolio_id: int) -> Optional[Dict[str, Any]]:
        """Get portfolio by ID"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                # Get portfolio
                cursor = await db.execute("""
                    SELECT * FROM portfolios WHERE id = ? AND is_active = 1
                """, (portfolio_id,))
                
                portfolio_row = await cursor.fetchone()
                if not portfolio_row:
                    return None
                
                # Get positions
                cursor = await db.execute("""
                    SELECT * FROM portfolio_positions WHERE portfolio_id = ?
                """, (portfolio_id,))
                
                positions = await cursor.fetchall()
                
                # Build portfolio object
                portfolio = {
                    "id": portfolio_row[0],
                    "name": portfolio_row[1],
                    "description": portfolio_row[2],
                    "risk_tolerance": portfolio_row[3],
                    "investment_horizon": portfolio_row[4],
                    "total_value": portfolio_row[5],
                    "created_at": portfolio_row[6],
                    "updated_at": portfolio_row[7],
                    "optimization_data": json.loads(portfolio_row[8]) if portfolio_row[8] else {},
                    "positions": []
                }
                
                for pos in positions:
                    portfolio["positions"].append({
                        "symbol": pos[2],
                        "shares": pos[3],
                        "avg_cost": pos[4],
                        "target_weight": pos[5],
                        "created_at": pos[6],
                        "updated_at": pos[7]
                    })
                
                return portfolio
                
        except Exception as e:
            logger.error(f"Failed to get portfolio {portfolio_id}: {e}")
            return None
    
    async def list_portfolios(self) -> List[Dict[str, Any]]:
        """List all active portfolios"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT id, name, description, risk_tolerance, investment_horizon,
                           total_value, created_at, updated_at
                    FROM portfolios 
                    WHERE is_active = 1
                    ORDER BY updated_at DESC
                """)
                
                portfolios = []
                rows = await cursor.fetchall()
                
                for row in rows:
                    portfolios.append({
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "risk_tolerance": row[3],
                        "investment_horizon": row[4],
                        "total_value": row[5],
                        "created_at": row[6],
                        "updated_at": row[7]
                    })
                
                return portfolios
                
        except Exception as e:
            logger.error(f"Failed to list portfolios: {e}")
            return []
    
    async def update_portfolio(self, portfolio_id: int, updates: Dict[str, Any]) -> bool:
        """Update portfolio"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                # Build update query dynamically
                set_clauses = []
                values = []
                
                if "name" in updates:
                    set_clauses.append("name = ?")
                    values.append(updates["name"])
                
                if "description" in updates:
                    set_clauses.append("description = ?")
                    values.append(updates["description"])
                
                if "total_value" in updates:
                    set_clauses.append("total_value = ?")
                    values.append(updates["total_value"])
                
                if "optimization_data" in updates:
                    set_clauses.append("optimization_data = ?")
                    values.append(json.dumps(updates["optimization_data"]))
                
                set_clauses.append("updated_at = ?")
                values.append(datetime.now().isoformat())
                values.append(portfolio_id)
                
                await db.execute(f"""
                    UPDATE portfolios 
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                """, values)
                
                await db.commit()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to update portfolio {portfolio_id}: {e}")
            return False
    
    async def delete_portfolio(self, portfolio_id: int) -> bool:
        """Delete portfolio (soft delete)"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE portfolios SET is_active = 0, updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), portfolio_id))
                
                await db.commit()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete portfolio {portfolio_id}: {e}")
            return False
    
    async def save_search_history(self, query: str, search_type: str, results_data: Dict[str, Any]) -> int:
        """Save search history"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO search_history (
                        query, search_type, results_count, search_data, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    query,
                    search_type,
                    len(results_data.get("news_articles", [])),
                    json.dumps(results_data),
                    datetime.now().isoformat()
                ))
                
                search_id = cursor.lastrowid
                await db.commit()
                
            return search_id
            
        except Exception as e:
            logger.error(f"Failed to save search history: {e}")
            return 0
    
    async def get_search_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent search history"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT query, search_type, results_count, created_at
                    FROM search_history
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                
                history = []
                rows = await cursor.fetchall()
                
                for row in rows:
                    history.append({
                        "query": row[0],
                        "search_type": row[1],
                        "results_count": row[2],
                        "created_at": row[3]
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Failed to get search history: {e}")
            return []
    
    async def save_chat_message(self, session_id: str, message_type: str, content: str, metadata: Dict[str, Any] = None) -> int:
        """Save chat message"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO chat_history (
                        session_id, message_type, content, metadata, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    session_id,
                    message_type,
                    content,
                    json.dumps(metadata or {}),
                    datetime.now().isoformat()
                ))
                
                message_id = cursor.lastrowid
                await db.commit()
                
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to save chat message: {e}")
            return 0
    
    async def get_chat_history(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get chat history for session"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT message_type, content, metadata, created_at
                    FROM chat_history
                    WHERE session_id = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                """, (session_id, limit))
                
                messages = []
                rows = await cursor.fetchall()
                
                for row in rows:
                    messages.append({
                        "message_type": row[0],
                        "content": row[1],
                        "metadata": json.loads(row[2]) if row[2] else {},
                        "created_at": row[3]
                    })
                
                return messages
                
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return []
    
    async def save_news_cache(self, query: str, news_data: List[Dict[str, Any]], expires_hours: int = 24) -> bool:
        """Cache news data"""
        try:
            if not self.initialized:
                await self.initialize()
            
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO news_cache (
                        query, news_data, sentiment_score, relevance_score, created_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    query,
                    json.dumps(news_data),
                    sum(article.get("sentiment", 0) for article in news_data) / len(news_data) if news_data else 0,
                    sum(article.get("relevance_score", 0) for article in news_data) / len(news_data) if news_data else 0,
                    datetime.now().isoformat(),
                    expires_at.isoformat()
                ))
                
                await db.commit()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to save news cache: {e}")
            return False
    
    async def get_news_cache(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached news data"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT news_data FROM news_cache
                    WHERE query = ? AND expires_at > ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (query, datetime.now().isoformat()))
                
                row = await cursor.fetchone()
                if row:
                    return json.loads(row[0])
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get news cache: {e}")
            return None
    
    async def save_user_preference(self, key: str, value: Any) -> bool:
        """Save user preference"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO user_preferences (
                        preference_key, preference_value, updated_at
                    ) VALUES (?, ?, ?)
                """, (
                    key,
                    json.dumps(value),
                    datetime.now().isoformat()
                ))
                
                await db.commit()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to save user preference: {e}")
            return False
    
    async def get_user_preference(self, key: str, default_value: Any = None) -> Any:
        """Get user preference"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT preference_value FROM user_preferences
                    WHERE preference_key = ?
                """, (key,))
                
                row = await cursor.fetchone()
                if row:
                    return json.loads(row[0])
                
                return default_value
                
        except Exception as e:
            logger.error(f"Failed to get user preference: {e}")
            return default_value
    
    async def cleanup_expired_data(self) -> bool:
        """Clean up expired cached data"""
        try:
            if not self.initialized:
                await self.initialize()
            
            current_time = datetime.now().isoformat()
            
            async with aiosqlite.connect(self.db_path) as db:
                # Clean expired news cache
                await db.execute("""
                    DELETE FROM news_cache WHERE expires_at < ?
                """, (current_time,))
                
                # Clean expired market data cache
                await db.execute("""
                    DELETE FROM market_data_cache WHERE expires_at < ?
                """, (current_time,))
                
                # Clean old search history (keep last 1000 entries)
                await db.execute("""
                    DELETE FROM search_history WHERE id NOT IN (
                        SELECT id FROM search_history 
                        ORDER BY created_at DESC 
                        LIMIT 1000
                    )
                """)
                
                # Clean old chat history (keep last 30 days)
                thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
                await db.execute("""
                    DELETE FROM chat_history WHERE created_at < ?
                """, (thirty_days_ago,))
                
                await db.commit()
                
            logger.info("Database cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
            return False
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            if not self.initialized:
                await self.initialize()
            
            stats = {}
            
            async with aiosqlite.connect(self.db_path) as db:
                # Count records in each table
                tables = ["portfolios", "portfolio_positions", "search_history", "chat_history", "news_cache", "user_preferences"]
                
                for table in tables:
                    cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                    count = await cursor.fetchone()
                    stats[f"{table}_count"] = count[0] if count else 0
                
                # Database file size
                if os.path.exists(self.db_path):
                    stats["database_size_mb"] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
                
                stats["last_updated"] = datetime.now().isoformat()
                
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}
