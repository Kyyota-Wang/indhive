from __future__ import annotations

from typing import Any

from .utils import get_path


FIELD_MAPPINGS: list[dict[str, Any]] = [
    {
        "field_id": "submission_type",
        "label": "Submission Type",
        "canonical_path": "submission.submission_type",
        "required": True,
    },
    {
        "field_id": "submission_date",
        "label": "Submission Date",
        "canonical_path": "submission.submission_date",
        "required": True,
    },
    {
        "field_id": "serial_number",
        "label": "Serial Number",
        "canonical_path": "submission.serial_number",
        "required": False,
    },
    {
        "field_id": "ind_number",
        "label": "IND Number",
        "canonical_path": "submission.ind_number",
        "required": False,
    },
    {
        "field_id": "sponsor_name",
        "label": "Sponsor Name",
        "canonical_path": "sponsor.legal_name",
        "required": True,
    },
    {
        "field_id": "sponsor_address_line_1",
        "label": "Sponsor Address Line 1",
        "canonical_path": "sponsor.address_line_1",
        "required": True,
    },
    {
        "field_id": "sponsor_address_line_2",
        "label": "Sponsor Address Line 2",
        "canonical_path": "sponsor.address_line_2",
        "required": False,
    },
    {
        "field_id": "sponsor_city",
        "label": "Sponsor City",
        "canonical_path": "sponsor.city",
        "required": True,
    },
    {
        "field_id": "sponsor_state",
        "label": "Sponsor State",
        "canonical_path": "sponsor.state",
        "required": True,
    },
    {
        "field_id": "sponsor_postal_code",
        "label": "Sponsor Postal Code",
        "canonical_path": "sponsor.postal_code",
        "required": True,
    },
    {
        "field_id": "sponsor_country",
        "label": "Sponsor Country",
        "canonical_path": "sponsor.country",
        "required": True,
    },
    {
        "field_id": "sponsor_contact_name",
        "label": "Sponsor Contact Name",
        "canonical_path": "sponsor.contact_name",
        "required": True,
    },
    {
        "field_id": "sponsor_contact_title",
        "label": "Sponsor Contact Title",
        "canonical_path": "sponsor.contact_title",
        "required": False,
    },
    {
        "field_id": "sponsor_phone",
        "label": "Sponsor Phone",
        "canonical_path": "sponsor.phone",
        "required": True,
    },
    {
        "field_id": "sponsor_email",
        "label": "Sponsor Email",
        "canonical_path": "sponsor.email",
        "required": True,
    },
    {
        "field_id": "investigational_product",
        "label": "Investigational Product",
        "canonical_path": "product.code_name",
        "required": True,
    },
    {
        "field_id": "generic_name",
        "label": "Generic Name",
        "canonical_path": "product.generic_name",
        "required": False,
    },
    {
        "field_id": "dosage_form",
        "label": "Dosage Form",
        "canonical_path": "product.dosage_form",
        "required": False,
    },
    {
        "field_id": "route",
        "label": "Route of Administration",
        "canonical_path": "product.route",
        "required": False,
    },
    {
        "field_id": "indication",
        "label": "Indication",
        "canonical_path": "product.indication",
        "required": False,
    },
    {
        "field_id": "study_phase",
        "label": "Study Phase",
        "canonical_path": "protocol.phase",
        "required": True,
    },
    {
        "field_id": "protocol_number",
        "label": "Protocol Number",
        "canonical_path": "protocol.protocol_number",
        "required": True,
    },
    {
        "field_id": "protocol_title",
        "label": "Protocol Title",
        "canonical_path": "protocol.title",
        "required": False,
    },
    {
        "field_id": "protocol_version",
        "label": "Protocol Version",
        "canonical_path": "protocol.version",
        "required": False,
    },
    {
        "field_id": "protocol_date",
        "label": "Protocol Date",
        "canonical_path": "protocol.protocol_date",
        "required": False,
    },
    {
        "field_id": "investigator_name",
        "label": "Principal Investigator",
        "canonical_path": "investigator.name",
        "required": False,
    },
    {
        "field_id": "investigator_institution",
        "label": "Investigator Institution",
        "canonical_path": "investigator.institution",
        "required": False,
    },
]


