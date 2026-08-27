"""The gap register, and the crosswalk against a partner's own gap list.

Two things happen here.

First, `build_gap_register` collects everything the pipeline already knows is
outstanding - empty required fields on Form 1571, sections the Module 1 skeleton
could not satisfy, conditional sections still awaiting a sponsor decision - into one
list where each row carries an owner, the source that would close it, and evidence
pointing back at where the finding came from.

Second, `crosswalk` lines that register up against a gap list somebody produced by
hand. The point of the comparison is not to score anybody. It is to show that a
deterministic pass over the same inputs reaches the same conclusions, and to make
the places where the two lists differ visible instead of quietly absent.

Matching is by topic, never by wording. Each of our gaps declares its topic in the
skeleton; each of theirs is classified by the rules in `PARTNER_TOPIC_RULES`, which
read only their own text. The rules are ordered, first match wins, and they are
listed here in full so a reader can check them against the list they wrote.
"""
from __future__ import annotations

import re
from typing import Any

from .toc import CLOSED, OPEN

AGREED = "AGREED"
ONLY_OURS = "ONLY_OURS"
ONLY_THEIRS = "ONLY_THEIRS"


# Form 1571 fields whose absence is itself a filing gap, with the same owner and
# unlock condition shape the Module 1 skeleton uses.
FORM_FIELD_GAPS: dict[str, dict[str, str]] = {
    "ind_number": {
        "owner": "Regulatory Affairs",
        "source_needed": "The IND number FDA assigns on receipt",
        "topic": "ind_number",
        "item": "Box 6 IND number is empty; no number has been assigned",
    },
    "sponsor_email": {
        "owner": "Regulatory Affairs",
        "source_needed": "Sponsor contact email address",
        "topic": "sponsor_contact",
        "item": "No sponsor contact email in the input",
    },
}


# Ordered, first match wins. Each rule reads the partner's own item text and nothing
# else. Specific forms and identifiers come before general words, so "IRB approvals
# at each site" is not swept up by a rule about sites.
PARTNER_TOPIC_RULES: list[tuple[str, str]] = [
    (r"ind number", "ind_number"),
    (r"\b1572\b", "investigator_list"),
    (r"\b3674\b|clinicaltrials\.gov|\bnct\b", "nct_registration"),
    (r"\b3454\b|\b3455\b|financial disclosure", "financial_disclosure"),
    (r"\birb\b|ethics committee", "irb_approval"),
    (r"signator|signature", "signatory"),
    (r"proprietary|\binn\b", "proprietary_name"),
    (r"clinical data", "clinical_data"),
    (r"\bcoa\b|batch", "batch_coa"),
    (r"label", "labeling"),
    (r"protocol", "protocol_final"),
    (r"investigator|\bsite\b", "investigator_list"),
]


def classify_partner_gap(item: str) -> str:
    text = (item or "").lower()
    for pattern, topic in PARTNER_TOPIC_RULES:
        if re.search(pattern, text):
            return topic
    return "unclassified"


