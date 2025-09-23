# Repository Guidelines

## Project Structure & Module Organization
The FastAPI application lives under `app/`. `app/main.py` exposes the ASGI `app` object and route definitions; keep new routers in subpackages like `app/routers/` and import them from `main.py`. Shared schemas should reside in `app/schemas/`, and business logic in `app/services/`. Runtime configuration is loaded via `python-dotenv`; store environment defaults in `.env.example`. Place automated tests under `tests/`, mirroring the package layout, e.g., `tests/test_health.py`.

## Build, Test, and Development Commands
Create an isolated environment before installing dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
Run the development server with hot reload using `uvicorn app.main:app --reload`. Validate the health endpoint locally with `curl http://127.0.0.1:8000/health`. Execute the test suite using `pytest` (install via `pip install pytest` if missing). Use `uvicorn app.main:app --host 0.0.0.0 --port 8000` for container-friendly runs.

## Coding Style & Naming Conventions
Adhere to PEP 8 with 4-space indentation. Use type hints on all public functions and pydantic models for request/response validation. Name modules and functions with `snake_case`, classes with `PascalCase`, and environment variables in `UPPER_SNAKE_CASE`. Keep FastAPI route handlers thin; delegate work to service modules.

## Testing Guidelines
Write tests with `pytest` and FastAPI's `TestClient`. Mirror module names (`tests/test_<module>.py`) and cover new endpoints and error paths. Use fixtures for sample data and prefer explicit assertions over broad status checks. Aim for unit tests on services plus integration checks for the HTTP layer.

## Commit & Pull Request Guidelines
Write imperative commit messages (`Add health check`) and keep changes scoped. Reference issues in the body using `Refs #123` when applicable. Pull requests should include a summary of behavior changes, manual verification notes (e.g., curl output), and screenshots for any API docs or schema changes. Request review once CI passes and merge only after at least one approval.

## Environment & Configuration
Document required variables in `.env.example`, and never commit secrets. Use `python-dotenv` to load configuration in development; production deployments should rely on real environment variables. Keep default ports and hosts configurable, especially when deploying to containers or cloud runtimes.
