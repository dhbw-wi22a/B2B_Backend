# Stage 1: Build Dependencies
FROM python:3.10-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies for building packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Stage 2: Final Runtime Image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=${DJANGO_PREPARE_DB:-true} \
    DJANGO_CREATE_DEFAULT_ADMIN=${DJANGO_CREATE_DEFAULT_ADMIN:-true} \
    DJANGO_APP_HOST=${DJANGO_APP_HOST:-0.0.0.0}\
    DJANGO_WORKERS=${DJANGO_WORKERS:-3}

# Set the working directory inside the container
WORKDIR /app

# Copy installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application code from the builder stage
COPY . /app/

# Conditionally run development commands if DJANGO_PREPARE_DB is true
RUN if [ "DJANGO_PREPARE_DB" = "true" ]; then \
        python manage.py collectstatic --noinput && \
        python manage.py makemigrations --noinput && \
        python manage.py migrate --noinput && \
        if [ "$DJANGO_CREATE_DEFAULT_ADMIN" = "true" ]; then \
            python manage.py shell -c "from manage import create_default_admin; create_default_admin()"; \
        fi; \
    fi

# Expose the port the application runs on
EXPOSE 8000

# Command to run the ASGI app with Uvicorn
CMD ["sh", "-c", "uvicorn B2B_Backend.asgi:application --host 0.0.0.0 --port 8000 --workers ${DJANGO_WORKERS}"]
