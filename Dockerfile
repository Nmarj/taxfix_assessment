# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENDPOINT=persons

COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip &&\
pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

CMD ["python", "fakerapi/main.py"]