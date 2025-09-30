from langchain_google_genai import ChatGoogleGenerativeAI
import json
from configs.config import logger
from dotenv import load_dotenv
import os

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class SturResumeExtractor:
    def __init__(self, model="gemini-2.5-flash", temperature=0.0):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self.llm = ChatGoogleGenerativeAI(
            model=model, temperature=temperature, api_key=GOOGLE_API_KEY
        )
        self.model = model

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

        logger.info(f"Extracting Structured Resume Data through {self.model} ")
        response = self.llm.invoke(stur_resume_prompt)
        structured_resume = response.content
        logger.info("Extraction of Strucutred Resume Successful")
        try:
            return json.loads(structured_resume)
        except:
            logger.critical("Structured Resume Data Extraction Failed.")
            return {"error": "Some error occured Failed to parse JSON"}
