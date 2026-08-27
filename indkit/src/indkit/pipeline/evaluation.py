from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .loader import load_canonical_case
from .paths import GOLDEN_TRUTH_DIR


def evaluate_golden_case(case_id: str, golden_dir: Path = GOLDEN_TRUTH_DIR) -> dict[str, Any]:
    expected_path = golden_dir / f"{case_id}_expected.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    canonical = load_canonical_case(case_id)

    canonical_checks = []
    for field_path, expected_value in expected.get("expected_canonical", {}).items():
        actual = _get_path(canonical, field_path)
        canonical_checks.append(
            {
                "field": field_path,
                "expected": expected_value,
                "actual": actual,
                "passed": actual == expected_value,
            }
        )

    actual_conflicts = sorted(conflict["field"] for conflict in canonical.get("conflicts", []))
    expected_conflicts = sorted(expected.get("expected_validation", {}).get("conflict_fields", []))

    return {
        "case_id": case_id,
        "canonical_checks": canonical_checks,
        "conflict_check": {
            "expected": expected_conflicts,
            "actual": actual_conflicts,
            "passed": actual_conflicts == expected_conflicts,
        },
        "passed": all(check["passed"] for check in canonical_checks) and actual_conflicts == expected_conflicts,
    }


def _get_path(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        current = current.get(part) if isinstance(current, dict) else None
    return current

