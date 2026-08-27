from __future__ import annotations

import json
import os
from typing import Any

from .utils import get_path


COVER_FACT_PATHS = [
    "submission.submission_date",
    "submission.submission_type",
    "submission.serial_number",
    "sponsor.legal_name",
    "sponsor.address_line_1",
    "sponsor.address_line_2",
    "sponsor.city",
    "sponsor.state",
    "sponsor.postal_code",
    "sponsor.country",
    "sponsor.contact_name",
    "sponsor.contact_title",
    "sponsor.phone",
    "sponsor.email",
    "product.code_name",
    "product.generic_name",
    "product.dosage_form",
    "product.route",
    "product.indication",
    "protocol.protocol_number",
    "protocol.title",
    "protocol.phase",
    "protocol.version",
    "protocol.protocol_date",
]


def generate_cover_letter(canonical: dict[str, Any], use_llm: bool = True) -> dict[str, Any]:
    facts = _available_facts(canonical)
    warnings = []

    if use_llm:
        try:
            text, model = _generate_with_openai(canonical, facts)
            return {
                "case_id": canonical["case_id"],
                "document_name": "IND Cover Letter - POC Draft",
                "generation_method": "llm",
                "model": model,
                "text": text,
                "facts_used": facts,
                "warnings": warnings,
            }
        except Exception as exc:  # noqa: BLE001 - fallback must keep demo running.
            warnings.append(f"LLM generation unavailable; used deterministic fallback. Reason: {type(exc).__name__}: {exc}")

    return {
        "case_id": canonical["case_id"],
        "document_name": "IND Cover Letter - POC Draft",
        "generation_method": "template_fallback",
        "model": None,
        "text": _generate_with_template(canonical, facts),
        "facts_used": facts,
        "warnings": warnings,
    }


def _available_facts(canonical: dict[str, Any]) -> list[dict[str, Any]]:
    conflicted_paths = {conflict["field"] for conflict in canonical.get("conflicts", [])}
    facts = []
    for path in COVER_FACT_PATHS:
        if path in conflicted_paths:
            continue
        value = get_path(canonical, path)
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        facts.append(
            {
                "path": path,
                "value": value,
                "source": f"synthetic_case.{canonical['case_id']}.{path}",
            }
        )
    return facts


def _generate_with_openai(canonical: dict[str, Any], facts: list[dict[str, Any]]) -> tuple[str, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    from openai import OpenAI  # type: ignore

    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    client = OpenAI(api_key=api_key)
    prompt_payload = {
        "case_id": canonical["case_id"],
        "facts": facts,
        "conflicts": canonical.get("conflicts", []),
        "instructions": [
            "Use only the supplied structured facts.",
            "Never invent missing information.",
            "Do not resolve conflicting fields; omit them or state that human review is required.",
            "Clearly label the output as a POC draft.",
            "Do not claim that the package is FDA-submission-ready.",
            "Keep sponsor, product, protocol, and submission facts exactly consistent with the supplied data.",
        ],
    }
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": "You draft concise FDA IND Module 1 POC cover letters using only supplied structured facts.",
            },
            {
                "role": "user",
                "content": json.dumps(prompt_payload, indent=2),
            },
        ],
    )
    text = getattr(response, "output_text", None)
    if not text:
        raise RuntimeError("OpenAI response did not include output_text")
    return text, model


def _generate_with_template(canonical: dict[str, Any], facts: list[dict[str, Any]]) -> str:
    fact_map = {fact["path"]: fact["value"] for fact in facts}
    conflicts = canonical.get("conflicts", [])
    date = fact_map.get("submission.submission_date", "[Submission date unavailable]")
    sponsor = fact_map.get("sponsor.legal_name", "[Sponsor name pending human review]")
    submission_type = fact_map.get("submission.submission_type", "IND submission")
    product = fact_map.get("product.code_name", "[Product name unavailable]")
    protocol_number = fact_map.get("protocol.protocol_number")
    protocol_title = fact_map.get("protocol.title")
    phase = fact_map.get("protocol.phase")
    contact_name = fact_map.get("sponsor.contact_name")
    contact_title = fact_map.get("sponsor.contact_title")
    contact_phone = fact_map.get("sponsor.phone")
    contact_email = fact_map.get("sponsor.email")

    lines = [
        "# IND Cover Letter - POC Draft",
        "",
        "**POC draft for demonstration only. Not FDA-submission-ready.**",
        "",
        str(date),
        "",
        "Food and Drug Administration",
        "Center for Drug Evaluation and Research",
        "",
        f"Re: {submission_type} for {product}",
        "",
        "Dear FDA Reviewer:",
        "",
        (
            f"{sponsor} is submitting this POC draft package for {product}. "
            "This generated document is based only on the selected synthetic IND case."
        ),
    ]

    protocol_bits = []
    if protocol_number:
        protocol_bits.append(f"Protocol {protocol_number}")
    if protocol_title:
        protocol_bits.append(str(protocol_title))
    if phase:
        protocol_bits.append(str(phase))
    if protocol_bits:
        lines.extend(["", "The referenced clinical protocol information is: " + "; ".join(protocol_bits) + "."])

    lines.extend(
        [
            "",
            "The POC Module 1 package includes:",
            "- IND Cover Letter",
            "- FDA Form 1571 POC Field View",
            "- Simplified Module 1 Table of Contents",
            "- Basic validation results",
        ]
    )

    if conflicts:
        conflicted_fields = ", ".join(conflict["field"] for conflict in conflicts)
        lines.extend(
            [
                "",
                f"Fields requiring human review due to conflicting source values: {conflicted_fields}.",
            ]
        )

    contact_lines = []
    if contact_name:
        contact_lines.append(str(contact_name))
    if contact_title:
        contact_lines.append(str(contact_title))
    if contact_phone:
        contact_lines.append(str(contact_phone))
    if contact_email:
        contact_lines.append(str(contact_email))
    if contact_lines:
        lines.extend(["", "Sponsor contact:", *contact_lines])

    lines.extend(["", "Sincerely,", str(contact_name or "Sponsor Regulatory Contact")])
    return "\n".join(lines)

