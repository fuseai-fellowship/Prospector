import os
import json
import re
from dotenv import load_dotenv

from configs.config import logger, settings
from src.utils.llm_client import LLMClient

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

            Organize the extracted information into clearly defined JSON fields. Include the following sections:

            1. "personal_details": {{
                "name": "<full name>",
                "email": "<email address>",
                "phone": "<phone number>",
                "address": "<address if available>",
                "linkedin": "<LinkedIn profile if available>",
                "github": "<GitHub or portfolio link if available>"
            }}

            2. "projects": [
                {{
                    "title": "<project title>",
                    "description": "<project description>"
                }},
                ...
            ]

            3. "work_experience": [
                {{
                    "company": "<company name>",
                    "position": "<job title>",
                    "duration": "<years/months>",
                    "description": "<responsibilities, tasks, and achievements in this role>"
                }},
                ...
            ]

            4. "certifications": [
                {{
                    "name": "<certification name>",
                    "issuer": "<issuing organization>",
                    "year": "<year>"
                }},
                ...
            ]

            5. "education": [
                {{
                    "degree": "<degree name>",
                    "institution": "<institution name>",
                    "year": "<graduation year>"
                }},
                ...
            ]

            6. "skills": ["<extract all skills mentioned anywhere in the resume>"]

            7. "others": {{
                "additional_info": "<any other relevant information from the resume not covered above, such as awards, hobbies, interests, or volunteer work>"
            }}

            Respond **only** with valid JSON, no explanations, no markdown, no backticks. If any field is missing, return an empty string, empty array, or empty object for that field. Extract all skills mentioned anywhere in the resume. Do not include any explanations or text outside the JSON.
        """

        try:
            logger.info(f"Extracting Structured Resume Data through {self.model} ")

            response = self.llm.invoke(stur_resume_prompt)
            structured_resume = re.sub(r"^```[a-zA-Z]*\n?", "", response)
            structured_resume = re.sub(r"\n?```$", "", structured_resume).strip()
            parsed = json.loads(structured_resume)
            logger.info("Successfully extracted resume data.")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            return {"error": "Some error occured Failed to parse JSON"}
        except Exception as e:
            logger.critical("Structured Resume Data Extraction Failed.")
            return {"error": "Some error occured."}
