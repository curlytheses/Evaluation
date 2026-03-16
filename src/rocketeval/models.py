from dataclasses import dataclass
from typing import Literal


@dataclass
class Factor:
    name: str
    weight: float
    description: str


@dataclass
class ParsedAnswerScript:
    script_id: str
    question_id: str
    question_text: str
    answer_text: str
    max_marks: float
    factors: list[Factor]


@dataclass
class ReviewerAssessment:
    reviewer_id: str
    model: str
    factor_scores: dict[str, float]
    total_score: float
    justification: str


@dataclass
class FactorCheck:
    factor_name: str
    model: str
    score: float
    justification: str


@dataclass
class DebateTurn:
    round_id: int
    reviewer_id: str
    model: str
    stance_by_reviewer: dict[str, Literal["support", "contradict"]]
    revised_factor_scores: dict[str, float]
    revised_total_score: float
    revised_justification: str


@dataclass
class SupremeReview:
    model: str
    final_factor_scores: dict[str, float]
    final_total_score: float
    final_justification: str
    improvement_areas: list[str]
    override_notes: list[str]
