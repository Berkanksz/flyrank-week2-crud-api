-- Stage 4: SQL I ran by hand against tasks.db (DB Browser "Execute SQL" tab / sqlite3 CLI)
-- The API was running the whole time. After every query that changed data,
-- GET /tasks showed the change instantly, with no server restart.

-- 1. List every task -> 3 rows: Buy milk (0), Learn FastAPI (1), Complete internship assignment (0)
SELECT * FROM tasks;

-- 2. Only completed tasks -> 1 row: id 2, "Learn FastAPI"
SELECT * FROM tasks WHERE done = 1;

-- 3. How many tasks are there? -> 3
SELECT COUNT(*) FROM tasks;

-- 4. Mark every task completed -> GET /tasks now returns all three with "done": true
UPDATE tasks SET done = 1;

-- 5. Delete all completed tasks -> GET /tasks now returns []
DELETE FROM tasks WHERE done = 1;

-- Reset: delete tasks.db and restart the server. The table and the 3 seed tasks come back automatically.
