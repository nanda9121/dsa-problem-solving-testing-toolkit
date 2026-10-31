import json
import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("ALGOTEST_DB", BASE_DIR / "instance" / "algotest.sqlite3"))


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                topic TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                description TEXT NOT NULL,
                input_format TEXT NOT NULL,
                output_format TEXT NOT NULL,
                constraints_text TEXT NOT NULL,
                examples_json TEXT NOT NULL,
                starter_code TEXT NOT NULL,
                tests_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                status TEXT NOT NULL,
                passed INTEGER NOT NULL,
                total INTEGER NOT NULL,
                runtime_ms REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(problem_id) REFERENCES problems(id)
            );
        """)


def seed_problems(problems):
    with get_connection() as conn:
        for p in problems:
            conn.execute("""
                INSERT OR IGNORE INTO problems
                (slug, title, topic, difficulty, description, input_format,
                 output_format, constraints_text, examples_json, starter_code, tests_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["slug"], p["title"], p["topic"], p["difficulty"], p["description"],
                p["input_format"], p["output_format"], p["constraints"],
                json.dumps(p["examples"]), p["starter_code"], json.dumps(p["tests"])
            ))


def list_problems(topic=None, difficulty=None, search=None):
    query = "SELECT id, slug, title, topic, difficulty, description FROM problems WHERE 1=1"
    params = []
    if topic:
        query += " AND topic = ?"
        params.append(topic)
    if difficulty:
        query += " AND difficulty = ?"
        params.append(difficulty)
    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY CASE difficulty WHEN 'Easy' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, title"
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


def get_problem(problem_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM problems WHERE id = ?", (problem_id,)).fetchone()
    if not row:
        return None
    item = dict(row)
    item["examples"] = json.loads(item.pop("examples_json"))
    item["tests"] = json.loads(item.pop("tests_json"))
    item["constraints"] = item.pop("constraints_text")
    return item


def add_submission(problem_id, code, status, passed, total, runtime_ms):
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO submissions (problem_id, code, status, passed, total, runtime_ms)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (problem_id, code, status, passed, total, runtime_ms))
        return cur.lastrowid


def get_submissions(problem_id, limit=20):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, status, passed, total, runtime_ms, created_at
            FROM submissions WHERE problem_id = ?
            ORDER BY id DESC LIMIT ?
        """, (problem_id, limit)).fetchall()
    return [dict(row) for row in rows]


def get_stats():
    with get_connection() as conn:
        total_problems = conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
        total_submissions = conn.execute("SELECT COUNT(*) FROM submissions").fetchone()[0]
        solved = conn.execute("""
            SELECT COUNT(DISTINCT problem_id) FROM submissions WHERE status = 'Accepted'
        """).fetchone()[0]
        accepted = conn.execute("SELECT COUNT(*) FROM submissions WHERE status = 'Accepted'").fetchone()[0]
    rate = round((accepted / total_submissions) * 100, 1) if total_submissions else 0
    return {
        "total_problems": total_problems,
        "total_submissions": total_submissions,
        "solved_problems": solved,
        "success_rate": rate,
    }
