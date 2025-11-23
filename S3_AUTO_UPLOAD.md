# S3 Auto-Upload Quick Reference

## ✅ Yes, Uploads Are Automatically Saved to S3

When you upload audio via Render, the API automatically:
1. Saves to local `extracted_audio/` folder
2. **Uploads to S3** `s3://ecosight-training-data/extracted_audio/`
3. Returns confirmation with `"s3_uploaded": true`

## Setup on Render

### Add Environment Variables
In Render Dashboard → Your Service → Environment:

```
S3_BUCKET=ecosight-training-data
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
AWS_REGION=us-east-1
```

## How It Works

### Upload Request
```bash
curl -X POST "https://ecosight-api.onrender.com/upload" \
  -F "file=@gunshot.wav" \
  -F "class_name=gun_shot"
```

### What Happens
```
1. API receives file
2. Saves to /app/extracted_audio/gun_shot/20251123_165432_gunshot.wav
3. Uploads to s3://ecosight-training-data/extracted_audio/gun_shot/20251123_165432_gunshot.wav
4. Returns success response
```

### Response
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file_path": "/app/extracted_audio/gun_shot/20251123_165432_gunshot.wav",
  "class": "gun_shot",
  "s3_uploaded": true,  ← Confirms S3 upload worked
  "timestamp": "2025-11-23T16:54:32"
}
```

## Verify S3 Upload

### Check via AWS CLI
```bash
# List recent uploads
aws s3 ls s3://ecosight-training-data/extracted_audio/gun_shot/ \
  --human-readable | tail -10

# Count total files
aws s3 ls s3://ecosight-training-data/extracted_audio/ \
  --recursive | wc -l
```

### Check via AWS Console
1. Go to https://s3.console.aws.amazon.com
2. Open bucket: `ecosight-training-data`
3. Navigate to: `extracted_audio/<class>/`
4. See your uploaded files

## Retraining Uses S3 Files

When you trigger retraining:
```bash
curl -X POST "https://ecosight-api.onrender.com/retrain"
```

The system:
1. **Downloads ALL files** from `s3://bucket/extracted_audio/`
2. **Applies augmentation** (1 file → 6 files)
3. **Trains model** on augmented data
4. **Saves new model** to Render persistent disk

## Storage Locations

| What | Where | Persistent? |
|------|-------|-------------|
| **Original uploads** | S3 `extracted_audio/` | ✅ Permanent |
| **Original uploads** | Render `extracted_audio/` | ❌ Temporary |
| **Augmented files** | Generated during retraining | ❌ Deleted after |
| **Trained model** | Render `models/` | ✅ Persistent disk |

## Cost
- **S3 storage**: ~$0.04/month for 1.7GB
- **S3 requests**: Negligible (~$0.001/month)
- **Total**: Less than $0.05/month

## Troubleshooting

### If `"s3_uploaded": false`
1. Check Render environment variables are set
2. Verify AWS credentials are correct
3. Check AWS IAM permissions (needs `s3:PutObject`)
4. Look at logs: "S3 upload failed: <error>"

### Files still saved locally
Yes! Even if S3 upload fails, file is saved locally to `extracted_audio/`. The upload continues gracefully - S3 is a backup, not required for basic operation.

## Key Takeaways

✅ **All uploads automatically go to S3** (when credentials configured)  
✅ **Retraining uses S3 as source** (downloads originals, augments, trains)  
✅ **Cost-efficient** (stores originals only, ~$0.04/month)  
✅ **Reliable** (S3 provides 99.999999999% durability)  
✅ **No manual steps needed** (fully automatic after env vars set)
