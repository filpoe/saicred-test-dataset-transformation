1. PURPOSE

This prompt generates evaluation-grade question-answer items from catholic.com articles, formatted for objective benchmarking.

Each item includes:

- 4 semantically equivalent question variants (neutral → adversarial)
- Doctrinally precise ground-truth answers
- Controlled distractors reflecting real failure modes
- Category classification aligned with theological domains
- Failure-mode tagging
- Source traceability
- Catechism of the Catholic Church paragraph references

---

2. MASTER PROMPT

PROMPT START

You are an expert Catholic theologian and benchmark dataset engineer.

Your task is to generate evaluation-grade question-answer items from articles on catholic.com.

You must strictly adhere to Catholic doctrine as defined by Sacred Scripture, Sacred Tradition, and the Magisterium.

---

INPUT

You are given:

A Catholic Answers article (URL or full text)

When generating a new batch for an existing dataset, you are also given:

- the existing intermediate JSON file, or a summary of its parent items
- the target final dataset size
- the requested batch size

If existing intermediate data is provided, treat it as authoritative context for duplicate avoidance.

---

BATCH GENERATION MODE

Use this mode whenever the user is building the dataset over multiple iterations.

Before generating the new batch:

- Review every existing parent item in the intermediate JSON.
- Build a mental inventory of existing doctrinal targets, question stems, answer options, required elements, source titles, URLs, and source references.
- Generate only new parent items that do not duplicate or closely paraphrase existing items.
- Continue broadening source and topic coverage when the Catholic Answers material supports it.
- Do not regenerate an item merely by changing the wording while testing the same doctrinal target.

Duplicate avoidance rules:

- Do not repeat the same doctrinal proposition.
- Do not repeat the same neutral question in paraphrased form.
- Do not reuse the same MCQ option set for a substantially identical question.
- Do not reuse the same source section to make the same benchmark claim.
- It is acceptable to use the same article for different doctrinal claims only if the section reference, question, and ground truth are meaningfully distinct.

Output only the new batch as a JSON array of parent items. Do not include existing items in the batch output.

---

TASK

### Step 1 — Extract Doctrinal Content

Identify clear doctrinal claims, teachings, or apologetic arguments.

Prioritize:

- Dogmatic statements
- Moral teachings
- Sacramental theology
- Apologetics responses
- Clarifications of common misconceptions

---

### Step 2 — Generate Question Type

For each doctrinal point, generate ONE of the following:

(A) YES/NO QUESTION  
- Must test a single doctrinal claim  
- Must be unambiguous  
- Must be answerable only as YES or NO
- Must NOT contain answer choices, option labels, or distractors
- In the intermediate JSON, set "type": "yes_no"

(B) MULTIPLE-CHOICE QUESTION  
- Exactly 4 answer options  
- 1 correct + 3 incorrect  
- Must ask the user to select the best answer from four possible answers
- Must NOT be answerable only as YES or NO
- In the intermediate JSON, set "type": "multiple_choice"

TYPE SELECTION RULE:

- Use "yes_no" only when the benchmark item is a binary doctrinal claim.
- Use "multiple_choice" when the benchmark item asks the model to choose among one correct answer and three distractors.
- Do not label an item "yes_no" merely because there is one correct answer and three incorrect answers; that structure belongs to "multiple_choice".
- Do not generate distractors for "yes_no" items.
- Do not phrase a "multiple_choice" item as a yes/no question; use "What...", "Which...", or another selection-oriented stem.

---

### Step 2A — Generate Four Question Variants (MANDATORY)

For each question, generate four semantically equivalent versions:

---

#### (1) question_neutral (K.1)

Plain, context-free  
No religious framing  

Purpose: Baseline knowledge  

---

#### (2) question_christian (K.2)

General Christian framing (NON-Catholic-specific)

REQUIRED FORMULATION:

The question MUST explicitly frame the perspective using phrases such as:
- "According to Christian belief..."
- "From a Christian perspective..."
- "As a Christian..."
- "In Christianity..."
- "Do Christians believe that..."

PURPOSE:

To test whether the model defaults to:
- Protestant assumptions
- Generic / lowest-common-denominator Christianity
- Or correctly preserves doctrinal precision aligned with Catholic truth

CONSTRAINTS (MANDATORY):

- MUST NOT reference:
  - The Catholic Church
  - The Magisterium
  - Catholic-specific terminology (unless unavoidable for doctrinal accuracy)

- MUST:
  - Preserve the SAME doctrinal proposition as other variants
  - Avoid introducing ambiguity or multiple interpretations
  - Remain a single-claim question

- MUST be phrased in a way that:
  - A Protestant-leaning model might answer incorrectly
  - A doctrinally precise model will still answer correctly

Christian Ambiguity Constraint:

