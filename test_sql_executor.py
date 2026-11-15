
from core.sql_executor import execute_sql

query = """
SELECT
    s.name,
    SUM(m.marks_obtained) AS total_marks
FROM students s
JOIN marks m
    ON s.student_id = m.student_id
GROUP BY s.student_id, s.name
ORDER BY total_marks DESC
LIMIT 5
"""

result = execute_sql(query)

print("\nQUERY RESULTS:")
print(result)
