"""Module 1 table of contents, modelled on the US regional eCTD M1 structure.

This is not a flat list of what the POC produced. It is the section skeleton an
Initial IND is expected to populate, with each node resolved against the case so
the reader can see what exists, what is still owed, and what does not apply.

Applicability here is a demonstration heuristic scoped to Initial INDs. It is not
regulatory advice and it does not replace the current FDA eCTD US regional
specification.

Every section that is not already satisfied carries the two things a reader needs in
order to act on it: who owns it, and what has to arrive before it can close. A gap
list without an owner is a complaint; with one it is a work item.
"""
from __future__ import annotations

from typing import Any, Callable

from .utils import get_path


REQUIRED = "required"
CONDITIONAL = "conditional"
NOT_APPLICABLE = "not_applicable"

PRESENT = "PRESENT"
ABSENT = "ABSENT"
NEEDS_DECISION = "NEEDS DECISION"
NA = "N/A"

OPEN = "OPEN"
CLOSED = "CLOSED"
NOT_TRACKED = "NOT TRACKED"


def _has(canonical: dict[str, Any], path: str) -> bool:
    value = get_path(canonical, path)
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def _forms_1571(canonical: dict[str, Any]) -> tuple[bool, str]:
    conflicts = len(canonical.get("conflicts", []))
    if conflicts:
        return True, f"Generated field view; {conflicts} field(s) unresolved pending human review."
    return True, "Generated field view."


def _forms_1572(canonical: dict[str, Any]) -> tuple[bool, str]:
    if _has(canonical, "investigator.name"):
        return False, "Investigator data is present in this case, but no Form 1572 generator exists yet."
    return False, "No investigator data and no Form 1572 generator."


def _cover_letter(canonical: dict[str, Any]) -> tuple[bool, str]:
    return True, "Drafted from the approved fact list and grounding-checked."


def _contact_info(canonical: dict[str, Any]) -> tuple[bool, str]:
    have = [p for p in ("sponsor.contact_name", "sponsor.phone", "sponsor.email") if _has(canonical, p)]
    if len(have) == 3:
        return True, "Sponsor contact name, telephone, and email are all present."
    if have:
        missing = [p.split(".")[-1] for p in ("sponsor.contact_name", "sponsor.phone", "sponsor.email") if not _has(canonical, p)]
        return False, f"Incomplete; missing {', '.join(missing)}."
    return False, "No sponsor contact details in the case."


def _investigational_plan(canonical: dict[str, Any]) -> tuple[bool, str]:
    from .gip import ELEMENTS

    present = [e for e in ELEMENTS if _has(canonical, e[1])]
    missing = [e for e in ELEMENTS if not _has(canonical, e[1])]
    studies = len(canonical.get("planned_studies", []))

    if not present:
        return False, "No investigational plan data in the case."
    if missing:
        names = ", ".join(e[0].replace("_", " ") for e in missing)
        return False, f"Drafted but incomplete; missing {names}."
    return True, f"All six required elements present; {studies} planned study/studies described."


def _never(reason: str) -> Callable[[dict[str, Any]], tuple[bool, str]]:
    def resolve(_canonical: dict[str, Any]) -> tuple[bool, str]:
        return False, reason

    return resolve


# Who owns a section and what has to arrive before it can close. Keyed by section
# number so the skeleton below stays readable. `topic` is the coarse subject the
# gap is about; it is what the partner-crosswalk matches on, and it is deliberately
# coarser than the section number so two organisations that file the same obligation
# under different labels still line up.
GAP_OWNERS: dict[str, dict[str, str]] = {
    "1.1.1": {
        "owner": "Regulatory Affairs",
        "source_needed": "Sponsor authorisation, and the IND number once FDA assigns it",
        "topic": "ind_number",
    },
    "1.1.2": {
        "owner": "Clinical Operations",
        "source_needed": "Site selection, then one signed Form FDA 1572 per investigator",
        "topic": "investigator_list",
    },
    "1.1.3": {
        "owner": "Clinical Operations",
        "source_needed": "ClinicalTrials.gov registration and the resulting NCT number",
        "topic": "nct_registration",
    },
    "1.2": {
        "owner": "Regulatory Affairs",
        "source_needed": "An approved fact list for the letter",
        "topic": "cover_letter",
    },
    "1.3.1": {
        "owner": "Regulatory Affairs",
        "source_needed": "Sponsor contact record: name, telephone and email",
        "topic": "sponsor_contact",
    },
    "1.3.4": {
        "owner": "Regulatory Affairs",
        "source_needed": "Form FDA 3454 or 3455 collected from each covered clinical investigator",
        "topic": "financial_disclosure",
    },
    "1.4.1": {
        "owner": "Regulatory Affairs",
        "source_needed": "Letter of authorisation from the DMF or application holder",
        "topic": "letter_of_authorization",
    },
    "1.4.2": {
        "owner": "Regulatory Affairs",
        "source_needed": "Right-of-reference statement from the same holder",
        "topic": "letter_of_authorization",
    },
    "1.6.1": {
        "owner": "Regulatory Affairs",
        "source_needed": "A sponsor decision on whether to request a meeting with this submission",
        "topic": "meeting",
    },
    "1.6.3": {
        "owner": "Regulatory Affairs",
        "source_needed": "Minutes or correspondence from a pre-IND meeting, where one occurred",
        "topic": "meeting",
    },
    "1.7": {
        "owner": "Regulatory Affairs",
        "source_needed": "A sponsor decision on whether to request fast track designation",
        "topic": "fast_track",
    },
    "1.9": {
        "owner": "Regulatory Affairs",
        "source_needed": "PREA waiver or deferral request with its justification",
        "topic": "pediatric",
    },
    "1.12.1": {
        "owner": "Regulatory Affairs",
        "source_needed": "Prior FDA correspondence for this programme, where any exists",
        "topic": "pre_ind_correspondence",
    },
    "1.14.4": {
        "owner": "Regulatory Labeling / CMC",
        "source_needed": "Investigational drug label text and container/carton copy",
        "topic": "labeling",
    },
    "1.20": {
        "owner": "Clinical Development",
        "source_needed": "The six elements required by 21 CFR 312.23(a)(3)(iv)",
        "topic": "investigational_plan",
    },
}


