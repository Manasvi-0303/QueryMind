
import time

from core.schema_reader import get_database_schema
from core.sql_generator import generate_sql
from core.sql_executor import execute_sql


def ask_database(question, db_path):

    total_start = time.perf_counter()

    # Step 1: Read database schema
    start = time.perf_counter()
    schema = get_database_schema(db_path)
    schema_time = time.perf_counter() - start

    # Step 2: Generate SQL or clarification
    start = time.perf_counter()
    response = generate_sql(question, schema)
    gemini_time = time.perf_counter() - start

    # Step 3: Stop if clarification is needed
    if response["status"] == "clarification":

        total_time = time.perf_counter() - total_start

        print("\n--- QueryMind Performance ---")
        print(f"Schema reading: {schema_time:.3f} seconds")
        print(f"AI response: {gemini_time:.3f} seconds")
        print(f"Total time: {total_time:.3f} seconds")

        return {
            "status": "clarification",
            "clarification_question": response["clarification_question"],
            "sql": None,
            "result": None
        }

    # Step 4: Execute SQL
    start = time.perf_counter()
    sql_query = response["sql"]
    result = execute_sql(sql_query, db_path)
    sql_time = time.perf_counter() - start

    total_time = time.perf_counter() - total_start

    # Performance report
    print("\n--- QueryMind Performance ---")
    print(f"Schema reading: {schema_time:.3f} seconds")
    print(f"AI response: {gemini_time:.3f} seconds")
    print(f"SQL execution: {sql_time:.3f} seconds")
    print(f"Total time: {total_time:.3f} seconds")

    return {
        "status": "ready",
        "clarification_question": None,
        "sql": sql_query,
        "result": result
    }



