# Single image: FastAPI serves the API under /api and the built Angular app at /.
# Stage 1: build the frontend.
FROM node:22-bookworm-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
# npm 10 crashes resolving vitest 4's optional peers; npm 11 reads the lockfile cleanly.
RUN npm install -g npm@11 && npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npx ng build --configuration production

# Stage 2: the API, with the static build copied in.
FROM python:3.11-slim AS api
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY backend/pyproject.toml ./
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./
RUN pip install --no-cache-dir .
COPY --from=web /web/dist/frontend/browser /app/static
ENV HUB_STATIC_DIR=/app/static PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
