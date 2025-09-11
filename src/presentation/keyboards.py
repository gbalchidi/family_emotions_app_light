from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

from ..domain.entities import ExamplePhrase


class KeyboardBuilder:
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="🔍 Расшифровать фразу", callback_data="decode")],
            [InlineKeyboardButton(text="📚 Посмотреть примеры", callback_data="examples")],
            [InlineKeyboardButton(text="❓ Как это работает", callback_data="how_it_works")],
            [InlineKeyboardButton(text="💡 Советы родителям", callback_data="tips")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def after_analysis_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(text="🔄 Новая фраза", callback_data="decode"),
                InlineKeyboardButton(text="💡 Ещё варианты", callback_data="more_options")
            ],
            [
                InlineKeyboardButton(text="📚 Похожие примеры", callback_data="similar"),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def examples_menu(examples: List[ExamplePhrase]) -> InlineKeyboardMarkup:
        keyboard = []
        
        emoji_map = {
            "Отстань!": "😤",
            "Ты ничего не понимаешь": "🙄",
            "Мне всё равно": "😑",
            "Ненавижу школу!": "😠",
            "Не хочу об этом говорить": "🤐",
            "У меня всё нормально": "😔",
            "Достали все!": "😡",
            "Уйду из дома!": "🚪"
        }
        
        for example in examples[:8]:
            emoji = emoji_map.get(example.phrase, "💭")
            button_text = f"{emoji} \"{example.phrase}\""
            callback_data = f"example_{examples.index(example)}"
            keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def back_to_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="🔍 Попробовать", callback_data="decode")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def error_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="decode")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def feedback_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(text="👍 Полезно", callback_data="feedback_positive"),
                InlineKeyboardButton(text="👎 Не помогло", callback_data="feedback_negative")
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)