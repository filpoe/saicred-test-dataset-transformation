from __future__ import annotations

import argparse
import json
import re
import tempfile
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


VARIANT_KEYS = (
    "question_neutral",
    "question_christian",
    "question_catholic",
    "question_adversarial",
)
OPTION_KEYS = {"A", "B", "C", "D"}
QUESTION_TYPES = {"yes_no", "multiple_choice"}
SIMILARITY_THRESHOLD = 0.88


class AppendValidationError(ValueError):
    """Raised when a generated batch should not be appended."""


def append_batch(
    existing_items: Sequence[Dict[str, Any]],
    batch_items: Sequence[Dict[str, Any]],
    *,
    similarity_threshold: float = SIMILARITY_THRESHOLD,
) -> List[Dict[str, Any]]:
    validate_items(existing_items, "existing")
    validate_items(batch_items, "batch")
    validate_no_duplicates(
        existing_items,
        batch_items,
        similarity_threshold=similarity_threshold,
    )
    return list(existing_items) + list(batch_items)


def validate_items(items: Sequence[Dict[str, Any]], label: str) -> None:
    if not isinstance(items, list):
        raise AppendValidationError(f"{label} data must be a JSON array")

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise AppendValidationError(f"{label} item #{index} must be an object")

        questions = item.get("questions")
        if not isinstance(questions, dict):
            raise AppendValidationError(f"{label} item #{index} questions must be an object")
        for variant_key in VARIANT_KEYS:
            value = questions.get(variant_key)
            if not isinstance(value, str) or not value.strip():
                raise AppendValidationError(
                    f"{label} item #{index} questions.{variant_key} must be a non-empty string"
                )

        question_type = item.get("type")
        if question_type not in QUESTION_TYPES:
            raise AppendValidationError(
                f"{label} item #{index} type must be yes_no or multiple_choice"
            )

        _validate_category(item, label, index)
        _validate_use_case(item, label, index)
        _validate_answers(item, question_type, label, index)
        _validate_variant_ground_truth(item, question_type, label, index)
        _validate_source(item, label, index)


def validate_no_duplicates(
    existing_items: Sequence[Dict[str, Any]],
    batch_items: Sequence[Dict[str, Any]],
    *,
    similarity_threshold: float = SIMILARITY_THRESHOLD,
) -> None:
    seen: List[Tuple[str, int, Dict[str, Any]]] = [
        ("existing", index, item) for index, item in enumerate(existing_items, start=1)
    ]

    for batch_index, batch_item in enumerate(batch_items, start=1):
        for group, other_index, other_item in seen:
            duplicate_reason = _duplicate_reason(
                batch_item,
                other_item,
                similarity_threshold=similarity_threshold,
            )
            if duplicate_reason:
                raise AppendValidationError(
                    "Duplicate or near-duplicate item detected: "
                    f"batch item #{batch_index} conflicts with {group} item #{other_index}. "
                    f"{duplicate_reason}"
                )
        seen.append(("batch", batch_index, batch_item))


def load_json_array(path: Path, label: str) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as input_file:
        data = json.load(input_file)
    if not isinstance(data, list):
        raise AppendValidationError(f"{label} file must contain a JSON array: {path}")
    return data


