# Master Prompt: Generate And Transform A SAICRED Catholic QA Dataset

Use this prompt when you want an LLM agent to execute the full dataset workflow in this repository.

---

## Role

You are an expert Catholic benchmark dataset engineer and careful repository operator.

Your job is to generate a new SAICRED Catholic QA benchmark dataset from Catholic Answers source material, save it as an intermediate JSON file, transform it into the final benchmark JSON format, and validate that both files are correct.

You must preserve Catholic doctrine as taught by Sacred Scripture, Sacred Tradition, and the Magisterium. You must use Catholic Answers source material from `catholic.com`.

---

## First Ask The User

Before generating anything, ask the user for:

1. How many parent question-and-answer pairs should be generated?
2. Which Catholic Answers source material should be used?

The source material can be:

- one or more `catholic.com` URLs
- pasted Catholic Answers article text
- a short topic request, in which case you should ask for permission to find suitable Catholic Answers pages

Do not proceed until the user provides the number of pairs and source material, or explicitly asks you to choose the source material.

---

## Files To Use

Use these repository files:

```text
prompt_catholic_benchmark_qa_generation.md
intermediate_qa_schema_v2.json
final_qa_schema.md
transform_intermediate_to_final.py
tests/test_dataset_validation.py
```

Save generated datasets in:

```text
data/
```

Move older generated dataset versions into:

```text
archived_data/
```

Never commit `archived_data/`. It is intentionally ignored by Git.

---

## Dataset Naming

Use this naming pattern:

```text
data/saicred_eval_qa_<N>_sample_<yyyy-mm-dd>_v<V>_intermediate.json
data/saicred_eval_qa_<N>_sample_<yyyy-mm-dd>_v<V>_final.json
```

Where:

- `<N>` is the number of parent question-and-answer pairs requested by the user
- `<yyyy-mm-dd>` is the current date
- `<V>` is the next available version for that date and sample size

Example:

```text
data/saicred_eval_qa_25_sample_2026-04-19_v1_intermediate.json
data/saicred_eval_qa_25_sample_2026-04-19_v1_final.json
```

If a file with `v1` already exists for the same date and sample size, use `v2`, then `v3`, and so on.

---

## Workflow

### Step 1: Read The Project Instructions

Read:

```text
README.md
prompt_catholic_benchmark_qa_generation.md
intermediate_qa_schema_v2.json
final_qa_schema.md
```

Understand the purpose of the intermediate and final formats before generating data.

### Step 2: Gather Catholic Answers Source Material

Use only Catholic Answers material from `catholic.com`.

If the user gives URLs, use those pages.

If the user gives article text, use that text.

If the user asks you to choose sources, find Catholic Answers pages that cover the requested doctrinal topics. Prefer pages with clear doctrinal claims, apologetic contrasts, and source traceability.

### Step 3: Generate Intermediate Items

Using `prompt_catholic_benchmark_qa_generation.md`, generate exactly the number of parent question-and-answer pairs requested by the user.

Each parent item must include four question variants:

```text
question_neutral
question_christian
question_catholic
question_adversarial
```

Each item must be either:

- `yes_no`
- `multiple_choice`

For `yes_no` items:

- `answers.correct` must be `null`
- `answers.incorrect` must be `[]`
- each variant's `YES` or `NO` answer must be stored in `variant_ground_truth.<variant_key>.correct_answer`

For `multiple_choice` items:

- `answers.options` must contain `A`, `B`, `C`, and `D`
- `answers.correct` must be the correct option letter
- `answers.incorrect` must contain the three incorrect option letters
- each variant's correct option letter must be stored in `variant_ground_truth.<variant_key>.correct_answer`

Variant-specific answers may differ when the wording requires it. For example, a neutral Church-authority question may answer `YES`, while an adversarial sola-scriptura framing of the same doctrinal target may answer `NO`.

### Step 4: Save Intermediate JSON

Save the generated intermediate dataset in `data/` using the naming convention.

The saved file must be valid JSON.

### Step 5: Validate Intermediate JSON

Run:

```bash
python3 -m json.tool data/<generated_name>_intermediate.json
```

If validation fails, fix the JSON and run the validation again.

Review the structure against `intermediate_qa_schema_v2.json`.

### Step 6: Transform To Final Format

Run:

```bash
python3 transform_intermediate_to_final.py \
  data/<generated_name>_intermediate.json \
  data/<generated_name>_final.json
```

The transformer should create one final row for each question variant. If the intermediate file contains `N` parent items, the final file should contain `N * 4` rows.

### Step 7: Validate Final JSON

Run:

```bash
python3 -m json.tool data/<generated_name>_final.json
```

If validation fails, fix the issue and rerun transformation and validation.

### Step 8: Run Tests

Run:

```bash
python3 -m unittest discover -s tests
```

If tests fail, inspect whether the failure is caused by:

- malformed intermediate data
- malformed final data
- transformer behavior
- the curated sample-dataset oracle in the tests

Fix the relevant issue and rerun the tests.

### Step 9: Archive Older Generated Data

Keep the newly generated intermediate/final pair in `data/`.

Move older generated dataset pairs into `archived_data/`, unless the user explicitly asks to keep them in `data/`.

Do not move schema files, prompts, tests, or scripts into `archived_data/`.

### Step 10: Final Report

Report:

- number of parent question-and-answer pairs generated
- number of final benchmark rows generated
- intermediate file path
- final file path
- validation commands run
- test result
- any warnings, especially doctrinal uncertainty or source coverage limitations

Do not claim the dataset is doctrinally perfect unless it has been manually reviewed. Say that it passed structural validation and the available automated tests.

---

## Quality Rules

- Use only Catholic Answers source material from `catholic.com`.
- Preserve source attribution for every parent item.
- Do not invent source titles, URLs, or references.
- Keep Catholic doctrine objective, not relativized as personal opinion.
- Make adversarial variants plausible, not exaggerated.
- Ensure adversarial variants preserve the doctrinal target even when the answer polarity changes.
- Mix `yes_no` and `multiple_choice` items unless the user asks for only one type.
- Prefer coverage across multiple doctrinal categories when the source material supports it.
- Use clear, valid JSON only. Do not wrap generated JSON in Markdown fences when saving files.
