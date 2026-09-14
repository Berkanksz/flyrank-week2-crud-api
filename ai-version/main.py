"""
Task API - Single-file CRUD service built with FastAPI.
In-memory storage, no database dependency.
"""

from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, field_validator

app = FastAPI(title="Task API", version="1.0")


# ---------- Models ----------

class Task(BaseModel):
    id: int
    title: str
    done: bool = False


class TaskCreate(BaseModel):
    title: str
    done: bool = False

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title must not be empty")
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_not_empty_if_present(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("title must not be empty")
        return v


# ---------- In-memory storage ----------

tasks: list[Task] = [
    Task(id=1, title="Set up FastAPI project", done=True),
    Task(id=2, title="Design task schema", done=True),
    Task(id=3, title="Implement CRUD endpoints", done=False),
]
_next_id = 4


def get_next_id() -> int:
    global _next_id
    current = _next_id
    _next_id += 1
    return current


def find_task(task_id: int) -> Optional[Task]:
    return next((t for t in tasks if t.id == task_id), None)


# ---------- Root / Health ----------

@app.get("/")
def read_root():
    """Return basic API metadata."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health_check():
    """Return service health status."""
    return {"status": "ok"}


# ---------- Task Endpoints ----------

@app.get("/tasks", response_model=list[Task])
def list_tasks():
    """Return all tasks."""
    return tasks


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    """Return a single task by id. 404 if not found."""
    task = find_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(payload: TaskCreate):
    """Create a new task. 400 if title is missing or empty."""
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="title must not be empty")
    task = Task(id=get_next_id(), title=payload.title.strip(), done=payload.done)
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate):
    """Update title and/or done. 400 if body empty/invalid, 404 if not found."""
    if payload.title is None and payload.done is None:
        raise HTTPException(status_code=400, detail="request body must include title and/or done")

    task = find_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if payload.title is not None:
        task.title = payload.title.strip()
    if payload.done is not None:
        task.done = payload.done

    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task. 404 if not found. Returns empty body on success."""
    task = find_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    tasks.remove(task)
    return Response(status_code=204)


# ---------- Entrypoint ----------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)