def write_json_array(path: Path, items: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as tmp_file:
        json.dump(list(items), tmp_file, ensure_ascii=False, indent=2)
        tmp_file.write("\n")
        tmp_path = Path(tmp_file.name)
    tmp_path.replace(path)


def _validate_category(item: Dict[str, Any], label: str, index: int) -> None:
    category = item.get("category")
    if not isinstance(category, dict):
        raise AppendValidationError(f"{label} item #{index} category must be an object")
    if not _non_empty_string(category.get("name")):
        raise AppendValidationError(f"{label} item #{index} category.name is required")
    failure_modes = category.get("failure_modes")
    if not isinstance(failure_modes, list) or not failure_modes:
        raise AppendValidationError(
            f"{label} item #{index} category.failure_modes must be a non-empty list"
        )


def _validate_use_case(item: Dict[str, Any], label: str, index: int) -> None:
    use_case = item.get("use_case")
    if not isinstance(use_case, dict):
        raise AppendValidationError(f"{label} item #{index} use_case must be an object")
    if not _non_empty_string(use_case.get("id")):
        raise AppendValidationError(f"{label} item #{index} use_case.id is required")
    if not _non_empty_string(use_case.get("label")):
        raise AppendValidationError(f"{label} item #{index} use_case.label is required")


def _validate_answers(
    item: Dict[str, Any],
    question_type: str,
    label: str,
    index: int,
) -> None:
    answers = item.get("answers")
    if not isinstance(answers, dict):
        raise AppendValidationError(f"{label} item #{index} answers must be an object")

    if question_type == "yes_no":
        if answers.get("correct") is not None:
            raise AppendValidationError(
                f"{label} item #{index} yes_no answers.correct must be null"
            )
        if answers.get("incorrect") != []:
            raise AppendValidationError(
                f"{label} item #{index} yes_no answers.incorrect must be []"
            )
        options = answers.get("options")
        if options not in (None, {}):
            raise AppendValidationError(
                f"{label} item #{index} yes_no answers.options must be absent, null, or empty"
            )
        return

    options = answers.get("options")
    if not isinstance(options, dict) or set(options) != OPTION_KEYS:
        raise AppendValidationError(
            f"{label} item #{index} multiple_choice answers.options must contain A-D"
        )
    for option_key in OPTION_KEYS:
        if not _non_empty_string(options.get(option_key)):
            raise AppendValidationError(
                f"{label} item #{index} answers.options.{option_key} is required"
            )

    correct = answers.get("correct")
    if correct not in OPTION_KEYS:
        raise AppendValidationError(
            f"{label} item #{index} multiple_choice answers.correct must be A-D"
        )
    incorrect = answers.get("incorrect")
    if not isinstance(incorrect, list) or set(incorrect) != OPTION_KEYS - {correct}:
        raise AppendValidationError(
            f"{label} item #{index} answers.incorrect must contain the three incorrect letters"
        )


def _validate_variant_ground_truth(
    item: Dict[str, Any],
    question_type: str,
    label: str,
    index: int,
) -> None:
    variant_ground_truth = item.get("variant_ground_truth")
    if not isinstance(variant_ground_truth, dict):
        raise AppendValidationError(
            f"{label} item #{index} variant_ground_truth must be an object"
        )

    valid_answers = {"YES", "NO"} if question_type == "yes_no" else OPTION_KEYS
    for variant_key in VARIANT_KEYS:
        value = variant_ground_truth.get(variant_key)
        if not isinstance(value, dict):
            raise AppendValidationError(
                f"{label} item #{index} variant_ground_truth.{variant_key} must be an object"
            )
        if value.get("correct_answer") not in valid_answers:
            raise AppendValidationError(
                f"{label} item #{index} variant_ground_truth.{variant_key}.correct_answer is invalid"
            )
        for text_key in ("justification",):
            if not _non_empty_string(value.get(text_key)):
                raise AppendValidationError(
                    f"{label} item #{index} variant_ground_truth.{variant_key}.{text_key} is required"
                )
        for list_key in ("required_elements", "prohibited_moves"):
            if not isinstance(value.get(list_key), list) or not value[list_key]:
                raise AppendValidationError(
                    f"{label} item #{index} variant_ground_truth.{variant_key}.{list_key} must be a non-empty list"
                )
        scoring_anchors = value.get("scoring_anchors")
        if not isinstance(scoring_anchors, dict):
            raise AppendValidationError(
                f"{label} item #{index} variant_ground_truth.{variant_key}.scoring_anchors must be an object"
            )
        for score_key in ("score_5", "score_3", "score_1"):
            if not _non_empty_string(scoring_anchors.get(score_key)):
                raise AppendValidationError(
                    f"{label} item #{index} variant_ground_truth.{variant_key}.scoring_anchors.{score_key} is required"
                )


def _validate_source(item: Dict[str, Any], label: str, index: int) -> None:
    source = item.get("source")
    if not isinstance(source, dict):
        raise AppendValidationError(f"{label} item #{index} source must be an object")
    for key in ("title", "url", "reference"):
        if not _non_empty_string(source.get(key)):
            raise AppendValidationError(f"{label} item #{index} source.{key} is required")
    if "catholic.com" not in source["url"]:
        raise AppendValidationError(
            f"{label} item #{index} source.url must point to catholic.com"
        )


def _duplicate_reason(
    left: Dict[str, Any],
    right: Dict[str, Any],
    *,
    similarity_threshold: float,
) -> Optional[str]:
    left_questions = _question_texts(left)
    right_questions = _question_texts(right)

    if set(left_questions) & set(right_questions):
        return "At least one question variant is an exact duplicate."

    left_neutral = _normalized_question(left, "question_neutral")
    right_neutral = _normalized_question(right, "question_neutral")
    neutral_similarity = SequenceMatcher(None, left_neutral, right_neutral).ratio()
    if neutral_similarity >= similarity_threshold:
        return f"Neutral questions are {neutral_similarity:.0%} similar."

    left_signature = _doctrinal_signature(left)
    right_signature = _doctrinal_signature(right)
    signature_similarity = SequenceMatcher(None, left_signature, right_signature).ratio()
    same_category = left.get("category", {}).get("name") == right.get("category", {}).get("name")
    if same_category and signature_similarity >= similarity_threshold:
        return f"Doctrinal signatures are {signature_similarity:.0%} similar."

    return None


def _question_texts(item: Dict[str, Any]) -> List[str]:
    return [_normalized_question(item, variant_key) for variant_key in VARIANT_KEYS]


def _normalized_question(item: Dict[str, Any], variant_key: str) -> str:
    return _normalize_text(item.get("questions", {}).get(variant_key, ""))


def _doctrinal_signature(item: Dict[str, Any]) -> str:
    source = item.get("source", {})
    first_truth = item.get("variant_ground_truth", {}).get("question_neutral", {})
    parts: Iterable[str] = (
        item.get("category", {}).get("name", ""),
        source.get("title", ""),
        source.get("reference", ""),
        " ".join(first_truth.get("required_elements", [])),
        first_truth.get("justification", ""),
    )
    return _normalize_text(" ".join(parts))


def _normalize_text(value: str) -> str:
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate and append a generated intermediate JSON batch."
    )
    parser.add_argument("existing", type=Path, help="Current accumulated intermediate JSON")
    parser.add_argument("batch", type=Path, help="New generated intermediate batch JSON")
    parser.add_argument("output", type=Path, help="Output path for the appended intermediate JSON")
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=SIMILARITY_THRESHOLD,
        help="Near-duplicate threshold from 0.0 to 1.0; default: 0.88",
    )
    parser.add_argument(
        "--expected-total",
        type=int,
        help="Optional expected item count after appending",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report counts without writing output",
    )
    args = parser.parse_args()

    try:
        existing_items = load_json_array(args.existing, "existing")
        batch_items = load_json_array(args.batch, "batch")
        appended_items = append_batch(
            existing_items,
            batch_items,
            similarity_threshold=args.similarity_threshold,
        )
        if args.expected_total is not None and len(appended_items) != args.expected_total:
            raise AppendValidationError(
                f"Expected {args.expected_total} total items, got {len(appended_items)}"
            )
        if not args.dry_run:
            write_json_array(args.output, appended_items)
    except (AppendValidationError, json.JSONDecodeError) as error:
        raise SystemExit(f"ERROR: {error}") from error

    action = "Validated" if args.dry_run else "Appended"
    print(
        f"{action} {len(batch_items)} batch items to {len(existing_items)} existing items; "
        f"total: {len(appended_items)}"
    )


if __name__ == "__main__":
    main()
