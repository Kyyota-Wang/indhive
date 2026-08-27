# IND Module 1 POC Agent — Codex Implementation Guideline

## 1. Project Goal

Build a fast proof-of-concept (POC) agent for **IND Module 1**.

The POC does **not** need to be production-ready, submission-ready, Part 11 compliant, or fully accurate. Its purpose is to demonstrate visible progress quickly and show that a software agent can take a hypothetical IND case and automatically generate recognizable Module 1 outputs.

For this first POC, the agent should focus on:

1. **IND Cover Letter**
2. **FDA Form 1571 field population**
3. **Module 1 Table of Contents (TOC)**

If time permits, Form FDA 1572 can be added later, but it is not part of the initial required scope.

The core demo should be:

> **Synthetic IND case → Module 1 Agent → Cover Letter + 1571 field view + Module 1 TOC**

---

## 2. Important Scope Assumptions

We currently do **not** have real pharmaceutical sponsor source documents or real completed IND Module 1 submissions.

Therefore, the POC should use a **synthetic IND case database**.

The synthetic cases should be realistic enough to demonstrate the workflow, but all sponsor names, drug names, investigators, institutions, addresses, phone numbers, and emails must be fictional.

Do not present synthetic cases as real FDA submissions.

The architecture should be designed so that synthetic structured input can later be replaced by real document extraction from PDF, DOCX, XLSX, SharePoint, or other enterprise data sources.

---

## 3. Product Concept

The future production concept is:

```text
Real Sponsor / Protocol / Regulatory Source Documents
                     ↓
        Extraction + Normalization Layer
                     ↓
             Canonical IND Data
                     ↓
              Module 1 Agent
               /     |      \
              /      |       \
     Cover Letter   1571      TOC
```

For the current POC, skip real document extraction and begin directly from **Canonical IND Data** stored in the synthetic database.

Therefore:

```text
Synthetic IND Database
          ↓
    Select One Case
          ↓
     Module 1 Agent
          ↓
 ┌────────┼─────────┐
 ↓        ↓         ↓
Cover    1571      TOC
Letter   View
```

---

## 4. POC Input Definition

The direct POC input is **one synthetic IND case**.

Each case should contain structured information in the following categories.

### 4.1 Sponsor Information

Required example fields:

```json
{
  "legal_name": "NovaCura Therapeutics, Inc.",
  "address_line_1": "1200 Innovation Drive",
  "address_line_2": null,
  "city": "Boston",
  "state": "MA",
  "postal_code": "02115",
  "country": "USA",
  "contact_name": "Emily Carter",
  "contact_title": "VP, Regulatory Affairs",
  "phone": "617-555-0138",
  "email": "emily.carter@example.com"
}
```

### 4.2 Investigational Product Information

Example:

```json
{
  "code_name": "NCT-101",
  "generic_name": null,
  "dosage_form": "oral tablet",
  "route": "oral",
  "indication": "moderate-to-severe ulcerative colitis"
}
```

### 4.3 Protocol Information

Example:

```json
{
  "protocol_number": "NCT101-101",
  "title": "A Phase 1 Study of NCT-101 in Healthy Adult Participants",
  "phase": "Phase 1",
  "version": "1.0",
  "protocol_date": "2026-07-15"
}
```

### 4.4 Submission Metadata

Example:

```json
{
  "submission_type": "Initial IND",
  "submission_date": "2026-08-18",
  "serial_number": "0000",
  "ind_number": null
}
```

### 4.5 Investigator Information

Example:

```json
{
  "name": "Sarah Johnson, MD",
  "institution": "Example Clinical Research Center",
  "address": "500 Research Avenue, Cambridge, MA 02139",
  "phone": "617-555-0191",
  "email": "sarah.johnson@example.com"
}
```

Investigator information is not the main focus of the first POC, but keeping it in the schema will make later expansion to Form FDA 1572 easier.

---

## 5. Synthetic Database Requirements

Create an initial database with **10 fictional IND cases**.

A lightweight implementation is preferred. SQLite, JSON files, or another simple local persistence layer is sufficient.

Do not over-engineer the database.

### 5.1 Recommended Case Diversity

The 10 cases should include:

- 5 clean / complete cases
- 2 cases with missing information
- 2 cases with internally conflicting information
- 1 case with unusual formatting or naming conventions

Examples of useful variation:

- Sponsor name with “Inc.” vs “Incorporated”
- Missing contact title
- Missing protocol date
- Different dosage forms
- Different study phases
- Missing IND number for Initial IND
- Product code name only, no generic name
- Conflicting protocol version values
- Inconsistent sponsor name in two simulated source records

### 5.2 Suggested Storage Structure

A simple repository structure is acceptable:

