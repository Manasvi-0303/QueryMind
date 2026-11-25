import json
import re

import pandas as pd

from core.gemini_client import ask_gemini


ALLOWED_OPERATORS = {"<", "<=", ">", ">=", "=="}


def interpret_scenario(scenario, data):
    """Convert a natural-language scenario into a restricted JSON instruction."""

    if data.empty:
        raise ValueError("There are no query results to simulate.")

    column_details = [
        {
            "name": str(column),
            "data_type": str(data[column].dtype)
        }
        for column in data.columns
    ]

    prompt = f"""
You are QueryMind's What-If Analysis interpreter.
Convert the user's hypothetical scenario into a safe, structured instruction.

USER SCENARIO:
{scenario}

AVAILABLE RESULT COLUMNS:
{json.dumps(column_details, ensure_ascii=False)}

SUPPORTED OPERATION:
Increase or decrease numeric percentage values by a fixed number of percentage points
for rows that match one numeric threshold condition.

Return ONLY valid JSON in this exact structure:
{{
    "target_column": "exact column name from the available columns",
    "condition_operator": "<",
    "threshold": 60,
    "adjustment_type": "percentage_points",
    "adjustment_value": 10,
    "cap_min": 0,
    "cap_max": 100,
    "interpretation": "Increase values below 60 by 10 percentage points."
}}

Rules:
1. target_column must exactly match an available column name.
2. Choose a numeric column that represents the percentage being changed.
3. Supported condition_operator values: <, <=, >, >=, ==.
4. adjustment_type must be either percentage_points or relative_percent.
5. Use percentage_points for wording such as '10 percentage points'.
6. Use relative_percent for wording such as 'increase by 10 percent'.
7. Do not confuse a 10 percentage-point increase with a 10 percent relative increase.
8. threshold and adjustment_value must be numeric.
9. cap_min and cap_max should normally be 0 and 100 for percentages.
10. If the scenario is unclear, unsupported, or cannot be mapped to a numeric percentage column,
    return {{"error": "Explain what needs clarification."}}.
11. Do not generate SQL or Python code.
12. Return JSON only, without Markdown fences.
"""

    response = ask_gemini(prompt, max_output_tokens=700)

    try:
        instruction = json.loads(response)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Could not understand the scenario. Please rephrase it."
        ) from error

    if not isinstance(instruction, dict):
        raise ValueError("The scenario interpreter returned an invalid response.")

    if instruction.get("error"):
        raise ValueError(str(instruction["error"]))

    required = [
        "target_column",
        "condition_operator",
        "threshold",
        "adjustment_type",
        "adjustment_value",
        "cap_min",
        "cap_max",
        "interpretation"
    ]

    missing = [key for key in required if key not in instruction]
    if missing:
        raise ValueError(
            "The scenario could not be converted into a complete instruction."
        )

    target_column = instruction["target_column"]

    if target_column not in data.columns:
        raise ValueError(
            f"The selected column '{target_column}' is not in the query results."
        )

    if not pd.api.types.is_numeric_dtype(data[target_column]):
        raise ValueError(
            f"'{target_column}' is not a numeric column. Choose a result containing percentage values."
        )

    if instruction["condition_operator"] not in ALLOWED_OPERATORS:
        raise ValueError("The scenario uses an unsupported comparison operator.")

    if instruction["adjustment_type"] != "percentage_points":
        raise ValueError(
            "This version supports percentage-point changes, not relative percentage changes. "
            "For example, say 'increase by 10 percentage points'."
        )

    try:
        threshold = float(instruction["threshold"])
        adjustment_value = float(instruction["adjustment_value"])
        cap_min = float(instruction["cap_min"])
        cap_max = float(instruction["cap_max"])
    except (TypeError, ValueError) as error:
        raise ValueError("The scenario contains an invalid numeric value.") from error

    if not all(pd.notna(value) for value in [threshold, adjustment_value, cap_min, cap_max]):
        raise ValueError("The scenario contains a missing numeric value.")

    if not (0 <= threshold <= 100):
        raise ValueError("The percentage threshold must be between 0 and 100.")

    if not (-100 <= adjustment_value <= 100) or adjustment_value == 0:
        raise ValueError("The adjustment must be a non-zero value between -100 and 100.")

    if cap_min < 0 or cap_max > 100 or cap_min >= cap_max:
        raise ValueError("Percentage limits must be valid values between 0 and 100.")

    instruction["threshold"] = threshold
    instruction["adjustment_value"] = adjustment_value
    instruction["cap_min"] = cap_min
    instruction["cap_max"] = cap_max
    instruction["target_column"] = target_column

    return instruction


def _matches_condition(values, operator, threshold):
    if operator == "<":
        return values < threshold
    if operator == "<=":
        return values <= threshold
    if operator == ">":
        return values > threshold
    if operator == ">=":
        return values >= threshold
    if operator == "==":
        return values == threshold

    raise ValueError("Unsupported comparison operator.")


def run_what_if(scenario, data):
    """Apply a hypothetical percentage-point change to a copy of the results."""

    if not scenario or not scenario.strip():
        raise ValueError("Enter a what-if scenario first.")

    instruction = interpret_scenario(scenario, data)
    target_column = instruction["target_column"]

    original_values = pd.to_numeric(
        data[target_column],
        errors="coerce"
    )

    valid_values = original_values.dropna()

    if valid_values.empty:
        raise ValueError("The selected column has no numeric values to simulate.")

    if ((valid_values < 0) | (valid_values > 100)).any():
        raise ValueError(
            f"'{target_column}' contains values outside the 0–100 percentage range. "
            "This simulation expects percentage values, not decimals or fractions."
        )

    matching_rows = _matches_condition(
        original_values,
        instruction["condition_operator"],
        instruction["threshold"]
    ) & original_values.notna()

    affected_rows = int(matching_rows.sum())

    if affected_rows == 0:
        raise ValueError(
            "No rows match the scenario's condition. Check the threshold and query results."
        )

    simulated_data = data.copy(deep=True)
    simulated_values = original_values.copy()

    simulated_values.loc[matching_rows] = (
        simulated_values.loc[matching_rows]
        + instruction["adjustment_value"]
    ).clip(
        lower=instruction["cap_min"],
        upper=instruction["cap_max"]
    )

    simulated_data[target_column] = simulated_values

    original_average = float(valid_values.mean())
    simulated_average = float(simulated_values.dropna().mean())
    average_change = simulated_average - original_average

    comparison_data = pd.DataFrame({
        "Original value": original_values,
        "Simulated value": simulated_values,
        "Changed": matching_rows
    })

    return {
        "interpretation": instruction["interpretation"],
        "target_column": target_column,
        "affected_rows": affected_rows,
        "total_rows": int(len(data)),
        "original_average": round(original_average, 2),
        "simulated_average": round(simulated_average, 2),
        "average_change": round(average_change, 2),
        "comparison_data": comparison_data,
        "simulated_data": simulated_data
    }


