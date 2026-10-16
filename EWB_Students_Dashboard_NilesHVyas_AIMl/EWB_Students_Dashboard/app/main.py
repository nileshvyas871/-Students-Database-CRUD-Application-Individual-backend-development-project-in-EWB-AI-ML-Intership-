from __future__ import annotations

import csv
import io
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("STUDENT_DB_PATH", BASE_DIR.parent / "students.db"))
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="EWB Edu Tech | Student Management",
    description="Student records CRUD API for the EWB Edu Tech internship project.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this list before deploying publicly.
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@contextmanager
def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_code TEXT UNIQUE,
                name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                phone TEXT,
                course TEXT,
                address TEXT,
                enrollment_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active'
                    CHECK(status IN ('Active', 'Completed', 'On Hold')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if count == 0 and os.getenv("SEED_DEMO_DATA", "true").lower() == "true":
            now = datetime.now(timezone.utc).isoformat()
            sample_rows = [
                ("EWB-1001", "Aarav Sharma", "2004-04-18", "aarav.sharma@example.com", "+91 90000 10001", "AI & Machine Learning", "Jaipur, Rajasthan", "2026-09-22", "Active"),
                ("EWB-1002", "Diya Patel", "2005-11-02", "diya.patel@example.com", "+91 90000 10002", "Python Backend Development", "Ahmedabad, Gujarat", "2026-09-22", "Active"),
                ("EWB-1003", "Kabir Singh", "2003-07-27", "kabir.singh@example.com", "+91 90000 10003", "AI & Machine Learning", "Delhi, India", "2026-09-23", "Completed"),
                ("EWB-1004", "Ananya Verma", "2006-01-14", "ananya.verma@example.com", "+91 90000 10004", "Data Analytics", "Lucknow, Uttar Pradesh", "2026-09-24", "Active"),
                ("EWB-1005", "Ishaan Mehta", "2004-09-09", "ishaan.mehta@example.com", "+91 90000 10005", "Python Backend Development", "Pune, Maharashtra", "2026-09-25", "On Hold"),
            ]
            conn.executemany("""
                INSERT INTO students
                (student_code, name, date_of_birth, email, phone, course, address, enrollment_date, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [(*row, now, now) for row in sample_rows])


class StudentCreate(BaseModel):
    student_code: Optional[str] = Field(default=None, max_length=30)
    name: str = Field(min_length=2, max_length=100)
    date_of_birth: date
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    course: Optional[str] = Field(default=None, max_length=120)
    address: Optional[str] = Field(default=None, max_length=250)
    enrollment_date: date = Field(default_factory=date.today)
    status: str = Field(default="Active")

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        value = " ".join(value.split())
        if not value:
            raise ValueError("Name cannot be blank")
        return value

    @field_validator("student_code", "phone", "course", "address")
    @classmethod
    def trim_optional(cls, value):
        return value.strip() if value else value

    @field_validator("status")
    @classmethod
    def valid_status(cls, value):
        if value not in {"Active", "Completed", "On Hold"}:
            raise ValueError("Status must be Active, Completed, or On Hold")
        return value


class StudentUpdate(BaseModel):
    student_code: Optional[str] = Field(default=None, max_length=30)
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    course: Optional[str] = Field(default=None, max_length=120)
    address: Optional[str] = Field(default=None, max_length=250)
    enrollment_date: Optional[date] = None
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, value):
        if value is not None and value not in {"Active", "Completed", "On Hold"}:
            raise ValueError("Status must be Active, Completed, or On Hold")
        return value


def row_to_dict(row):
    return dict(row) if row else None


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    with get_db() as conn:
        conn.execute("SELECT 1").fetchone()
    return {"status": "ok", "database": "connected", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/stats")
def stats():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM students WHERE status='Active'").fetchone()[0]
        completed = conn.execute("SELECT COUNT(*) FROM students WHERE status='Completed'").fetchone()[0]
        on_hold = conn.execute("SELECT COUNT(*) FROM students WHERE status='On Hold'").fetchone()[0]
        courses = conn.execute("SELECT COUNT(DISTINCT course) FROM students WHERE course IS NOT NULL AND course != ''").fetchone()[0]
        recent = conn.execute("SELECT id, student_code, name, course, status, enrollment_date FROM students ORDER BY id DESC LIMIT 5").fetchall()
        course_rows = conn.execute("""
            SELECT COALESCE(NULLIF(course, ''), 'Not specified') AS course, COUNT(*) AS count
            FROM students GROUP BY COALESCE(NULLIF(course, ''), 'Not specified')
            ORDER BY count DESC, course ASC LIMIT 6
        """).fetchall()
    return {
        "total": total, "active": active, "completed": completed, "on_hold": on_hold,
        "courses": courses, "recent": [row_to_dict(r) for r in recent],
        "course_breakdown": [row_to_dict(r) for r in course_rows],
    }


@app.get("/students")
def list_students(
    search: Optional[str] = Query(default=None, max_length=120),
    status: Optional[str] = Query(default=None),
    course: Optional[str] = Query(default=None, max_length=120),
    born_after: Optional[date] = None,
    born_before: Optional[date] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
):
    if status and status not in {"Active", "Completed", "On Hold"}:
        raise HTTPException(status_code=422, detail="Invalid status filter")
    clauses, params = [], []
    if search:
        like = f"%{search.strip()}%"
        clauses.append("(name LIKE ? OR email LIKE ? OR student_code LIKE ? OR phone LIKE ? OR course LIKE ?)")
        params.extend([like] * 5)
    if status:
        clauses.append("status = ?")
        params.append(status)
    if course:
        clauses.append("course = ?")
        params.append(course)
    if born_after:
        clauses.append("date_of_birth > ?")
        params.append(born_after.isoformat())
    if born_before:
        clauses.append("date_of_birth < ?")
        params.append(born_before.isoformat())
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM students" + where, params).fetchone()[0]
        rows = conn.execute(
            "SELECT * FROM students" + where + " ORDER BY id DESC LIMIT ? OFFSET ?",
            [*params, page_size, (page - 1) * page_size],
        ).fetchall()
    return {"items": [row_to_dict(r) for r in rows], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}


@app.get("/students/{student_id}")
def get_student(student_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")
    return row_to_dict(row)


@app.post("/students", status_code=201)
def create_student(student: StudentCreate):
    payload = student.model_dump()
    payload["date_of_birth"] = payload["date_of_birth"].isoformat()
    payload["enrollment_date"] = payload["enrollment_date"].isoformat()
    now = datetime.now(timezone.utc).isoformat()
    payload["created_at"] = now
    payload["updated_at"] = now
    fields = list(payload.keys())
    try:
        with get_db() as conn:
            cursor = conn.execute(
                f"INSERT INTO students ({', '.join(fields)}) VALUES ({', '.join(['?'] * len(fields))})",
                [str(payload[k]) if payload[k] is not None else None for k in fields],
            )
            row = conn.execute("SELECT * FROM students WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return row_to_dict(row)
    except sqlite3.IntegrityError as exc:
        message = "Student code already exists" if "student_code" in str(exc) else "Email already exists"
        raise HTTPException(status_code=409, detail=message)


@app.put("/students/{student_id}")
@app.patch("/students/{student_id}")
def update_student(student_id: int, student: StudentUpdate):
    changes = student.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")
    for key in ("date_of_birth", "enrollment_date"):
        if changes.get(key) is not None:
            changes[key] = changes[key].isoformat()
    if "name" in changes and changes["name"] is not None:
        changes["name"] = " ".join(changes["name"].split())
    changes["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        with get_db() as conn:
            exists = conn.execute("SELECT id FROM students WHERE id = ?", (student_id,)).fetchone()
            if not exists:
                raise HTTPException(status_code=404, detail="Student not found")
            set_clause = ", ".join(f"{key} = ?" for key in changes)
            conn.execute(f"UPDATE students SET {set_clause} WHERE id = ?", [*changes.values(), student_id])
            row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        return row_to_dict(row)
    except sqlite3.IntegrityError as exc:
        message = "Student code already exists" if "student_code" in str(exc) else "Email already exists"
        raise HTTPException(status_code=409, detail=message)


@app.delete("/students/{student_id}", status_code=204)
def delete_student(student_id: int):
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Student not found")
    return Response(status_code=204)


@app.get("/students/export/csv")
def export_students_csv():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT student_code, name, date_of_birth, email, phone, course, address,
                   enrollment_date, status, created_at, updated_at
            FROM students ORDER BY id
        """).fetchall()
    # Pandas is used here to provide a clean, portable export for reporting.
    df = pd.DataFrame([dict(r) for r in rows], columns=[
        "student_code", "name", "date_of_birth", "email", "phone", "course",
        "address", "enrollment_date", "status", "created_at", "updated_at"
    ])
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="ewb_students.csv"'},
    )


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
