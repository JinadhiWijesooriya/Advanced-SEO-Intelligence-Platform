# ---- Stage 1: Builder ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker cache layer)
COPY requirements.txt .

# Install Python dependencies into a prefix directory
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


# ---- Stage 2: Production Image ----
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Create directory for SQLite DB and report storage
RUN mkdir -p /app/storage/reports

# Expose the API port
EXPOSE 8000

# Default command: start Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
