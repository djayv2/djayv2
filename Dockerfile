# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app/

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN uv pip install --system -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Execute Driver
CMD ["python", "./main_driver.py"]