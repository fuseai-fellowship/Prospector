import os
from dotenv import load_dotenv

from configs.config import logger, settings
from ..utils.llm_client import LLMClient
from ..schemas.resume_schema import ResumeSchema

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class SturResumeExtractor:
    def __init__(self, model=None, temperature=None):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self.llm = LLMClient(model=model, temperature=temperature)
        self.model = settings.get("normal_model")

    def extract(self, resume_text: str) -> ResumeSchema:
        stur_resume_prompt = f"""
            Extract structured JSON data from the following resume text:
            {resume_text}

            Respond only with valid JSON.
            Do not include any explanations, markdown, or backticks.
            For any missing field, use an empty string (""), empty array ([]), or empty object ({{}}) as appropriate.
            Extract all skills mentioned anywhere in the resume.
            Keep all the extra info in the others section
            Ensure the JSON strictly matches the schema structure.
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
