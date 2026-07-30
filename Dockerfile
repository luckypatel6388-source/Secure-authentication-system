# 1. Base Image: Use official lightweight Python image
FROM python:3.11-slim

# 2. Environment Configurations
# Prevents Python from writing .pyc files & keeps logs unbuffered (shows instantly in terminal)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set Working Directory inside the container
WORKDIR /app

# 4. Install System Dependencies (Needed for MySQL / C extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy requirements first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# 6. Install Python packages
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 7. Copy application code into container
COPY . /app/

# 8. Expose Web Port
EXPOSE 10000

# 9. Startup Command to launch FastAPI app using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]