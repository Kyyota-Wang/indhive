from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ind_m1_poc.evaluation import evaluate_golden_case  # noqa: E402


GOLDEN_CASES = ["IND001", "IND002", "IND003"]


def main() -> int:
    all_passed = True
    for case_id in GOLDEN_CASES:
        result = evaluate_golden_case(case_id)
        all_passed = all_passed and result["passed"]
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{case_id}: {status}")
        for check in result["canonical_checks"]:
            if not check["passed"]:
                print(
                    f"  {check['field']}: expected={check['expected']!r} actual={check['actual']!r}"
                )
        if not result["conflict_check"]["passed"]:
            print(
                "  conflicts: "
                f"expected={result['conflict_check']['expected']!r} "
                f"actual={result['conflict_check']['actual']!r}"
            )
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

