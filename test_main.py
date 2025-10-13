from src.utils.llm_client import LLMClient

# Initialize client
client = LLMClient()

# Session 1 interactions
resp1 = client.invoke("Hello — who are you?", session_id="session_1")
print("AI:", resp1)

resp2 = client.invoke("What did I just ask you?", session_id="session_1")
print("AI:", resp2)

resp3 = client.invoke("Summarize our chat in one line.", session_id="session_1")
print("AI:", resp3)

# View chat history for session_1
print("History (session_1):", client.get_history("session_1"))

# Session 2 interactions
resp4 = client.invoke("Hey, my name is Sandesh", session_id="session_2")
print("AI:", resp4)

resp5 = client.invoke("Summarize our chat in one line.", session_id="session_2")
print("AI:", resp5)

# View chat history for session_2
print("History (session_2):", client.get_history("session_2"))

# Optional — separate test with generic example
sid = "example-session"
resp6 = client.invoke("Hello!", session_id=sid)
print("Response:", resp6)
print("History:", client.get_history(sid))
