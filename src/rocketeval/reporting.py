from dataclasses import asdict
from .models import ParsedAnswerScript, SupremeReview

def summarize_result(script: ParsedAnswerScript, supreme_review: SupremeReview) -> dict:
    return {
        "script_id": script.script_id,
        "question_id": script.question_id,
        "final_total_score": supreme_review.final_total_score,
        "max_marks": script.max_marks,
        "final_factor_scores": supreme_review.final_factor_scores,
        "final_justification": supreme_review.final_justification,
        "improvement_areas": supreme_review.improvement_areas,
        "override_notes": supreme_review.override_notes,
        "supreme_model": supreme_review.model,
        "supreme_review": asdict(supreme_review),
    }
