import argparse
import logging
from pathlib import Path

from agent.career_advisor import CareerAdvisor
from agent.market_analyst import MarketAnalyst
from agent.quality_verifier import QualityVerifier
from agent.salary_estimator import SalaryEstimator
from util.report_storage import save_json_report, save_md_report


def init_args():
    parser = argparse.ArgumentParser(
        description='Мультиагент помощник для анализа карьерного рынка IT'
    )

    parser.add_argument(
        '--role',
        type=str,
        required=True,
        help='Название IT-специальности'
    )

    parser.add_argument(
        '--out',
        type=str,
        default='examples',
        help='Директория для вывода'
    )

    args = parser.parse_args()
    role = args.role
    out = args.out

    return role, out

def init_logging(out, role):
    out_path = Path(out)
    out_path.mkdir(parents=True, exist_ok=True)

    log_file = out_path / f"{role.replace(' ', '_')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("MultiAgentSystem")

def main():
    role, out = init_args()
    logger = init_logging(out, role)

    full_context = {}

    logger.info(f"--- Запуск генерации отчета для роли: {role} ---")

    try:
        # Инициализирую всех агентов
        market_analyst = MarketAnalyst(logger)
        salary_estimator = SalaryEstimator(logger)
        career_advisor = CareerAdvisor(logger)
        quality_verifier = QualityVerifier(logger)

        # Агент 1: Анализ рынка
        skill_map = market_analyst.analyze(role)
        full_context.update(skill_map.model_dump())

        # Агент 2: Оценка зарплат
        salary_data = salary_estimator.estimate(full_context)
        full_context.update(salary_data.model_dump())

        # Агент 3: Карьерный совет
        career_data = career_advisor.advise(full_context)
        full_context.update(career_data.model_dump())

        # Агент 4: Верификация отчёта
        verification = quality_verifier.verify_report(full_context)
        full_context.update(verification.model_dump())

        # 5: Сохранение отчётов
        logger.info(f"Сохранение отчёта в {out}")
        save_json_report(full_context, out)
        save_md_report(full_context, out)


    except Exception as ex:
        logger.error(f"Критический сбой в цепочке агентов: {ex}", exc_info=True)


if __name__ == "__main__":
    main()
