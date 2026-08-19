from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SOURCE_CASES_DIR = DATA_DIR / "source_cases"
GOLDEN_TRUTH_DIR = DATA_DIR / "evaluation" / "golden_truth"
OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "generated"