# number, title, requirement, resolver (None = structural parent or non-applicable leaf)
SKELETON: list[dict[str, Any]] = [
    {
        "number": "1.1",
        "title": "Forms",
        "children": [
            {"number": "1.1.1", "title": "Form FDA 1571", "requirement": REQUIRED, "resolve": _forms_1571},
            {"number": "1.1.2", "title": "Form FDA 1572", "requirement": REQUIRED, "resolve": _forms_1572},
            {
                "number": "1.1.3",
                "title": "Form FDA 3674 (ClinicalTrials.gov certification)",
                "requirement": REQUIRED,
                "resolve": _never("Not in scope for this POC."),
            },
        ],
    },
    {
        "number": "1.2",
        "title": "Cover Letter",
        "children": [
            {"number": "1.2", "title": "Initial IND cover letter", "requirement": REQUIRED, "resolve": _cover_letter},
        ],
    },
    {
        "number": "1.3",
        "title": "Administrative Information",
        "children": [
            {"number": "1.3.1", "title": "Contact / Agent Information", "requirement": REQUIRED, "resolve": _contact_info},
            {
                "number": "1.3.4",
                "title": "Financial Certification and Disclosure (Forms FDA 3454 / 3455)",
                "requirement": CONDITIONAL,
                "condition": "Required where covered clinical investigators have disclosable financial interests.",
            },
            {
                "number": "1.3.2",
                "title": "Field Copy Certification",
                "requirement": NOT_APPLICABLE,
                "condition": "Applies to NDA/BLA submissions, not an IND.",
            },
            {
                "number": "1.3.3",
                "title": "Debarment Certification",
                "requirement": NOT_APPLICABLE,
                "condition": "Applies to marketing applications, not an IND.",
            },
        ],
    },
    {
        "number": "1.4",
        "title": "References",
        "children": [
            {
                "number": "1.4.1",
                "title": "Letter of Authorization",
                "requirement": CONDITIONAL,
                "condition": "Required only when relying on a Drug Master File or another sponsor's application.",
            },
            {
                "number": "1.4.2",
                "title": "Statement of Right of Reference",
                "requirement": CONDITIONAL,
                "condition": "Required alongside a Letter of Authorization.",
            },
        ],
    },
    {
        "number": "1.5",
        "title": "Application Status",
        "requirement": NOT_APPLICABLE,
        "condition": "Withdrawal, inactivation, and reactivation requests do not apply to an initial submission.",
    },
    {
        "number": "1.6",
        "title": "Meetings",
        "children": [
            {
                "number": "1.6.1",
                "title": "Meeting Request",
                "requirement": CONDITIONAL,
                "condition": "Include only if requesting a meeting with this submission.",
            },
            {
                "number": "1.6.3",
                "title": "Correspondence Regarding Meetings",
                "requirement": CONDITIONAL,
                "condition": "Include if a pre-IND meeting occurred.",
            },
        ],
    },
    {
        "number": "1.7",
        "title": "Fast Track",
        "requirement": CONDITIONAL,
        "condition": "Include only when requesting fast track designation.",
    },
    {
        "number": "1.9",
        "title": "Pediatric Administrative Information",
        "requirement": CONDITIONAL,
        "condition": "Include where a pediatric study plan applies.",
    },
    {
        "number": "1.11",
        "title": "Information Amendment",
        "requirement": NOT_APPLICABLE,
        "condition": "Amendments follow the initial submission; they are not part of it.",
    },
    {
        "number": "1.12",
        "title": "Other Correspondence",
        "children": [
            {
                "number": "1.12.1",
                "title": "Pre-IND Correspondence",
                "requirement": CONDITIONAL,
                "condition": "Include prior FDA correspondence where it exists.",
            },
        ],
    },
    {
        "number": "1.13",
        "title": "Annual Report",
        "requirement": NOT_APPLICABLE,
        "condition": "Applies to an IND already in effect.",
    },
    {
        "number": "1.14",
        "title": "Labeling",
        "children": [
            {
                "number": "1.14.4",
                "title": "Investigational Drug Labeling",
                "requirement": REQUIRED,
                "resolve": _never("No labeling content in the case data and no generator."),
            },
        ],
    },
    {
        "number": "1.20",
        "title": "General Investigational Plan",
        "requirement": REQUIRED,
        "resolve": _investigational_plan,
    },
]