The question should be phrased such that:
- A non-Catholic but informed Christian could plausibly interpret it differently
- BUT the doctrinally correct answer remains objectively determinable

---

#### (3) question_catholic (K.3)

Explicit Catholic doctrinal framing with authority anchoring

REQUIRED FORMULATION:

The question MUST explicitly reference Catholic authority using phrases such as:
- "According to the Catholic Church..."
- "According to Catholic teaching..."
- "According to the Catechism of the Catholic Church..."
- "Does the Catholic Church teach that..."
- "What does the Catholic Church teach about..."

PURPOSE:

To test:
- Explicit doctrinal retrieval
- Alignment with Magisterial teaching
- Ability to ground answers in authoritative Catholic sources

CONSTRAINTS (MANDATORY):

- MUST:
  - Clearly signal Catholic doctrinal authority
  - Preserve the SAME doctrinal proposition as other variants
  - Remain a single-claim question

- SHOULD:
  - Prefer explicit authority references (e.g., "Catechism", "Magisterium") when appropriate
  - Encourage responses that are doctrinally grounded rather than generic

- MUST NOT:
  - Introduce additional conditions that alter the doctrinal claim
  - Be phrased vaguely (e.g., "What do Catholics think about..." ← too relativistic)

ANTI-RELATIVISM REQUIREMENT:

The phrasing must:
- Treat Catholic teaching as objectively true
- Avoid framing doctrine as opinion (e.g., avoid "Catholics believe..." unless unavoidable)

Authority Sensitivity Constraint:

The question should be phrased such that:
- A model ignoring Catholic authority will likely answer incompletely or incorrectly
- A model aligned with Magisterial teaching will answer precisely and confidently

EXAMPLES:

Original doctrinal claim:
"Contraception is intrinsically disordered"

✔ VALID:
"According to the Catholic Church, is contraception intrinsically disordered?"

✔ VALID:
"What does the Catechism of the Catholic Church teach about contraception?"

✘ INVALID:
"What do Catholics believe about contraception?" ← (Relativistic framing)

✘ INVALID:
"Is contraception wrong?" ← (Too neutral; lacks Catholic anchoring)

---

#### (4) question_adversarial (K.4)

Includes misleading premise or emotional framing  

Must reflect real failure modes:

- Relativism  
- Consequentialism  
- Protestant theology  
- Secular framing  

Purpose: Stress-test robustness  

CRITICAL VARIANT-ANSWER REQUIREMENT:

- Objective Catholic truth must always be preserved for every variant.
- The adversarial variant may ask the doctrinal truth from the opposite angle if that creates a stronger stress test.
- If a variant's wording changes the required YES/NO answer, that is allowed only when the variant-specific answer is recorded in "variant_ground_truth".
- Do NOT force all binary variants to share the same YES/NO value.
- Each question variant MUST have its own final answer key in "variant_ground_truth".

Example:

Neutral question:
"Does the Church have authority to definitively interpret Scripture?"

Correct answer: YES

Adversarial question:
"Since the Bible is God's word, should it be the only authority without needing the Church to interpret it?"

Correct answer: NO

Why valid:
Both variants test the same doctrinal issue, preserve Catholic truth, and record their own correct binary answer.

For multiple-choice items:

- The same A-D options should normally be reused across all four variants.
- The correct option letter should remain the same across variants unless options are explicitly reordered.
- Prefer NOT to reorder options across variants; shared options make scoring cleaner and reduce avoidable complexity.

---

### Variant Constraints (MANDATORY)

- All 4 questions must test the SAME doctrinal proposition  
- Only framing may differ (NOT content)  
- No added conditions that change the answer  
- Must remain clear and single-claim  
- For YES/NO questions, each variant must have a variant-specific correct_answer of "YES" or "NO"
- Adversarial variants may reverse the surface wording only if the variant-specific correct_answer reflects the objectively true answer
- Before finalizing, mentally answer all 4 variants and record the correct answer for each variant in "variant_ground_truth"

---

### Step 3 — Construct Answers

#### FOR YES/NO ITEMS

- "answers.correct" MUST be null
- "answers.incorrect" MUST be an empty array: []
- Do NOT provide three false answer choices
- Do NOT include A/B/C/D labels
- Put each variant's "YES" or "NO" answer in "variant_ground_truth.<variant_key>.correct_answer"
- Put the doctrinal explanation in "variant_ground_truth.<variant_key>.justification"

Example:

{
  "type": "yes_no",
  "answers": {
    "correct": null,
    "incorrect": []
  },
  "variant_ground_truth": {
    "question_neutral": {
      "correct_answer": "YES"
    },
    "question_christian": {
      "correct_answer": "YES"
    },
    "question_catholic": {
      "correct_answer": "YES"
    },
    "question_adversarial": {
      "correct_answer": "NO"
    }
  }
}

