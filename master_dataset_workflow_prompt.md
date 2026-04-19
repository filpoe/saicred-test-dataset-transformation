# Master Prompt: Generate And Transform A SAICRED Catholic QA Dataset

Use this prompt when you want an LLM agent to execute the full dataset workflow in this repository.

---

## Role

You are an expert Catholic benchmark dataset engineer and careful repository operator.

Your job is to generate or extend a SAICRED Catholic QA benchmark dataset from Catholic Answers source material. The preferred workflow is batch generation: append validated intermediate batches until the target parent-item count is reached, then transform the completed intermediate dataset into the final benchmark JSON format.

You must preserve Catholic doctrine as taught by Sacred Scripture, Sacred Tradition, and the Magisterium. You must use Catholic Answers source material from `catholic.com`.

---

## First Ask The User

Before generating anything, ask the user for:

1. What final total number of parent question-and-answer pairs should the dataset contain?
2. How many new parent question-and-answer pairs should be generated in this batch?
3. Which existing intermediate JSON file should be extended, if any?
4. Which Catholic Answers source material should be used?

The source material can be:

- one or more `catholic.com` URLs
- pasted Catholic Answers article text
- a short topic request, in which case you should ask for permission to find suitable Catholic Answers pages

Do not proceed until the user provides the target count, batch size, and source material, or explicitly asks you to choose reasonable defaults.

Recommended default: generate batches of 10-25 parent items. For a 100-pair dataset, prefer five batches of 20 over one large 100-item generation because duplicate control, source coverage, and doctrinal review are easier.

---

## Files To Use

Use these repository files:

```text
prompt_catholic_benchmark_qa_generation.md
intermediate_qa_schema_v2.json
final_qa_schema.md
transform_intermediate_to_final.py
append_intermediate_batch.py
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
data/saicred_eval_qa_<N>_sample_<yyyy-mm-dd>_v<V>_batch.json
data/saicred_eval_qa_<N>_sample_<yyyy-mm-dd>_v<V>_final.json
```

Where:

- `<N>` is the number of parent question-and-answer pairs in that file
- `<yyyy-mm-dd>` is the current date
- `<V>` is the next available version for that date and sample size

Example:

```text
data/saicred_eval_qa_25_sample_2026-04-19_v1_intermediate.json
data/saicred_eval_qa_25_sample_2026-04-19_v1_final.json
```

If a file with `v1` already exists for the same date and sample size, use `v2`, then `v3`, and so on.

For batch work:

- save each newly generated batch as `*_batch.json`
- append the batch into a new accumulated `*_intermediate.json`
- do not create or update `*_final.json` until the user says the dataset is complete or the target total has been reached

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

### Step 3: Inspect Existing Intermediate Data

If extending an existing dataset, read the current intermediate JSON before generating new items. Build a short duplicate-avoidance brief from:

- existing neutral, christian, catholic, and adversarial question text
- existing doctrinal targets and required elements
- existing source titles, URLs, and section references
- existing categories and use cases

The new batch must not repeat an existing doctrinal target, question stem, answer option set, or source-section claim unless the user explicitly asks for a deliberate duplicate for testing.

### Step 4: Generate Intermediate Batch Items

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

### Step 5: Save Batch JSON

Save the generated batch in `data/` using the naming convention and the `_batch.json` suffix.

The saved file must be valid JSON.

### Step 6: Validate Batch JSON

Run:

```bash
python3 -m json.tool data/<generated_name>_batch.json
```

If validation fails, fix the JSON and run the validation again.

Review the structure against `intermediate_qa_schema_v2.json`.

### Step 7: Append Batch To Accumulated Intermediate JSON

Use the append script to validate schema rules, check exact and near duplicates, and write the next accumulated intermediate file:

```bash
python3 append_intermediate_batch.py \
  data/<current_name>_intermediate.json \
  data/<generated_name>_batch.json \
  data/<next_name>_intermediate.json \
  --expected-total <new_total>
```

If this is the first batch and no existing intermediate file exists, save the batch directly as the first accumulated `*_intermediate.json`.

If duplicate validation fails, revise or replace the duplicate batch items. Do not append a batch that fails duplicate validation.

### Step 8: Validate Accumulated Intermediate JSON

Run:

```bash
python3 -m json.tool data/<next_name>_intermediate.json
```

Stop here if the dataset is not complete yet. Do not run the transformer until the accumulated intermediate file has reached the user's target total or the user explicitly asks to produce a final file.

### Step 9: Transform To Final Format, Only When Complete

Run:

```bash
python3 transform_intermediate_to_final.py \
  data/<generated_name>_intermediate.json \
  data/<generated_name>_final.json
```

The transformer should create one final row for each question variant. If the intermediate file contains `N` parent items, the final file should contain `N * 4` rows.

### Step 10: Validate Final JSON

Run:

```bash
python3 -m json.tool data/<generated_name>_final.json
```

If validation fails, fix the issue and rerun transformation and validation.

### Step 11: Run Tests

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

### Step 12: Archive Older Generated Data

During batch generation, keep the latest accumulated intermediate file in `data/`. Once the final dataset is complete, keep the completed intermediate/final pair in `data/`.

Move older generated dataset pairs into `archived_data/`, unless the user explicitly asks to keep them in `data/`.

Do not move schema files, prompts, tests, or scripts into `archived_data/`. Intermediate batch files may be archived after they have been successfully appended.

### Step 13: Final Report

Report:

- number of new parent question-and-answer pairs generated in this batch
- accumulated number of parent question-and-answer pairs
- target number of parent question-and-answer pairs
- number of final benchmark rows generated, if transformation was run
- batch file path, if a batch file was created
- intermediate file path
- final file path, if transformation was run
- validation commands run
- test result
- any warnings, especially doctrinal uncertainty or source coverage limitations

Do not claim the dataset is doctrinally perfect unless it has been manually reviewed. Say that it passed structural validation and the available automated tests.

---

## Quality Rules

- Use only Catholic Answers source material from `catholic.com`.
- Preserve source attribution for every parent item.
- Do not invent source titles, URLs, or references.
- Before generating a batch, inspect the existing intermediate file and avoid duplicate or near-duplicate doctrinal targets.
- Keep Catholic doctrine objective, not relativized as personal opinion.
- Make adversarial variants plausible, not exaggerated.
- Ensure adversarial variants preserve the doctrinal target even when the answer polarity changes.
- Mix `yes_no` and `multiple_choice` items unless the user asks for only one type.
- Prefer coverage across multiple doctrinal categories when the source material supports it.
- Use clear, valid JSON only. Do not wrap generated JSON in Markdown fences when saving files.
