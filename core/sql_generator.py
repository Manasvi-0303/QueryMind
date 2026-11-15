
from core.gemini_client import ask_gemini


def generate_sql(question, schema):

    prompt = f"""
You are an expert SQLite SQL query generator.

Your task is to convert the user's question into a valid SQLite query.

DATABASE SCHEMA:
{schema}

USER QUESTION:
{question}

RULES:
1. Generate only valid SQLite SQL.
2. Use only tables and columns present in the schema.
3. Generate only SELECT queries.
4. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
5. Do not include explanations or markdown formatting.
6. Return only the SQL query.

SQL QUERY:
"""

    response = ask_gemini(prompt)

    return response.strip().replace("```sql", "").replace("```", "").strip()
