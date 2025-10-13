import os
from dotenv import load_dotenv
from configs.config import settings
from pydantic import BaseModel
from typing import Dict, List, Optional, Type

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory


load_dotenv()


class LLMClient:
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.3,
        use_reasoning_model: bool = False,
    ):
        self.model = (
            settings.get("reasoning_model")
            if use_reasoning_model
            else model or settings.get("normal_model")
        )
        self.temperature = temperature or settings.get("temperature", 0.3)

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        # Initialize base LLM
        self.llm = ChatGoogleGenerativeAI(
            model=self.model,
            temperature=self.temperature,
            api_key=api_key,
        )

        # Store chat sessions in memory
        self._sessions: Dict[str, InMemoryChatMessageHistory] = {}

        def get_session_history(session_id: Optional[str]):
            sid = session_id or "__ephemeral__"
            if sid not in self._sessions:
                self._sessions[sid] = InMemoryChatMessageHistory()
            return self._sessions[sid]

        # Create runnable that automatically saves chat history
        self.runnable = RunnableWithMessageHistory(
            runnable=self.llm,
            get_session_history=get_session_history,
        )

        self._get_session_history = get_session_history

    # ----------------- Basic invoke -----------------
    def invoke(self, prompt: str, session_id: Optional[str] = None) -> str:
        if not session_id:
            response = self.llm.invoke(prompt)
        else:
            config = {"configurable": {"session_id": session_id}}
            response = self.runnable.invoke(prompt, config=config)
        return getattr(response, "content", str(response))

    # ----------------- Structured output -----------------
    def get_structured_response(
        self, prompt: str, schema: Type[BaseModel], session_id: Optional[str] = None
    ) -> BaseModel:
        structured_llm = self.llm.with_structured_output(schema)
        if session_id:
            config = {"configurable": {"session_id": session_id}}
            structured_runnable = RunnableWithMessageHistory(
                runnable=structured_llm,
                get_session_history=self._get_session_history,
            )
            return structured_runnable.invoke(prompt, config=config)
        return structured_llm.invoke(prompt)

    # ----------------- History Management -----------------
    def get_history(self, session_id: str) -> List[dict]:
        if session_id not in self._sessions:
            return []
        history = self._sessions[session_id].messages
        return [
            {
                "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                "content": msg.content,
            }
            for msg in history
        ]

    def clear_history(self, session_id: str):
        self._sessions.pop(session_id, None)

    def clear_all_histories(self):
        self._sessions.clear()

    # ----------------- Export / Import -----------------
    def export_history(self, session_id: str) -> Dict[str, List[dict]]:
        return {session_id: self.get_history(session_id)}

    def import_history(self, session_id: str, items: List[dict]):
        history = InMemoryChatMessageHistory()
        for item in items:
            role = item.get("role")
            content = item.get("content", "")
            if role == "user":
                history.add_message(HumanMessage(content=content))
            else:
                history.add_message(AIMessage(content=content))
        self._sessions[session_id] = history
