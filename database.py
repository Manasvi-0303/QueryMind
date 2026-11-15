
import sqlite3
import random
from pathlib import Path

# Database location
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "college.db"


def create_database():
    DATA_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    # 1. Students table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        department TEXT,
        year INTEGER,
        city TEXT
    )
    """)

    # 2. Courses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY,
        course_name TEXT NOT NULL,
        department TEXT,
        credits INTEGER
    )
    """)

    # 3. Marks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marks (
        mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        marks_obtained REAL,
        max_marks REAL,
        exam_type TEXT,
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
    )
    """)

    # 4. Attendance table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        classes_attended INTEGER,
        total_classes INTEGER,
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
    )
    """)

    # 5. Assignments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        assignment_name TEXT,
        score REAL,
        max_score REAL,
        submission_date TEXT,
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
    )
    """)

    # Insert sample data only when database is empty
    cursor.execute("SELECT COUNT(*) FROM students")
    student_count = cursor.fetchone()[0]

    if student_count == 0:

        departments = ["Computer Science", "AI & Data Science",
                       "Information Technology", "Electronics"]

        cities = ["Delhi", "Mumbai", "Jaipur", "Pune",
                  "Bangalore", "Chandigarh"]

        first_names = ["Aarav", "Ananya", "Rohan", "Priya",
                       "Ishaan", "Diya", "Kabir", "Meera",
                       "Arjun", "Sanya", "Rahul", "Kavya"]

        last_names = ["Sharma", "Verma", "Gupta", "Singh",
                      "Mehta", "Malhotra", "Kapoor", "Jain"]

        # Generate 100 students
        students = []

        for i in range(1, 101):
            name = random.choice(first_names) + " " + random.choice(last_names)

            students.append((
                i,
                name,
                f"student{i}@college.edu",
                random.choice(departments),
                random.randint(1, 4),
                random.choice(cities)
            ))

        cursor.executemany("""
        INSERT INTO students
        VALUES (?, ?, ?, ?, ?, ?)
        """, students)

        # Insert courses
        courses = [
            (1, "Data Structures", "Computer Science", 4),
            (2, "Database Management", "Computer Science", 4),
            (3, "Machine Learning", "AI & Data Science", 4),
            (4, "Artificial Intelligence", "AI & Data Science", 3),
            (5, "Operating Systems", "Computer Science", 4),
            (6, "Computer Networks", "Information Technology", 3),
            (7, "Statistics", "AI & Data Science", 3),
            (8, "Web Development", "Information Technology", 3)
        ]

        cursor.executemany("""
        INSERT INTO courses VALUES (?, ?, ?, ?)
        """, courses)

        # Generate marks, attendance and assignments
        marks_data = []
        attendance_data = []
        assignment_data = []

        exam_types = ["Midterm", "Final", "Quiz"]

        for student_id in range(1, 101):
            for course_id in range(1, 9):

                # Marks
                marks_data.append((
                    student_id,
                    course_id,
                    random.randint(30, 100),
                    100,
                    random.choice(exam_types)
                ))

                # Attendance
                total = random.randint(40, 60)
                attended = random.randint(20, total)

                attendance_data.append((
                    student_id,
                    course_id,
                    attended,
                    total
                ))

                # Three assignments per course
                for j in range(1, 4):
                    assignment_data.append((
                        student_id,
                        course_id,
                        f"Assignment {j}",
                        random.randint(5, 20),
                        20,
                        f"2026-10-{random.randint(1, 28):02d}"
                    ))

        cursor.executemany("""
        INSERT INTO marks
        (student_id, course_id, marks_obtained, max_marks, exam_type)
        VALUES (?, ?, ?, ?, ?)
        """, marks_data)

        cursor.executemany("""
        INSERT INTO attendance
        (student_id, course_id, classes_attended, total_classes)
        VALUES (?, ?, ?, ?)
        """, attendance_data)

        cursor.executemany("""
        INSERT INTO assignments
        (student_id, course_id, assignment_name, score, max_score, submission_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """, assignment_data)

    conn.commit()
    conn.close()

    print("Database created successfully!")


if __name__ == "__main__":
    create_database()