# Box numbers as printed on Form FDA 1571. Fields that carry no box number are
# reference-only context we keep alongside the form (for example investigator
# details, which belong on Form FDA 1572, not 1571).
BOX_NUMBERS: dict[str, str] = {
    "sponsor_name": "1",
    "submission_date": "2",
    "sponsor_address_line_1": "3",
    "sponsor_address_line_2": "3",
    "sponsor_city": "3",
    "sponsor_state": "3",
    "sponsor_postal_code": "3",
    "sponsor_country": "3",
    "sponsor_phone": "4",
    "investigational_product": "5",
    "generic_name": "5",
    "ind_number": "6",
    "indication": "7",
    "study_phase": "8",
    "serial_number": "10",
    "submission_type": "11",
    "sponsor_contact_name": "14",
    "sponsor_contact_title": "14",
}

BOX_LABELS: dict[str, str] = {
    "1": "Name of sponsor",
    "2": "Date of submission",
    "3": "Address",
    "4": "Telephone number",
    "5": "Name(s) of drug",
    "6": "IND number",
    "7": "Indication(s)",
    "8": "Phase(s) of clinical investigation",
    "9": "Numbers of referenced applications",
    "10": "Serial number",
    "11": "This submission contains",
    "12": "Contents of application",
    "14": "Person responsible for monitoring the investigations",
}

# Fields the pipeline carries because downstream documents need them, but which do
# not appear anywhere on Form FDA 1571. Showing them under a box number would
# misrepresent the form, so they are grouped separately and marked as context.
CONTEXT_FIELDS: set[str] = {
    "dosage_form",
    "route",
    "protocol_number",
    "protocol_title",
    "protocol_version",
    "protocol_date",
    "sponsor_email",
    "investigator_name",
    "investigator_institution",
}

# Box 12 on the real form is a checklist, not free text. Each item is ticked from
# what this package actually contains, which makes the box a second gap analysis.
CONTENTS_ITEMS: list[dict[str, Any]] = [
    {"number": "1", "label": "Form FDA 1571", "source": "always"},
    {"number": "2", "label": "Table of contents", "source": "always"},
    {
        "number": "3",
        "label": "Introductory statement and general investigational plan",
        "source": "investigational_plan",
    },
    {"number": "5", "label": "Investigator's brochure", "source": "never"},
    {"number": "6", "label": "Protocol(s)", "source": "never"},
    {"number": "7", "label": "Chemistry, manufacturing and control data", "source": "never"},
    {"number": "8", "label": "Pharmacology and toxicology data", "source": "never"},
    {"number": "9", "label": "Previous human experience", "source": "never"},
    {"number": "10", "label": "Additional information", "source": "never"},
]

NO_GENERATOR = "No generator for this content class in this POC."


def map_to_form_1571(canonical: dict[str, Any]) -> dict[str, Any]:
    conflicts_by_field = {item["field"]: item for item in canonical.get("conflicts", [])}
    fields = []

    for mapping in FIELD_MAPPINGS:
        canonical_path = mapping["canonical_path"]
        value = get_path(canonical, canonical_path)
        provenance = canonical.get("provenance", {}).get(canonical_path)

        if canonical_path in conflicts_by_field:
            status = "CONFLICT"
            message = conflicts_by_field[canonical_path]["message"]
            display_value = None
        elif _has_value(value):
            status = "PASS"
            message = None
            display_value = value
        else:
            status = "MISSING" if mapping["required"] else "WARNING"
            message = "Required value is unavailable." if mapping["required"] else "Optional value is unavailable."
            display_value = None

        field_id = mapping["field_id"]
        box = BOX_NUMBERS.get(field_id)
        fields.append(
            {
                "field_id": field_id,
                "kind": "value",
                "box": box,
                "box_label": BOX_LABELS.get(box) if box else None,
                "context": field_id in CONTEXT_FIELDS,
                "label": mapping["label"],
                "canonical_path": canonical_path,
                "status": status,
                "value": display_value,
                "message": message,
                "provenance": provenance,
            }
        )

    fields.append(_referenced_applications())
    fields.append(_contents_of_application(canonical))

    return {
        "case_id": canonical["case_id"],
        "form_name": "FDA Form 1571 - POC Field View",
        "fields": fields,
    }


