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
    PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application code from the builder stage
COPY . /app/

# Conditionally run development commands if DEBUG is true
# Default is true; can be overridden at build time
ARG DEBUG=true

RUN if [ "$DEBUG" = "true" ]; then \
        python manage.py collectstatic --noinput && \
        python manage.py makemigrations --noinput && \
        python manage.py migrate --noinput && \
        python manage.py shell -c "from manage import create_default_admin; create_default_admin()"; \
    fi

# Expose the port the application runs on
EXPOSE 8000

# Command to run the ASGI app with Uvicorn
CMD ["uvicorn", "B2B_Backend.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "3"]