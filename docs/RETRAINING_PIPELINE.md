# EcoSight Retraining Pipeline

## Overview

The EcoSight retraining pipeline uses a **download → augment → train** workflow to retrain the YAMNet classifier with new audio data stored in AWS S3.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    S3 Storage (Cloud)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  extracted_audio/ (Original/Raw Audio Files)           │ │
│  │    ├── dog_bark/                                       │ │
│  │    │   ├── audio1.mp3                                  │ │
│  │    │   └── audio2.wav                                  │ │
│  │    ├── gun_shot/                                       │ │
│  │    └── engine_idling/                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    (Download via S3)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Container/Local Environment                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  extracted_audio/ (Downloaded from S3)                 │ │
│  │    ├── dog_bark/                                       │ │
│  │    │   ├── audio1.mp3                                  │ │
│  │    │   └── audio2.wav                                  │ │
│  │    └── ...                                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│                  (Apply Augmentation)                        │
│              • Pitch shift (+/- 2 semitones)                 │
│              • Time stretch (0.9x - 1.1x)                    │
│              • Noise addition                                │
│              • Volume adjustment                             │
│              • Combinations                                  │
│                            ↓                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  augmented_audio/ (Generated, 6x more files)           │ │
│  │    ├── dog_bark/                                       │ │
│  │    │   ├── audio1_original.wav                         │ │
│  │    │   ├── audio1_pitch_up.wav                         │ │
│  │    │   ├── audio1_time_stretch_fast.wav                │ │
│  │    │   ├── audio1_noise_light.wav                      │ │
│  │    │   ├── audio1_volume_up.wav                        │ │
│  │    │   ├── audio1_combined_1.wav                       │ │
│  │    │   └── ... (5-6 variants per original)             │ │
│  │    └── ...                                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│                  (Extract YAMNet Embeddings)                 │
│                            ↓                                 │
│                  (Train Classifier)                          │
│                            ↓                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  models/                                               │ │
│  │    ├── yamnet_classifier.keras (New Model)             │ │
│  │    └── class_names.pkl                                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Workflow

### 1. **Upload Original Audio to S3** (One-time setup)

Upload your original/raw audio files to S3:

```bash
./scripts/upload-extracted-audio-to-s3.sh
```

This uploads the `extracted_audio/` folder containing:
- Original recordings (MP3/WAV format)
- Organized by class (dog_bark, gun_shot, etc.)
- Total size: ~1.7GB in your case

**Why upload extracted_audio?**
- Source of truth (original recordings)
- Smaller than augmented data
- Can regenerate augmented files anytime
- Consistent quality across retraining runs

### 2. **Retraining Process** (Automatic when triggered)

When retraining is triggered (via API or script), the pipeline:

**Step 1: Download from S3**
```python
# Downloads extracted_audio/ from S3
s3_storage.download_extracted_audio("/app/extracted_audio")
```

**Step 2: Apply Augmentation**
```python
# Creates augmented_audio/ with 5-6 variants per file
augment_directory(
    input_dir="/app/extracted_audio",
    output_dir="/app/augmented_audio",
    augmentations_per_file=5
)
```

Augmentation techniques:
- **Pitch shift**: ±2 semitones (higher/lower tone)
- **Time stretch**: 0.9x-1.1x speed (faster/slower)
- **Noise addition**: Light/medium background noise
- **Volume adjustment**: ±20% amplitude
- **Combinations**: Mixed augmentations

Result: **1 original file → 6 augmented files** (original + 5 variants)

**Step 3: Extract YAMNet Embeddings**
```python
# Extract 1024-dimensional embeddings from each audio file
for audio_file in augmented_audio_files:
    embedding = yamnet_model(audio_waveform)
```

**Step 4: Train Classifier**
```python
# Train dense neural network on embeddings
model.fit(embeddings, labels, epochs=100)
```

**Step 5: Save Model**
```python
# Save trained model and class names
model.save("models/yamnet_classifier.keras")
```

## Files and Directories

### Source Code

| File | Purpose |
|------|---------|
| `scripts/retrain_model.py` | Main retraining pipeline script |
| `src/audio_augmentation.py` | Audio augmentation functions |
| `src/s3_storage.py` | S3 download/upload utilities |
| `scripts/upload-extracted-audio-to-s3.sh` | Upload script for extracted audio |

