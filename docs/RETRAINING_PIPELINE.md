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

### Configuration

Environment variables required for S3 integration:

```bash
S3_BUCKET=ecosight-training-data
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_REGION=us-east-1
```

### Automatic Retraining

Retraining is triggered automatically when:
- New audio files uploaded via `/upload` endpoint
- Minimum threshold met (100+ new samples)

## Adding New Training Data

### 1: Upload via Web UI

1. Open EcoSight dashboard
2. Navigate to "Training Data" tab
3. Select class (dog_bark, gun_shot, etc.)
4. Upload audio file (WAV/MP3)
5. File is saved to `extracted_audio/<class>/`
