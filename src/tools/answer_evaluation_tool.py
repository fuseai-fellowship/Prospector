from langchain.tools import BaseTool
from pydantic import PrivateAttr

from configs.config import logger
from ..schemas.evaluation_schema import AnswerEvaluation
from ..utils.llm_client import LLMClient


class AnswerEvaluationTool(BaseTool):
    name: str = "AnswerEvaluator"
    description: str = (
        "Evaluates interview answers with scoring and follow-up recommendations"
    )
    _llm: LLMClient = PrivateAttr()

    def __init__(self, model=None, temperature=None):
        super().__init__()
        self._llm = LLMClient(
            model=model, temperature=temperature, use_reasoning_model=True
        )

    def _run(self, user_answer, session_id: str) -> AnswerEvaluation:
        """
        Evaluate a user's answer to an interview question.

        Args:
            user_answer: QuestionItem with the question and candidate's answer
            session_id: Session ID for history tracking

        Returns:
            AnswerEvaluation with scores and follow-up recommendation
        """
        prompt = f"""
                You are an expert interviewer tasked with evaluating a candidate's answer.

                **Question Details:**
                - Question ID: {user_answer.id}
                - Question: {user_answer.question}
                - Target Concepts: {", ".join(user_answer.target_concepts)}
                - Difficulty Level: {user_answer.difficulty}

                **Candidate's Answer:**
                {user_answer.answer}

                **Evaluation Criteria (0-10 for each):**
                1. Relevance: Does the answer address the question and target concepts?
                2. Clarity: Is the answer structured and easy to understand?
                3. Depth: Does it demonstrate deep understanding beyond surface-level knowledge?
                4. Accuracy: Are the technical facts and concepts correct?
                5. Completeness: Does it cover all important aspects?

                **Scoring Guidelines:**
                - "Don't know" or similar → all scores = 0, follow_up_status = false
                - Partial understanding or incomplete → moderate scores, follow_up_status = true
                - Vague or error-prone → lower scores, follow_up_status = true
                - Complete and accurate → high scores, follow_up_status = false
                - High-level understanding or key terms are sufficient; exact code is not required.

                **Overall Assessment:**
                Provide a concise, one-sentence summary of the candidate's answer.

                **Follow-up Decision:**
                Set follow_up_status = true only if:
                - Answer shows partial understanding or needs clarification
                - Answer is incomplete but demonstrates basic knowledge
                - Candidate made errors that need correction

                Set follow_up_status = false if:
                - Candidate has no idea ("don't know")
                - Answer is complete and accurate

                Keep the evaluation focused and concise; assume candidates may not include every detail.
                """

        try:
            logger.info(f"Evaluating answer for Question ID: {user_answer.id}")

            # Get structured response with conversation history
            response = self._llm.get_structured_response(
                prompt=prompt,
                schema=AnswerEvaluation,
                session_id=session_id,
                metadata={
                    "question_id": user_answer.id,
                    "action": "evaluation",
                    "difficulty": user_answer.difficulty,
                },
            )

            logger.info(
                f"✅ Evaluation complete - Follow-up needed: {response.follow_up_status}"
            )
            return response

        except Exception as e:
            logger.critical(f"❌ Error evaluating answer: {e}")
            raise

    async def _arun(self, user_answer, session_id: str):
        """Asynchronous execution"""
        return self._run(user_answer, session_id)

    def overall_evaluation(self, evaluation_text):
        prompt = f"You are a interviewer and given the context, write one brief sentence that summarizes the overall performance.. Return only that sentence, nothing else. {evaluation_text}"

        return self._llm.invoke(prompt=prompt, add_to_history=False)
