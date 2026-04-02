import json
from typing import List
from pydantic import BaseModel, Field, ValidationError

from util.llm_provider import call_yandex_gpt, call_gemini
from util.formatters import clean_llm_json


# --- Модели данных ---

class LearningPhase(BaseModel):
    """Описание конкретного этапа обучения (30 дней)."""
    topics: List[str] = Field(
        ..., description="Список конкретных тем и технологий для изучения"
    )
    resources: List[str] = Field(
        ..., description="Минимум 2 конкретных ресурса: название книги, название курсы или название документация"
    )
    milestone: str = Field(
        ..., description="Осязаемый результат фазы (что должно быть сделано/написано)"
    )


class LearningPath(BaseModel):
    """План развития, разделенный на логические фазы."""
    Foundation: LearningPhase = Field(..., description="База и теоретическая подготовка")
    Practice: LearningPhase = Field(..., description="Активное применение и пет-проекты")
    Portfolio: LearningPhase = Field(..., description="Подготовка финального проекта и выход на рынок")


class GapAnalysis(BaseModel):
    """Анализ пробелов в текущих компетенциях."""
    quick_wins: List[str] = Field(
        ..., description="Навыки, которые можно подтянуть за 2–4 недели"
    )
    long_term: List[str] = Field(
        ..., description="Фундаментальные навыки, требующие 3+ месяцев изучения"
    )


class PortfolioProject(BaseModel):
    """Детальное описание проекта для портфолио."""
    name: str = Field(..., description="Название проекта")
    description: str = Field(..., description="Максимально подробное описание сути и функционала")
    skills_demonstrated: List[str] = Field(
        ..., description="Какие полезные или нужные навыки демострирует этот проект"
    )


class CareerPlanResponse(BaseModel):
    """Итоговый карьерный план от советника."""
    learning_path: LearningPath
    gap_analysis: GapAnalysis
    portfolio_project: PortfolioProject


class CareerAdvisor:
    def __init__(self, logger):
        self.logger = logger.getChild("CareerAdvisor")

    def advise(self, report: dict) -> CareerPlanResponse:
        self.logger.info("Формирование плана обучения")

        json_schema = CareerPlanResponse.model_json_schema()

        system_instruction = f"""
        Ты - профессиональный Карьерный советник в IT. 
        Твоя задача - составить реалистичный и детальный план обучения на основе данных о рынке и текущем стеке.

        ПРАВИЛА:
        - Ответ СТРОГО в формате JSON.
        - План обучения (learning_path) всегда состоит из 3-х фаз по 30 дней: Foundation, Practice, Portfolio.
        - В каждой фазе должен быть список тем и минимум 2 конкретных актуальных НАЗВАНИЯ ресурса (документация, книги или курсы). А так же ожидаемый milestone
        - portfolio_project — конкретная масксимально подробная идея с названием, описанием и списком используемых технологий
            - name название;
            - description описание;
            - skills_demonstrated какие навыки из необходимых для профессии демонстрирует этот проект.
        
        ФОРМАТ ОТВЕТА:
        {json.dumps(json_schema, ensure_ascii=False)}
        """

        prompt = f"Составь карьерный план на основе следующих данных: {json.dumps(report, ensure_ascii=False)}"

        try:
            response = call_yandex_gpt(prompt=prompt, system_instruction=system_instruction)
            clean_json_str = clean_llm_json(response)
            result = CareerPlanResponse.model_validate_json(clean_json_str)

            self.logger.info("Карьерный план успешно создан и валидирован")
            return result

        except ValidationError as e:
            self.logger.error(f"Ошибка валидации плана обучения: {e.json()}")
            raise ValueError("LLM вернула план с некорректной структурой.")
        except Exception as e:
            self.logger.error(f"Ошибка при работе CareerAdvisor: {e}")
            raise
