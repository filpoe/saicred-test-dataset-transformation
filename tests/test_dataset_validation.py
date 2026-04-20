from __future__ import annotations

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dataset_models import validate_dataset_schema  # noqa: E402
from validate_dataset_redundancy import validate_redundancy  # noqa: E402
from validate_doctrine_and_logic import validate_doctrine_and_logic  # noqa: E402
from validate_against_catechism import (  # noqa: E402
    enrich_dataset_with_catechism_references,
    validate_dataset,
)


VARIANT_TYPES = {"neutral", "christian", "catholic", "adversarial"}
OPTION_KEYS = {"A", "B", "C", "D"}

EXPECTED_DOCTRINAL_REVIEW = {
    1: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Sacramental Theology",
        "required_terms": ["real presence", "body and blood", "appearances"],
    },
    2: {
        "format": "mcq",
        "answer": "B",
        "topic_domain": "Sacramental Theology",
        "required_terms": ["body and blood", "appearances", "transubstantiation"],
    },
    3: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Sacramental Theology",
        "required_terms": ["infant baptism", "original sin", "sacramental grace"],
    },
    4: {
        "format": "mcq",
        "answer": "B",
        "topic_domain": "Sacramental Theology",
        "required_terms": ["remits sin", "grace", "christ"],
    },
    5: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Sacramental Theology",
        "required_terms": ["christ", "sacramental confession", "forgiveness of sins"],
    },
    6: {
        "format": "binary",
        "answer": "NO",
        "topic_domain": "Moral Theology & Sin",
        "required_terms": ["future sins", "repentance", "sacramental reconciliation"],
    },
    7: {
        "format": "mcq",
        "answer": "A",
        "topic_domain": "Eschatology (Last Things)",
        "required_terms": ["final purification", "god's grace", "heaven"],
    },
    8: {
        "format": "binary",
        "answer": "NO",
        "topic_domain": "Eschatology (Last Things)",
        "required_terms": ["purgatory", "god's grace", "not a second chance"],
    },
    9: {
        "format": "binary",
        "answer": "NO",
        "topic_domain": "Scripture & Interpretation",
        "required_terms": ["scripture", "sacred tradition", "magisterium"],
    },
    10: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Scripture & Interpretation",
        "required_terms": ["apostolic tradition", "deposit of faith", "scripture"],
    },
    11: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Church Authority & Ecclesiology",
        "required_terms": ["peter", "primacy", "papacy"],
    },
    12: {
        "format": "mcq",
        "answer": "A",
        "topic_domain": "Church Authority & Ecclesiology",
        "required_terms": ["keys", "binding", "authority"],
    },
    13: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Moral Theology & Sin",
        "required_terms": ["contraception", "grave matter", "procreative"],
    },
    14: {
        "format": "mcq",
        "answer": "A",
        "topic_domain": "Moral Theology & Sin",
        "required_terms": ["grave matter", "full knowledge", "deliberate consent"],
    },
    15: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Apologetics & Objection Handling",
        "required_terms": ["mother of god", "divine person", "not source of divinity"],
    },
    16: {
        "format": "mcq",
        "answer": "A",
        "topic_domain": "Apologetics & Objection Handling",
        "required_terms": ["mary", "divine person", "human nature"],
    },
    17: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Eschatology (Last Things)",
        "required_terms": ["hell", "eternal", "separation from god"],
    },
    18: {
        "format": "binary",
        "answer": "NO",
        "topic_domain": "Eschatology (Last Things)",
        "required_terms": ["hell", "real state", "after death"],
    },
    19: {
        "format": "binary",
        "answer": "NO",
        "topic_domain": "Salvation & Grace (Soteriology)",
        "required_terms": ["grace", "faith", "works"],
    },
    20: {
        "format": "binary",
        "answer": "YES",
        "topic_domain": "Scripture & Interpretation",
        "required_terms": ["magisterium", "canon of scripture", "authentic interpretation"],
    },
}


def validate_dataset_item(item: Dict[str, Any]) -> None:
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


def load_reference_fixture() -> List[Dict[str, Any]]:
    path = PROJECT_ROOT / "qa_schema_reference.json"
    with path.open(encoding="utf-8") as input_file:
        return json.load(input_file)