### Data Directories

| Directory | Contains | Generated? | Stored in S3? |
|-----------|----------|------------|---------------|
| `extracted_audio/` | Original audio files (MP3/WAV) | No (uploaded by user) | ✅ Yes |
| `augmented_audio/` | Augmented training files (WAV) | Yes (during retraining) | ❌ No (regenerated) |
| `models/` | Trained model files | Yes (after training) | ❌ No (too large) |
| `features/` | Cached embeddings | Yes (optional) | ❌ No (ephemeral) |

### Configuration

Environment variables required for S3 integration:

```bash
S3_BUCKET=ecosight-training-data
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_REGION=us-east-1
```

## Usage

### Initial Setup

1. **Upload original audio to S3:**
   ```bash
   ./scripts/upload-extracted-audio-to-s3.sh
   ```

2. **Configure Render environment variables:**
   - Go to Render dashboard → ecosight-api → Environment
   - Add the 4 variables listed above
   - Save (triggers auto-redeploy)

### Manual Retraining

Run retraining manually:

```bash
python scripts/retrain_model.py
```

This will:
1. Check S3 credentials
2. Download extracted_audio from S3
3. Apply augmentation
4. Train model
5. Save to `models/yamnet_classifier.keras`

### Automatic Retraining

Retraining is triggered automatically when:
- New audio files uploaded via `/upload` endpoint
- Minimum threshold met (100+ new samples)

## Adding New Training Data

### Option 1: Upload via Web UI

1. Open EcoSight dashboard
2. Navigate to "Training Data" tab
3. Select class (dog_bark, gun_shot, etc.)
4. Upload audio file (WAV/MP3)
5. File is saved to `extracted_audio/<class>/`

### Option 2: Manual Upload to S3

```bash
# Add files locally to extracted_audio/
cp new_audio.mp3 extracted_audio/dog_bark/

# Upload to S3
./scripts/upload-extracted-audio-to-s3.sh
```

### Option 3: AWS CLI Direct Upload

```bash
# Upload single file
aws s3 cp audio.mp3 s3://ecosight-training-data/extracted_audio/dog_bark/

# Upload directory
aws s3 sync local_dir/ s3://ecosight-training-data/extracted_audio/dog_bark/
```

## Augmentation Details

Each original audio file generates multiple variants:

| Augmentation | Description | Example |
|--------------|-------------|---------|
| `original` | Unchanged copy | `audio1_original.wav` |
| `pitch_up` | +2 semitones | `audio1_pitch_up.wav` |
| `pitch_down` | -2 semitones | `audio1_pitch_down.wav` |
| `time_stretch_fast` | 1.1x speed | `audio1_time_stretch_fast.wav` |
| `time_stretch_slow` | 0.9x speed | `audio1_time_stretch_slow.wav` |
| `noise_light` | +0.2% noise | `audio1_noise_light.wav` |
| `noise_medium` | +0.5% noise | `audio1_noise_medium.wav` |
| `volume_up` | +20% volume | `audio1_volume_up.wav` |
| `volume_down` | -20% volume | `audio1_volume_down.wav` |
| `combined_1` | Time stretch + noise | `audio1_combined_1.wav` |
| `combined_2` | Pitch + volume | `audio1_combined_2.wav` |

**Random selection**: 5 augmentations are randomly selected per file to prevent overfitting.

## Benefits of This Approach

### ✅ Advantages

1. **Data Expansion**: 1 audio file → 6 training samples (6x increase)
2. **Robustness**: Model learns to handle variations (pitch, speed, noise)
3. **Generalization**: Better performance on real-world audio
4. **Consistency**: Same augmentation applied to all retraining runs
5. **Storage Efficiency**: Store originals (1.7GB), not augmented (10GB+)
6. **Reproducibility**: Can regenerate augmented data anytime

### 📊 Data Volume Example

Starting with 100 original audio files:
- Extracted audio: 100 files (stored in S3)
- Augmented audio: 600 files (generated during training)
- Training samples: 600 embeddings × epochs
- Storage: Only 100 files stored, 600 generated on-demand

## Monitoring and Debugging

### Check S3 Contents

