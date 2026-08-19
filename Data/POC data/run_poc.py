from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ind_m1_poc.loader import list_cases  # noqa: E402
from ind_m1_poc.orchestrator import generate_module1_package  # noqa: E402
from ind_m1_poc.paths import OUTPUTS_DIR  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate IND Module 1 POC packages.")
    parser.add_argument("--case", help="Case ID to generate, for example IND001.")
    parser.add_argument("--all", action="store_true", help="Generate packages for all source cases.")
    parser.add_argument("--no-llm", action="store_true", help="Use deterministic cover-letter fallback.")
    args = parser.parse_args()

    case_ids = [case["case_id"] for case in list_cases()] if args.all else [args.case]
    if not case_ids or not case_ids[0]:
        parser.error("Specify --case IND001 or --all.")

    for case_id in case_ids:
        package = generate_module1_package(case_id, use_llm=not args.no_llm)
        summary = package["validation"]["summary"]
        method = package["cover_letter"]["generation_method"]
        print(
            f"{case_id}: generated in {OUTPUTS_DIR / case_id} "
            f"| cover={method} | validation={summary}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