def _referenced_applications() -> dict[str, Any]:
    """Box 9. No source record carries a referenced application, so the answer is None."""
    return {
        "field_id": "referenced_applications",
        "kind": "value",
        "box": "9",
        "box_label": BOX_LABELS["9"],
        "context": False,
        "label": "Numbers of all INDs, NDAs, DMFs and BLAs referred to in this application",
        "canonical_path": None,
        "status": "PASS",
        "value": "None",
        "message": "Derived: no source record supplies a referenced application number.",
        "provenance": None,
    }


def _contents_of_application(canonical: dict[str, Any]) -> dict[str, Any]:
    """Box 12, ticked from what the generated package actually contains."""
    from .gip import ELEMENTS

    plan_complete = all(_has_value(get_path(canonical, path)) for _, path, _ in ELEMENTS)

    items = []
    for item in CONTENTS_ITEMS:
        if item["source"] == "always":
            checked, note = True, "Generated by this POC."
        elif item["source"] == "investigational_plan":
            checked = plan_complete
            note = (
                "Section 1.20 is complete."
                if plan_complete
                else "Section 1.20 is absent or incomplete for this case."
            )
        else:
            checked, note = False, NO_GENERATOR
        items.append({"number": item["number"], "label": item["label"], "checked": checked, "note": note})

    ticked = sum(1 for i in items if i["checked"])
    return {
        "field_id": "contents_of_application",
        "kind": "checklist",
        "box": "12",
        "box_label": BOX_LABELS["12"],
        "context": False,
        "label": "This application contains the following items",
        "canonical_path": None,
        "status": "PASS" if ticked else "MISSING",
        "value": f"{ticked} of {len(items)} items present",
        "items": items,
        "message": "Item 4 is reserved on the current form and is not shown.",
        "provenance": None,
    }


def render_form_1571_markdown(form_view: dict[str, Any]) -> str:
    lines = [
        "# FDA Form 1571 - POC Field View",
        "",
        "This is a demonstration field view only. It is not an official FDA PDF and is not submission-ready.",
        "",
    ]
    boxed = [f for f in form_view["fields"] if f.get("box")]
    context = [f for f in form_view["fields"] if not f.get("box")]

    boxed.sort(key=lambda f: int(f["box"]))

    for field in boxed:
        lines.extend(_render_field(field))

    if context:
        lines.extend(
            [
                "# Supporting data - not a Form 1571 box",
                "",
                "These values are carried by the pipeline for other Module 1 documents. They do",
                "not appear on Form FDA 1571.",
                "",
            ]
        )
        for field in context:
            lines.extend(_render_field(field))

    return "\n".join(lines)


def _render_field(field: dict[str, Any]) -> list[str]:
    heading = f"Box {field['box']} - {field['label']}" if field.get("box") else field["label"]
    lines = [f"## {heading}", f"- Status: {field['status']}"]

    if field.get("kind") == "checklist":
        lines.append(f"- {field['value']}")
        for item in field["items"]:
            mark = "[x]" if item["checked"] else "[ ]"
            lines.append(f"  - {mark} {item['number']}. {item['label']} - {item['note']}")
    else:
        lines.append(f"- Value: {field['value'] if field['value'] not in (None, '') else '-'}")

    if field.get("message"):
        lines.append(f"- Note: {field['message']}")
    if field.get("provenance"):
        source_labels = [
            f"{source['record_id']} -> {source['field']}"
            for source in field["provenance"].get("sources", [])
        ]
        if source_labels:
            lines.append(f"- Source: {'; '.join(source_labels)}")
    lines.append("")
    return lines


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True

