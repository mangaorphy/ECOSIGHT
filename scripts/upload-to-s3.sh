#!/bin/bash

###############################################################################
# Upload EcoSight Training Data to AWS S3
###############################################################################

set -e
export AWS_PAGER=""

# Configuration
BUCKET_NAME="ecosight-training-data"
AWS_REGION="${AWS_REGION:-us-east-1}"
LOCAL_AUDIO_PATH="./augmented_audio"

echo "========================================="
echo "EcoSight S3 Training Data Upload"
echo "========================================="
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS credentials not configured!"
    echo "Please run: aws configure"
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✓ AWS Account ID: $AWS_ACCOUNT_ID"
echo ""

# Check if bucket exists
echo "Step 1: Checking S3 bucket..."
if aws s3 ls "s3://${BUCKET_NAME}" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Creating S3 bucket: $BUCKET_NAME"
    
    # Create bucket
    if [ "$AWS_REGION" == "us-east-1" ]; then
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$AWS_REGION"
    else
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$AWS_REGION" \
            --create-bucket-configuration LocationConstraint="$AWS_REGION"
    fi
    
    # Block public access (security best practice)
    aws s3api put-public-access-block \
        --bucket "$BUCKET_NAME" \
        --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    
    echo "✓ Bucket created: $BUCKET_NAME"
else
    echo "✓ Bucket exists: $BUCKET_NAME"
fi

echo ""

# Upload audio files
echo "Step 2: Uploading training audio files..."
if [ ! -d "$LOCAL_AUDIO_PATH" ]; then
    echo "❌ Directory not found: $LOCAL_AUDIO_PATH"
    exit 1
fi

# Count files
TOTAL_FILES=$(find "$LOCAL_AUDIO_PATH" -type f -name "*.wav" | wc -l | tr -d ' ')
echo "Found $TOTAL_FILES audio files to upload"
echo ""

# Upload with progress
aws s3 sync "$LOCAL_AUDIO_PATH" "s3://${BUCKET_NAME}/augmented_audio/" \
    --exclude "*" \
    --include "*.wav" \
    --no-progress

echo "✓ Audio files uploaded to S3"
echo ""

# Show bucket contents
echo "Step 3: Verifying upload..."
echo ""
echo "Files in S3 bucket:"
aws s3 ls "s3://${BUCKET_NAME}/augmented_audio/" --recursive --human-readable | head -20

echo ""
echo "========================================="
echo "✓ Upload Complete!"
echo "========================================="
echo ""
echo "📦 S3 Bucket: $BUCKET_NAME"
echo "📍 Region: $AWS_REGION"
echo "📁 Path: s3://${BUCKET_NAME}/augmented_audio/"
echo ""
echo "💰 Cost: S3 Free Tier includes:"
echo "   - 5 GB storage"
echo "   - 20,000 GET requests"
echo "   - 2,000 PUT requests"
echo ""
echo "Next steps:"
echo "1. Set S3_BUCKET environment variable in Render"
echo "2. Add AWS credentials to Render"
echo "3. Model will download training data from S3 when retraining"
echo ""
