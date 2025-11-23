#!/bin/bash

#############################################################################
# EcoSight Local Docker Testing Script
#############################################################################
# Tests the complete retraining pipeline locally with Docker:
# 1. Build containers
# 2. Start services
# 3. Test S3 download + augmentation (optional)
# 4. Test retraining
# 5. Test predictions
#
# Usage: ./scripts/test-docker-local.sh [--with-s3]
#############################################################################

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
USE_S3=false
if [[ "$1" == "--with-s3" ]]; then
    USE_S3=true
fi

echo ""
echo "================================================================"
echo "  🐳 EcoSight Local Docker Testing"
echo "================================================================"
echo ""

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo ""
    
    if [ "$USE_S3" = true ]; then
        echo -e "${YELLOW}⚠️  Please edit .env and add your AWS credentials:${NC}"
        echo "   - AWS_ACCESS_KEY_ID"
        echo "   - AWS_SECRET_ACCESS_KEY"
        echo ""
        echo "Press Enter to continue once you've added credentials..."
        read
    fi
fi

# Test mode
if [ "$USE_S3" = true ]; then
    echo -e "${BLUE}📦 Test Mode: WITH S3 (will download from S3)${NC}"
    echo ""
    
    # Check AWS credentials in .env
    if ! grep -q "AWS_ACCESS_KEY_ID=.\+" .env; then
        echo -e "${RED}❌ Error: AWS_ACCESS_KEY_ID not set in .env${NC}"
        echo "Edit .env and add your AWS credentials"
        exit 1
    fi
else
    echo -e "${BLUE}📂 Test Mode: LOCAL ONLY (uses local extracted_audio/)${NC}"
    echo ""
    
    # Check if extracted_audio exists
    if [ ! -d "extracted_audio" ]; then
        echo -e "${RED}❌ Error: extracted_audio/ directory not found${NC}"
        echo "This directory should contain your original audio files"
        echo ""
        echo "Expected structure:"
        echo "  extracted_audio/"
        echo "    ├── dog_bark/"
        echo "    ├── gun_shot/"
        echo "    └── engine_idling/"
        exit 1
    fi
    
    # Count files
    AUDIO_COUNT=$(find extracted_audio -type f \( -name "*.wav" -o -name "*.mp3" \) | wc -l | tr -d ' ')
    echo -e "${GREEN}✓ Found $AUDIO_COUNT audio files in extracted_audio/${NC}"
    echo ""
fi

# Stop any running containers
echo -e "${YELLOW}Stopping any running containers...${NC}"
cd deployment
docker compose down > /dev/null 2>&1 || true
cd ..
echo -e "${GREEN}✓ Cleaned up old containers${NC}"
echo ""

# Build containers
echo "================================================================"
echo -e "${YELLOW}Step 1: Building Docker containers...${NC}"
echo "================================================================"
echo "This may take a few minutes on first run..."
echo ""

cd deployment
docker compose build --no-cache
cd ..

echo ""
echo -e "${GREEN}✓ Containers built successfully${NC}"
echo ""

# Start services
echo "================================================================"
echo -e "${YELLOW}Step 2: Starting services...${NC}"
echo "================================================================"
echo ""

cd deployment
docker compose up -d
cd ..

echo ""
echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Wait for API to be ready
echo -e "${YELLOW}Waiting for API to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/status > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is ready${NC}"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# Test retraining
echo "================================================================"
echo -e "${YELLOW}Step 3: Testing Retraining Pipeline${NC}"
echo "================================================================"
echo ""

if [ "$USE_S3" = true ]; then
    echo "This will:"
    echo "  1. Download extracted_audio from S3"
    echo "  2. Apply augmentation (creates augmented_audio)"
    echo "  3. Train model on augmented data"
    echo "  4. Save model to models/"
else
    echo "This will:"
    echo "  1. Use local extracted_audio/"
    echo "  2. Apply augmentation (creates augmented_audio)"
    echo "  3. Train model on augmented data"
    echo "  4. Save model to models/"
fi

echo ""
echo -e "${YELLOW}Running retrain script in container...${NC}"
echo ""

docker exec -it ecosight-api-1 python /app/scripts/retrain_model.py

echo ""
echo -e "${GREEN}✓ Retraining completed${NC}"
echo ""

# Check results
echo "================================================================"
echo -e "${YELLOW}Step 4: Checking Results${NC}"
echo "================================================================"
echo ""

# Check if model was created
if [ -f "models/yamnet_classifier.keras" ]; then
    MODEL_SIZE=$(du -h models/yamnet_classifier.keras | cut -f1)
    echo -e "${GREEN}✓ Model created: yamnet_classifier.keras ($MODEL_SIZE)${NC}"
else
    echo -e "${RED}❌ Model not found${NC}"
fi

# Check augmented_audio
if [ -d "augmented_audio" ]; then
    AUG_COUNT=$(find augmented_audio -type f -name "*.wav" 2>/dev/null | wc -l | tr -d ' ')
    AUG_SIZE=$(du -sh augmented_audio 2>/dev/null | cut -f1)
    echo -e "${GREEN}✓ Augmented audio: $AUG_COUNT files ($AUG_SIZE)${NC}"
else
    echo -e "${YELLOW}⚠️  augmented_audio/ not found (may have been cleaned up)${NC}"
fi

echo ""

# Test API endpoints
echo "================================================================"
echo -e "${YELLOW}Step 5: Testing API Endpoints${NC}"
echo "================================================================"
echo ""

echo "Testing /status endpoint..."
STATUS=$(curl -s http://localhost:8000/status)
echo "Response: $STATUS"
echo ""

echo "Testing /classes endpoint..."
CLASSES=$(curl -s http://localhost:8000/classes)
echo "Response: $CLASSES"
echo ""

# Summary
echo "================================================================"
echo -e "${GREEN}✅ LOCAL TESTING COMPLETE${NC}"
echo "================================================================"
echo ""
echo "Services running:"
echo "  • API:        http://localhost:8000"
echo "  • UI:         http://localhost:8501"
echo "  • Nginx:      http://localhost:80"
echo ""
echo "Test the UI:"
echo "  Open browser: http://localhost:8501"
echo ""
echo "View logs:"
echo "  docker compose -f deployment/docker-compose.yml logs -f api"
echo ""
echo "Stop services:"
echo "  docker compose -f deployment/docker-compose.yml down"
echo ""
echo "================================================================"
echo ""
