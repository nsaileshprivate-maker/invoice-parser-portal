FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL application files (FIXED!)
COPY . .

# Create necessary directories
RUN mkdir -p uploads

# Expose port for Gunicorn (Railway uses 8000)
EXPOSE 8000

# Health check (FIXED to use port 8000)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000')"

# Run with Gunicorn (better for production)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]