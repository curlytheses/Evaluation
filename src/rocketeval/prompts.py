import json
from dataclasses import asdict
from .models import DebateTurn, FactorCheck, ParsedAnswerScript, ReviewerAssessment

def factor_schema(script: ParsedAnswerScript) -> str:
    return "\n".join([f"- {f.name} (weight={f.weight}): {f.description}" for f in script.factors])

def review_prompt(script: ParsedAnswerScript) -> str:
    return f"""
You are an IIT-level strict exam evaluator.

Question:
{script.question_text}

Student answer:
{script.answer_text}

Max marks: {script.max_marks}

Rubric factors:
{factor_schema(script)}

Return JSON with:
- factor_scores: object mapping each factor to awarded marks (0..factor.weight)
- total_score: number in [0, {script.max_marks}]
- justification: concise but evidence-based justification with direct references to answer content

Rules:
- Never hallucinate missing points.
- Penalize factual errors and missing key steps.
- Keep score internally consistent: sum(factor_scores) ~= total_score (difference <= 0.25).
""".strip()

def factor_review_prompt(script: ParsedAnswerScript, factor_name: str, factor_weight: float, factor_description: str) -> str:
    return f"""
You are a dedicated specialist evaluator for ONLY ONE factor in an IIT-level exam review.

Question:
{script.question_text}

Student answer:
{script.answer_text}

Evaluate only this factor:
- {factor_name} (weight={factor_weight}): {factor_description}

Return JSON with:
- score: numeric in [0, {factor_weight}]
- justification: one concise evidence-based justification focused only on {factor_name}
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
You are reviewer {reviewer_id} in a multi-reviewer debate for IIT-level exam grading.

Question:
{script.question_text}

Student answer:
{script.answer_text}

Rubric factors:
{factor_schema(script)}

Your current assessment JSON:
{json.dumps(asdict(assessment), indent=2)}

Peer assessments JSON:
{json.dumps(peer_blob, indent=2)}

Your prior debate turns JSON:
{json.dumps(round_blob, indent=2)}

Now debate rigorously:
1) For each peer reviewer, choose stance: support or contradict.
2) If contradicting, explain concrete rubric/evidence disagreement in justification.
3) You may revise your factor scores and total score if convinced.

Return JSON with keys:
- stance_by_reviewer: object mapping peer reviewer_id -> "support" | "contradict"
- revised_factor_scores: object mapping factor name -> numeric marks
- revised_total_score: numeric
- revised_justification: string
""".strip()

def supreme_prompt(
    script: ParsedAnswerScript,
    assessments: list[ReviewerAssessment],
    debate_transcript: list[DebateTurn],
    factor_checks: list[FactorCheck],
) -> str:
    return f"""
You are the supreme reviewer for IIT-level evaluation quality assurance.
You may override any prior score or justification.

Question:
{script.question_text}

Student answer:
{script.answer_text}

Max marks: {script.max_marks}
Rubric factors:
{factor_schema(script)}

Final reviewer assessments JSON:
{json.dumps([asdict(a) for a in assessments], indent=2)}

Debate transcript JSON:
{json.dumps([asdict(t) for t in debate_transcript], indent=2)}

Dedicated factor-specialist checks JSON:
{json.dumps([asdict(fc) for fc in factor_checks], indent=2)}

Return JSON with keys:
- final_factor_scores: object mapping each factor to marks
- final_total_score: numeric in [0, {script.max_marks}]
- final_justification: string
- improvement_areas: list of concrete improvement bullets for student
- override_notes: list describing where and why you changed reviewer decisions
""".strip()
