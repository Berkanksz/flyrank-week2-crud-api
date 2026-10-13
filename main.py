from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import repository


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the server starts: make sure Postgres tasks table & seed are ready."""
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
    """Check if the server and database are alive."""
    # Extra stretch: check db health as well
    try:
        with repository.get_db() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "db": "ok"}
    except Exception:
        return {"status": "ok"}


@app.get("/tasks")
def get_tasks(search: str | None = None, done: bool | None = None, sort: str | None = None):
    """List all tasks in the database.

    Optional filters (Extras), all done in Postgres with SQL:
    ?search=milk  -> WHERE title ILIKE '%milk%'
    ?done=true    -> WHERE done = true
    ?sort=title   -> ORDER BY LOWER(title) (default is ORDER BY id)
    """
    if sort not in (None, "id", "title"):
        raise HTTPException(status_code=400, detail="sort must be 'id' or 'title'")
    return repository.list_tasks(search=search, done=done, sort=sort)


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Get a single task by its ID."""
    task = repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.post("/tasks", status_code=201)
def create_task(task_in: TaskCreate):
    """Create a new task."""
    if not task_in.title or not task_in.title.strip():
        raise HTTPException(status_code=400, detail="Title is missing or empty")

    return repository.create_task(task_in.title.strip())


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_in: TaskUpdate):
    """Update an existing task."""
    if task_in.title is None and task_in.done is None:
        raise HTTPException(status_code=400, detail="Empty or invalid body")
    if task_in.title is not None and not task_in.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    clean_title = task_in.title.strip() if task_in.title is not None else None
    task = repository.update_task(task_id, title=clean_title, done=task_in.done)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task from the database."""
    deleted = repository.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.get("/stats")
def get_stats():
    """Get statistics about the tasks."""
    return repository.get_stats()