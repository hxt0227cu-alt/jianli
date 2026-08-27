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

# Runtime dependencies (must stay in sync with apps/api/pyproject.toml [project].
# dependencies). httpx is a runtime dep since TASK-FEISHU-001; dev extras like
# pytest/ruff are intentionally excluded.
COPY pyproject.toml alembic.ini ./
RUN python -m pip install --upgrade pip && \
    python -m pip install \
        alembic==1.16.5 \
        bcrypt==5.0.0 \
        cryptography==46.0.7 \
        fastapi==0.141.1 \
        httpx==0.28.1 \
        psycopg==3.2.10 \
        python-multipart==0.0.20 \
        pypdf==6.15.0 \
        redis==8.1.0 \
        SQLAlchemy==2.0.43 \
        uvicorn==0.52.1 \
        pydantic==2.13.4 \
        prometheus-client==0.26.0 \
        opentelemetry-sdk==1.44.0 \
        opentelemetry-exporter-otlp-proto-http==1.44.0

# Application code + migrations (alembic.ini copied above).
COPY app ./app
COPY migrations ./migrations

# Non-root user for defense in depth (no write access to image layers).
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Default = API; worker overrides via compose command.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
