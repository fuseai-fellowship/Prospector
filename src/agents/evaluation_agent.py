from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

from ..utils.llm_client import LLMClient
from ..tools.answer_evaluation_tool import AnswerEvaluationTool
from ..tools.followup_question_tool import FollowUpQuestionTool


class EvaluationAgent:
    def __init__(self, model=None, temperature=None):
        self.llm = LLMClient()

        self.evaluation_tool = AnswerEvaluationTool()
        self.followup_question_tool = FollowUpQuestionTool()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        self.tools = [self.evaluation_tool, self.followup_question_tool]

        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            memory=self.memory,
            verbose=True,
        )
