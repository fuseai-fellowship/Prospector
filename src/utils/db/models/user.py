# src/db/models/user.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=False, nullable=False)
    phone_no = Column(String, unique=True, nullable=False)
    resume_file_name = Column(String, unique=True, nullable=True)
    processed_resume_file_path = Column(String, unique=False, nullable=True)
    interview_result_file_name = Column(String, unique=False, nullable=True)
    interview_score = Column(String, unique=False, nullable=True)

    # Link to the job
    job_name = Column(String, ForeignKey("jobs.job_file_name"), nullable=False)
    job = relationship("Job", back_populates="applicants")

    def __repr__(self):
        return f"<User(name={self.name}, id={self.id}, job_id={self.job_id})>"
