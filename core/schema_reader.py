
import sqlite3

DB_PATH = "data/college.db"


def get_database_schema():

    connection = sqlite3.connect(DB_PATH)
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

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        schema += f"\nTable: {table_name}\n"
        schema += "Columns:\n"

        for column in columns:
            column_name = column[1]
            column_type = column[2]

            schema += f"- {column_name} ({column_type})\n"

    connection.close()

    return schema
