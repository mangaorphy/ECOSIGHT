# How to Get AWS Credentials for S3

## Method 1: Check Your Existing AWS CLI Configuration (Fastest)

You already have AWS CLI configured since you uploaded files to S3! Get your credentials:

```bash
# View your AWS access key ID
cat ~/.aws/credentials

# Or if using profiles
cat ~/.aws/config
```

**Output will look like:**
```ini
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
region = us-east-1
```

## Method 2: Get From AWS Console

### Step 1: Log into AWS Console
1. Go to https://console.aws.amazon.com
2. Sign in with your account

### Step 2: Navigate to IAM
1. Search for **IAM** in the top search bar
2. Click **IAM** (Identity and Access Management)

### Step 3: Create Access Key
1. Click **Users** in left sidebar
2. Click on your username (or create new user)
3. Click **Security credentials** tab
4. Scroll to **Access keys** section
5. Click **Create access key**
6. Choose **Application running outside AWS**
7. Click **Next** → **Create access key**

### Step 4: Save Credentials
⚠️ **IMPORTANT**: This is the ONLY time you'll see the secret key!

```
Access key ID: AKIAIOSFODNN7EXAMPLE
Secret access key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**Save these somewhere safe!** (You'll need them for Render)

### Step 5: Set Permissions (If Creating New User)
Your user needs S3 permissions. Attach this policy:

1. Go to **Permissions** tab
2. Click **Add permissions** → **Attach policies directly**
3. Search for **AmazonS3FullAccess** (or create custom policy below)
4. Check the box and click **Add permissions**

## Method 3: Find Existing Credentials in Your Code/Files

Check if you stored them anywhere:

```bash
# Check environment variables
env | grep AWS

# Check bash profile
cat ~/.bash_profile | grep AWS
cat ~/.bashrc | grep AWS
cat ~/.zshrc | grep AWS

# Check AWS config
cat ~/.aws/credentials
```

## What You Need for Render

Copy these 4 values:

```bash
S3_BUCKET=ecosight-training-data
AWS_ACCESS_KEY_ID=AKIA...           ← From Step 3
AWS_SECRET_ACCESS_KEY=wJal...       ← From Step 3
AWS_REGION=us-east-1
```

## Quick Test

Verify your credentials work:

```bash
# Test S3 access
aws s3 ls s3://ecosight-training-data/

# If it lists files, your credentials are working! ✅
```

## For Render Deployment

### Option A: Use Existing Credentials (Recommended)
```bash
# Get from your current AWS config
cat ~/.aws/credentials
```

### Option B: Create New Credentials Just for Render
1. Follow Method 2 above
2. Create new access key
3. Name it "render-ecosight" for tracking
4. Copy the credentials
5. Add to Render environment variables

## Security Best Practices

✅ **DO:**
- Keep credentials secret (never commit to Git)
- Use specific IAM policies (limit to S3 only)
- Rotate keys periodically (every 90 days)
- Delete old/unused keys

❌ **DON'T:**
- Share credentials publicly
- Commit to GitHub
- Use root account keys (create IAM user instead)
- Store in code files

## Custom IAM Policy (More Secure)

Instead of `AmazonS3FullAccess`, use this limited policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::ecosight-training-data",
        "arn:aws:s3:::ecosight-training-data/*"
      ]
    }
  ]
}
```

This only allows:
- Upload files (`PutObject`)
- Download files (`GetObject`)
- List files (`ListBucket`)
- Only for `ecosight-training-data` bucket

## Troubleshooting

### "Credentials not found"
- Check `~/.aws/credentials` exists
- Run `aws configure` to set them up

### "Access Denied" 
- User needs S3 permissions
- Add `AmazonS3FullAccess` policy to IAM user

### "Invalid credentials"
- Key might be deactivated
- Check IAM console → Users → Security credentials
- Create new access key

## Quick Setup Commands

```bash
# 1. Check current credentials
cat ~/.aws/credentials

# 2. If empty, configure AWS CLI
aws configure
# Enter: Access Key ID
# Enter: Secret Access Key
# Enter: Default region (us-east-1)
# Enter: Default output format (json)

# 3. Test it works
aws s3 ls s3://ecosight-training-data/

# 4. Copy credentials for Render
echo "Copy these to Render:"
cat ~/.aws/credentials
```

## Need Help?

If you get stuck:
1. Check AWS CLI is installed: `aws --version`
2. Your S3 upload worked, so credentials exist somewhere
3. Most likely location: `~/.aws/credentials`
4. Or check: `env | grep AWS`
