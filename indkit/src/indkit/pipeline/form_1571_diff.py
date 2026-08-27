"""Compare the generated Form 1571 field view against a hand-filled draft.

The partner filled a 1571 by hand and sent it with the package. That draft is the
closest thing this project has to an answer key, so the pipeline's own output is put
next to it field by field.

One thing has to be settled before any comparison is meaningful: his draft numbers
its fields 1 to 17, and Form FDA 1571 does not. The current form runs Box 1 to Box 13
plus a certification and signature area, and several of his numbered items are not
fields on the form at all. Everything here is organised by the box numbers printed on
the form, and every place his numbering diverges is reported rather than silently
reconciled - the numbering is the first thing worth telling him.
"""
from __future__ import annotations

import re
from typing import Any

from .form_1571 import BOX_LABELS

SAME = "SAME"
EQUIVALENT = "EQUIVALENT"
OURS_BROADER = "OURS_BROADER"
THEIRS_BROADER = "THEIRS_BROADER"
DIFFERENT = "DIFFERENT"
ONLY_OURS = "ONLY_OURS"
ONLY_THEIRS = "ONLY_THEIRS"

# Words that carry no content when comparing two renderings of the same field.
STOPWORDS = {
    "a", "an", "and", "the", "of", "or", "to", "for", "in", "on", "is", "are",
    "generic", "trade", "name", "names", "check", "all", "that", "apply", "attached",
}


# His draft item -> where that content actually sits on Form FDA 1571.
#
# `box`         the printed box that carries this content, so the values can be compared
# `nearest`     content the form covers somewhere else, but not as a numbered box of its own
# neither       content the form does not carry at all
#
# Keys are matched against the label he wrote, lower-cased, first substring hit wins.
DRAFT_MAP: list[dict[str, Any]] = [
    {"match": "ind number", "box": "6", "note": "He writes this above the numbering, not as a numbered item."},
    {"match": "serial number", "box": "10", "note": "He writes this above the numbering, not as a numbered item."},
    {"match": "name of sponsor", "box": "1", "note": ""},
    {
        "match": "address of sponsor",
        "box": "3",
        "note": "His item 2. On the form the address is Box 3; Box 2 is the date of submission.",
    },
    {
        "match": "representative",
        "nearest": "14",
        "note": "His item 3. The form has no field called Representative. The nearest is Box 14, "
        "the person responsible for monitoring the conduct and progress of the investigations.",
    },
    {"match": "telephone", "box": "4", "note": ""},
    {"match": "drug name", "box": "5", "note": ""},
    {"match": "indication", "box": "7", "note": "His item 6. On the form indications are Box 7."},
    {"match": "phase of study", "box": "8", "note": "His item 7. On the form the phase is Box 8."},
    {
        "match": "ind is not for a",
        "note": "His item 8. There is no such field on Form FDA 1571.",
    },
    {
        "match": "type of submission",
        "box": "11",
        "note": "His item 9. On the form this is Box 11, 'this submission contains'.",
    },
    {
        "match": "contents of application",
        "box": "12",
        "note": "His item 10, labelled 'Section a-k'. Box 12 is a checklist of items numbered 1 to 10; "
        "it has no lettered sections.",
    },
    {
        "match": "investigator's brochure status",
        "nearest": "12",
        "note": "His item 11. The brochure is item 5 inside the Box 12 checklist, not a field of its own.",
    },
    {
        "match": "pre-existing ind references",
        "nearest": "9",
        "note": "His item 12. Box 9 lists the numbers of all INDs, NDAs, DMFs and BLAs referred to, "
        "which is broader than a cross-reference letter.",
    },
    {
        "match": "pediatric studies",
        "note": "His item 13. Not a field on Form FDA 1571; a PREA waiver or deferral request is filed "
        "under Module 1.9.",
    },
    {
        "match": "human subject protection",
        "note": "His item 14. Covered by the pre-printed certification text the signature attests to, "
        "not by a fillable box.",
    },
    {
        "match": "sponsor commitments",
        "note": "His item 15. Also part of the pre-printed certification text, not a fillable box.",
    },
    {
        "match": "certification of compliance w/ form fda 3674",
        "note": "His item 16. Form FDA 3674 is a separate form filed under Module 1.1.3; the 1571 "
        "carries no certification field for it.",
    },
    {
        "match": "signature & date",
        "note": "His item 17. The signature area is not a numbered box.",
    },
]

MONTHS = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May", "06": "June", "07": "July", "08": "August",
    "09": "September", "10": "October", "11": "November", "12": "December",
}

# Characters the partner's package and this pipeline render differently. Folding them
# stops a comparison failing over a multiplication sign.
FOLD = {"×": "x", "ε": "epsilon", "≥": ">=", "≤": "<=", "—": "-", "–": "-", "’": "'", "“": '"', "”": '"'}


def _fold(text: str) -> str:
    for source, target in FOLD.items():
        text = text.replace(source, target)
    return text


