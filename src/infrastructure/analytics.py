"""
Analytics module for tracking user events and behavior
"""
import hashlib
import uuid
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from enum import Enum


# Configure analytics logger
analytics_logger = logging.getLogger('analytics')
analytics_logger.setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# Create JSON formatter for analytics events
class AnalyticsJSONFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, 'event_data'):
            return json.dumps(record.event_data, ensure_ascii=False)
        return super().format(record)

# Add JSON handler for analytics
try:
    analytics_handler = logging.FileHandler('analytics_events.log')
    analytics_handler.setFormatter(AnalyticsJSONFormatter())
    analytics_logger.addHandler(analytics_handler)
except Exception as e:
    # If file handler fails, just use console
    print(f"Warning: Could not create analytics file handler: {e}")

# Also log to console with prefix
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('📊 ANALYTICS: %(message)s'))
analytics_logger.addHandler(console_handler)


class EventType(Enum):
    # Onboarding
    BOT_STARTED = "bot_started"
    MAIN_MENU_OPENED = "main_menu_opened"
    
    # Core Function
    DECODE_INITIATED = "decode_initiated"
    PHRASE_SUBMITTED = "phrase_submitted"
    API_REQUEST_SENT = "api_request_sent"
    DECODE_COMPLETED = "decode_completed"
    DECODE_FAILED = "decode_failed"
    
    # User Actions
    BUTTON_CLICKED = "button_clicked"
    EXAMPLE_VIEWED = "example_viewed"
    HOW_IT_WORKS_VIEWED = "how_it_works_viewed"
    TIPS_VIEWED = "tips_viewed"
    
    # Session
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    
    # Engagement
    MORE_OPTIONS_REQUESTED = "more_options_requested"
    SIMILAR_EXAMPLES_REQUESTED = "similar_examples_requested"
    USER_RETURNED = "user_returned"


