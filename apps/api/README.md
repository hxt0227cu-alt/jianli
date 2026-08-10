# Jianli API

This is a FastAPI project skeleton without business routes. API and Worker use
separate process entry points, and configuration reads only the documented
`JIANLI_*` environment variables.

## Local Run

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.lock
.venv\Scripts\python -m uvicorn app.main:app
```

The one-shot Worker smoke entry point records one structured startup event and exits:

```powershell
.venv\Scripts\python -m app.worker
```

Checks: `python -m pytest`, `python -m ruff check .`, `python -m ruff format --check .`,
and `python -m mypy app`.
