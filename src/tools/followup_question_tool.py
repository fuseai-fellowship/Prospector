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
        )

    def _run(self, user_answer: QuestionItem, jd: str, session_id: str) -> QuestionItem:
        prompt = f"""
        You are an AI interview assistant generating a follow-up question.
        
        **Context:**
        - Original id: {user_answer.id}
        - Original Question: {user_answer.question}
        - Target Concepts: {", ".join(user_answer.target_concepts)}
        - Candidate's Answer: {user_answer.answer}
        - Job Description: {jd}
        
        The evaluation has determined that a follow-up question is needed.
        
        **Your Task:**
        Generate ONE insightful follow-up question that:
        - Probes deeper into the candidate's understanding
        - Clarifies ambiguous or incomplete parts of their answer
        - Is related to the original question's target concepts
        - Can be answered in ~1 minute
        - Has a clear, specific answer
        - keep track of follow_up_question_no and its List length should be follow_up_count
        
        **Requirements:**
        - Single-line question (no newlines)
        - Professional and conversational tone
        - Include relevant target_concepts
        - Assign appropriate difficulty level
        -- Generate a new unique follow-up ID as follows: if {user_answer.id} is a single digit, append "01" to make a three-digit ID (e.g., 3 → 301); if {user_answer.id} is already three digits, increment it numerically for each follow-up (e.g., 301 → 302 → 303, …).


        Do NOT repeat or rephrase the original question.
        """

        try:
            logger.info(f"Generating Follow-up for Question ID: {user_answer.id}")
            response = self._llm.get_structured_response(
                prompt=prompt,
                session_id=session_id,
                schema=QuestionItem,
                add_to_history=False,
            )
            logger.info("Successfully Generated Follow-up Question")
            return response
        except Exception as e:
            logger.critical(f"Error generating follow-up question: {e}")
            raise
