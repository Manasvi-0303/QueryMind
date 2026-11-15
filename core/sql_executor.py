
import sqlite3
import pandas as pd
from pathlib import Path


def execute_sql(sql, db_path):

    db_path = Path(db_path).resolve()

    if not db_path.exists():
        raise FileNotFoundError("Database file not found.")

    connection = sqlite3.connect(
        db_path.as_uri() + "?mode=ro",
        uri=True
    )

    try:
        connection.execute("PRAGMA query_only = ON")

        allowed_actions = {
            sqlite3.SQLITE_SELECT,
            sqlite3.SQLITE_READ,
            sqlite3.SQLITE_FUNCTION
        }

        if hasattr(sqlite3, "SQLITE_RECURSIVE"):
            allowed_actions.add(sqlite3.SQLITE_RECURSIVE)

        def authorize(action, arg1, arg2, database, trigger):
            if action in allowed_actions:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        connection.set_authorizer(authorize)

        cursor = connection.cursor()

        # Reject multiple SQL statements
        if not sql.strip():
            raise ValueError("SQL query cannot be empty.")

        cursor.execute(sql)

        if cursor.description is None:
            raise ValueError("Only queries returning data are allowed.")

        columns = [description[0] for description in cursor.description]

        rows = cursor.fetchmany(501)

        if len(rows) > 500:
            rows = rows[:500]

        return pd.DataFrame(rows, columns=columns)

    finally:
        connection.close()

