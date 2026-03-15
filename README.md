## 🎓 Exam Answer Evaluation with Multi-LLM Debate

RocketEval now includes a full answer-script evaluation pipeline designed for rigorous exam grading workflows:

1. Multiple reviewer LLMs independently grade each parsed answer script against weighted rubric factors.
2. Each reviewer returns:
   - factor-wise marks
   - total marks
   - one justification
3. Reviewers enter a multi-round debate to support or contradict peers and may revise scores.
4. If all reviewers support each other during the latest two rounds, debate converges early.
5. A supreme reviewer receives all scores, factors, and debate traces, and can override any prior decision.
6. Final outputs include:
   - final marks
   - final justification
   - improvement areas for the student

### Input format for parsed answer scripts

Each line in `input_file` must be JSON with this schema:

```json
{
  "script_id": "script-001",
  "question_id": "q-1",
  "question_text": "Prove ...",
  "answer_text": "Student's parsed answer script text ...",
  "max_marks": 15,
  "factors": [
    {"name": "concept_accuracy", "weight": 6, "description": "Core concepts and correctness"},
    {"name": "derivation", "weight": 5, "description": "Logical derivation and completeness"},
    {"name": "clarity", "weight": 4, "description": "Presentation and notation"}
  ]
}
```

### Run the pipeline

```bash
python src/run_exam_review.py \
  --input_file data/exam/parsed_scripts.jsonl \
  --output_file data/exam/review_results.jsonl \
  --reviewer_models gpt-4o,deepseek-chat,qwen-max \
  --supreme_model gpt-4o \
  --debate_rounds 6 \
  --pairing_strategy all_to_all
```

Pairing strategies:
- `all_to_all`: each reviewer debates against all peers every round.
- `random`: each reviewer debates a random peer each round.
- `round_robin`: each reviewer debates the next reviewer cyclically.