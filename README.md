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

```json
{
  "script_id": "script-001",
  "question_id": "q-1",
  "question_text": "Prove ...",
  "answer_text": "Student parsed answer ...",
  "max_marks": 15,
  "factors": [
    {"name": "concept_accuracy", "weight": 6, "description": "Core concepts and correctness"},
    {"name": "derivation", "weight": 5, "description": "Logical derivation and completeness"},
    {"name": "clarity", "weight": 4, "description": "Presentation and notation"}
  ]
}
```

## CLI run

```bash
python run_exam_review.py \
  --input_file config/template/exam_parsed_script.sample.jsonl \
  --output_file outputs/review_results.jsonl \
  --reviewer_models gemini:gemini-1.5-pro,anthropic:claude-3-5-sonnet,openai:qwen-max \
  --factor_specialists concept_accuracy=gemini:gemini-1.5-pro,derivation=anthropic:claude-3-5-sonnet,clarity=openai:qwen-max \
  --supreme_model openai:gpt-4o \
  --debate_rounds 6 \
  --pairing_strategy all_to_all \
  --openai_api_key $OPENAI_API_KEY \
  --openai_base_url $OPENAI_BASE_URL \
  --anthropic_api_key $ANTHROPIC_API_KEY \
  --gemini_api_key $GEMINI_API_KEY
```

> `openai` provider is OpenAI-compatible; you can route Qwen/DeepSeek/etc through compatible base URLs.

## Engineering notes

- Provider routing uses stable `provider:model` IDs to minimize integration churn across environments.
- Core orchestration logic is split into small private methods for easier review and reduced merge-conflict risk during parallel development.
- Score parsing is defensive: invalid numeric fields are normalized using deterministic fallbacks.
