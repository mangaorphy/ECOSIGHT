# EcoSight Retraining Flow Summary

## Quick Overview

Your notebook follows this workflow:
1. **Load raw audio** from `extracted_audio/` (original MP3/WAV files)
2. **Apply augmentation** (pitch shift, time stretch, noise, etc.)
3. **Save augmented files** to `augmented_audio/` (as WAV files)
4. **Extract YAMNet embeddings** from augmented files
5. **Train classifier** on embeddings
6. **Save model** for deployment

## What You Need

You want to:
1. **Upload `extracted_audio/`** to S3 (the original raw audio files - 1.7GB)
2. **For retraining**: Download from S3 → Augment → Train → Save model

This is the RIGHT approach because:
- `extracted_audio/` = source of truth (original recordings)
- `augmented_audio/` = generated from originals (can be recreated)
- Docker containers shouldn't contain large datasets (ephemeral)
- S3 stores originals, augmentation happens during retraining
- Saves storage costs (1.7GB vs 10GB+)

## What I've Implemented

### 1. Upload Script for Extracted Audio

**File**: `scripts/upload-extracted-audio-to-s3.sh`

Uploads your `extracted_audio/` folder (original audio files) to S3:

```bash
./scripts/upload-extracted-audio-to-s3.sh
```

This creates:
```
s3://ecosight-training-data/
  └── extracted_audio/
      ├── dog_bark/
      │   ├── audio1.mp3
      │   └── audio2.wav
      ├── gun_shot/
      ├── engine_idling/
      └── clips/
```

### 2. Audio Augmentation Module

**File**: `src/audio_augmentation.py`

Implements all augmentation techniques from your notebook:
- `time_stretch()` - Speed changes (0.9x-1.1x)
- `pitch_shift()` - Tone changes (±2 semitones)
- `add_noise()` - Background noise addition
- `time_shift()` - Temporal offset
- `change_volume()` - Amplitude changes (±20%)
- `augment_audio_file()` - Apply 5 random augmentations per file
- `augment_directory()` - Process entire class structure

Result: **1 audio file → 6 augmented files** (original + 5 variants)

### 3. Updated S3 Storage Library

**File**: `src/s3_storage.py`

Added new method:
- `download_extracted_audio()` - Downloads original audio from S3

Existing method (now deprecated):
- `download_training_data()` - Downloads augmented audio (old approach)

### 4. Updated Retraining Pipeline

**File**: `scripts/retrain_model.py`

Complete workflow:

```python
def _download_training_data_from_s3(self):
    # Step 1: Download extracted_audio from S3
    s3_storage.download_extracted_audio("/app/extracted_audio")
    
    # Step 2: Apply augmentation to create augmented_audio
    augment_directory(
        input_dir="/app/extracted_audio",
        output_dir="/app/augmented_audio",
        augmentations_per_file=5
    )
    
    # Step 3: Continue with normal training...
```

### 5. Comprehensive Documentation

**File**: `docs/RETRAINING_PIPELINE.md`

Complete guide covering:
- Architecture diagram
- Workflow explanation
- File structure
- Usage instructions
- Augmentation details
- Troubleshooting
- Cost optimization

## How It Works

### Current State (Your Notebook)

```
Local Machine:
  extracted_audio/     [1.7GB original audio]
       ↓
  (Manual augmentation in notebook)
       ↓
  augmented_audio/     [10GB+ augmented audio]
       ↓
  (Train model)
       ↓
  models/yamnet_classifier.keras
```

### New Cloud Pipeline

```
S3 (Cloud Storage):
  extracted_audio/     [1.7GB - stored permanently]
       ↓ (download on retraining)
       ↓
Container/Render:
  extracted_audio/     [1.7GB - downloaded]
       ↓ (augment automatically)
       ↓
  augmented_audio/     [10GB+ - generated, ephemeral]
       ↓ (train model)
       ↓
  models/yamnet_classifier.keras
```

**Key Benefits**:
1. Store only 1.7GB in S3 (not 10GB+)
2. Augmentation happens automatically during retraining
3. Consistent augmentation across all retraining runs
4. Can regenerate augmented data anytime
5. ~$0.04/month S3 costs vs $1-2/month if storing augmented data

## Your Data Structure

Current `extracted_audio/` contents:

