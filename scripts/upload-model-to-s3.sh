#!/bin/bash

# Upload trained model to S3
# This allows Render to download the model on startup instead of including in Git

set -e

BUCKET="ecosight-training-data"
MODEL_FILE="models/yamnet_classifier_v2.keras"
METADATA_FILE="models/model_metadata.json"
CLASSES_FILE="models/class_names.json"

echo "================================================================"
echo "  📦 Uploading Model to S3"
echo "================================================================"

# Check if model exists
if [ ! -f "$MODEL_FILE" ]; then
    echo "❌ Error: Model file not found at $MODEL_FILE"
    exit 1
fi

# Upload model
echo "Uploading model file..."
aws s3 cp "$MODEL_FILE" "s3://$BUCKET/models/yamnet_classifier_v2.keras" \
    --metadata "uploaded=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "✓ Model uploaded"

# Upload metadata if exists
if [ -f "$METADATA_FILE" ]; then
    echo "Uploading metadata..."
    aws s3 cp "$METADATA_FILE" "s3://$BUCKET/models/model_metadata.json"
    echo "✓ Metadata uploaded"
fi

# Upload class names if exists
if [ -f "$CLASSES_FILE" ]; then
    echo "Uploading class names..."
    aws s3 cp "$CLASSES_FILE" "s3://$BUCKET/models/class_names.json"
    echo "✓ Class names uploaded"
fi

echo ""
echo "================================================================"
echo "  ✅ Model Upload Complete"
echo "================================================================"
echo ""
echo "Files uploaded to s3://$BUCKET/models/"
echo ""
echo "Next steps:"
echo "1. Remove models/ from Git: git rm -r --cached models/"
echo "2. Add models/ to .gitignore"
echo "3. Render will download model on startup from S3"
echo ""
