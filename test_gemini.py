from core.gemini_client import ask_gemini

question = "Explain what SQL is in two simple sentences."

answer = ask_gemini(question)

print("\nGemini Response:")
print(answer)