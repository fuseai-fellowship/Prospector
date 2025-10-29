from typing import Tuple, Union

from ..schemas.evaluation_schema import EvaluationScores
from ..schemas.interview_questions_schema import QuestionItem
from ..tools.answer_evaluation_tool import AnswerEvaluationTool
from ..tools.followup_question_tool import FollowUpQuestionTool


class EvaluationAgent:
    def __init__(self, model=None, temperature=None):
        self.evaluation_tool = AnswerEvaluationTool(
            model=model, temperature=temperature
        )
        self.followup_question_tool = FollowUpQuestionTool(
            model=model, temperature=temperature
        )
        self.tools = [self.evaluation_tool, self.followup_question_tool]

    def run(
        self, user_answer: QuestionItem, jd: str, session_id: str
    ) -> Tuple[EvaluationScores, Union[QuestionItem, bool]]:
        eval_result = self.evaluation_tool._run(
            user_answer=user_answer, session_id=session_id
        )

        if user_answer.follow_up_count >= 1:
            need_followup = False
            # Manually set the eval_result status to False if max follow-ups reached
            eval_result.follow_up_status = False
        else:
            need_followup: bool = eval_result.follow_up_status

        if need_followup:
            followup_question = self.followup_question_tool._run(
                user_answer, jd, session_id
            )

            # When generating a new follow-up, increment its count
            if followup_question:
                followup_question.follow_up_count = user_answer.follow_up_count + 1

            return eval_result, followup_question
        else:
            return eval_result, False

    def get_overall_assessment(self, evaluation_text) -> str:
        overall_summary = self.evaluation_tool.overall_evaluation(
            evaluation_text=evaluation_text
        )

        return overall_summary
