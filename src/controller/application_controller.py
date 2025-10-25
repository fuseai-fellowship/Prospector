from ..agents.jd_resume_processor_agent import ResumeProcessorAgent
from ..schemas.resume_schema import ResumeSchema
from pathlib import Path
import json


class ApplicationController:
    def __init__(self):
        self.resume_processor = ResumeProcessorAgent()
        pass

    def process_applicant_info(self, resume_file_path) -> ResumeSchema:
        # result = self.resume_processor.run_extraction_pipline(
        #     resume_file=resume_file_path
        # )
        # # Save result as JSON
        # self.save_result_as_json(result, resume_file_path)
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
