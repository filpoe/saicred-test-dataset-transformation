# SAICRED Catholic QA Dataset Pipeline

This repository builds benchmark datasets for testing whether LLMs answer Catholic doctrine questions accurately, consistently, and with appropriate theological precision.

The dataset is a JSON array of evaluation rows. Each row contains one prompt, source references, the correct ground-truth answer, and guidance for judging the quality of the model's explanation.

## What The Dataset Tests

The benchmark is designed to catch common Catholic-doctrine failure modes:

- treating Catholic doctrine as merely one opinion among many
- defaulting to generic Protestant assumptions where Catholic teaching differs
- reducing sacramental or moral doctrines to symbols, feelings, or intentions
- mishandling adversarial framing
- giving plausible but incomplete answers

Each parent question is written in four variants:

- `neutral`: plain baseline wording
- `christian`: general Christian framing that may expose generic or Protestant defaults
- `catholic`: explicit Catholic-authority framing
- `adversarial`: objection-style or misleading framing

Every row has its own answer key. This matters because an adversarial question may reverse the proposition and require a different `YES` or `NO` answer than the neutral wording.

## How The Workflow Works

```text
Generate dataset rows from catholic.com
        |
        v
Validate JSON structure
        |
        v
Check for overlap with existing datasets
        |
        v
Validate doctrine and logic against CCC references
        |
        v
Save dataset and validation reports
```

The source corpus is [Catholic Answers](https://www.catholic.com/). Each row must also include supporting references to the Catechism of the Catholic Church (`CCC`).

Use `prompt_generate_dataset_from_catholic_com.md` to generate rows, and `dataset_workflow.py` to validate and save them.

## Key Files

`prompt_generate_dataset_from_catholic_com.md`: prompt for generating new dataset rows from Catholic Answers.

`qa_schema_reference.json`: compact example of the expected JSON structure.

`dataset_workflow.py`: main workflow script for validating, saving, checking overlap, and optionally appending new data.

`validate_dataset_schema.py`: validates JSON structure.

`validate_dataset_redundancy.py`: checks whether new questions overlap existing datasets in `data/`.

`validate_doctrine_and_logic.py`: checks doctrinal and logical consistency, using CCC-backed validation.

`validate_against_catechism.py`: lower-level Catechism validator.

`data/`: committed dataset files.

`data_validation_results/`: local validation reports. JSON files in this folder are ignored by Git.

## Generate A New Dataset

There are two supported ways to create a dataset: use the master prompt with an LLM agent, or run the generation and validation steps manually.

### Recommended: LLM Agent Workflow

Use this when an LLM agent has access to this repository and can read/write files.

1. Open `master_dataset_workflow_prompt.md`.
2. Give that prompt to the LLM agent.
3. Answer the agent's setup questions:
   - how many parent question groups to generate
   - whether to check existing `data/*.json` files for overlap
   - whether to append the new batch to an existing cumulative dataset
4. Let the agent generate a draft dataset, run validation, save the accepted dataset in `data/`, and save reports in `data_validation_results/`.
5. Review the validation summary before using the dataset.

The master prompt tells the LLM to use [Catholic Answers](https://www.catholic.com/) as the source corpus and to run doctrinal auto-fix when validation finds correctable CCC-reference issues. These are workflow defaults, not separate decisions the user needs to make each run.

### Manual Workflow

Use this when you want to generate the JSON yourself and then run the repository scripts.

1. Open `prompt_generate_dataset_from_catholic_com.md`.
2. Use it with an LLM to generate a JSON array of dataset rows.
3. Save the draft outside `data/`, for example:

```text
tmp/generated_draft_dataset.json
```

4. Validate and save the draft as a standalone dataset:

```bash
python3 dataset_workflow.py \
  --draft-dataset path/to/generated_draft_dataset.json \
  --parent-groups 20 \
  --check-existing \
  --no-append
```

5. If you want this batch appended to an existing cumulative dataset, use `--append-to` instead of `--no-append`:

```bash
python3 dataset_workflow.py \
  --draft-dataset path/to/generated_draft_dataset.json \
  --parent-groups 20 \
  --check-existing \
  --append-to data/saicred_eval_qa_100_sample_2026-04-19_v1.json
```

6. Check the generated outputs:

- a new dataset file in `data/`
- validation reports in `data_validation_results/`
- an appended cumulative dataset, if requested

The `--parent-groups` value must match the number of parent question groups in the draft. Each parent group produces four rows, one for each variant.

## Validation

The workflow runs three checks.

Schema validation checks that rows have the required fields, parent groups have four variants, binary answers use `YES` or `NO`, MCQ answers use `A-D`, and sources/CCC references are present.

Redundancy validation checks for overlap with existing datasets, including near-duplicate prompts, repeated doctrinal targets, repeated source sections, and repeated MCQ option sets.

Doctrinal and logical validation checks that answers align with Catholic teaching, CCC references are present, MCQ choices are coherent, and adversarial wording does not accidentally invert the answer key.

Manual commands:

```bash
python3 validate_dataset_schema.py data/saicred_eval_qa_100_sample_2026-04-19_v1.json
python3 validate_dataset_redundancy.py path/to/generated_draft_dataset.json --existing-dir data
python3 validate_doctrine_and_logic.py data/saicred_eval_qa_100_sample_2026-04-19_v1.json
python3 -m unittest discover -s tests
```

## File Naming

Dataset files:

```text
data/saicred_eval_qa_<sample_size>_sample_<yyyy-mm-dd>_v<version>.json
```

Validation reports:

```text
data_validation_results/<dataset_stem>_<validator>_validation_results.json
```

## Dataset Row Structure

Each row contains:

- `question_id`, such as `3.4`
- `parent_question_id`, such as `3`
- `variant_type`, such as `neutral`, `christian`, `catholic`, or `adversarial`
- `format`, either `binary` or `mcq`
- `prompt`
- `options`, only for MCQ rows
- `source`, including Catholic Answers and CCC references
- `ground_truth.correct_answer`
- `ground_truth.justification`
- `ground_truth.required_elements`
- `ground_truth.prohibited_moves`
- `ground_truth.scoring_anchors`

For binary rows, `ground_truth.correct_answer` is `YES` or `NO`.

For MCQ rows, `ground_truth.correct_answer` is `A`, `B`, `C`, or `D`.

See `data/README.md` for more detail about how to use the dataset for LLM evaluation.
