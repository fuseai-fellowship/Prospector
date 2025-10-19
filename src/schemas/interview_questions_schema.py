from pydantic import BaseModel
from typing import List, Literal, Optional


class QuestionItem(BaseModel):
    id: int
    question: str
    target_concepts: List[str]
    difficulty: Literal["Easy", "Medium", "Hard"]
    answer: Optional[str] = None
    follow_up_question_no: List[int] = []
    follow_up_count: int = 0


class InterviewQuestionsSchema(BaseModel):
    resume_questions: List[QuestionItem]
    jd_questions: List[QuestionItem]
    mixed_questions: List[QuestionItem]
