from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from dataset_models import load_json, validate_dataset_schema, write_json
from validate_dataset_redundancy import (
    discover_dataset_files,
    load_existing_datasets,
    validate_redundancy,
)
from validate_doctrine_and_logic import validate_doctrine_and_logic


DATA_DIR = Path("data")
VALIDATION_DIR = Path("data_validation_results")


def ask_int(prompt: str) -> int:
    while True:
        value = input(prompt).strip()
        try:
            parsed = int(value)
        except ValueError:
            print("Please enter a whole number.")
            continue
        if parsed > 0:
            return parsed
        print("Please enter a number greater than zero.")


def ask_yes_no(prompt: str) -> bool:
    while True:
        value = input(f"{prompt} [y/n]: ").strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer y or n.")


def next_dataset_path(
    *,
    parent_count: int,
    today: Optional[str] = None,
) -> Path:
    if today is None:
        today = dt.date.today().isoformat()
    version = 1
    while True:
        candidate = DATA_DIR / f"saicred_eval_qa_{parent_count}_sample_{today}_v{version}.json"
        if not candidate.exists():
            return candidate
        version += 1


def validation_report_path(dataset_path: Path, validator: str) -> Path:
    stem = dataset_path.stem
    return VALIDATION_DIR / f"{stem}_{validator}_validation_results.json"


def parent_count(rows: Sequence[Dict[str, Any]]) -> int:
    return len({
        row.get("parent_question_id")
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("parent_question_id"), int)
    })


def renumber_dataset(
    rows: Sequence[Dict[str, Any]],
    *,
    start_parent_id: int = 1,
) -> List[Dict[str, Any]]:
    variant_suffixes = {
        "neutral": "1",
        "christian": "2",
        "catholic": "3",
        "adversarial": "4",
    }
    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for row in rows:
        old_parent_id = row.get("parent_question_id")
        if not isinstance(old_parent_id, int):
            continue
        grouped.setdefault(old_parent_id, []).append(dict(row))

    output: List[Dict[str, Any]] = []
    for offset, old_parent_id in enumerate(sorted(grouped), start=start_parent_id):
        for row in sorted(grouped[old_parent_id], key=lambda item: variant_suffixes.get(str(item.get("variant_type")), "9")):
            variant_type = row.get("variant_type")
            row["parent_question_id"] = offset
            row["question_id"] = f"{offset}.{variant_suffixes.get(variant_type, '0')}"
            output.append(row)
    return output


