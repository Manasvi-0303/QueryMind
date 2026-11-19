
import json
import re
from functools import lru_cache

from core.gemini_client import ask_gemini


@lru_cache(maxsize=128)
def generate_sql(question, schema):

    prompt = f"""
You are QueryMind. Convert the user's question into SQLite SQL.

DATABASE SCHEMA:
{schema}

USER QUESTION:
{question}

RULES:
- Use only tables and columns in the schema.
- Generate only valid SQLite SELECT queries.
- Never generate write operations or modify the database.
- If the question has multiple reasonable meanings, ask one
  short clarification question.
- Do not ask for clarification if the question is clear.
- Never invent table or column names.

Return ONLY valid JSON.

For clarification:
{{
    "status": "clarification",
    "clarification_question": "Your question",
    "sql": ""
}}

For a clear question:
{{
    "status": "ready",
    "clarification_question": "",
    "sql": "SELECT ...;"
}}
"""

    response = ask_gemini(prompt)

    response = re.sub(
        r"```(?:json)?",
        "",
        response
    ).replace("```", "").strip()

    try:
        result = json.loads(response)

    except json.JSONDecodeError:
        raise ValueError(
            "Gemini returned an invalid response. Please try again."
        )

    if not isinstance(result, dict):
        raise ValueError("Gemini returned an unexpected response.")

    if result.get("status") not in ["ready", "clarification"]:
        raise ValueError("Unexpected response from Gemini.")

    if result["status"] == "clarification":

        if not result.get("clarification_question", "").strip():
            raise ValueError("Gemini returned an empty clarification.")

        return result

    sql = result.get("sql", "")

    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("Gemini did not generate a SQL query.")

    return result



