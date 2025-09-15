"""
Database module for storing analytics events
"""
import os
import json
import logging
import asyncio
import asyncpg
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AnalyticsDatabase:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = int(os.getenv('DB_PORT', '5432'))
        self.db_name = os.getenv('DB_NAME', 'analytics')
        self.db_user = os.getenv('DB_USER', 'analytics_user')
        self.db_password = os.getenv('DB_PASSWORD', 'analytics_secret_2024')
        
    async def connect(self):
        """Create connection pool to database"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info(f"Connected to database at {self.db_host}:{self.db_port}/{self.db_name}")
            
            # Ensure table exists
            await self.ensure_table_exists()
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            logger.warning("Analytics will continue without database storage")
            self.pool = None
    
    async def ensure_table_exists(self):
        """Ensure analytics_events table exists"""
        if not self.pool:
            return
            
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS analytics_events (
                        id SERIAL PRIMARY KEY,
                        event_data JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_event_type 
                    ON analytics_events ((event_data->>'event'))
                ''')
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_user_id 
                    ON analytics_events ((event_data->'properties'->>'user_id'))
                ''')
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON analytics_events ((event_data->'properties'->>'timestamp'))
                ''')
                
                logger.info("Analytics table and indexes ensured")
                
        except Exception as e:
            logger.error(f"Failed to ensure table exists: {e}")
    
    async def store_event(self, event_data: Dict[str, Any]):
        """Store analytics event in database"""
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    'INSERT INTO analytics_events (event_data) VALUES ($1)',
                    json.dumps(event_data)
                )
            return True
            
        except Exception as e:
            logger.error(f"Failed to store event in database: {e}")
            return False
    
    async def get_events_count(self) -> int:
        """Get total count of events in database"""
        if not self.pool:
            return 0
            
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval('SELECT COUNT(*) FROM analytics_events')
                return result or 0
                
        except Exception as e:
            logger.error(f"Failed to get events count: {e}")
            return 0
    
    async def get_recent_events(self, limit: int = 100):
        """Get recent events from database"""
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT event_data, created_at 
                    FROM analytics_events 
                    ORDER BY created_at DESC 
                    LIMIT $1
                ''', limit)
                
                return [
                    {
                        'event': json.loads(row['event_data']),
                        'stored_at': row['created_at'].isoformat()
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            return []
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection closed")


# Global database instance
analytics_db = AnalyticsDatabase()