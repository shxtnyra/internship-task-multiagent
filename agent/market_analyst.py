import json
from pydantic import BaseModel, Field, ValidationError

from util.llm_provider import call_yandex_gpt, call_gemini
from util.formatters import clean_llm_json
from enum import Enum
from typing import List
from pydantic import BaseModel, Field


# --- Модели данных ---

class Importance(str, Enum):
    """Оценка приоритетности навыка для успешного трудоустройства."""
    CRITICAL = "critical"
    IMPORTANT = "important"
    NICE_TO_HAVE = "nice-to-have"


class Trend(str, Enum):
    """Динамика востребованности технологии на рынке труда."""
    GROWING = "growing"
    STABLE = "stable"
    DECLINING = "declining"


class Skill(BaseModel):
    """Описание конкретного технологического навыка или инструмента."""

    name: str = Field(
        ...,
        description="Название технологии, инструмента или концепции (например, 'Python', 'Docker', 'Asyncio')"
    )
    importance: Importance = Field(
        ...,
        description="Степень важности навыка для данной специализации"
    )
    trend: Trend = Field(
        ...,
        description="Текущий тренд технологии на рынке"
    )


class SkillMap(BaseModel):
    """Карта навыков, структурированная по категориям компетенций."""

    languages: List[Skill] = Field(
        ...,
        description="Языки программирования, необходимые для этой роли"
    )
    frameworks: List[Skill] = Field(
        ...,
        description="Библиотеки и фреймворки (например, FastAPI, React, Pytest)"
    )
    infrastructure: List[Skill] = Field(
        ...,
        description="Инструменты CI/CD, облака, базы данных и контейнеризация, методологии управления, или архитектурные навыки"
    )
    soft_skills: List[Skill] = Field(
        ...,
        description="Межличностные навыки и методологии управления (например, Scrum, Teamwork)"
    )


class SkillMapResponse(BaseModel):
    """Финальный объект ответа аналитика рынка."""

    skill_map: SkillMap = Field(
        ...,
        description="Полная декомпозиция навыков для запрашиваемой специализации"
    )


class MarketAnalyst:
    def __init__(self, logger):
        self.logger = logger.getChild("MarketAnalyst")

    def analyze(self, specialty: str) -> SkillMapResponse:
        self.logger.info(f"Запуск анализа для: {specialty}")

        json_schema = SkillMapResponse.model_json_schema()

        system_instruction = f"""
        Ты — эксперт-аналитик IT-рынка с глубоким пониманием стеков технологий.
        Твоя задача — декомпозировать ИТ-специальность на атомарные навыки.

        ПРАВИЛА:
        - Ответ СТРОГО в формате JSON.
        - Если специальность не относится к IT, верни объект с пустыми списками.
        
        ФОРМАТ ОТВЕТА:
        {json.dumps(json_schema, ensure_ascii=False)}
        """

        prompt = f"Проанализируй рынок для специальности: '{specialty}'"

        try:
            response = call_yandex_gpt(prompt=prompt, system_instruction=system_instruction)

            clean_json_str = clean_llm_json(response)
            result = SkillMapResponse.model_validate_json(clean_json_str)

            self.logger.info("Skill_map успешно сформирован и проверен")
            return result

        except ValidationError as e:
            self.logger.error(f"Ошибка схемы данных: {e.json()}")
            raise ValueError("LLM нарушила контракт структуры данных.")
        except Exception as e:
            self.logger.error(f"Ошибка при обработке: {e}")
            raise
