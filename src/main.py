import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .infrastructure.config import get_settings
from .infrastructure.anthropic_client import AnthropicAnalyzer
from .infrastructure.rate_limiter import RateLimiter
from .application.services import PhraseAnalysisService, InteractionService
from .presentation.handlers import register_handlers


def setup_logging(log_level: str):
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log')
        ]
    )


async def main():
    settings = get_settings()
    setup_logging(settings.log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Emotions Translator Bot...")
    
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    anthropic_analyzer = AnthropicAnalyzer(api_key=settings.anthropic_api_key)
    analysis_service = PhraseAnalysisService(anthropic_analyzer=anthropic_analyzer)
    interaction_service = InteractionService()
    
    rate_limiter = RateLimiter(
        max_requests=settings.rate_limit_messages,
        window_seconds=settings.rate_limit_window
    )
    
    from aiogram import Router
    router = Router()
    register_handlers(router, analysis_service, interaction_service)
    dp.include_router(router)
    
    from aiogram import BaseMiddleware
    from aiogram.types import Message, CallbackQuery
    from typing import Callable, Dict, Any, Awaitable
    
    class RateLimitMiddleware(BaseMiddleware):
        def __init__(self, rate_limiter: RateLimiter):
            self.rate_limiter = rate_limiter
        
        async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
        ) -> Any:
            user_id = event.from_user.id if hasattr(event, 'from_user') else None
            
            if user_id and not await self.rate_limiter.check_rate_limit(user_id):
                wait_time = self.rate_limiter.get_wait_time(user_id)
                if isinstance(event, Message):
                    await event.answer(
                        f"⏱ Слишком много запросов. Подождите {wait_time} секунд."
                    )
                return
            
            return await handler(event, data)
    
    dp.message.middleware(RateLimitMiddleware(rate_limiter))
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Critical error: {e}")
        sys.exit(1)