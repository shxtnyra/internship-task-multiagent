import json
from typing import List
from pydantic import BaseModel, Field, ValidationError

from util.llm_provider import call_yandex_gpt, call_gemini
from util.formatters import clean_llm_json


# --- Модели данных ---

class VerificationResult(BaseModel):
    """Результат технического аудита отчета."""

    quality_score: int = Field(
        ...,
        ge=0, le=100,
        description="Итоговая оценка качества от 0 до 100. 100 — идеальный, логически непротиворечивый отчет."
    )
    is_consistent: bool = Field(
        ...,
        description="Итоговый вердикт о целостности отчёта, можно ли на него ориентироваться"
    )
    warnings: List[str] = Field(
        ...,
        description="Список найденных аномалий, галлюцинаций или логических несостыковок."
    )
    rationale_quality_score: str = Field(
        ...,
        description="Подробное и сухое обоснование выставленной оценки."
    )


class QualityVerifierResponse(BaseModel):
    """Корневой объект ответа аудитора."""
    verification: VerificationResult


class QualityVerifier:
    def __init__(self, logger):
        self.logger = logger.getChild("QualityVerifier")

    def verify_report(self, report: dict) -> VerificationResult:
        self.logger.info("Запуск технического аудита отчета")

        json_schema = QualityVerifierResponse.model_json_schema()

        system_instruction = f"""
        Ты — Senior Technical Auditor & Data Scientist. Твоя задача — провести жесткий аудит IT-отчета.
        Ты ищешь галлюцинации, логические ошибки и несоответствия между секциями (например, когда в навыках указан один стек, а в обучении — другой).        

        КРИТЕРИИ ПРОВЕРКИ:
        - Соответствие навыков (skill_map) и плана обучения (learning_path).
        - Реалистичность зарплатных вилок для 2026 года.
        - Наличие галлюцинаций (вымышленные технологии или несуществующие компании).
        - Отсутствие вежливости: только факты, только критика.
        
        ФОРМАТ ОТВЕТА:
        {json.dumps(json_schema, ensure_ascii=False)}
        """

        prompt = f"Проведи глубокий аудит следующего отчета: {json.dumps(report, ensure_ascii=False)}"

        try:
            response = call_yandex_gpt(prompt, system_instruction)

            clean_json_str = clean_llm_json(response)
            result = QualityVerifierResponse.model_validate_json(clean_json_str)

            self.logger.info(
                f"Аудит завершен. Score: {result.verification.quality_score}/100. "
                f"Warnings: {len(result.verification.warnings)}"
            )

            return result.verification

        except ValidationError as e:
            self.logger.error(f"Ошибка валидации аудита: {e.json()}")
            raise ValueError("Контролер качества вернул некорректную структуру данных.")
        except Exception as e:
            self.logger.error(f"Критическая ошибка QualityVerifier: {e}")
            raise
