from typing import List, Optional
from datetime import datetime
import logging

from ..domain.entities import PhraseAnalysis, EmotionalState, ExamplePhrase, UserInteraction
from ..domain.value_objects import AnalysisRequest, EmotionalContext
from ..domain.examples import PhraseExamples
from ..infrastructure.anthropic_client import AnthropicAnalyzer


logger = logging.getLogger(__name__)


class PhraseAnalysisService:
    
    def __init__(self, anthropic_analyzer: AnthropicAnalyzer):
        self.analyzer = anthropic_analyzer
        self.examples = PhraseExamples()
    
    async def analyze_phrase(self, request: AnalysisRequest) -> PhraseAnalysis:
        try:
            logger.info(f"Analyzing phrase: {request.phrase[:50]}...")
            
            similar_examples = self.examples.find_similar(request.phrase)
            
            analysis = await self.analyzer.analyze(
                phrase=request.phrase,
                context=request.context,
                age_range=request.child_age_range,
                similar_examples=similar_examples
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing phrase: {e}")
            return self._create_fallback_analysis(request.phrase)
    
    def get_examples(self) -> List[ExamplePhrase]:
        return self.examples.get_common_phrases()
    
    def get_example_by_phrase(self, phrase: str) -> Optional[ExamplePhrase]:
        examples = self.examples.get_common_phrases()
        for example in examples:
            if example.phrase.lower() == phrase.lower():
                return example
        return None
    
    def _create_fallback_analysis(self, phrase: str) -> PhraseAnalysis:
        return PhraseAnalysis(
            original_phrase=phrase,
            emotional_state=[EmotionalState.CONFUSED],
            true_meaning="Не удалось проанализировать фразу. Попробуйте переформулировать или добавить контекст.",
            child_needs="Понимание и поддержка",
            suggested_responses=[
                "Я вижу, что тебе сложно. Давай попробуем разобраться вместе.",
                "Расскажи подробнее, что происходит?"
            ],
            what_to_avoid=[
                "Не обесценивайте чувства",
                "Не давите на ребёнка"
            ],
            confidence_score=0.3,
            analyzed_at=datetime.now()
        )


class InteractionService:
    
    def __init__(self):
        self.interactions: List[UserInteraction] = []
    
    def record_interaction(
        self, 
        user_id: int, 
        phrase: str, 
        analysis: Optional[PhraseAnalysis] = None
    ) -> UserInteraction:
        interaction = UserInteraction(
            user_id=user_id,
            phrase=phrase,
            analysis=analysis,
            timestamp=datetime.now()
        )
        self.interactions.append(interaction)
        return interaction
    
    def get_user_interactions(self, user_id: int) -> List[UserInteraction]:
        return [i for i in self.interactions if i.user_id == user_id]
    
    def add_feedback(self, user_id: int, feedback: str) -> bool:
        user_interactions = self.get_user_interactions(user_id)
        if user_interactions:
            latest = user_interactions[-1]
            latest.feedback = feedback
            return True
        return False


class ResponseFormatterService:
    
    @staticmethod
    def format_analysis(analysis: PhraseAnalysis) -> str:
        # Format emotions in Russian
        emotion_names = {
            "angry": "злость",
            "frustrated": "раздражение", 
            "sad": "грусть",
            "anxious": "тревога",
            "defensive": "защищённость",
            "overwhelmed": "перегруженность",
            "disconnected": "отчуждение",
            "confused": "растерянность"
        }
        emotions = ", ".join([emotion_names.get(e.value, e.value) for e in analysis.emotional_state])
        
        responses = "\n".join([f"• {r}" for r in analysis.suggested_responses])
        avoid = "\n".join([f"• {a}" for a in analysis.what_to_avoid])
        
        # Check if there's a safety section in the response
        safety_text = ""
        if hasattr(analysis, 'safety_notice') and analysis.safety_notice:
            safety_text = f"""🚨 СРОЧНО О БЕЗОПАСНОСТИ:
{analysis.safety_notice}

"""
        
        return f"""🔍 Анализ фразы: "{analysis.original_phrase}"
{safety_text}
📊 ЧТО РЕБЁНОК ЧУВСТВУЕТ:
{emotions.capitalize()}

💭 ЧТО НА САМОМ ДЕЛЕ ОЗНАЧАЕТ:
{analysis.true_meaning}

🎯 ПОТРЕБНОСТЬ РЕБЁНКА:
{analysis.child_needs}

💬 КАК ЛУЧШЕ ОТВЕТИТЬ:
{responses}

⚠️ ЧЕГО ИЗБЕГАТЬ:
{avoid}"""
    
    @staticmethod
    def format_example(example: ExamplePhrase) -> str:
        return f"""📚 Пример фразы: "{example.phrase}"

🎭 Эмоциональный контекст:
{example.emotional_context}

💭 Типичное значение:
{example.typical_meaning}

💡 Рекомендуемый подход:
{example.suggested_approach}"""
    
    @staticmethod
    def format_error_message() -> str:
        return """⚠️ Упс! Что-то пошло не так.

Возможно, фраза слишком короткая или содержит только эмодзи.

Попробуйте написать полную фразу, которую сказал ребёнок."""