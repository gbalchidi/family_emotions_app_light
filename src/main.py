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
from .infrastructure.database import analytics_db
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
    
    # Connect to database for analytics
    logger.info("Connecting to analytics database...")
    await analytics_db.connect()
    
    # Log library versions for debugging
    import anthropic
    logger.info(f"Anthropic library version: {anthropic.__version__}")
    
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    logger.info("Initializing Anthropic analyzer...")
    anthropic_analyzer = AnthropicAnalyzer(
        api_key=settings.anthropic_api_key,
        use_proxy=settings.use_proxy,
        proxy_url=settings.proxy_url
    )
    analysis_service = PhraseAnalysisService(anthropic_analyzer=anthropic_analyzer)
    interaction_service = InteractionService()
    
    rate_limiter = RateLimiter(
        max_requests=settings.rate_limit_messages,
        window_seconds=settings.rate_limit_window
    )
    
    from aiogram import Router
    router = Router()
    logger.info("Registering handlers...")
    register_handlers(router, analysis_service, interaction_service)
    logger.info("Handlers registered successfully")
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
    
    logger.info("Adding middleware...")
    dp.message.middleware(RateLimitMiddleware(rate_limiter))
    logger.info("Middleware added")
    
    # Test bot connection before starting polling (with timeout)
    logger.info("Testing bot connection...")
    try:
        import asyncio
        me = await asyncio.wait_for(bot.get_me(), timeout=5.0)
        logger.info(f"Bot connected successfully: @{me.username} (ID: {me.id})")
    except asyncio.TimeoutError:
        logger.warning("Bot connection test timed out, proceeding anyway...")
    except Exception as e:
        logger.error(f"Failed to connect to Telegram: {e}")
        logger.warning("Proceeding with polling anyway...")
    
    logger.info("Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Critical error: {e}")
        sys.exit(1)
    finally:
        # Close database connection
        loop = asyncio.new_event_loop()
        loop.run_until_complete(analytics_db.close())