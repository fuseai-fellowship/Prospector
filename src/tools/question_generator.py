from langchain_google_genai import ChatGoogleGenerativeAI
import json
from configs.config import logger
from dotenv import load_dotenv
import os


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class QuestionGenerator:
    def __init__(self, model="gemini-2.5-flash", temperature=0.0):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self.llm = ChatGoogleGenerativeAI(
            model=model, temperature=temperature, api_key=GOOGLE_API_KEY
        )
        self.model = model

    def generateInterviewQuestion(self, resume_json: str, job_description: str):
        logger.info(f"Extracting Structured Resume Data through {self.model} ")

        response = self.llm.invoke(prompt)
