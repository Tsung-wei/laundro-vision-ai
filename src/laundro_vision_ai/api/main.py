import uvicorn
from fastapi import FastAPI

from laundro_vision_ai.models.schemas import (
    AssessmentRequest,
    AssessmentResponse,
    CompetitorEvalRequest,
    CompetitorEvalResponse,
)
from laundro_vision_ai.services.scoring import calculate_total_score, evaluate_competitor

app = FastAPI(title="LaundroVision AI MVP API")


@app.post("/api/v1/assessments/evaluate-competitor", response_model=CompetitorEvalResponse)
def evaluate_competitor_route(req: CompetitorEvalRequest):
    """Endpoint to evaluate competitor strength and determine knock‑out."""
    return evaluate_competitor(req)


@app.post("/api/v1/assessments/calculate-score", response_model=AssessmentResponse)
def calculate_score_route(req: AssessmentRequest):
    """Endpoint to calculate the total site score based on the questionnaire."""
    return calculate_total_score(req)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
