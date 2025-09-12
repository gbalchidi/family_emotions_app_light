import anthropic
from typing import List, Optional
import logging
from datetime import datetime
import os
import httpx

from ..domain.entities import PhraseAnalysis, EmotionalState, ExamplePhrase


logger = logging.getLogger(__name__)


class AnthropicAnalyzer:
    
    def __init__(self, api_key: str, use_proxy: bool = False, proxy_url: Optional[str] = None):
        try:
            if use_proxy and proxy_url:
                logger.info(f"Configuring Anthropic client with proxy: {proxy_url}")
                
                # For SOCKS5 proxy, use httpx-socks
                if 'socks5://' in proxy_url:
                    try:
                        from httpx_socks import SyncProxyTransport
                        transport = SyncProxyTransport.from_url(proxy_url)
                        http_client = httpx.Client(
                            transport=transport, 
                            timeout=httpx.Timeout(60.0),
                            verify=False  # Disable SSL verification for proxy
                        )
                        logger.info("Using SOCKS5 proxy via httpx-socks")
                    except ImportError:
                        logger.warning("httpx-socks not available, falling back to regular httpx")
                        # Fallback to regular httpx
                        http_client = httpx.Client(
                            proxies=proxy_url,
                            timeout=httpx.Timeout(60.0),
                            verify=False
                        )
                else:
                    # HTTP proxy
                    logger.info("Using HTTP proxy")
                    http_client = httpx.Client(
                        proxies={
                            "http://": proxy_url,
                            "https://": proxy_url
                        },
                        timeout=httpx.Timeout(60.0)
                    )
                    
                self.client = anthropic.Anthropic(
                    api_key=api_key,
                    http_client=http_client
                )
            else:
                logger.info("Configuring Anthropic client without proxy")
                self.client = anthropic.Anthropic(api_key=api_key)
            
            self.model = "claude-3-haiku-20240307"
            logger.info(f"Anthropic client initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise
    
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
                max_tokens=900,
                temperature=0.6,
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
        
        return f"""ЗАДАЧА
Ты опытный детский психолог, специализирующийся на подростках. По фразе ребёнка/подростка проанализируй состояние, намерение и потребности, а затем предложи родителю короткие, поддерживающие и безопасные ответы.

ВХОДНЫЕ ДАННЫЕ
• Возраст ребёнка: {age_range} лет
• Фраза ребёнка: "{phrase}"{context_text}{examples_text}

ПРАВИЛА И ТОН
• Поддерживай родителя, не осуждай ребёнка. Избегай ярлыков и диагнозов.
• Пиши по-русски простым, тёплым языком. Используй я-сообщения во фразах-ответах.
• Адаптируй стиль под возраст:
  - 10-12: короче, конкретнее, больше структурной поддержки
  - 13-15: признание чувств, совместный поиск решений
  - 16-17: уважение автономии, партнёрский тон
• Будь краток: каждый раздел — 1-3 строки. Чёткие формулировки без общих слов.

БЕЗОПАСНОСТЬ
Если во фразе есть признаки риска (самоповреждение/суицид, насилие/угрозы, бегство из дома, употребление веществ):
• Сначала выведи раздел "СРОЧНО О БЕЗОПАСНОСТИ" с 2-4 конкретными шагами
• Затем основные разделы. Не ставь диагнозов.

ФОРМАТ ВЫВОДА (строго соблюдать):

ЭМОЦИОНАЛЬНОЕ СОСТОЯНИЕ:
[3-5 эмоций по-русски: злость, раздражение, грусть, тревога, защищённость, перегруженность, отчуждение, растерянность]

ИСТИННЫЙ СМЫСЛ:
[2-3 предложения, что ребёнок пытается донести]

ПОТРЕБНОСТЬ РЕБЁНКА:
[1-2 предложения о ключевых потребностях]

ВАРИАНТЫ ОТВЕТА:
[3 короткие фразы в кавычках, естественные, с я-сообщениями, адаптированные под возраст]

ЧЕГО ИЗБЕГАТЬ:
[3 конкретных пункта - формулировки или действия]"""
    
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
                "ЧЕГО ИЗБЕГАТЬ:",
                "СРОЧНО О БЕЗОПАСНОСТИ:"
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
            # Russian emotions mapping
            "злость": EmotionalState.ANGRY,
            "злится": EmotionalState.ANGRY,
            "гнев": EmotionalState.ANGRY,
            "раздражение": EmotionalState.FRUSTRATED,
            "раздражён": EmotionalState.FRUSTRATED,
            "фрустрация": EmotionalState.FRUSTRATED,
            "грусть": EmotionalState.SAD,
            "печаль": EmotionalState.SAD,
            "грустит": EmotionalState.SAD,
            "тревога": EmotionalState.ANXIOUS,
            "тревожность": EmotionalState.ANXIOUS,
            "беспокойство": EmotionalState.ANXIOUS,
            "защищённость": EmotionalState.DEFENSIVE,
            "защитная": EmotionalState.DEFENSIVE,
            "защищается": EmotionalState.DEFENSIVE,
            "перегруженность": EmotionalState.OVERWHELMED,
            "перегружен": EmotionalState.OVERWHELMED,
            "истощение": EmotionalState.OVERWHELMED,
            "отчуждение": EmotionalState.DISCONNECTED,
            "отчуждён": EmotionalState.DISCONNECTED,
            "одиночество": EmotionalState.DISCONNECTED,
            "растерянность": EmotionalState.CONFUSED,
            "растерян": EmotionalState.CONFUSED,
            "замешательство": EmotionalState.CONFUSED,
            # Keep English as fallback
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
            if keyword in text_lower and state not in states:
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