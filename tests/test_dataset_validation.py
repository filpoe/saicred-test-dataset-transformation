from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from transform_intermediate_to_final import convert_intermediate_to_final  # noqa: E402


VARIANT_KEYS = [
    "question_neutral",
    "question_christian",
    "question_catholic",
    "question_adversarial",
]
VARIANT_TYPES = {"neutral", "christian", "catholic", "adversarial"}
OPTION_KEYS = {"A", "B", "C", "D"}

EXPECTED_DOCTRINAL_REVIEW = {
    1: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Sacramental Theology",
        "required_terms": ["real presence", "body and blood", "substance"],
    },
    2: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Sacramental Theology",
        "required_terms": ["infant baptism", "original sin", "sacramental grace"],
    },
    3: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Sacramental Theology",
        "required_terms": ["christ", "authority", "forgiveness of sins"],
    },
    4: {
        "format": "mcq",
        "answer": "A",
        "topic_domain": "Eschatology (Last Things)",
        "required_terms": ["final purification", "god's grace", "heaven"],
    },
    5: {
        "format": "binary",
        "answer": "NO",
        "topic_domain": "Scripture & Interpretation",
        "required_terms": ["scripture", "sacred tradition", "magisterium"],
    },
    6: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Church Authority & Ecclesiology",
        "required_terms": ["peter", "primacy", "papacy"],
    },
    7: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Moral Theology & Sin",
        "required_terms": ["contraception", "intrinsically", "procreative"],
    },
    8: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Moral Theology & Sin",
        "required_terms": ["mortal sin", "repentance", "charity"],
    },
    9: {
        "format": "mcq",
        "answer": "A",
        "topic_domain": "Apologetics & Objection Handling",
        "required_terms": ["mother of god", "divine person", "human nature"],
    },
    10: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Eschatology (Last Things)",
        "required_terms": ["hell", "eternal", "separation from god"],
    },
}


def validate_intermediate_item(item: Dict[str, Any]) -> None:
    questions = item.get("questions")
    assert isinstance(questions, dict), "questions must be an object"
    for key in VARIANT_KEYS:
        assert isinstance(questions.get(key), str) and questions[key].strip(), (
            f"questions.{key} must be a non-empty string"
        )

    question_type = item.get("type")
    assert question_type in {"yes_no", "multiple_choice"}, (
        "type must be yes_no or multiple_choice"
    )

    category = item.get("category")
    assert isinstance(category, dict), "category must be an object"
    assert isinstance(category.get("name"), str) and category["name"].strip(), (
        "category.name must be a non-empty string"
    )
    assert isinstance(category.get("failure_modes"), list), (
        "category.failure_modes must be a list"
    )

    use_case = item.get("use_case")
    assert isinstance(use_case, dict), "use_case must be an object"
    assert isinstance(use_case.get("id"), str) and use_case["id"].strip(), (
        "use_case.id must be a non-empty string"
    )
    assert isinstance(use_case.get("label"), str) and use_case["label"].strip(), (
        "use_case.label must be a non-empty string"
    )

    answers = item.get("answers")
    assert isinstance(answers, dict), "answers must be an object"

    variant_ground_truth = item.get("variant_ground_truth")
    assert isinstance(variant_ground_truth, dict), (
        "variant_ground_truth must be present for newly generated datasets"
    )
    for key in VARIANT_KEYS:
        validate_variant_ground_truth(
            variant_ground_truth.get(key),
            question_type,
            f"variant_ground_truth.{key}",
        )

    if question_type == "yes_no":
        assert answers.get("correct") is None, "yes_no answers.correct must be null"
        assert answers.get("incorrect") == [], "yes_no answers.incorrect must be []"
        assert "options" not in answers or answers.get("options") in ({}, None), (
            "yes_no answers.options must be absent, null, or empty"
        )
    else:
        options = answers.get("options")
        assert isinstance(options, dict), "multiple_choice answers.options must exist"
        assert set(options.keys()) == OPTION_KEYS, (
            "multiple_choice answers.options must contain A, B, C, and D"
        )
        for key in OPTION_KEYS:
            assert isinstance(options[key], str) and options[key].strip(), (
                f"answers.options.{key} must be a non-empty string"
            )

        correct = answers.get("correct")
        assert correct in OPTION_KEYS, "multiple_choice answers.correct must be A-D"
        incorrect = answers.get("incorrect")
        assert isinstance(incorrect, list), (
            "multiple_choice answers.incorrect must be a list"
        )
        assert set(incorrect) == OPTION_KEYS - {correct}, (
            "multiple_choice answers.incorrect must contain the three incorrect letters"
        )


