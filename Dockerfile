# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install dependencies into a local prefix so we can copy them cleanly
COPY app/requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install -r requirements.txt

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim

# Security: run as non-root
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY app/ .

# Correct ownership
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

# Use gunicorn for production; 2 workers × 2 threads is a safe baseline
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--timeout", "60", "app:app"]