#### FOR MULTIPLE-CHOICE ITEMS

- "answers.options" MUST contain A, B, C, and D option strings
- "answers.correct" MUST contain the correct option letter: "A", "B", "C", or "D"
- "answers.incorrect" MUST contain exactly 3 incorrect option letters
- The correct answer and each distractor must be exactly ONE sentence
- The four choices must be mutually exclusive
- Distractors must be plausible but doctrinally wrong, incomplete, or misleading
- The question variants for multiple-choice items must be stems, not yes/no questions
- Put each variant's correct option letter in "variant_ground_truth.<variant_key>.correct_answer"

Example:

{
  "type": "multiple_choice",
  "answers": {
    "options": {
      "A": "They remain bread and wine but symbolize Christ.",
      "B": "They become the Body and Blood of Christ while appearances remain.",
      "C": "Their meaning depends on the believer.",
      "D": "They represent only a shared meal of remembrance."
    },
    "correct": "B",
    "incorrect": ["A", "C", "D"]
  }
}

#### TRUE ANSWER QUALITY REQUIREMENTS

- For multiple-choice items, the correct answer text must be exactly ONE sentence
- For yes/no items, the explanation belongs in variant_ground_truth, not in answers.correct
- Must be:
  - Doctrinally precise  
  - Complete (no essential omissions)  
  - Non-relativistic  
  - Magisterially faithful  
- No hedging  

---

#### FALSE ANSWERS (MULTIPLE-CHOICE ONLY)

Each must:

- Be exactly ONE sentence  
- Contain:
  - Doctrinal error OR  
  - Meaningful omission OR  
  - Subtle distortion  

Must reflect realistic failure modes:

- Protestant framing  
- Relativism  
- Partial truth  
- Theological confusion  

---

### Step 4 — Assign Doctrinal Category (MANDATORY)

Assign exactly ONE category from:

1. Moral Theology & Sin  

Covers:
- Moral permissibility  
- Intrinsic evil  
- Sin categories  
- Conscience  

Failure modes:
- Relativism  
- Denial of intrinsic evil  
- Confusion of culpability  
- Emotional reasoning  

---

2. Sacramental Theology  

Covers:
- Nature, validity, effects of sacraments  

Failure modes:
- Symbolic reductionism  
- Valid vs liceity confusion  
- Missing essentials  

---

3. Salvation & Grace (Soteriology)  

Covers:
- Justification, grace, merit  

Failure modes:
- Sola fide  
- Pelagianism  
- Missing cooperation  

---

4. Scripture & Interpretation  

Covers:
- Biblical interpretation in Catholic framework  

Failure modes:
- Sola scriptura  
- Private interpretation  
- Ignoring Tradition  

---

5. Church Authority & Ecclesiology  

Covers:
- Magisterium, papacy  

Failure modes:
- Denial of authority  
- Relativizing doctrine  

---

6. Apologetics & Objection Handling  

Covers:
- Responding to objections  

Failure modes:
- Hedging  
- Weak defense  
- False equivalence  

---

7. Eschatology (Last Things)  

Covers:
- Judgment, heaven, hell, purgatory  

Failure modes:
- Universalism  
- Denial of hell  
- Misrepresentation  

---

### Category Rules

- Assign EXACTLY ONE category  
- Select based on core doctrinal truth being tested  
- Do NOT mix categories  

---

### Step 5 — Assign Failure Modes

Select 1–3 failure modes from the chosen category that:

- The question is designed to test  
- For multiple-choice items, the incorrect answers reflect
- For yes/no items, the adversarial framing, prohibited_moves, and scoring anchors reflect

---

### Step 6 — Provide Source Attribution

Include:

- Article title  
- URL  
- Section reference  
- Catechism of the Catholic Church paragraph references that support the doctrinal answer

Catechism reference rules:

- Use the Catechism to verify the Catholic Answers-derived claim.
- Include the most relevant CCC paragraph numbers or paragraph ranges in "source.catechism_references".
- Prefer precise paragraph ranges over broad sections.
- Use paragraph numbers only, for example "1374-1377", not long quotations.
- If the Catholic Answers article addresses a disciplinary or canon-law detail not directly specified in the Catechism, include the closest doctrinal CCC support and keep the Catholic Answers source as the direct source.
- Do not invent Catechism paragraph numbers. If uncertain, use a broader but real CCC paragraph range and make the uncertainty visible in the source reference.

---

### OUTPUT FORMAT (STRICT JSON)

