# 📋 Retraining Setup Checklist

## Understanding the Notebook Flow

Your notebook (`acoustic_togetherso_(1).ipynb`) follows this workflow:

1. **Load raw audio** from `extracted_audio/` → Original MP3/WAV files (1.7GB)
2. **Apply augmentation** → Pitch shift, time stretch, noise, etc.
3. **Save augmented** to `augmented_audio/` → 6x more files (10GB+)
4. **Extract embeddings** → YAMNet 1024-dim vectors
5. **Train classifier** → Dense neural network on embeddings
6. **Save model** → `yamnet_classifier.keras`

## What I've Implemented for Production

### ✅ Files Created/Updated

| File | Purpose |
|------|---------|
| `scripts/upload-extracted-audio-to-s3.sh` | Upload original audio to S3 |
| `src/audio_augmentation.py` | Augmentation functions (from notebook) |
| `src/s3_storage.py` | Added `download_extracted_audio()` method |
| `scripts/retrain_model.py` | Updated: Download → Augment → Train |
| `docs/RETRAINING_PIPELINE.md` | Complete technical documentation |
| `RETRAINING_FLOW_SUMMARY.md` | Detailed setup guide |

### ✅ The New Cloud Workflow

```
┌─────────────────────────────────────────┐
│   S3: extracted_audio/ (1.7GB)          │  ← Upload once
└─────────────────────────────────────────┘
               ↓ (download on retrain)
┌─────────────────────────────────────────┐
│   Container: extracted_audio/ (1.7GB)   │  ← Downloaded
└─────────────────────────────────────────┘
               ↓ (augment automatically)
┌─────────────────────────────────────────┐
│   Container: augmented_audio/ (10GB+)   │  ← Generated
└─────────────────────────────────────────┘
               ↓ (train model)
┌─────────────────────────────────────────┐
│   Container: models/*.keras             │  ← Saved
└─────────────────────────────────────────┘
```

**Key Benefits**:
- Store only 1.7GB in S3 (not 10GB+)
- Augmentation happens automatically
- Consistent across retraining runs
- Can regenerate anytime
- ~$0.04/month vs $1-2/month

## Setup Steps

### 1️⃣ Upload Original Audio to S3

```bash
# Upload extracted_audio/ to S3
./scripts/upload-extracted-audio-to-s3.sh
```

**What this does**:
- Creates S3 bucket: `ecosight-training-data`
- Uploads all files from `extracted_audio/`
- Sets bucket to private
- Shows upload summary

**Expected output**:
```
✓ Bucket created
✓ Upload complete!
✓ Downloaded 1000+ extracted audio files
```

### 2️⃣ Configure Render Environment

Go to: Render Dashboard → ecosight-api → Environment

Add these 4 variables:
```
S3_BUCKET=ecosight-training-data
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_REGION=us-east-1
```

Get credentials:
```bash
# View existing credentials
cat ~/.aws/credentials

# Or create new in AWS Console:
# IAM → Users → Your User → Security Credentials → Create Access Key
```

### 3️⃣ Verify Setup

```bash
# Check S3 upload successful
aws s3 ls s3://ecosight-training-data/extracted_audio/ --recursive | head -20

# Count total files
aws s3 ls s3://ecosight-training-data/extracted_audio/ --recursive | wc -l

# Check bucket size
aws s3 ls s3://ecosight-training-data/extracted_audio/ --recursive --summarize
```

### 4️⃣ Test Retraining (Optional)

Test locally before deploying:

```bash
# Set environment variables
export S3_BUCKET=ecosight-training-data
export AWS_ACCESS_KEY_ID=<your-key>
export AWS_SECRET_ACCESS_KEY=<your-secret>
export AWS_REGION=us-east-1

# Run retraining
python scripts/retrain_model.py
```

**Expected output**:
```
==================================================
DOWNLOADING AND AUGMENTING TRAINING DATA
==================================================
Step 1: Downloading extracted audio from S3...
✓ Downloaded 1000+ extracted audio files

Step 2: Applying audio augmentation...
  dog_bark: 100 → 600 files (6.0x)
  gun_shot: 50 → 300 files (6.0x)
  engine_idling: 75 → 450 files (6.0x)
✓ Total augmented files: 1350

==================================================
STARTING MODEL TRAINING
==================================================
[Training progress...]
```

