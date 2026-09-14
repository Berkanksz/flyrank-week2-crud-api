# FlyRank Backend Internship - Week 2: First CRUD API

This is a RESTful API built with **Python 3.10** and **FastAPI** that manages a simple in-memory to-do list. It supports the full CRUD (Create, Read, Update, Delete) cycle and includes automatic interactive documentation via Swagger UI.

## How to Install and Run
1. Ensure you have Python installed.
2. Install the required packages: `pip install fastapi uvicorn`
3. Start the server on localhost:
```bash
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000`.

## API Endpoints
| CRUD Operation | HTTP Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **-** | GET | `/` | Returns API metadata |
| **-** | GET | `/health` | Returns server health status |
| **Read** | GET | `/tasks` | Lists all tasks |
| **Read** | GET | `/tasks/{task_id}` | Gets a specific task by ID |
| **Create** | POST | `/tasks` | Creates a new task |
| **Update** | PUT | `/tasks/{task_id}` | Updates an existing task |
| **Delete** | DELETE | `/tasks/{task_id}` | Deletes a task |
| **Extra** | GET | `/stats` | Returns task statistics |

## Example `curl` Output (GET /tasks/1)
```bash
$ curl -i http://localhost:8000/tasks/1
HTTP/1.1 200 OK
date: Mon, 14 Sep 2026 09:37:46 GMT
server: uvicorn
content-length: 62
content-type: application/json

{"id":1,"title":"Buy milk","done":false}
```

## Swagger UI Screenshot
Interactive documentation is available at `http://localhost:8000/docs`.
![Swagger UI](Screenshots/Fastapi.png)