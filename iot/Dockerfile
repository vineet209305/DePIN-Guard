FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Switch to non-root user
USER appuser

# Note: IoT simulator runs continuously, sends data to backend
# No port exposed - this is a data producer, not a service
# No health check - simulator runs indefinitely

# Start the data ingestion simulator
CMD ["python", "-m", "data_ingestor"]
