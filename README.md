# Resume Vacancy AI Agent

Production-style FastAPI application for matching resumes with job vacancies and generating
grounded resume improvement recommendations.

This repository is currently initialized with the service skeleton only. Complex LLM, RAG,
document parsing, matching, and evaluation logic are intentionally left as placeholders.

## Current Scope

- FastAPI app factory and entrypoint
- Health endpoint
- Pydantic v2 schemas for resumes, vacancies, extraction, and reports
- Placeholder service modules for parsing, extraction, matching, RAG, agents, generation, and evaluation
- PostgreSQL and Qdrant Docker Compose services
- Pytest smoke tests
- Ruff, mypy, and pytest configuration

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
copy .env.example .env
```

## Run the API

```powershell
uvicorn app.main:app --reload
```

The root, docs, and health endpoints are available at:

```text
GET http://127.0.0.1:8000/
GET http://127.0.0.1:8000/docs
GET http://127.0.0.1:8000/health
```

## Run with Docker

Build and start the API, PostgreSQL, and Qdrant locally:

```powershell
docker compose up --build
```

The API container runs:

```text
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Check the API endpoints:

```powershell
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health
```

Open the interactive API docs at:

```text
http://127.0.0.1:8000/docs
```

PostgreSQL and Qdrant are included for end-to-end local development. The current test suite does
not require either service to be available.

To stop the stack:

```powershell
docker compose down
```

## Run Infrastructure Only

```powershell
docker compose up -d postgres qdrant
```

## Quality Checks

```powershell
ruff check .
pytest
mypy src/app
```
