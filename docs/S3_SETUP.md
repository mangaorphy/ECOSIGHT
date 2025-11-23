# AWS S3 Setup Guide for EcoSight Training Data

This guide shows you how to store your training audio files in AWS S3 so they're available when retraining on Render.

---

## 📋 **Prerequisites**

1. **AWS Account** - Already set up ✓
2. **AWS CLI configured** - Already done ✓
3. **Training audio files** - In `augmented_audio/` folder ✓

---

## 🚀 **Quick Setup (3 Steps)**

### **Step 1: Upload Training Data to S3**

```bash
chmod +x scripts/upload-to-s3.sh
./scripts/upload-to-s3.sh
```

This will:
- Create S3 bucket: `ecosight-training-data`
- Upload all `.wav` files from `augmented_audio/`
- Show confirmation with file count

**Expected Output:**
```
✓ Bucket created: ecosight-training-data
Found 10 audio files to upload
✓ Audio files uploaded to S3
```

---

### **Step 2: Get AWS Credentials for Render**

You need to give Render access to your S3 bucket. Get your AWS credentials:

```bash
aws configure list
```

Or create new access keys:
1. Go to AWS Console → IAM → Users → Your user
2. **Security credentials** tab
3. **Create access key** → Choose **Application running outside AWS**
4. Copy the **Access Key ID** and **Secret Access Key**

---

### **Step 3: Configure Render with S3 Credentials**

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on your **ecosight-api** service
3. Go to **Environment** tab
4. Add these environment variables:

| Variable Name | Value |
|--------------|-------|
| `S3_BUCKET` | `ecosight-training-data` |
| `AWS_ACCESS_KEY_ID` | Your AWS access key from Step 2 |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key from Step 2 |
| `AWS_REGION` | `us-east-1` |

5. Click **Save Changes**
6. Service will automatically redeploy

---

## ✅ **How It Works**

### **Before (Without S3):**
```
Render Container
├── api.py
├── model.keras
└── augmented_audio/  ❌ EMPTY!
```

### **After (With S3):**
```
When retraining starts:
1. Download audio from S3 → local container
2. Train model with downloaded audio
3. Save new model

Render Container
├── api.py
├── model.keras
└── augmented_audio/  ✓ Downloaded from S3
    ├── dog_bark/
    ├── gun_shot/
    ├── clips/
    └── engine_idling/
```

---

## 🔄 **Adding New Training Data**

When you collect more audio samples:

1. **Save locally** to `augmented_audio/` folder
2. **Upload to S3**:
   ```bash
   ./scripts/upload-to-s3.sh
   ```
3. **Trigger retraining** via API or Streamlit UI
4. Retraining will download latest audio from S3 automatically

---

## 💰 **S3 Costs**

### **Free Tier (First 12 Months):**
- ✅ 5 GB storage
- ✅ 20,000 GET requests/month
- ✅ 2,000 PUT requests/month

### **Your Current Usage:**
- Audio files: ~1.6 MB (well within 5 GB limit!)
- Downloads per retrain: ~10 files
- **Cost: $0** (within free tier)

### **After Free Tier:**
- Storage: $0.023 per GB/month
- Your cost: ~$0.04/month for 1.6 MB

---

## 🧪 **Testing S3 Integration**

### **1. Verify Upload:**
```bash
aws s3 ls s3://ecosight-training-data/augmented_audio/ --recursive
```

Should show all your audio files.

### **2. Test Download (Locally):**
```python
from src.s3_storage import get_s3_storage

s3 = get_s3_storage()
success = s3.download_training_data("./test_download")
print(f"Download successful: {success}")
```

### **3. Test on Render:**
1. Go to your Streamlit UI: https://ecosight-ui.onrender.com
2. Navigate to **Training** tab
3. Click **Retrain Model**
4. Check logs - should see: `✓ Downloaded X training audio files from S3`

---

## 🔍 **Viewing S3 Contents**

### **Via Command Line:**
```bash
# List all files
aws s3 ls s3://ecosight-training-data/augmented_audio/ --recursive

# Show bucket size
aws s3 ls s3://ecosight-training-data --recursive --summarize --human-readable

# Download everything to local (for backup)
aws s3 sync s3://ecosight-training-data/augmented_audio/ ./backup_audio/
```

### **Via AWS Console:**
1. Go to [S3 Console](https://s3.console.aws.amazon.com/s3/)
2. Click on `ecosight-training-data` bucket
3. Navigate to `augmented_audio/` folder
4. See all your audio files organized by class

---

## 🔐 **Security Best Practices**

✅ **Already Implemented:**
- Bucket is **private** (not public)
- Only accessible with your AWS credentials
- Credentials stored securely in Render (encrypted)

✅ **Additional Security (Optional):**
- Use IAM role with limited permissions (S3 read-only for Render)
- Enable bucket versioning (recover deleted files)
- Set lifecycle rules (auto-delete old files after X days)

---

## 🛠️ **Manual S3 Operations**

### **Upload Single File:**
```bash
aws s3 cp augmented_audio/dog_bark/new_sample.wav \
  s3://ecosight-training-data/augmented_audio/dog_bark/new_sample.wav
```

### **Download Specific Class:**
```bash
aws s3 sync s3://ecosight-training-data/augmented_audio/dog_bark/ \
  ./local_dogbark/
```

### **Delete Old Files:**
```bash
aws s3 rm s3://ecosight-training-data/augmented_audio/dog_bark/old_file.wav
```

---

## 📊 **Monitoring S3 Usage**

### **Check Storage Size:**
```bash
aws s3 ls s3://ecosight-training-data --recursive --summarize --human-readable | tail -2
```

### **List Recently Added Files:**
```bash
aws s3api list-objects-v2 \
  --bucket ecosight-training-data \
  --prefix augmented_audio/ \
  --query 'sort_by(Contents, &LastModified)[-10:].[Key, LastModified, Size]' \
  --output table
```

---

## ❌ **Troubleshooting**

### **Error: "Access Denied"**
**Solution:** Check AWS credentials in Render environment variables

### **Error: "Bucket does not exist"**
**Solution:** Run `./scripts/upload-to-s3.sh` to create bucket

### **Retraining shows "No training data"**
**Solution:** 
1. Verify S3 has files: `aws s3 ls s3://ecosight-training-data/augmented_audio/ --recursive`
2. Check Render logs for S3 download errors
3. Verify AWS credentials are set in Render

### **Download is slow**
**Solution:** 
- Normal for first download
- Subsequent retrains use same files if available
- Consider caching in Render persistent disk (paid feature)

---

## 🎯 **Next Steps**

After setting up S3:

1. ✅ Upload training data: `./scripts/upload-to-s3.sh`
2. ✅ Add S3 credentials to Render
3. ✅ Test retraining via Streamlit UI
4. ✅ Monitor S3 costs (should be $0 for your usage)
5. ✅ Set up automated backups (optional)

---

## 📚 **Additional Resources**

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [AWS Free Tier Details](https://aws.amazon.com/free/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Render Environment Variables](https://render.com/docs/environment-variables)

---

**Need Help?** Check CloudWatch logs in Render dashboard or AWS S3 console for error details.
