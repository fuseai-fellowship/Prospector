# src/db/models/job.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from ..base import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_file_name = Column(String, unique=True, nullable=False)  # make unique

    # Back reference to users who applied
    applicants = relationship("User", back_populates="job")

    def __repr__(self):
        return f"<Job(title={self.title}, id={self.id})>"
