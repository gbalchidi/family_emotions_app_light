import pytest
from datetime import datetime

from src.domain.entities import (
    PhraseAnalysis, 
    EmotionalState, 
    ExamplePhrase, 
    UserInteraction
)
from src.domain.value_objects import (
    ResponseSuggestion, 
    EmotionalContext, 
    AnalysisRequest
)


class TestPhraseAnalysis:
    
    def test_create_valid_analysis(self):
        analysis = PhraseAnalysis(
            original_phrase="Отстань от меня",
            emotional_state=[EmotionalState.ANGRY, EmotionalState.OVERWHELMED],
            true_meaning="Мне нужно пространство",
            child_needs="Время побыть одному",
            suggested_responses=["Хорошо, я дам тебе время"],
            what_to_avoid=["Не давить"],
            confidence_score=0.85,
            analyzed_at=datetime.now()
        )
        
        assert analysis.original_phrase == "Отстань от меня"
        assert EmotionalState.ANGRY in analysis.emotional_state
        assert analysis.confidence_score == 0.85
    
    def test_invalid_empty_phrase(self):
        with pytest.raises(ValueError, match="Original phrase cannot be empty"):
            PhraseAnalysis(
                original_phrase="",
                emotional_state=[EmotionalState.ANGRY],
                true_meaning="Test",
                child_needs="Test",
                suggested_responses=["Test"],
                what_to_avoid=["Test"],
                confidence_score=0.5,
                analyzed_at=datetime.now()
            )
    
    def test_invalid_confidence_score(self):
        with pytest.raises(ValueError, match="Confidence score must be between 0 and 1"):
            PhraseAnalysis(
                original_phrase="Test",
                emotional_state=[EmotionalState.ANGRY],
                true_meaning="Test",
                child_needs="Test",
                suggested_responses=["Test"],
                what_to_avoid=["Test"],
                confidence_score=1.5,
                analyzed_at=datetime.now()
            )


class TestExamplePhrase:
    
    def test_create_example(self):
        example = ExamplePhrase(
            phrase="Ты ничего не понимаешь",
            category="disconnection",
            emotional_context="Чувство непонимания",
            typical_meaning="Мои чувства обесценивают",
            suggested_approach="Показать желание понять"
        )
        
        assert example.phrase == "Ты ничего не понимаешь"
        assert example.category == "disconnection"
    
    def test_matches_pattern(self):
        example = ExamplePhrase(
            phrase="Отстань",
            category="boundaries",
            emotional_context="Test",
            typical_meaning="Test",
            suggested_approach="Test"
        )
        
        assert example.matches_pattern("Отстань от меня")
        assert example.matches_pattern("ОТСТАНЬ")
        assert not example.matches_pattern("Привет")


class TestValueObjects:
    
    def test_response_suggestion(self):
        suggestion = ResponseSuggestion(
            text="Я понимаю твои чувства",
            tone="supportive",
            effectiveness_rating=4
        )
        
        assert suggestion.text == "Я понимаю твои чувства"
        assert suggestion.effectiveness_rating == 4
    
    def test_invalid_effectiveness_rating(self):
        with pytest.raises(ValueError, match="Effectiveness rating must be between 1 and 5"):
            ResponseSuggestion(
                text="Test",
                tone="test",
                effectiveness_rating=6
            )
    
    def test_emotional_context(self):
        context = EmotionalContext(
            primary_emotion="anger",
            secondary_emotions=["frustration", "sadness"],
            intensity_level=8,
            underlying_needs=["space", "understanding"]
        )
        
        assert context.primary_emotion == "anger"
        assert context.is_high_intensity
        assert "anger" in context.all_emotions
        assert "frustration" in context.all_emotions
    
    def test_analysis_request(self):
        request = AnalysisRequest(
            phrase="Мне всё равно",
            context="После ссоры",
            child_age_range="13-15"
        )
        
        assert request.phrase == "Мне всё равно"
        assert request.has_context
    
    def test_invalid_analysis_request(self):
        with pytest.raises(ValueError, match="Phrase cannot be empty"):
            AnalysisRequest(phrase="")
        
        with pytest.raises(ValueError, match="Phrase too short"):
            AnalysisRequest(phrase="А")
        
        with pytest.raises(ValueError, match="Phrase too long"):
            AnalysisRequest(phrase="x" * 501)