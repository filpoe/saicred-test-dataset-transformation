# SAICRED Catholic QA Dataset Pipeline

This repository is a small pipeline for building evaluation datasets that test whether an AI system answers Catholic doctrine questions accurately, consistently, and with the right level of theological precision.

The dataset is generated in two forms:

1. **Intermediate dataset**: review-friendly source data with one parent question, four variants, answer metadata, source attribution, and scoring guidance.
2. **Final dataset**: flattened benchmark data where each question variant becomes its own evaluation row.

The separation matters. The intermediate file is where humans and models can reason about doctrine, variants, answer keys, and sources. The final file is optimized for running evaluations.

## What We Are Trying To Achieve

The goal is to produce a benchmark dataset that can catch common Catholic-doctrine failure modes, including:

- treating Catholic doctrine as merely one opinion among many
- defaulting to generic Protestant assumptions where Catholic teaching differs
- reducing sacramental or moral doctrines to symbols, feelings, or intentions
- mishandling adversarial framing
- giving plausible but incomplete answers

Each parent item has four variants:

- `neutral`: plain baseline wording
- `christian`: general Christian framing that may expose generic or Protestant defaults
- `catholic`: explicit Catholic-authority framing
- `adversarial`: misleading, emotional, or objection-style framing

The final benchmark should test not only whether the model knows the answer, but whether it remains stable when the same doctrine is asked from different angles.

## How The Pipeline Works

```text
Catholic Answers source material
        |
        v
prompt_catholic_benchmark_qa_generation.md
        |
        v
data/*_intermediate.json
        |
        |  repeat batch append until target size is reached
        v
data/*_intermediate.json
        |
        v
transform_intermediate_to_final.py
        |
        v
data/*_final.json
```

The generation prompt creates intermediate JSON from Catholic Answers articles or article excerpts. Each intermediate parent item starts from one doctrinal target, then formulates that target in four question styles so we can test whether a model stays doctrinally consistent across different framings.

The transformer expands each parent item into four final benchmark rows:

```text
1.1 neutral      Plain wording with no explicit religious framing.
1.2 christian    General Christian wording that can expose generic or Protestant defaults.
1.3 catholic     Explicit Catholic-authority wording that asks for Magisterial precision.
1.4 adversarial  Objection-style wording that tests whether the model resists misleading framing.
```

## Key Files

`prompt_catholic_benchmark_qa_generation.md`: prompt used to generate new intermediate dataset items by pulling doctrinal source material from Catholic Answers through their website, `catholic.com`. The prompt expects either a Catholic Answers URL or article text, then asks the model to extract doctrinal claims, create question variants, assign answer keys, and preserve source attribution.

`master_dataset_workflow_prompt.md`: operator prompt that tells an LLM agent how to run the batch workflow end to end, including asking for the target dataset size, batch size, existing intermediate file, Catholic Answers sources, duplicate checks, append steps, final transformation, validation, and tests.

`intermediate_qa_schema_v2.json`: expected structure for newly generated intermediate data.

`final_qa_schema.md`: target flattened benchmark format.

`transform_intermediate_to_final.py`: Python script that converts intermediate JSON into final JSON.

`append_intermediate_batch.py`: Python script that validates a newly generated intermediate batch, rejects exact or near duplicates, and writes the next accumulated intermediate JSON file.

`data/`: current generated dataset files that should be committed.

`archived_data/`: older generated dataset files. This folder is ignored by Git and should not be committed.

`tests/test_dataset_validation.py`: validation tests for schema, transformation behavior, and the checked-in sample dataset.

## Current Dataset

The current checked-in sample dataset is:

```text
data/saicred_eval_qa_20_sample_2026-04-19_v1_intermediate.json
data/saicred_eval_qa_20_sample_2026-04-19_v1_final.json
```

This sample follows `intermediate_qa_schema_v2.json`, including per-variant `variant_ground_truth` so adversarial variants can preserve objective truth even when their correct binary label differs from the neutral wording.

## Generate A New Dataset

This workflow assumes you are running in an environment where the LLM agent can:

- read the repository files, especially `master_dataset_workflow_prompt.md`, `prompt_catholic_benchmark_qa_generation.md`, `intermediate_qa_schema_v2.json`, and `final_qa_schema.md`
- write new JSON files into `data/`
- run shell commands such as `python3 -m json.tool`, `python3 append_intermediate_batch.py`, `python3 transform_intermediate_to_final.py`, and `python3 -m unittest discover -s tests`
- access Catholic Answers source material from `catholic.com`, either through web access or through article text provided by the user
- keep `archived_data/` local and ignored by Git

If the LLM agent does not have web access, provide the Catholic Answers article text directly. If the agent cannot run shell commands, it can still generate intermediate JSON, but a human should run the transform and validation commands afterward.

Recommended path: give `master_dataset_workflow_prompt.md` to an LLM agent and let it run the full workflow. The master prompt instructs the agent to ask for the target dataset size, batch size, existing intermediate file, and Catholic Answers source material. It then generates a new batch, checks for duplicates, appends it to the accumulated intermediate file, and delays transformation until the target size is reached.

For a 100-parent-item dataset, prefer batches of 10-25 items. A good default is five batches of 20. This is usually better than generating all 100 at once because the model can compare against the existing intermediate file, avoid duplicates, and keep doctrinal quality higher.

Use the manual workflow below only if you want to perform each step yourself:

1. Open `prompt_catholic_benchmark_qa_generation.md`.
2. Provide Catholic Answers source material, either as a URL or article text.
3. Ask the model to generate only the next batch of intermediate-format items.
4. Save the generated batch JSON in `data/` using the naming convention below.
5. Validate the batch JSON.
6. Append the batch to the current accumulated intermediate file.
7. Repeat until the target parent-item count is reached.
8. Transform the completed intermediate file into final format.
9. Validate the final JSON.
10. Run the test suite.
11. Move older generated data into `archived_data/`.

