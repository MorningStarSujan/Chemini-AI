from utils.gemini_service import ask_gemini

question = input("Ask a chemistry question: ")

answer = ask_gemini(question)

print("\n")
print(answer)