### 5️⃣ Deploy to Render

Push changes to git (Render auto-deploys):

```bash
git add .
git commit -m "Add S3 + augmentation pipeline for retraining"
git push origin main
```

Render will:
1. Detect changes
2. Rebuild containers
3. Deploy with new S3 integration
4. Next retraining will use S3 workflow

## Verification Checklist

### Before Upload
- [ ] `extracted_audio/` folder exists
- [ ] Contains subdirectories (dog_bark, gun_shot, etc.)
- [ ] Files are WAV/MP3 format
- [ ] Total size ~1.7GB
- [ ] AWS CLI configured (`aws s3 ls` works)

### After Upload
- [ ] S3 bucket created: `ecosight-training-data`
- [ ] Files visible: `aws s3 ls s3://ecosight-training-data/extracted_audio/`
- [ ] File count matches local
- [ ] Upload script completed without errors

### Render Configuration
- [ ] Environment variables added
- [ ] S3_BUCKET = ecosight-training-data
- [ ] AWS_ACCESS_KEY_ID set
- [ ] AWS_SECRET_ACCESS_KEY set
- [ ] AWS_REGION = us-east-1

### After Deployment
- [ ] Render build successful
- [ ] No errors in logs
- [ ] Retraining logs show S3 download
- [ ] Augmentation running correctly

## How Augmentation Works

Each original file generates 6 variants:

| File | Augmentation |
|------|--------------|
| `audio1_original.wav` | Unchanged copy |
| `audio1_pitch_up.wav` | +2 semitones |
| `audio1_pitch_down.wav` | -2 semitones |
| `audio1_time_stretch_fast.wav` | 1.1x speed |
| `audio1_time_stretch_slow.wav` | 0.9x speed |
| `audio1_noise_light.wav` | +0.2% noise |

Plus combinations (pitch + volume, time + noise, etc.)

**Total**: 5 random augmentations selected per file → **6x data expansion**

## Cost Breakdown

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| S3 Storage | 1.7 GB | $0.04 |
| GET Requests | ~500/month | $0.00 |
| PUT Requests | ~50/month | $0.00 |
| Data Transfer | ~2GB/month | $0.00* |
| **TOTAL** | | **~$0.04/month** |

*Within free tier (Render to S3 in same region)

## Common Issues

### Issue: S3 download fails

**Error**: "S3 download failed, using local data"

**Solutions**:
1. Check AWS credentials in Render environment
2. Verify bucket name: `ecosight-training-data`
3. Check IAM permissions (s3:GetObject, s3:ListBucket)
4. Test: `aws s3 ls s3://ecosight-training-data/`

### Issue: Augmentation not working

**Error**: "Augmentation not available"

**Solutions**:
1. Check librosa installed: `pip show librosa`
2. Check soundfile installed: `pip show soundfile`
3. Verify extracted_audio has files
4. Check file formats (.wav/.mp3 only)

### Issue: Out of memory

**Error**: Container crashes during augmentation

**Solutions**:
1. Reduce `augmentations_per_file` from 5 to 3
2. Process classes one at a time
3. Increase Render instance memory

## Next Actions

1. **Run upload script**: `./scripts/upload-extracted-audio-to-s3.sh`
2. **Configure Render**: Add 4 environment variables
3. **Deploy**: Push to git
4. **Monitor**: Check Render logs during first retrain
5. **Verify**: Confirm S3 download and augmentation working

## Additional Resources

- **Full Documentation**: `docs/RETRAINING_PIPELINE.md`
- **Detailed Summary**: `RETRAINING_FLOW_SUMMARY.md`
- **S3 Setup Guide**: `docs/S3_SETUP.md`
- **Original Notebook**: `acoustic_togetherso_(1).ipynb`

---

**Status**: ✅ Ready to upload  
**Next Step**: `./scripts/upload-extracted-audio-to-s3.sh`
