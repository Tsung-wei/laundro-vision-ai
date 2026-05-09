from laundro_vision_ai.models.schemas import AssessmentRequest, CompetitorEvalRequest
from laundro_vision_ai.services.scoring import calculate_total_score, evaluate_competitor


def test_evaluate_competitor_knockout():
    req = CompetitorEvalRequest(
        q2_residential=4, q3_visibility=4, q4_signage=4, q5_motorcycle=4, q7_machine_status=4, q8_cleanliness=4
    )
    res = evaluate_competitor(req)
    assert res.competitor_score == 4.0
    assert res.knock_out is True
    assert "過於強大" in res.message


def test_evaluate_competitor_pass():
    req = CompetitorEvalRequest(
        q2_residential=2, q3_visibility=2, q4_signage=2, q5_motorcycle=2, q7_machine_status=2, q8_cleanliness=2
    )
    res = evaluate_competitor(req)
    assert res.competitor_score == 2.0
    assert res.knock_out is False


def test_calculate_total_score_no_competitor():
    req = AssessmentRequest(
        has_competitor=False, q1_cvs=5, q2_residential=5, q3_visibility=5, q4_signage=5, q5_motorcycle=5
    )
    res = calculate_total_score(req)
    assert res.total_score == 5.0
    assert res.category_scores.audience == 3.0
    assert res.category_scores.hardware == 2.0
    assert res.category_scores.operations is None


def test_calculate_total_score_with_competitor():
    req = AssessmentRequest(
        has_competitor=True,
        q1_cvs=5,
        q2_residential=5,
        q3_visibility=5,
        q4_signage=5,
        q5_motorcycle=5,
        q7_machine_status=5,
        q8_cleanliness=5,
    )
    res = calculate_total_score(req)
    assert res.total_score == 5.0
    assert res.category_scores.operations == 1.0
