# Working Log

Project: Synthetic data for IND Module 1 POC

## 2026-08-18

- Started working log for the POC data-generation phase.
- Current understanding: the broader project is an agent that generates IND Module 1 materials for FDA submission workflows; this task focuses on creating synthetic data that another AI/workstream can use later.
- Existing files in this folder:
  - `IND_HIVE_MVP.docx`
  - `IND_Module1_POC_Codex_Guideline.md`
- Awaiting source materials and the user's specific ideas before defining schemas, assumptions, and synthetic data outputs.
- Reviewed `IND_Module1_POC_Codex_Guideline.md` as the current implementation specification.
- Confirmed current folder has no existing application code and is not currently a git repository.
- Initial direction: build a small Python/Streamlit POC around canonical JSON synthetic cases, deterministic 1571/TOC/validation modules, and an isolated cover-letter generator interface.
- User approved the plan with changes:
  - Keep agent-visible synthetic source data separate from evaluation ground truth.
  - The agent must not directly consume expected canonical answers.
  - Add an explicit FDA 1571 field-mapping layer.
  - Persist generated outputs.
  - Create three golden cases first: clean, missing, and conflict.
  - Use LLM as the primary Cover Letter generation path, with deterministic templating only as fallback.
  - Initialize the folder as a git repository before implementation.
  - After the three golden cases run end-to-end, expand the dataset to 10 cases.
- Initialized the folder as a git repository.
- Implemented the POC with separate data layers:
  - `data/source_cases/` contains agent-visible synthetic source records.
  - `data/evaluation/golden_truth/` contains evaluation-only expected outputs for the three golden cases.
- Created three golden cases first:
  - `IND001`: clean
  - `IND002`: missing optional fields
  - `IND003`: conflicting sponsor name and protocol version
- Ran the three golden cases end-to-end and persisted outputs under `outputs/generated/<case_id>/`.
- Ran golden evaluation checks; `IND001`, `IND002`, and `IND003` passed.
- Expanded synthetic dataset to 10 fictional cases:
  - 5 clean: `IND001`, `IND004`, `IND005`, `IND006`, `IND007`
  - 2 missing: `IND002`, `IND008`
  - 2 conflict: `IND003`, `IND009`
  - 1 unusual formatting: `IND010`
- Implemented explicit deterministic FDA 1571 field mapping in `src/ind_m1_poc/form_1571.py`.
- Implemented LLM-first Cover Letter generation in `src/ind_m1_poc/cover_letter.py`; current local verification used deterministic fallback because `OPENAI_API_KEY` and the `openai` package are not configured in the bundled Python environment.
- Implemented package persistence with JSON and Markdown artifacts for each case.
- Added two UI paths:
  - `web_app.py`: no-dependency local demo server.
  - `app.py`: optional Streamlit UI.
- Verification completed:
  - Python compile check passed.
  - `evaluate_golden.py` passed for all three golden cases.
  - `run_poc.py --all` generated all 10 cases.
  - `web_app.py` responded with HTTP 200 at `http://127.0.0.1:8501/`.
