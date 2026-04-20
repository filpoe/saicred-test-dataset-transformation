from __future__ import annotations

import argparse
import difflib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from dataset_models import load_json, write_json


SIMILAR_PROMPT_THRESHOLD = 0.88
SIMILAR_PARENT_THRESHOLD = 0.82


def normalize_text(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def text_similarity(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, normalize_text(left), normalize_text(right)).ratio()


def parent_groups(rows: Sequence[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for row in rows:
        parent_id = row.get("parent_question_id")
        if isinstance(parent_id, int):
            grouped.setdefault(parent_id, []).append(row)
    return grouped


def parent_signature(rows: Sequence[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for row in sorted(rows, key=lambda item: str(item.get("question_id", ""))):
        ground_truth = row.get("ground_truth") or {}
        source = row.get("source") or {}
        parts.extend(
            [
                str(row.get("topic_domain", "")),
                str(row.get("prompt", "")),
                " ".join(map(str, ground_truth.get("required_elements") or [])),
                str(source.get("title", "")),
                str(source.get("reference", "")),
            ]
        )
        options = row.get("options")
        if isinstance(options, dict):
            parts.extend(str(options.get(key, "")) for key in sorted(options))
    return normalize_text(" ".join(parts))


def validate_redundancy(
    candidate_rows: Sequence[Dict[str, Any]],
    existing_datasets: Sequence[tuple[str, Sequence[Dict[str, Any]]]] = (),
) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []

    _check_internal_redundancy(candidate_rows, issues)
    for dataset_name, existing_rows in existing_datasets:
        _check_overlap_with_existing(candidate_rows, dataset_name, existing_rows, issues)

    return {
        "summary": {
            "candidate_rows_checked": len(candidate_rows),
            "existing_datasets_checked": len(existing_datasets),
            "errors": len([issue for issue in issues if issue["severity"] == "error"]),
            "warnings": len([issue for issue in issues if issue["severity"] == "warning"]),
        },
        "issues": issues,
    }


def _check_internal_redundancy(
    rows: Sequence[Dict[str, Any]],
    issues: List[Dict[str, Any]],
) -> None:
    grouped = parent_groups(rows)
    parent_items = list(grouped.items())
    for left_index, (left_parent, left_rows) in enumerate(parent_items):
        left_signature = parent_signature(left_rows)
        for right_parent, right_rows in parent_items[left_index + 1:]:
            similarity = text_similarity(left_signature, parent_signature(right_rows))
            if similarity >= SIMILAR_PARENT_THRESHOLD:
                issues.append(
                    {
                        "severity": "error",
                        "type": "internal_parent_overlap",
                        "parent_question_id": left_parent,
                        "overlapping_parent_question_id": right_parent,
                        "similarity": round(similarity, 3),
                        "message": "Two parent question groups appear to test the same doctrinal target.",
                    }
                )

    prompts: Dict[str, str] = {}
    for row in rows:
        question_id = str(row.get("question_id", ""))
        prompt = str(row.get("prompt", ""))
        normalized = normalize_text(prompt)
        if normalized in prompts:
            issues.append(
                {
                    "severity": "error",
                    "type": "internal_duplicate_prompt",
                    "question_id": question_id,
                    "overlapping_question_id": prompts[normalized],
                    "message": "Duplicate prompt text inside candidate dataset.",
                }
            )
        prompts[normalized] = question_id


def _check_overlap_with_existing(
    candidate_rows: Sequence[Dict[str, Any]],
    dataset_name: str,
    existing_rows: Sequence[Dict[str, Any]],
    issues: List[Dict[str, Any]],
) -> None:
    candidate_groups = parent_groups(candidate_rows)
    existing_groups = parent_groups(existing_rows)

    for candidate_parent, candidate_parent_rows in candidate_groups.items():
        candidate_signature = parent_signature(candidate_parent_rows)
        for existing_parent, existing_parent_rows in existing_groups.items():
            similarity = text_similarity(candidate_signature, parent_signature(existing_parent_rows))
            if similarity >= SIMILAR_PARENT_THRESHOLD:
                issues.append(
                    {
                        "severity": "error",
                        "type": "existing_parent_overlap",
                        "parent_question_id": candidate_parent,
                        "existing_dataset": dataset_name,
                        "existing_parent_question_id": existing_parent,
                        "similarity": round(similarity, 3),
                        "message": "Candidate parent group appears to overlap an existing dataset item.",
                    }
                )

    existing_prompts = [
        (str(row.get("question_id", "")), str(row.get("prompt", "")))
        for row in existing_rows
    ]
    for row in candidate_rows:
        question_id = str(row.get("question_id", ""))
        prompt = str(row.get("prompt", ""))
        for existing_question_id, existing_prompt in existing_prompts:
            similarity = text_similarity(prompt, existing_prompt)
            if similarity >= SIMILAR_PROMPT_THRESHOLD:
                issues.append(
                    {
                        "severity": "error",
                        "type": "existing_prompt_overlap",
                        "question_id": question_id,
                        "existing_dataset": dataset_name,
                        "existing_question_id": existing_question_id,
                        "similarity": round(similarity, 3),
                        "message": "Candidate prompt is too similar to an existing prompt.",
                    }
                )


def load_existing_datasets(paths: Iterable[Path]) -> List[tuple[str, Sequence[Dict[str, Any]]]]:
    datasets: List[tuple[str, Sequence[Dict[str, Any]]]] = []
    for path in paths:
        if not path.exists():
            continue
        data = load_json(path)
        if isinstance(data, list):
            datasets.append((path.name, data))
    return datasets


def discover_dataset_files(data_dir: Path, *, exclude: Path | None = None) -> List[Path]:
    exclude_resolved = exclude.resolve() if exclude and exclude.exists() else None
    paths = sorted(data_dir.glob("*.json"))
    if exclude_resolved is None:
        return paths
    return [path for path in paths if path.resolve() != exclude_resolved]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check a candidate dataset for duplicate or overlapping questions."
    )
    parser.add_argument("candidate", type=Path, help="Candidate dataset JSON file")
    parser.add_argument("--existing", action="append", type=Path, default=[], help="Existing dataset JSON file to compare against")
    parser.add_argument("--existing-dir", type=Path, help="Directory containing existing *.json files")
    parser.add_argument("--report", type=Path, help="Optional report path")
    args = parser.parse_args()

    candidate_rows = load_json(args.candidate)
    existing_paths = list(args.existing)
    if args.existing_dir:
        existing_paths.extend(discover_dataset_files(args.existing_dir, exclude=args.candidate))

    report = validate_redundancy(
        candidate_rows,
        load_existing_datasets(existing_paths),
    )
    if args.report:
        write_json(args.report, report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if report["summary"]["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
