"""Cross-document checks run over the partner's own materials.

Everything else in this pipeline reads the partner's package as input. This module
reads it as a subject: three deterministic checks that ask whether the package agrees
with itself, and with the eCTD Module 1 structure the rest of the pipeline already
models.

This is the same class of check the tool exists to perform - a value stated one way in
one document and another way in a second - applied to the material the partner sent.
Findings are stated with both sides quoted and the file each came from, so every one
of them can be checked in a minute without taking this code's word for it.
"""
from __future__ import annotations

import re
from typing import Any

from .toc import SKELETON

# "M1.7", "M2.6", "M3", "M1.10" - the module references used in the matrix.
MODULE_REF = re.compile(r"\bM(\d)(?:\.(\d+(?:\.\d+)*))?\b")

# The 21 CFR 312.23(a)(n) item a Section Map row is about.
CFR_ITEM = re.compile(r"\(a\)\((\d+)\)")


def _module1_titles() -> dict[str, str]:
    """Section number -> title, from the skeleton the gap analysis already uses."""
    titles: dict[str, str] = {}
    for entry in SKELETON:
        titles[entry["number"]] = entry["title"]
        for child in entry.get("children", []):
            titles.setdefault(child["number"], child["title"])
    return titles


# 21 CFR 312.23(a) item numbers and eCTD Module 1 section numbers are two different
# schemes. They coincide at one place only: (a)(1), the cover sheet, is Form FDA 1571,
# which is filed in Module 1.1 Forms. Past that they diverge completely.
CFR_ECTD_COINCIDE = {"1"}