```bash
# List all files in S3
aws s3 ls s3://ecosight-training-data/extracted_audio/ --recursive

# Check total size
aws s3 ls s3://ecosight-training-data/extracted_audio/ --recursive --summarize

# Count files per class
aws s3 ls s3://ecosight-training-data/extracted_audio/dog_bark/ | wc -l
```

### Check Local Augmentation

```bash
# Count augmented files
find augmented_audio -name "*.wav" | wc -l

# Check augmentation ratio
# Expected: 6x more files than extracted_audio
```

### View Retraining Logs

```bash
# Check retraining history
cat models/retraining_log.json

# View Render logs
# Render dashboard → ecosight-api → Logs
```

## Troubleshooting

### S3 Download Fails

**Symptom**: "S3 download failed, using local data"

**Solutions**:
1. Check AWS credentials are set in Render
2. Verify bucket name: `ecosight-training-data`
3. Check IAM permissions (s3:GetObject, s3:ListBucket)
4. Test locally: `aws s3 ls s3://ecosight-training-data/`

### Augmentation Fails

**Symptom**: "Augmentation not available"

**Solutions**:
1. Check librosa installed: `pip show librosa`
2. Check soundfile installed: `pip show soundfile`
3. Verify extracted_audio exists and contains files
4. Check file formats (WAV/MP3 supported)

### Out of Memory

**Symptom**: Container crashes during augmentation

**Solutions**:
1. Reduce `augmentations_per_file` from 5 to 3
2. Process classes sequentially (not in parallel)
3. Increase Render instance memory
4. Delete old augmented files before regenerating

### Training Data Not Found

**Symptom**: "No audio files found"

**Solutions**:
1. Check extracted_audio has class subdirectories
2. Verify file extensions (.wav, .mp3)
3. Check S3 upload completed successfully
4. Ensure class names match (dog_bark, not dog-bark)

## Best Practices

1. **Keep originals safe**: Always store extracted_audio in S3
2. **Test locally first**: Run retraining locally before deploying
3. **Monitor storage**: Check S3 usage to avoid unexpected costs
4. **Version models**: Keep old models before retraining
5. **Validate augmentation**: Listen to augmented samples to verify quality
6. **Balanced classes**: Ensure each class has similar number of samples

## Cost Optimization

### S3 Costs (extracted_audio only)

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| Storage | 1.7 GB | $0.04 |
| GET requests | ~500/month | $0.00 |
| PUT requests | ~50/month | $0.00 |
| **Total** | | **~$0.04/month** |

### Why Not Store Augmented Audio?

If you stored augmented_audio (6x larger = ~10GB):
- Storage: $0.23/month
- Transfer: $0.90/GB downloaded
- **Total**: $1-2/month vs $0.04/month

**Savings**: 95% by regenerating augmented data during retraining

## Advanced Configuration

### Custom Augmentation Settings

Edit `scripts/retrain_model.py`:

```python
# Change number of augmentations per file
results = augment_directory(
    input_dir=EXTRACTED_AUDIO_DIR,
    output_dir=self.augmented_audio_dir,
    sr=SAMPLE_RATE,
    augmentations_per_file=3  # Reduce from 5 to 3
)
```

### Custom Augmentation Techniques

Edit `src/audio_augmentation.py`:

```python
# Add custom augmentation
augmentation_configs = [
    # ... existing augmentations ...
    ('custom', lambda a: your_custom_function(a)),
]
```

### Change Sample Rate

Edit `scripts/retrain_model.py`:

```python
SAMPLE_RATE = 16000  # YAMNet uses 16kHz (don't change unless using different model)
```

## Next Steps

1. ✅ Upload extracted_audio to S3
2. ✅ Configure Render environment variables
3. ✅ Test retraining locally
4. ✅ Deploy to Render
5. ✅ Monitor first retraining run
6. ✅ Add new training data as needed

## Related Documentation

- [S3 Setup Guide](./S3_SETUP.md) - Detailed S3 configuration
- [Retraining Guide](./RETRAINING_GUIDE.md) - Manual retraining instructions
- [Deployment Guide](./RENDER_DEPLOYMENT.md) - Render deployment steps
- [Audio Augmentation Notebook](../acoustic_togetherso_(1).ipynb) - Original augmentation research

---

**Last Updated**: 2025-11-23  
**Version**: 2.0 (Extracted Audio Pipeline)
