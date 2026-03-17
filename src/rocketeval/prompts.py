import json
from dataclasses import asdict
from .models import DebateTurn, FactorCheck, ParsedAnswerScript, ReviewerAssessment


def factor_schema(script: ParsedAnswerScript) -> str:
    return "\n".join(
        [f"- {f.name} (weight={f.weight}): {f.description}" for f in script.factors]
    )


def review_schema(script: ParsedAnswerScript) -> dict[str, object]:
    factor_props = {f.name: {"type": "number"} for f in script.factors}
    return {
        "type": "object",
        "properties": {
            "factor_scores": {
                "type": "object",
                "properties": factor_props,
                "required": list(factor_props.keys()),
            },
            "total_score": {"type": "number"},
            "justification": {"type": "string"},
        },
        "required": ["factor_scores", "total_score", "justification"],
    }


def review_prompt(script: ParsedAnswerScript) -> str:
    factor_template = {
        f.name: f"number (0–{f.weight})"
        for f in script.factors
    }
    
    return f"""
ROLE
You are an exam answerscript evaluator.

TASK
Evaluate the student's answer using the provided rubric factors.

INPUT
Question:
{script.question_text}

Student Answer:
{script.answer_text}

Max Marks:
{script.max_marks}

Rubric Factors:
{factor_schema(script)}

EVALUATION PROCESS
1. Carefully read the student answer.
2. Evaluate each rubric factor independently.
3. Award marks strictly within the allowed range.
4. Penalize factual errors, missing reasoning, or incomplete steps.
5. Do NOT assume information not present in the answer.

OUTPUT FORMAT (STRICT JSON ONLY)

{json.dumps({
    "factor_scores": factor_template,
    "total_score": "number",
    "justification": "Concise evidence-based reasoning referencing the answer"
}, indent=2)}

SCORING RULES
- factor_scores values must be between 0 and the factor weight.
- total_score must be between 0 and {script.max_marks}.
- sum(factor_scores) should approximately equal total_score (difference ≤ 0.25).
- justification must reference actual answer content.
""".strip()


def factor_review_prompt(script: ParsedAnswerScript, factor_name: str, factor_weight: float, factor_description: str) -> str:
    return f"""
ROLE
You are a specialist evaluator responsible for ONLY ONE rubric factor.

TASK
Evaluate the student answer for the specified factor.

INPUT
Question:
{script.question_text}

Student Answer:
{script.answer_text}

Factor To Evaluate
Name: {factor_name}
Weight: {factor_weight}
Description: {factor_description}

EVALUATION PROCESS
1. Focus only on this factor.
2. Ignore all other rubric factors.
3. Use strict evidence from the student's answer.
4. Do NOT infer missing information.

OUTPUT FORMAT (STRICT JSON ONLY)

{{
  "score": number,
  "justification": "Concise evidence-based justification focused on {factor_name}"
}}

SCORING RULES
- score must be within [0, {factor_weight}]
""".strip()


def debate_prompt(
    script: ParsedAnswerScript,
    reviewer_id: str,
    assessment: ReviewerAssessment,
    peers: list[ReviewerAssessment],
    prior_rounds: list[DebateTurn],
) -> str:

    peer_blob = [asdict(peer) for peer in peers if peer.reviewer_id != reviewer_id]
    round_blob = [asdict(r) for r in prior_rounds if r.reviewer_id == reviewer_id]

    return f"""
ROLE
You are reviewer {reviewer_id} participating in a multi-reviewer debate for grading.

TASK
Critically analyze peer reviewers' assessments and update your evaluation if necessary.

INPUT
Question:
{script.question_text}

Student Answer:
{script.answer_text}

Rubric Factors:
{factor_schema(script)}

Your Current Assessment
{json.dumps(asdict(assessment), indent=2)}

Peer Reviewer Assessments
{json.dumps(peer_blob, indent=2)}

Your Previous Debate Turns
{json.dumps(round_blob, indent=2)}

DEBATE PROCESS
1. Compare your assessment with each peer reviewer.
2. For each peer reviewer decide:
   - support
   - contradict
3. If contradicting:
   - explain the rubric disagreement
   - reference specific answer evidence.
4. If convinced by peers, revise your scores.

OUTPUT FORMAT (STRICT JSON ONLY)

{{
  "stance_by_reviewer": {{
      "<reviewer_id>": "support | contradict"
  }},
  "revised_factor_scores": {{
      "<factor_name>": number
  }},
  "revised_total_score": number,
  "revised_justification": "Updated reasoning referencing rubric and answer"
}}

RULES
- revised_total_score must remain within valid range.
- revised_factor_scores must follow factor weights.
- justification must clearly explain any revisions.
""".strip()


def supreme_prompt(
    script: ParsedAnswerScript,
    assessments: list[ReviewerAssessment],
    debate_transcript: list[DebateTurn],
    factor_checks: list[FactorCheck],
) -> str:

    return f"""
ROLE
You are the Supreme Reviewer responsible for final grading quality assurance.

You may override any reviewer decision if justified.

INPUT
Question:
{script.question_text}

Student Answer:
{script.answer_text}

Max Marks:
{script.max_marks}

Rubric Factors:
{factor_schema(script)}

Final Reviewer Assessments
{json.dumps([asdict(a) for a in assessments], indent=2)}

Debate Transcript
{json.dumps([asdict(t) for t in debate_transcript], indent=2)}

Factor Specialist Checks
{json.dumps([asdict(fc) for fc in factor_checks], indent=2)}

DECISION PROCESS
1. Review the student answer carefully.
2. Analyze reviewer scores and debate disagreements.
3. Check factor specialist evaluations.
4. Resolve inconsistencies or scoring errors.
5. Produce the final authoritative score.

OUTPUT FORMAT (STRICT JSON ONLY)

{{
  "final_factor_scores": {{
      "<factor_name>": number
  }},
  "final_total_score": number,
  "final_justification": "Clear reasoning referencing rubric and answer",
  "improvement_areas": [
      "Specific improvement suggestion"
  ],
  "override_notes": [
      "Explain where reviewer decisions were overridden and why"
  ]
}}

RULES
- final_total_score must be within [0, {script.max_marks}]
- final_factor_scores must respect factor weights.
- Justification must reference evidence from the answer.
""".strip()