from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
import logging

from .keyboards import KeyboardBuilder
from .states import AnalysisStates, FeedbackStates
from .messages import BotMessages
from ..application.services import (
    PhraseAnalysisService, 
    InteractionService, 
    ResponseFormatterService
)
from ..domain.value_objects import AnalysisRequest
from ..domain.examples import PhraseExamples


logger = logging.getLogger(__name__)
router = Router()


class BotHandlers:
    
    def __init__(
        self, 
        analysis_service: PhraseAnalysisService,
        interaction_service: InteractionService
    ):
        self.analysis_service = analysis_service
        self.interaction_service = interaction_service
        self.formatter = ResponseFormatterService()
        self.keyboards = KeyboardBuilder()
        self.messages = BotMessages()
        self.examples = PhraseExamples()
    
    async def start_command(self, message: Message, state: FSMContext):
        await state.clear()
        await message.answer(
            self.messages.WELCOME_MESSAGE,
            reply_markup=self.keyboards.main_menu()
        )
    
    async def decode_callback(self, callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        await callback.message.answer(self.messages.ENTER_PHRASE_MESSAGE)
        await state.set_state(AnalysisStates.waiting_for_phrase)
    
    async def process_phrase(self, message: Message, state: FSMContext):
        try:
            phrase = message.text.strip()
            
            if len(phrase) < 2:
                await message.answer(
                    self.formatter.format_error_message(),
                    reply_markup=self.keyboards.error_menu()
                )
                await state.clear()
                return
            
            await message.answer("🔄 Анализирую фразу...")
            await state.set_state(AnalysisStates.processing)
            
            request = AnalysisRequest(phrase=phrase)
            analysis = await self.analysis_service.analyze_phrase(request)
            
            self.interaction_service.record_interaction(
                user_id=message.from_user.id,
                phrase=phrase,
                analysis=analysis
            )
            
            await message.answer(
                self.formatter.format_analysis(analysis),
                reply_markup=self.keyboards.after_analysis_menu()
            )
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error processing phrase: {e}")
            await message.answer(
                self.formatter.format_error_message(),
                reply_markup=self.keyboards.error_menu()
            )
            await state.clear()
    
    async def examples_callback(self, callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        examples = self.examples.get_common_phrases()
        
        await callback.message.answer(
            self.messages.EXAMPLES_MESSAGE,
            reply_markup=self.keyboards.examples_menu(examples)
        )
    
    async def example_detail_callback(self, callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        
        example_index = int(callback.data.split("_")[1])
        examples = self.examples.get_common_phrases()
        
        if 0 <= example_index < len(examples):
            example = examples[example_index]
            await callback.message.answer(
                self.formatter.format_example(example),
                reply_markup=self.keyboards.after_analysis_menu()
            )
    
    async def how_it_works_callback(self, callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        await callback.message.answer(
            self.messages.HOW_IT_WORKS_MESSAGE,
            reply_markup=self.keyboards.back_to_menu()
        )
    
    async def tips_callback(self, callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        await callback.message.answer(
            self.messages.TIPS_MESSAGE,
            reply_markup=self.keyboards.back_to_menu()
        )
    
    async def home_callback(self, callback: CallbackQuery, state: FSMContext):
        await callback.answer()
        await state.clear()
        await callback.message.answer(
            self.messages.MAIN_MENU_MESSAGE,
            reply_markup=self.keyboards.main_menu()
        )
    
    async def feedback_positive_callback(self, callback: CallbackQuery):
        await callback.answer("Спасибо за отзыв! 😊")
        self.interaction_service.add_feedback(
            user_id=callback.from_user.id,
            feedback="positive"
        )
    
    async def feedback_negative_callback(self, callback: CallbackQuery):
        await callback.answer("Спасибо за отзыв. Мы постараемся улучшить анализ.")
        self.interaction_service.add_feedback(
            user_id=callback.from_user.id,
            feedback="negative"
        )
    
    async def more_options_callback(self, callback: CallbackQuery):
        await callback.answer()
        # Get last interaction and generate more options
        interactions = self.interaction_service.get_user_interactions(callback.from_user.id)
        if interactions and interactions[-1].analysis:
            analysis = interactions[-1].analysis
            additional_responses = [
                "Я вижу, что тебе тяжело. Давай поговорим, когда будешь готов.",
                "Понимаю твои чувства. Что могло бы помочь тебе сейчас?",
                "Хочешь рассказать, что произошло? Я просто послушаю."
            ]
            message = f"""💡 Дополнительные варианты ответов:

{chr(10).join(['• ' + r for r in additional_responses])}

💭 Помните: важнее всего показать, что вы рядом и готовы поддержать."""
            
            await callback.message.answer(
                message,
                reply_markup=self.keyboards.after_analysis_menu()
            )
        else:
            await callback.answer("Сначала проанализируйте фразу", show_alert=True)
    
    async def similar_examples_callback(self, callback: CallbackQuery):
        await callback.answer()
        # Get last interaction and find similar examples
        interactions = self.interaction_service.get_user_interactions(callback.from_user.id)
        if interactions:
            last_phrase = interactions[-1].phrase
            similar = self.examples.find_similar(last_phrase)
            
            if similar:
                message = "📚 Похожие примеры:\n\n"
                for ex in similar[:3]:
                    message += f"➤ \"{ex.phrase}\"\n{ex.typical_meaning}\n\n"
            else:
                # Show general examples if no similar found
                examples = self.examples.get_common_phrases()[:3]
                message = "📚 Другие частые фразы:\n\n"
                for ex in examples:
                    message += f"➤ \"{ex.phrase}\"\n{ex.typical_meaning}\n\n"
            
            await callback.message.answer(
                message,
                reply_markup=self.keyboards.back_to_menu()
            )
        else:
            await callback.answer("Сначала проанализируйте фразу", show_alert=True)


def register_handlers(
    router: Router,
    analysis_service: PhraseAnalysisService,
    interaction_service: InteractionService
):
    handlers = BotHandlers(analysis_service, interaction_service)
    
    router.message.register(handlers.start_command, CommandStart())
    router.callback_query.register(handlers.decode_callback, F.data == "decode")
    router.message.register(
        handlers.process_phrase, 
        AnalysisStates.waiting_for_phrase
    )
    router.callback_query.register(handlers.examples_callback, F.data == "examples")
    router.callback_query.register(
        handlers.example_detail_callback, 
        F.data.startswith("example_")
    )
    router.callback_query.register(handlers.how_it_works_callback, F.data == "how_it_works")
    router.callback_query.register(handlers.tips_callback, F.data == "tips")
    router.callback_query.register(handlers.home_callback, F.data == "home")
    router.callback_query.register(
        handlers.more_options_callback,
        F.data == "more_options"
    )
    router.callback_query.register(
        handlers.similar_examples_callback,
        F.data == "similar"
    )
    router.callback_query.register(
        handlers.feedback_positive_callback, 
        F.data == "feedback_positive"
    )
    router.callback_query.register(
        handlers.feedback_negative_callback, 
        F.data == "feedback_negative"
    )