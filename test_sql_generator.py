
from core.schema_reader import get_database_schema
from core.sql_generator import generate_sql

# Read the database structure
schema = get_database_schema()

# Ask a question in normal English
question = "Show the top 5 students by their total marks obtained."

# Generate SQL using Gemini
sql_query = generate_sql(question, schema)

print("\nYour Question:")
print(question)

print("\nGenerated SQL Query:")
print(sql_query)
