# Build stage
FROM python:3.10-slim as builder

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app

# Install Python dependencies in a virtual environment
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv /app/venv && \
    . /app/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

# Final stage
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/venv /app/venv

# Copy the rest of the application
COPY ./app /app

# Expose port 8888 to the outside world
EXPOSE 8888

# Define environment variables
ENV WORKERS=2
ENV UVICORN_CONCURRENCY=32
ENV PATH="/app/venv/bin:$PATH"

# Set the command to run your FastAPI application with Uvicorn and environment variables
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8888", "--workers", "$WORKERS", "--limit-concurrency", "$UVICORN_CONCURRENCY", "--timeout-keep-alive", "32"]
