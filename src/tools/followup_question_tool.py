import random
from langchain.tools import BaseTool

from configs.config import logger
from ..utils.llm_client import LLMClient
from ..schemas.interview_questions_schema import QuestionItem


class FollowUpQuestionTool(BaseTool):
    name: str = "FollowupQuestionTool"
    description: str = "Generates context-aware follow-up questions to assess a candidate’s understanding and clarify incomplete interview answers."

    def __init__(self, model=None, temperature=None):
        self.session_id: str

        self._llm = LLMClient(
            model=model,
            temperature=temperature,
            use_reasoning_model=True,
        )

    def _run(
        self, resume_json: str, job_description: str, session_id: str
    ) -> QuestionItem:
        prompt = """
                You are an AI interview assistant that generates a single, high-quality follow-up question
                based on the interview context provided. The evaluation has already determined that a follow-up question is needed.
                Your task is only to generate one insightful and context-aware follow-up question based on the previous question and answer that the we have provided

                Guidelines:
                - Use the Chat History guide your generation.
                - Generate the question in the given schema or format
                - **Do not repeat or rephrase previous questions.**
                - Focus on clarifying or deepening the candidate’s latest answer.
                - Be phrased naturally as if spoken by an interviewer.
                - Be answerable within about 1 minute in a concise spoken reply.
                - Be specific, uniquely answerable, and have only one correct answer.
                - Include a short array of exact **target_concepts** derived from the resume or job description.
                - The question must be a **single-line string** (no newlines).
                - Maintain a **professional and conversational** tone.
                - Generate only one follow-up question.
                """

        try:
            logger.info("Generating Follow-up Questions")

            response = self._llm.get_structured_response(
                prompt=prompt,
                session_id=session_id,
                schema=QuestionItem,
            )
            logger.info("Successfully Generated Followup Questions.")
            print(self._llm.get_history(session_id=session_id))
            return response

        except Exception as e:
            logger.critical(f"Error in Follow-up questions: {e}")
            return e