```text
data/
├── cases/
│   ├── IND001.json
│   ├── IND002.json
│   ├── IND003.json
│   └── ...
│
├── schemas/
│   ├── canonical_ind.schema.json
│   ├── form_1571.schema.json
│   └── validation.schema.json
│
└── references/
    └── README.md
```

Alternatively, use SQLite with tables such as:

- `cases`
- `sponsor`
- `product`
- `protocol`
- `submission`
- `investigator`
- `validation_issues`

Use whichever implementation is faster and cleaner.

---

## 6. Canonical IND Data Model

The agent should consume one stable internal schema.

Recommended high-level structure:

```json
{
  "case_id": "IND001",
  "sponsor": {},
  "product": {},
  "protocol": {},
  "submission": {},
  "investigator": {}
}
```

This schema is important because future real document extraction should populate this exact structure.

The POC generator should not depend directly on raw file formats.

---

## 7. Required Output 1 — IND Cover Letter

Generate a professional draft IND Cover Letter based on the selected synthetic case.

The Cover Letter should use the canonical data and include, when available:

- Submission date
- Sponsor legal name
- Investigational product name/code
- Submission type
- Protocol number
- Protocol title
- Study phase
- Sponsor contact information
- A concise statement explaining that the sponsor is submitting an Initial IND
- A short list or description of included Module 1 materials

### 7.1 Important Generation Rules

The agent must:

- Use only facts present in the selected case.
- Never invent missing regulatory facts.
- If an important fact is missing, omit it or flag it.
- Keep the letter concise and professional.
- Clearly label the generated document as a **POC draft**.
- Avoid claiming that the package is FDA-submission-ready.

### 7.2 Evaluation

Do not use exact text matching for Cover Letter evaluation.

Instead, verify:

- Required facts are included.
- No unsupported facts are introduced.
- Sponsor name is correct.
- Drug/product name is correct.
- Submission type is correct.
- Protocol number/title are correct where applicable.
- Cover Letter facts are consistent with the 1571 output.

---

## 8. Required Output 2 — FDA Form 1571 Field View

For the POC, it is **not required to edit the official FDA PDF**.

Instead, create a clean HTML/web representation of the important Form FDA 1571 fields.

Example:

```text
FDA FORM 1571 — POC FIELD VIEW

Submission Type:
Initial IND

Sponsor Name:
NovaCura Therapeutics, Inc.

Sponsor Address:
1200 Innovation Drive
Boston, MA 02115

Investigational Product:
NCT-101

Study Phase:
Phase 1

Protocol Number:
NCT101-101
```

Later, a real PDF population layer can replace this view.

### 8.1 Mapping Behavior

Prefer deterministic mapping from canonical data to 1571 fields.

Example:

```text
canonical.sponsor.legal_name
        ↓
1571.sponsor_name
```

Do not use an LLM to guess straightforward field mappings.

### 8.2 Missing Data Behavior

If a field is unavailable:

```text
Status: MISSING
Value: —
```

Never invent a value.

### 8.3 Conflict Behavior

If simulated input contains conflicting authoritative values:

```text
Status: CONFLICT
Human review required
```

Do not silently select one.

---

## 9. Required Output 3 — Module 1 Table of Contents

Generate a simplified POC Module 1 TOC.

Example:

```text
Module 1 — Administrative Information

1.1 Forms
    - Form FDA 1571

1.2 Cover Letter
    - Initial IND Cover Letter

1.3 Administrative Information
    - Sponsor Information

Supporting Clinical Information
    - Protocol NCT101-101
```

This TOC is for demonstration only.

Do not claim that the first POC TOC is a complete eCTD-ready US regional Module 1 structure.

Add a visible note such as:

> POC structure for demonstration; not validated as a submission-ready eCTD package.

---

## 10. Validation Layer

Implement a lightweight validation layer.

Use four statuses:

```text
PASS
WARNING
MISSING
CONFLICT
```

Example output:

```text
Validation Summary

PASS
- Sponsor legal name
- Product name
- Protocol number
- Submission type

WARNING
- Sponsor contact title is unavailable

MISSING
- Protocol date

CONFLICT
- Protocol version differs across simulated source records
```

### 10.1 Minimum Validation Rules

Check at least:

- Sponsor legal name exists
- Product name/code exists
- Protocol number exists
- Protocol phase exists
- Submission type exists
- Submission date exists
- Cover Letter and 1571 use the same sponsor name
- Cover Letter and 1571 use the same product name
- Cover Letter and 1571 use the same protocol number
- No hallucinated fields are introduced

---

## 11. Field-Level Provenance

Even though the POC input is synthetic, implement a simple provenance concept.

Example:

```json
{
  "field": "sponsor_name",
  "value": "NovaCura Therapeutics, Inc.",
  "source": "synthetic_case.IND001.sponsor.legal_name",
  "source_type": "synthetic_structured_data"
}
```

This makes the architecture extensible to future real document evidence.

