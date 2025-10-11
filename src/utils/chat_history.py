class ChatHistoryManager:
    def __init__(self):
        self.sessions = {}

    def create_session(self, session_id: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []  # list of messages
        return self.sessions[session_id]

    def get_all_session_memory(self, session_id: str):
        return self.sessions.get(session_id, [])

    def add_message(self, session_id: str, role: str, message: str):
        """
        Add a message to the specified session.
        role = 'user' or 'ai'
        """
        memory = self.create_session(session_id)  # auto-create if missing
        role_lower = role.lower()
        if role_lower not in ("user", "ai"):
            raise ValueError("Role must be 'user' or 'ai'")

        memory.append({"role": role_lower, "message": message})
        return True

    def get_chat_history(self, session_id: str):
        """Return list of (role, message) tuples."""
        memory = self.get_all_session_memory(session_id)
        return [(msg["role"], msg["message"]) for msg in memory]

    def delete_session(self, session_id: str):
        """Delete a specific session by its ID"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return "No Such History"

    def clear_all_sessions(self):
        """Completely clear all stored sessions"""
        self.sessions.clear()
