# IND Module 1 POC Agent

Fast proof-of-concept for generating a small FDA IND Module 1 demo package from fictional synthetic data.

The current workflow is:

```text
Synthetic source records
        -> canonical IND data
        -> Module 1 POC generator
        -> Cover Letter + FDA 1571 Field View + TOC + Validation
```

This is not regulatory production software and does not create a submission-ready FDA package.

## What It Generates

For a selected synthetic IND case, the app generates and persists:

- IND Cover Letter POC draft
- FDA Form 1571 populated field view
- Simplified Module 1 Table of Contents
- Basic validation results for missing and conflicting data

Generated artifacts are written under:

```text
outputs/generated/<CASE_ID>/
```

## Data Layout

```text
data/
  source_cases/
    IND001.json ... IND010.json
  evaluation/
    golden_truth/
      IND001_expected.json
      IND002_expected.json
      IND003_expected.json
  schemas/
    synthetic_source_case.schema.json
    canonical_ind.schema.json
    form_1571.schema.json
    validation.schema.json
```

`data/source_cases` is agent-visible synthetic source data. It mimics already-extracted source snippets and is intentionally not the expected canonical answer.

`data/evaluation/golden_truth` is evaluation-only. The application and generation pipeline do not read these files.

## Synthetic Case Mix

- `IND001`, `IND004`, `IND005`, `IND006`, `IND007`: clean cases
- `IND002`, `IND008`: missing-data cases
- `IND003`, `IND009`: conflict cases
- `IND010`: unusual formatting / naming case

All sponsors, products, investigators, institutions, contact details, and addresses are fictional.

## Architecture

```text
src/ind_m1_poc/
  loader.py        source case loading and normalization
  form_1571.py    explicit deterministic 1571 field mapping
  cover_letter.py LLM-first cover letter interface with template fallback
  toc.py          deterministic simplified TOC generation
  validation.py   missing/conflict/cross-output validation
  orchestrator.py end-to-end package generation and persistence
  evaluation.py   golden-case checks
```

The explicit 1571 mapping layer lives in `src/ind_m1_poc/form_1571.py` as `FIELD_MAPPINGS`.

## Run From CLI

Use any Python 3.11+ interpreter.

```powershell
python run_poc.py --case IND001
python run_poc.py --all
python evaluate_golden.py
```

In this Codex desktop environment, the bundled Python path used for verification was:

```powershell
& "C:\Users\kangc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" run_poc.py --all
```

## Run No-Dependency Demo UI

This route uses only the Python standard library.

```powershell
python web_app.py --port 8501
```

Then open:

```text
http://127.0.0.1:8501
```

## Optional Streamlit UI

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Start the app:

```powershell
streamlit run app.py
```

## Cover Letter Generation

The Cover Letter generator tries the LLM path first when:

- `openai` is installed
- `OPENAI_API_KEY` is set

Optional model override:

```powershell
$env:OPENAI_MODEL="gpt-5-mini"
```

If LLM generation is unavailable, the app uses a deterministic template fallback and records the reason in the generated `cover_letter.json`.

## Validation Scope

The validation layer checks:

- Required canonical fields
- Useful optional fields
- Source-record conflicts
- Cross-output consistency between Cover Letter fact manifest and FDA 1571 field view
- Whether Cover Letter facts are supported by canonical data

It uses four statuses:

- `PASS`
- `WARNING`
- `MISSING`
- `CONFLICT`

## Known Limitations

- No real PDF/DOCX extraction
- No official FDA PDF population
- No eCTD packaging
- No Part 11 controls
- No production audit trail
- No real regulatory completeness checks
- No Form FDA 1572 in the initial scope

## Future Extension Path

The next layer can replace `data/source_cases` with real extraction outputs while preserving the canonical schema and downstream generators.
