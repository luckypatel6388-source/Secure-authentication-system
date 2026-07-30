# 1. Base Image: Official lightweight Python image
FROM python:3.11-slim

# 2. Environment Configurations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set Working Directory
WORKDIR /app

# 4. Install System Dependencies (Replaced MySQL with Postgres libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy requirements first for Docker layer caching
COPY requirements.txt /app/requirements.txt

# 6. Install Python packages
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 7. Copy application code into container
COPY . /app/

# 8. Expose Web Port
EXPOSE 10000

# 9. Startup Command for FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]