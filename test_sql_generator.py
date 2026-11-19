
import time
from pathlib import Path

from core.schema_reader import get_database_schema
from core.sql_generator import generate_sql

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "college.db"

if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found: {DB_PATH}")

question = "Show me the performance of students."

print("Reading database schema...")
schema = get_database_schema(DB_PATH)

print("Generating SQL...")
start = time.perf_counter()

sql = generate_sql(question, schema)

end = time.perf_counter()

print("\nGenerated SQL:")
print(sql)

print(f"\nGemini SQL generation time: {end - start:.2f} seconds")

