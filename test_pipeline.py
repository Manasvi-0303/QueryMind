
from core.query_pipeline import ask_database

question = "Show the top 5 students by their total marks."

sql, result = ask_database(question)

print("\nYOUR QUESTION:")
print(question)

print("\nGENERATED SQL:")
print(sql)

print("\nQUERY RESULTS:")
print(result)
