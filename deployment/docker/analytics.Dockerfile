# deployment/docker/analytics.Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    pandas matplotlib seaborn

# Copy application code
COPY microservices/analytics_service /app/microservices/analytics_service
COPY infrastructure /app/infrastructure

# Expose port
EXPOSE 8000

# Set Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Command to run on container start
CMD ["uvicorn", "microservices.analytics_service.main:app", "--host", "0.0.0.0", "--port", "8000"]