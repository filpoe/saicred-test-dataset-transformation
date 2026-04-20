# Prompt: Generate SAICRED Catholic QA Dataset Rows

Use this prompt to generate SAICRED benchmark dataset rows.

## Role

You are an expert Catholic theologian and benchmark dataset engineer.

Your task is to generate dataset SAICRED Catholic QA benchmark rows from Catholic Answers source material at `www.catholic.com`.

Use Catholic Answers as the generation source and validate doctrinal content against the Catechism of the Catholic Church (`CCC`).

## User Inputs

Before generating rows, ask only:

1. How many new parent question groups should be generated?
2. Should existing `data/*.json` files be checked so the new dataset does not overlap existing questions?
3. Should the new dataset be appended to an existing cumulative dataset?

Assume the source corpus is `www.catholic.com`.

Always run doctrinal auto-fix if validation finds issues.

## Output Shape

Output a JSON array. Do not output Markdown fences.

Each parent question group must produce exactly four rows:

- `neutral` as question id `N.1`
- `christian` as question id `N.2`
- `catholic` as question id `N.3`
- `adversarial` as question id `N.4`

Each row must stand alone. Do not rely on another row to explain the answer.

## Required Row Fields

Each row must include:

- `question_id`
- `parent_question_id`
- `variant_type`
- `use_case`
- `use_case_label`
- `format`
- `risk_level`
- `topic_domain`
- `prompt`
- `options`
- `source_type`
- `source`
- `ground_truth`

Use `qa_schema_reference.json` as the concrete reference.

Use these use cases when appropriate:

- `UC1`: `Doctrinal Clarification`
- `UC2`: `Catechetical Learning`
- `UC3`: `Scripture`
- `UC4`: `Apologetics`
- `UC5`: `Moral Theology`

Use these topic domains when appropriate:

- `Moral Theology & Sin`
- `Sacramental Theology`
- `Salvation & Grace (Soteriology)`
- `Scripture & Interpretation`
- `Church Authority & Ecclesiology`
- `Apologetics & Objection Handling`
- `Eschatology (Last Things)`

## Formats

For binary rows:

- `format` must be `binary`
- `options` must be `null`
- `ground_truth.correct_answer` must be `YES` or `NO`

For MCQ rows:

- `format` must be `mcq`
- `options` must contain exactly `A`, `B`, `C`, and `D`
- `ground_truth.correct_answer` must be the correct option letter
- exactly one option must be doctrinally correct
- the other three options must be plausible but wrong, incomplete, or misleading

## Variants

The four variants must test the same doctrinal target, but each row owns its own answer.

This is especially important for adversarial questions. If adversarial wording reverses the proposition, the adversarial row must have its own correct answer.

Example:

- Neutral: "Does the Church have authority to interpret Scripture?" -> `YES`
- Adversarial: "Should Scripture be the only authority without the Church?" -> `NO`

Do not copy one answer blindly across all variants.

## Sources

Each row must include:

```json
"source": {
  "title": "Catholic Answers page title",
  "url": "https://www.catholic.com/...",
  "reference": "source section or local reference",
  "catechism_references": ["CCC paragraph or range"]
}
```

Rules:

- `source.url` must be from `catholic.com`.
- `source.catechism_references` must contain real CCC paragraph numbers or ranges.
- `ground_truth.justification` must include `See CCC ...`.
- Do not invent Catholic Answers pages or CCC references.

## Ground Truth

Each row must include:

```json
"ground_truth": {
  "correct_answer": "YES | NO | A | B | C | D",
  "justification": "2-3 sentence doctrinal explanation with See CCC ...",
  "required_elements": ["string"],
  "prohibited_moves": ["string"],
  "scoring_anchors": {
    "score_5": "string",
    "score_3": "string",
    "score_1": "string"
  }
}
```

The ground truth must be objective Catholic teaching, not a survey of opinions.

## Redundancy Avoidance

If existing data is provided or if the workflow loads existing `data/*.json`, avoid:

- duplicate prompts
- near-paraphrases of existing prompts
- the same doctrinal target with superficial rewording
- the same Catholic Answers section used for the same teaching
- repeated MCQ option sets
- repeated adversarial framing patterns

## Quality Rules

- Keep every row answerable as written.
- Keep adversarial prompts plausible, not exaggerated.
- Do not create vague "what do Catholics think" prompts.
- Do not put multiple doctrines into a single row.
- Do not include long quotations from Catholic Answers or the CCC.
- Preserve Catholic doctrine as taught by Scripture, Tradition, and the Magisterium.
