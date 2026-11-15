
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Gemini API key not found. Check your .env file.")

client = genai.Client(api_key=API_KEY)


def ask_gemini(prompt):
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )

    return response.text