The UI can optionally display:

```text
Sponsor Name
NovaCura Therapeutics, Inc.

Source:
IND001 → sponsor.legal_name
```

---

## 12. User Interface

Build a minimal UI that is easy to demo to a coworker.

Streamlit is acceptable and probably the fastest option. A simple React frontend is also acceptable if already convenient in the repository.

Recommended demo flow:

```text
--------------------------------------------------

IND Module 1 POC Agent

Demo Case
[ IND001 - NCT-101 ▼ ]

[ Generate Module 1 Package ]

--------------------------------------------------

✓ Cover Letter Generated
✓ FDA 1571 Field View Generated
✓ Module 1 TOC Generated
✓ Validation Completed

[ View Cover Letter ]
[ View FDA 1571 ]
[ View TOC ]
[ View Validation ]

--------------------------------------------------
```

Useful optional features:

- Case detail panel
- Provenance panel
- Download Cover Letter as DOCX
- Download package as ZIP
- Display missing/conflicting fields prominently

Do not spend excessive time on UI polish.

---

## 13. Agent Design

Avoid unnecessary multi-agent complexity.

A simple pipeline is preferred:

```text
Selected Synthetic Case
        ↓
Schema Validation
        ↓
Canonical IND Data
        ↓
┌────────────────────────────┐
│ Module 1 POC Orchestrator  │
└────────────────────────────┘
        │
        ├── Deterministic 1571 Mapper
        │
        ├── Cover Letter Generator
        │
        ├── TOC Generator
        │
        └── Validator
        ↓
POC Module 1 Package
```

Only the Cover Letter generation clearly requires an LLM.

1571 population, TOC assembly, and basic validation should preferably be deterministic.

---

## 14. LLM Usage

Use the existing model/API configuration in the repository if one exists.

If no model integration exists yet, isolate LLM access behind a simple interface such as:

```python
generate_cover_letter(canonical_ind_data) -> str
```

The rest of the application should work independently of a specific model provider.

### LLM Prompt Requirements

The Cover Letter prompt should instruct the model to:

1. Use only supplied structured facts.
2. Never invent missing information.
3. Avoid adding regulatory claims not supported by the input.
4. Produce a concise professional POC draft.
5. Keep sponsor, drug, protocol, and submission metadata exactly consistent with the structured input.

---

## 15. Deliverables

The first implementation should include:

### A. Synthetic Data

- 10 fictional IND cases
- Stable canonical schema
- At least a few missing/conflict cases

### B. Generator

- Cover Letter generation
- FDA 1571 field mapping
- Simplified Module 1 TOC generation

### C. Validation

- Missing-field detection
- Conflict detection
- Cross-document consistency checks

### D. UI

- Select synthetic case
- Generate outputs
- View generated outputs
- View validation results

### E. Documentation

Update the project README with:

- POC purpose
- How to run
- Architecture
- Input schema
- Output definitions
- Known limitations
- Future roadmap

---

## 16. Non-Goals for This POC

Do **not** spend time implementing:

- Full IND Module 1 coverage
- Form FDA 1572 unless time permits
- FDA 3454 / 3455
- Real FDA PDF editing
- Real PDF/DOCX source extraction
- OCR
- SharePoint integration
- OneDrive integration
- eCTD packaging
- Part 11 compliance
- Electronic signature
- GAMP validation
- Production authentication
- Full audit trail
- Knowledge graph
- Multi-agent orchestration
- Fine-tuning
- Model training
- Production-grade regulatory validation

These are future phases.

---

## 17. Future Extension Path

Design the code so that the POC can evolve in this order:

```text
Phase 0
Synthetic structured cases
        ↓
CL + 1571 POC

Phase 1
Real PDF/DOCX ingestion
        ↓
Extraction into Canonical IND Data

Phase 2
Add FDA 1572
Add more Module 1 documents

Phase 3
Field-level evidence from source documents
Cross-document consistency validation

Phase 4
Actual FDA form rendering
Real regulatory templates

Phase 5
eCTD packaging / enterprise integration
Part 11 / validation / audit workflow
```

---

## 18. Acceptance Criteria for the First Demo

The POC is successful if a user can:

1. Start the application.
2. Select one of 10 synthetic IND cases.
3. Click one button to generate the Module 1 POC package.
4. View a plausible IND Cover Letter.
5. View a populated FDA 1571 field representation.
6. View a simplified Module 1 TOC.
7. See missing/conflicting data warnings when applicable.
8. Confirm that the Cover Letter and 1571 use consistent sponsor/product/protocol information.

The goal is a clear, credible demo — not regulatory completeness.

---

## 19. Engineering Principle

Optimize for:

> **Fast, understandable, extensible POC**

not:

> **Perfect regulatory platform**

Keep modules small, schemas explicit, outputs inspectable, and logic easy to replace later.
