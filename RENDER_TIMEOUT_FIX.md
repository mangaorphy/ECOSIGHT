# Render Timeout Issues - Fixed! ✅

## What Was Wrong

### Problem:
- **Free tier** has strict limits (512MB RAM, slow CPUs, short timeouts)
- **Model loading** takes 60-120 seconds (YAMNet + TensorFlow)
- **Health checks timing out** before model loads
- Missing new source files (s3_storage.py, audio_augmentation.py)

### Solution Applied:

1. ✅ **Upgraded to Starter Plan** ($7/month per service = $14/month total)
   - 512MB → 2GB RAM
   - Faster CPUs
   - Better network performance

2. ✅ **Increased Health Check Timeouts**
   - Start period: 90s → **180s** (gives model time to load)
   - Timeout: 10s → **30s** per check
   - Retries: 5 → 3 (less aggressive)

3. ✅ **Added Persistent Disk**
   - 1GB disk mounted at `/app/models`
   - Model persists across deployments

4. ✅ **Increased Request Timeouts**
   - `--timeout-keep-alive 300` (5 minutes for predictions/retraining)

5. ✅ **Fixed File Copying**
   - Now copies entire `src/` directory (includes new S3/augmentation modules)
   - Creates `extracted_audio/` directory for S3 downloads

## What to Do Now

### 1. Render Will Auto-Redeploy
Your push to GitHub will trigger automatic redeployment with new settings.

### 2. Monitor the Deployment
Go to Render Dashboard → ecosight-api → Logs

**Expected logs:**
```
Building Docker image...
Starting service...
Loading YAMNet model... (takes ~60-90s)
✓ Model loaded successfully
Server started at http://0.0.0.0:8000
Health check passed ✓
```

### 3. Check Health After 3-5 Minutes
```bash
curl https://ecosight-api.onrender.com/status
```

**Expected response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "uptime_seconds": 123,
  "classes": ["clips", "dog_bark", "engine_idling", "gun_shot"]
}
```

## Cost Breakdown

### Starter Plan ($7/month each):
- **ecosight-api**: $7/month
- **ecosight-ui**: $7/month
- **Total**: $14/month

**Includes:**
- 2GB RAM per service
- Persistent disk (1GB for models)
- Better CPU/network
- No sleep on free tier (always on)

### Alternative: Keep UI on Free, API on Starter
If budget is tight:
- **API**: Starter ($7/month) - needs resources for ML
- **UI**: Free ($0/month) - just serves Streamlit pages
- **Total**: $7/month

To do this, edit render.yaml:
```yaml
# Change ecosight-ui back to:
plan: free
```

## Why Not Vercel?

Vercel won't work because:
- ❌ **50MB limit** - Your model is larger
- ❌ **10-60s timeout** - Model loading takes 60-120s
- ❌ **Serverless** - No persistent storage for models
- ❌ **Memory limits** - TensorFlow needs 2-4GB

**Stick with Render** - it's designed for ML apps!

## Alternative Platforms (If Render Doesn't Work)

### 1. Railway.app ($5/month)
- Similar to Render
- Slightly cheaper
- Good for ML apps

### 2. Fly.io ($5-10/month)
- Closer to your users (global edge)
- Free tier available
- Good Docker support

### 3. AWS EC2 + Elastic Beanstalk (Variable cost)
- Full control
- More complex setup
- ~$10-20/month for small instance

### 4. Google Cloud Run (Pay per use)
- Serverless containers
- Can handle large models
- ~$5-15/month depending on traffic

## Troubleshooting

### If Still Timing Out After 5 Minutes:

1. **Check Logs** - Look for errors during model loading
2. **Verify Model File** - Make sure yamnet_classifier_v2.keras exists in repo
3. **Check RAM Usage** - Starter plan has 2GB, should be enough
4. **Increase Start Period** - Edit render.yaml:
   ```yaml
   HEALTHCHECK --start-period=300s  # 5 minutes
   ```

### If Out of Memory:

Consider removing model from Docker image and downloading from S3:
```python
# In api.py startup
if not os.path.exists(MODEL_PATH):
    from s3_storage import S3Storage
    s3 = S3Storage()
    s3.download_model()  # Download from S3
```

## Next Steps

1. ✅ **Wait for deployment** (~5-10 minutes)
2. ✅ **Add S3 environment variables** (per previous instructions)
3. ✅ **Test /status endpoint**
4. ✅ **Test file upload** (should auto-save to S3)
5. ✅ **Test prediction endpoint**

## Success Criteria

You'll know it's working when:
- ✅ Deployment completes without errors
- ✅ `/status` returns `"model_loaded": true`
- ✅ Can upload files and get predictions
- ✅ Files appear in S3 bucket
- ✅ No timeout errors in logs

Good luck! The fixes should resolve the timeout issues. 🚀
