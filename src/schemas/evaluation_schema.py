from pydantic import BaseModel, Field
from typing import List, Optional


class EvaluationScores(BaseModel):
    relevance: int = Field(..., ge=0, le=10)
    clarity: int = Field(..., ge=0, le=10)
    depth: int = Field(..., ge=0, le=10)
    accuracy: int = Field(..., ge=0, le=10)
    completeness: int = Field(..., ge=0, le=10)


class AnswerEvaluation(BaseModel):
    question_id: int
    overall_assessment: str
    scores: EvaluationScores
    follow_up_status: bool
