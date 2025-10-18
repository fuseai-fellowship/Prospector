from langchain.tools import BaseTool
from pydantic import PrivateAttr

from configs.config import logger
from ..schemas.evaluation_schema import AnswerEvaluation
from ..utils.llm_client import LLMClient


class AnswerEvaluationTool(BaseTool):
    name: str = "AnswerEvaluator"
    description: str = "A LangChain tool that assesses interview answers by scoring relevance, clarity, depth, accuracy, and completeness, and provides a concise overall assessment of the candidate’s understanding."
    _llm: LLMClient = PrivateAttr()

    def __init__(self, model=None, temperature=None):
        super().__init__()
        self._llm = LLMClient(
            model=model,
            temperature=temperature,
        )

    def _run(self, user_answer, session_id) -> AnswerEvaluation:
        prompt = f"""
                    Evaluate Understanding: Check if the candidate’s answer demonstrates a clear understanding of the question and sufficiently addresses the target concepts.
                    Score the Answer across the following categories (each rated 1–5, where 1 = very poor and 5 = excellent):

                    Relevance: Does the answer stay focused on the question and cover the target concepts?
                    Clarity: Is the answer easy to understand, logically structured, and free from ambiguity?
                    Depth: Does the answer provide sufficient detail and insight, showing real understanding beyond surface-level statements?
                    Accuracy: Are the facts, concepts, or technical points explained correctly?
                    Completeness: Does the answer cover all important aspects of the question without leaving major gaps?

                    Provide a short overall assessment (1 sentences).
                    Alse decide whether this requires followup question or not. Also If the users doesn't know the answer then keep it false and give the score 0 for everything.
                    Here is user_answer[{user_answer}]
                """
        try:
            logger.info("Evaluating User Answer")
            response = self._llm.get_structured_response(
                prompt=prompt,
                schema=AnswerEvaluation,
                session_id=session_id,
            )
            logger.info("Successfully Evaluated User Answer")
            return response
        except Exception as e:
            logger.critical(f"Error Evaluating User Answer {e}")
            print(e)

    async def _arun(self, user_answer):
        """Asynchronous execution using LLM"""
        return self._run(user_answer)
