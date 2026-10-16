# EWB Edu Tech — Student Management Dashboard

A full-stack student records CRUD project built for the EWB Edu Tech Python Backend Development internship assignment. It uses **FastAPI**, **SQLite**, **Pydantic**, **Pandas**, and a responsive HTML/CSS/JavaScript dashboard.

## Features

- Create, read, update and delete student records.
- Persistent SQLite database; records remain after restarting the server.
- Dashboard metrics for total, active, completed students and distinct courses.
- Search across name, email, student code, phone and course.
- Filter by status and course; paginated results.
- Form validation, duplicate email/student-code protection, and helpful 404/409 errors.
- CSV export using Pandas.
- API docs at `/docs`, health check at `/health`.
- Fictional demo records are inserted into an empty database by default.

## Requirements

- Python 3.10 or newer (Python 3.11/3.12 recommended)
- Internet only for the first dependency installation; the app itself runs locally.
- No separate SQLite download is required. SQLite is included with most Python installations.
- Ollama is **not required**; the assignment's AI extension is optional and is not included in this core CRUD version.

## Run on Windows

Open PowerShell in this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

- Dashboard: http://127.0.0.1:8000
- Interactive API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

Stop the server with `Ctrl+C`.

## Run on macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/students` | Create a student |
| `GET` | `/students` | List/search/filter students |
| `GET` | `/students/{student_id}` | Fetch one student |
| `PUT` / `PATCH` | `/students/{student_id}` | Update a student |
| `DELETE` | `/students/{student_id}` | Delete a student |
| `GET` | `/api/stats` | Dashboard summary metrics |
| `GET` | `/students/export/csv` | Download student CSV |
| `GET` | `/health` | API/database health |
| `GET` | `/docs` | Swagger API documentation |

### Example create request

```json
{
  "student_code": "EWB-2001",
  "name": "Riya Sharma",
  "date_of_birth": "2005-05-12",
  "email": "riya.sharma@example.com",
  "phone": "+91 98765 43210",
  "course": "AI & Machine Learning",
  "address": "Jaipur, Rajasthan",
  "enrollment_date": "2026-10-01",
  "status": "Active"
}
```

### Search and filters

- `/students?search=riya`
- `/students?status=Active`
- `/students?course=AI%20%26%20Machine%20Learning`
- `/students?born_after=2005-01-01`
- `/students?page=2&page_size=10`

The `born_after` and `born_before` filters use strict comparisons. Use ISO dates (`YYYY-MM-DD`).

## Database and demo data

The database is created automatically at `students.db` in the project root. The first launch seeds five fictional sample records if the database is empty.

To start with an empty database, set `SEED_DEMO_DATA=false` before the first launch.

PowerShell:
```powershell
$env:SEED_DEMO_DATA="false"
uvicorn app.main:app --reload
```

macOS/Linux:
```bash
SEED_DEMO_DATA=false uvicorn app.main:app --reload
```

To use another database path, set `STUDENT_DB_PATH` to an absolute path. Do not delete `students.db` unless you intend to remove the stored records.

## Run tests

```bash
pytest -q
```

## GitHub submission checklist

1. Create a new GitHub repository, for example `ewb-student-management`.
2. Upload the project source, `README.md`, and `requirements.txt`.
3. Do not upload `.venv`, `.env`, database files, passwords, or real student data.
4. Copy your repository URL and submit it through the channel shared by your EWB trainer.

## Before real deployment

This is an internship/demo project, not a production student information system. Before exposing it to the public internet, add authentication and role-based authorization, restrict CORS origins, configure HTTPS, add backups and audit logging, and review privacy requirements. The current dashboard is intended for local development.

## Project structure

```text
EWB_Students_Dashboard/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── static/
│       ├── index.html
│       ├── styles.css
│       └── app.js
├── tests/
│   └── test_api.py
├── .gitignore
├── README.md
└── requirements.txt
```