class Analytics:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.user_stats: Dict[str, Dict] = {}
        
    def get_user_hash(self, telegram_id: int) -> str:
        """Return real telegram ID as string"""
        return str(telegram_id)
    
    def get_or_create_session(self, user_hash: str) -> tuple[str, bool]:
        """Get current session or create new one. Returns (session_id, is_new)"""
        now = datetime.now()
        is_new = False
        
        if user_hash not in self.sessions:
            # First session for this user
            session_id = str(uuid.uuid4())
            self.sessions[user_hash] = {
                'id': session_id,
                'started': now,
                'last_activity': now,
                'phrases_decoded': 0,
                'examples_viewed': 0,
                'errors_encountered': 0,
                'successful_decodes': 0
            }
            is_new = True
        else:
            session = self.sessions[user_hash]
            time_diff = (now - session['last_activity']).total_seconds()
            
            # New session if more than 30 minutes inactive
            if time_diff > 1800:
                # End previous session
                self._end_session(user_hash)
                
                # Start new session
                old_session_id = session['id']
                session_id = str(uuid.uuid4())
                self.sessions[user_hash] = {
                    'id': session_id,
                    'started': now,
                    'last_activity': now,
                    'phrases_decoded': 0,
                    'examples_viewed': 0,
                    'errors_encountered': 0,
                    'successful_decodes': 0,
                    'previous_session_id': old_session_id,
                    'time_since_last_session_minutes': int(time_diff / 60)
                }
                is_new = True
            else:
                session_id = session['id']
                session['last_activity'] = now
        
        return session_id, is_new
    
    def _end_session(self, user_hash: str):
        """Log session end event"""
        if user_hash in self.sessions:
            session = self.sessions[user_hash]
            duration_ms = int((datetime.now() - session['started']).total_seconds() * 1000)
            
            self._log_event({
                'event': EventType.SESSION_ENDED.value,
                'properties': {
                    'user_id': user_hash,
                    'timestamp': datetime.now().isoformat(),
                    'session_id': session['id'],
                    'session_duration_ms': duration_ms,
                    'phrases_decoded': session.get('phrases_decoded', 0),
                    'examples_viewed': session.get('examples_viewed', 0),
                    'errors_encountered': session.get('errors_encountered', 0),
                    'successful_decodes': session.get('successful_decodes', 0)
                }
            })
    
    def track_bot_started(self, telegram_id: int, source: str = 'direct', utm_params: Dict[str, str] = None):
        """Track bot start event with UTM parameters"""
        user_hash = self.get_user_hash(telegram_id)
        session_id, is_new_session = self.get_or_create_session(user_hash)
        
        # Update user stats
        if user_hash not in self.user_stats:
            self.user_stats[user_hash] = {
                'first_seen': datetime.now(),
                'total_sessions': 0,
                'total_phrases': 0
            }
        
        # Build event properties
        properties = {
            'user_id': user_hash,
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'platform': 'telegram',
            'language': 'ru',
            'session_id': session_id
        }
        
        # Add UTM parameters if provided
        if utm_params:
            properties.update(utm_params)
            logger.info(f"Bot started with UTM params: {utm_params}")
        
        event = {
            'event': EventType.BOT_STARTED.value,
            'properties': properties
        }
        
        self._log_event(event)
        
        if is_new_session:
            self.track_session_started(user_hash)
    
    def track_session_started(self, user_hash: str):
        """Track session start"""
        session = self.sessions.get(user_hash, {})
        
        event = {
            'event': EventType.SESSION_STARTED.value,
            'properties': {
                'user_id': user_hash,
                'timestamp': datetime.now().isoformat(),
                'session_id': session.get('id'),
                'previous_session_id': session.get('previous_session_id'),
                'time_since_last_session_minutes': session.get('time_since_last_session_minutes')
            }
        }
        
        self._log_event(event)
    
    def track_decode_initiated(self, telegram_id: int, entry_point: str):
        """Track decode initiation"""
        user_hash = self.get_user_hash(telegram_id)
        session_id, _ = self.get_or_create_session(user_hash)
        
        event = {
            'event': EventType.DECODE_INITIATED.value,
            'properties': {
                'user_id': user_hash,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'entry_point': entry_point
            }
        }
        
        self._log_event(event)
    
    def track_phrase_submitted(self, telegram_id: int, phrase: str):
        """Track phrase submission"""
        user_hash = self.get_user_hash(telegram_id)
        session_id, _ = self.get_or_create_session(user_hash)
        
        # Detect phrase category by keywords
        category = self._detect_phrase_category(phrase)
        
        event = {
            'event': EventType.PHRASE_SUBMITTED.value,
            'properties': {
                'user_id': user_hash,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'phrase_length': len(phrase),
                'phrase_words_count': len(phrase.split()),
                'contains_emoji': any(ord(c) > 127 for c in phrase),
                'language_detected': 'ru' if any('а' <= c <= 'я' or 'А' <= c <= 'Я' for c in phrase) else 'en',
                'phrase_category': category
            }
        }
        
        self._log_event(event)
        
        # Update session stats
        if user_hash in self.sessions:
            self.sessions[user_hash]['phrases_decoded'] += 1
    
    def track_api_request(self, telegram_id: int, request_id: str):
        """Track API request"""
        user_hash = self.get_user_hash(telegram_id)
        session_id, _ = self.get_or_create_session(user_hash)
        
        event = {
            'event': EventType.API_REQUEST_SENT.value,
            'properties': {
                'user_id': user_hash,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'request_id': request_id,
                'prompt_template': 'v2',
                'estimated_tokens': 150
            }
        }
        
        self._log_event(event)
    
    def track_decode_completed(self, telegram_id: int, request_id: str, response_time_ms: int, category: str = None):
        """Track successful decode"""
        user_hash = self.get_user_hash(telegram_id)
        session_id, _ = self.get_or_create_session(user_hash)
        
        event = {
            'event': EventType.DECODE_COMPLETED.value,
            'properties': {
                'user_id': user_hash,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'request_id': request_id,
                'response_time_ms': response_time_ms,
                'phrase_category': category,
                'suggestions_count': 3
            }
        }
        
        self._log_event(event)
        
        # Update session stats
        if user_hash in self.sessions:
            self.sessions[user_hash]['successful_decodes'] += 1
    
    def track_decode_failed(self, telegram_id: int, error_type: str, error_message: str):
        """Track decode failure"""
        user_hash = self.get_user_hash(telegram_id)
        session_id, _ = self.get_or_create_session(user_hash)
        
        event = {
            'event': EventType.DECODE_FAILED.value,
            'properties': {
                'user_id': user_hash,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'error_type': error_type,
                'error_message': error_message,
                'retry_attempted': False
            }
        }
        
        self._log_event(event)
        
        # Update session stats
        if user_hash in self.sessions:
            self.sessions[user_hash]['errors_encountered'] += 1
    
    def track_button_click(self, telegram_id: int, button_id: str, screen: str, context: str = None):
        """Track button clicks"""
        user_hash = self.get_user_hash(telegram_id)
        session_id, _ = self.get_or_create_session(user_hash)
        
        event = {
            'event': EventType.BUTTON_CLICKED.value,
            'properties': {
                'user_id': user_hash,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'button_id': button_id,
                'screen': screen,
                'context': context or 'navigation'
            }
        }
        
        self._log_event(event)
    
    def track_example_viewed(self, telegram_id: int, example_id: str, position: int):
        """Track example view"""
        user_hash = self.get_user_hash(telegram_id)
        session_id, _ = self.get_or_create_session(user_hash)
        
        event = {
            'event': EventType.EXAMPLE_VIEWED.value,
            'properties': {
                'user_id': user_hash,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'example_id': example_id,
                'example_position': position
            }
        }
        
        self._log_event(event)
        
        # Update session stats
        if user_hash in self.sessions:
            self.sessions[user_hash]['examples_viewed'] += 1
    
    def track_how_it_works_viewed(self, telegram_id: int):
        """Track how it works view"""
        user_hash = self.get_user_hash(telegram_id)
        session_id, _ = self.get_or_create_session(user_hash)
        
        event = {
            'event': EventType.HOW_IT_WORKS_VIEWED.value,
            'properties': {
                'user_id': user_hash,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id
            }
        }
        
        self._log_event(event)
    
    def track_tips_viewed(self, telegram_id: int):
        """Track tips view"""
        user_hash = self.get_user_hash(telegram_id)
        session_id, _ = self.get_or_create_session(user_hash)
        
        event = {
            'event': EventType.TIPS_VIEWED.value,
            'properties': {
                'user_id': user_hash,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id
            }
        }
        
        self._log_event(event)
    
    def track_more_options_requested(self, telegram_id: int, category: str = None):
        """Track more options request"""
        user_hash = self.get_user_hash(telegram_id)
        session_id, _ = self.get_or_create_session(user_hash)
        
        event = {
            'event': EventType.MORE_OPTIONS_REQUESTED.value,
            'properties': {
                'user_id': user_hash,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'original_phrase_category': category
            }
        }
        
        self._log_event(event)
    
    def track_similar_examples_requested(self, telegram_id: int):
        """Track similar examples request"""
        user_hash = self.get_user_hash(telegram_id)
        session_id, _ = self.get_or_create_session(user_hash)
        
        event = {
            'event': EventType.SIMILAR_EXAMPLES_REQUESTED.value,
            'properties': {
                'user_id': user_hash,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id
            }
        }
        
        self._log_event(event)
    
    def _detect_phrase_category(self, phrase: str) -> str:
        """Detect phrase emotional category"""
        phrase_lower = phrase.lower()
        
        if any(word in phrase_lower for word in ['отстань', 'уйди', 'достал', 'ненавижу']):
            return 'anger'
        elif any(word in phrase_lower for word in ['грустно', 'плохо', 'устал', 'одиноко']):
            return 'sadness'
        elif any(word in phrase_lower for word in ['всё равно', 'неважно', 'пофиг']):
            return 'dismissive'
        elif any(word in phrase_lower for word in ['не понима', 'не знаю', 'запутал']):
            return 'confusion'
        else:
            return 'neutral'
    
    def _log_event(self, event_data: Dict[str, Any]):
        """Log event to file, console and database"""
        # Log as JSON with special attribute
        record = analytics_logger.makeRecord(
            analytics_logger.name,
            logging.INFO,
            __file__,
            0,
            json.dumps(event_data, ensure_ascii=False),
            (),
            None
        )
        record.event_data = event_data
        analytics_logger.handle(record)
        
        # Also log summary to console
        event_type = event_data.get('event', 'unknown')
        user_id = event_data.get('properties', {}).get('user_id', 'unknown')
        analytics_logger.info(f"Event: {event_type} | User: {user_id}")
        
        # Store in database asynchronously
        from .database import analytics_db
        asyncio.create_task(self._store_in_db(event_data))
    
    async def _store_in_db(self, event_data: Dict[str, Any]):
        """Store event in database"""
        try:
            from .database import analytics_db
            if analytics_db.pool:
                await analytics_db.store_event(event_data)
        except Exception as e:
            logger.error(f"Failed to store event in database: {e}")


# Global analytics instance
analytics = Analytics()