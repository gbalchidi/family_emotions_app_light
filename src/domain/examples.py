from typing import List, Dict
from .entities import ExamplePhrase


class PhraseExamples:
    
    @staticmethod
    def get_common_phrases() -> List[ExamplePhrase]:
        return [
            ExamplePhrase(
                phrase="Отстань!",
                category="boundaries",
                emotional_context="Перегруженность, потребность в личном пространстве",
                typical_meaning="Мне нужно время побыть одному и разобраться в своих чувствах",
                suggested_approach="Дайте пространство, но покажите готовность поговорить позже"
            ),
            ExamplePhrase(
                phrase="Ты ничего не понимаешь",
                category="disconnection",
                emotional_context="Чувство непонимания, одиночество",
                typical_meaning="Мне кажется, что мои чувства и опыт обесценивают",
                suggested_approach="Признайте сложность ситуации и покажите желание понять"
            ),
            ExamplePhrase(
                phrase="Мне всё равно",
                category="defense",
                emotional_context="Защитная реакция на разочарование или боль",
                typical_meaning="Мне очень важно, но я боюсь показать уязвимость",
                suggested_approach="Не давите, покажите принятие любого решения"
            ),
            ExamplePhrase(
                phrase="Ненавижу школу!",
                category="frustration",
                emotional_context="Стресс, социальное давление, усталость",
                typical_meaning="В школе происходит что-то, с чем я не справляюсь",
                suggested_approach="Узнайте о конкретных ситуациях без критики"
            ),
            ExamplePhrase(
                phrase="Не хочу об этом говорить",
                category="boundaries",
                emotional_context="Неготовность к обсуждению, страх осуждения",
                typical_meaning="Мне нужно время обдумать или я не доверяю реакции",
                suggested_approach="Уважайте границы, предложите альтернативные способы поддержки"
            ),
            ExamplePhrase(
                phrase="У меня всё нормально",
                category="masking",
                emotional_context="Скрытие проблем, нежелание беспокоить",
                typical_meaning="Есть проблемы, но я не готов ими делиться",
                suggested_approach="Покажите доступность без навязчивости"
            ),
            ExamplePhrase(
                phrase="Достали все!",
                category="overwhelm",
                emotional_context="Эмоциональное истощение, перегрузка",
                typical_meaning="Я устал от социального взаимодействия и давления",
                suggested_approach="Предложите способы снизить нагрузку"
            ),
            ExamplePhrase(
                phrase="Уйду из дома!",
                category="desperation",
                emotional_context="Чувство безвыходности, желание контроля",
                typical_meaning="Мне невыносимо тяжело и я не вижу другого выхода",
                suggested_approach="Серьёзно отнеситесь к чувствам, предложите совместный поиск решения"
            )
        ]
    
    @staticmethod
    def get_by_category(category: str) -> List[ExamplePhrase]:
        all_phrases = PhraseExamples.get_common_phrases()
        return [p for p in all_phrases if p.category == category]
    
    @staticmethod
    def find_similar(user_phrase: str) -> List[ExamplePhrase]:
        all_phrases = PhraseExamples.get_common_phrases()
        similar = []
        for example in all_phrases:
            if example.matches_pattern(user_phrase):
                similar.append(example)
        return similar
    
    @staticmethod
    def get_categories() -> Dict[str, str]:
        return {
            "boundaries": "Границы и пространство",
            "disconnection": "Непонимание и отчуждение",
            "defense": "Защитные реакции",
            "frustration": "Фрустрация и злость",
            "masking": "Скрытие чувств",
            "overwhelm": "Перегруженность",
            "desperation": "Отчаяние"
        }