from laundro_vision_ai.models.schemas import (
    AssessmentRequest,
    AssessmentResponse,
    CategoryScores,
    CompetitorEvalRequest,
    CompetitorEvalResponse,
)


def evaluate_competitor(req: CompetitorEvalRequest) -> CompetitorEvalResponse:
    """Calculate average score and determine knock-out.
    Knock-out if average > 3.0.
    """
    total = (
        req.q2_residential
        + req.q3_visibility
        + req.q4_signage
        + req.q5_motorcycle
        + req.q7_machine_status
        + req.q8_cleanliness
    )
    avg_score = round(total / 6.0, 2)
    knock_out = avg_score > 3.0
    message = "對手過於強大，建議放棄此店址" if knock_out else "對手威脅可控，請繼續評估候選店址"
    return CompetitorEvalResponse(
        competitor_score=avg_score,
        knock_out=knock_out,
        message=message,
    )


def calculate_total_score(req: AssessmentRequest) -> AssessmentResponse:
    """Calculate total score based on dynamic weights.
    Weights differ depending on presence of competitor.
    """
    if req.has_competitor:
        if req.q7_machine_status is None or req.q8_cleanliness is None:
            raise ValueError("q7 and q8 are required when competitor exists")
        audience = req.q1_cvs * 0.30 + req.q2_residential * 0.20
        hardware = req.q3_visibility * 0.10 + req.q4_signage * 0.10 + req.q5_motorcycle * 0.10
        operations = req.q7_machine_status * 0.10 + req.q8_cleanliness * 0.10
        total = audience + hardware + operations
    else:
        audience = req.q1_cvs * 0.35 + req.q2_residential * 0.25
        hardware = req.q3_visibility * 0.15 + req.q4_signage * 0.15 + req.q5_motorcycle * 0.10
        operations = None
        total = audience + hardware
    return AssessmentResponse(
        total_score=round(total, 2),
        category_scores=CategoryScores(
            audience=round(audience, 2),
            hardware=round(hardware, 2),
            operations=round(operations, 2) if operations is not None else None,
        ),
    )
