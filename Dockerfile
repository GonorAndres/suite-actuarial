# Stage 1: Build Next.js frontend
FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
ARG NEXT_PUBLIC_API_URL=/api/v1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# Stage 2: Python backend + static frontend
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/
COPY data/ data/

RUN pip install --no-cache-dir -e ".[api]"

# Copy built frontend
COPY --from=frontend-build /app/frontend/.next/standalone ./frontend-standalone
COPY --from=frontend-build /app/frontend/.next/static ./frontend-standalone/.next/static
COPY --from=frontend-build /app/frontend/public ./frontend-standalone/public

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "uvicorn", "suite_actuarial.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
