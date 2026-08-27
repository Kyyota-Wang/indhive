from __future__ import annotations

from pathlib import Path

# indkit/src/indkit/pipeline/paths.py  ->  parents[3] is the project folder.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = PROJECT_ROOT.parent

DATA_DIR = PROJECT_ROOT / "data"
SOURCE_CASES_DIR = DATA_DIR / "source_cases"
PARTNER_REFERENCE_DIR = DATA_DIR / "partner_reference"
GOLDEN_TRUTH_DIR = DATA_DIR / "evaluation" / "golden_truth"

OUTPUTS_DIR = PROJECT_ROOT / "out" / "cases"

# Shared with the rest of the repository, not owned by this project.
PARTNER_PACKAGE_DIR = REPO_ROOT / "inputs" / "partner-package" / "AI Inputs"
REPORTS_DIR = REPO_ROOT / "reports"
