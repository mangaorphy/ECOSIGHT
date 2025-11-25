# Deploy API to Railway + UI to Streamlit

## Part 1: Deploy API to Railway

### 1. Create Railway Account
- Go to https://railway.app
- Sign up with GitHub
- You get $5 free credit/month

### 2. Create New Project
- Click "New Project"
- Select "Deploy from GitHub repo"
- Choose `mangaorphy/ECOSIGHT`
- Railway will auto-detect the Dockerfile

### 3. Add Environment Variables
In Railway dashboard, go to Variables tab and add:

```bash
PORT=8000
PYTHONUNBUFFERED=1
S3_BUCKET=ecosight-training-data
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
AWS_REGION=us-east-1
MODEL_PATH=/app/models/yamnet_classifier_v2.keras
```

**Get your AWS credentials from:** `~/.aws/credentials`

### 4. Configure Build
- Root Directory: `/`
- Dockerfile Path: `deployment/Dockerfile`
- Click "Deploy"

### 5. Get Your API URL
- After deployment, Railway gives you a URL like: `https://ecosight-api-production.up.railway.app`
- **Copy this URL** - you'll need it for the UI

---

## Quick Start Commands

### Deploy to Railway (CLI method)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to project (or create new)
railway init

# Add environment variables
railway variables set S3_BUCKET=ecosight-training-data
railway variables set AWS_ACCESS_KEY_ID=<your-aws-access-key>
railway variables set AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
railway variables set AWS_REGION=us-east-1

# Deploy
railway up
```