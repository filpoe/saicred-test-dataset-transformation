# SAICRED Test Dataset Transformation

This repository supports creating Catholic doctrine benchmark datasets in two stages:

1. Generate a human-reviewable intermediate Q&A dataset from Catholic Answers source material.
2. Transform that intermediate dataset into the final flat evaluation format used by benchmark runs.

The project is designed to keep generation, review, and transformation separate. The intermediate format preserves source traceability, question variants, use cases, answer keys, and scoring guidance. The final format expands each parent question into four benchmark rows: neutral, Christian, Catholic, and adversarial.

## Repository Layout

```text
.
├── data/
│   ├── saicred_eval_qa_10_sample_2026-04-19_v1_intermediate.json
│   └── saicred_eval_qa_10_sample_2026-04-19_v1_final.json
├── archived_data/
├── final_qa_schema.md
├── intermediate_qa_schema_v2.json
├── prompt_catholic_benchmark_qa_generation.md
└── transform_intermediate_to_final.py
```

`data/` contains the latest generated dataset files that should be committed.

`archived_data/` contains older generated datasets. This folder is intentionally ignored by Git.

`prompt_catholic_benchmark_qa_generation.md` is the prompt used to generate new intermediate-format items from Catholic Answers material.

`intermediate_qa_schema_v2.json` documents the expected intermediate JSON structure.

`final_qa_schema.md` documents the final flattened benchmark format.

`transform_intermediate_to_final.py` converts intermediate JSON into final JSON.

Note: the current checked-in sample dataset was generated before `variant_ground_truth` was added to the intermediate schema. The transformer remains backward-compatible with that older shape, but newly generated datasets should follow `intermediate_qa_schema_v2.json`.

## Naming Convention

Generated dataset files should use:

```text
saicred_eval_qa_<sample_size>_sample_<yyyy-mm-dd>_v<version>_<stage>.json
```

Example:

```text
saicred_eval_qa_10_sample_2026-04-19_v1_intermediate.json
saicred_eval_qa_10_sample_2026-04-19_v1_final.json
```

Use `_intermediate.json` for generated source data and `_final.json` for transformed benchmark data. Increment `v1`, `v2`, etc. when regenerating a dataset on the same date or changing its contents materially.

## Generate A New Intermediate Dataset

1. Open `prompt_catholic_benchmark_qa_generation.md`.
2. Provide the Catholic Answers article URL or article text as the input.
3. Ask the model to generate the desired number of intermediate-format items.
4. Save the output JSON in `data/` using the naming convention above.

For example:

```text
data/saicred_eval_qa_10_sample_2026-04-19_v2_intermediate.json
```

Before transforming, validate that the generated file is valid JSON:

```bash
python3 -m json.tool data/saicred_eval_qa_10_sample_2026-04-19_v2_intermediate.json
```

## Intermediate Format Expectations

Each intermediate item represents one parent benchmark question and includes four variants:

```text
question_neutral
question_christian
question_catholic
question_adversarial
```

The supported question types are:

`yes_no`: A binary doctrinal claim. `answers.correct` should be `null`, `answers.incorrect` should be `[]`, and each variant's `YES` or `NO` answer should appear in `variant_ground_truth`.

`multiple_choice`: A four-option question. `answers.options` should contain `A`, `B`, `C`, and `D`; `answers.correct` should be the correct option letter; and `answers.incorrect` should contain the three incorrect option letters.

Use `variant_ground_truth` whenever variant wording changes the correct answer. For example, a neutral Church-authority question may have answer `YES`, while an adversarial sola-scriptura framing of the same doctrinal target may have answer `NO`.

## Transform To Final Format

Run:

```bash
python3 transform_intermediate_to_final.py \
  data/saicred_eval_qa_10_sample_2026-04-19_v2_intermediate.json \
  data/saicred_eval_qa_10_sample_2026-04-19_v2_final.json
```

Then validate the final JSON:

```bash
python3 -m json.tool data/saicred_eval_qa_10_sample_2026-04-19_v2_final.json
```

The transformer expands each parent item into four final rows with IDs like:

```text
1.1 neutral
1.2 christian
1.3 catholic
1.4 adversarial
```

For `yes_no` items, final `format` becomes `binary` and `ground_truth.correct_answer` is `YES` or `NO`.

For `multiple_choice` items, final `format` becomes `mcq`, `options` contains `A-D`, and `ground_truth.correct_answer` is the correct option letter.

## Run Tests

Run the validation test suite before committing new dataset changes:

```bash
python3 -m unittest discover -s tests
```

The tests validate:

- new v2 intermediate-format rules for binary and multiple-choice items
- variant-specific binary answers such as `YES, YES, YES, NO`
- labeled MCQ options and answer keys
- transformed final-format rows
- the checked-in final dataset under `data/`
- a curated doctrinal oracle for the checked-in sample dataset, including expected answer keys, topic domains, and core doctrinal concepts

## Archive Older Data

Keep only the latest generated dataset pair in `data/`.

Move older generated files into `archived_data/`:

```bash
mv data/old_dataset_intermediate.json archived_data/
mv data/old_dataset_final.json archived_data/
```

`archived_data/` is ignored by Git through `.gitignore`, so archived datasets remain local and are not committed.

## Recommended Workflow

1. Generate a new intermediate dataset with `prompt_catholic_benchmark_qa_generation.md`.
2. Save it in `data/` with a new versioned name.
3. Validate the intermediate JSON.
4. Transform it with `transform_intermediate_to_final.py`.
5. Validate the final JSON.
6. Run the test suite.
7. Move older generated data into `archived_data/`.
8. Review `git status` and commit only the current dataset, schemas, prompt, transformer, tests, and README changes.
