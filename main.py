from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# In-memory "database" (Stage 2)
tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Learn FastAPI", "done": True},
    {"id": 3, "title": "Complete internship assignment", "done": False}
]

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
def get_tasks():
    """List all tasks in the database."""
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Get a single task by its ID."""
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.post("/tasks", status_code=201)
def create_task(task_in: TaskCreate):
    """Create a new task."""
    if not task_in.title or not task_in.title.strip():
        raise HTTPException(status_code=400, detail="Title is missing or empty")
    
    new_id = max((task["id"] for task in tasks), default=0) + 1
    new_task = {"id": new_id, "title": task_in.title, "done": False}
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_in: TaskUpdate):
    """Update an existing task."""
    if task_in.title is None and task_in.done is None:
        raise HTTPException(status_code=400, detail="Empty or invalid body")
    if task_in.title is not None and not task_in.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    for task in tasks:
        if task["id"] == task_id:
            if task_in.title is not None:
                task["title"] = task_in.title
            if task_in.done is not None:
                task["done"] = task_in.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task from the database."""
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            del tasks[index]
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")