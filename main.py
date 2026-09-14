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
    # Validate the input: return 400 Bad Request if title is missing or empty
    if not task_in.title or not task_in.title.strip():
        raise HTTPException(status_code=400, detail="Title is missing or empty")
    
    # Calculate the next free ID
    new_id = max((task["id"] for task in tasks), default=0) + 1
    
    # Create the new task dictionary
    new_task = {
        "id": new_id,
        "title": task_in.title,
        "done": False
    }
    
    # Add the new task to the in memory list
    tasks.append(new_task)
    
    # Return the created task (FastAPI automatically converts this to JSON)
    return new_task