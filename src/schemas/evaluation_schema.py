from pydantic import BaseModel, Field
from typing import List, Optional


class EvaluationScores(BaseModel):
    relevance: int = Field(..., ge=1, le=5)
    clarity: int = Field(..., ge=1, le=5)
    depth: int = Field(..., ge=1, le=5)
    accuracy: int = Field(..., ge=1, le=5)
    completeness: int = Field(..., ge=1, le=5)


class AnswerEvaluation(BaseModel):
    question_id: int
    overall_assessment: str
    scores: EvaluationScores
    follow_up_status: bool
    # follow_up_question: Optional[str] = None
