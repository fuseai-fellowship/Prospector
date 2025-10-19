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

    def run(self, user_answer, jd, session_id):
        eval_result = self.evaluation_tool._run(
            user_answer=user_answer, session_id=session_id
        )
        print(eval_result)
        need_followup: bool = eval_result.follow_up_status

        if need_followup:
            followup_questions = self.followup_question_tool._run(
                user_answer, jd, session_id
            )
            return eval_result, followup_questions
        else:
            return eval_result, False
