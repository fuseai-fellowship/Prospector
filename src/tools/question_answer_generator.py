import json
import os
import re
from dotenv import load_dotenv

from configs.config import logger
from src.utils.llm_client import LLMClient
from ..schemas.interview_questions_schema import InterviewQuestionsSchema

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class QuestionAnswerGenerator:
    def __init__(self, model=None, temperature=None):
        self.llm = LLMClient(
            model=model,
            temperature=temperature,
        )

    def generateInterviewQuestion(self, resume_json: str, job_description: str) -> str:
        logger.info("Generating Interview Questions")
        prompt = f"""
            You are an interviewer preparing 15 short-answer technical questions for a candidate.
            Use ONLY the pasted candidate resume and job description as source.

            INSTRUCTIONS:
            1. Produce exactly 15 questions grouped into three sections:
            - resume_questions (5 questions)
            - jd_questions (5 questions)
            - mixed_questions (5 questions)
            2. Order each section's questions from Easy → Medium → Hard.
            3. Each question must:
            - Be phrased naturally as if spoken by an interviewer.
            - Be answerable within ~1 minute in a concise spoken reply.
            - Be specific, uniquely answerable, and have only one correct answer.
            - Include a short array of exact target_concepts from the resume/job description.
            - Be a single-line string (no newlines inside the question).
            4. **Coverage requirement:** ensure every explicitly named technical concept, tool, skill, or methodology in the pasted resume and job description appears as a target_concept at least once across the 15 questions.
            5. Output: return ONLY a single JSON object that exactly matches the schema below.

            PASTE BELOW:
            Resume JSON: [{resume_json}]
            Job Description: [{job_description}]

            Respond **only** with valid JSON, no explanations, no markdown, no backticks.
            """

        try:
            logger.info("Generating Interview Questions from resume and JD")

            response = self.llm.get_structured_response(
                prompt,
                InterviewQuestionsSchema,
            )
            logger.info("Successfully generated interview questions.")
            print(response.resume_questions)
            return response
        except Exception as e:
            logger.error(f"Error generating interview questions: {e}")
            return None

    def generateFollowupQuestion(self, chat_history):
        logger.info("Generating Followup Questions")

        return None

    def generateAnswer(self, questions):
        logger.info("Generating Answers for Interview Questions")
        return None
