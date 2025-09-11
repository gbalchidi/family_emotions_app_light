from typing import List
from dataclasses import dataclass


@dataclass(frozen=True)
class ResponseSuggestion:
    text: str
    tone: str
    effectiveness_rating: int
    
    def __post_init__(self):
        if not 1 <= self.effectiveness_rating <= 5:
            raise ValueError("Effectiveness rating must be between 1 and 5")
        if not self.text:
            raise ValueError("Response text cannot be empty")


@dataclass(frozen=True)
class EmotionalContext:
    primary_emotion: str
    secondary_emotions: List[str]
    intensity_level: int
    underlying_needs: List[str]
    
    def __post_init__(self):
        if not 1 <= self.intensity_level <= 10:
            raise ValueError("Intensity level must be between 1 and 10")
        if not self.primary_emotion:
            raise ValueError("Primary emotion cannot be empty")
    
    @property
    def is_high_intensity(self) -> bool:
        return self.intensity_level >= 7
    
    @property
    def all_emotions(self) -> List[str]:
        return [self.primary_emotion] + self.secondary_emotions


@dataclass(frozen=True)
class AnalysisRequest:
    phrase: str
    context: str = ""
    child_age_range: str = "10-17"
    
    def __post_init__(self):
        if not self.phrase:
            raise ValueError("Phrase cannot be empty")
        if len(self.phrase) < 2:
            raise ValueError("Phrase too short for analysis")
        if len(self.phrase) > 500:
            raise ValueError("Phrase too long (max 500 characters)")
    
    @property
    def has_context(self) -> bool:
        return bool(self.context)