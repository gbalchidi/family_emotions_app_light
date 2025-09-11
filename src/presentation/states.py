from aiogram.fsm.state import State, StatesGroup


class AnalysisStates(StatesGroup):
    waiting_for_phrase = State()
    waiting_for_context = State()
    processing = State()


class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()