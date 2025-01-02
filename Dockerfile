# Stage 1: Build Dependencies
FROM python:3.10-slim AS builder

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
    DJANGO_PREPARE_DB=1 \
    DJANGO_CREATE_DEFAULT_ADMIN=1 \
    DJANGO_WORKERS=3

# Set the working directory inside the container
WORKDIR /app

# Copy installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application code from the builder stage
COPY . /app/

# Create the required directories with permissions
RUN mkdir -p /app/data/db /app/data/media /app/data/static
# Create necessary log directory
RUN mkdir -p /app/log


# Conditionally run database setup and collectstatic
RUN if [ $DJANGO_PREPARE_DB = 1 ]; then \
        echo "Starting static files collection..." && \
        python manage.py collectstatic --noinput && \
        echo "Static files collected successfully." && \
        echo "Starting database migrations..." && \
        python manage.py makemigrations --noinput && \
        echo "Migrations created successfully." && \
        python manage.py migrate --noinput && \
        echo "Database migrations applied successfully." && \
        if [ $DJANGO_CREATE_DEFAULT_ADMIN = 1 ]; then \
            echo "Creating default admin user..." && \
            python manage.py shell -c "from manage import create_default_admin; create_default_admin()" && \
            echo "Default admin created successfully."; \
        fi; \
    else \
        echo "Database preparation is disabled. Skipping migrations and static file collection."; \
    fi


# Expose the port the application runs on
EXPOSE 8000

# Command to run the ASGI app with Uvicorn
CMD ["sh", "-c", "uvicorn B2B_Backend.asgi:application --host 0.0.0.0 --port 8000 --workers ${DJANGO_WORKERS}"]