def _gap(number: str, status: str) -> dict[str, str]:
    """Owner and unlock condition for one leaf.

    Not applicable sections carry no owner: nobody is waiting on them. Sections that
    are already satisfied keep their owner but close, so the same row can be read
    before and after the gap is filled.
    """
    if status == NA:
        return {"owner": "", "source_needed": "", "status": NOT_TRACKED, "topic": ""}

    meta = GAP_OWNERS.get(number)
    if not meta:
        return {"owner": "Unassigned", "source_needed": "", "status": OPEN if status != PRESENT else CLOSED, "topic": ""}

    return {
        "owner": meta["owner"],
        "source_needed": meta["source_needed"] if status != PRESENT else "",
        "status": CLOSED if status == PRESENT else OPEN,
        "topic": meta["topic"],
    }


def _resolve_node(node: dict[str, Any], canonical: dict[str, Any]) -> dict[str, Any]:
    requirement = node.get("requirement")
    resolver = node.get("resolve")

    if requirement == NOT_APPLICABLE:
        status, detail = NA, node.get("condition", "")
    elif requirement == CONDITIONAL:
        status, detail = NEEDS_DECISION, node.get("condition", "")
    else:
        present, detail = resolver(canonical) if resolver else (False, "")
        status = PRESENT if present else ABSENT

    return {
        "number": node["number"],
        "title": node["title"],
        "requirement": requirement,
        "status": status,
        "detail": detail,
        "gap": _gap(node["number"], status),
    }


def generate_toc(canonical: dict[str, Any]) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []

    for entry in SKELETON:
        if "children" in entry:
            children = [_resolve_node(child, canonical) for child in entry["children"]]
            sections.append({"number": entry["number"], "title": entry["title"], "children": children})
        else:
            resolved = _resolve_node(entry, canonical)
            sections.append({"number": entry["number"], "title": entry["title"], "children": [resolved]})

    leaves = [leaf for section in sections for leaf in section["children"]]
    required = [leaf for leaf in leaves if leaf["requirement"] == REQUIRED]

    summary = {
        "required_total": len(required),
        "required_present": sum(1 for leaf in required if leaf["status"] == PRESENT),
        "required_absent": sum(1 for leaf in required if leaf["status"] == ABSENT),
        "needs_decision": sum(1 for leaf in leaves if leaf["status"] == NEEDS_DECISION),
        "not_applicable": sum(1 for leaf in leaves if leaf["status"] == NA),
        "open_gaps": sum(1 for leaf in leaves if (leaf.get("gap") or {}).get("status") == OPEN),
    }

    return {
        "case_id": canonical["case_id"],
        "document_name": "Module 1 Table of Contents - POC",
        "note": (
            "Section structure follows the US regional eCTD Module 1 organisation. Applicability is a "
            "demonstration heuristic for Initial INDs, not regulatory advice, and this is not a validated "
            "submission-ready eCTD package."
        ),
        "summary": summary,
        "sections": sections,
        "markdown": render_toc_markdown(canonical["case_id"], sections, summary),
    }


def render_toc_markdown(case_id: str, sections: list[dict[str, Any]], summary: dict[str, int]) -> str:
    lines = [
        "# Module 1 Table of Contents - POC",
        "",
        f"Case: {case_id}",
        "",
        (
            f"{summary['required_present']} of {summary['required_total']} required sections present; "
            f"{summary['required_absent']} outstanding; {summary['needs_decision']} awaiting a sponsor decision."
        ),
        "",
        "Section structure follows the US regional eCTD Module 1 organisation. Applicability is a",
        "demonstration heuristic for Initial INDs, not regulatory advice.",
        "",
    ]
    for section in sections:
        lines.append(f"## {section['number']} {section['title']}")
        for leaf in section["children"]:
            same = leaf["number"] == section["number"]
            label = leaf["title"] if same else f"{leaf['number']} {leaf['title']}"
            lines.append(f"- [{leaf['status']}] {label}")
            if leaf["detail"]:
                lines.append(f"  - {leaf['detail']}")
            gap = leaf.get("gap") or {}
            if gap.get("status") == OPEN:
                owed = f" - needs {gap['source_needed']}" if gap.get("source_needed") else ""
                lines.append(f"  - Owner: {gap['owner']}{owed}")
        lines.append("")
    return "\n".join(lines)
