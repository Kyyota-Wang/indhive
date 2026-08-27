from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .cover_letter import generate_cover_letter
from .form_1571 import map_to_form_1571, render_form_1571_markdown
from .form_1571_diff import diff_form_1571, render_form_diff_markdown
from .gaps import (
    build_gap_register,
    crosswalk,
    render_gap_crosswalk_markdown,
    render_gap_register_markdown,
)
from .gip import generate_investigational_plan
from .loader import load_source_case, normalize_source_case
from .partner_review import render_partner_review_markdown, review_partner_package
from .paths import OUTPUTS_DIR, PARTNER_REFERENCE_DIR, SOURCE_CASES_DIR
from .toc import generate_toc
from .validation import render_validation_markdown, validate_package


def load_partner_reference(case_id: str, reference_dir: Path = PARTNER_REFERENCE_DIR) -> dict[str, Any] | None:
    """The partner's own answers for this case, where a case has them.

    Only the partner-supplied case does. Everything downstream treats its absence as
    the normal state, so the ten fictional cases run exactly as before.
    """
    path = reference_dir / f"{case_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


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
    gap_register = build_gap_register(canonical, form_1571, toc)

    package = {
        "case_id": case_id,
        "case_label": canonical["case_label"],
        "canonical": canonical,
        "cover_letter": cover_letter,
        "form_1571": form_1571,
        "plan": plan,
        "toc": toc,
        "validation": validation,
        "gap_register": gap_register,
    }

    # A partner-supplied case can be checked against the partner's own answers. The
    # comparison runs after generation and never feeds back into it: the pipeline
    # must reach its conclusions from the input alone or the comparison proves nothing.
    reference = load_partner_reference(case_id)
    if reference:
        form_diff = diff_form_1571(form_1571, reference, canonical)
        package["form_1571_diff"] = form_diff
        package["gap_crosswalk"] = crosswalk(gap_register, reference, form_diff)
        package["partner_review"] = review_partner_package(reference)
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
    _write_json(case_dir / "gap_register.json", package["gap_register"])

    (case_dir / "cover_letter.md").write_text(package["cover_letter"]["text"], encoding="utf-8")
    (case_dir / "form_1571.md").write_text(render_form_1571_markdown(package["form_1571"]), encoding="utf-8")
    (case_dir / "module1_toc.md").write_text(package["toc"]["markdown"], encoding="utf-8")
    (case_dir / "investigational_plan.md").write_text(package["plan"]["markdown"], encoding="utf-8")
    (case_dir / "validation.md").write_text(render_validation_markdown(package["validation"]), encoding="utf-8")
    (case_dir / "gap_register.md").write_text(
        render_gap_register_markdown(package["gap_register"]), encoding="utf-8"
    )

    extras: list[str] = []
    if "form_1571_diff" in package:
        _write_json(case_dir / "form_1571_diff.json", package["form_1571_diff"])
        (case_dir / "form_1571_diff.md").write_text(
            render_form_diff_markdown(package["form_1571_diff"]), encoding="utf-8"
        )
        extras += ["form_1571_diff.json", "form_1571_diff.md"]
    if "gap_crosswalk" in package:
        _write_json(case_dir / "gap_crosswalk.json", package["gap_crosswalk"])
        (case_dir / "gap_crosswalk.md").write_text(
            render_gap_crosswalk_markdown(package["gap_crosswalk"]), encoding="utf-8"
        )
        extras += ["gap_crosswalk.json", "gap_crosswalk.md"]
    if "partner_review" in package:
        _write_json(case_dir / "partner_review.json", package["partner_review"])
        (case_dir / "partner_review.md").write_text(
            render_partner_review_markdown(package["partner_review"]), encoding="utf-8"
        )
        extras += ["partner_review.json", "partner_review.md"]

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
                "gap_register.md",
                "gap_register.json",
                *extras,
            ],
            "validation_summary": package["validation"]["summary"],
            "cover_letter_generation_method": package["cover_letter"]["generation_method"],
        },
    )
    return case_dir


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

