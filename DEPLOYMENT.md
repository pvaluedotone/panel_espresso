# Deploying Panel Espresso to Google Cloud Run

This guide will walk you through deploying the Panel Espresso application to Google Cloud Run, making it accessible through your custom domain.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup Guide](#detailed-setup-guide)
4. [Custom Domain Configuration](#custom-domain-configuration)
5. [Environment Configuration](#environment-configuration)
6. [Troubleshooting](#troubleshooting)
7. [Cost Optimization](#cost-optimization)

---

## Prerequisites

Before you begin, ensure you have:

1. **Google Cloud Account**: [Sign up here](https://cloud.google.com/free) (includes $300 free credit)
2. **Google Cloud SDK (gcloud CLI)**: [Install here](https://cloud.google.com/sdk/docs/install)
3. **Docker** (optional, for local testing): [Install Docker](https://docs.docker.com/get-docker/)
4. **A domain name**: For custom domain access
5. **Project files**: Clone this repository

---

## Quick Start

For experienced users, here's the fastest way to deploy:

```bash
# 1. Set up Google Cloud project
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com

# 2. Build and deploy with Cloud Build
gcloud builds submit --config cloudbuild.yaml

# 3. Get the service URL
gcloud run services describe panel-espresso --region=us-central1 --format='value(status.url)'
```

That's it! Your app is now live. Continue reading for custom domain setup.

---

## Detailed Setup Guide

### Step 1: Set Up Google Cloud Project

1. **Create a new Google Cloud project** (or use an existing one):
   ```bash
   # Create a new project
   gcloud projects create YOUR_PROJECT_ID --name="Panel Espresso"
   
   # Set as active project
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable billing** for your project:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Navigate to Billing and link a billing account
   - Or use: `gcloud beta billing projects link YOUR_PROJECT_ID --billing-account=BILLING_ACCOUNT_ID`

3. **Enable required APIs**:
   ```bash
   gcloud services enable \
     run.googleapis.com \
     containerregistry.googleapis.com \
     cloudbuild.googleapis.com \
     compute.googleapis.com
   ```

### Step 2: Configure the Application

1. **Update app.py launch settings** (if needed):
   
   The app is already configured for Cloud Run with these settings in `app.py`:
   ```python
   demo.launch(
       share=False, 
       server_name="0.0.0.0",  # Listen on all interfaces
       server_port=8080,        # Cloud Run default port
       inbrowser=False          # Don't open browser in container
   )
   ```

2. **Review Dockerfile**:
   
   The provided `Dockerfile` is optimized for Cloud Run. Key features:
   - Uses Python 3.11 slim image for smaller size
   - Installs dependencies via `uv` for fast builds
   - Exposes port 8080 (Cloud Run requirement)
   - Includes health check endpoint

### Step 3: Build and Deploy

#### Option A: Using Cloud Build (Recommended)

Cloud Build automatically builds and deploys your app in the cloud:

```bash
# From the project root directory
gcloud builds submit --config cloudbuild.yaml
```

This command:
- Builds your Docker image in the cloud
- Pushes it to Google Container Registry
- Deploys to Cloud Run
- Takes ~5-10 minutes for first deployment

#### Option B: Manual Deployment

If you prefer more control:

```bash
# 1. Build the Docker image
docker build -t gcr.io/YOUR_PROJECT_ID/panel-espresso:latest .

# 2. Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/panel-espresso:latest

# 3. Deploy to Cloud Run
gcloud run deploy panel-espresso \
  --image gcr.io/YOUR_PROJECT_ID/panel-espresso:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --port 8080
```

#### Option C: Local Testing First

Test the Docker container locally before deploying:

```bash
# Build the image
docker build -t panel-espresso-local .

# Run locally
docker run -p 8080:8080 panel-espresso-local

# Access at http://localhost:8080
# If it works, deploy using Option A or B
```

### Step 4: Verify Deployment

1. **Get your Cloud Run URL**:
   ```bash
   gcloud run services describe panel-espresso \
     --region=us-central1 \
     --format='value(status.url)'
   ```

2. **Test the application**:
   ```bash
   # Replace with your actual URL
   curl https://panel-espresso-XXXXX-uc.a.run.app
   ```

3. **View logs** (if needed):
   ```bash
   gcloud run services logs read panel-espresso --region=us-central1
   ```

---

## Custom Domain Configuration

To access your app via your own domain (e.g., `panel.yourdomain.com`):

### Step 1: Map Domain to Cloud Run

1. **Add domain mapping**:
   ```bash
   gcloud run domain-mappings create \
     --service panel-espresso \
     --domain panel.yourdomain.com \
     --region us-central1
   ```

2. **Get DNS records**:
   ```bash
   gcloud run domain-mappings describe \
     --domain panel.yourdomain.com \
     --region us-central1
   ```

   This will show you the DNS records to add (usually CNAME or A records).

### Step 2: Configure Your DNS Provider

Add the DNS records shown in Step 1 to your domain registrar (e.g., Google Domains, Cloudflare, GoDaddy):

**Example CNAME record**:
- **Name/Host**: `panel` (for panel.yourdomain.com)
- **Type**: `CNAME`
- **Value**: `ghs.googlehosted.com`
- **TTL**: `3600` (or default)

**Example A record** (if CNAME not provided):
- **Name/Host**: `panel`
- **Type**: `A`
- **Value**: The IP address provided by Google Cloud
- **TTL**: `3600`

### Step 3: Wait for SSL Certificate

Google Cloud automatically provisions a free SSL certificate:
- Initial provisioning: 15-60 minutes
- Check status:
  ```bash
  gcloud run domain-mappings describe \
    --domain panel.yourdomain.com \
    --region us-central1
  ```

### Step 4: Verify HTTPS Access

Once the SSL certificate is ready (status: `ACTIVE`):
```bash
# Test your domain
curl https://panel.yourdomain.com
```

Your app is now accessible at `https://panel.yourdomain.com` 🎉

---

## Environment Configuration

### Resource Settings

Adjust resources based on your needs in `cloudbuild.yaml`:

```yaml
# Memory: 256Mi to 32Gi
--memory 2Gi

# CPU: 1, 2, 4, 6, 8
--cpu 2

# Timeout: Max request duration (seconds)
--timeout 300

# Instances: Auto-scaling limits
--max-instances 10
--min-instances 0  # Set to 1+ to avoid cold starts
```

### Authentication

By default, the app is publicly accessible. To require authentication:

1. **Deploy with authentication**:
   ```bash
   gcloud run deploy panel-espresso \
     --image gcr.io/YOUR_PROJECT_ID/panel-espresso:latest \
     --no-allow-unauthenticated \
     --region us-central1
   ```

2. **Grant access to specific users**:
   ```bash
   gcloud run services add-iam-policy-binding panel-espresso \
     --region=us-central1 \
     --member='user:email@example.com' \
     --role='roles/run.invoker'
   ```

### Environment Variables

To add environment variables (e.g., for configuration):

```bash
gcloud run services update panel-espresso \
  --region us-central1 \
  --set-env-vars "KEY1=value1,KEY2=value2"
```

---

## Troubleshooting

### Common Issues

#### 1. Build Fails

**Error**: `Dependency installation failed`

**Solution**: Check `pyproject.toml` and `uv.lock` are up to date:
```bash
# Locally update dependencies
uv sync
git add pyproject.toml uv.lock
git commit -m "Update dependencies"
gcloud builds submit --config cloudbuild.yaml
```

#### 2. App Won't Start

**Error**: `Container failed to start`

**Solution**: Check logs:
```bash
gcloud run services logs read panel-espresso --region=us-central1 --limit=50
```

Common fixes:
- Ensure port 8080 is exposed
- Verify `app.py` has correct launch settings
- Check for missing dependencies

#### 3. Timeout Errors

**Error**: `Request deadline exceeded`

**Solution**: Increase timeout:
```bash
gcloud run services update panel-espresso \
  --region us-central1 \
  --timeout 600  # 10 minutes
```

#### 4. Domain Not Working

**Error**: `SSL certificate not ready` or `Domain not found`

**Solution**:
1. Verify DNS records are correct (use `nslookup panel.yourdomain.com`)
2. Wait 15-60 minutes for SSL provisioning
3. Check domain mapping status:
   ```bash
   gcloud run domain-mappings describe \
     --domain panel.yourdomain.com \
     --region us-central1
   ```

#### 5. Out of Memory

**Error**: `Container killed due to memory limit`

**Solution**: Increase memory:
```bash
gcloud run services update panel-espresso \
  --region us-central1 \
  --memory 4Gi
```

### Viewing Real-Time Logs

```bash
# Stream logs in real-time
gcloud run services logs tail panel-espresso --region=us-central1

# Filter by severity
gcloud run services logs read panel-espresso \
  --region=us-central1 \
  --filter="severity>=ERROR"
```

---

## Cost Optimization

Cloud Run pricing is based on:
- **CPU and memory** allocated
- **Request count** and **duration**
- **Network egress**

### Estimate Costs

For moderate usage (1000 requests/day, 2GB RAM, 2 CPU):
- **Free tier**: First 2 million requests/month
- **Estimated**: $0-$10/month for typical academic/research use

**Check current pricing**: [Cloud Run Pricing](https://cloud.google.com/run/pricing)

### Cost-Saving Tips

1. **Scale to zero**: Use `--min-instances 0` to avoid charges when idle
   ```bash
   gcloud run services update panel-espresso \
     --region us-central1 \
     --min-instances 0
   ```

2. **Right-size resources**: Start small and scale up if needed
   ```bash
   # For light usage
   --memory 1Gi --cpu 1
   
   # For heavy analysis
   --memory 4Gi --cpu 4
   ```

3. **Set max instances**: Prevent runaway costs
   ```bash
   --max-instances 5
   ```

4. **Monitor usage**: Set up budget alerts in Google Cloud Console
   - Go to Billing → Budgets & Alerts
   - Create alert at $10, $25, $50, etc.

5. **Use Cloud Run Jobs** for batch processing (if applicable):
   - Process uploaded datasets asynchronously
   - Only pay for actual computation time

---

## Advanced Configuration

### Custom Startup Command

Modify the `CMD` in `Dockerfile`:

```dockerfile
# Default
CMD ["python", "app.py"]

# With custom workers (if using Gunicorn)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
```

### Add Secrets

For sensitive data (API keys, credentials):

```bash
# Create secret
echo -n "your-secret-value" | \
  gcloud secrets create my-secret --data-file=-

# Grant access to Cloud Run
gcloud secrets add-iam-policy-binding my-secret \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Mount secret
gcloud run services update panel-espresso \
  --region us-central1 \
  --set-secrets="SECRET_KEY=my-secret:latest"
```

### Enable Cloud Storage Integration

For persisting user uploads across container restarts:

```bash
# Create bucket
gsutil mb -l us-central1 gs://YOUR_PROJECT_ID-panel-data

# Update app.py to use Cloud Storage
# (requires code changes to use Google Cloud Storage SDK)

# Grant access
gcloud run services add-iam-policy-binding panel-espresso \
  --region=us-central1 \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@developer.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

---

## Updating Your Deployment

### Deploy New Version

```bash
# After making code changes
git add .
git commit -m "Update application"
gcloud builds submit --config cloudbuild.yaml
```

Cloud Run will:
1. Build new image with updated code
2. Deploy with zero-downtime rollout
3. Automatically route traffic to new version

### Rollback to Previous Version

```bash
# List revisions
gcloud run revisions list --service panel-espresso --region us-central1

# Rollback to specific revision
gcloud run services update-traffic panel-espresso \
  --region us-central1 \
  --to-revisions=panel-espresso-XXXXX=100
```

---

## Security Best Practices

1. **Enable authentication** for sensitive data
2. **Use HTTPS only** (Cloud Run enforces this automatically)
3. **Implement request size limits** in `app.py`
4. **Validate file uploads** to prevent malicious files
5. **Set up VPC connector** for private database access (if needed)
6. **Regular dependency updates**: Run `uv sync` and redeploy monthly

---

## Monitoring and Alerts

### Set Up Monitoring

1. **Go to Cloud Console** → Cloud Run → panel-espresso → Metrics
2. **Monitor**:
   - Request count
   - Request latency
   - Container instance count
   - Memory utilization
   - CPU utilization

### Create Alerts

```bash
# Alert on high error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error Rate > 5%" \
  --condition-threshold-value=0.05
```

---

## Support and Resources

### Official Documentation
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Domain Mapping Guide](https://cloud.google.com/run/docs/mapping-custom-domains)

### Community Support
- [Stack Overflow - google-cloud-run](https://stackoverflow.com/questions/tagged/google-cloud-run)
- [Google Cloud Community](https://www.googlecloudcommunity.com/)

### Getting Help
- Check logs: `gcloud run services logs read panel-espresso --region=us-central1`
- Review [troubleshooting guide](#troubleshooting)
- Open an issue in this repository

---

## Summary

You've successfully deployed Panel Espresso to Google Cloud Run! Here's what you accomplished:

✅ Containerized the application with Docker  
✅ Deployed to Google Cloud Run  
✅ Set up auto-scaling and HTTPS  
✅ (Optional) Configured custom domain  
✅ Optimized for cost and performance  

Your panel data analysis app is now accessible worldwide at:
- **Cloud Run URL**: `https://panel-espresso-XXXXX-uc.a.run.app`
- **Custom Domain**: `https://panel.yourdomain.com` (if configured)

**Next Steps**:
1. Share the URL with users
2. Monitor usage and costs
3. Set up billing alerts
4. Configure backups for important analyses
5. Consider adding authentication for sensitive data

Happy analyzing! 📊✨
