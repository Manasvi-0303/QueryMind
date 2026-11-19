
from pathlib import Path

from core.sql_executor import execute_sql

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "college.db"

sql = "DELETE FROM students;"

print("Executing SQL...")

result = execute_sql(sql, DB_PATH)

print("\nQuery Result:")
print(result)

print("\nNumber of rows:", len(result))

