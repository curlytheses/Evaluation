from __future__ import annotations
import logging
import random
from dataclasses import asdict
from typing import Any
from .config import ModelConfig, RuntimeConfig
from .debate import all_supporting_last_two_rounds, select_peer_set
from .models import DebateTurn, Factor, FactorCheck, ParsedAnswerScript, ReviewerAssessment, SupremeReview
from .prompts import debate_prompt, factor_review_prompt, review_prompt, supreme_prompt
from .providers.router import MultiProviderRouter
from .validators import clip_factor_scores, normalize_total_score, safe_float

logger = logging.getLogger("rich")


class EvaluationOrchestrator:
    def __init__(self, provider: MultiProviderRouter, model_config: ModelConfig, runtime_config: RuntimeConfig):
        self.provider = provider
        self.model_config = model_config
        self.runtime_config = runtime_config
        self.model_config.validate()
        self.runtime_config.validate()

    def evaluate_script(self, script: ParsedAnswerScript) -> dict[str, Any]:
        initial_assessments = self._initial_reviews(script)
        final_reviewer_assessments, debate_transcript = self._debate(script, initial_assessments)
        factor_checks = self._factor_specialist_reviews(script)
        supreme_review = self._supreme_review(script, final_reviewer_assessments, debate_transcript, factor_checks)
        return {
            "script_id": script.script_id,
            "question_id": script.question_id,
            "initial_assessments": [asdict(assessment) for assessment in initial_assessments],
            "final_reviewer_assessments": [asdict(assessment) for assessment in final_reviewer_assessments],
            "debate_transcript": [asdict(turn) for turn in debate_transcript],
            "factor_checks": [asdict(fc) for fc in factor_checks],
            "supreme_review": asdict(supreme_review),
        }

    def _initial_reviews(self, script: ParsedAnswerScript) -> list[ReviewerAssessment]:
        assessments: list[ReviewerAssessment] = []
        for index, model in enumerate(self.model_config.reviewer_models, start=1):
            reviewer_id = f"reviewer_{index}"
            payload = self.provider.complete_json(agent_model=model, prompt=review_prompt(script))
            factor_scores = clip_factor_scores(script.factors, payload.get("factor_scores", {}))
            assessments.append(
                ReviewerAssessment(
                    reviewer_id=reviewer_id,
                    model=model,
                    factor_scores=factor_scores,
                    total_score=self._normalize_assessment_total(script.max_marks, payload.get("total_score"), factor_scores),
                    justification=str(payload.get("justification", "")).strip(),
                )
            )
        return assessments

    def _factor_specialist_reviews(self, script: ParsedAnswerScript) -> list[FactorCheck]:
        checks: list[FactorCheck] = []
        factors_by_name = {factor.name: factor for factor in script.factors}

        for factor_name, agent_model in self.model_config.factor_specialists.items():
            factor = factors_by_name.get(factor_name)
            if factor is None:
                logger.warning(
                    "Skipping factor specialist mapping for unknown factor '%s' on script %s",
                    factor_name,
                    script.script_id,
                )
                continue

            payload = self.provider.complete_json(
                agent_model=agent_model,
                prompt=factor_review_prompt(
                    script,
                    factor_name=factor.name,
                    factor_weight=factor.weight,
                    factor_description=factor.description,
                ),
            )
            checks.append(self._build_factor_check(factor, agent_model, payload))
        return checks

    def _debate(
        self,
        script: ParsedAnswerScript,
        initial_assessments: list[ReviewerAssessment],
    ) -> tuple[list[ReviewerAssessment], list[DebateTurn]]:
        current_assessments = initial_assessments
        debate_transcript: list[DebateTurn] = []
        reviewer_ids = [assessment.reviewer_id for assessment in current_assessments]
        rng = random.Random(self.runtime_config.random_seed)

        for round_id in range(1, self.runtime_config.debate_rounds + 1):
            updated_assessments: list[ReviewerAssessment] = []
            for assessment in current_assessments:
                updated_assessment, debate_turn = self._single_debate_turn(
                    script=script,
                    assessment=assessment,
                    current_assessments=current_assessments,
                    reviewer_ids=reviewer_ids,
                    round_id=round_id,
                    rng=rng,
                    prior_rounds=debate_transcript,
                )
                updated_assessments.append(updated_assessment)
                debate_transcript.append(debate_turn)

            current_assessments = updated_assessments
            if all_supporting_last_two_rounds(debate_transcript, reviewer_ids):
                logger.info("Debate converged at round %s for script %s", round_id, script.script_id)
                break

        return current_assessments, debate_transcript

    def _single_debate_turn(
        self,
        script: ParsedAnswerScript,
        assessment: ReviewerAssessment,
        current_assessments: list[ReviewerAssessment],
        reviewer_ids: list[str],
        round_id: int,
        rng: random.Random,
        prior_rounds: list[DebateTurn],
    ) -> tuple[ReviewerAssessment, DebateTurn]:
        peer_ids = select_peer_set(reviewer_ids, assessment.reviewer_id, self.runtime_config.pairing_strategy, rng)
        peers = [candidate for candidate in current_assessments if candidate.reviewer_id in peer_ids]

        payload = self.provider.complete_json(
            agent_model=assessment.model,
            prompt=debate_prompt(
                script=script,
                reviewer_id=assessment.reviewer_id,
                assessment=assessment,
                peers=peers,
                prior_rounds=prior_rounds,
            ),
        )

        stance_by_reviewer = {
            reviewer: ("support" if str(value).lower() == "support" else "contradict")
            for reviewer, value in payload.get("stance_by_reviewer", {}).items()
            if reviewer in peer_ids
        }

        revised_factor_scores = clip_factor_scores(
            script.factors,
            payload.get("revised_factor_scores", assessment.factor_scores),
        )
        revised_total_score = self._normalize_assessment_total(
            script.max_marks,
            payload.get("revised_total_score"),
            revised_factor_scores,
        )
        revised_justification = str(payload.get("revised_justification", assessment.justification)).strip()

        debate_turn = DebateTurn(
            round_id=round_id,
            reviewer_id=assessment.reviewer_id,
            model=assessment.model,
            stance_by_reviewer=stance_by_reviewer,
            revised_factor_scores=revised_factor_scores,
            revised_total_score=revised_total_score,
            revised_justification=revised_justification,
        )
        updated_assessment = ReviewerAssessment(
            reviewer_id=assessment.reviewer_id,
            model=assessment.model,
            factor_scores=revised_factor_scores,
            total_score=revised_total_score,
            justification=revised_justification,
        )
        return updated_assessment, debate_turn

    def _supreme_review(
        self,
        script: ParsedAnswerScript,
        assessments: list[ReviewerAssessment],
        debate_transcript: list[DebateTurn],
        factor_checks: list[FactorCheck],
    ) -> SupremeReview:
        payload = self.provider.complete_json(
            agent_model=self.model_config.supreme_model,
            prompt=supreme_prompt(
                script=script,
                assessments=assessments,
                debate_transcript=debate_transcript,
                factor_checks=factor_checks,
            ),
        )
        return SupremeReview(
            model=self.model_config.supreme_model,
            final_factor_scores=clip_factor_scores(script.factors, payload.get("final_factor_scores", {})),
            final_total_score=normalize_total_score(script.max_marks, payload.get("final_total_score"), 0.0),
            final_justification=str(payload.get("final_justification", "")).strip(),
            improvement_areas=[str(item).strip() for item in payload.get("improvement_areas", [])],
            override_notes=[str(item).strip() for item in payload.get("override_notes", [])],
        )

    def _normalize_assessment_total(self, max_marks: float, total_score: Any, factor_scores: dict[str, float]) -> float:
        return normalize_total_score(max_marks, total_score, sum(factor_scores.values()))

    def _build_factor_check(self, factor: Factor, agent_model: str, payload: dict[str, Any]) -> FactorCheck:
        raw_score = safe_float(payload.get("score", 0.0), default=0.0)
        score = round(min(max(raw_score, 0.0), float(factor.weight)), 2)
        return FactorCheck(
            factor_name=factor.name,
            model=agent_model,
            score=score,
            justification=str(payload.get("justification", "")).strip(),
        )
