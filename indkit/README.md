# indkit

Python behind INDHIVE. Two things live here, and they are different jobs.

**`pipeline`** — the deterministic Module 1 engine. Source records in, canonical
record out, then Form FDA 1571, the Module 1 gap analysis, section 1.20, the
validation report and the partner-comparison views. This is the only
implementation of that logic; the web app ships its output as a build artifact.

**`docgen`** — the authored IND document. Assembles a Word file across Modules 1
to 5 with cited facts, IRIS comments carrying assumptions, and blue placeholders
where a fact is not available.

## Layout

```
indkit/
├── src/indkit/
│   ├── pipeline/     canonical model, 1571, TOC, 1.20, validation, comparisons
│   └── docgen/       Word document construction
├── scripts/          command-line entry points
├── data/             synthetic source cases, schemas, golden truth
└── out/              generated artifacts (git-ignored)
    └── cases/
```

Inputs supplied by the partner live outside this project at `../inputs/`, and
delivered documents at `../reports/`. Neither is owned by this package;
`pipeline/paths.py` names both.

## Running

```bash
cd indkit
pip install -r requirements.txt

python scripts/run_pipeline.py --all          # regenerate every case
python scripts/run_pipeline.py --case PMX103  # one case
python scripts/evaluate_golden.py             # golden-case checks
python scripts/build_ind_document.py          # author the IND Word document
python scripts/scan_invariants.py             # invariant scan across dossiers
python scripts/tamper_demo.py                 # alter one number, prove the scan catches it
```

After changing pipeline logic or case data, refresh the web app's bundle:

```bash
cd ../V1 && python build/bundle_cases.py
```
