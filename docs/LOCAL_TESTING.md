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

### 7. Test UI

Open browser: http://localhost:8501

### 8. Stop Services

```bash
cd deployment
docker compose down
```

## Expected Output (Local Mode)

```
================================================================
  🐳 EcoSight Local Docker Testing
================================================================

✓ Docker is running

📂 Test Mode: LOCAL ONLY (uses local extracted_audio/)

✓ Found 1234 audio files in extracted_audio/

✓ Cleaned up old containers

================================================================
Step 1: Building Docker containers...
================================================================
...
✓ Containers built successfully

================================================================
Step 2: Starting services...
================================================================
...
✓ Services started
✓ API is ready

================================================================
Step 3: Testing Retraining Pipeline
================================================================

This will:
  1. Use local extracted_audio/
  2. Apply augmentation (creates augmented_audio)
  3. Train model on augmented data
  4. Save model to models/

Running retrain script in container...

======================================================================
DOWNLOADING AND AUGMENTING TRAINING DATA
======================================================================
📦 Bucket: ecosight-training-data
📥 Downloading to: /app/extracted_audio
🎵 Augmenting to: /app/augmented_audio

ℹ️  S3 credentials not set, using local training data

Step 2: Applying audio augmentation...
  This creates multiple variants of each audio file
  Augmentations: pitch shift, time stretch, noise, volume, etc.

Augmentation Results:
----------------------------------------------------------------------
  dog_bark: 100 → 600 files (6.0x)
  gun_shot: 50 → 300 files (6.0x)
  engine_idling: 75 → 450 files (6.0x)
----------------------------------------------------------------------
✓ Total augmented files: 1350

======================================================================
EXTRACTING YAMNET EMBEDDINGS
======================================================================
...
✓ Extracted 1350 embeddings

======================================================================
TRAINING CLASSIFIER
======================================================================
Epoch 1/100
...
✓ TRAINING COMPLETE!

✓ Retraining completed

================================================================
Step 4: Checking Results
================================================================

✓ Model created: yamnet_classifier.keras (2.3M)
✓ Augmented audio: 1350 files (1.2G)

================================================================
Step 5: Testing API Endpoints
================================================================

Testing /status endpoint...
Response: {"status":"healthy","model_loaded":true}

Testing /classes endpoint...
Response: {"classes":["dog_bark","gun_shot","engine_idling"]}

================================================================
✅ LOCAL TESTING COMPLETE
================================================================

Services running:
  • API:        http://localhost:8000
  • UI:         http://localhost:8501
  • Nginx:      http://localhost:80

Test the UI:
  Open browser: http://localhost:8501

View logs:
  docker compose -f deployment/docker-compose.yml logs -f api

Stop services:
  docker compose -f deployment/docker-compose.yml down
```

## Troubleshooting

### Docker Not Running

```bash
# Start Docker Desktop
open -a Docker

# Wait for it to start, then verify
docker info
```

### extracted_audio Not Found

```bash
# Check if folder exists
ls -la | grep extracted

# If missing, you need your audio files first
# OR test with S3 mode: ./scripts/test-docker-local.sh --with-s3
```

### S3 Credentials Error

```bash
# Check .env file
cat .env

# Verify credentials are set (not empty)
grep AWS_ACCESS_KEY_ID .env

# Test AWS CLI
aws s3 ls s3://ecosight-training-data/
```

### Container Build Fails

```bash
# Clean up and rebuild
docker compose -f deployment/docker-compose.yml down
docker system prune -f
docker compose -f deployment/docker-compose.yml build --no-cache
```

### Out of Memory

```bash
# Check Docker memory settings
# Docker Desktop → Preferences → Resources → Memory
# Increase to at least 4GB

# Or reduce augmentation in retrain_model.py:
# augmentations_per_file=3  # instead of 5
```

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Stop conflicting process or change port in docker-compose.yml
```

## Cleanup

### Remove Containers

```bash
cd deployment
docker compose down
```

### Remove Images

```bash
docker rmi ecosight-api ecosight-ui
```

### Remove Volumes

```bash
docker volume prune
```

### Clean Everything

```bash
# Stop containers
docker compose -f deployment/docker-compose.yml down

# Remove all EcoSight images
docker images | grep ecosight | awk '{print $3}' | xargs docker rmi

# Clean system
docker system prune -a
```

## Next Steps After Successful Local Test

1. ✅ Verify model works locally
2. ✅ Test predictions via UI
3. ✅ Commit changes to git
4. ✅ Push to GitHub
5. ✅ Deploy to Render (will auto-deploy from GitHub)

## Files Created/Modified

| File | Purpose |
|------|---------|
| `scripts/test-docker-local.sh` | Automated test script |
| `.env.example` | Environment variables template |
| `deployment/docker-compose.yml` | Updated with S3 vars + extracted_audio volume |

---

**Quick Commands:**

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
