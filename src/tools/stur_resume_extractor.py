import os
from dotenv import load_dotenv

from configs.config import logger, settings
from src.utils.llm_client import LLMClient
from src.schemas.resume_schema import ResumeSchema

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class SturResumeExtractor:
    def __init__(self, model=None, temperature=None):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self.llm = LLMClient(model=model, temperature=temperature)
        self.model = settings.get("normal_model")

    def extract(self, resume_text: str) -> dict:
        stur_resume_prompt = f"""
            Extract structured JSON data from the following resume text:
            {resume_text}

            Respond **only** with valid JSON, no explanations, no markdown, no backticks. If any field is missing, return an empty string, empty array, or empty object for that field. Extract all skills mentioned anywhere in the resume. Do not include any explanations or text outside the JSON.
        """

        try:
            logger.info("Extracting Structured Resume Data ")
            response = self.llm.get_structured_response(
                stur_resume_prompt,
                ResumeSchema,
            )
            logger.info("Successfully extracted resume data.")

            print(response.personal_details)
            return response
        except Exception as e:
            print(e)
            logger.critical("Structured Resume Data Extraction Failed.")
            return {"error": "Some error occured."}
