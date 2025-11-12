# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/chromadb data/drafts data/metrics data/profiles

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Start command (Railway will override with railway.json if present)
CMD uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
