
from core.schema_reader import get_database_schema
from core.sql_generator import generate_sql
from core.sql_executor import execute_sql


def ask_database(question):

    # Step 1: Read database schema
    schema = get_database_schema()

    # Step 2: Generate SQL using Gemini
    sql_query = generate_sql(question, schema)

    # Step 3: Execute generated SQL
    result = execute_sql(sql_query)

    # Step 4: Return SQL and results
    return sql_query, result
