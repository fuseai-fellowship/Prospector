import os
from dotenv import load_dotenv
from configs.config import settings
from pydantic import BaseModel
from typing import Optional, Type, Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage

from .chat_history_manager import ChatHistoryManager

load_dotenv()

# Single Shared instance for all
chat_history_manager = ChatHistoryManager()


def singleton(cls):
    """
    Simple singleton decorator.
    """
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class LLMClient:
    """
    Enhanced LLM Client with integrated history management.
    Handles both regular and structured responses with conversation context.
    """

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

        # Initialize history manager
        self.history_manager = chat_history_manager

    # ==================== Basic Invoke ====================

    def invoke(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        use_history: Optional[bool] = True,
        add_to_history: Optional[bool] = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Basic invoke with optional conversation history.

        Args:
            prompt: The prompt to send to the LLM
            session_id: Session ID for history tracking
            metadata: Optional metadata to attach to messages

        Returns:
            String response from LLM
        """
        if session_id and add_to_history:
            # Build prompt with conversation context
            full_prompt = self.history_manager.build_context_for_llm(
                session_id=session_id, current_prompt=prompt, include_last_n=10
            )
        else:
            full_prompt = prompt

        # Get response from LLM
        response = self.llm.invoke(full_prompt)
        response_content = getattr(response, "content", str(response))

        # Save to history if session_id provided
        if session_id & add_to_history:
            self.history_manager.add_user_message(session_id, prompt, metadata=metadata)
            self.history_manager.add_assistant_message(
                session_id, response_content, metadata=metadata
            )

        return response_content

    # ==================== Structured Output ====================

    def get_structured_response(
        self,
        prompt: str,
        schema: Type[BaseModel],
        session_id: Optional[str] = None,
        use_history: Optional[bool] = True,
        add_to_history: Optional[bool] = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BaseModel:
        """
        Get structured response with conversation history support.

        Args:
            prompt: The prompt to send to the LLM
            schema: Pydantic model schema for structured output
            session_id: Session ID for history tracking
            metadata: Optional metadata to attach to messages

        Returns:
            Pydantic model instance
        """
        structured_llm = self.llm.with_structured_output(schema)

        if session_id and use_history:
            full_prompt = self.history_manager.build_context_for_llm(
                session_id=session_id, current_prompt=prompt, include_last_n=10
            )
        else:
            full_prompt = prompt

        # Get structured response
        response = structured_llm.invoke(full_prompt)

        # Save to history if session_id provided
        if session_id and add_to_history:
            self.history_manager.add_structured_exchange(
                session_id=session_id,
                user_content=prompt,
                assistant_response=response,
                user_metadata=metadata,
                assistant_metadata={
                    **(metadata or {}),
                    "schema": schema.__name__,
                    "structured": True,
                },
            )

        return response

    # ==================== History Management Shortcuts ====================

    def get_history(self, session_id: str, limit: Optional[int] = None) -> list[dict]:
        """
        Get conversation history as list of dicts.
        Format: [{'role': 'user'|'assistant', 'content': '...', 'timestamp': '...'}]
        """
        messages = self.history_manager.get_messages(session_id, limit)
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "metadata": msg.metadata,
            }
            for msg in messages
        ]

    def clear_history(self, session_id: str):
        """Clear history for a specific session"""
        self.history_manager.delete_session(session_id)

    def clear_all_histories(self):
        """Clear all session histories"""
        self.history_manager.clear_all_sessions()

    def print_history(
        self, session_id: str, limit: Optional[int] = None, show_metadata: bool = False
    ):
        """Pretty print conversation history"""
        self.history_manager.print_session(
            session_id, limit=limit, show_metadata=show_metadata
        )

    def get_context_summary(self, session_id: str, max_length: int = 1000) -> str:
        """Get a brief summary of conversation context"""
        return self.history_manager.build_context_string(
            session_id=session_id, max_length=max_length
        )
