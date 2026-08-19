from __future__ import annotations

from collections import Counter
from typing import Any

from .utils import get_path


REQUIRED_FIELDS = [
    ("sponsor.legal_name", "Sponsor legal name exists"),
    ("product.code_name", "Product name/code exists"),
    ("protocol.protocol_number", "Protocol number exists"),
    ("protocol.phase", "Protocol phase exists"),
    ("submission.submission_type", "Submission type exists"),
    ("submission.submission_date", "Submission date exists"),
]

OPTIONAL_BUT_USEFUL_FIELDS = [
    ("sponsor.contact_title", "Sponsor contact title is available"),
    ("protocol.protocol_date", "Protocol date is available"),
    ("investigator.email", "Investigator email is available"),
]

CROSS_DOCUMENT_FIELDS = [
    ("sponsor.legal_name", "sponsor_name", "Cover Letter and 1571 use the same sponsor name"),
    ("product.code_name", "investigational_product", "Cover Letter and 1571 use the same product name"),
    ("protocol.protocol_number", "protocol_number", "Cover Letter and 1571 use the same protocol number"),
]


def validate_package(
    canonical: dict[str, Any],
    form_1571: dict[str, Any],
    cover_letter: dict[str, Any],
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    conflict_fields = {conflict["field"] for conflict in canonical.get("conflicts", [])}

    for field_path, message in REQUIRED_FIELDS:
        if field_path in conflict_fields:
            issues.append(
                {
                    "status": "CONFLICT",
                    "check_id": f"required_conflict:{field_path}",
                    "field": field_path,
                    "message": f"{message}, but source records conflict; human review required.",
                }
            )
        elif _has_value(get_path(canonical, field_path)):
            issues.append(
                {
                    "status": "PASS",
                    "check_id": f"required_present:{field_path}",
                    "field": field_path,
                    "message": message,
                }
            )
        else:
            issues.append(
                {
                    "status": "MISSING",
                    "check_id": f"required_missing:{field_path}",
                    "field": field_path,
                    "message": f"{message}, but no value was found.",
                }
            )

    for field_path, message in OPTIONAL_BUT_USEFUL_FIELDS:
        if field_path in conflict_fields:
            issues.append(
                {
                    "status": "CONFLICT",
                    "check_id": f"optional_conflict:{field_path}",
                    "field": field_path,
                    "message": f"{message}, but source records conflict; human review required.",
                }
            )
        elif _has_value(get_path(canonical, field_path)):
            issues.append(
                {
                    "status": "PASS",
                    "check_id": f"optional_present:{field_path}",
                    "field": field_path,
                    "message": message,
                }
            )
        else:
            issues.append(
                {
                    "status": "WARNING",
                    "check_id": f"optional_missing:{field_path}",
                    "field": field_path,
                    "message": f"{message}, but it is unavailable in the selected case.",
                }
            )

    for conflict in canonical.get("conflicts", []):
        issues.append(
            {
                "status": "CONFLICT",
                "check_id": f"source_conflict:{conflict['field']}",
                "field": conflict["field"],
                "message": conflict["message"],
            }
        )

    form_fields = {field["field_id"]: field for field in form_1571["fields"]}
    cover_facts = {fact["path"]: fact["value"] for fact in cover_letter.get("facts_used", [])}

    for canonical_path, form_field_id, message in CROSS_DOCUMENT_FIELDS:
        canonical_value = get_path(canonical, canonical_path)
        form_field = form_fields.get(form_field_id, {})
        form_value = form_field.get("value")
        cover_value = cover_facts.get(canonical_path)

        if canonical_path in conflict_fields:
            issues.append(
                {
                    "status": "CONFLICT",
                    "check_id": f"cross_doc_conflict:{canonical_path}",
                    "field": canonical_path,
                    "message": f"{message}, but the canonical field is conflicted.",
                }
            )
        elif not _has_value(canonical_value):
            issues.append(
                {
                    "status": "MISSING",
                    "check_id": f"cross_doc_missing:{canonical_path}",
                    "field": canonical_path,
                    "message": f"{message}, but the canonical value is missing.",
                }
            )
        elif canonical_value == form_value and canonical_value == cover_value:
            issues.append(
                {
                    "status": "PASS",
                    "check_id": f"cross_doc_match:{canonical_path}",
                    "field": canonical_path,
                    "message": message,
                }
            )
        else:
            issues.append(
                {
                    "status": "WARNING",
                    "check_id": f"cross_doc_mismatch:{canonical_path}",
                    "field": canonical_path,
                    "message": f"{message}, but generated outputs did not expose identical values.",
                }
            )

    issues.extend(_validate_cover_letter_facts(canonical, cover_letter, conflict_fields))
    summary = Counter(issue["status"] for issue in issues)

    return {
        "case_id": canonical["case_id"],
        "summary": {status: int(summary.get(status, 0)) for status in ["PASS", "WARNING", "MISSING", "CONFLICT"]},
        "issues": issues,
    }


def render_validation_markdown(validation: dict[str, Any]) -> str:
    lines = [
        "# Validation Summary",
        "",
        f"Case: {validation['case_id']}",
        "",
    ]
    for status in ["PASS", "WARNING", "MISSING", "CONFLICT"]:
        lines.append(f"## {status}")
        matching = [issue for issue in validation["issues"] if issue["status"] == status]
        if not matching:
            lines.append("- None")
        else:
            for issue in matching:
                field = f" ({issue['field']})" if issue.get("field") else ""
                lines.append(f"- {issue['message']}{field}")
        lines.append("")
    return "\n".join(lines)


def _validate_cover_letter_facts(
    canonical: dict[str, Any],
    cover_letter: dict[str, Any],
    conflict_fields: set[str],
) -> list[dict[str, Any]]:
    issues = []
    for fact in cover_letter.get("facts_used", []):
        path = fact["path"]
        value = fact["value"]
        canonical_value = get_path(canonical, path)
        if path in conflict_fields:
            issues.append(
                {
                    "status": "CONFLICT",
                    "check_id": f"cover_fact_conflicted:{path}",
                    "field": path,
                    "message": "Cover Letter fact manifest includes a conflicted field.",
                }
            )
        elif value == canonical_value:
            issues.append(
                {
                    "status": "PASS",
                    "check_id": f"cover_fact_supported:{path}",
                    "field": path,
                    "message": "Cover Letter fact is supported by canonical data.",
                }
            )
        else:
            issues.append(
                {
                    "status": "WARNING",
                    "check_id": f"cover_fact_unsupported:{path}",
                    "field": path,
                    "message": "Cover Letter fact manifest contains a value not supported by canonical data.",
                }
            )
    return issues


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True

