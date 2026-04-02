import json
from enum import Enum
from typing import List, Dict
from pydantic import BaseModel, Field, ValidationError

from util.llm_provider import call_yandex_gpt, call_gemini
from util.formatters import clean_llm_json


# --- Модели данных ---

class SalaryRange(BaseModel):
    """Минимальная, медианная и максимальная зарплаты."""
    min: int = Field(..., description="Нижняя граница (от)")
    median: int = Field(..., description="Медиана")
    max: int = Field(..., description="Верхняя граница (до)")


class RegionalSalaries(BaseModel):
    """Распределение зарплат по ключевым локациям."""
    Moscow: SalaryRange = Field(..., description="Зарплаты в Москве (в тыс. руб.)")
    Regions: SalaryRange = Field(..., description="Зарплаты в регионах РФ (в тыс. руб.)")
    Remote_USD: SalaryRange = Field(..., description="Зарплаты на удаленке в валюте (в USD)")


class MarketTrendStatus(str, Enum):
    """Общий статус динамики рынка для данного стека."""
    GROWING = "growing"
    STABLE = "stable"
    DECLINING = "declining"


class MarketTrend(BaseModel):
    """Анализ тренда рынка."""
    status: MarketTrendStatus
    reason: str = Field(..., description="Краткое обоснование тренда (1–2 предложения)")


class SalaryTable(BaseModel):
    """Зарплатная сетка по грейдам."""
    Junior: RegionalSalaries
    Middle: RegionalSalaries
    Senior: RegionalSalaries
    Lead: RegionalSalaries


class SalaryEstimatorResponse(BaseModel):
    """Полный отчет по зарплатам и компаниям."""
    salary_table: SalaryTable
    market_trend: MarketTrend
    top_employers: List[str] = Field(..., description="Список из 3-5 реальных компаний-работодателей")


class SalaryEstimator:
    def __init__(self, logger):
        self.logger = logger.getChild("SalaryEstimator")

    def estimate(self, skill_map: dict) -> SalaryEstimatorResponse:
        self.logger.info("Начало оценки зарплат и трендов")

        json_schema = SalaryEstimatorResponse.model_json_schema()

        system_instruction = f"""
        Ты - старший аналитик по компенсациям в IT.
        Твоя задача - рассчитать актуальные и реалистичные вилки зарплат на основе переданного стека технологий.

        ПРАВИЛА ОЦЕНКИ:
        - Ответ СТРОГО в формате JSON.
        - Помни что чсто зарплаты завышены, стоит указывать более вероятную зарплату
        - Москва и Регионы: значения в ТЫСЯЧАХ рублей (например, 150 означает 150 000).
        - Remote_USD: значения в долларах США.
        - Вилки должны быть реалистичными для 2026 года.
        - В top_employers укажи только реально существующие компании, активно нанимающие этот стек.
        
        ФОРМАТ ОТВЕТА:
        {json.dumps(json_schema, ensure_ascii=False)}
        """

        prompt = f"Рассчитай зарплаты для следующего стека (skill_map): {json.dumps(skill_map, ensure_ascii=False)}"

        try:
            response = call_yandex_gpt(prompt=prompt, system_instruction=system_instruction)

            clean_json_str = clean_llm_json(response)
            result = SalaryEstimatorResponse.model_validate_json(clean_json_str)

            self.logger.info("Зарплатная таблица и тренды успешно получены и проверены")
            return result

        except ValidationError as e:
            self.logger.error(f"Ошибка валидации зарплат: {e.json()}")
            raise ValueError("Данные от LLM не соответствуют зарплатному контракту.")
        except Exception as e:
            self.logger.error(f"Ошибка в процессе оценки: {e}")
            raise
