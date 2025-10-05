from pydantic import BaseModel
from typing import List, Literal


class QuestionItem(BaseModel):
    id: int
    question: str
    target_concepts: List[str]
    difficulty: Literal["Easy", "Medium", "Hard"]


class InterviewQuestionsSchema(BaseModel):
    resume_questions: List[QuestionItem]
    jd_questions: List[QuestionItem]
    mixed_questions: List[QuestionItem]
