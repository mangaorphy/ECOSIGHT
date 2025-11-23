# EcoSight Wildlife Monitoring - Render Deployment Guide

## Overview
This guide walks you through deploying EcoSight to Render with both API and UI services, including S3 integration for automatic audio storage and retraining.

## 🎯 Key Features
- ✅ **Automatic S3 Upload**: All uploaded audio files are automatically saved to S3
- ✅ **Cloud-Based Retraining**: Downloads originals from S3, applies augmentation, trains model
- ✅ **Cost-Efficient Storage**: Stores only originals (~$0.04/month), generates augmented files on-demand
- ✅ **Persistent Model Storage**: Trained models persist across deployments

## Prerequisites
- GitHub account with EcoSight repository pushed
- Render account (free tier works)
- Your model files committed to the repository

## Deployment Steps

### 1. Prepare Your Repository

Ensure these files are committed:
```bash
git add render.yaml deployment/Dockerfile deployment/Dockerfile.streamlit
git add models/yamnet_classifier_v2.keras models/class_names.json models/model_metadata.json
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. Connect to Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Select the repository containing EcoSight
5. Render will detect `render.yaml` automatically

### 3. Configure Services

Render will create two services from `render.yaml`:

**ecosight-api** (FastAPI Backend)
- Runtime: Docker
- Region: Oregon (change in render.yaml if needed)
- Plan: Starter ($7/month) or Free
- Disk: 10GB persistent storage
- Health check: `/status`

**ecosight-ui** (Streamlit Dashboard)
- Runtime: Docker
- Region: Oregon
- Plan: Starter ($7/month) or Free
- Health check: `/_stcore/health`
- Auto-connected to API service

### 4. Environment Variables

**Required for S3 Integration:**

Add these in Render Dashboard → Service → Environment:

```bash
S3_BUCKET=ecosight-training-data
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
AWS_REGION=us-east-1
```

**Auto-configured by render.yaml:**
- `API_URL`: Auto-linked from ecosight-api service
- `PORT`: 8000 (API), 8501 (UI)
- `PYTHONUNBUFFERED`: 1
- Streamlit server configs

**Optional:**
```bash
MIN_NEW_SAMPLES=100  # Minimum samples before retraining
LOG_LEVEL=INFO       # Logging verbosity
```

### 5. Deploy

1. Click **"Apply"** to create both services
2. Render will:
   - Build Docker images
   - Deploy API service
   - Deploy UI service
   - Link services together

**Build time**: ~5-10 minutes per service

### 6. Access Your Application

After deployment completes:
- **API**: `https://ecosight-api.onrender.com`
- **UI**: `https://ecosight-ui.onrender.com`

Test the API:
```bash
curl https://ecosight-api.onrender.com/status
```

## Monitoring

### View Logs
1. Go to Render Dashboard
2. Click on service (ecosight-api or ecosight-ui)
3. Navigate to **"Logs"** tab

### Health Checks
Render automatically monitors:
- API: `GET /status` every 30s
- UI: `GET /_stcore/health` every 30s

## How Audio Upload Works on Render

### Upload Flow
1. **User uploads audio** via UI `/upload` endpoint
2. **API saves locally** to `extracted_audio/<class>/`
3. **API uploads to S3** `s3://ecosight-training-data/extracted_audio/<class>/`
4. **Returns success** with S3 upload confirmation

### Example Response
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file_path": "/app/extracted_audio/gun_shot/20251123_165432_shot.wav",
  "class": "gun_shot",
  "s3_uploaded": true,
  "timestamp": "2025-11-23T16:54:32"
}
```

### Storage Architecture

| Location | Content | Persistent? | Purpose |
|----------|---------|-------------|---------|
| `extracted_audio/` (Render) | Original uploads | ❌ Ephemeral | Temporary local copy |
| `s3://bucket/extracted_audio/` | Original uploads | ✅ Permanent | Source of truth |
| `augmented_audio/` (Render) | Generated during retraining | ❌ Temporary | Training data |
| `models/` (Render) | Trained model | ✅ Persistent disk | Active model |

### Why S3?
- ✅ **Permanent storage**: Files persist even if Render restarts
- ✅ **Cost-efficient**: ~$0.04/month for 1.7GB (vs ephemeral Render storage)
- ✅ **Retraining source**: Model downloads originals from S3
- ✅ **Automatic backup**: All uploads backed up in cloud

