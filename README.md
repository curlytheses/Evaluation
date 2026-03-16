## 🎓 RocketEval: Multi-LLM IIT-Style Answer Script Evaluation

This system supports **multi-provider reviewer ensembles** (Gemini, Anthropic, Qwen/OpenAI-compatible, others) and an **OpenAI supreme adjudicator**.

### End-to-end flow

1. **Reviewer ensemble stage**: multiple reviewer LLMs (e.g., Gemini + Anthropic + Qwen) score the full rubric.
2. **Debate stage**: reviewers support/contradict each other across rounds and can revise marks.
3. **Convergence rule**: early stop when all reviewer stances are `support` in the latest 2 rounds.
4. **Dedicated factor specialists**: one dedicated LLM agent call per factor (e.g., concept_accuracy, derivation, clarity).
5. **Supreme OpenAI adjudication**: receives reviewer outputs + debate transcript + factor checks and can override anything.
6. **Final output**: factor-wise marks, final marks, final justification, improvement areas.

## Environment setup (.env)

Create a `.env` file in the repository root:

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=...   # optional for OpenAI-compatible routing (Qwen/DeepSeek/etc)
ANTHROPIC_API_KEY=...
GEMINI_API_KEY=...
```

The pipeline automatically loads `.env` (via `python-dotenv` if installed).

## Dependencies

Recommended runtime dependencies:

- `openai`
- `anthropic`
- `google-generativeai`
- `python-dotenv`
- `rich`

## CLI run

```bash
python run_exam_review.py \
  --input_file config/template/exam_parsed_script.sample.jsonl \
  --output_file outputs/review_results.jsonl \
  --reviewer_models gemini:gemini-1.5-pro,anthropic:claude-3-5-sonnet,openai:qwen-max \
  --factor_specialists concept_accuracy=gemini:gemini-1.5-pro,derivation=anthropic:claude-3-5-sonnet,clarity=openai:qwen-max \
  --supreme_model openai:gpt-4o \
  --debate_rounds 6 \
  --pairing_strategy all_to_all
```

## Recommended factors

At minimum include:
- `concept_accuracy`
- `derivation`
- `clarity`

You can add more rubric factors depending on exam style, e.g. `completeness`, `logical_structure`, `notation`, `edge_case_handling`.

## Engineering notes

- Provider routing uses stable `provider:model` IDs to minimize integration churn across environments.
- Core orchestration logic is split into small private methods for easier review and reduced merge-conflict risk during parallel development.
- Score parsing is defensive: invalid numeric fields are normalized using deterministic fallbacks.
