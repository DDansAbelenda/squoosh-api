# Dockerfile for Railway - Without Chrome
FROM python:3.12-slim

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install basic system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create user before creating work directory
RUN adduser --disabled-password --gecos "" appuser

# Work directory
WORKDIR /app

# Change ownership of directory
RUN chown -R appuser:appuser /app

# Copy requirements as root first
COPY requirements.txt* ./

# Install Python dependencies (without selenium or webdriver-manager)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn[standard]==0.30.0 \
    pillow==10.4.0 \
    python-multipart==0.0.9

# Copy code and change ownership
COPY . .
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Start command with Railway PORT variable and memory options
CMD /usr/local/bin/python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1