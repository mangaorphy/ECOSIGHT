# Deploy UI to Streamlit Cloud (Free & Easy!)

## Why Streamlit Cloud?

Vercel doesn't support long-running apps like Streamlit. **Streamlit Cloud** is:
- ✅ **Free forever** for public repos
- ✅ **Built for Streamlit** (obviously!)
- ✅ **Auto-deploys** from GitHub
- ✅ **No configuration** needed
- ✅ **Always on** (no sleep)

---

## Deploy in 3 Minutes

### 1. Go to Streamlit Cloud
- Visit: https://share.streamlit.io
- Click "Sign in with GitHub"

### 2. Create New App
- Click "New app"
- Repository: `mangaorphy/ECOSIGHT`
- Branch: `main`
- Main file path: `src/app.py`

### 3. Advanced Settings (Important!)
Click "Advanced settings" and add:

**Environment Variables:**
```
API_URL=https://ecosight-api-production.up.railway.app
```

### 4. Deploy
- Click "Deploy!"
- Wait ~2 minutes
- Your app will be live at: `https://ecosight.streamlit.app`

---

## That's It! 🎉

Your full stack is now:
- **API**: Railway (https://ecosight-api-production.up.railway.app)
- **UI**: Streamlit Cloud (https://ecosight.streamlit.app)
- **Storage**: AWS S3
- **Total Cost**: $0/month

---

## Alternative: Render for Both API + UI

If you want everything in one place:

### Deploy to Render (Both Services)

**1. API Service (already done)**
- Just add S3 credentials to environment variables

**2. UI Service**
- New Web Service
- Repo: `mangaorphy/ECOSIGHT`
- Build Command: `pip install -r config/requirements-ui.txt`
- Start Command: `streamlit run src/app.py --server.port $PORT --server.address 0.0.0.0`
- Environment Variables:
  - `API_URL=https://ecosight-api.onrender.com`
  - `PORT=8501`

**Pros:**
- Everything in one platform
- Easy to manage

**Cons:**
- UI will also sleep on free tier (30s wake-up)

---

## Recommended Setup

**Best Performance + Cost:**
```
API: Railway ($0/month, no sleep)
UI: Streamlit Cloud ($0/month, no sleep)
Storage: S3 ($0.04/month)
Total: ~$0.04/month
```

**Easiest Management:**
```
API: Render Free ($0/month, sleeps)
UI: Streamlit Cloud ($0/month, no sleep)
Storage: S3 ($0.04/month)
Total: ~$0.04/month
```

---

## Quick Links

- **Streamlit Cloud**: https://share.streamlit.io
- **Railway Dashboard**: https://railway.app/dashboard
- **Render Dashboard**: https://dashboard.render.com
- **Your API**: https://ecosight-api-production.up.railway.app/status

---

## Troubleshooting

### Streamlit app won't start
- Check environment variables are set
- Verify API_URL is correct
- Check Streamlit Cloud logs

### API not responding
- Check Railway logs
- Verify S3 credentials
- Test: `curl https://your-api-url/status`

### UI can't connect to API
- Verify API_URL environment variable
- Check API is responding
- Check CORS settings (already configured)
