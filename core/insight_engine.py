import json
import math

import pandas as pd

from core.gemini_client import ask_gemini


SENSITIVE_COLUMN_HINTS = (
    "name",
    "email",
    "phone",
    "mobile",
    "address",
    "password",
    "token",
    "ssn",
    "social_security",
    "account",
    "customer_id",
    "student_id",
    "user_id",
    "employee_id",
)


def _is_sensitive_or_identifier(column_name):
    name = str(column_name).lower().replace(" ", "_")
    return any(hint in name for hint in SENSITIVE_COLUMN_HINTS)


def _clean_number(value):
    if pd.isna(value):
        return None

    number = float(value)

    if not math.isfinite(number):
        return None

    return round(number, 3)


def _build_data_summary(data):
    if data.empty:
        raise ValueError("There are no query results to analyse.")

    summary = {
        "rows_analyzed": int(len(data)),
        "columns_analyzed": int(len(data.columns)),
        "columns": []
    }

    # Limit the amount of result metadata sent to Gemini.
    for column in data.columns[:12]:

        series = data[column]
        column_summary = {
            "column": str(column),
            "data_type": str(series.dtype),
            "missing_values": int(series.isna().sum()),
            "unique_values": int(series.nunique(dropna=True))
        }

        # Do not send values from columns that look like personal identifiers.
        if _is_sensitive_or_identifier(column):
            column_summary["values_omitted"] = (
                "Potentially sensitive or identifier column; values omitted."
            )

        elif pd.api.types.is_numeric_dtype(series):

            numeric = pd.to_numeric(series, errors="coerce").dropna()

            if not numeric.empty:
                column_summary["statistics"] = {
                    "minimum": _clean_number(numeric.min()),
                    "maximum": _clean_number(numeric.max()),
                    "mean": _clean_number(numeric.mean()),
                    "median": _clean_number(numeric.median()),
                    "standard_deviation": _clean_number(numeric.std())
                }

        elif series.nunique(dropna=True) <= 30:

            top_values = series.value_counts(dropna=True).head(5)

            column_summary["most_common_values"] = [
                {
                    "value": str(value)[:80],
                    "count": int(count)
                }
                for value, count in top_values.items()
            ]

        summary["columns"].append(column_summary)

    if len(data.columns) > 12:
        summary["omitted_columns"] = int(len(data.columns) - 12)

    # Include only strong correlations between non-identifier numeric columns.
    numeric_columns = [
        column
        for column in data.select_dtypes(include="number").columns
        if not _is_sensitive_or_identifier(column)
    ][:8]

    if len(numeric_columns) >= 2:
        correlations = data[numeric_columns].corr(numeric_only=True)
        pairs = []

        for i, first_column in enumerate(numeric_columns):
            for second_column in numeric_columns[i + 1:]:
                correlation = correlations.loc[first_column, second_column]

                if pd.notna(correlation) and abs(correlation) >= 0.6:
                    pairs.append({
                        "first_column": str(first_column),
                        "second_column": str(second_column),
                        "correlation": _clean_number(correlation)
                    })

        summary["strong_correlations"] = pairs[:8]

    return summary


def generate_insights(question, sql, data):

    data_summary = _build_data_summary(data)

    prompt = f"""
You are QueryMind's AI Insight Engine, a careful data analyst.

Analyse the user's SQL query result and produce useful, evidence-based insights.

USER QUESTION:
{question}

SQL QUERY:
{sql}

DATA SUMMARY:
{json.dumps(data_summary, ensure_ascii=False, allow_nan=False)}

INSTRUCTIONS:

1. Use only the supplied data summary. Do not invent values, columns, trends or causes.
2. Identify useful comparisons, high/low values, distributions, missing data,
   unusual values or strong correlations when supported by the summary.
3. Do not force insights when the data does not support them.
4. Every finding must include specific evidence from the supplied summary.
5. Do not confuse correlation with causation.
6. Recommendations must be practical and must not claim unsupported causes.
7. Do not make claims about rows or columns that were omitted.
8. Do not repeat the same observation in multiple insights.
9. Write in clear, concise language for a non-technical user.
10. Return 2 to 5 insights when the data supports them. Return fewer if necessary.

Return ONLY valid JSON in this exact structure:

{{
    "overall_summary": "A concise summary of what the returned data shows.",
    "insights": [
        {{
            "title": "Short finding title",
            "type": "comparison",
            "observation": "Explain the finding in plain English.",
            "evidence": "Quote the relevant values or counts from the data summary.",
            "recommendation": "A practical next step, or an empty string if none is justified."
        }}
    ],
    "caveats": "Mention relevant limitations, or an empty string if there are none."
}}

Allowed insight types:
- comparison
- trend
- distribution
- anomaly
- data_quality
- correlation
- general

Return valid JSON only. Do not include Markdown fences.
"""

    response = ask_gemini(
        prompt,
        max_output_tokens=1600
    )

    try:
        insights = json.loads(response)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Gemini returned an invalid insight response. Please try again."
        ) from error

    required_keys = ["overall_summary", "insights", "caveats"]

    for key in required_keys:
        if key not in insights:
            raise ValueError(f"Missing insight field: {key}")

    if not isinstance(insights["insights"], list):
        raise ValueError("Invalid AI insights format.")

    cleaned_insights = []

    for insight in insights["insights"]:

        if not isinstance(insight, dict):
            continue

        required_insight_fields = [
            "title",
            "type",
            "observation",
            "evidence"
        ]

        if not all(field in insight for field in required_insight_fields):
            continue

        cleaned_insights.append({
            "title": str(insight["title"]),
            "type": str(insight["type"]),
            "observation": str(insight["observation"]),
            "evidence": str(insight["evidence"]),
            "recommendation": str(insight.get("recommendation", ""))
        })

    insights["insights"] = cleaned_insights
    insights["overall_summary"] = str(insights["overall_summary"])
    insights["caveats"] = str(insights["caveats"])

    return insights
