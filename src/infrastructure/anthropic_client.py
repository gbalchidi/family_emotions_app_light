import anthropic
from typing import List, Optional
import logging
from datetime import datetime

from ..domain.entities import PhraseAnalysis, EmotionalState, ExamplePhrase


logger = logging.getLogger(__name__)


class AnthropicAnalyzer:
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-sonnet-20240229"
    
    async def analyze(
        self,
        phrase: str,
        context: str = "",
        age_range: str = "10-17",
        similar_examples: List[ExamplePhrase] = None
    ) -> PhraseAnalysis:
        try:
            prompt = self._build_prompt(phrase, context, age_range, similar_examples)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return self._parse_response(phrase, response.content[0].text)
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def _build_prompt(
        self,
        phrase: str,
        context: str,
        age_range: str,
        similar_examples: List[ExamplePhrase]
    ) -> str:
        examples_text = ""
        if similar_examples:
            examples_text = "\n\nПохожие примеры из базы:\n"
            for ex in similar_examples[:2]:
                examples_text += f"- \"{ex.phrase}\": {ex.typical_meaning}\n"
        
        context_text = f"\nДополнительный контекст: {context}" if context else ""
        
        return f"""Ты опытный детский психолог, специализирующийся на подростковой психологии.

Родитель прислал фразу, которую сказал его ребёнок/подросток (возраст {age_range} лет):
"{phrase}"{context_text}{examples_text}

Проанализируй эту фразу и предоставь структурированный ответ в следующем формате:

ЭМОЦИОНАЛЬНОЕ СОСТОЯНИЕ:
[Опиши основные эмоции, которые испытывает ребёнок. Используй слова: angry, frustrated, sad, anxious, defensive, overwhelmed, disconnected, confused]

ИСТИННЫЙ СМЫСЛ:
[Объясни в 2-3 предложениях, что на самом деле хочет сказать ребёнок]

ПОТРЕБНОСТЬ РЕБЁНКА:
[В 1-2 предложениях опиши, что нужно ребёнку в данный момент]

ВАРИАНТЫ ОТВЕТА:
[Предложи 3 конкретных фразы, которые родитель может использовать в ответ. Каждая фраза должна быть естественной и поддерживающей]

ЧЕГО ИЗБЕГАТЬ:
[Укажи 3 конкретных действия или фразы, которых следует избегать]

Ответ должен быть:
- Емким и практичным
- Поддерживающим для родителя
- Учитывающим возрастные особенности
- Без осуждения и критики"""
    
    def _parse_response(self, original_phrase: str, response_text: str) -> PhraseAnalysis:
        sections = self._extract_sections(response_text)
        
        emotional_states = self._parse_emotional_states(
            sections.get("ЭМОЦИОНАЛЬНОЕ СОСТОЯНИЕ", "")
        )
        
        return PhraseAnalysis(
            original_phrase=original_phrase,
            emotional_state=emotional_states,
            true_meaning=sections.get("ИСТИННЫЙ СМЫСЛ", "Не удалось определить"),
            child_needs=sections.get("ПОТРЕБНОСТЬ РЕБЁНКА", "Понимание и поддержка"),
            suggested_responses=self._parse_list_section(sections.get("ВАРИАНТЫ ОТВЕТА", "")),
            what_to_avoid=self._parse_list_section(sections.get("ЧЕГО ИЗБЕГАТЬ", "")),
            confidence_score=0.85,
            analyzed_at=datetime.now()
        )
    
    def _extract_sections(self, text: str) -> dict:
        sections = {}
        current_section = None
        current_content = []
        
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
                
            if any(header in line.upper() for header in [
                "ЭМОЦИОНАЛЬНОЕ СОСТОЯНИЕ:",
                "ИСТИННЫЙ СМЫСЛ:",
                "ПОТРЕБНОСТЬ РЕБЁНКА:",
                "ВАРИАНТЫ ОТВЕТА:",
                "ЧЕГО ИЗБЕГАТЬ:"
            ]):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line.rstrip(":")
                current_content = []
            else:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()
        
        return sections
    
    def _parse_emotional_states(self, text: str) -> List[EmotionalState]:
        states = []
        emotion_keywords = {
            "angry": EmotionalState.ANGRY,
            "frustrated": EmotionalState.FRUSTRATED,
            "sad": EmotionalState.SAD,
            "anxious": EmotionalState.ANXIOUS,
            "defensive": EmotionalState.DEFENSIVE,
            "overwhelmed": EmotionalState.OVERWHELMED,
            "disconnected": EmotionalState.DISCONNECTED,
            "confused": EmotionalState.CONFUSED
        }
        
        text_lower = text.lower()
        for keyword, state in emotion_keywords.items():
            if keyword in text_lower:
                states.append(state)
        
        if not states:
            states.append(EmotionalState.CONFUSED)
        
        return states
    
    def _parse_list_section(self, text: str) -> List[str]:
        items = []
        for line in text.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                cleaned = line.lstrip("0123456789.-•) ").strip()
                if cleaned:
                    items.append(cleaned)
            elif line and len(items) < 3:
                items.append(line)
        
        return items[:3] if items else ["Информация недоступна"]