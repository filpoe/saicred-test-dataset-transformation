from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


CATEGORY_TO_RISK = {
    "Moral Theology & Sin": "HIGH",
    "Sacramental Theology": "HIGH",
    "Salvation & Grace (Soteriology)": "MEDIUM",
    "Scripture & Interpretation": "MEDIUM",
    "Church Authority & Ecclesiology": "HIGH",
    "Apologetics & Objection Handling": "MEDIUM",
    "Eschatology (Last Things)": "MEDIUM",
}

VARIANT_MAP = {
    "question_neutral": ("1", "neutral"),
    "question_christian": ("2", "christian"),
    "question_catholic": ("3", "catholic"),
    "question_adversarial": ("4", "adversarial"),
}


def convert_intermediate_to_final(
    intermediate_items: List[Dict[str, Any]],
    *,
    default_source_type: str = "qa",
    risk_by_category: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Convert a list of intermediate benchmark items into the final flat schema.

    Input schema source:
      intermediate-test-dataset-format-(q-and-a)-v2 :contentReference[oaicite:2]{index=2}

    Output schema target:
      test-dataset-(Q&A)-format :contentReference[oaicite:3]{index=3}

    Assumptions:
    - Each intermediate item becomes 4 output items:
      neutral, christian, catholic, adversarial.
    - Parent question numbering starts at 1 in input order: K = 1, 2, 3, ...
    - For yes/no questions:
        * final format = "binary"
        * correct_answer = "YES" or "NO", preferably from variant_ground_truth
        * options = omitted (set to None)
    - For multiple-choice questions:
        * final format = "mcq"
        * if answers.options is present, options map directly from A-D and
          correct_answer comes from variant_ground_truth or answers.correct.
        * otherwise, legacy answers.correct maps to A and
          answers.incorrect[0..2] map to B, C, D.
    - variant_ground_truth can provide variant-specific correct answers and
      scoring metadata. If absent, the legacy shared ground_truth object is used.
    - risk_level is inferred from category name unless overridden.
    - topic_domain is taken from category.name.
    - source_type is not present in the intermediate schema, so it is filled
      with default_source_type ("qa" by default).
    """
    if risk_by_category is None:
        risk_by_category = CATEGORY_TO_RISK

    final_items: List[Dict[str, Any]] = []

    for idx, item in enumerate(intermediate_items, start=1):
        parent_question_id = idx

        questions = item.get("questions", {})
        q_type = item.get("type")
        category = item.get("category", {})
        use_case = item.get("use_case", {})
        answers = item.get("answers", {})
        shared_ground_truth = item.get("ground_truth", {})

        category_name = category.get("name", "")
        risk_level = risk_by_category.get(category_name, "MEDIUM")

        final_format = _map_format(q_type)

        options = _build_options(q_type, answers)

        for variant_key, (variant_suffix, variant_type) in VARIANT_MAP.items():
            prompt = questions.get(variant_key)
            if not prompt:
                raise ValueError(
                    f"Missing question variant '{variant_key}' for item #{idx}"
                )

            variant_ground_truth = _get_variant_ground_truth(
                item,
                variant_key,
                shared_ground_truth,
            )
            correct_answer = _build_correct_answer(
                q_type,
                answers,
                variant_ground_truth,
                has_labeled_options=isinstance(answers.get("options"), dict),
            )
            scoring_anchors = _ground_truth_value(
                variant_ground_truth,
                shared_ground_truth,
                "scoring_anchors",
                {},
            )

            final_item = {
                "question_id": f"{parent_question_id}.{variant_suffix}",
                "parent_question_id": parent_question_id,
                "variant_type": variant_type,
                "use_case": use_case.get("id"),
                "use_case_label": use_case.get("label"),
                "format": final_format,
                "risk_level": risk_level,
                "topic_domain": category_name,
                "prompt": prompt,
                "options": options,
                "source_type": default_source_type,
                "ground_truth": {
                    "correct_answer": correct_answer,
                    "justification": _ground_truth_value(
                        variant_ground_truth,
                        shared_ground_truth,
                        "justification",
                    ),
                    "required_elements": _ground_truth_value(
                        variant_ground_truth,
                        shared_ground_truth,
                        "required_elements",
                        [],
                    ),
                    "prohibited_moves": _ground_truth_value(
                        variant_ground_truth,
                        shared_ground_truth,
                        "prohibited_moves",
                        [],
                    ),
                    "scoring_anchors": {
                        "score_5": scoring_anchors.get("score_5"),
                        "score_3": scoring_anchors.get("score_3"),
                        "score_1": scoring_anchors.get("score_1"),
                    },
                },
            }

            final_items.append(final_item)

    return final_items


def _map_format(q_type: Optional[str]) -> str:
    if q_type == "yes_no":
        return "binary"
    if q_type == "multiple_choice":
        return "mcq"
    raise ValueError(f"Unsupported question type: {q_type!r}")


def _get_variant_ground_truth(
    item: Dict[str, Any],
    variant_key: str,
    shared_ground_truth: Dict[str, Any],
) -> Dict[str, Any]:
    variant_ground_truth = item.get("variant_ground_truth", {})
    if isinstance(variant_ground_truth, dict):
        value = variant_ground_truth.get(variant_key)
        if isinstance(value, dict):
            return value
    return shared_ground_truth


def _ground_truth_value(
    variant_ground_truth: Dict[str, Any],
    shared_ground_truth: Dict[str, Any],
    key: str,
    default: Any = None,
) -> Any:
    if key in variant_ground_truth:
        return variant_ground_truth.get(key)
    return shared_ground_truth.get(key, default)


def _build_correct_answer(
    q_type: Optional[str],
    answers: Dict[str, Any],
    variant_ground_truth: Dict[str, Any],
    *,
    has_labeled_options: bool,
) -> str:
    variant_correct = variant_ground_truth.get("correct_answer")
    correct = variant_correct if variant_correct is not None else answers.get("correct")

    if q_type == "yes_no":
        if not isinstance(correct, str) or not correct.strip():
            raise ValueError(
                "For yes_no items, variant_ground_truth.correct_answer must be 'YES' or 'NO'"
            )
        normalized = _normalize_yes_no_answer(correct)
        if normalized not in {"YES", "NO"}:
            raise ValueError(
                "For yes_no items, answers.correct must be 'YES'/'NO' or start with 'Yes,'/'No,'"
            )
        return normalized

    if q_type == "multiple_choice":
        if has_labeled_options:
            if not isinstance(correct, str) or correct.strip().upper() not in {"A", "B", "C", "D"}:
                raise ValueError(
                    "For multiple_choice items with answers.options, correct_answer must be A, B, C, or D"
                )
            return correct.strip().upper()
        return "A"

    raise ValueError(f"Unsupported question type: {q_type!r}")


def _normalize_yes_no_answer(answer: str) -> str:
    normalized = answer.strip().upper()
    if normalized in {"YES", "NO"}:
        return normalized
    if normalized.startswith("YES,") or normalized.startswith("YES."):
        return "YES"
    if normalized.startswith("NO,") or normalized.startswith("NO."):
        return "NO"
    return normalized


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transform intermediate SAICRED benchmark JSON into final flat JSON."
    )
    parser.add_argument("input", type=Path, help="Intermediate-format input JSON file")
    parser.add_argument("output", type=Path, help="Final-format output JSON file")
    args = parser.parse_args()

    with args.input.open(encoding="utf-8") as input_file:
        intermediate_items = json.load(input_file)

    final_items = convert_intermediate_to_final(intermediate_items)

    with args.output.open("w", encoding="utf-8") as output_file:
        json.dump(final_items, output_file, ensure_ascii=False, indent=2)
        output_file.write("\n")


def _build_options(
    q_type: Optional[str],
    answers: Dict[str, Any]
) -> Optional[Dict[str, str]]:
    if q_type == "yes_no":
        return None

    if q_type == "multiple_choice":
        labeled_options = answers.get("options")
        if isinstance(labeled_options, dict):
            option_keys = {"A", "B", "C", "D"}
            if set(labeled_options.keys()) != option_keys:
                raise ValueError(
                    "For multiple_choice items, answers.options must contain A, B, C, and D"
                )
            correct_key = answers.get("correct")
            if not isinstance(correct_key, str) or correct_key.strip().upper() not in option_keys:
                raise ValueError(
                    "For multiple_choice items, answers.correct must be A, B, C, or D"
                )
            incorrect_keys = answers.get("incorrect", [])
            if (
                not isinstance(incorrect_keys, list)
                or len(incorrect_keys) != 3
                or {str(key).strip().upper() for key in incorrect_keys}
                != option_keys - {correct_key.strip().upper()}
            ):
                raise ValueError(
                    "For multiple_choice items, answers.incorrect must contain the three incorrect option letters"
                )
            for key in sorted(option_keys):
                value = labeled_options.get(key)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"For multiple_choice items, answers.options.{key} must be a non-empty string"
                    )
            return {
                "A": labeled_options["A"],
                "B": labeled_options["B"],
                "C": labeled_options["C"],
                "D": labeled_options["D"],
            }

        correct = answers.get("correct")
        incorrect = answers.get("incorrect", [])

        if not isinstance(correct, str) or not correct.strip():
            raise ValueError(
                "For multiple_choice items, answers.correct must be a non-empty string"
            )

        if not isinstance(incorrect, list) or len(incorrect) != 3:
            raise ValueError(
                "For multiple_choice items, answers.incorrect must contain exactly 3 items"
            )

        return {
            "A": correct,
            "B": incorrect[0],
            "C": incorrect[1],
            "D": incorrect[2],
        }

    raise ValueError(f"Unsupported question type: {q_type!r}")


if __name__ == "__main__":
    main()
