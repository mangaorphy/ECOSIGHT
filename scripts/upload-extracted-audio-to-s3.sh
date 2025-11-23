#!/bin/bash

#############################################################################
# Upload Extracted Audio (Original/Raw Audio Files) to S3
#############################################################################
# This script uploads the extracted_audio/ folder containing original
# audio files to S3. These are the source files that will be downloaded
# during retraining, augmented, and used to train the model.
#
# Usage: ./scripts/upload-extracted-audio-to-s3.sh
#############################################################################

set -e  # Exit on error

# Configuration
S3_BUCKET="ecosight-training-data"
AWS_REGION="us-east-1"
SOURCE_DIR="extracted_audio"
S3_PREFIX="extracted_audio"

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "================================================================"
echo "  📤 Upload Extracted Audio (Original Files) to S3"
echo "================================================================"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ Error: AWS CLI is not installed${NC}"
    echo "Install it with: brew install awscli"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ Error: AWS credentials not configured${NC}"
    echo "Configure with: aws configure"
    exit 1
fi

echo -e "${BLUE}✓ AWS CLI configured${NC}"
echo ""

# Check if extracted_audio directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}❌ Error: Directory '$SOURCE_DIR' not found${NC}"
    echo "Make sure you have the extracted_audio folder with your original audio files"
    exit 1
fi

# Count files before upload
TOTAL_FILES=$(find "$SOURCE_DIR" -type f \( -name "*.wav" -o -name "*.mp3" \) | wc -l | tr -d ' ')
TOTAL_SIZE=$(du -sh "$SOURCE_DIR" | cut -f1)

echo -e "${BLUE}📊 Upload Summary:${NC}"
echo "  Source directory: $SOURCE_DIR"
echo "  Total audio files: $TOTAL_FILES"
echo "  Total size: $TOTAL_SIZE"
echo "  S3 bucket: $S3_BUCKET"
echo "  S3 path: s3://$S3_BUCKET/$S3_PREFIX/"
echo ""

# Create S3 bucket if it doesn't exist
echo -e "${YELLOW}📦 Checking S3 bucket...${NC}"
if aws s3 ls "s3://$S3_BUCKET" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "  Creating bucket: $S3_BUCKET"
    aws s3 mb "s3://$S3_BUCKET" --region "$AWS_REGION"
    echo -e "${GREEN}  ✓ Bucket created${NC}"
else
    echo -e "${GREEN}  ✓ Bucket exists${NC}"
fi
echo ""

# Upload extracted_audio folder to S3
echo -e "${YELLOW}📤 Uploading extracted audio files to S3...${NC}"
echo "  This may take several minutes depending on file size..."
echo ""

aws s3 sync "$SOURCE_DIR" "s3://$S3_BUCKET/$S3_PREFIX/" \
    --exclude "*.DS_Store" \
    --exclude "*/.*" \
    --include "*.wav" \
    --include "*.mp3" \
    --delete \
    --region "$AWS_REGION"

echo ""
echo -e "${GREEN}✓ Upload complete!${NC}"
echo ""

# Set bucket to private (block public access)
echo -e "${YELLOW}🔒 Setting bucket to private...${NC}"
aws s3api put-public-access-block \
    --bucket "$S3_BUCKET" \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
    --region "$AWS_REGION"

echo -e "${GREEN}✓ Bucket is private${NC}"
echo ""

# Show what was uploaded
echo "================================================================"
echo -e "${GREEN}  ✅ UPLOAD SUCCESSFUL${NC}"
echo "================================================================"
echo ""
echo "📁 S3 Structure:"
aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/" --recursive --human-readable --summarize | tail -20
echo ""

echo "================================================================"
echo "  Next Steps:"
echo "================================================================"
echo ""
echo "1. Add environment variables to Render:"
echo "   S3_BUCKET=$S3_BUCKET"
echo "   AWS_ACCESS_KEY_ID=<your-key>"
echo "   AWS_SECRET_ACCESS_KEY=<your-secret>"
echo "   AWS_REGION=$AWS_REGION"
echo ""
echo "2. The retraining script will:"
echo "   • Download extracted_audio from S3"
echo "   • Apply augmentation to create augmented_audio"
echo "   • Train model on augmented data"
echo ""
echo "================================================================"
echo ""
echo -e "${BLUE}💡 Tip: View bucket contents anytime with:${NC}"
echo "   aws s3 ls s3://$S3_BUCKET/$S3_PREFIX/ --recursive --human-readable"
echo ""
