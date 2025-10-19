from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pydantic import BaseModel


class Message(BaseModel):
    """Represents a single message in conversation history"""

    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class ConversationSession(BaseModel):
    """Represents a complete conversation session"""

    session_id: str
    messages: List[Message] = []
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


class ChatHistoryManager:
    """
    Comprehensive chat history manager for interview sessions.
    Handles message storage, context building, and history retrieval.
    """

    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}

    # ==================== Session Management ====================

    def create_session(
        self, session_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationSession:
        """Create a new conversation session"""
        if session_id in self.sessions:
            return self.sessions[session_id]

        session = ConversationSession(
            session_id=session_id,
            created_at=datetime.now().isoformat(),
            metadata=metadata or {},
        )
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get a session by ID"""
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a specific session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def clear_all_sessions(self):
        """Clear all sessions"""
        self.sessions.clear()

    def list_sessions(self) -> List[str]:
        """List all session IDs"""
        return list(self.sessions.keys())

    # ==================== Message Management ====================

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a message to a session.
        Creates session if it doesn't exist.
        """
        if role.lower() not in ["user", "assistant"]:
            raise ValueError("Role must be 'user' or 'assistant'")

        # Create session if it doesn't exist
        if session_id not in self.sessions:
            self.create_session(session_id)

        message = Message(
            role=role.lower(),
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
        )

        self.sessions[session_id].messages.append(message)
        return True

    def add_user_message(
        self, session_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ):
        """Convenience method to add user message"""
        return self.add_message(session_id, "user", content, metadata)

    def add_assistant_message(
        self, session_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ):
        """Convenience method to add assistant message"""
        return self.add_message(session_id, "assistant", content, metadata)

    def add_structured_exchange(
        self,
        session_id: str,
        user_content: str,
        assistant_response: Any,
        user_metadata: Optional[Dict[str, Any]] = None,
        assistant_metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Add a complete question-answer exchange.
        Handles Pydantic models by converting to string.
        """

        # Add user message
        self.add_user_message(session_id, user_content, user_metadata)

        # Convert response to string if it's a Pydantic model
        if isinstance(assistant_response, BaseModel):
            response_str = assistant_response.model_dump_json(indent=2)
        else:
            response_str = str(assistant_response)

        # Add assistant message
        self.add_assistant_message(session_id, response_str, assistant_metadata)

    # ==================== History Retrieval ====================

    def get_messages(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get messages from a session.
        If limit is provided, returns last N messages.
        """
        session = self.get_session(session_id)
        if not session:
            return []

        messages = session.messages
        if limit:
            return messages[-limit:]
        return messages

    def get_message_count(self, session_id: str) -> int:
        """Get total number of messages in a session"""
        session = self.get_session(session_id)
        return len(session.messages) if session else 0

    def get_last_message(self, session_id: str) -> Optional[Message]:
        """Get the last message from a session"""
        messages = self.get_messages(session_id)
        return messages[-1] if messages else None

    # ==================== Context Building ====================

    def build_context_string(
        self,
        session_id: str,
        limit: Optional[int] = None,
        include_metadata: bool = False,
        max_length: int = 2000,
    ) -> str:
        """
        Build a formatted context string from conversation history.
        Useful for including in prompts.
        """
        messages = self.get_messages(session_id, limit)

        if not messages:
            return ""

        context_parts = ["=== Previous Conversation ===\n"]
        total_length = 0

        for msg in messages:
            role_label = "User" if msg.role == "user" else "Assistant"

            # Truncate individual messages if needed
            content = msg.content
            if len(content) > 500:
                content = content[:497] + "..."

            msg_str = f"\n[{role_label}]:\n{content}\n"

            if include_metadata and msg.metadata:
                msg_str += f"Metadata: {json.dumps(msg.metadata, indent=2)}\n"

            # Check total length
            if total_length + len(msg_str) > max_length:
                context_parts.append("\n... (earlier messages truncated) ...\n")
                break

            context_parts.append(msg_str)
            total_length += len(msg_str)

        context_parts.append("\n=== End of Previous Conversation ===\n")
        return "".join(context_parts)

    def build_context_for_llm(
        self, session_id: str, current_prompt: str, include_last_n: int = 10
    ) -> str:
        """
        Build a complete prompt with conversation context.
        Optimized for LLM consumption.
        """
        context = self.build_context_string(
            session_id, limit=include_last_n, max_length=3000
        )

        if context:
            return f"{context}\n\n=== Current Request ===\n{current_prompt}"
        else:
            return current_prompt

    # ==================== Export / Import ====================

    def export_session(self, session_id: str) -> Optional[Dict]:
        """Export a session to a dictionary"""
        session = self.get_session(session_id)
        if not session:
            return None

        return session.model_dump()

    def export_all_sessions(self) -> Dict[str, Dict]:
        """Export all sessions"""
        return {
            session_id: session.model_dump()
            for session_id, session in self.sessions.items()
        }

    def import_session(self, session_data: Dict) -> bool:
        """Import a session from dictionary"""
        try:
            session = ConversationSession(**session_data)
            self.sessions[session.session_id] = session
            return True
        except Exception as e:
            print(f"Error importing session: {e}")
            return False

    def save_to_file(self, filepath: str):
        """Save all sessions to a JSON file"""
        data = self.export_all_sessions()
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filepath: str):
        """Load sessions from a JSON file"""
        with open(filepath, "r") as f:
            data = json.load(f)

        for session_data in data.values():
            self.import_session(session_data)

    # ==================== Display Methods ====================

    def print_session(
        self, session_id: str, limit: Optional[int] = None, show_metadata: bool = False
    ):
        """Pretty print a session's conversation"""
        messages = self.get_messages(session_id, limit)

        if not messages:
            print(f"\n📭 No messages in session '{session_id}'")
            return

        print(f"\n{'=' * 70}")
        print(f"SESSION: {session_id}")
        print(f"Messages: {len(messages)}")
        print(f"{'=' * 70}\n")

        for i, msg in enumerate(messages, 1):
            role_icon = "👤" if msg.role == "user" else "🤖"
            role_label = msg.role.upper()

            print(f"{role_icon} [{i}] {role_label} ({msg.timestamp})")
            print("-" * 70)

            # Display content
            content = msg.content
            if len(content) > 500:
                content = content[:497] + "..."
            print(content)

            if show_metadata and msg.metadata:
                print(f"\n📎 Metadata: {json.dumps(msg.metadata, indent=2)}")

            print("=" * 70 + "\n")

    def print_all_sessions_summary(self):
        """Print summary of all sessions"""
        if not self.sessions:
            print("\n📭 No active sessions")
            return

        print(f"\n{'=' * 70}")
        print(f"ALL SESSIONS SUMMARY ({len(self.sessions)} sessions)")
        print(f"{'=' * 70}\n")

        for session_id in self.sessions:
            stats = self.get_session_stats(session_id)
            print(f"📝 {session_id}")
            print(
                f"   Messages: {stats['total_messages']} "
                f"(👤 {stats['user_messages']} | 🤖 {stats['assistant_messages']})"
            )
            print(f"   Created: {stats['created_at']}")
            if stats.get("metadata"):
                print(f"   Metadata: {stats['metadata']}")
            print()