def _check_module1_numbering(section_map: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Where an M1.x claim is really the 21 CFR 312.23(a)(x) item number in disguise.

    The test is narrow on purpose. It fires only when the eCTD subsection number the
    row claims is the same digit as the CFR item the row is about - the signature of
    one scheme being written in the other's notation - and it says what section 1.x
    actually is rather than asserting where the content should have gone. Which eCTD
    leaf each CFR item belongs in is a question this pipeline does not answer.
    """
    titles = _module1_titles()
    findings: list[dict[str, Any]] = []

    for row in section_map:
        location = row.get("ectd_location", "")
        section = row.get("section", "")
        cfr = CFR_ITEM.search(section)
        if not cfr:
            continue
        item = cfr.group(1)

        for match in MODULE_REF.finditer(location):
            module, sub = match.group(1), match.group(2)
            if module != "1" or sub != item or item in CFR_ECTD_COINCIDE:
                continue
            number = f"1.{sub}"
            known = titles.get(number)
            findings.append(
                {
                    "check": "module1_numbering",
                    "severity": "correction",
                    "where": f"Section Map row “{section}”",
                    "claim": f"eCTD location {match.group(0)}",
                    "conflict": (
                        f"In the US regional Module 1 structure, section {number} is “{known}”."
                        if known
                        else f"This pipeline's Module 1 skeleton carries no section {number}, so "
                        "the claim cannot be checked against it."
                    ),
                    "reads_as": f"the 21 CFR 312.23(a)({item}) item number written as an eCTD "
                    "section number",
                }
            )

    if findings:
        findings.append(
            {
                "check": "module1_numbering",
                "severity": "summary",
                "where": "Section Map, eCTD Location column",
                "claim": f"{len(findings)} row(s) affected",
                "conflict": "Every M1.<n> in the column is the same digit as the 21 CFR "
                "312.23(a)(<n>) item the row is about. The two numbering schemes coincide only at "
                "(a)(1) / M1.1; everywhere else the column is stating a CFR citation in eCTD "
                "notation.",
                "reads_as": "",
            }
        )
    return findings


def _files_in(text: str) -> set[str]:
    return set(re.findall(r"\b\d{2}_[A-Za-z0-9_\-\.]+?\.(?:docx|xlsx|json)\b", text or ""))


def _short_refs(text: str) -> set[str]:
    """`07_CMC`, `09_NCD`, `11_TOX` - the abbreviated form the brief uses."""
    return set(re.findall(r"\b(\d{2})_[A-Za-z]", text or ""))


def _check_module_assignment(
    section_map: list[dict[str, str]], module_map: list[dict[str, str]]
) -> list[dict[str, Any]]:
    """The same dossier, filed to two different modules by two of his own documents."""
    # Which module the brief's Section C assigns each numbered source file to.
    brief_module: dict[str, str] = {}
    for row in module_map:
        module = row.get("module", "")
        if module.lower() in ("module 1", "module 2"):
            # Module 1 lists every dossier as a summary source and Module 2 lists the
            # same files as summary inputs. Neither is a filing location, so a row
            # appearing there is not a contradiction.
            continue
        for prefix in _short_refs(row.get("source_documents", "")):
            brief_module[prefix] = module

    findings: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in section_map:
        location = row.get("ectd_location", "")
        modules = {f"Module {m.group(1)}" for m in MODULE_REF.finditer(location)}
        if "Module 1" not in modules:
            continue
        for prefix in _short_refs(row.get("source_file", "")):
            assigned = brief_module.get(prefix)
            key = (row.get("section", ""), assigned or "")
            if not assigned or assigned == "Module 1" or key in seen:
                continue
            seen.add(key)
            findings.append(
                {
                    "check": "module_assignment",
                    "severity": "contradiction",
                    "where": f"Section Map row “{row.get('section')}”",
                    "claim": f"the traceability matrix gives the eCTD location as {location}",
                    "conflict": f"the input brief Section C files the same dossier under {assigned} "
                    "and gives it no Module 1 location at all",
                    "reads_as": "two of the partner's own documents disagree on where this content "
                    "is filed",
                }
            )
    return findings


def _check_file_references(
    section_map: list[dict[str, str]], package_files: list[str]
) -> list[dict[str, Any]]:
    """Every file the matrix points at should be a file that shipped."""
    present = set(package_files)
    seen: set[str] = set()
    findings: list[dict[str, Any]] = []

    for row in section_map:
        for referenced in _files_in(row.get("source_file", "")):
            if referenced in present or referenced in seen:
                continue
            seen.add(referenced)
            stem = referenced.split("_")[0]
            nearby = sorted(f for f in present if f.startswith(stem + "_"))
            findings.append(
                {
                    "check": "file_reference",
                    "severity": "correction",
                    "where": f"Section Map row “{row.get('section')}”",
                    "claim": f"points at {referenced}",
                    "conflict": f"the package ships {', '.join(nearby)}"
                    if nearby
                    else "no file with that number is in the package",
                    "reads_as": "",
                }
            )
    return findings


def review_partner_package(partner_reference: dict[str, Any]) -> dict[str, Any]:
    section_map = partner_reference.get("section_map", [])
    module_map = partner_reference.get("module_map", [])
    package_files = partner_reference.get("package_files", [])

    findings = (
        _check_module1_numbering(section_map)
        + _check_module_assignment(section_map, module_map)
        + _check_file_references(section_map, package_files)
    )

    by_check: dict[str, int] = {}
    for finding in findings:
        by_check[finding["check"]] = by_check.get(finding["check"], 0) + 1

    return {
        "case_id": partner_reference["case_id"],
        "document_name": "Cross-document review of the partner's package",
        "summary": {"findings": len(findings), "by_check": by_check},
        "findings": findings,
        "checks": [
            {
                "id": "module1_numbering",
                "question": "Is any M1.x in the traceability matrix really the 21 CFR "
                "312.23(a)(x) item number written in eCTD notation?",
                "compares": "14 > Section Map against the Module 1 skeleton this pipeline models",
            },
            {
                "id": "module_assignment",
                "question": "Do the traceability matrix and the input brief file the same dossier "
                "to the same module?",
                "compares": "14 > Section Map against 12 > Section C",
            },
            {
                "id": "file_reference",
                "question": "Does every file the matrix cites exist in the package as delivered?",
                "compares": "14 > Section Map against the package file list",
            },
        ],
        "note": (
            "These are consistency findings, not regulatory judgements. Each one quotes both sides "
            "and names the document it came from so it can be checked directly."
        ),
    }


def render_partner_review_markdown(review: dict[str, Any]) -> str:
    lines = [
        "# Cross-document review of the partner's package",
        "",
        f"Case: {review['case_id']}",
        "",
        f"{review['summary']['findings']} finding(s).",
        "",
    ]
    for check in review["checks"]:
        hits = [f for f in review["findings"] if f["check"] == check["id"]]
        lines.append(f"## {check['question']}")
        lines.append(f"_{check['compares']}_")
        lines.append("")
        if not hits:
            lines.append("- No findings.")
        for finding in hits:
            lines.append(f"- **{finding['where']}** - {finding['claim']}")
            lines.append(f"  - {finding['conflict']}")
            if finding["reads_as"]:
                lines.append(f"  - Reads as: {finding['reads_as']}")
        lines.append("")
    lines.append(review["note"])
    return "\n".join(lines)


__all__ = ["review_partner_package", "render_partner_review_markdown"]
