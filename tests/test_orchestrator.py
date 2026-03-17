from src.rocketeval.config import ModelConfig, RuntimeConfig
from src.rocketeval.models import Factor, ParsedAnswerScript
from src.rocketeval.orchestrator import EvaluationOrchestrator
from src.rocketeval.providers.mock_provider import MockJsonProvider
from src.rocketeval.providers.router import MultiProviderRouter

def test_orchestrator_with_multi_llm_factor_specialists_and_supreme():
    script = ParsedAnswerScript(
        script_id="s1",
        question_id="q1",
        question_text="Explain Gauss law.",
        answer_text="The student explains integral form correctly but misses one implication.",
        max_marks=10,
        factors=[
            Factor(name="concept_accuracy", weight=6, description="Correctness"),
            Factor(name="derivation", weight=2, description="Logical derivation"),
            Factor(name="clarity", weight=2, description="Clarity"),
        ],
    )

    gemini = MockJsonProvider(
        responses_by_model={
            "gemini-1.5-pro": [
                {
                    "factor_scores": {"concept_accuracy": 5, "derivation": 1.5, "clarity": 1},
                    "total_score": 7.5,
                    "justification": "g init",
                },
                {
                    "stance_by_reviewer": {"reviewer_2": "support"},
                    "revised_factor_scores": {"concept_accuracy": 5, "derivation": 1.5, "clarity": 1},
                    "revised_total_score": 7.5,
                    "revised_justification": "g d1",
                },
                {
                    "stance_by_reviewer": {"reviewer_2": "support"},
                    "revised_factor_scores": {"concept_accuracy": 5.2, "derivation": 1.6, "clarity": 1.1},
                    "revised_total_score": 7.9,
                    "revised_justification": "g d2",
                },
                {"score": 5.3, "justification": "concept strong"},
            ]
        }
    )
    anthropic = MockJsonProvider(
        responses_by_model={
            "claude-3-5-sonnet": [
                {
                    "factor_scores": {"concept_accuracy": 4.8, "derivation": 1.4, "clarity": 1.2},
                    "total_score": 7.4,
                    "justification": "a init",
                },
                {
                    "stance_by_reviewer": {"reviewer_1": "support"},
                    "revised_factor_scores": {"concept_accuracy": 5, "derivation": 1.5, "clarity": 1.1},
                    "revised_total_score": 7.6,
                    "revised_justification": "a d1",
                },
                {
                    "stance_by_reviewer": {"reviewer_1": "support"},
                    "revised_factor_scores": {"concept_accuracy": 5.1, "derivation": 1.6, "clarity": 1.1},
                    "revised_total_score": 7.8,
                    "revised_justification": "a d2",
                },
                {"score": 1.6, "justification": "derivation mostly correct"},
            ]
        }
    )
    openai = MockJsonProvider(
        responses_by_model={
            "qwen-max": [{"score": 1.2, "justification": "clarity okay but terse"}],
            "gpt-4o": [
                {
                    "final_factor_scores": {"concept_accuracy": 5.4, "derivation": 1.6, "clarity": 1.3},
                    "final_total_score": 8.3,
                    "final_justification": "Integrated debate and specialist checks.",
                    "improvement_areas": ["Add missing implication from divergence form."],
                    "override_notes": ["Raised concept score based on specialist confidence."],
                }
            ],
        }
    )

    orchestrator = EvaluationOrchestrator(
        provider=MultiProviderRouter(
            providers={"gemini": gemini, "anthropic": anthropic, "openai": openai},
            default_provider="openai",
        ),
        model_config=ModelConfig(
            reviewer_models=["gemini:gemini-1.5-pro", "anthropic:claude-3-5-sonnet"],
            supreme_model="openai:gpt-4o",
            factor_specialists={
                "concept_accuracy": "gemini:gemini-1.5-pro",
                "derivation": "anthropic:claude-3-5-sonnet",
                "clarity": "openai:qwen-max",
            },
        ),
        runtime_config=RuntimeConfig(debate_rounds=6, pairing_strategy="all_to_all", random_seed=1),
    )

    result = orchestrator.evaluate_script(script)
    assert len(result["factor_checks"]) == 3
    assert result["supreme_review"]["final_total_score"] == 8.3
    assert len(result["debate_transcript"]) == 4
    assert result["supreme_review"]["override_notes"]


