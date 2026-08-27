"""Module 1.20 - General Investigational Plan.

The six required elements come from 21 CFR 312.23(a)(3)(iv). The per-study entry
template (objectives, design, sample size, population, parameters, status)
follows the convention used in the publicly released IND 36,357 file, which lays
its planned studies out in exactly that shape.

Like every other generator here, this one refuses to fill a gap: an element with
no supporting data is reported MISSING rather than written around.
"""
from __future__ import annotations

from typing import Any

from .utils import get_path


# (regulatory element, canonical path, heading)
ELEMENTS: list[tuple[str, str, str]] = [
    ("rationale", "plan.rationale", "Rationale for the drug and the research"),
    ("indication", "product.indication", "Indication to be studied"),
    ("general_approach", "plan.general_approach", "General approach to evaluating the drug"),
    ("first_year_scope", "plan.first_year_scope", "Kinds of clinical trials planned for the first year"),
    ("estimated_enrollment", "plan.estimated_enrollment", "Estimated number of participants"),
    ("anticipated_risks", "plan.anticipated_risks", "Anticipated risks of particular severity or seriousness"),
]

STUDY_FIELDS: list[tuple[str, str]] = [
    ("objectives", "Objectives"),
    ("design", "Study design"),
    ("sample_size", "Planned sample size"),
    ("population", "Study population"),
    ("parameters", "Study parameters"),
    ("status", "Status"),
]


def _has(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def generate_investigational_plan(canonical: dict[str, Any]) -> dict[str, Any]:
    conflicted = {c["field"] for c in canonical.get("conflicts", [])}

    elements = []
    for element_id, path, heading in ELEMENTS:
        value = get_path(canonical, path)
        if path in conflicted:
            status = "CONFLICT"
            value = None
        elif _has(value):
            status = "PRESENT"
        else:
            status = "MISSING"
        elements.append(
            {
                "element_id": element_id,
                "heading": heading,
                "canonical_path": path,
                "status": status,
                "value": value,
            }
        )

    studies = canonical.get("planned_studies", [])
    present = sum(1 for e in elements if e["status"] == "PRESENT")

    supplied = present > 0
    return {
        "case_id": canonical["case_id"],
        "document_name": "1.20 General Investigational Plan - POC Draft",
        "supplied": supplied,
        "summary": {
            "elements_total": len(elements),
            "elements_present": present,
            "elements_missing": sum(1 for e in elements if e["status"] == "MISSING"),
            "studies": len(studies),
        },
        "elements": elements,
        "planned_studies": studies,
        "note": (
            "Required elements follow 21 CFR 312.23(a)(3)(iv). This is a POC draft assembled from "
            "synthetic case data and is not a submission-ready document."
        ),
        "markdown": render_plan_markdown(canonical["case_id"], elements, studies, supplied),
    }


def render_plan_markdown(
    case_id: str,
    elements: list[dict[str, Any]],
    studies: list[dict[str, Any]],
    supplied: bool,
) -> str:
    lines = [
        "# 1.20 General Investigational Plan - POC Draft",
        "",
        f"Case: {case_id}",
        "",
    ]

    if not supplied:
        lines.extend(
            [
                "No investigational plan data was supplied for this case.",
                "",
                "This section is required for an Initial IND under 21 CFR 312.23(a)(3)(iv).",
                "",
            ]
        )
        return "\n".join(lines)

    for element in elements:
        lines.append(f"## {element['heading']}")
        if element["status"] == "PRESENT":
            lines.append(str(element["value"]))
        elif element["status"] == "CONFLICT":
            lines.append("_Source records conflict on this element; human review required._")
        else:
            lines.append("_Not supplied._")
        lines.append("")

    if studies:
        lines.extend(["## Studies planned for the first year", ""])
        for index, study in enumerate(studies, start=1):
            title = study.get("title") or study.get("study_id") or f"Study {index}"
            lines.append(f"### {index}. {title}")
            for key, heading in STUDY_FIELDS:
                value = study.get(key)
                if _has(value):
                    lines.append(f"- **{heading}:** {value}")
            lines.append("")

    lines.append(
        "_Required elements follow 21 CFR 312.23(a)(3)(iv). POC draft from synthetic data; not submission-ready._"
    )
    return "\n".join(lines)
