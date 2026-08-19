"""Turn the Python POC's generated output into a single JSON bundle for the Worker.

The Python pipeline stays the source of truth for all deterministic mapping.
This script only collects what it already produced; it computes nothing new.

    python build/bundle_cases.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

V1_DIR = Path(__file__).resolve().parent.parent
POC_DIR = V1_DIR.parent / "Data" / "POC data"
SOURCE_CASES = POC_DIR / "data" / "source_cases"
GENERATED = POC_DIR / "outputs" / "generated"
OUT_FILE = V1_DIR / "src" / "cases.json"

# Only these paths are offered to the cover-letter model. Anything outside this
# list is not a fact the letter is allowed to state.
COVER_FACT_PATHS = [
    "submission.submission_date", "submission.submission_type", "submission.serial_number",
    "sponsor.legal_name", "sponsor.address_line_1", "sponsor.address_line_2",
    "sponsor.city", "sponsor.state", "sponsor.postal_code", "sponsor.country",
    "sponsor.contact_name", "sponsor.contact_title", "sponsor.phone", "sponsor.email",
    "product.code_name", "product.generic_name", "product.dosage_form",
    "product.route", "product.indication",
    "protocol.protocol_number", "protocol.title", "protocol.phase",
    "protocol.version", "protocol.protocol_date",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def get_path(data, dotted: str):
    current = data
    for part in dotted.split("."):
        current = current.get(part) if isinstance(current, dict) else None
    return current


def has_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def cover_facts(canonical) -> list[dict]:
    conflicted = {c["field"] for c in canonical.get("conflicts", [])}
    facts = []
    for path in COVER_FACT_PATHS:
        if path in conflicted:
            continue
        value = get_path(canonical, path)
        if not has_value(value):
            continue
        facts.append({"path": path, "value": value})
    return facts


def build_case(case_id: str) -> dict:
    case_out = GENERATED / case_id
    source = read_json(SOURCE_CASES / f"{case_id}.json")
    canonical = read_json(case_out / "canonical_ind.json")
    validation = read_json(case_out / "validation.json")

    return {
        "case_id": case_id,
        "case_label": source["case_label"],
        "scenario_type": source["scenario_type"],
        "notes": source.get("notes", []),
        "source_records": source["source_records"],
        "canonical": canonical,
        "form_1571": read_json(case_out / "form_1571.json"),
        "toc": read_json(case_out / "toc.json"),
        "investigational_plan": read_json(case_out / "investigational_plan.json"),
        "validation": validation,
        "cover_letter_facts": cover_facts(canonical),
    }


def main() -> int:
    if not GENERATED.is_dir():
        print(f"error: no generated output at {GENERATED}", file=sys.stderr)
        print("run `python run_poc.py --all` in the POC folder first", file=sys.stderr)
        return 1

    case_ids = sorted(p.stem for p in SOURCE_CASES.glob("IND*.json"))
    cases = {}
    skipped = []
    for case_id in case_ids:
        if not (GENERATED / case_id / "canonical_ind.json").exists():
            skipped.append(case_id)
            continue
        cases[case_id] = build_case(case_id)

    bundle = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "IND Module 1 POC deterministic pipeline",
        "case_order": list(cases.keys()),
        "cases": cases,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    size_kb = OUT_FILE.stat().st_size / 1024
    print(f"wrote {OUT_FILE.relative_to(V1_DIR)}  ({len(cases)} cases, {size_kb:.0f} KB)")
    if skipped:
        print(f"skipped (no generated output): {', '.join(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
