# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY job_scraper.py .
COPY config.yaml .

# Create volume mount points for persistence
VOLUME ["/app/data"]

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sqlite3; conn = sqlite3.connect('jobs.db'); conn.close()" || exit 1

# Run the scraper
CMD ["python", "job_scraper.py"]