def _has(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def build_gap_register(
    canonical: dict[str, Any],
    form_1571: dict[str, Any],
    toc: dict[str, Any],
) -> dict[str, Any]:
    """One list of everything outstanding, from both the form and the section map."""
    items: list[dict[str, Any]] = []

    fields = {field["field_id"]: field for field in form_1571["fields"]}
    for field_id, meta in FORM_FIELD_GAPS.items():
        field = fields.get(field_id)
        if field is None or _has(field.get("value")):
            continue
        box = field.get("box")
        items.append(
            {
                "origin": "form_1571",
                "where": f"Form FDA 1571 Box {box}" if box else "Form FDA 1571 (supporting data)",
                "item": meta["item"],
                "owner": meta["owner"],
                "source_needed": meta["source_needed"],
                "status": OPEN,
                "topic": meta["topic"],
                "evidence": {
                    "canonical_path": field.get("canonical_path"),
                    "field_status": field.get("status"),
                },
            }
        )

    for section in toc.get("sections", []):
        for leaf in section.get("children", []):
            gap = leaf.get("gap") or {}
            if gap.get("status") != OPEN:
                continue
            items.append(
                {
                    "origin": "module1_toc",
                    "where": f"Module 1 section {leaf['number']}",
                    "item": f"{leaf['title']} - {leaf['status']}",
                    "owner": gap.get("owner", ""),
                    "source_needed": gap.get("source_needed", ""),
                    "status": OPEN,
                    "topic": gap.get("topic", ""),
                    "evidence": {
                        "section_status": leaf["status"],
                        "detail": leaf.get("detail", ""),
                    },
                }
            )

    # A section that is present still deserves a row when its topic is one the
    # partner tracks, so the crosswalk can say "we looked, and it is closed".
    closed_topics = sorted(
        {
            (leaf.get("gap") or {}).get("topic", "")
            for section in toc.get("sections", [])
            for leaf in section.get("children", [])
            if (leaf.get("gap") or {}).get("status") == CLOSED
        }
        - {""}
    )

    return {
        "case_id": canonical["case_id"],
        "document_name": "Module 1 gap register",
        "summary": {
            "open": len(items),
            "from_form_1571": sum(1 for i in items if i["origin"] == "form_1571"),
            "from_module1_toc": sum(1 for i in items if i["origin"] == "module1_toc"),
        },
        "items": items,
        "closed_topics": closed_topics,
        "note": (
            "Derived from the canonical record, the Form 1571 field view and the Module 1 "
            "section skeleton. Owners are the function that normally holds the item for an "
            "Initial IND; they are a demonstration default, not the partner's own assignment."
        ),
    }


def crosswalk(
    register: dict[str, Any],
    partner_reference: dict[str, Any],
    form_diff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Line our register up against the partner's hand-written gap list."""
    ours_by_topic: dict[str, list[dict[str, Any]]] = {}
    for item in register["items"]:
        ours_by_topic.setdefault(item["topic"], []).append(item)

    # Findings from the 1571 diff can corroborate a partner gap our register has no
    # field for. They never create a match; they are shown alongside one.
    diff_by_topic: dict[str, list[dict[str, Any]]] = {}
    for finding in (form_diff or {}).get("findings", []):
        if finding.get("topic"):
            diff_by_topic.setdefault(finding["topic"], []).append(finding)

    rows: list[dict[str, Any]] = []
    matched_topics: set[str] = set()

    for gap in partner_reference.get("gaps_log", []):
        topic = classify_partner_gap(gap.get("item", ""))
        ours = ours_by_topic.get(topic, [])
        if ours:
            matched_topics.add(topic)
        rows.append(
            {
                "verdict": AGREED if ours else ONLY_THEIRS,
                "topic": topic,
                "theirs": {
                    "id": gap.get("id"),
                    "item": gap.get("item"),
                    "owner": gap.get("owner"),
                    "source_needed": gap.get("source_needed"),
                    "status": gap.get("status"),
                },
                "ours": [
                    {
                        "where": item["where"],
                        "item": item["item"],
                        "owner": item["owner"],
                        "source_needed": item["source_needed"],
                    }
                    for item in ours
                ],
                "corroborated_by": [
                    {"where": f["where"], "note": f["note"]} for f in diff_by_topic.get(topic, [])
                ],
                "why_not": (
                    ""
                    if ours
                    else "The canonical record this pipeline builds carries no field for it, so "
                    "the pipeline cannot derive it."
                ),
            }
        )

    for topic, items in sorted(ours_by_topic.items()):
        if topic in matched_topics or not topic:
            continue
        for item in items:
            rows.append(
                {
                    "verdict": ONLY_OURS,
                    "topic": topic,
                    "theirs": None,
                    "ours": [
                        {
                            "where": item["where"],
                            "item": item["item"],
                            "owner": item["owner"],
                            "source_needed": item["source_needed"],
                        }
                    ],
                    "corroborated_by": [],
                    "why_not": "Not listed in the partner's GAPS Log.",
                }
            )

    order = {AGREED: 0, ONLY_OURS: 1, ONLY_THEIRS: 2}
    rows.sort(key=lambda r: (order[r["verdict"]], r["topic"]))

    return {
        "case_id": register["case_id"],
        "document_name": "Gap crosswalk - our derivation vs the partner's GAPS Log",
        "partner_source": partner_reference.get("source_files", {}).get("gaps_log", ""),
        "summary": {
            "agreed": sum(1 for r in rows if r["verdict"] == AGREED),
            "only_ours": sum(1 for r in rows if r["verdict"] == ONLY_OURS),
            "only_theirs": sum(1 for r in rows if r["verdict"] == ONLY_THEIRS),
            "partner_total": len(partner_reference.get("gaps_log", [])),
        },
        "rows": rows,
        "method": (
            "Our gaps come from the deterministic pipeline: an empty required field on Form 1571, "
            "or a Module 1 section the skeleton could not satisfy. Theirs are read from the GAPS "
            "Log sheet as written. The two are matched on topic, using ordered keyword rules that "
            "read only the partner's own wording - never on similarity of phrasing."
        ),
        "note": (
            "Rows marked ONLY_THEIRS are not errors on either side. Most of them are Module 2 to 5 "
            "obligations this pipeline does not model. Where one is a Module 1 obligation, it marks "
            "a field the canonical record does not yet carry - a hole on our side, not theirs."
        ),
    }


def render_gap_crosswalk_markdown(cross: dict[str, Any]) -> str:
    s = cross["summary"]
    lines = [
        "# Gap crosswalk",
        "",
        f"Case: {cross['case_id']}",
        "",
        (
            f"{s['agreed']} of the partner's {s['partner_total']} logged gaps were reached "
            f"independently by the pipeline. {s['only_ours']} gap(s) the pipeline found are not "
            f"in their log; {s['only_theirs']} of theirs are outside what it models."
        ),
        "",
        cross["method"],
        "",
    ]
    headings = {
        AGREED: "Reached by both",
        ONLY_OURS: "Found only by the pipeline",
        ONLY_THEIRS: "Listed only in the partner's log",
    }
    for verdict, heading in headings.items():
        rows = [r for r in cross["rows"] if r["verdict"] == verdict]
        if not rows:
            continue
        lines.extend([f"## {heading}", ""])
        for row in rows:
            theirs = row["theirs"]
            indent = ""
            if theirs:
                lines.append(f"- **{theirs['id']}** {theirs['item']} _(owner: {theirs['owner']})_")
                indent = "  "
            for item in row["ours"]:
                prefix = f"{indent}- pipeline: " if indent else "- "
                lines.append(f"{prefix}{item['where']} - {item['item']}")
                if item["source_needed"]:
                    lines.append(f"{indent}  - needs {item['source_needed']} ({item['owner']})")
            for note in row["corroborated_by"]:
                lines.append(f"{indent}- corroborated by {note['where']}: {note['note']}")
            if row["why_not"] and verdict == ONLY_THEIRS:
                lines.append(f"{indent}- {row['why_not']}")
        lines.append("")
    lines.append(cross["note"])
    return "\n".join(lines)


def render_gap_register_markdown(register: dict[str, Any]) -> str:
    lines = [
        "# Module 1 gap register",
        "",
        f"Case: {register['case_id']}",
        "",
        f"{register['summary']['open']} open item(s).",
        "",
    ]
    for item in register["items"]:
        lines.append(f"## {item['where']}")
        lines.append(f"- {item['item']}")
        lines.append(f"- Owner: {item['owner']}")
        if item["source_needed"]:
            lines.append(f"- Closes when: {item['source_needed']}")
        lines.append(f"- Status: {item['status']}")
        lines.append("")
    lines.append(register["note"])
    return "\n".join(lines)


__all__ = [
    "AGREED",
    "ONLY_OURS",
    "ONLY_THEIRS",
    "build_gap_register",
    "classify_partner_gap",
    "crosswalk",
    "render_gap_crosswalk_markdown",
    "render_gap_register_markdown",
]
