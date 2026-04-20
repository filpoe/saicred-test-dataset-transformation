from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


VARIANT_SUFFIXES = {
    "neutral": "1",
    "christian": "2",
    "catholic": "3",
    "adversarial": "4",
}
VARIANT_TYPES = set(VARIANT_SUFFIXES)
OPTION_KEYS = {"A", "B", "C", "D"}
FORMATS = {"binary", "mcq"}
RISK_LEVELS = {"LOW", "MEDIUM", "HIGH"}
REQUIRED_SCORING_ANCHORS = {"score_5", "score_3", "score_1"}


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str
    severity: str = "error"

    def to_dict(self) -> Dict[str, str]:
        return {
            "path": self.path,
            "severity": self.severity,
            "message": self.message,
        }


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as input_file:
        return json.load(input_file)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output_file:
        json.dump(value, output_file, ensure_ascii=False, indent=2)
        output_file.write("\n")


def validate_dataset_schema(
    data: Any,
    *,
    expected_parent_count: Optional[int] = None,
) -> Dict[str, Any]:
    issues: List[ValidationIssue] = []
    if not isinstance(data, list):
        issues.append(ValidationIssue("$", "Dataset must be a JSON array"))
        return _report(0, 0, issues)

    for index, item in enumerate(data):
        _validate_dataset_row(item, f"$[{index}]", issues)

    _validate_parent_groups(data, issues)

    parent_ids = {
        item.get("parent_question_id")
        for item in data
        if isinstance(item, dict) and isinstance(item.get("parent_question_id"), int)
    }
    if expected_parent_count is not None and len(parent_ids) != expected_parent_count:
        issues.append(
            ValidationIssue(
                "$",
                f"Expected {expected_parent_count} parent question groups, found {len(parent_ids)}",
            )
        )

    return _report(len(data), len(parent_ids), issues)


def _validate_dataset_row(
    item: Any,
    path: str,
    issues: List[ValidationIssue],
) -> None:
    if not isinstance(item, dict):
        issues.append(ValidationIssue(path, "Each dataset row must be an object"))
        return

    question_id = _require_non_empty_str(item, "question_id", path, issues)
    parent_question_id = item.get("parent_question_id")
    if not isinstance(parent_question_id, int):
        issues.append(ValidationIssue(f"{path}.parent_question_id", "Must be an integer"))

    variant_type = item.get("variant_type")
    if variant_type not in VARIANT_TYPES:
        issues.append(
            ValidationIssue(
                f"{path}.variant_type",
                "Must be neutral, christian, catholic, or adversarial",
            )
        )

    if isinstance(question_id, str) and isinstance(parent_question_id, int) and variant_type in VARIANT_TYPES:
        expected_question_id = f"{parent_question_id}.{VARIANT_SUFFIXES[variant_type]}"
        if question_id != expected_question_id:
            issues.append(
                ValidationIssue(
                    f"{path}.question_id",
                    f"Expected {expected_question_id!r} from parent_question_id and variant_type",
                )
            )
        if not re.match(r"^\d+\.[1-4]$", question_id):
            issues.append(
                ValidationIssue(
                    f"{path}.question_id",
                    "Must use parent.variant form, e.g. 12.4",
                )
            )

    _require_non_empty_str(item, "use_case", path, issues)
    _require_non_empty_str(item, "use_case_label", path, issues)
    _require_non_empty_str(item, "topic_domain", path, issues)
    _require_non_empty_str(item, "prompt", path, issues)
    _require_non_empty_str(item, "source_type", path, issues)

    item_format = item.get("format")
    if item_format not in FORMATS:
        issues.append(ValidationIssue(f"{path}.format", "Must be binary or mcq"))

    risk_level = item.get("risk_level")
    if risk_level not in RISK_LEVELS:
        issues.append(ValidationIssue(f"{path}.risk_level", "Must be LOW, MEDIUM, or HIGH"))

    _validate_source(item.get("source"), f"{path}.source", issues)
    _validate_ground_truth(
        item.get("ground_truth"),
        f"{path}.ground_truth",
        item_format if isinstance(item_format, str) else None,
        item.get("options"),
        issues,
    )


def _validate_source(source: Any, path: str, issues: List[ValidationIssue]) -> None:
    if not isinstance(source, dict):
        issues.append(ValidationIssue(path, "Must be an object"))
        return
    _require_non_empty_str(source, "title", path, issues)
    url = _require_non_empty_str(source, "url", path, issues)
    _require_non_empty_str(source, "reference", path, issues)
    if isinstance(url, str) and "catholic.com" not in url.lower():
        issues.append(
            ValidationIssue(
                f"{path}.url",
                "Must reference Catholic Answers source material from catholic.com",
            )
        )
    catechism_references = source.get("catechism_references")
    if not isinstance(catechism_references, list) or not catechism_references:
        issues.append(
            ValidationIssue(
                f"{path}.catechism_references",
                "Must contain at least one CCC paragraph number or range",
            )
        )
    elif not all(isinstance(ref, str) and ref.strip() for ref in catechism_references):
        issues.append(
            ValidationIssue(
                f"{path}.catechism_references",
                "Every Catechism reference must be a non-empty string",
            )
        )


