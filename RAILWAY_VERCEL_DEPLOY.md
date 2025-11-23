# Deploy API to Railway + UI to Vercel

## Why This Approach?

- **Railway** (API): Better free tier, no sleep, handles ML models well
- **Vercel** (UI): Free unlimited deployments, fast, easy Streamlit support
- **Total Cost**: $0/month (within free tiers)

---

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

## Part 2: Deploy UI to Vercel

### 1. Create Vercel Account
- Go to https://vercel.com
- Sign up with GitHub

### 2. Install Vercel CLI (Optional - or use dashboard)
```bash
npm i -g vercel
```

### 3. Deploy from GitHub
- Click "Add New Project"
- Import `mangaorphy/ECOSIGHT`
- Framework Preset: **Other**
- Root Directory: `/`

### 4. Configure Build Settings

**Build Command:**
```bash
pip install -r config/requirements-ui.txt
```

**Start Command:**
```bash
streamlit run src/app.py --server.port $PORT
```

**Note:** UI uses lightweight requirements (no TensorFlow) since it only makes API calls.

### 5. Add Environment Variables
In Vercel project settings → Environment Variables:

```bash
API_URL=https://ecosight-api-production.up.railway.app
PORT=8501
```
(Replace with your actual Railway API URL)

### 6. Deploy
- Click "Deploy"
- Vercel will give you a URL like: `https://ecosight.vercel.app`

---

## Part 3: Test the Deployment

### Test API
```bash
curl https://your-railway-url.railway.app/status
```

Should return:
```json
{
  "status": "operational",
  "model_loaded": true,
  ...
}
```

### Test UI
- Open your Vercel URL
- UI should connect to Railway API
- Try uploading an audio file

---

## Alternative: Keep API on Render, UI on Vercel

If you prefer to keep the API on Render (already deployed):

### Just Deploy UI to Vercel

**Environment Variables:**
```bash
API_URL=https://ecosight-api.onrender.com
PORT=8501
```

**Pros:**
- API already working on Render
- Just need to deploy UI

**Cons:**
- Render free tier sleeps after 15min inactivity
- First request takes ~30s to wake up

---

## Cost Comparison

| Platform | Service | Free Tier | Sleep? | Cost |
|----------|---------|-----------|--------|------|
| Railway | API | $5/month credit | No | $0 |
| Vercel | UI | Unlimited | No | $0 |
| Render (Free) | API | 750hrs/month | Yes (15min) | $0 |
| Render (Starter) | API | Always on | No | $7/month |

**Recommended:** Railway (API) + Vercel (UI) = $0/month, no sleep, fast

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

### Deploy to Vercel (CLI method)
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod

# Set environment variable
vercel env add API_URL production
# Enter your Railway API URL when prompted
```

---

## Troubleshooting

### API not responding
- Check Railway logs: `railway logs`
- Verify S3 credentials are set
- Check health: `curl https://your-url/status`

### UI can't connect to API
- Verify `API_URL` environment variable in Vercel
- Check CORS settings in API
- Test API directly with curl

### Model not loading
- Railway logs should show "Model downloaded from S3"
- Verify S3 credentials
- Check model exists: `aws s3 ls s3://ecosight-training-data/models/`

---

## Need Help?

- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- Railway Discord: https://discord.gg/railway
