import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.application.services import (
    PhraseAnalysisService,
    InteractionService,
    ResponseFormatterService
)
from src.domain.entities import PhraseAnalysis, EmotionalState, ExamplePhrase
from src.domain.value_objects import AnalysisRequest


class TestPhraseAnalysisService:
    
    @pytest.mark.asyncio
    async def test_analyze_phrase_success(self):
        mock_analyzer = Mock()
        mock_analyzer.analyze = AsyncMock(return_value=PhraseAnalysis(
            original_phrase="Test phrase",
            emotional_state=[EmotionalState.ANGRY],
            true_meaning="Test meaning",
            child_needs="Test needs",
            suggested_responses=["Response 1"],
            what_to_avoid=["Avoid 1"],
            confidence_score=0.9,
            analyzed_at=datetime.now()
        ))
        
        service = PhraseAnalysisService(anthropic_analyzer=mock_analyzer)
        request = AnalysisRequest(phrase="Test phrase")
        
        result = await service.analyze_phrase(request)
        
        assert result.original_phrase == "Test phrase"
        assert result.confidence_score == 0.9
        mock_analyzer.analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_phrase_fallback(self):
        mock_analyzer = Mock()
        mock_analyzer.analyze = AsyncMock(side_effect=Exception("API Error"))
        
        service = PhraseAnalysisService(anthropic_analyzer=mock_analyzer)
        request = AnalysisRequest(phrase="Test phrase")
        
        result = await service.analyze_phrase(request)
        
        assert result.original_phrase == "Test phrase"
        assert result.confidence_score == 0.3
        assert EmotionalState.CONFUSED in result.emotional_state
    
    def test_get_examples(self):
        mock_analyzer = Mock()
        service = PhraseAnalysisService(anthropic_analyzer=mock_analyzer)
        
        examples = service.get_examples()
        
        assert len(examples) > 0
        assert all(isinstance(ex, ExamplePhrase) for ex in examples)


class TestInteractionService:
    
    def test_record_interaction(self):
        service = InteractionService()
        
        interaction = service.record_interaction(
            user_id=123,
            phrase="Test phrase",
            analysis=None
        )
        
        assert interaction.user_id == 123
        assert interaction.phrase == "Test phrase"
        assert not interaction.is_analyzed
    
    def test_get_user_interactions(self):
        service = InteractionService()
        
        service.record_interaction(user_id=123, phrase="Phrase 1")
        service.record_interaction(user_id=456, phrase="Phrase 2")
        service.record_interaction(user_id=123, phrase="Phrase 3")
        
        user_interactions = service.get_user_interactions(123)
        
        assert len(user_interactions) == 2
        assert all(i.user_id == 123 for i in user_interactions)
    
    def test_add_feedback(self):
        service = InteractionService()
        
        service.record_interaction(user_id=123, phrase="Test")
        result = service.add_feedback(user_id=123, feedback="positive")
        
        assert result is True
        interactions = service.get_user_interactions(123)
        assert interactions[-1].feedback == "positive"


class TestResponseFormatterService:
    
    def test_format_analysis(self):
        analysis = PhraseAnalysis(
            original_phrase="Отстань",
            emotional_state=[EmotionalState.ANGRY, EmotionalState.OVERWHELMED],
            true_meaning="Нужно пространство",
            child_needs="Время побыть одному",
            suggested_responses=["Дам тебе время", "Я рядом, когда понадоблюсь"],
            what_to_avoid=["Не давить", "Не критиковать"],
            confidence_score=0.85,
            analyzed_at=datetime.now()
        )
        
        formatted = ResponseFormatterService.format_analysis(analysis)
        
        assert "Отстань" in formatted
        assert "angry" in formatted.lower()
        assert "Нужно пространство" in formatted
        assert "Дам тебе время" in formatted
    
    def test_format_example(self):
        example = ExamplePhrase(
            phrase="Мне всё равно",
            category="defense",
            emotional_context="Защитная реакция",
            typical_meaning="Мне важно, но боюсь показать",
            suggested_approach="Не давить"
        )
        
        formatted = ResponseFormatterService.format_example(example)
        
        assert "Мне всё равно" in formatted
        assert "Защитная реакция" in formatted
        assert "Не давить" in formatted
    
    def test_format_error_message(self):
        message = ResponseFormatterService.format_error_message()
        
        assert "Упс" in message
        assert "слишком короткая" in message