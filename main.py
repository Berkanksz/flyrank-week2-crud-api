import sqlite3
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import repository

# SQLite database file. It lives next to main.py and is created automatically.
DB_PATH = Path(__file__).parent / "tasks.db"

# Example tasks inserted only on the very first run (when the table is empty).
SEED_TASKS = [
    ("Buy milk", 0),
    ("Learn FastAPI", 1),
    ("Complete internship assignment", 0),
]


@contextmanager
def get_db():
    """Open a connection, commit on success, roll back on error, always close."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def row_to_task(row: sqlite3.Row) -> dict:
    """Turn a database row into the same JSON shape A1 returned (done as true/false)."""
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


def init_db():
    """Create tasks.db, the tasks table and the seed rows if they are missing."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id    INTEGER PRIMARY KEY,
                title TEXT    NOT NULL,
                done  INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1))
            )
            """
        )
        # Index on done: lets SQLite jump straight to matching rows for ?done=true
        # instead of scanning the whole table.
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks (done)")

        # get_db() wraps this block in one transaction: either all three seed tasks
        # are inserted or none are, so a crash mid-seed can't leave a half-seeded table.
        count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count == 0:
            conn.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", SEED_TASKS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the server starts: make sure the database is ready."""
    repository.init_db()
    yield


app = FastAPI(lifespan=lifespan)

class TaskCreate(BaseModel):
    title: str | None = None

class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

@app.get("/")
def read_root():
    """Get API metadata."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health_check():
    """Check if the server is alive."""
    return {"status": "ok"}

@app.get("/tasks")
def get_tasks(search: str | None = None, done: bool | None = None, sort: str | None = None):
    """List all tasks in the database.

    Optional filters (Extras), all done by SQL instead of Python loops:
    ?search=milk  -> WHERE title LIKE '%milk%'
    ?done=true    -> WHERE done = 1
    ?sort=title   -> ORDER BY title (default is ORDER BY id)
    """
    if sort not in (None, "id", "title"):
        raise HTTPException(status_code=400, detail="sort must be 'id' or 'title'")

    # Only fixed SQL fragments are joined together. User values always go in params.
    conditions = []
    params = []
    if search:
        conditions.append("title LIKE ?")
        params.append(f"%{search}%")
    if done is not None:
        conditions.append("done = ?")
        params.append(int(done))

    query = "SELECT * FROM tasks"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY title COLLATE NOCASE, id" if sort == "title" else " ORDER BY id"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [row_to_task(row) for row in rows]

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Get a single task by its ID."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return row_to_task(row)

@app.post("/tasks", status_code=201)
def create_task(task_in: TaskCreate):
    """Create a new task."""
    if not task_in.title or not task_in.title.strip():
        raise HTTPException(status_code=400, detail="Title is missing or empty")

    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)", (task_in.title, 0)
        )
        new_id = cursor.lastrowid
    return {"id": new_id, "title": task_in.title, "done": False}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_in: TaskUpdate):
    """Update an existing task."""
    if task_in.title is None and task_in.done is None:
        raise HTTPException(status_code=400, detail="Empty or invalid body")
    if task_in.title is not None and not task_in.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    # COALESCE(?, column) keeps the old value when a field is not sent,
    # so partial updates behave exactly like in Assignment 1.
    done_value = None if task_in.done is None else int(task_in.done)
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE tasks SET title = COALESCE(?, title), done = COALESCE(?, done) WHERE id = ?",
            (task_in.title, done_value, task_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row_to_task(row)

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task from the database."""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.get("/stats")
def get_stats():
    """Get statistics about the tasks."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(done), 0) AS done FROM tasks"
        ).fetchone()
    total = row["total"]
    done = row["done"]
    open_tasks = total - done
    return {"total": total, "done": done, "open": open_tasks}