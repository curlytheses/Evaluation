import logging
import random
from dataclasses import asdict
from typing import Any, Literal
import openai
from .llm import chat_json
from .models import DebateTurn, ParsedAnswerScript, ReviewerAssessment, SupremeReview
from .prompts import debate_prompt, review_prompt, supreme_prompt
from .rules import all_supporting, clip_scores, select_peer_set

logger = logging.getLogger("rich")

def evaluate_script_with_debate(
    script: ParsedAnswerScript,
    client: openai.OpenAI,
    reviewer_models: list[str],
    supreme_model: str,
    debate_rounds: int = 4,
    pairing_strategy: Literal["all_to_all", "random", "round_robin"] = "all_to_all",
    random_seed: int = 42,
) -> dict[str, Any]:
    if len(reviewer_models) < 2:
        raise ValueError("At least two reviewer models are required for debate.")

    rng = random.Random(random_seed)

    initial_assessments: list[ReviewerAssessment] = []
    for index, model in enumerate(reviewer_models, start=1):
        reviewer_id = f"reviewer_{index}"
        payload = chat_json(
            client=client,
            model=model,
            messages=[{"role": "user", "content": review_prompt(script)}],
        )
        factor_scores = clip_scores(script.factors, payload.get("factor_scores", {}))
        total_score = round(
            min(max(float(payload.get("total_score", sum(factor_scores.values()))), 0.0), script.max_marks),
            2,
        )
        initial_assessments.append(
            ReviewerAssessment(
                reviewer_id=reviewer_id,
                model=model,
                factor_scores=factor_scores,
                total_score=total_score,
                justification=str(payload.get("justification", "")),
            )
        )

    current_assessments = initial_assessments
    debate_transcript: list[DebateTurn] = []
    reviewer_ids = [assessment.reviewer_id for assessment in current_assessments]

    for round_id in range(1, debate_rounds + 1):
        updated_assessments: list[ReviewerAssessment] = []

        for assessment in current_assessments:
            peer_ids = select_peer_set(reviewer_ids, assessment.reviewer_id, pairing_strategy, rng)
            peers = [candidate for candidate in current_assessments if candidate.reviewer_id in peer_ids]
            payload = chat_json(
                client=client,
                model=assessment.model,
                messages=[
                    {
                        "role": "user",
                        "content": debate_prompt(
                            script=script,
                            reviewer_id=assessment.reviewer_id,
                            assessment=assessment,
                            peers=peers,
                            prior_rounds=debate_transcript,
                        ),
                    }
                ],
            )

            stance_by_reviewer = {
                reviewer: ("support" if str(value).lower() == "support" else "contradict")
                for reviewer, value in payload.get("stance_by_reviewer", {}).items()
                if reviewer in peer_ids
            }

            revised_factor_scores = clip_scores(
                script.factors,
                payload.get("revised_factor_scores", assessment.factor_scores),
            )
            revised_total_score = round(
                min(
                    max(float(payload.get("revised_total_score", sum(revised_factor_scores.values()))), 0.0),
                    script.max_marks,
                ),
                2,
            )
            revised_justification = str(payload.get("revised_justification", assessment.justification))

            debate_transcript.append(
                DebateTurn(
                    round_id=round_id,
                    reviewer_id=assessment.reviewer_id,
                    model=assessment.model,
                    stance_by_reviewer=stance_by_reviewer,
                    revised_factor_scores=revised_factor_scores,
                    revised_total_score=revised_total_score,
                    revised_justification=revised_justification,
                )
            )

            updated_assessments.append(
                ReviewerAssessment(
                    reviewer_id=assessment.reviewer_id,
                    model=assessment.model,
                    factor_scores=revised_factor_scores,
                    total_score=revised_total_score,
                    justification=revised_justification,
                )
            )

        current_assessments = updated_assessments
        if all_supporting(debate_transcript, reviewer_ids):
            logger.info(f"Debate converged at round {round_id} for script {script.script_id}")
            break

    supreme_payload = chat_json(
        client=client,
        model=supreme_model,
        messages=[
            {
                "role": "user",
                "content": supreme_prompt(
                    script=script,
                    assessments=current_assessments,
                    debate_transcript=debate_transcript,
                ),
            }
        ],
    )

    supreme_review = SupremeReview(
        model=supreme_model,
        final_factor_scores=clip_scores(script.factors, supreme_payload.get("final_factor_scores", {})),
        final_total_score=round(
            min(max(float(supreme_payload.get("final_total_score", 0.0)), 0.0), script.max_marks),
            2,
        ),
        final_justification=str(supreme_payload.get("final_justification", "")),
        improvement_areas=[str(item) for item in supreme_payload.get("improvement_areas", [])],
        override_notes=[str(item) for item in supreme_payload.get("override_notes", [])],
    )

    return {
        "script_id": script.script_id,
        "question_id": script.question_id,
        "initial_assessments": [asdict(assessment) for assessment in initial_assessments],
        "final_reviewer_assessments": [asdict(assessment) for assessment in current_assessments],
        "debate_transcript": [asdict(turn) for turn in debate_transcript],
        "supreme_review": asdict(supreme_review),
    }

