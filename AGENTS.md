# AGENTS.md

## Cursor Cloud specific instructions

### Services Overview

This is a FastAPI-based community backend API. It requires **MySQL 8.0** as the sole database dependency.

- **FastAPI server**: `uvicorn main:app --reload` (port 8000)
- **MySQL**: must be running on 127.0.0.1:3306

### Starting the dev server

```bash
sudo service mysql start
cd /workspace && uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The `.env` file at project root configures DB credentials and app settings. The dev environment uses:
- DB user: `community`, DB name: `community`, host: `127.0.0.1`
- `DEBUG=True` enables the test router at `/v1/test/`

### Known issues

- **pytest tests (`test/test_api.py`)**: All 12 tests fail due to a pre-existing bug in `utils/test/test_utils.py` where `seed_database()` calls async model methods (`execute`, `user_model.clear()`, `user_model.createUser()`) without `await`. This is a repo-level issue, not an environment problem.
- **Missing `routers/test_router.py`**: The file was referenced in `routers/__init__.py` but did not exist in the repo. A minimal stub was created to allow the app to start.

### Testing

- Use `scripts/qa-smoke.sh http://localhost:8000` for end-to-end smoke testing (health, signup, login, CRUD for posts/comments, logout). This is the reliable integration test.
- Swagger UI is available at `http://localhost:8000/docs`.
- No linter is configured in the project (`pyproject.toml` has no lint tool dependencies).

### Environment details

- Python 3.12.3 (system), packages installed to `~/.local` via `pip install -e .`
- `~/.local/bin` must be on `PATH` for `uvicorn`, `pytest`, etc.
- DB schema is at `db/schema.sql`; seed data at `db/seed.sql`.
