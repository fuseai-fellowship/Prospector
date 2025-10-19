from src.utils.chat_history_manager import ChatHistoryManager

if __name__ == "__main__":
    mgr = ChatHistoryManager()
    mgr.create_session("session")
    mgr.add_structured_exchange("session", "hello", "hi there")
    # Use the pretty print helper:
    mgr.print_session("session")
