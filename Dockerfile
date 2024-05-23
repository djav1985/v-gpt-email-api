# Use a slimmer Python image as base
FROM python:3.9-slim as base

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and clean up apt cache
RUN apt-get update && \
    apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy only the requirements file
COPY ./app/requirements.txt /app/

# Install Python dependencies with pip cache to speed up builds
RUN --mount=type=cache,target=/root/.cache/pip pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY ./app /app

# Expose port 8040 to the outside world
EXPOSE 8040

# Define environment variables
ENV WORKERS=2
ENV UVICORN_CONCURRENCY=32

# Set the command to run your FastAPI application with Uvicorn and environment variables
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8040 --workers $WORKERS --limit-concurrency $UVICORN_CONCURRENCY --timeout-keep-alive 32"]
