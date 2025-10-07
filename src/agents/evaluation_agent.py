from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

from ..utils.llm_client import LLMClient
from ..tools.answer_evaluation_tool import AnswerEvaluationTool
from ..tools.followup_question_tool import FollowUpQuestionTool


class EvaluationAgent:
    def __init__(self, chat_history_name: str, model=None, temperature=None):
        self.evaluation_tool = AnswerEvaluationTool(
            model=model, temperature=temperature
        )
        self.followup_question_tool = FollowUpQuestionTool(
            model=model, temperature=temperature
        )
        self.memory = ConversationBufferMemory(
            memory_key=chat_history_name, return_messages=True
        )
        self.tools = [self.evaluation_tool, self.followup_question_tool]

    def run(self, user_answer, jd, chat_history):
        eval_result = self.evaluation_tool._run(user_answer)
        need_followup: bool = eval_result.follow_up_status

        if need_followup:
            followup_questions = self.followup_question_tool._run(
                user_answer, jd, chat_history
            )
            return eval_result, followup_questions
        else:
            return eval_result, False