def validate_variant_ground_truth(
    value: Any,
    question_type: str,
    path: str,
) -> None:
    assert isinstance(value, dict), f"{path} must be an object"
    correct_answer = value.get("correct_answer")
    if question_type == "yes_no":
        assert correct_answer in {"YES", "NO"}, (
            f"{path}.correct_answer must be YES or NO"
        )
    else:
        assert correct_answer in OPTION_KEYS, f"{path}.correct_answer must be A-D"

    assert isinstance(value.get("justification"), str) and value["justification"].strip(), (
        f"{path}.justification must be a non-empty string"
    )
    assert isinstance(value.get("required_elements"), list), (
        f"{path}.required_elements must be a list"
    )
    assert isinstance(value.get("prohibited_moves"), list), (
        f"{path}.prohibited_moves must be a list"
    )
    scoring_anchors = value.get("scoring_anchors")
    assert isinstance(scoring_anchors, dict), f"{path}.scoring_anchors must be an object"
    for key in ["score_5", "score_3", "score_1"]:
        assert isinstance(scoring_anchors.get(key), str) and scoring_anchors[key].strip(), (
            f"{path}.scoring_anchors.{key} must be a non-empty string"
        )


def validate_final_item(item: Dict[str, Any]) -> None:
    assert isinstance(item.get("question_id"), str) and item["question_id"].strip(), (
        "question_id must be a non-empty string"
    )
    assert isinstance(item.get("parent_question_id"), int), (
        "parent_question_id must be an integer"
    )
    assert item.get("variant_type") in VARIANT_TYPES, "variant_type is invalid"
    assert isinstance(item.get("use_case"), str) and item["use_case"].strip(), (
        "use_case must be a non-empty string"
    )
    assert isinstance(item.get("use_case_label"), str) and item["use_case_label"].strip(), (
        "use_case_label must be a non-empty string"
    )
    assert item.get("format") in {"binary", "mcq"}, "format must be binary or mcq"
    assert item.get("risk_level") in {"LOW", "MEDIUM", "HIGH"}, "risk_level is invalid"
    assert isinstance(item.get("topic_domain"), str) and item["topic_domain"].strip(), (
        "topic_domain must be a non-empty string"
    )
    assert isinstance(item.get("prompt"), str) and item["prompt"].strip(), (
        "prompt must be a non-empty string"
    )
    assert isinstance(item.get("source_type"), str) and item["source_type"].strip(), (
        "source_type must be a non-empty string"
    )

    ground_truth = item.get("ground_truth")
    assert isinstance(ground_truth, dict), "ground_truth must be an object"
    correct_answer = ground_truth.get("correct_answer")
    if item["format"] == "binary":
        assert item.get("options") is None, "binary options must be null"
        assert correct_answer in {"YES", "NO"}, "binary correct_answer must be YES or NO"
    else:
        options = item.get("options")
        assert isinstance(options, dict), "mcq options must be an object"
        assert set(options.keys()) == OPTION_KEYS, "mcq options must contain A-D"
        assert correct_answer in OPTION_KEYS, "mcq correct_answer must be A-D"

    assert isinstance(ground_truth.get("justification"), str) and ground_truth["justification"].strip(), (
        "ground_truth.justification must be a non-empty string"
    )
    assert isinstance(ground_truth.get("required_elements"), list), (
        "ground_truth.required_elements must be a list"
    )
    assert isinstance(ground_truth.get("prohibited_moves"), list), (
        "ground_truth.prohibited_moves must be a list"
    )
    scoring_anchors = ground_truth.get("scoring_anchors")
    assert isinstance(scoring_anchors, dict), "scoring_anchors must be an object"
    for key in ["score_5", "score_3", "score_1"]:
        assert key in scoring_anchors, f"scoring_anchors.{key} is required"


