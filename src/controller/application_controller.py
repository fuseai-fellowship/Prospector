import json
import time
from pathlib import Path
from typing import Tuple, Union

from ..agents.jd_resume_processor_agent import ResumeProcessorAgent
from ..agents.evaluation_agent import EvaluationAgent

from ..schemas.resume_schema import ResumeSchema
from ..schemas.interview_questions_schema import InterviewQuestionsSchema, QuestionItem
from ..schemas.evaluation_schema import EvaluationScores

from ..utils.db import db, create_user
from ..utils.file_savings import save_processed_json_resume


session = db.get_session()


class ApplicationController:
    def __init__(self):
        self.resume_processor = ResumeProcessorAgent()
        self.evaluation_agent = EvaluationAgent()
        self.session = db.get_session()

        pass

    def process_applicant_info(self, resume_file_path) -> ResumeSchema:
        # result = self.resume_processor.run_extraction_pipline(
        #     resume_file=resume_file_path
        # )
        # Save result as JSON
        # Example usage
        result = self.load_resume_as_schema(
            "data/applications/processed_resumes/_SandeshShrestha_CV (1).json"
        )

        return result

    def load_resume_as_schema(self, json_file_path: str) -> ResumeSchema:
        """
        Load a saved resume JSON and convert it back to ResumeSchema (Pydantic model).
        """
        json_path = Path(json_file_path)
        if not json_path.exists():
            raise FileNotFoundError(f"No file found at {json_file_path}")

        # Read JSON
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Convert dictionary to ResumeSchema
        resume_schema = ResumeSchema(**data)
        return resume_schema

    def save_applicaticant_info(self, applicant_info, resume_file_name, jd_name):
        file_path = save_processed_json_resume(
            json_text=applicant_info, file_name=resume_file_name
        )
        applicant_personal_info = applicant_info.personal_details
        create_user(
            session=self.session,
            name=applicant_personal_info.name,
            email=applicant_personal_info.email,
            phone_no=applicant_personal_info.phone,
            resume_file_name=resume_file_name,
            processed_resume_file_path=file_path,
            job_name=jd_name,
        )

    def check_qualification(self):
        time.sleep(3)
        return True

    def prepeare_interview_questions(
        self, resume_json: str, jd_json: str
    ) -> InterviewQuestionsSchema:
        interview_question = self.resume_processor.generate_questions(
            resume_json=resume_json, jd_json=jd_json
        )
        return interview_question

    def evaluate_answer(
        self, user_answer, jd, session_id
    ) -> Tuple[EvaluationScores, Union[QuestionItem, bool]]:
        eval_reslt, followup = self.evaluation_agent.run(
            user_answer=user_answer, jd=jd, session_id=session_id
        )

        return eval_reslt, followup
