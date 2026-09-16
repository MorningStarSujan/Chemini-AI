import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

for model in client.models.list():
    if hasattr(model, "supported_actions"):
        if "generateContent" in model.supported_actions:
            print(model.name)
