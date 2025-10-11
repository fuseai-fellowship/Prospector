# llm_client_with_history.py
from typing import Dict, List, Union, Optional, Callable, Type
import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from pydantic import BaseModel

from configs.config import settings

load_dotenv()


class LLMClientWithHistory:
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        use_reasoning_model: bool = False,
    ):
        model = (
            settings.get("resoning_model")
            if use_reasoning_model
            else (model or settings.get("normal_model"))
        )
        temperature = temperature or settings.get("temperature")

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self.llm = ChatGoogleGenerativeAI(
            model=model, temperature=temperature, api_key=api_key
        )

        self._sessions: Dict[str, InMemoryChatMessageHistory] = {}

        def _get_session_history(session_id: Optional[str]):
            sid = session_id or "__ephemeral__"
            if sid not in self._sessions:
                self._sessions[sid] = InMemoryChatMessageHistory()
            return self._sessions[sid]

        self.runnable = RunnableWithMessageHistory(
            runnable=self.llm,
            get_session_history=_get_session_history,
        )

        self._get_session_history: Callable[
            [Optional[str]], InMemoryChatMessageHistory
        ] = _get_session_history

    def invoke_with_history(
        self, session_id: str, user_input: str, config: Optional[dict] = None
    ) -> str:
        config = config or {}
        config.setdefault("configurable", {})["session_id"] = session_id

        try:
            out = self.runnable.invoke(user_input, config=config)
            return getattr(out, "content", str(out))
        except Exception as e:
            print(e)

    def get_structured_response_with_history(
        self, session_id: str, prompt: str, schema: Type[BaseModel]
    ) -> BaseModel:
        if session_id not in self._sessions:
            self._sessions[session_id] = InMemoryChatMessageHistory()

        history = self._sessions[session_id]
        messages: List[Union[HumanMessage, AIMessage]] = history.messages + [
            HumanMessage(content=prompt)
        ]

        structured_llm = self.llm.with_structured_output(schema)
        resp = structured_llm.invoke(messages)
        return resp

    def get_history(self, session_id: str) -> List[dict]:
        """Return history as list of {'role': 'user'|'assistant', 'content': str}"""
        if session_id not in self._sessions:
            return []
        return [
            {
                "role": "user" if isinstance(m, HumanMessage) else "assistant",
                "content": m.content,
            }
            for m in self._sessions[session_id].messages
        ]

    def clear_history(self, session_id: str):
        """Clear a specific session's history."""
        self._sessions.pop(session_id, None)

    def clear_all_histories(self):
        """Clear all sessions."""
        self._sessions.clear()

    def export_history_as_json(self, session_id: str) -> Dict[str, List[dict]]:
        """
        Return a JSON-serializable structure for a given session_id:
          {"session_id": [{"role": "...", "content": "..."}, ...]}
        """
        return {session_id: self.get_history(session_id)}

    def import_history_from_json(self, session_id: str, items: List[dict]):
        """Load a list of {'role','content'} into the session history (overwrites existing)."""
        from langchain.schema import HumanMessage, AIMessage

        hist = InMemoryChatMessageHistory()
        for it in items:
            role = it.get("role")
            content = it.get("content", "")
            if role == "user":
                hist.add_message(HumanMessage(content=content))
            else:
                hist.add_message(AIMessage(content=content))
        self._sessions[session_id] = hist
