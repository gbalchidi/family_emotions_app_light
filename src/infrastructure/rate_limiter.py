import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


class RateLimiter:
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests: Dict[int, list] = {}
    
    async def check_rate_limit(self, user_id: int) -> bool:
        now = datetime.now()
        
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        self.user_requests[user_id] = [
            timestamp for timestamp in self.user_requests[user_id]
            if now - timestamp < timedelta(seconds=self.window_seconds)
        ]
        
        if len(self.user_requests[user_id]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False
        
        self.user_requests[user_id].append(now)
        return True
    
    def get_wait_time(self, user_id: int) -> Optional[int]:
        if user_id not in self.user_requests or not self.user_requests[user_id]:
            return None
        
        oldest_request = min(self.user_requests[user_id])
        wait_time = self.window_seconds - (datetime.now() - oldest_request).seconds
        
        return max(0, wait_time)