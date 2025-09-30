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
        temperature=0.0,
        use_history=False,
    ):
        if model is None:
            model = settings.get("normal_model")

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            api_key=api_key,
        )
        self.use_history = use_history
        self.history = [] if use_history else None

    def ask(self, prompt: str) -> str:
        """Send a prompt to the LLM. Optionally maintain chat history."""
        if self.use_history:
            self.history.append(HumanMessage(content=prompt))
            response = self.llm.invoke(self.history)
            self.history.append(response)
        else:
            response = self.llm.invoke(prompt)

        return response.content

    def _reset_history(self):
        """Clear conversation history if enabled."""
        if self.use_history:
            self.history = []


if __name__ == "__main__":
    # Initialize the client
    client = LLMClient(model=settings.normal_model, temperature=0.7, use_history=True)

    print("Welcome to LLMClient. Type 'exit' to quit or 'reset' to clear history.")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Exiting...")
            break
        elif user_input.lower() == "reset":
            client._reset_history()
            print("History cleared.")
            continue

        # Get LLM response
        response = client.ask(user_input)
        print(f"LLM: {response}")
