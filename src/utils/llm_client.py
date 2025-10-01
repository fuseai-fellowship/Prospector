from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv
from configs.config import settings
import os

load_dotenv()


class LLMClient:
    def __init__(
        self,
        model=None,
        temperature=None,
        use_history=False,
    ):
        if model is None:
            self.model = settings.get("normal_model")
        else:
            self.model = model

        if temperature is None:
            self.temperature = settings.get("temperature")
        else:
            self.model = temperature

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self.llm = ChatGoogleGenerativeAI(
            model=self.model,
            temperature=self.temperature,
            api_key=api_key,
        )
        self.use_history = use_history
        self.history = [] if use_history else None

    def invoke(self, prompt: str) -> str:
        """Send a prompt to the LLM. Optionally maintain chat history."""
        if self.use_history:
            self.history.append(HumanMessage(content=prompt))
            response = self.llm.invoke(self.history)
            self.history.append(response)
            print(self.history)
        else:
            response = self.llm.invoke(prompt)

        return response.content if hasattr(response, "content") else str(response)

    def _reset_history(self):
        """Clear conversation history if enabled."""
        if self.use_history:
            self.history = []
