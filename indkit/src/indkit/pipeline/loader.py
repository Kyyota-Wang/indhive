from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .paths import SOURCE_CASES_DIR
from .utils import set_path


CANONICAL_SECTIONS: dict[str, list[str]] = {
    "sponsor": [
        "legal_name",
        "address_line_1",
        "address_line_2",
        "city",
        "state",
        "postal_code",
        "country",
        "contact_name",
        "contact_title",
        "phone",
        "email",
    ],
    "product": ["code_name", "generic_name", "dosage_form", "route", "indication"],
    "protocol": ["protocol_number", "title", "phase", "version", "protocol_date"],
    "submission": ["submission_type", "submission_date", "serial_number", "ind_number"],
    "investigator": ["name", "institution", "address", "phone", "email"],
    # 21 CFR 312.23(a)(3)(iv) - the narrative half of the general investigational plan.
    "plan": [
        "rationale",
        "general_approach",
        "first_year_scope",
        "estimated_enrollment",
        "anticipated_risks",
    ],
}

CANONICAL_FIELD_PATHS = [
    f"{section}.{field}"
    for section, fields in CANONICAL_SECTIONS.items()
    for field in fields
]


def list_case_files(source_dir: Path = SOURCE_CASES_DIR) -> list[Path]:
    """Fictional cases first, in ID order, then any partner-supplied case.

    The partner cases are not a continuation of the IND001-010 series and must not
    be sorted in among them: they carry real-shaped input and are reviewed against
    the partner's own answers.
    """
    synthetic = sorted(source_dir.glob("IND*.json"))
    partner = sorted(p for p in source_dir.glob("*.json") if p not in set(synthetic))
    return synthetic + partner


def list_cases(source_dir: Path = SOURCE_CASES_DIR) -> list[dict[str, str]]:
    cases = []
    for path in list_case_files(source_dir):
        source_case = load_source_case(path)
        cases.append(
            {
                "case_id": source_case["case_id"],
                "case_label": source_case["case_label"],
                "scenario_type": source_case["scenario_type"],
                "origin": source_case.get("origin", "synthetic"),
            }
        )
    return cases


def load_source_case(case_id_or_path: str | Path, source_dir: Path = SOURCE_CASES_DIR) -> dict[str, Any]:
    path = Path(case_id_or_path)
    if not path.suffix:
        path = source_dir / f"{case_id_or_path}.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_source_case(source_case: dict[str, Any]) -> dict[str, Any]:
    values_by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for record in source_case.get("source_records", []):
        for field_path, value in record.get("fields", {}).items():
            if field_path not in CANONICAL_FIELD_PATHS:
                continue
            values_by_path[field_path].append(
                {
                    "value": value,
                    "record_id": record["record_id"],
                    "record_type": record["record_type"],
                    "source_type": record["source_type"],
                    "source_field": field_path,
                }
            )

    canonical: dict[str, Any] = {
        "case_id": source_case["case_id"],
        "case_label": source_case["case_label"],
        "scenario_type": source_case["scenario_type"],
        "origin": source_case.get("origin", "synthetic"),
        "sponsor": {},
        "product": {},
        "protocol": {},
        "submission": {},
        "investigator": {},
        "plan": {},
        "planned_studies": [],
        "provenance": {},
        "conflicts": [],
    }

    for section, fields in CANONICAL_SECTIONS.items():
        for field in fields:
            set_path(canonical, f"{section}.{field}", None)

    # Study entries are structured records rather than single values, so they are
    # carried through as supplied. Conflict detection stays on the scalar fields.
    for record in source_case.get("source_records", []):
        for study in record.get("planned_studies", []):
            canonical["planned_studies"].append({**study, "source_record": record["record_id"]})

    for field_path in CANONICAL_FIELD_PATHS:
        observations = values_by_path.get(field_path, [])
        non_empty = [obs for obs in observations if _has_value(obs["value"])]
        distinct_values = _distinct_values(non_empty)

        if len(distinct_values) > 1:
            set_path(canonical, field_path, None)
            canonical["conflicts"].append(
                {
                    "field": field_path,
                    "values": [
                        {
                            "value": obs["value"],
                            "record_id": obs["record_id"],
                            "source_type": obs["source_type"],
                        }
                        for obs in non_empty
                    ],
                    "message": f"Conflicting values found for {field_path}; human review required.",
                }
            )
            canonical["provenance"][field_path] = {
                "field": field_path,
                "value": None,
                "sources": [
                    {
                        "record_id": obs["record_id"],
                        "source_type": obs["source_type"],
                        "field": obs["source_field"],
                    }
                    for obs in observations
                ],
            }
            continue

        value = distinct_values[0] if distinct_values else None
        set_path(canonical, field_path, value)
        canonical["provenance"][field_path] = {
            "field": field_path,
            "value": value,
            "sources": [
                {
                    "record_id": obs["record_id"],
                    "source_type": obs["source_type"],
                    "field": obs["source_field"],
                }
                for obs in observations
            ],
        }

    return canonical


def load_canonical_case(case_id: str, source_dir: Path = SOURCE_CASES_DIR) -> dict[str, Any]:
    return normalize_source_case(load_source_case(case_id, source_dir=source_dir))


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def _distinct_values(observations: list[dict[str, Any]]) -> list[Any]:
    distinct: list[Any] = []
    seen = set()
    for obs in observations:
        value = obs["value"]
        key = value.strip() if isinstance(value, str) else value
        if key not in seen:
            seen.add(key)
            distinct.append(value)
    return distinct

