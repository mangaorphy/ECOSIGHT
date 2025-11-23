# Render Deployment Checklist

## Pre-Deployment

- [ ] All code committed and pushed to GitHub
- [ ] S3 bucket exists: `ecosight-training-data`
- [ ] Initial audio uploaded to S3 `extracted_audio/` folder
- [ ] AWS credentials ready (Access Key ID + Secret Key)

## Render Setup

- [ ] Create new Web Service on Render
- [ ] Connect to GitHub repository: `mangaorphy/ECOSIGHT`
- [ ] Configure as Docker service
- [ ] Add environment variables:
  - [ ] `S3_BUCKET=ecosight-training-data`
  - [ ] `AWS_ACCESS_KEY_ID=<your-key>`
  - [ ] `AWS_SECRET_ACCESS_KEY=<your-secret>`
  - [ ] `AWS_REGION=us-east-1`

## Post-Deployment Testing

- [ ] Check service status: `curl https://your-app.onrender.com/status`
- [ ] Test file upload:
  ```bash
  curl -X POST "https://your-app.onrender.com/upload" \
    -F "file=@test.wav" \
    -F "class_name=gun_shot"
  ```
- [ ] Verify S3 upload worked: Check `"s3_uploaded": true` in response
- [ ] Verify file in S3:
  ```bash
  aws s3 ls s3://ecosight-training-data/extracted_audio/gun_shot/
  ```
- [ ] Test prediction endpoint with sample audio
- [ ] Trigger test retraining (optional):
  ```bash
  curl -X POST "https://your-app.onrender.com/retrain"
  ```

## Verification

- [ ] Logs show: "✓ File uploaded to S3"
- [ ] No errors in Render logs
- [ ] API responds to all endpoints
- [ ] Model loads successfully
- [ ] Can access via Render URL

## Done! 🎉

Your app is live and automatically saving all uploads to S3!

Next steps:
- Share URL with team/users
- Monitor uploads in S3 console
- Schedule periodic retraining as data grows
