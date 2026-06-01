# Multi-stage build: slim runtime image for FitTrack API
# Stage 1: builder
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build deps
COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --upgrade pip \
 && pip install --no-cache-dir build \
 && python -m build --wheel

# Stage 2: runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

# Security: run as non-root
RUN groupadd -r fittrack && useradd -r -g fittrack fittrack

# Install the wheel and runtime deps only
COPY --from=builder /build/dist/*.whl /tmp/
COPY pyproject.toml README.md ./

RUN pip install --upgrade pip \
 && pip install --no-cache-dir /tmp/*.whl \
 && rm /tmp/*.whl

# Copy static assets
COPY static/ static/

USER fittrack

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"

CMD ["uvicorn", "fittrack.main:app", "--host", "0.0.0.0", "--port", "8000"]
