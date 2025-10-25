from pydantic import BaseModel, Field
from typing import List


class JobDescription(BaseModel):
    title: str = Field(..., description="A concise and professional job title.")
    requirements: List[str] = Field(
        ..., description="List of required skills, experience, and competencies."
    )
    responsibilities: List[str] = Field(
        ..., description="List of main roles and daily tasks."
    )
    qualifications: List[str] = Field(
        ...,
        description="Educational and professional qualifications required for the job.",
    )
