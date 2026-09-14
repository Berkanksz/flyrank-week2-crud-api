from fastapi import FastAPI, HTTPException

app = FastAPI()

# In memory "database" (Stage 2)
tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Learn FastAPI", "done": True},
    {"id": 3, "title": "Complete internship assignment", "done": False}
]

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
    
    # Return 404 Not Found if the task does not exist
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")