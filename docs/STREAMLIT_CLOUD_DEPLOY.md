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
