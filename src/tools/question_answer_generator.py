import json
import os
import re
from dotenv import load_dotenv

from configs.config import logger
from src.utils.llm_client import LLMClient

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
                Use ONLY the pasted candidate resume and the pasted job description (insert both where indicated) as the source for topic selection.

                INSTRUCTIONS (follow exactly):
                1. Produce exactly 15 questions grouped into three sections (5 each):
                - past_skills_experience (5 questions)
                - role_responsibilities_technical_needs (5 questions)
                - mixed_background_and_role (5 questions)

                2. Order each section's questions from Easy → Medium → Hard.

                3. Each question must:
                - Be phrased naturally as if spoken by an interviewer (examples: “Can you explain…”, “Walk me through…”, “How would you…?”).
                - Be answerable within ~1 minute in a concise spoken reply.
                - Be specific and have only one correct answer (no ambiguity).
                - Not be multiple-choice.
                - Directly test concepts, skills, tools, or experiences explicitly named in the pasted text.
                - Include a short array of exact target concept keywords from the pasted text.
                - Be a single-line string (no newlines inside the question).

                4. Coverage requirement: ensure that every explicitly named technical concept, tool, skill, or methodology in the pasted resume and job description appears as a target_concept at least once across the 15 questions.

                5. Output: return ONLY a single JSON object that exactly matches the schema below. Do not include any commentary, explanation, or additional fields.

                RESPONSE JSON SCHEMA (produce JSON that conforms exactly):
                {{
                "resume_questions": [
                    {{ "id": 1, "question": "<one-line interviewer-style question>", "target_concepts": ["concept1","concept2"], "difficulty": "Easy" }},
                    {{ "id": 2, "question": "...", "target_concepts": ["..."], "difficulty": "Easy|Medium|Hard" }}
                ],
                "jd_questions": [
                    {{ "id": 1, "question": "...", "target_concepts": ["..."], "difficulty": "Easy" }}
                ],
                "mixed_questions": [
                    {{ "id": 1, "question": "...", "target_concepts": ["..."], "difficulty": "Easy" }}
                ]
                }}

                ADDITIONAL FORMATTING RULES:
                - Each section must have exactly 5 items (ids start at 1 and increment within each section).
                - The "difficulty" value must be exactly one of: "Easy", "Medium", or "Hard".
                - target_concepts must use the same exact words/phrasing that appear in the pasted resume/job description when possible.
                - Do not include example answers, commentary, or any extra keys.
                - Ensure each question is uniquely answerable and time-limited (~1 minute).

                PASTE BELOW:
                This is resume :- [{resume_json}]
                This is the job description :- [{job_description}]

                Respond **only** with valid JSON, no explanations, no markdown, no backticks
                """
        try:
            response = self.llm.invoke(prompt)
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", response)
            cleaned = re.sub(r"\n?```$", "", cleaned).strip()
            parsed = json.loads(cleaned)
            logger.info("Successfully generated interview questions.")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.debug(f"Raw response: {cleaned}")
            return None
        except Exception as e:
            logger.error(f"Error generating interview questions: {e}")
            return None

    def generateFollowupQuestion(self, chat_history):
        logger.info("Generating Followup Questions")

        return None

    def generateAnswer(self, questions):
        logger.info("Generating Answers for Interview Questions")
        return None
