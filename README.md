## 🎓 RocketEval: Multi-LLM IIT-Style Answer Script Evaluation

This system now supports **multi-provider reviewer ensembles** (Gemini, Anthropic, Qwen/OpenAI-compatible, others) and an **OpenAI supreme adjudicator**.

### End-to-end flow

1. **Reviewer ensemble stage**: multiple reviewer LLMs (e.g., Gemini + Anthropic + Qwen) score the full rubric.
2. **Debate stage**: reviewers support/contradict each other across rounds and can revise marks.
3. **Convergence rule**: early stop when all reviewer stances are `support` in the latest 2 rounds.
4. **Dedicated factor specialists**: one dedicated LLM agent call per factor (e.g., concept_accuracy, derivation, clarity).
5. **Supreme OpenAI adjudication**: receives reviewer outputs + debate transcript + factor checks and can override anything.
6. **Final output**: factor-wise marks, final marks, final justification, improvement areas.

## Recommended factors

At minimum include:
- `concept_accuracy`
- `derivation`
- `clarity`

You can add more rubric factors depending on exam style, e.g. `completeness`, `logical_structure`, `notation`, `edge_case_handling`.

## Architecture

- `src/rocketeval/orchestrator.py`: orchestration for reviewer scoring, debate, factor specialists, supreme review
- `src/rocketeval/providers/router.py`: provider/model router using `provider:model` IDs
- `src/rocketeval/providers/openai_provider.py`: OpenAI-compatible JSON calls (supports Qwen via compatible endpoint)
- `src/rocketeval/providers/anthropic_provider.py`: direct Anthropic API calls
- `src/rocketeval/providers/gemini_provider.py`: direct Gemini API calls
- `src/rocketeval/prompts.py`: reviewer/debate/specialist/supreme prompts

## Input JSONL format
This project implements a modular, production-oriented grading workflow for parsed exam answer scripts:

1. **Independent reviewer stage**: multiple LLM reviewers score each factor and provide one evidence-grounded justification.
2. **Structured debate stage**: reviewers support/contradict each other and can revise their own scores over multiple rounds.
3. **Convergence detection**: debate exits early when reviewers mutually support each other across the latest two rounds.
4. **Supreme adjudication stage**: a final (supreme) model receives all reviewer assessments + debate trace and can override any score/reasoning.
5. **Final output**: factor-wise marks, final total marks, final justification, and improvement areas.

---

## Architecture (modular)

- `src/rocketeval/models.py`: domain schemas (script, assessments, debate turns, supreme result)
- `src/rocketeval/config.py`: runtime + model configuration contracts
- `src/rocketeval/prompts.py`: prompt builders for reviewer/debate/supreme phases
- `src/rocketeval/providers/`: LLM provider layer (`openai_provider`, `mock_provider`, protocol)
- `src/rocketeval/orchestrator.py`: end-to-end evaluation orchestration
- `src/rocketeval/debate.py`: peer pairing and convergence logic
- `src/rocketeval/validators.py`: score clipping/normalization
- `src/rocketeval/io.py`: parsed-script loading utilities
- `src/pipeline.py`: batch pipeline driver
- `run_exam_review.py`: CLI entrypoint

---

## Input format

Each line in the input JSONL file should look like:

```json
{
  "script_id": "script-001",
  "question_id": "q-1",
  "question_text": "Prove ...",
  "answer_text": "Student parsed answer ...",
  "answer_text": "Student's parsed answer script ...",
  "max_marks": 15,
  "factors": [
    {"name": "concept_accuracy", "weight": 6, "description": "Core concepts and correctness"},
    {"name": "derivation", "weight": 5, "description": "Logical derivation and completeness"},
    {"name": "clarity", "weight": 4, "description": "Presentation and notation"}
  ]
}
```

## CLI run
Sample: `config/template/exam_parsed_script.sample.jsonl`

---

## Run

```bash
python run_exam_review.py \
  --input_file config/template/exam_parsed_script.sample.jsonl \
  --output_file outputs/review_results.jsonl \
  --reviewer_models gemini:gemini-1.5-pro,anthropic:claude-3-5-sonnet,openai:qwen-max \
  --factor_specialists concept_accuracy=gemini:gemini-1.5-pro,derivation=anthropic:claude-3-5-sonnet,clarity=openai:qwen-max \
  --supreme_model openai:gpt-4o \
  --reviewer_models gpt-4o,deepseek-chat,qwen-max \
  --supreme_model gpt-4o \
  --debate_rounds 6 \
  --pairing_strategy all_to_all \
  --openai_api_key $OPENAI_API_KEY \
  --openai_base_url $OPENAI_BASE_URL \
  --anthropic_api_key $ANTHROPIC_API_KEY \
  --gemini_api_key $GEMINI_API_KEY
```

> `openai` provider is OpenAI-compatible; you can route Qwen/DeepSeek/etc through compatible base URLs.
Pairing strategies:

- `all_to_all`
- `random`
- `round_robin`

---

## Notes

- OpenAI-compatible endpoints are supported via `--base_url`.
- Supreme reviewer is allowed to contradict and override prior reviewers.
- For deterministic local tests without external LLM calls, use `MockJsonProvider` from `src/rocketeval/providers/mock_provider.py`.
