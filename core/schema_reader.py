
import sqlite3
from pathlib import Path
from functools import lru_cache


@lru_cache(maxsize=16)
def get_database_schema(db_path):
    db_path = Path(db_path).resolve()

    if not db_path.exists():
        raise FileNotFoundError("Database file not found.")

    connection = sqlite3.connect(
        db_path.as_uri() + "?mode=ro",
        uri=True
    )

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
        """)

        tables = cursor.fetchall()
        schema = ""

        for table in tables:
            table_name = table[0]

            cursor.execute(
                f'PRAGMA table_info("{table_name}")'
            )

            columns = cursor.fetchall()

            schema += f"\nTable: {table_name}\n"
            schema += "Columns:\n"

            for column in columns:
                schema += f"- {column[1]} ({column[2]})\n"

        return schema

    finally:
        connection.close()



