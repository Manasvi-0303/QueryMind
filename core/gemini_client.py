import os
import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Gemini API key not found. Check your .env file.")

client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(
        timeout=45000,
        retry_options=types.HttpRetryOptions(
            attempts=1,
            initial_delay=1,
            max_delay=1,
            http_status_codes=[408, 500, 502, 503, 504]
        )
    )
)


def ask_gemini(prompt, max_output_tokens=512):

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=max_output_tokens,
                thinking_config=types.ThinkingConfig(
                    thinking_level="minimal"
                )
            )
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        return response.text.strip()

    except httpx.TimeoutException as e:
        raise RuntimeError(
            "Gemini took too long to respond. Please retry."
        ) from e

    except errors.APIError as e:
        if e.code == 429:
            raise RuntimeError(
                "Gemini API quota exceeded. Please try again later."
            ) from e

        raise RuntimeError(f"Gemini API error: {e}") from e