def test_orchestrator_skips_unknown_factor_specialists():
    script = ParsedAnswerScript(
        script_id="s2",
        question_id="q2",
        question_text="Q",
        answer_text="A",
        max_marks=5,
        factors=[Factor(name="concept_accuracy", weight=5, description="d")],
    )

    provider = MockJsonProvider(
        responses=[
            {
                "factor_scores": {"concept_accuracy": 4},
                "total_score": 4,
                "justification": "r1",
            },
            {
                "factor_scores": {"concept_accuracy": 4},
                "total_score": 4,
                "justification": "r2",
            },
            {
                "stance_by_reviewer": {"reviewer_2": "support"},
                "revised_factor_scores": {"concept_accuracy": 4},
                "revised_total_score": 4,
                "revised_justification": "d1",
            },
            {
                "stance_by_reviewer": {"reviewer_1": "support"},
                "revised_factor_scores": {"concept_accuracy": 4},
                "revised_total_score": 4,
                "revised_justification": "d1",
            },
            {
                "stance_by_reviewer": {"reviewer_2": "support"},
                "revised_factor_scores": {"concept_accuracy": 4},
                "revised_total_score": 4,
                "revised_justification": "d2",
            },
            {
                "stance_by_reviewer": {"reviewer_1": "support"},
                "revised_factor_scores": {"concept_accuracy": 4},
                "revised_total_score": 4,
                "revised_justification": "d2",
            },
            {
                "final_factor_scores": {"concept_accuracy": 4},
                "final_total_score": 4,
                "final_justification": "ok",
                "improvement_areas": [],
                "override_notes": [],
            },
        ]
    )

    orchestrator = EvaluationOrchestrator(
        provider=MultiProviderRouter(providers={"openai": provider}),
        model_config=ModelConfig(
            reviewer_models=["openai:m1", "openai:m2"],
            supreme_model="openai:m3",
            factor_specialists={"unknown_factor": "openai:m4"},
        ),
        runtime_config=RuntimeConfig(debate_rounds=2),
    )

    result = orchestrator.evaluate_script(script)
    assert result["factor_checks"] == []


def test_orchestrator_retries_invalid_initial_review_output():
    script = ParsedAnswerScript(
        script_id="s3",
        question_id="q3",
        question_text="Q",
        answer_text="A",
        max_marks=5,
        factors=[Factor(name="concept_accuracy", weight=5, description="d")],
    )

    provider = MockJsonProvider(
        responses_by_model={
            "m1": [
                {
                    "factor_scores": {"concept_accuracy": 10},
                    "total_score": 10,
                    "justification": "invalid",
                },
                {
                    "factor_scores": {"concept_accuracy": 4},
                    "total_score": 4,
                    "justification": "valid",
                },
                {
                    "stance_by_reviewer": {"reviewer_2": "support"},
                    "revised_factor_scores": {"concept_accuracy": 4},
                    "revised_total_score": 4,
                    "revised_justification": "d1",
                },
            ],
            "m3": [
                {
                    "factor_scores": {"concept_accuracy": 4},
                    "total_score": 4,
                    "justification": "valid r2",
                },
                {
                    "stance_by_reviewer": {"reviewer_1": "support"},
                    "revised_factor_scores": {"concept_accuracy": 4},
                    "revised_total_score": 4,
                    "revised_justification": "d1",
                },
            ],
            "m2": [
                {
                    "final_factor_scores": {"concept_accuracy": 4},
                    "final_total_score": 4,
                    "final_justification": "ok",
                    "improvement_areas": [],
                    "override_notes": [],
                }
            ],
        }
    )

    orchestrator = EvaluationOrchestrator(
        provider=MultiProviderRouter(providers={"openai": provider}),
        model_config=ModelConfig(
            reviewer_models=["openai:m1", "openai:m3"],
            supreme_model="openai:m2",
            factor_specialists={},
        ),
        runtime_config=RuntimeConfig(debate_rounds=1),
    )

    result = orchestrator.evaluate_script(script)
    assert result["initial_assessments"][0]["total_score"] == 4
    assert result["initial_assessments"][0]["justification"] == "valid"


def test_orchestrator_retries_initial_review_after_provider_exception():
    script = ParsedAnswerScript(
        script_id="s4",
        question_id="q4",
        question_text="Q",
        answer_text="A",
        max_marks=5,
        factors=[Factor(name="concept_accuracy", weight=5, description="d")],
    )

    provider = MockJsonProvider(
        responses_by_model={
            "m1": [
                ValueError("Model returned invalid JSON"),
                {
                    "factor_scores": {"concept_accuracy": 3.5},
                    "total_score": 3.5,
                    "justification": "valid after exception",
                },
                {
                    "stance_by_reviewer": {"reviewer_2": "support"},
                    "revised_factor_scores": {"concept_accuracy": 3.5},
                    "revised_total_score": 3.5,
                    "revised_justification": "d1",
                },
            ],
            "m3": [
                {
                    "factor_scores": {"concept_accuracy": 3.5},
                    "total_score": 3.5,
                    "justification": "peer",
                },
                {
                    "stance_by_reviewer": {"reviewer_1": "support"},
                    "revised_factor_scores": {"concept_accuracy": 3.5},
                    "revised_total_score": 3.5,
                    "revised_justification": "d1",
                },
            ],
            "m2": [
                {
                    "final_factor_scores": {"concept_accuracy": 3.5},
                    "final_total_score": 3.5,
                    "final_justification": "ok",
                    "improvement_areas": [],
                    "override_notes": [],
                }
            ],
        }
    )

    orchestrator = EvaluationOrchestrator(
        provider=MultiProviderRouter(providers={"openai": provider}),
        model_config=ModelConfig(
            reviewer_models=["openai:m1", "openai:m3"],
            supreme_model="openai:m2",
            factor_specialists={},
        ),
        runtime_config=RuntimeConfig(debate_rounds=1),
    )

    result = orchestrator.evaluate_script(script)
    assert result["initial_assessments"][0]["total_score"] == 3.5
    assert result["initial_assessments"][0]["justification"] == "valid after exception"