def _validate_ground_truth(
    ground_truth: Any,
    path: str,
    item_format: Optional[str],
    options: Any,
    issues: List[ValidationIssue],
) -> None:
    if not isinstance(ground_truth, dict):
        issues.append(ValidationIssue(path, "Must be an object"))
        return

    correct_answer = ground_truth.get("correct_answer")
    if item_format == "binary":
        if options is not None:
            issues.append(ValidationIssue(f"{path.rsplit('.', 1)[0]}.options", "Binary rows must use null options"))
        if correct_answer not in {"YES", "NO"}:
            issues.append(ValidationIssue(f"{path}.correct_answer", "Binary answer must be YES or NO"))
    elif item_format == "mcq":
        if not isinstance(options, dict) or set(options) != OPTION_KEYS:
            issues.append(ValidationIssue(f"{path.rsplit('.', 1)[0]}.options", "MCQ rows must contain options A-D"))
        elif not all(isinstance(options[key], str) and options[key].strip() for key in OPTION_KEYS):
            issues.append(ValidationIssue(f"{path.rsplit('.', 1)[0]}.options", "All MCQ options must be non-empty strings"))
        if correct_answer not in OPTION_KEYS:
            issues.append(ValidationIssue(f"{path}.correct_answer", "MCQ answer must be A, B, C, or D"))

    justification = _require_non_empty_str(ground_truth, "justification", path, issues)
    if isinstance(justification, str) and "CCC " not in justification:
        issues.append(
            ValidationIssue(
                f"{path}.justification",
                "Justification must include an explicit CCC reference, e.g. 'See CCC 1374-1377.'",
            )
        )

    for key in ("required_elements", "prohibited_moves"):
        value = ground_truth.get(key)
        if not isinstance(value, list):
            issues.append(ValidationIssue(f"{path}.{key}", "Must be a list"))
        elif not all(isinstance(item, str) and item.strip() for item in value):
            issues.append(ValidationIssue(f"{path}.{key}", "Must contain only non-empty strings"))

    scoring_anchors = ground_truth.get("scoring_anchors")
    if not isinstance(scoring_anchors, dict):
        issues.append(ValidationIssue(f"{path}.scoring_anchors", "Must be an object"))
    else:
        missing = REQUIRED_SCORING_ANCHORS - set(scoring_anchors)
        if missing:
            issues.append(
                ValidationIssue(
                    f"{path}.scoring_anchors",
                    f"Missing scoring anchors: {', '.join(sorted(missing))}",
                )
            )
        for key in REQUIRED_SCORING_ANCHORS & set(scoring_anchors):
            if not isinstance(scoring_anchors.get(key), str) or not scoring_anchors[key].strip():
                issues.append(ValidationIssue(f"{path}.scoring_anchors.{key}", "Must be a non-empty string"))


def _validate_parent_groups(data: Sequence[Any], issues: List[ValidationIssue]) -> None:
    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("parent_question_id"), int):
            grouped.setdefault(item["parent_question_id"], []).append(item)

    for parent_id, rows in grouped.items():
        path = f"parent_question_id={parent_id}"
        if len(rows) != 4:
            issues.append(ValidationIssue(path, "Each parent group must contain exactly four rows"))
        variants = [row.get("variant_type") for row in rows]
        if set(variants) != VARIANT_TYPES:
            issues.append(ValidationIssue(path, "Each parent group must include neutral, christian, catholic, and adversarial variants"))
        formats = {row.get("format") for row in rows}
        if len(formats) != 1:
            issues.append(ValidationIssue(path, "All variants in a parent group must share the same format"))


def _require_non_empty_str(
    mapping: Dict[str, Any],
    key: str,
    path: str,
    issues: List[ValidationIssue],
) -> Optional[str]:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        issues.append(ValidationIssue(f"{path}.{key}", "Must be a non-empty string"))
        return None
    return value


def _report(row_count: int, parent_group_count: int, issues: Sequence[ValidationIssue]) -> Dict[str, Any]:
    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]
    return {
        "summary": {
            "rows_checked": row_count,
            "parent_groups_checked": parent_group_count,
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "issues": [issue.to_dict() for issue in issues],
    }
