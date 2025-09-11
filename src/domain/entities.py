from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum


class EmotionalState(Enum):
    ANGRY = "angry"
    FRUSTRATED = "frustrated"
    SAD = "sad"
    ANXIOUS = "anxious"
    DEFENSIVE = "defensive"
    OVERWHELMED = "overwhelmed"
    DISCONNECTED = "disconnected"
    CONFUSED = "confused"


@dataclass
class PhraseAnalysis:
    original_phrase: str
    emotional_state: List[EmotionalState]
    true_meaning: str
    child_needs: str
    suggested_responses: List[str]
    what_to_avoid: List[str]
    confidence_score: float
    analyzed_at: datetime

    def __post_init__(self):
        if not self.original_phrase:
            raise ValueError("Original phrase cannot be empty")
        if self.confidence_score < 0 or self.confidence_score > 1:
            raise ValueError("Confidence score must be between 0 and 1")


@dataclass
class ExamplePhrase:
    phrase: str
    category: str
    emotional_context: str
    typical_meaning: str
    suggested_approach: str
    
    def matches_pattern(self, user_phrase: str) -> bool:
        normalized_user = user_phrase.lower().strip()
        normalized_example = self.phrase.lower().strip()
        return normalized_example in normalized_user or normalized_user in normalized_example


@dataclass
class UserInteraction:
    user_id: int
    phrase: str
    analysis: Optional[PhraseAnalysis]
    timestamp: datetime
    feedback: Optional[str] = None
    
    @property
    def is_analyzed(self) -> bool:
        return self.analysis is not None