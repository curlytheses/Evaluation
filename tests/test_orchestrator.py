from rocketeval.config import ModelConfig, RuntimeConfig
from rocketeval.models import Factor, ParsedAnswerScript
from rocketeval.orchestrator import EvaluationOrchestrator
from rocketeval.providers.mock_provider import MockJsonProvider


def test_orchestrator_end_to_end_with_convergence_and_override():
    script = ParsedAnswerScript(
        script_id="s1",
        question_id="q1",
        question_text="Explain Gauss law.",
        answer_text="The student explains the integral form correctly but misses one implication.",
        max_marks=10,
        factors=[
            Factor(name="accuracy", weight=6, description="Correctness"),
            Factor(name="completeness", weight=4, description="Coverage"),
        ],
    )

    responses = [
        {"factor_scores": {"accuracy": 5, "completeness": 2}, "total_score": 7, "justification": "r1 init"},
        {"factor_scores": {"accuracy": 4, "completeness": 3}, "total_score": 7, "justification": "r2 init"},
        {
            "stance_by_reviewer": {"reviewer_2": "support"},
            "revised_factor_scores": {"accuracy": 5, "completeness": 2},
            "revised_total_score": 7,
            "revised_justification": "r1 round1",
        },
        {
            "stance_by_reviewer": {"reviewer_1": "support"},
            "revised_factor_scores": {"accuracy": 4.5, "completeness": 2.5},
            "revised_total_score": 7,
            "revised_justification": "r2 round1",
        },
        {
            "stance_by_reviewer": {"reviewer_2": "support"},
            "revised_factor_scores": {"accuracy": 5, "completeness": 2},
            "revised_total_score": 7,
            "revised_justification": "r1 round2",
        },
        {
            "stance_by_reviewer": {"reviewer_1": "support"},
            "revised_factor_scores": {"accuracy": 5, "completeness": 2},
            "revised_total_score": 7,
            "revised_justification": "r2 round2",
        },
        {
            "final_factor_scores": {"accuracy": 5.5, "completeness": 2.5},
            "final_total_score": 8,
            "final_justification": "Supreme adjusted based on stronger conceptual precision.",
            "improvement_areas": ["Cover implications of flux-density relation."],
            "override_notes": ["Raised accuracy by 0.5 after consistency check."],
        },
    ]

    orchestrator = EvaluationOrchestrator(
        provider=MockJsonProvider(responses=responses),
        model_config=ModelConfig(reviewer_models=["m1", "m2"], supreme_model="supreme"),
        runtime_config=RuntimeConfig(debate_rounds=5, pairing_strategy="all_to_all", random_seed=1),
    )

    result = orchestrator.evaluate_script(script)
    assert result["supreme_review"]["final_total_score"] == 8.0
    assert len(result["debate_transcript"]) == 4
    assert result["supreme_review"]["override_notes"]