## Retraining on Render

### Trigger Retraining
```bash
curl -X POST "https://ecosight-api.onrender.com/retrain" \
  -H "Content-Type: application/json" \
  -d '{"min_samples": 100}'
```

### Retraining Process
1. **Download from S3**: `s3://bucket/extracted_audio/` → `/app/extracted_audio/`
2. **Apply augmentation**: 1 file → 6 files (1 original + 5 variants)
3. **Train model**: YAMNet embeddings → Classifier
4. **Save model**: `/app/models/yamnet_classifier.keras`
5. **Cleanup**: Delete augmented files (save disk space)

### Expected Timeline
- Download from S3: ~2-5 min (for 3500 files)
- Augmentation: ~5-10 min (3500 → 21000 files)
- Training: ~10-20 min (depends on data size)
- **Total**: ~20-30 minutes

### Monitoring Retraining
Check logs for:
```
✓ Retraining started
✓ Downloaded 3500 files from S3
✓ Applied augmentation: 3500 → 21000 files
✓ Extracting YAMNet embeddings...
✓ Training classifier...
✓ Model training complete
✓ Model saved to /app/models/yamnet_classifier.keras
```

## Persistent Storage

The API service includes a 10GB disk for:
- Uploaded audio files (`/app/uploads`)
- Augmented audio (`/app/augmented_audio`)
- Model files (`/app/models`)

**Note**: Free tier doesn't include persistent disks. Upgrade to Starter plan for storage.

## Updating Your Deployment

### Auto-Deploy (Enabled by default)
Push to main branch:
```bash
git add .
git commit -m "Update model/code"
git push origin main
```
Render auto-deploys within minutes.

### Manual Deploy
1. Go to service in Render Dashboard
2. Click **"Manual Deploy"** → **"Deploy latest commit"**

## Troubleshooting

### Build Fails
- Check Render build logs
- Verify all files are committed (models/, config/, src/)
- Ensure requirements.txt is complete

### API/UI Can't Connect
- Check environment variables in Render Dashboard
- Verify `API_URL` is set correctly in ecosight-ui
- Check service logs for connection errors

### Out of Memory
- Upgrade to larger Render plan
- Reduce model complexity
- Optimize Docker image size

### Model Files Too Large
If model files exceed GitHub limits (>100MB):

**Option 1: Use Git LFS**
```bash
git lfs install
git lfs track "models/*.keras"
git add .gitattributes models/
git commit -m "Add models with LFS"
git push
```

**Option 2: Download during build**
Add to Dockerfile:
```dockerfile
RUN curl -o models/yamnet_classifier_v2.keras https://your-storage-url/model.keras
```

## Cost Estimate

### Free Tier
- API: Free (spins down after inactivity)
- UI: Free (spins down after inactivity)
- **Limitation**: No persistent storage, cold starts

### Starter Plan
- API: $7/month (always on)
- UI: $7/month (always on)
- Disk: $0.25/GB/month (10GB = $2.50/month)
- **Total**: ~$16.50/month

## Scaling

### Increase Resources
In `render.yaml`, change:
```yaml
plan: starter  # → standard, pro
disk:
  sizeGB: 10   # → 20, 50, 100
```

### Add Workers
For retraining jobs, add background worker:
```yaml
- type: worker
  name: ecosight-worker
  runtime: docker
  dockerfilePath: ./deployment/Dockerfile
  dockerContext: .
  startCommand: python retrain_model.py
```

## Custom Domain

1. Go to service settings
2. Click **"Custom Domain"**
3. Add your domain (e.g., `ecosight.yourdomain.com`)
4. Update DNS records as instructed
5. Render provides free SSL

## Security

### API Keys (Recommended)
Add to `render.yaml`:
```yaml
envVars:
  - key: API_KEY
    generateValue: true
```

Update API to require authentication:
```python
from fastapi import Header, HTTPException

@app.post("/predict")
async def predict(api_key: str = Header(None)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(401, "Invalid API key")
    # ... prediction logic
```

## Next Steps

1. ✅ Deploy to Render
2. Set up custom domain (optional)
3. Configure API authentication
4. Set up monitoring/alerts
5. Schedule automated retraining
6. Add MongoDB for audio storage (see MongoDB guide)

## Support

- Render Docs: https://render.com/docs
- EcoSight Issues: https://github.com/mangaorphy/ECOSIGHT/issues
- Render Community: https://community.render.com
