from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# In-memory "database" (Stage 2)
tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Learn FastAPI", "done": True},
    {"id": 3, "title": "Complete internship assignment", "done": False}
]

# Model for incoming POST request body (Stage 3)
class TaskCreate(BaseModel):
    title: str | None = None

# Model for incoming PUT request body (Stage 4)
class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

# Root endpoint
@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Endpoint to list all tasks
@app.get("/tasks")
def get_tasks():
    return tasks

# Endpoint to get a single task by its ID
@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

# Endpoint to create a new task
@app.post("/tasks", status_code=201)
def create_task(task_in: TaskCreate):
    if not task_in.title or not task_in.title.strip():
        raise HTTPException(status_code=400, detail="Title is missing or empty")
    
    new_id = max((task["id"] for task in tasks), default=0) + 1
    new_task = {"id": new_id, "title": task_in.title, "done": False}
    tasks.append(new_task)
    return new_task

# Endpoint to update an existing task
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_in: TaskUpdate):
    # Validate the input: return 400 Bad Request if body is empty or invalid
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
            
    # Return 404 Not Found if the task does not exist
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

# Endpoint to delete a task
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            del tasks[index]
            return # Returns 204 No Content with an empty body
            
    # Return 404 Not Found if the task does not exist
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")