def _normalise(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(_fold(str(value)).lower().split()).strip(" .")


def _tokens(value: Any) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", _normalise(value)) if t and t not in STOPWORDS}


def _compare(ours: Any, theirs: Any) -> str:
    if not _normalise(ours) and not _normalise(theirs):
        return SAME
    if not _normalise(ours):
        return ONLY_THEIRS
    if not _normalise(theirs):
        return ONLY_OURS
    if _normalise(ours) == _normalise(theirs):
        return SAME

    ours_t, theirs_t = _tokens(ours), _tokens(theirs)
    if ours_t == theirs_t:
        return EQUIVALENT
    if theirs_t and theirs_t < ours_t:
        return OURS_BROADER
    if ours_t and ours_t < theirs_t:
        return THEIRS_BROADER
    return DIFFERENT


def _long_date(iso: str) -> str:
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    if not match:
        return iso or ""
    year, month, day = match.groups()
    return f"{int(day)} {MONTHS[month]} {year}"


def _map_entry(label: str) -> dict[str, Any]:
    lowered = (label or "").lower()
    for entry in DRAFT_MAP:
        if entry["match"] in lowered:
            return entry
    return {"match": "", "note": "Not recognised; no mapping to a box on the form."}


def _address(slot: dict[str, Any]) -> str:
    """Box 3 is one address, not six fields. Print it the way it is written."""
    values = dict(zip(slot["labels"], slot["parts"]))
    lines = [
        values.get("Sponsor Address Line 1"),
        values.get("Sponsor Address Line 2"),
        values.get("Sponsor City"),
    ]
    state = values.get("Sponsor State")
    postal = values.get("Sponsor Postal Code")
    region = " ".join(part for part in (state, postal) if part)
    parts = [str(v) for v in lines if v] + ([region] if region else [])
    country = values.get("Sponsor Country")
    if country:
        parts.append(str(country))
    return ", ".join(parts)


def _our_box_values(form_1571: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Group the generated fields by the box they print in."""
    by_box: dict[str, dict[str, Any]] = {}
    for field in form_1571["fields"]:
        box = field.get("box")
        if not box:
            continue
        slot = by_box.setdefault(box, {"parts": [], "statuses": [], "labels": []})
        slot["parts"].append(field.get("value"))
        slot["statuses"].append(field.get("status"))
        slot["labels"].append(field["label"])

    out: dict[str, dict[str, Any]] = {}
    for box, slot in by_box.items():
        filled = [str(p) for p in slot["parts"] if p not in (None, "")]
        out[box] = {
            "value": _address(slot) if box == "3" else ", ".join(filled),
            "status": "MISSING" if not filled else ("CONFLICT" if "CONFLICT" in slot["statuses"] else "PASS"),
            "from_fields": slot["labels"],
        }
    return out


def diff_form_1571(
    form_1571: dict[str, Any],
    partner_reference: dict[str, Any],
    canonical: dict[str, Any],
) -> dict[str, Any]:
    draft = partner_reference.get("form_1571_draft", [])
    ours = _our_box_values(form_1571)

    theirs_by_box: dict[str, dict[str, Any]] = {}
    unplaced: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    for entry in draft:
        mapping = _map_entry(entry["label"])
        record = {
            "draft_number": entry["draft_number"],
            "label": entry["label"],
            "value": entry["value"],
            "note": mapping["note"],
            "nearest_box": mapping.get("nearest"),
        }
        box = mapping.get("box")
        if box:
            theirs_by_box[box] = record
            if entry["draft_number"] and entry["draft_number"] != box:
                findings.append(
                    {
                        "code": "numbering",
                        "topic": "form_numbering",
                        "where": f"his item {entry['draft_number']} -> Box {box}",
                        "note": f"“{entry['label']}” is numbered {entry['draft_number']} in his draft. "
                        f"On Form FDA 1571 it is Box {box}, {BOX_LABELS.get(box, '')}.",
                        "severity": "correction",
                    }
                )
        else:
            unplaced.append(record)
            findings.append(
                {
                    "code": "not_a_field",
                    "topic": "form_numbering",
                    "where": f"his item {entry['draft_number']}" if entry["draft_number"] else entry["label"],
                    "note": mapping["note"],
                    "severity": "correction",
                }
            )

        if re.search(r"\[[^\]]+\]", entry["value"]):
            findings.append(
                {
                    "code": "placeholder",
                    "topic": "signatory",
                    "where": f"his item {entry['draft_number']}" if entry["draft_number"] else entry["label"],
                    "note": f"Value still contains an unfilled placeholder: “{entry['value']}”.",
                    "severity": "gap",
                }
            )

    rows: list[dict[str, Any]] = []
    for box in sorted(set(ours) | set(theirs_by_box), key=int):
        our_side = ours.get(box)
        their_side = theirs_by_box.get(box)
        verdict = _compare(our_side["value"] if our_side else None, their_side["value"] if their_side else None)
        rows.append(
            {
                "box": box,
                "box_label": BOX_LABELS.get(box, ""),
                "verdict": verdict,
                "ours": our_side,
                "theirs": their_side,
                "note": their_side["note"] if their_side else "",
            }
        )

    # Box 6: a reserved number is not an assigned one. Worth saying out loud, because
    # a placeholder in Box 6 is exactly the kind of value that survives into a filing.
    ind_row = next((r for r in rows if r["box"] == "6"), None)
    if ind_row and ind_row["verdict"] == ONLY_THEIRS:
        findings.append(
            {
                "code": "reserved_not_assigned",
                "topic": "ind_number",
                "where": "Box 6",
                "note": f"His draft carries “{ind_row['theirs']['value']}”. A sponsor reservation "
                "is not an assigned IND number, so the pipeline leaves Box 6 empty and reports it "
                "as a gap instead.",
                "severity": "gap",
            }
        )

    # Box 2 is the date of submission. If his draft never captures it as a field,
    # say where the date does appear so the point lands as a fix, not a complaint.
    date_row = next((r for r in rows if r["box"] == "2"), None)
    if date_row and date_row["verdict"] == ONLY_OURS:
        iso = canonical.get("submission", {}).get("submission_date") or ""
        wanted = {_normalise(iso), _normalise(_long_date(iso))} - {""}
        elsewhere = [
            entry
            for entry in draft
            if any(form in _normalise(entry["value"]) for form in wanted)
        ]
        where = (
            "; it appears only in "
            + ", ".join(
                f"his item {e['draft_number']} ({e['label']})" if e["draft_number"] else e["label"]
                for e in elsewhere
            )
            if elsewhere
            else "; it does not appear anywhere in his draft"
        )
        findings.append(
            {
                "code": "missing_box",
                "topic": "form_numbering",
                "where": "Box 2",
                "note": f"Box 2 is the date of submission. His draft has no field for it{where}.",
                "severity": "correction",
            }
        )

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1

    return {
        "case_id": form_1571["case_id"],
        "document_name": "Form 1571 - generated vs the partner's hand-filled draft",
        "partner_source": partner_reference.get("source_files", {}).get("form_1571_draft", ""),
        "summary": {
            "boxes_compared": len(rows),
            "agree": counts.get(SAME, 0) + counts.get(EQUIVALENT, 0),
            "differ": counts.get(DIFFERENT, 0) + counts.get(OURS_BROADER, 0) + counts.get(THEIRS_BROADER, 0),
            "only_ours": counts.get(ONLY_OURS, 0),
            "only_theirs": counts.get(ONLY_THEIRS, 0),
            "draft_items_off_form": len(unplaced),
            "findings": len(findings),
        },
        "rows": rows,
        "unplaced": unplaced,
        "findings": findings,
        "numbering_note": (
            "His draft numbers its fields 1 to 17. Form FDA 1571 does not use that numbering, so "
            "this view is organised by the box numbers printed on the form and each of his items is "
            "placed against the box that actually carries it."
        ),
        "note": (
            "Values are compared after folding whitespace, case and a few characters the two packages "
            "render differently. A verdict of OURS_BROADER or THEIRS_BROADER means one side states "
            "everything the other does and more; it is not a disagreement."
        ),
    }


def render_form_diff_markdown(diff: dict[str, Any]) -> str:
    s = diff["summary"]
    lines = [
        "# Form 1571 - generated vs the partner's draft",
        "",
        f"Case: {diff['case_id']}",
        "",
        f"{s['boxes_compared']} boxes compared: {s['agree']} agree, {s['differ']} differ, "
        f"{s['only_ours']} only in the generated form, {s['only_theirs']} only in his draft. "
        f"{s['draft_items_off_form']} of his numbered items are not fields on Form FDA 1571.",
        "",
        diff["numbering_note"],
        "",
        "## Box by box",
        "",
    ]
    for row in diff["rows"]:
        lines.append(f"### Box {row['box']} - {row['box_label']}")
        lines.append(f"- Verdict: {row['verdict']}")
        lines.append(f"- Generated: {row['ours']['value'] if row['ours'] else '-'}")
        if row["theirs"]:
            number = row["theirs"]["draft_number"]
            label = f"his item {number}" if number else "his draft"
            lines.append(f"- Draft ({label}): {row['theirs']['value']}")
        else:
            lines.append("- Draft: no corresponding field")
        if row["note"]:
            lines.append(f"- Note: {row['note']}")
        lines.append("")

    if diff["unplaced"]:
        lines.extend(["## Draft items that are not fields on the form", ""])
        for entry in diff["unplaced"]:
            number = entry["draft_number"]
            lines.append(f"- item {number}. {entry['label']}: {entry['value']}")
            lines.append(f"  - {entry['note']}")
        lines.append("")

    lines.extend(["## Findings", ""])
    for finding in diff["findings"]:
        lines.append(f"- [{finding['severity']}] {finding['where']}: {finding['note']}")
    lines.extend(["", diff["note"]])
    return "\n".join(lines)


__all__ = ["diff_form_1571", "render_form_diff_markdown"]
