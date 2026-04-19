JSON object representing the final format of the questions and answers for our AI benchmark:

[
  {
    "question_id": "K.V",
    "parent_question_id": K,
    "variant_type": "neutral | christian | catholic | adversarial",

    "use_case": "UC1 | UC2 | UC3 | UC4 | UC5",
    "use_case_label": "Doctrinal Clarification | Catechetical Learning | Scripture | Apologetics | Moral Theology",

    "format": "binary | mcq",
    "risk_level": "LOW | MEDIUM | HIGH",
    "topic_domain": "string",

    "prompt": "string",

    "options": {
      "A": "string",
      "B": "string",
      "C": "string",
      "D": "string"
    },

    "source_type": "tract | encyclopedia | qa",

    "ground_truth": {
      "correct_answer": "YES | NO | A | B | C | D",

      "justification": "2–3 sentence doctrinal explanation",

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
  }
]