from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


CCC_INDEX_URL = "https://www.vatican.va/archive/ENG0015/_INDEX.HTM"

VARIANT_KEYS = {
    "question_neutral": ("1", "neutral"),
    "question_christian": ("2", "christian"),
    "question_catholic": ("3", "catholic"),
    "question_adversarial": ("4", "adversarial"),
}

OPTION_KEYS = {"A", "B", "C", "D"}


@dataclass(frozen=True)
class CatechismReference:
    doctrine_id: str
    title: str
    ccc: Sequence[str]
    keywords: Sequence[str]
    anchors: Sequence[str]
    forbidden_affirmations: Sequence[str] = ()


CATECHISM_REFERENCES: Sequence[CatechismReference] = (
    CatechismReference(
        doctrine_id="eucharist_real_presence",
        title="Eucharist, Real Presence, and Transubstantiation",
        ccc=("1324", "1374-1377", "1413"),
        keywords=("eucharist", "communion", "real presence", "transubstantiation", "body and blood"),
        anchors=("real presence", "body and blood", "transubstantiation", "appearances", "substance", "source and summit", "christian life"),
        forbidden_affirmations=("merely symbolic", "symbol only", "only a symbol", "remain bread and wine"),
    ),
    CatechismReference(
        doctrine_id="baptism",
        title="Baptism and Infant Baptism",
        ccc=("1213", "1250", "1263", "1279"),
        keywords=("baptism", "infant baptism", "original sin", "baptized"),
        anchors=("baptism", "original sin", "grace", "incorporates", "forgiveness"),
        forbidden_affirmations=("only a public sign", "adult only", "no connection to salvation"),
    ),
    CatechismReference(
        doctrine_id="penance_reconciliation",
        title="Penance, Confession, and Forgiveness of Sins",
        ccc=("1441-1442", "1446", "1468-1470"),
        keywords=("confession", "penance", "reconciliation", "forgive sins", "mortal sin"),
        anchors=("forgiveness", "confession", "reconciliation", "absolution", "church"),
        forbidden_affirmations=("private prayer only", "no sacramental ministry"),
    ),
    CatechismReference(
        doctrine_id="purgatory",
        title="Purgatory and Final Purification",
        ccc=("1030-1032",),
        keywords=("purgatory", "final purification", "second chance"),
        anchors=("purgatory", "purification", "heaven", "grace"),
        forbidden_affirmations=("second chance after death", "not real"),
    ),
    CatechismReference(
        doctrine_id="scripture_tradition_magisterium",
        title="Scripture, Tradition, Magisterium, and Canon",
        ccc=("80-83", "85-87", "100", "105-108", "120"),
        keywords=("scripture", "tradition", "magisterium", "canon", "deuterocanonical", "apocrypha"),
        anchors=("scripture", "tradition", "magisterium", "church", "canon"),
        forbidden_affirmations=("scripture alone", "private interpretation only", "individual reader alone"),
    ),
    CatechismReference(
        doctrine_id="papacy_church_authority",
        title="Papal Primacy and Infallibility",
        ccc=("880-882", "891"),
        keywords=("pope", "papacy", "peter", "infallibility", "keys", "binding"),
        anchors=("peter", "pope", "authority", "infallibility", "keys"),
        forbidden_affirmations=("impeccability", "no special authority"),
    ),
    CatechismReference(
        doctrine_id="mortal_sin",
        title="Mortal Sin and Venial Sin",
        ccc=("1849-1864",),
        keywords=("mortal sin", "venial sin", "grave matter", "full knowledge", "deliberate consent"),
        anchors=("grave matter", "full knowledge", "deliberate consent", "mortal", "venial"),
        forbidden_affirmations=("feelings alone", "no grave matter"),
    ),
    CatechismReference(
        doctrine_id="marian_dogma",
        title="Mary, Mother of God, Immaculate Conception, and Assumption",
        ccc=("466", "490-493", "966-970"),
        keywords=("mary", "mother of god", "theotokos", "immaculate conception", "assumption"),
        anchors=("mary", "mother of god", "christ", "grace", "assumption"),
        forbidden_affirmations=("source of christ's divinity", "goddess"),
    ),
    CatechismReference(
        doctrine_id="saints_communion",
        title="Communion and Intercession of Saints",
        ccc=("946-962", "956"),
        keywords=("saints", "communion of saints", "intercession", "pray to saints"),
        anchors=("communion", "saints", "intercession", "church", "charity"),
        forbidden_affirmations=("worship saints", "replace christ"),
    ),
    CatechismReference(
        doctrine_id="apostolic_succession_orders",
        title="Apostolic Succession and Holy Orders",
        ccc=("77", "861-862", "1536", "1548-1553", "1576"),
        keywords=("apostolic succession", "holy orders", "bishop", "priest", "laying on of hands"),
        anchors=("apostolic", "succession", "orders", "bishop", "priest"),
        forbidden_affirmations=("authority died with apostles",),
    ),
    CatechismReference(
        doctrine_id="confirmation",
        title="Confirmation",
        ccc=("1285", "1302-1305"),
        keywords=("confirmation", "holy spirit", "chrism"),
        anchors=("confirmation", "holy spirit", "strengthens", "grace"),
        forbidden_affirmations=("optional symbol only",),
    ),
    CatechismReference(
        doctrine_id="anointing_sick",
        title="Anointing of the Sick",
        ccc=("1499", "1520-1523"),
        keywords=("anointing of the sick", "dying", "illness", "sick"),
        anchors=("sick", "anointing", "healing", "grace", "suffering"),
        forbidden_affirmations=("only for the dead",),
    ),
    CatechismReference(
        doctrine_id="indulgences",
        title="Indulgences",
        ccc=("1471-1479",),
        keywords=("indulgence", "temporal punishment"),
        anchors=("indulgence", "temporal punishment", "sin", "church"),
        forbidden_affirmations=("forgive future sins", "permission to sin"),
    ),
    CatechismReference(
        doctrine_id="matrimony",
        title="Matrimony, Indissolubility, and Nullity",
        ccc=("1601", "1625-1632", "1638-1640", "1644-1651"),
        keywords=("marriage", "matrimony", "divorce", "annulment", "nullity", "consent"),
        anchors=("marriage", "matrimony", "consent", "indissoluble", "covenant"),
        forbidden_affirmations=("church dissolves valid marriage",),
    ),
    CatechismReference(
        doctrine_id="trinity_christology",
        title="Trinity and Christology",
        ccc=("232-267", "464-469"),
        keywords=("trinity", "divinity of christ", "incarnation", "god and man"),
        anchors=("trinity", "christ", "divine", "person", "nature"),
        forbidden_affirmations=("created being", "not god"),
    ),
    CatechismReference(
        doctrine_id="resurrection_original_sin",
        title="Resurrection of the Body and Original Sin",
        ccc=("396-409", "988-1019"),
        keywords=("resurrection of the body", "original sin", "wounded nature", "dead rise"),
        anchors=("resurrection", "body", "original sin", "death", "human nature"),
        forbidden_affirmations=("soul only", "no bodily resurrection"),
    ),
    CatechismReference(
        doctrine_id="moral_life",
        title="Moral Acts, Conscience, Abortion, and Euthanasia",
        ccc=("1749-1761", "1776-1802", "2270-2279"),
        keywords=("conscience", "intrinsically evil", "abortion", "euthanasia", "intention", "circumstances"),
        anchors=("conscience", "moral", "intrinsic", "human life", "evil"),
        forbidden_affirmations=("intention alone determines", "direct abortion can be good"),
    ),
    CatechismReference(
        doctrine_id="adoration_images_relics",
        title="Adoration, Images, Relics, and Idolatry",
        ccc=("2096-2097", "2112-2114", "2129-2132", "2138"),
        keywords=("adoration", "latria", "statues", "images", "relics", "idolatry", "veneration"),
        anchors=("adoration", "god alone", "veneration", "images", "idolatry", "blessed sacrament", "priest or deacon", "blesses faithful"),
        forbidden_affirmations=("worship statues", "adoration of creatures"),
    ),
    CatechismReference(
        doctrine_id="mass_obligation",
        title="Mass, Lord's Day, and Eucharistic Preparation",
        ccc=("1387", "2042-2043", "2180-2183"),
        keywords=("mass", "sunday obligation", "holy day", "eucharistic fast", "communion fast"),
        anchors=("mass", "sunday", "obligation", "eucharist", "fast", "participate", "serious reason", "dispensation", "before communion", "water and medicine"),
        forbidden_affirmations=("watching mass fulfills", "weekday replaces sunday"),
    ),
    CatechismReference(
        doctrine_id="heaven_hell_judgment",
        title="Heaven, Hell, Judgment, and Beatific Vision",
        ccc=("678-682", "1021-1029", "1033-1037", "1038-1041"),
        keywords=("heaven", "hell", "judgment", "beatific vision", "last judgment"),
        anchors=("heaven", "hell", "judgment", "god", "eternal"),
        forbidden_affirmations=("hell is not real", "all are automatically saved"),
    ),
    CatechismReference(
        doctrine_id="angels_revelation",
        title="Angels, Demons, and Definitive Revelation in Christ",
        ccc=("65-67", "328-336", "391-395"),
        keywords=("angels", "guardian angels", "demons", "public revelation", "occult"),
        anchors=("angels", "spiritual", "christ", "revelation", "demons"),
        forbidden_affirmations=("new public revelation", "occult practices are harmless"),
    ),
    CatechismReference(
        doctrine_id="sacramentals",
        title="Sacramentals and Holy Water",
        ccc=("1667-1679",),
        keywords=("sacramentals", "holy water", "blessing"),
        anchors=("sacramental", "blessing", "church", "prayer"),
        forbidden_affirmations=("sacramentals work automatically",),
    ),
    CatechismReference(
        doctrine_id="works_mercy_fasting_almsgiving",
        title="Works of Mercy, Fasting, and Almsgiving",
        ccc=("1434", "1438", "2447", "2462"),
        keywords=("works of mercy", "fasting", "almsgiving", "mercy", "forgive offenses"),
        anchors=("mercy", "fasting", "almsgiving", "charity", "penance", "feed the hungry", "feeding the hungry", "corporal work", "abstinence", "dependence on god"),
        forbidden_affirmations=("optional sentiment only",),
    ),
    CatechismReference(
        doctrine_id="grace_merit_virtues",
        title="Grace, Merit, Hope, and Virtues",
        ccc=("1803-1809", "1812-1821", "1996-2005", "2006-2011"),
        keywords=("grace", "merit", "hope", "virtue", "prudence", "justice", "temperance", "cardinal virtues"),
        anchors=("grace", "virtue", "hope", "merit", "prudence", "justice", "temperance"),
        forbidden_affirmations=("grace is natural ability", "merit without grace"),
    ),
)


