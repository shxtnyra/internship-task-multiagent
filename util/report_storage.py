import json
from datetime import datetime
from pathlib import Path
from typing import Union, Dict, Any

from util.formatters import create_md_report


def save_json_report(report: Dict[str, Any], out: str):
    """Сохраняет отчет в формате JSON"""
    output_path = Path(out)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / "report.json"

    # Добавляем метаданные в копию
    report_to_save = report.copy()
    report_to_save["metadata"] = datetime.now().isoformat()

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(report_to_save, f, ensure_ascii=False, indent=4)

    return file_path

def save_md_report(report: Dict[str, Any], out: str):
    """Сохраняет отчет в формате MD"""
    output_path = Path(out)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / "report.md"

    # Добавляем метаданные в копию
    report_to_save = report.copy()
    report_to_save["generated_at"] = datetime.now().isoformat()

    md_report = create_md_report(report_to_save)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    return file_path