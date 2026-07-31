FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_RELEASE_LAB_DB=/data/model-release-lab.db \
    PATH=/app/.venv/bin:$PATH
WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir /data && chown app:app /data
COPY --from=ghcr.io/astral-sh/uv:0.11.28 /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
COPY --from=frontend /app/frontend/dist ./frontend/dist
RUN uv sync --frozen --no-dev --no-editable
USER app
EXPOSE 8000
CMD ["sh", "-c", "uvicorn model_release_lab.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