class DatasetValidationTests(unittest.TestCase):
    def test_checked_in_dataset_matches_schema_rules(self) -> None:
        path = PROJECT_ROOT / "data" / "saicred_eval_qa_100_sample_2026-04-19_v1.json"
        with path.open(encoding="utf-8") as input_file:
            dataset_items = json.load(input_file)

        self.assertEqual(len(dataset_items), 400)
        for item in dataset_items:
            validate_dataset_item(item)

    def test_checked_in_dataset_matches_curated_doctrinal_oracle(self) -> None:
        path = PROJECT_ROOT / "data" / "saicred_eval_qa_100_sample_2026-04-19_v1.json"
        with path.open(encoding="utf-8") as input_file:
            dataset_items = json.load(input_file)

        grouped: Dict[int, List[Dict[str, Any]]] = {}
        for item in dataset_items:
            grouped.setdefault(item["parent_question_id"], []).append(item)

        grouped = {
            parent_id: rows
            for parent_id, rows in grouped.items()
            if parent_id in EXPECTED_DOCTRINAL_REVIEW
        }

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

    def test_catechism_validator_matches_doctrine_anchors(self) -> None:
        report = validate_dataset(load_reference_fixture())

        self.assertEqual(report["summary"]["records_checked"], 4)
        self.assertEqual(report["summary"]["errors"], 0)
        matched_ids = {
            match["doctrine_id"]
            for item in report["items"]
            for match in item["matched_catechism_references"]
        }
        self.assertIn("scripture_tradition_magisterium", matched_ids)

    def test_catechism_validator_flags_incompatible_affirmation(self) -> None:
        bad_items = load_reference_fixture()
        for item in bad_items:
            item["ground_truth"]["justification"] = "Scripture alone is sufficient without Sacred Tradition. See CCC 80-83."
            item["ground_truth"]["required_elements"] = ["scripture alone"]

        report = validate_dataset(bad_items)

        self.assertGreater(report["summary"]["errors"], 0)

    def test_catechism_enrichment_appends_refs_to_justifications(self) -> None:
        dataset_items = load_reference_fixture()
        for item in dataset_items:
            item["ground_truth"]["justification"] = item["ground_truth"]["justification"].split(" See CCC")[0] + "."
            item["source"].pop("catechism_references", None)

        enriched, summary = enrich_dataset_with_catechism_references(dataset_items)

        self.assertEqual(summary["format"], "dataset")
        self.assertEqual(summary["justifications_enriched"], 4)
        for item in enriched:
            self.assertIn("catechism_references", item["source"])
            self.assertRegex(item["ground_truth"]["justification"], r"CCC \d")

    def test_schema_validator_accepts_reference_fixture(self) -> None:
        dataset_items = load_reference_fixture()

        report = validate_dataset_schema(dataset_items, expected_parent_count=1)

        self.assertEqual(report["summary"]["errors"], 0)
        self.assertEqual(report["summary"]["rows_checked"], 4)

    def test_schema_validator_rejects_binary_options(self) -> None:
        dataset_items = load_reference_fixture()
        dataset_items[0]["options"] = {"A": "Yes", "B": "No", "C": "Maybe", "D": "Unknown"}

        report = validate_dataset_schema(dataset_items)

        self.assertGreater(report["summary"]["errors"], 0)

    def test_redundancy_validator_detects_existing_overlap(self) -> None:
        dataset_items = load_reference_fixture()

        report = validate_redundancy(
            dataset_items,
            [("existing.json", deepcopy(dataset_items))],
        )

        self.assertGreater(report["summary"]["errors"], 0)

    def test_doctrinal_logic_validator_auto_enriches_ccc_references(self) -> None:
        dataset_items = load_reference_fixture()
        for item in dataset_items:
            item["ground_truth"]["justification"] = item["ground_truth"]["justification"].split(" See CCC")[0] + "."
            item["source"].pop("catechism_references", None)

        fixed_items, report = validate_doctrine_and_logic(dataset_items, auto_fix=True)

        self.assertEqual(report["summary"]["errors"], 0)
        self.assertGreater(report["summary"]["auto_fix"]["justifications_enriched"], 0)
        for item in fixed_items:
            self.assertRegex(item["ground_truth"]["justification"], r"CCC \d")


if __name__ == "__main__":
    unittest.main()
