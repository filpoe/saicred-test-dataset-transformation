# SAICRED Final Evaluation Dataset

This folder contains generated SAICRED Catholic question-and-answer datasets.

Final-format benchmark datasets use this filename pattern:

```text
*_final.json
```

## Purpose

Each `*_final.json` file is a reference benchmark for testing LLM answers to Catholic doctrine questions.

It is designed to evaluate whether a model can answer accurately, consistently, and without being misled by framing changes. Each question includes ground truth answer data so model outputs can be compared against a known doctrinal reference.

## How To Use It

Use each row as one evaluation prompt.

For each row:

1. Send the `prompt` to the model being tested.
2. If the row is `binary`, evaluate whether the model answers according to `ground_truth.correct_answer`, which will be `YES` or `NO`.
3. If the row is `mcq`, evaluate whether the model selects the letter in `ground_truth.correct_answer`, which will be `A`, `B`, `C`, or `D`.
4. Use `ground_truth.justification`, `required_elements`, `prohibited_moves`, and `scoring_anchors` to judge whether the explanation is doctrinally complete and precise.

The dataset is not only checking answer labels. It is also checking whether the model can justify the answer in a way that preserves Catholic teaching.

## Sources

The questions and answers were first generated from Catholic Answers source material from [catholic.com](https://www.catholic.com/).

After generation, the dataset was validated against the [Catechism of the Catholic Church](https://www.vatican.va/archive/ENG0015/_INDEX.HTM), abbreviated `CCC`. Each row includes both source layers:

- `source.title`, `source.url`, and `source.reference` identify the Catholic Answers material used to generate the item.
- `source.catechism_references` lists supporting CCC paragraph numbers or paragraph ranges.
- `ground_truth.justification` includes an explicit `See CCC ...` reference.

Validation results are stored separately in `../data_validation_results/`. Those files are audit outputs, not dataset inputs.

## High-Level Schema

Each final-format file is a JSON array. Each object in the array is one benchmark row.

Each final dataset starts from parent question-and-answer items. Each parent item is expanded into four variants, so a final file contains four rows for every parent item.

Each parent item has these four variant types:

- `neutral`: plain baseline wording.
- `christian`: general Christian framing that can expose generic or non-Catholic defaults.
- `catholic`: explicit Catholic framing that asks for doctrinal precision.
- `adversarial`: objection-style or misleading framing that tests robustness.

The `question_id` shows both the parent item and the variant. For example:

```text
1.1 = parent question 1, neutral variant
1.2 = parent question 1, christian variant
1.3 = parent question 1, catholic variant
1.4 = parent question 1, adversarial variant
```

Rows can have one of two formats:

- `binary`: yes/no questions with `ground_truth.correct_answer` equal to `YES` or `NO`.
- `mcq`: multiple-choice questions with four options, where `ground_truth.correct_answer` is `A`, `B`, `C`, or `D`.

## Field Reference

`question_id`: Unique row identifier in `parent.variant` form, such as `12.4`.

`parent_question_id`: Integer identifier for the parent doctrinal question.

`variant_type`: One of `neutral`, `christian`, `catholic`, or `adversarial`.

`use_case`: Short use-case identifier, such as `UC1`.

`use_case_label`: Human-readable use-case name, such as `Doctrinal Clarification` or `Catechetical Learning`.

`format`: Either `binary` or `mcq`.

`risk_level`: Estimated evaluation risk level: `LOW`, `MEDIUM`, or `HIGH`.

`topic_domain`: The doctrinal domain being tested, such as `Sacramental Theology` or `Scripture & Interpretation`.

`prompt`: The exact question text to send to the model.

`options`: For `mcq` rows, an object containing answer choices `A`, `B`, `C`, and `D`. For `binary` rows, this is `null`.

`source_type`: Source category used by the transformer. Current rows use `qa`.

`source`: Source metadata for the item.

`source.title`: Catholic Answers article or page title.

`source.url`: Catholic Answers source URL.

`source.reference`: Article section, topic, or local reference used for the item.

`source.catechism_references`: Supporting Catechism paragraph numbers or ranges.

`ground_truth`: The reference answer and scoring guidance.

`ground_truth.correct_answer`: The correct benchmark answer. For `binary`, this is `YES` or `NO`. For `mcq`, this is the correct option letter.

`ground_truth.justification`: Doctrinal explanation of the correct answer, including explicit CCC references.

`ground_truth.required_elements`: Concepts that should appear in a strong answer.

`ground_truth.prohibited_moves`: Doctrinal errors or misleading moves that should be penalized.

`ground_truth.scoring_anchors`: Rubric guidance for grading model explanations.

`ground_truth.scoring_anchors.score_5`: Strong answer description.

`ground_truth.scoring_anchors.score_3`: Partially correct answer description.

`ground_truth.scoring_anchors.score_1`: Incorrect or seriously deficient answer description.