def normalize_text(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def contains_phrase(text: str, phrase: str) -> bool:
    return normalize_text(phrase) in normalize_text(text)


def has_unnegated_phrase(text: str, phrase: str) -> bool:
    normalized_phrase = normalize_text(phrase)
    phrase_words = normalized_phrase.split()
    if not phrase_words:
        return False

    negators = {"not", "no", "never", "neither", "nor", "without", "rejects", "denies", "denial"}
    raw_sentences = re.split(r"[.;:!?]", text)
    normalized_sentences = [normalize_text(sentence) for sentence in raw_sentences]

    for sentence in normalized_sentences:
        if normalized_phrase not in sentence:
            continue
        words = sentence.split()
        phrase_len = len(phrase_words)
        for index in range(0, len(words) - phrase_len + 1):
            if words[index:index + phrase_len] != phrase_words:
                continue
            window = words[max(0, index - 12):index]
            if any(word in negators for word in window):
                return False

    normalized_text = normalize_text(text)
    words = normalized_text.split()
    phrase_len = len(phrase_words)
    for index in range(0, len(words) - phrase_len + 1):
        if words[index:index + phrase_len] != phrase_words:
            continue
        window = words[max(0, index - 5):index]
        if not any(word in negators for word in window):
            return True
    return False


def extract_records(dataset: Any) -> List[Dict[str, Any]]:
    if not isinstance(dataset, list):
        raise ValueError("Dataset must be a JSON array")

    if not dataset:
        return []

    if all(isinstance(item, dict) and "questions" in item for item in dataset):
        return _extract_intermediate_records(dataset)

    if all(isinstance(item, dict) and "question_id" in item for item in dataset):
        return _extract_final_records(dataset)

    raise ValueError("Dataset must be consistently intermediate-format or final-format JSON")


def _extract_intermediate_records(items: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for parent_index, item in enumerate(items, start=1):
        questions = item.get("questions", {})
        answers = item.get("answers", {})
        variant_ground_truth = item.get("variant_ground_truth", {})
        source = item.get("source", {})
        item_refs = _extract_catechism_refs(item, source)

        for variant_key, (suffix, variant_type) in VARIANT_KEYS.items():
            ground_truth = variant_ground_truth.get(variant_key, {})
            record = {
                "record_id": f"{parent_index}.{suffix}",
                "parent_question_id": parent_index,
                "variant_type": variant_type,
                "format": "binary" if item.get("type") == "yes_no" else "mcq",
                "topic_domain": item.get("category", {}).get("name"),
                "prompt": questions.get(variant_key, ""),
                "options": answers.get("options") if item.get("type") == "multiple_choice" else None,
                "correct_answer": ground_truth.get("correct_answer") or answers.get("correct"),
                "ground_truth": ground_truth,
                "source": source,
                "catechism_references": item_refs,
            }
            records.append(record)
    return records


def _extract_final_records(items: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for item in items:
        source = item.get("source", {})
        refs = _extract_catechism_refs(item, source)
        ground_truth = item.get("ground_truth", {})
        records.append(
            {
                "record_id": item.get("question_id"),
                "parent_question_id": item.get("parent_question_id"),
                "variant_type": item.get("variant_type"),
                "format": item.get("format"),
                "topic_domain": item.get("topic_domain"),
                "prompt": item.get("prompt", ""),
                "options": item.get("options"),
                "correct_answer": ground_truth.get("correct_answer"),
                "ground_truth": ground_truth,
                "source": source,
                "catechism_references": refs,
            }
        )
    return records


def _extract_catechism_refs(item: Dict[str, Any], source: Dict[str, Any]) -> List[str]:
    refs = item.get("catechism_references")
    if refs is None and isinstance(source, dict):
        refs = source.get("catechism_references")
    if refs is None:
        return []
    if not isinstance(refs, list):
        return []
    return [str(ref).strip() for ref in refs if str(ref).strip()]


def validate_dataset(
    dataset: Any,
    *,
    require_explicit_refs: bool = False,
) -> Dict[str, Any]:
    records = extract_records(dataset)
    items = [
        validate_record(record, require_explicit_refs=require_explicit_refs)
        for record in records
    ]
    summary = {
        "records_checked": len(items),
        "errors": sum(len(item["errors"]) for item in items),
        "warnings": sum(len(item["warnings"]) for item in items),
        "records_with_explicit_catechism_refs": sum(
            1 for item in items if item["explicit_catechism_references"]
        ),
        "source": {
            "name": "Catechism of the Catholic Church",
            "url": CCC_INDEX_URL,
        },
    }
    return {
        "summary": summary,
        "items": items,
    }


def enrich_dataset_with_catechism_references(dataset: Any) -> tuple[Any, Dict[str, Any]]:
    if not isinstance(dataset, list):
        raise ValueError("Dataset must be a JSON array")
    if not dataset:
        return dataset, {"items_enriched": 0, "justifications_enriched": 0}

    if all(isinstance(item, dict) and "questions" in item for item in dataset):
        return _enrich_intermediate_dataset(dataset)
    if all(isinstance(item, dict) and "question_id" in item for item in dataset):
        return _enrich_final_dataset(dataset)
    raise ValueError("Dataset must be consistently intermediate-format or final-format JSON")


def _enrich_intermediate_dataset(
    items: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    justifications_enriched = 0
    items_enriched = 0

    for item in items:
        records = _extract_intermediate_records([item])
        refs = _record_group_catechism_refs(records)
        if not refs:
            continue

        source = item.setdefault("source", {})
        if isinstance(source, dict):
            existing_refs = _extract_catechism_refs(item, source)
            merged_refs = _merge_refs(existing_refs, refs)
            if merged_refs != existing_refs:
                source["catechism_references"] = merged_refs
                items_enriched += 1

        variant_ground_truth = item.get("variant_ground_truth", {})
        if isinstance(variant_ground_truth, dict):
            for variant_key in VARIANT_KEYS:
                value = variant_ground_truth.get(variant_key)
                if not isinstance(value, dict):
                    continue
                old = value.get("justification")
                new = append_ccc_reference_to_justification(old, refs)
                if new != old:
                    value["justification"] = new
                    justifications_enriched += 1

    return items, {
        "items_enriched": items_enriched,
        "justifications_enriched": justifications_enriched,
        "format": "intermediate",
    }


def _enrich_final_dataset(
    items: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    justifications_enriched = 0
    items_enriched = 0

    for item in items:
        record = _extract_final_records([item])[0]
        refs = _record_group_catechism_refs([record])
        if not refs:
            continue

        source = item.setdefault("source", {})
        if isinstance(source, dict):
            existing_refs = _extract_catechism_refs(item, source)
            merged_refs = _merge_refs(existing_refs, refs)
            if merged_refs != existing_refs:
                source["catechism_references"] = merged_refs
                items_enriched += 1

        ground_truth = item.get("ground_truth")
        if isinstance(ground_truth, dict):
            old = ground_truth.get("justification")
            new = append_ccc_reference_to_justification(old, refs)
            if new != old:
                ground_truth["justification"] = new
                justifications_enriched += 1

    return items, {
        "items_enriched": items_enriched,
        "justifications_enriched": justifications_enriched,
        "format": "final",
    }


def _record_group_catechism_refs(records: Sequence[Dict[str, Any]]) -> List[str]:
    refs: List[str] = []
    for record in records:
        explicit_refs = record.get("catechism_references") or []
        if explicit_refs:
            refs = _merge_refs(refs, explicit_refs)
            continue
        matched_refs = match_catechism_references(record)
        if matched_refs:
            refs = _merge_refs(refs, matched_refs[0].ccc)
    return refs


def _merge_refs(existing_refs: Sequence[str], new_refs: Sequence[str]) -> List[str]:
    merged: List[str] = []
    for ref in [*existing_refs, *new_refs]:
        clean = str(ref).strip()
        if clean and clean not in merged:
            merged.append(clean)
    return merged


def append_ccc_reference_to_justification(value: Any, refs: Sequence[str]) -> Any:
    if not isinstance(value, str) or not value.strip() or not refs:
        return value
    if re.search(r"\bCCC\s+\d", value):
        return value
    suffix = f" See CCC {'; '.join(refs)}."
    return value.rstrip() + suffix


def validate_record(
    record: Dict[str, Any],
    *,
    require_explicit_refs: bool = False,
) -> Dict[str, Any]:
    matched_refs = match_catechism_references(record)
    warnings: List[str] = []
    errors: List[str] = []

    explicit_refs = record.get("catechism_references") or []
    if require_explicit_refs and not explicit_refs:
        errors.append("Missing explicit catechism_references")

    if not matched_refs:
        errors.append("Could not infer a relevant Catechism doctrine anchor")
    else:
        if not _has_anchor_support(record, matched_refs):
            warnings.append(
                "Ground truth does not clearly contain anchor terms from the matched CCC doctrine"
            )
        _check_forbidden_affirmations(record, matched_refs, errors)

    if record.get("format") == "mcq":
        _check_mcq_record(record, matched_refs, warnings, errors)
    elif record.get("format") == "binary":
        if record.get("correct_answer") not in {"YES", "NO"}:
            errors.append("Binary item correct_answer must be YES or NO")
    else:
        errors.append("Record format must be binary or mcq")

    return {
        "record_id": record.get("record_id"),
        "parent_question_id": record.get("parent_question_id"),
        "variant_type": record.get("variant_type"),
        "topic_domain": record.get("topic_domain"),
        "correct_answer": record.get("correct_answer"),
        "explicit_catechism_references": explicit_refs,
        "used_inferred_catechism_references": not bool(explicit_refs),
        "matched_catechism_references": [
            {
                "doctrine_id": ref.doctrine_id,
                "title": ref.title,
                "ccc": list(ref.ccc),
            }
            for ref in matched_refs
        ],
        "warnings": warnings,
        "errors": errors,
    }


def match_catechism_references(record: Dict[str, Any]) -> List[CatechismReference]:
    corpus = _record_corpus(record, include_prohibited=True)
    explicit_refs = set(record.get("catechism_references") or [])
    scored: List[tuple[int, CatechismReference]] = []

    for ref in CATECHISM_REFERENCES:
        score = sum(2 for keyword in ref.keywords if contains_phrase(corpus, keyword))
        score += sum(1 for anchor in ref.anchors if contains_phrase(corpus, anchor))
        if explicit_refs and any(ccc in explicit_refs for ccc in ref.ccc):
            score += 10
        if score:
            scored.append((score, ref))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [ref for score, ref in scored[:3] if score >= 2]


def _record_corpus(record: Dict[str, Any], *, include_prohibited: bool) -> str:
    ground_truth = record.get("ground_truth") or {}
    parts = [
        str(record.get("topic_domain") or ""),
        str(record.get("prompt") or ""),
        str(ground_truth.get("justification") or ""),
        " ".join(map(str, ground_truth.get("required_elements") or [])),
    ]
    if include_prohibited:
        parts.append(" ".join(map(str, ground_truth.get("prohibited_moves") or [])))
    source = record.get("source") or {}
    if isinstance(source, dict):
        parts.extend([
            str(source.get("title") or ""),
            str(source.get("reference") or ""),
        ])
    options = record.get("options")
    if isinstance(options, dict):
        parts.extend(str(value) for value in options.values())
    return " ".join(parts)


def _answer_support_text(record: Dict[str, Any]) -> str:
    ground_truth = record.get("ground_truth") or {}
    parts = [
        str(ground_truth.get("justification") or ""),
        " ".join(map(str, ground_truth.get("required_elements") or [])),
    ]
    options = record.get("options")
    correct = record.get("correct_answer")
    if isinstance(options, dict) and isinstance(correct, str):
        parts.append(str(options.get(correct, "")))
    return " ".join(parts)


def _has_anchor_support(
    record: Dict[str, Any],
    matched_refs: Sequence[CatechismReference],
) -> bool:
    support_text = _answer_support_text(record)
    return any(
        contains_phrase(support_text, anchor)
        for ref in matched_refs
        for anchor in ref.anchors
    )


def _check_forbidden_affirmations(
    record: Dict[str, Any],
    matched_refs: Sequence[CatechismReference],
    errors: List[str],
) -> None:
    support_text = _answer_support_text(record)
    for ref in matched_refs:
        for phrase in ref.forbidden_affirmations:
            if has_unnegated_phrase(support_text, phrase):
                errors.append(
                    f"Ground truth appears to affirm a CCC-incompatible claim: {phrase!r}"
                )


def _check_mcq_record(
    record: Dict[str, Any],
    matched_refs: Sequence[CatechismReference],
    warnings: List[str],
    errors: List[str],
) -> None:
    options = record.get("options")
    correct = record.get("correct_answer")
    if not isinstance(options, dict) or set(options) != OPTION_KEYS:
        errors.append("MCQ item must include options A-D")
        return
    if correct not in OPTION_KEYS:
        errors.append("MCQ item correct_answer must be A, B, C, or D")
        return

    correct_option = options.get(correct, "")
    if matched_refs and not any(
        contains_phrase(correct_option, anchor)
        for ref in matched_refs
        for anchor in ref.anchors
    ):
        warnings.append(
            "Correct MCQ option does not clearly contain an anchor term from the matched CCC doctrine"
        )


def write_report(report: Dict[str, Any], output_path: Optional[Path]) -> None:
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if output_path is None:
        sys.stdout.write(text)
        return
    with output_path.open("w", encoding="utf-8") as output_file:
        output_file.write(text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate SAICRED QA datasets against Catechism doctrine anchors."
    )
    parser.add_argument("dataset", type=Path, help="Intermediate or final dataset JSON")
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional JSON report output path. Defaults to stdout.",
    )
    parser.add_argument(
        "--enrich-output",
        type=Path,
        help=(
            "Write a dataset copy with source.catechism_references populated "
            "and CCC references appended to each justification."
        ),
    )
    parser.add_argument(
        "--require-explicit-refs",
        action="store_true",
        help="Fail records that do not include catechism_references.",
    )
    parser.add_argument(
        "--fail-on",
        choices=("error", "warning"),
        default="error",
        help="Exit non-zero on errors only, or on errors and warnings.",
    )
    args = parser.parse_args()

    with args.dataset.open(encoding="utf-8") as input_file:
        dataset = json.load(input_file)

    if args.enrich_output is not None:
        dataset, enrich_summary = enrich_dataset_with_catechism_references(dataset)
        with args.enrich_output.open("w", encoding="utf-8") as output_file:
            json.dump(dataset, output_file, ensure_ascii=False, indent=2)
            output_file.write("\n")

    report = validate_dataset(
        dataset,
        require_explicit_refs=args.require_explicit_refs,
    )
    if args.enrich_output is not None:
        report["summary"]["enrichment"] = enrich_summary
    write_report(report, args.report)

    summary = report["summary"]
    if summary["errors"] > 0 or (
        args.fail_on == "warning" and summary["warnings"] > 0
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
