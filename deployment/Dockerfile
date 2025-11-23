# Dockerfile for EcoSight Wildlife Monitoring API
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY config/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy API code and dependencies
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY deployment/start.sh ./start.sh

# Make startup script executable
RUN chmod +x ./start.sh

# Create necessary directories (model will be downloaded from S3 on startup)
RUN mkdir -p uploads augmented_audio extracted_audio models

# Expose port (Railway will override with PORT env var)
EXPOSE 8000

# Health check with dynamic port support
HEALTHCHECK --interval=30s --timeout=30s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request, os; urllib.request.urlopen(f'http://localhost:{os.getenv(\"PORT\", \"8000\")}/status')" || exit 1

# Run the API using startup script that handles PORT env var
CMD ["./start.sh"]