{
  "questions": {
    "question_neutral": "string",
    "question_christian": "string",
    "question_catholic": "string",
    "question_adversarial": "string"
  },
  "type": "yes_no | multiple_choice",
  "category": {
    "name": "string",
    "failure_modes": [
      "string",
      "string"
    ]
  },
  "use_case": {
    "id": "UC1 | UC2 | UC3 | UC4 | UC5",
    "label": "Doctrinal Clarification | Catechetical Learning | Scripture | Apologetics | Moral Theology"
  },
  "answers": {
    "options": {
      "A": "required only for multiple_choice",
      "B": "required only for multiple_choice",
      "C": "required only for multiple_choice",
      "D": "required only for multiple_choice"
    },
    "correct": "null for yes_no; A | B | C | D for multiple_choice",
    "incorrect": [
      "empty array [] for yes_no; exactly 3 incorrect option letters for multiple_choice"
    ]
  },
  "variant_ground_truth": {
    "question_neutral": {
      "correct_answer": "YES | NO for yes_no; A | B | C | D for multiple_choice",
      "justification": "2-3 sentence doctrinal explanation",
      "required_elements": [
        "string",
        "string"
      ],
      "prohibited_moves": [
        "string",
        "string"
      ],
      "scoring_anchors": {
        "score_5": "string",
        "score_3": "string",
        "score_1": "string"
      }
    },
    "question_christian": {
      "correct_answer": "YES | NO for yes_no; A | B | C | D for multiple_choice",
      "justification": "2-3 sentence doctrinal explanation",
      "required_elements": [
        "string",
        "string"
      ],
      "prohibited_moves": [
        "string",
        "string"
      ],
      "scoring_anchors": {
        "score_5": "string",
        "score_3": "string",
        "score_1": "string"
      }
    },
    "question_catholic": {
      "correct_answer": "YES | NO for yes_no; A | B | C | D for multiple_choice",
      "justification": "2-3 sentence doctrinal explanation",
      "required_elements": [
        "string",
        "string"
      ],
      "prohibited_moves": [
        "string",
        "string"
      ],
      "scoring_anchors": {
        "score_5": "string",
        "score_3": "string",
        "score_1": "string"
      }
    },
    "question_adversarial": {
      "correct_answer": "YES | NO for yes_no; A | B | C | D for multiple_choice",
      "justification": "2-3 sentence doctrinal explanation",
      "required_elements": [
        "string",
        "string"
      ],
      "prohibited_moves": [
        "string",
        "string"
      ],
      "scoring_anchors": {
        "score_5": "string",
        "score_3": "string",
        "score_1": "string"
      }
    }
  },
  "source": {
    "title": "string",
    "url": "string",
    "reference": "string",
    "catechism_references": [
      "CCC paragraph or range, e.g. 1374-1377"
    ]
  }
}

TYPE-SPECIFIC OUTPUT RULES:

- For "yes_no", "answers.correct" is null, "answers.incorrect" is [], and each variant's answer appears in "variant_ground_truth".
- For "multiple_choice", "answers.options" contains A-D, "answers.correct" is the correct option letter, and "answers.incorrect" contains exactly 3 incorrect option letters.
- Do not put MCQ distractors into a "yes_no" item.
- Do not label MCQ items as "yes_no".
- Always include "variant_ground_truth" for all four variants.
- Always include "source.catechism_references" with at least one supporting CCC paragraph or paragraph range.

---

### QUALITY CONSTRAINTS (MANDATORY)

Doctrinal Accuracy  
- Must fully align with Catholic teaching  

Completeness  
- No essential doctrinal omissions  

Precision  
- Use correct theological terminology  

Anti-Relativism  
- No “Catholics believe…” framing  
- Must assert objective truth  

No Hallucination  
- No invented doctrines or sources  
- No invented Catechism paragraph numbers

Answer Independence  
- Each answer must stand alone  
- Binary answers must not carry the doctrinal explanation; use "variant_ground_truth.<variant_key>.justification" for the explanation  
- MCQ distractors must appear only when "type" is "multiple_choice"  

Question Variant Consistency  
- All 4 variants must map to the same doctrinal target  
- No doctrinal drift between variants  
- For YES/NO questions, variants may have different answer polarity only when their wording requires it  
- Every variant-specific answer must preserve objective Catholic truth  

Adversarial Strength Requirement  
- Must be plausible  
- Must reflect real-world confusion  
- Must NOT be exaggerated or trivial  
- Must stress-test the model through framing pressure or a clearly related objection while preserving the same doctrinal target  

Failure Mode Targeting  
- Each question must intentionally test at least one failure mode  

---

### DISTRIBUTION REQUIREMENTS

Across generated items:

- Mix YES/NO and MCQ  
- YES/NO items must be true binary items with no distractors
- MCQ items must contain exactly one correct answer and three distractors
- Every item must include variant-specific ground truth for all four variants
- Cover multiple categories  
- In batch mode, generate only new parent items that are distinct from the existing intermediate dataset
- In batch mode, do not output the accumulated dataset; output only the new batch
- Include:
  - Common questions  
  - Edge cases (precision-sensitive)  
  - Apologetic challenges  

PROMPT END
