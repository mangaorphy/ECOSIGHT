# 🧪 Local Docker Testing Guide

## Quick Start

### Option 1: Test WITHOUT S3 (Local Data Only)

Uses your local `extracted_audio/` folder:

```bash
./scripts/test-docker-local.sh
```

### Option 2: Test WITH S3 (Cloud Data)

Downloads from S3 and tests complete pipeline:

```bash
./scripts/test-docker-local.sh --with-s3
```

## What Gets Tested

The test script will:

1. ✅ **Build Docker containers** (API, UI, Nginx)
2. ✅ **Start all services**
3. ✅ **Run retraining pipeline**:
   - Download extracted_audio (from S3 or use local)
   - Apply augmentation → creates augmented_audio
   - Train model on augmented data
   - Save model to models/
4. ✅ **Verify model created**
5. ✅ **Test API endpoints**

## Prerequisites

### For Local Testing (No S3):

```bash
# 1. Check Docker is running
docker info

# 2. Check extracted_audio exists
ls -la extracted_audio/

# 3. Verify audio files present
find extracted_audio -name "*.wav" -o -name "*.mp3" | head
```

### For S3 Testing:

```bash
# 1. Create .env file from example
cp .env.example .env

# 2. Edit .env and add your AWS credentials:
nano .env

# Add:
# AWS_ACCESS_KEY_ID=your-key-here
# AWS_SECRET_ACCESS_KEY=your-secret-here

# 3. Test S3 access
aws s3 ls s3://ecosight-training-data/extracted_audio/
```

## Step-by-Step Manual Testing

If you prefer to test manually:

### 1. Build Containers

```bash
cd deployment
docker compose build
```

### 2. Start Services

```bash
docker compose up -d
```

### 3. Check Logs

```bash
# API logs
docker compose logs -f api

# UI logs
docker compose logs -f ui

# All logs
docker compose logs -f
```

### 4. Test Retraining (Inside Container)

```bash
# Enter API container
docker exec -it ecosight-api-1 bash

# Inside container, run retraining
python /app/scripts/retrain_model.py

# Exit container
exit
```

### 5. Verify Results

```bash
# Check model created
ls -lh models/yamnet_classifier.keras

# Check augmented audio
ls -la augmented_audio/

# Count augmented files
find augmented_audio -name "*.wav" | wc -l
```

### 6. Test API

```bash
# Check status
curl http://localhost:8000/status

# Get classes
curl http://localhost:8000/classes

# Test prediction (replace with actual file path)
curl -X POST http://localhost:8000/predict \
  -F "file=@path/to/audio.wav"
```

```bash
# Local test (no S3)
./scripts/test-docker-local.sh

# S3 test
./scripts/test-docker-local.sh --with-s3

# View logs
docker compose -f deployment/docker-compose.yml logs -f api

# Stop
docker compose -f deployment/docker-compose.yml down
```
