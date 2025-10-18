import random

from configs.config import logger
from ..utils.llm_client import LLMClient
from ..schemas.interview_questions_schema import InterviewQuestionsSchema


class QuestionGenerator:
    def __init__(self, model=None, temperature=None):
        self.llm = LLMClient(
            model=model,
            temperature=temperature,
            use_resoning_model=True,
        )

    def generateInterviewQn(
        self, resume_json: str, job_description: str, no_of_qn: int = 9
    ) -> InterviewQuestionsSchema:
        per_cat_qn = no_of_qn / 3
        prompt = f"""
            You are an interviewer preparing 15 short-answer technical questions for a candidate.
            Use ONLY the pasted candidate resume and job description as source.

            INSTRUCTIONS:
            1. Produce exactly {no_of_qn} questions grouped into three sections:
            - resume_questions ({per_cat_qn} questions)
            - jd_questions ({per_cat_qn} questions)
            - mixed_questions ({per_cat_qn} questions)
            2. Order each section's questions from Easy → Medium → Hard.
            3. Each question must:  
            - Be phrased naturally as if spoken by an interviewer.
            - Be answerable within ~1 minute in a concise spoken reply.
            - Be specific, uniquely answerable, and have only one correct answer.
            - Include a short array of exact target_concepts from the resume/job description.
            - Be a single-line string (no newlines inside the question).
            4. **Coverage requirement:** ensure every explicitly named technical concept, tool, skill, or methodology in the pasted resume and job description appears as a target_concept at least once across the 9 questions.
            5. Output: return ONLY a single JSON object that exactly matches the schema below.
            6. also generate answer also

            PASTE BELOW:
            Resume JSON: [{resume_json}]
            Job Description: [{job_description}]

            Respond **only** with valid JSON, no explanations, no markdown, no backticks.
            """

        try:
            logger.info(
                "Generating Interview Questions from resume and job description"
            )

            response = self.llm.get_structured_response(
                prompt,
                InterviewQuestionsSchema,
            )
            logger.info("Successfully Generated Interview Questions.")
            print("Resume \n")
            print(response.resume_questions)
            print("JD \n")
            print(response.jd_questions)
            print("Mixed \n")
            print(response.mixed_questions)

            return response
        except Exception as e:
            logger.error(f"Error generating interview questions: {e}")
            return e
