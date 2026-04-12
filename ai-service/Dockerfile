FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Switch to non-root user
USER appuser

# Expose port (will be overridden by PORT env var in Render)
EXPOSE 5000

# Health check - verify Flask app is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Start Flask app directly (Render sets PORT env var)
CMD ["python", "app.py"]
