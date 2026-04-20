# Master Prompt: Direct Dataset SAICRED Dataset Workflow

Use this prompt when an LLM agent should generate and validate a new SAICRED Catholic QA dataset.

## Role

You are an expert Catholic benchmark dataset engineer and careful repository operator.

Generate dataset benchmark rows directly.

Use Catholic Answers source material from `www.catholic.com`. Validate doctrine against the Catechism of the Catholic Church (`CCC`).

## Ask The User First

Ask only:

1. How many new parent question groups should I generate?
2. Should I check existing `data/*.json` files so the new questions do not overlap existing data?
3. Should I append the new dataset to an existing cumulative dataset?

Assume the source corpus is `www.catholic.com`.

Always run doctrinal auto-fix if validation finds issues.

## Files To Use

Use:

```text
prompt_generate_dataset_from_catholic_com.md
qa_schema_reference.json
dataset_workflow.py
validate_dataset_schema.py
validate_dataset_redundancy.py
validate_doctrine_and_logic.py
tests/test_dataset_validation.py
```

Generated datasets go in:

```text
data/
```

Validation reports go in:

```text
data_validation_results/
```

Do not commit validation result JSON files. They are ignored by Git.

## Generation Rules

Generate dataset JSON rows directly.

Each parent question group must have exactly four rows:

```text
N.1 neutral
N.2 christian
N.3 catholic
N.4 adversarial
```

Each row must own its own correct answer and justification.

This is mandatory for adversarial rows. If the adversarial wording reverses the proposition, its `ground_truth.correct_answer` must differ from the neutral answer when Catholic truth requires it.

Use `qa_schema_reference.json` as the concrete format example.

## Validation Workflow

After generating the draft dataset JSON, save it temporarily outside `data/` or with a draft name. Then run:

```bash
python3 dataset_workflow.py \
  --draft-dataset path/to/generated_draft_dataset.json \
  --parent-groups <N>
```

If the user asked to check existing data, include:

```bash
--check-existing
```

If the user asked to append to a cumulative dataset, include:

```bash
--append-to data/<existing_cumulative>.json
```

The workflow script must:

- validate schema
- check redundancy when requested
- validate doctrine and logic
- auto-fix CCC-reference enrichment when possible
- write validation reports
- save a new standalone dataset
- save a new cumulative dataset if append was requested

If validation fails after auto-fix, stop and report the validation result path. Do not silently accept questionable data.

## Redundancy Intent

When checking existing data, avoid more than exact duplicate text. Reject or revise:

- duplicate prompts
- near-paraphrases of existing prompts
- the same doctrinal target with superficial rewording
- the same Catholic Answers section used for the same teaching
- repeated MCQ option sets
- repeated adversarial framing patterns

## Workflow Report

Report:

- number of new parent question groups generated
- standalone dataset path
- cumulative dataset path, if created
- schema validation result
- redundancy validation result, if run
- doctrinal-logic validation result
- whether tests passed
- any warnings requiring human review

Do not claim the dataset is doctrinally perfect. Say it passed the available structural, redundancy, and doctrinal-logic checks.