```
extracted_audio/
├── clips/              (1000+ MP3 files)
├── dog_bark/           (audio files)
├── gun_shot/           (audio files)
└── engine_idling/      (audio files)

Total: ~1.7GB
```

After augmentation (generated automatically):

```
augmented_audio/
├── dog_bark/
│   ├── audio1_original.wav
│   ├── audio1_pitch_up.wav
│   ├── audio1_time_stretch_fast.wav
│   ├── audio1_noise_light.wav
│   ├── audio1_volume_up.wav
│   └── audio1_combined_1.wav
├── gun_shot/
│   └── ... (6x files per original)
└── engine_idling/
    └── ... (6x files per original)

Total: ~10GB+ (generated on-demand, not stored in S3)
```

## Next Steps

### 1. Upload Extracted Audio to S3

```bash
# Make script executable (already done)
chmod +x scripts/upload-extracted-audio-to-s3.sh

# Upload extracted_audio to S3
./scripts/upload-extracted-audio-to-s3.sh
```

This will:
- Create S3 bucket `ecosight-training-data`
- Upload all files from `extracted_audio/`
- Set bucket to private
- Show upload summary

### 2. Configure Render Environment Variables

Add to Render dashboard (ecosight-api → Environment):

```bash
S3_BUCKET=ecosight-training-data
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_REGION=us-east-1
```

Get your AWS credentials:
```bash
# View existing credentials
cat ~/.aws/credentials

# Or create new access key
# AWS Console → IAM → Users → Your User → Security Credentials → Create Access Key
```

### 3. Test Locally (Optional)

```bash
# Test retraining pipeline locally
python scripts/retrain_model.py
```

This will:
1. Download extracted_audio from S3
2. Apply augmentation
3. Train model
4. Save to models/

### 4. Deploy to Render

Render will automatically deploy when you push changes. The retraining will:
1. Download extracted_audio from S3
2. Apply augmentation (creates augmented_audio)
3. Train model on augmented data
4. Save model for predictions

## Files Changed

| File | Status | Purpose |
|------|--------|---------|
| `scripts/upload-extracted-audio-to-s3.sh` | ✅ Created | Upload script for original audio |
| `src/audio_augmentation.py` | ✅ Created | Augmentation functions from notebook |
| `src/s3_storage.py` | ✅ Updated | Added `download_extracted_audio()` |
| `scripts/retrain_model.py` | ✅ Updated | Download → Augment → Train workflow |
| `docs/RETRAINING_PIPELINE.md` | ✅ Created | Complete pipeline documentation |
| `config/requirements.txt` | ✅ No change | (soundfile already present) |

## Verification Checklist

Before uploading to S3:

- [ ] `extracted_audio/` exists
- [ ] Contains class subdirectories (dog_bark, gun_shot, etc.)
- [ ] Total size is ~1.7GB
- [ ] Files are WAV/MP3 format
- [ ] AWS CLI is configured (`aws s3 ls` works)

After uploading to S3:

- [ ] S3 bucket created: `ecosight-training-data`
- [ ] Files uploaded: `aws s3 ls s3://ecosight-training-data/extracted_audio/`
- [ ] Environment variables set in Render
- [ ] Render deployment successful
- [ ] Logs show S3 download working

## Cost Estimate

| Item | Monthly Cost |
|------|--------------|
| S3 Storage (1.7GB) | $0.04 |
| S3 Requests (~500 GET) | $0.00 |
| Data Transfer (~2GB/month) | $0.00* |
| **Total** | **~$0.04/month** |

*Within AWS free tier (1GB/month), Render to S3 in same region is free

## Questions?

**Q: Why not store augmented_audio in S3?**  
A: It's 6x larger (10GB+), costs more, and can be regenerated from extracted_audio anytime.

**Q: What if S3 download fails?**  
A: The system falls back to local data if available. Logs will show "S3 not configured, using local data".

**Q: How often does augmentation run?**  
A: Only during retraining. Augmented files are generated fresh each time to ensure consistency.

**Q: Can I change augmentation settings?**  
A: Yes, edit `augmentations_per_file` in `scripts/retrain_model.py` (default: 5 variants per file).

**Q: Will this work with my notebook workflow?**  
A: Yes! The augmentation code is directly from your notebook, just automated for production use.

---

**Ready to proceed?** Run the upload script:

```bash
./scripts/upload-extracted-audio-to-s3.sh
```
