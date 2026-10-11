"""Endpoint tests: the same checks used for the A1 in-memory API, run against SQLite.

Run with:  python test_api.py
Uses a temporary database file, so your real tasks.db is never touched.
"""
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

import main


def fresh_client(db_path: Path) -> TestClient:
    main.DB_PATH = db_path
    return TestClient(main.app)


def test_a1_contract(client: TestClient):
    # Read
    r = client.get("/tasks")
    assert r.status_code == 200
    assert r.json() == [
        {"id": 1, "title": "Buy milk", "done": False},
        {"id": 2, "title": "Learn FastAPI", "done": True},
        {"id": 3, "title": "Complete internship assignment", "done": False},
    ]
    assert client.get("/tasks/1").json() == {"id": 1, "title": "Buy milk", "done": False}
    assert client.get("/tasks/999").status_code == 404

    # Create
    r = client.post("/tasks", json={"title": "Write tests"})
    assert r.status_code == 201
    assert r.json() == {"id": 4, "title": "Write tests", "done": False}
    assert client.post("/tasks", json={}).status_code == 400
    assert client.post("/tasks", json={"title": "   "}).status_code == 400

    # Update
    r = client.put("/tasks/4", json={"done": True})
    assert r.status_code == 200
    assert r.json() == {"id": 4, "title": "Write tests", "done": True}
    assert client.put("/tasks/4", json={}).status_code == 400
    assert client.put("/tasks/4", json={"title": ""}).status_code == 400
    assert client.put("/tasks/999", json={"done": True}).status_code == 404

    # Delete
    r = client.delete("/tasks/4")
    assert r.status_code == 204
    assert r.content == b""
    assert client.delete("/tasks/4").status_code == 404

    # Stats
    assert client.get("/stats").json() == {"total": 3, "done": 1, "open": 2}


def test_extras(client: TestClient):
    assert [t["id"] for t in client.get("/tasks", params={"search": "milk"}).json()] == [1]
    assert [t["id"] for t in client.get("/tasks", params={"done": "true"}).json()] == [2]
    titles = [t["title"] for t in client.get("/tasks", params={"sort": "title"}).json()]
    assert titles == sorted(titles, key=str.lower)
    assert client.get("/tasks", params={"sort": "bogus"}).status_code == 400
    # SQL injection attempt is treated as plain text, not as SQL
    assert client.get("/tasks", params={"search": "' OR 1=1 --"}).json() == []


def test_persistence_and_seed_once(db_path: Path):
    with fresh_client(db_path) as client:
        client.post("/tasks", json={"title": "Survive restart"})
    # "Restart": a brand-new app startup on the same file
    with fresh_client(db_path) as client:
        tasks = client.get("/tasks").json()
    assert len(tasks) == 4, "seed must not run again and the new task must survive"
    assert tasks[-1]["title"] == "Survive restart"


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        with fresh_client(Path(tmp) / "a1.db") as c:
            test_a1_contract(c)
        with fresh_client(Path(tmp) / "extras.db") as c:
            test_extras(c)
        test_persistence_and_seed_once(Path(tmp) / "restart.db")
    print("All tests passed")
