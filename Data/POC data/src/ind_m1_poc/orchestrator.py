from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .cover_letter import generate_cover_letter
from .form_1571 import map_to_form_1571, render_form_1571_markdown
from .gip import generate_investigational_plan
from .loader import load_source_case, normalize_source_case
from .paths import OUTPUTS_DIR, SOURCE_CASES_DIR
from .toc import generate_toc
from .validation import render_validation_markdown, validate_package


def generate_module1_package(
    case_id: str,
    source_dir: Path = SOURCE_CASES_DIR,
    output_dir: Path = OUTPUTS_DIR,
    use_llm: bool = True,
) -> dict[str, Any]:
    source_case = load_source_case(case_id, source_dir=source_dir)
    canonical = normalize_source_case(source_case)
    form_1571 = map_to_form_1571(canonical)
    cover_letter = generate_cover_letter(canonical, use_llm=use_llm)
    plan = generate_investigational_plan(canonical)
    toc = generate_toc(canonical)
    validation = validate_package(canonical, form_1571, cover_letter)

    package = {
        "case_id": case_id,
        "case_label": canonical["case_label"],
        "canonical": canonical,
        "cover_letter": cover_letter,
        "form_1571": form_1571,
        "plan": plan,
        "toc": toc,
        "validation": validation,
    }
    persist_package(package, output_dir=output_dir)
    return package


def persist_package(package: dict[str, Any], output_dir: Path = OUTPUTS_DIR) -> Path:
    case_dir = output_dir / package["case_id"]
    case_dir.mkdir(parents=True, exist_ok=True)

    _write_json(case_dir / "canonical_ind.json", package["canonical"])
    _write_json(case_dir / "cover_letter.json", package["cover_letter"])
    _write_json(case_dir / "form_1571.json", package["form_1571"])
    _write_json(case_dir / "toc.json", package["toc"])
    _write_json(case_dir / "investigational_plan.json", package["plan"])
    _write_json(case_dir / "validation.json", package["validation"])

    (case_dir / "cover_letter.md").write_text(package["cover_letter"]["text"], encoding="utf-8")
    (case_dir / "form_1571.md").write_text(render_form_1571_markdown(package["form_1571"]), encoding="utf-8")
    (case_dir / "module1_toc.md").write_text(package["toc"]["markdown"], encoding="utf-8")
    (case_dir / "investigational_plan.md").write_text(package["plan"]["markdown"], encoding="utf-8")
    (case_dir / "validation.md").write_text(render_validation_markdown(package["validation"]), encoding="utf-8")
    _write_json(
        case_dir / "package_summary.json",
        {
            "case_id": package["case_id"],
            "case_label": package["case_label"],
            "artifacts": [
                "canonical_ind.json",
                "cover_letter.md",
                "cover_letter.json",
                "form_1571.md",
                "form_1571.json",
                "module1_toc.md",
                "investigational_plan.md",
                "investigational_plan.json",
                "toc.json",
                "validation.md",
                "validation.json",
            ],
            "validation_summary": package["validation"]["summary"],
            "cover_letter_generation_method": package["cover_letter"]["generation_method"],
        },
    )
    return case_dir


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