## File Naming

Generated dataset files should use this pattern:

```text
saicred_eval_qa_<sample_size>_sample_<yyyy-mm-dd>_v<version>_<stage>.json
```

Example:

```text
data/saicred_eval_qa_20_sample_2026-04-19_v2_intermediate.json
data/saicred_eval_qa_20_sample_2026-04-19_v2_final.json
```

Use:

- `_batch.json` for newly generated batch files that have not yet been appended
- `_intermediate.json` for generated source data
- `_final.json` for transformed benchmark data
- `v1`, `v2`, etc. when regenerating on the same date or materially changing the dataset

For batch generation, `<sample_size>` should describe the item count in that file. For example, a 20-item batch can be saved as `*_20_sample_*_batch.json`, then appended to an existing 40-item intermediate file to produce a new `*_60_sample_*_intermediate.json`.

## Validate Intermediate Batch JSON

First check that the generated batch file is valid JSON:

```bash
python3 -m json.tool data/saicred_eval_qa_20_sample_2026-04-19_v2_batch.json
```

For newly generated data, also make sure it follows `intermediate_qa_schema_v2.json`.

Important intermediate-format rules:

- `type` is either `yes_no` or `multiple_choice`
- `yes_no` items use `answers.correct: null` and `answers.incorrect: []`
- `multiple_choice` items use `answers.options` with `A`, `B`, `C`, and `D`
- every variant has its own entry in `variant_ground_truth`
- variant-specific binary answers may differ when the wording requires it

For example, a neutral question may correctly answer `YES`, while an adversarial version of the same doctrinal target may correctly answer `NO`.

## Append A Batch

Append a validated batch to the current accumulated intermediate file:

```bash
python3 append_intermediate_batch.py \
  data/saicred_eval_qa_40_sample_2026-04-19_v1_intermediate.json \
  data/saicred_eval_qa_20_sample_2026-04-19_v2_batch.json \
  data/saicred_eval_qa_60_sample_2026-04-19_v1_intermediate.json \
  --expected-total 60
```

The append script checks:

- both files are valid intermediate JSON arrays
- every item follows the v2 schema rules
- the new batch does not contain exact duplicate question variants
- the new batch does not contain likely near-duplicates of existing items
- the output contains the expected total count, when `--expected-total` is provided

If the script reports a duplicate, revise or replace the batch item. Do not append duplicate data just to reach the target count.

## Transform Intermediate To Final

Run the transformer only after the accumulated intermediate file reaches the desired total size, unless you intentionally need a temporary final file for review.

Run:

```bash
python3 transform_intermediate_to_final.py \
  data/saicred_eval_qa_20_sample_2026-04-19_v2_intermediate.json \
  data/saicred_eval_qa_20_sample_2026-04-19_v2_final.json
```

Then validate the final JSON:

```bash
python3 -m json.tool data/saicred_eval_qa_20_sample_2026-04-19_v2_final.json
```

The transformer maps:

- intermediate `yes_no` to final `binary`
- intermediate `multiple_choice` to final `mcq`
- one parent item to four final rows
- `variant_ground_truth` into each row's final `ground_truth`

## Final Format

The final dataset is a list of evaluation rows. Each row contains:

- `question_id`, such as `3.4`
- `parent_question_id`, such as `3`
- `variant_type`, such as `adversarial`
- `format`, either `binary` or `mcq`
- `prompt`
- `options`, only for MCQ rows
- `ground_truth.correct_answer`
- `ground_truth.justification`
- scoring guidance and prohibited failure modes

For binary rows, `ground_truth.correct_answer` is `YES` or `NO`.

For MCQ rows, `ground_truth.correct_answer` is `A`, `B`, `C`, or `D`.

## Tests

Run the tests before committing regenerated data:

```bash
python3 -m unittest discover -s tests
```

The tests check three things.

First, they validate structural rules:

- v2 intermediate items distinguish `yes_no` from `multiple_choice`
- binary items do not contain MCQ distractors
- MCQ items contain labeled `A-D` options
- final rows contain the expected benchmark fields

Second, they validate transformer behavior:

- variant-specific binary answers are preserved
- MCQ option keys and answer letters are preserved
- one intermediate parent item becomes four final rows

Third, they validate batch append behavior:

- valid new intermediate batches can be appended
- duplicate intermediate items are rejected before accumulation

Fourth, they validate the checked-in sample dataset against a curated doctrinal oracle:

- expected answer keys
- expected topic domains
- expected binary or MCQ format
- core doctrinal concepts that should appear in the prompt, options, or ground truth

This doctrinal test is intentionally curated. It does not prove Catholic doctrine automatically; it prevents accidental regressions in the known sample dataset.

## Archiving Old Data

Keep the current dataset pair in `data/`.

Move older generated files into `archived_data/`:

```bash
mv data/old_dataset_intermediate.json archived_data/
mv data/old_dataset_final.json archived_data/
```

`archived_data/` is ignored by Git via `.gitignore`, so archived datasets remain local.

## Before Committing

Use this checklist:

1. Validate any new batch JSON.
2. Append the batch and validate the accumulated intermediate JSON.
3. If the dataset is complete, transform it into final JSON.
4. If a final file was produced, validate the final JSON.
5. Run `python3 -m unittest discover -s tests`.
6. Move older generated files into `archived_data/`.
7. Check `git status` and confirm `archived_data/` is ignored.
8. Commit the current dataset, schemas, prompts, scripts, tests, and README changes.
