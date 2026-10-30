import sqlite3
from pathlib import Path
from datetime import datetime

# Database file location
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "student_progress.db"


def initialize_database():
    """Create the quiz history table if it does not exist."""

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_topic TEXT NOT NULL,
                total_questions INTEGER NOT NULL,
                score INTEGER NOT NULL,
                accuracy REAL NOT NULL,
                attempted_at TEXT NOT NULL
            )
        """)


def save_quiz_attempt(topic, total_questions, score):
    """Save a quiz attempt and return its database ID."""

    accuracy = (
        score / total_questions * 100
        if total_questions > 0 else 0
    )

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            INSERT INTO quiz_attempts (
                quiz_topic,
                total_questions,
                score,
                accuracy,
                attempted_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            topic,
            total_questions,
            score,
            round(accuracy, 2),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        return cursor.lastrowid


def get_quiz_history():
    """Return all saved quiz attempts, newest first."""

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT *
            FROM quiz_attempts
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]

# ---------------------------------------
# STUDY PLAN DATABASE
# ---------------------------------------

def initialize_study_plan_table():
    """Create the study plans table if it does not exist."""

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_name TEXT NOT NULL,
                exam_date TEXT NOT NULL,
                daily_hours INTEGER NOT NULL,
                weak_topics TEXT,
                other_topics TEXT,
                created_at TEXT NOT NULL
            )
        """)


def save_study_plan(
    exam_name,
    exam_date,
    daily_hours,
    weak_topics,
    other_topics
):
    """Save a study plan in the database."""

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            INSERT INTO study_plans (
                exam_name,
                exam_date,
                daily_hours,
                weak_topics,
                other_topics,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            exam_name,
            str(exam_date),
            daily_hours,
            weak_topics,
            other_topics,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        return cursor.lastrowid


def get_study_plans():
    """Return saved study plans, newest first."""

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT *
            FROM study_plans
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]

# ---------------------------------------
# STUDY TASK COMPLETION TRACKER
# ---------------------------------------

def initialize_study_tasks_table():
    """Create a table to track completed study tasks."""

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                task_name TEXT NOT NULL,
                is_completed INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (plan_id) REFERENCES study_plans(id)
            )
        """)


def add_study_task(plan_id, task_name):
    """Add a task to a saved study plan."""

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            INSERT INTO study_tasks (
                plan_id, task_name, is_completed, updated_at
            )
            VALUES (?, ?, 0, ?)
        """, (
            plan_id,
            task_name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        return cursor.lastrowid


def get_study_tasks(plan_id):
    """Get all tasks for a selected study plan."""

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT *
            FROM study_tasks
            WHERE plan_id = ?
            ORDER BY id
        """, (plan_id,)).fetchall()

        return [dict(row) for row in rows]


def update_study_task(task_id, is_completed):
    """Update a task's completion status."""

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            UPDATE study_tasks
            SET is_completed = ?, updated_at = ?
            WHERE id = ?
        """, (
            1 if is_completed else 0,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            task_id
        ))

# ---------------------------------------
# STUDENT PROFILE DATABASE
# ---------------------------------------

def initialize_student_profile_table():
    """Create the student profile table."""

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS student_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                course TEXT NOT NULL,
                semester TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def save_student_profile(student_name, course, semester):
    """Save or update the student's profile."""

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO student_profiles (
                id, student_name, course, semester, updated_at
            )
            VALUES (
                1, ?, ?, ?, ?
            )
            ON CONFLICT(id) DO UPDATE SET
                student_name = excluded.student_name,
                course = excluded.course,
                semester = excluded.semester,
                updated_at = excluded.updated_at
        """, (
            student_name,
            course,
            semester,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))


def get_student_profile():
    """Retrieve the saved student profile."""

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        row = conn.execute("""
            SELECT student_name, course, semester, updated_at
            FROM student_profiles
            WHERE id = 1
        """).fetchone()

        return dict(row) if row else None
