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

# Create necessary directories (model will be downloaded from S3 on startup)
RUN mkdir -p uploads augmented_audio extracted_audio models

# Expose port
EXPOSE 8000

# Health check with longer timeout for model loading
HEALTHCHECK --interval=30s --timeout=30s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/status')" || exit 1

# Run the API with increased timeout
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300"]
