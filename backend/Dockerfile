FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini ./

# Copy database utilities (seed script)
# Note: seed_data.py is in the database/ directory one level up,
# passed via build context. The docker-compose build context is ../backend
# so seed_data.py is added separately via the compose file or run manually.
# See seed instructions below.

# Expose the FastAPI port
EXPOSE 8000

# Run migrations on startup, then start the server.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
