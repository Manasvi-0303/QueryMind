
import sqlite3
import pandas as pd

DB_PATH = "data/college.db"


def execute_sql(sql):

    connection = sqlite3.connect(
        f"file:{DB_PATH}?mode=ro",
        uri=True
    )

    try:
        # Allow only read operations
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

        # Execute the generated SQL
        cursor.execute(sql)

        # Get column names
        columns = [description[0] for description in cursor.description]

        # Fetch a maximum of 500 rows
        rows = cursor.fetchmany(501)

        if len(rows) > 500:
            rows = rows[:500]

        # Convert results into a DataFrame
        result = pd.DataFrame(rows, columns=columns)

        return result

    finally:
        connection.close()
