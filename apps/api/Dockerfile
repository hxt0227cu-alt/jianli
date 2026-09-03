# TASK-DEPLOY-001: API + Worker shared image (python:3.12-slim).
# Entry point is chosen at runtime via compose `command`:
#   api:    uvicorn app.main:app --host 0.0.0.0 --port 8000
#   worker: python -m app.worker
# Business code is never modified for deployment; secrets come from the runtime
# environment (server .env), never baked into the image.
#
# Note: pyproject.toml has NO [build-system] section, so `pip install .` is not
# reliable here. We install the exact runtime dependency list explicitly and run
# the app from the workdir (app/ on sys.path) — same behavior, no packaging step.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv/jianli

# psycopg's non-binary production installation dynamically links libpq.
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Install the exact production dependency closure. ``--no-deps`` prevents pip
# from resolving a newer transitive version behind the lock; ``pip check`` then
# proves that the handoff image contains a complete compatible runtime graph.
# Dev-only pytest/ruff/mypy packages are intentionally excluded.
COPY pyproject.toml requirements.runtime.lock alembic.ini ./
RUN python -m pip install --no-deps -r requirements.runtime.lock && \
    python -m pip check

# Application code + migrations (alembic.ini copied above).
COPY app ./app
COPY migrations ./migrations
COPY scripts/seed_kb.py ./scripts/seed_kb.py

# Non-root user for defense in depth. The init container applies the same ownership
# to a brand-new named volume before API/Worker startup.
RUN useradd --create-home --uid 10001 --user-group appuser && \
    install -d -o appuser -g appuser -m 0700 /srv/jianli/var/knowledge
USER appuser

EXPOSE 8000

# Default = API; worker overrides via compose command.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