def run_workflow(
    *,
    draft_dataset: Path,
    parent_groups_to_generate: int,
    check_existing: bool,
    append_to: Optional[Path],
) -> Dict[str, Any]:
    DATA_DIR.mkdir(exist_ok=True)
    VALIDATION_DIR.mkdir(exist_ok=True)

    draft_rows = load_json(draft_dataset)
    if not isinstance(draft_rows, list):
        raise ValueError("Draft dataset must be a JSON array")

    standalone_rows = renumber_dataset(draft_rows)
    standalone_path = next_dataset_path(parent_count=parent_groups_to_generate)

    schema_report = validate_dataset_schema(
        standalone_rows,
        expected_parent_count=parent_groups_to_generate,
    )
    write_json(validation_report_path(standalone_path, "schema"), schema_report)
    if schema_report["summary"]["errors"]:
        raise SystemExit(
            f"Schema validation failed; see {validation_report_path(standalone_path, 'schema')}"
        )

    existing_datasets = []
    if check_existing:
        existing_paths = discover_dataset_files(DATA_DIR, exclude=draft_dataset)
        existing_datasets = load_existing_datasets(existing_paths)
    redundancy_report = validate_redundancy(standalone_rows, existing_datasets)
    write_json(validation_report_path(standalone_path, "redundancy"), redundancy_report)
    if redundancy_report["summary"]["errors"]:
        raise SystemExit(
            f"Redundancy validation failed; see {validation_report_path(standalone_path, 'redundancy')}"
        )

    fixed_rows, doctrine_report = validate_doctrine_and_logic(standalone_rows, auto_fix=True)
    write_json(validation_report_path(standalone_path, "doctrinal_logic"), doctrine_report)
    if doctrine_report["summary"]["errors"]:
        needs_review_path = standalone_path.with_name(standalone_path.stem + "_needs_review.json")
        write_json(needs_review_path, fixed_rows)
        raise SystemExit(
            f"Doctrinal validation failed; saved needs-review dataset to {needs_review_path}"
        )

    write_json(standalone_path, fixed_rows)

    cumulative_path: Optional[Path] = None
    if append_to is not None:
        base_rows = load_json(append_to)
        if not isinstance(base_rows, list):
            raise ValueError("Append target must be a JSON array")
        base_parent_count = parent_count(base_rows)
        appended_rows = list(base_rows) + renumber_dataset(
            fixed_rows,
            start_parent_id=base_parent_count + 1,
        )
        total_parent_count = parent_count(appended_rows)
        cumulative_path = next_dataset_path(parent_count=total_parent_count)
        cumulative_rows = renumber_dataset(appended_rows)

        cumulative_schema_report = validate_dataset_schema(
            cumulative_rows,
            expected_parent_count=total_parent_count,
        )
        write_json(validation_report_path(cumulative_path, "schema"), cumulative_schema_report)
        if cumulative_schema_report["summary"]["errors"]:
            raise SystemExit(
                f"Cumulative schema validation failed; see {validation_report_path(cumulative_path, 'schema')}"
            )

        cumulative_fixed_rows, cumulative_doctrine_report = validate_doctrine_and_logic(
            cumulative_rows,
            auto_fix=True,
        )
        write_json(validation_report_path(cumulative_path, "doctrinal_logic"), cumulative_doctrine_report)
        if cumulative_doctrine_report["summary"]["errors"]:
            needs_review_path = cumulative_path.with_name(cumulative_path.stem + "_needs_review.json")
            write_json(needs_review_path, cumulative_fixed_rows)
            raise SystemExit(
                f"Cumulative doctrinal validation failed; saved needs-review dataset to {needs_review_path}"
            )
        write_json(cumulative_path, cumulative_fixed_rows)

    return {
        "standalone_dataset": str(standalone_path),
        "cumulative_dataset": str(cumulative_path) if cumulative_path else None,
        "schema_report": str(validation_report_path(standalone_path, "schema")),
        "redundancy_report": str(validation_report_path(standalone_path, "redundancy")),
        "doctrinal_logic_report": str(validation_report_path(standalone_path, "doctrinal_logic")),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the SAICRED dataset workflow for an LLM-generated "
            "dataset draft JSON file."
        )
    )
    parser.add_argument(
        "--draft-dataset",
        type=Path,
        required=True,
        help="LLM-generated dataset draft JSON file to validate and save",
    )
    parser.add_argument(
        "--parent-groups",
        type=int,
        help="Number of new parent question groups expected in the draft",
    )
    parser.add_argument(
        "--check-existing",
        action="store_true",
        help="Check data/*.json for overlapping questions",
    )
    parser.add_argument(
        "--no-check-existing",
        action="store_true",
        help="Do not check data/*.json for overlapping questions",
    )
    parser.add_argument(
        "--append-to",
        type=Path,
        help="Existing cumulative *.json file to append to",
    )
    parser.add_argument(
        "--no-append",
        action="store_true",
        help="Do not append this dataset to a cumulative dataset",
    )
    args = parser.parse_args()

    parent_groups_to_generate = args.parent_groups
    if parent_groups_to_generate is None:
        parent_groups_to_generate = ask_int("How many new parent question groups should I generate? ")

    if args.check_existing and args.no_check_existing:
        raise SystemExit("Use only one of --check-existing or --no-check-existing")
    if args.check_existing:
        check_existing = True
    elif args.no_check_existing:
        check_existing = False
    else:
        check_existing = ask_yes_no("Should I check existing data/*.json files and avoid overlap?")

    if args.append_to is not None and args.no_append:
        raise SystemExit("Use only one of --append-to or --no-append")
    append_to = args.append_to
    if (
        append_to is None
        and not args.no_append
        and ask_yes_no("Should I append this new dataset to an existing cumulative dataset?")
    ):
        append_to = Path(input("Path to existing cumulative *.json file: ").strip())

    result = run_workflow(
        draft_dataset=args.draft_dataset,
        parent_groups_to_generate=parent_groups_to_generate,
        check_existing=check_existing,
        append_to=append_to,
    )
    print("Workflow completed:")
    for key, value in result.items():
        if value:
            print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
