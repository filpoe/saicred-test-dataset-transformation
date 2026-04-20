from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence

from dataset_models import load_json, write_json
from validate_against_catechism import (
    enrich_dataset_with_catechism_references,
    validate_dataset as validate_against_catechism,
)


NEGATIVE_FRAMING_PATTERNS = (
    r"\bisn'?t\b",
    r"\bshould(n't| not)?\b.*\bonly\b.*\bwithout\b",
    r"\bdoes that mean\b",
    r"\bjust\b.*\brather than\b",
    r"\bmerely\b",
)


def validate_doctrine_and_logic(
    rows: Sequence[Dict[str, Any]],
    *,
    auto_fix: bool = True,
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    working_rows: List[Dict[str, Any]] = json.loads(json.dumps(list(rows)))
    auto_fix_summary: Dict[str, Any] = {
        "enabled": auto_fix,
        "items_enriched": 0,
        "justifications_enriched": 0,
    }

    if auto_fix:
        working_rows, enrich_summary = enrich_dataset_with_catechism_references(working_rows)
        auto_fix_summary.update(enrich_summary)

    issues: List[Dict[str, Any]] = []
    catechism_report = validate_against_catechism(working_rows, require_explicit_refs=True)
    for item in catechism_report["items"]:
        for error in item["errors"]:
            issues.append(
                {
                    "severity": "error",
                    "type": "catechism_validation",
                    "question_id": item["record_id"],
                    "message": error,
                }
            )
        for warning in item["warnings"]:
            issues.append(
                {
                    "severity": "warning",
                    "type": "catechism_validation",
                    "question_id": item["record_id"],
                    "message": warning,
                }
            )

    for row in working_rows:
        _validate_row_logic(row, issues)

    report = {
        "summary": {
            "rows_checked": len(working_rows),
            "errors": len([issue for issue in issues if issue["severity"] == "error"]),
            "warnings": len([issue for issue in issues if issue["severity"] == "warning"]),
            "auto_fix": auto_fix_summary,
        },
        "issues": issues,
        "catechism_summary": catechism_report["summary"],
    }
    return working_rows, report


def _validate_row_logic(row: Dict[str, Any], issues: List[Dict[str, Any]]) -> None:
    question_id = str(row.get("question_id", ""))
    row_format = row.get("format")
    prompt = str(row.get("prompt", ""))
    ground_truth = row.get("ground_truth") or {}
    correct_answer = ground_truth.get("correct_answer")
    justification = str(ground_truth.get("justification", ""))

    if row_format == "mcq":
        options = row.get("options")
        if isinstance(options, dict) and correct_answer in options:
            correct_option = str(options[correct_answer])
            if not _shares_required_term(correct_option, ground_truth):
                issues.append(
                    {
                        "severity": "warning",
                        "type": "mcq_correct_option_support",
                        "question_id": question_id,
                        "message": "Correct MCQ option does not clearly share terms with required_elements.",
                    }
                )
            if correct_option.lower() not in justification.lower() and not _shares_keyword(correct_option, justification):
                issues.append(
                    {
                        "severity": "warning",
                        "type": "mcq_justification_alignment",
                        "question_id": question_id,
                        "message": "Justification may not clearly explain the selected MCQ option.",
                    }
                )

    if row_format == "binary" and correct_answer == "YES" and _has_negative_framing(prompt):
        issues.append(
            {
                "severity": "warning",
                "type": "answer_polarity_review",
                "question_id": question_id,
                "message": "Binary YES answer appears with negative or adversarial wording; verify the prompt does not invert the proposition.",
            }
        )

    if "CCC " not in justification:
        issues.append(
            {
                "severity": "error",
                "type": "missing_ccc_reference",
                "question_id": question_id,
                "message": "Ground truth justification must include explicit CCC references.",
            }
        )


def _has_negative_framing(prompt: str) -> bool:
    normalized = prompt.lower()
    return any(re.search(pattern, normalized) for pattern in NEGATIVE_FRAMING_PATTERNS)


def _shares_required_term(option: str, ground_truth: Dict[str, Any]) -> bool:
    option_words = set(_content_words(option))
    required_text = " ".join(map(str, ground_truth.get("required_elements") or []))
    required_words = set(_content_words(required_text))
    return bool(option_words & required_words)


def _shares_keyword(left: str, right: str) -> bool:
    return bool(set(_content_words(left)) & set(_content_words(right)))


def _content_words(text: str) -> List[str]:
    stop_words = {
        "the", "and", "or", "but", "while", "with", "without", "they", "their",
        "this", "that", "from", "into", "only", "just", "a", "an", "of", "to",
        "in", "is", "are", "be", "become", "becomes", "remain", "remains",
    }
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    return [word for word in words if word not in stop_words]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate dataset dataset rows for doctrinal and logical consistency."
    )
    parser.add_argument("dataset", type=Path, help="Dataset dataset JSON file")
    parser.add_argument("--report", type=Path, help="Optional report path")
    parser.add_argument(
        "--auto-fix-output",
        type=Path,
        help="Write an auto-fixed dataset copy with CCC references enriched.",
    )
    parser.add_argument(
        "--no-auto-fix",
        action="store_true",
        help="Disable automatic CCC-reference enrichment.",
    )
    args = parser.parse_args()

    rows = load_json(args.dataset)
    fixed_rows, report = validate_doctrine_and_logic(
        rows,
        auto_fix=not args.no_auto_fix,
    )

    if args.auto_fix_output:
        write_json(args.auto_fix_output, fixed_rows)
    if args.report:
        write_json(args.report, report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if report["summary"]["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
