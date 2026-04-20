from __future__ import annotations

import argparse
from pathlib import Path

from dataset_models import load_json, validate_dataset_schema, write_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a SAICRED dataset with strict schema rules."
    )
    parser.add_argument("dataset", type=Path, help="Dataset JSON file")
    parser.add_argument("--report", type=Path, help="Optional validation report path")
    parser.add_argument(
        "--expected-parent-count",
        type=int,
        help="Expected number of parent question groups",
    )
    args = parser.parse_args()

    data = load_json(args.dataset)
    report = validate_dataset_schema(
        data,
        expected_parent_count=args.expected_parent_count,
    )

    if args.report:
        write_json(args.report, report)
    else:
        write_json(Path("/dev/stdout"), report)

    if report["summary"]["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
