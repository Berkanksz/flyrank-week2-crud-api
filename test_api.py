"""Endpoint tests against the live API (docker compose stack or local server).

Run with:  python test_api.py
"""
import os
import httpx

BASE_URL = os.environ.get("API_URL", "http://localhost:8000")


def test_api():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    # 1. Health check
    r = client.get("/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("Health check OK:", r.json())

    # 2. Seeded tasks
    r = client.get("/tasks")
    assert r.status_code == 200
    tasks = r.json()
    assert len(tasks) >= 3
    print("GET /tasks OK, found tasks:", len(tasks))

    # 3. Read single
    r = client.get("/tasks/1")
    assert r.status_code == 200
    assert r.json()["id"] == 1

    # 4. Read not found
    assert client.get("/tasks/999999").status_code == 404

    # 5. Create
    r = client.post("/tasks", json={"title": "Test new task"})
    assert r.status_code == 201
    new_task = r.json()
    new_id = new_task["id"]
    assert new_task["title"] == "Test new task"
    assert new_task["done"] is False

    # Create validation errors
    assert client.post("/tasks", json={}).status_code == 400
    assert client.post("/tasks", json={"title": "   "}).status_code == 400

    # 6. Update
    r = client.put(f"/tasks/{new_id}", json={"done": True})
    assert r.status_code == 200
    assert r.json()["done"] is True

    # Update validation errors
    assert client.put(f"/tasks/{new_id}", json={}).status_code == 400
    assert client.put(f"/tasks/{new_id}", json={"title": ""}).status_code == 400
    assert client.put("/tasks/999999", json={"done": True}).status_code == 404

    # 7. Delete
    r = client.delete(f"/tasks/{new_id}")
    assert r.status_code == 204
    assert client.delete(f"/tasks/{new_id}").status_code == 404

    # 8. Stats
    r = client.get("/stats")
    assert r.status_code == 200
    stats = r.json()
    assert "total" in stats and "done" in stats and "open" in stats
    print("Stats OK:", stats)

    # 9. Extras: search, filter, sort
    assert len(client.get("/tasks", params={"search": "milk"}).json()) >= 1
    assert len(client.get("/tasks", params={"done": "true"}).json()) >= 1
    sorted_tasks = client.get("/tasks", params={"sort": "title"}).json()
    titles = [t["title"].lower() for t in sorted_tasks]
    assert titles == sorted(titles)

    print("All endpoint tests passed successfully!")


if __name__ == "__main__":
    test_api()