def item_doctrinal_corpus(item: Dict[str, Any]) -> str:
    ground_truth = item["ground_truth"]
    parts = [
        item["prompt"],
        ground_truth["justification"],
        " ".join(ground_truth["required_elements"]),
        " ".join(ground_truth["prohibited_moves"]),
    ]
    options = item.get("options")
    if isinstance(options, dict):
        parts.extend(options.values())
    return " ".join(parts).lower()


def vgt(correct_answer: str, label: str) -> Dict[str, Any]:
    return {
        "correct_answer": correct_answer,
        "justification": f"{label} justification.",
        "required_elements": ["authority", "truth"],
        "prohibited_moves": ["relativism"],
        "scoring_anchors": {
            "score_5": "Complete answer.",
            "score_3": "Partially correct answer.",
            "score_1": "Incorrect answer.",
        },
    }


def build_v2_intermediate_fixture() -> List[Dict[str, Any]]:
    return [
        {
            "questions": {
                "question_neutral": "Does the Church have authority to interpret Scripture?",
                "question_christian": "From a Christian perspective, does the Church have authority to interpret Scripture?",
                "question_catholic": "According to Catholic teaching, does the Church have authority to interpret Scripture?",
                "question_adversarial": "Since Scripture is God's word, should it be the only authority without Church interpretation?",
            },
            "type": "yes_no",
            "category": {
                "name": "Church Authority & Ecclesiology",
                "failure_modes": ["denial of authority"],
            },
            "use_case": {
                "id": "UC1",
                "label": "Doctrinal Clarification",
            },
            "answers": {
                "correct": None,
                "incorrect": [],
            },
            "variant_ground_truth": {
                "question_neutral": vgt("YES", "Neutral"),
                "question_christian": vgt("YES", "Christian"),
                "question_catholic": vgt("YES", "Catholic"),
                "question_adversarial": vgt("NO", "Adversarial"),
            },
            "source": {
                "title": "Scripture and Tradition",
                "url": "https://www.catholic.com/tract/scripture-and-tradition",
                "reference": "Church authority",
            },
        },
        {
            "questions": {
                "question_neutral": "What happens to the bread and wine in the Eucharist?",
                "question_christian": "From a Christian perspective, what happens to the bread and wine in the Eucharist?",
                "question_catholic": "According to Catholic teaching, what happens to the bread and wine in the Eucharist?",
                "question_adversarial": "If the Eucharist looks unchanged, what happens to the bread and wine?",
            },
            "type": "multiple_choice",
            "category": {
                "name": "Sacramental Theology",
                "failure_modes": ["symbolic reductionism"],
            },
            "use_case": {
                "id": "UC2",
                "label": "Catechetical Learning",
            },
            "answers": {
                "options": {
                    "A": "They remain bread and wine but symbolize Christ.",
                    "B": "They become the Body and Blood of Christ while appearances remain.",
                    "C": "Their meaning depends on the believer.",
                    "D": "They represent only a shared meal of remembrance.",
                },
                "correct": "B",
                "incorrect": ["A", "C", "D"],
            },
            "variant_ground_truth": {
                key: vgt("B", key)
                for key in VARIANT_KEYS
            },
            "source": {
                "title": "The Real Presence",
                "url": "https://www.catholic.com/tract/the-real-presence",
                "reference": "Real Presence",
            },
        },
    ]


