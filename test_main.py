from src.utils.llm_client_with_history import LLMClientWithHistory

client = LLMClientWithHistory()
resp = client.invoke_with_history("session_1", "Hello — who are you?")
print("AI:", resp)

resp2 = client.invoke_with_history("session_1", "What did I just ask you?")
print("AI:", resp2)

# Get history
print(client.get_history("session_1"))

# Try invoking via RunnableWithMessageHistory (useful if you want to plug this into other runnables)
resp3 = client.invoke_with_history("session_1", "Summarize our chat in one line.")
resp4 = client.invoke_with_history("session_2", "He my name is Sandesh")
resp5 = client.invoke_with_history("session_2", "Summarize our chat in one line.")
print("AI via runnable:", resp3)
print(client.get_history("session_2"))

print("AI via runnable:", resp5)
