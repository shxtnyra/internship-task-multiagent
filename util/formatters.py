import re


def clean_llm_json(text: str) -> str:
    """
    Не смотря на все просьбы LLM, всё равно возвращет ответ либо с ```...```, либо с ```json...```
    Очищает ответ LLM от Markdown-разметки и лишних символов.
    Находит содержимое между ```json и ``` или просто чистит от обратных кавычек.
    """
    # Ищем блок кода json
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Если блока нет, просто убираем кавычки и лишние пробелы
    return text.strip().strip("`").strip()

def create_md_report(data: dict) -> str:
    """Генерация текстового отчета в строгом стиле Markdown."""
    role = data.get("role", "IT-Специалист").upper()

    report = [
        f"# КАРЬЕРНЫЙ ОТЧЕТ: {role}",
        f"Дата генерации: {data.get('generated_at', 'N/A')}",
        "\n---\n",
        _render_market_overview(data),
        _render_skill_map(data.get("skill_map", {})),
        _render_salaries(data.get("salary_table", {})),
        _render_learning_path(data.get("learning_path", {})),
        _render_gap_analysis(data.get("gap_analysis", {})),
        _render_portfolio(data.get("portfolio_project", {})),
        _render_audit(data)
    ]

    return "\n\n".join(report)

def _render_market_overview(data: dict) -> str:
    trend = data.get("market_trend", {})
    return (
        f"## Обзор рынка\n"
        f"**Текущий статус:** {trend.get('status', 'N/A').upper()}\n\n"
        f"**Обоснование:** {trend.get('reason', '')}"
    )


def _render_skill_map(skill_map: dict) -> str:
    sections = ["## Карта компетенций"]
    titles = {
        "languages": "Языки программирования",
        "frameworks": "Стек технологий и фреймворки",
        "infrastructure": "Инфраструктура и базы данных",
        "soft_skills": "Дополнительные навыки (Soft Skills)"
    }

    for key, title in titles.items():
        skills = skill_map.get(key, [])
        if not skills: continue

        sections.append(f"### {title}")
        sections.append("| Навык | Приоритет | Тренд |")
        sections.append("| :--- | :--- | :--- |")
        for s in skills:
            sections.append(f"| {s['name']} | {s['importance']} | {s['trend']} |")

    return "\n".join(sections)


def _render_salaries(salary_table: dict) -> str:
    if not salary_table: return ""

    rows = [
        "## Финансовые показатели (тыс. руб / USD)",
        "| Грейд | Москва (Медиана) | Регионы (Медиана) | Remote (USD) |",
        "| :--- | :--- | :--- | :--- |"
    ]

    for level, locs in salary_table.items():
        mow = locs.get("Moscow", {}).get("median", "-")
        reg = locs.get("Regions", {}).get("median", "-")
        rem = locs.get("Remote_USD", {}).get("median", "-")
        rows.append(f"| {level} | {mow}k | {reg}k | ${rem} |")

    return "\n".join(rows)


def _render_learning_path(path: dict) -> str:
    sections = ["## Индивидуальный план развития"]
    for phase, info in path.items():
        sections.append(f"### Этап: {phase}")
        sections.append(f"**Контрольная точка (Milestone):** {info.get('milestone')}\n")

        sections.append("**Темы для изучения:**")
        for topic in info.get("topics", []):
            sections.append(f"- {topic}")

        sections.append("\n**Рекомендуемые ресурсы:**")
        for res in info.get("resources", []):
            sections.append(f"- {res}")
    return "\n".join(sections)


def _render_gap_analysis(gap: dict) -> str:
    return (
            f"## Анализ квалификационных разрывов\n"
            f"### Краткосрочные цели (Quick Wins):\n" +
            "\n".join([f"- {i}" for i in gap.get("quick_wins", [])]) +
            f"\n\n### Долгосрочные цели:\n" +
            "\n".join([f"- {i}" for i in gap.get("long_term", [])])
    )


def _render_portfolio(project: dict) -> str:
    skills = ", ".join(project.get("skills_demonstrated", []))
    return (
        f"## Проект для практического подтверждения навыков\n"
        f"### Наименование: {project.get('name')}\n"
        f"**Описание:** {project.get('description')}\n\n"
        f"**Применяемые технологии:** {skills}"
    )


def _render_audit(data: dict) -> str:
    # Пытаемся достать данные напрямую или из вложенного объекта верификации
    v_data = data.get("verification", data)
    score = v_data.get("quality_score", 0)
    warnings = v_data.get("warnings", [])

    status = "ACCEPTABLE" if score >= 70 else "REVISION REQUIRED"

    audit_md = [
        "---\n## Технический аудит отчета",
        f"**Статус валидации:** {status} ({score}/100)",
        f"**Заключение аудитора:** {v_data.get('rationale_quality_score', 'N/A')}"
    ]

    if warnings:
        audit_md.append("\n**Выявленные несоответствия:**")
        for w in warnings:
            audit_md.append(f"- ПРЕДУПРЕЖДЕНИЕ: {w}")

    return "\n".join(audit_md)