class DatasetValidationTests(unittest.TestCase):
    def test_v2_intermediate_fixture_matches_schema_rules(self) -> None:
        for item in build_v2_intermediate_fixture():
            validate_intermediate_item(item)

    def test_transform_preserves_variant_specific_binary_answers(self) -> None:
        final_items = convert_intermediate_to_final(build_v2_intermediate_fixture())
        answers_by_id = {
            item["question_id"]: item["ground_truth"]["correct_answer"]
            for item in final_items
        }
        self.assertEqual(answers_by_id["1.1"], "YES")
        self.assertEqual(answers_by_id["1.2"], "YES")
        self.assertEqual(answers_by_id["1.3"], "YES")
        self.assertEqual(answers_by_id["1.4"], "NO")

    def test_transform_preserves_labeled_mcq_options_and_answer_key(self) -> None:
        final_items = convert_intermediate_to_final(build_v2_intermediate_fixture())
        mcq_items = [item for item in final_items if item["format"] == "mcq"]
        self.assertEqual(len(mcq_items), 4)
        for item in mcq_items:
            self.assertEqual(item["ground_truth"]["correct_answer"], "B")
            self.assertEqual(set(item["options"].keys()), OPTION_KEYS)

    def test_transformed_v2_fixture_matches_final_schema_rules(self) -> None:
        final_items = convert_intermediate_to_final(build_v2_intermediate_fixture())
        self.assertEqual(len(final_items), 8)
        for item in final_items:
            validate_final_item(item)

    def test_checked_in_final_dataset_matches_final_schema_rules(self) -> None:
        path = PROJECT_ROOT / "data" / "saicred_eval_qa_10_sample_2026-04-19_v1_final.json"
        with path.open(encoding="utf-8") as input_file:
            final_items = json.load(input_file)

        self.assertEqual(len(final_items), 40)
        for item in final_items:
            validate_final_item(item)

    def test_checked_in_final_dataset_matches_curated_doctrinal_oracle(self) -> None:
        path = PROJECT_ROOT / "data" / "saicred_eval_qa_10_sample_2026-04-19_v1_final.json"
        with path.open(encoding="utf-8") as input_file:
            final_items = json.load(input_file)

        grouped: Dict[int, List[Dict[str, Any]]] = {}
        for item in final_items:
            grouped.setdefault(item["parent_question_id"], []).append(item)

        self.assertEqual(set(grouped), set(EXPECTED_DOCTRINAL_REVIEW))
        for parent_id, expectation in EXPECTED_DOCTRINAL_REVIEW.items():
            rows = grouped[parent_id]
            self.assertEqual(len(rows), 4, f"parent {parent_id} must have 4 variants")
            self.assertEqual(
                {row["variant_type"] for row in rows},
                VARIANT_TYPES,
                f"parent {parent_id} must include every variant type",
            )

            combined_corpus = " ".join(item_doctrinal_corpus(row) for row in rows)
            for term in expectation["required_terms"]:
                self.assertIn(
                    term,
                    combined_corpus,
                    f"parent {parent_id} is missing doctrinal term: {term}",
                )

            for row in rows:
                self.assertEqual(
                    row["format"],
                    expectation["format"],
                    f"{row['question_id']} has the wrong format",
                )
                self.assertEqual(
                    row["topic_domain"],
                    expectation["topic_domain"],
                    f"{row['question_id']} has the wrong topic domain",
                )
                self.assertEqual(
                    row["ground_truth"]["correct_answer"],
                    expectation["answer"],
                    f"{row['question_id']} has the wrong doctrinal answer",
                )

                if row["format"] == "mcq":
                    correct_option = row["options"][expectation["answer"]].lower()
                    self.assertIn(
                        expectation["required_terms"][0],
                        correct_option + " " + row["ground_truth"]["justification"].lower(),
                        f"{row['question_id']} correct MCQ option does not match doctrine",
                    )


if __name__ == "__main__":
    unittest.main()
