# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_LOG_LEVEL=INFO \
    PYTHONPATH=/app

# Create and set the working directory
WORKDIR /app

# Install system dependencies (needed for confluent-kafka build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure logs directory exists with appropriate permissions
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Run the main.py script
CMD ["python", "main.py"]
