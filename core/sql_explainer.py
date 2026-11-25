
import json

from core.gemini_client import ask_gemini


def explain_sql(question, sql):

    prompt = f"""
You are QueryMind, an expert SQL educator.

Your task is to explain an existing SQLite query in simple,
beginner-friendly language.

ORIGINAL USER QUESTION:
{question}

GENERATED SQL:
{sql}

INSTRUCTIONS:

1. Explain the overall purpose of the SQL query.
2. Break down every important SQL clause actually present.
3. Explain aggregate functions and SQL functions actually used.
4. Explain joins and relationships if present.
5. Explain the logical execution flow of the query.
6. Explain how this query answers the original question.
7. Do not invent tables, columns, relationships or database facts.
8. Do not modify, rewrite or generate another SQL query.
9. Do not explain clauses or functions that are not present.
10. Keep explanations clear and concise.

Return ONLY valid JSON in this exact structure:

{{
    "overview": "Short explanation of what the query does.",
    "clauses": [
        {{
            "name": "SELECT",
            "explanation": "What this clause does in this query."
        }}
    ],
    "functions": [
        {{
            "name": "AVG",
            "explanation": "What this function calculates."
        }}
    ],
    "execution_flow": [
        "First logical step.",
        "Second logical step."
    ],
    "how_it_answers": "Explain how the query answers the user's question."
}}

Rules:
- Include only clauses and functions that actually appear.
- If no SQL functions are used, return an empty functions array.
- Use plain English.
- Return valid JSON only.
"""

    try:

        response = ask_gemini(
            prompt,
            max_output_tokens=1400
        )

        explanation = json.loads(response)

        required_keys = [
            "overview",
            "clauses",
            "functions",
            "execution_flow",
            "how_it_answers"
        ]

        for key in required_keys:

            if key not in explanation:
                raise ValueError(
                    f"Missing explanation field: {key}"
                )

        if not isinstance(explanation["clauses"], list):
            raise ValueError("Invalid SQL clauses format.")

        if not isinstance(explanation["functions"], list):
            raise ValueError("Invalid SQL functions format.")

        if not isinstance(explanation["execution_flow"], list):
            raise ValueError("Invalid execution flow format.")

        return explanation

    except json.JSONDecodeError as error:

        raise ValueError(
            "Could not process the SQL explanation. Please try again."
        ) from error
