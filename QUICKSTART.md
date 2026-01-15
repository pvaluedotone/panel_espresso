# Quick Deployment Guide for Panel Espresso on pvalue.one

## Prerequisites
- Google Cloud account with billing enabled
- `gcloud` CLI installed
- Domain: pvalue.one

## 🚀 Deploy in 5 Minutes

### Option 1: Automated Script (Easiest)

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh YOUR_PROJECT_ID us-central1

# Follow prompts
```

### Option 2: Manual Commands

```bash
# 1. Set your project
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# 2. Enable required APIs
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com

# 3. Deploy application
gcloud builds submit --config cloudbuild.yaml

# 4. Get your app URL
gcloud run services describe panel-espresso --region=us-central1 --format='value(status.url)'
```

## 🌐 Connect Your Domain (panel.pvalue.one)

### Step 1: Map Domain
```bash
gcloud run domain-mappings create \
  --service panel-espresso \
  --domain panel.pvalue.one \
  --region us-central1
```

### Step 2: Get DNS Instructions
```bash
gcloud run domain-mappings describe \
  --domain panel.pvalue.one \
  --region us-central1
```

### Step 3: Add DNS Record

Add this CNAME record at your domain registrar:

| Field | Value |
|-------|-------|
| **Type** | CNAME |
| **Host/Name** | panel |
| **Target/Value** | ghs.googlehosted.com |
| **TTL** | 3600 (or Auto) |

**Important**: If using Cloudflare, set proxy status to "DNS only" (gray cloud)

### Step 4: Wait for SSL Certificate

- Time: 15-60 minutes
- Check status: `gcloud run domain-mappings describe --domain panel.pvalue.one --region us-central1`
- Look for: `certificateStatus: ACTIVE`

### Step 5: Test

```bash
curl https://panel.pvalue.one
# Or open in browser
```

## 📊 Your App URLs

- **Cloud Run**: `https://panel-espresso-xxxxx-uc.a.run.app` (after step 3 above)
- **Custom Domain**: `https://panel.pvalue.one` (after DNS setup)

## 🔄 Update Deployment

```bash
# After making code changes
git pull
gcloud builds submit --config cloudbuild.yaml
```

## 📝 Important Files

- `Dockerfile` - Container definition
- `cloudbuild.yaml` - Build and deployment config
- `requirements.txt` - Python dependencies
- `deploy.sh` - Automated deployment script
- `DEPLOYMENT.md` - Complete guide
- `DOMAIN_SETUP_pvalue.one.md` - Domain-specific guide

## 🆘 Troubleshooting

### Build Fails
```bash
# View build logs
gcloud builds list --limit=1
gcloud builds log BUILD_ID
```

### App Won't Start
```bash
# View service logs
gcloud run services logs read panel-espresso --region=us-central1 --limit=50
```

### Domain Issues
```bash
# Check DNS propagation
nslookup panel.pvalue.one

# Check SSL status
gcloud run domain-mappings describe --domain panel.pvalue.one --region us-central1
```

### Common Fixes

1. **"Permission denied"** → Enable billing in Cloud Console
2. **"Service not found"** → Check region (use us-central1)
3. **"DNS verification failed"** → Wait 10-15 minutes, CNAME must be exact
4. **"SSL pending"** → Normal, wait up to 60 minutes

## 💰 Cost Estimate

- **Free tier**: First 2 million requests/month
- **Typical usage**: $0-10/month
- **Heavy usage**: $20-50/month

Set up billing alerts:
```bash
# In Cloud Console → Billing → Budgets & Alerts
# Create alerts at $10, $25, $50
```

## 🔒 Security Options

### Enable Authentication
```bash
gcloud run services update panel-espresso \
  --region us-central1 \
  --no-allow-unauthenticated
```

### Grant Access to Specific Users
```bash
gcloud run services add-iam-policy-binding panel-espresso \
  --region=us-central1 \
  --member='user:email@example.com' \
  --role='roles/run.invoker'
```

## 📈 Monitoring

### View Metrics
Go to: https://console.cloud.google.com/run → panel-espresso → Metrics

### Stream Logs
```bash
gcloud run services logs tail panel-espresso --region=us-central1
```

### Set Up Alerts
```bash
# Create uptime check
gcloud monitoring uptime create \
  --display-name="Panel Espresso" \
  --resource-type="uptime-url" \
  --url="https://panel.pvalue.one"
```

## ✅ Deployment Checklist

- [ ] Google Cloud project created with billing
- [ ] `gcloud` CLI installed and authenticated
- [ ] Run `./deploy.sh PROJECT_ID` or manual deployment
- [ ] App accessible at Cloud Run URL
- [ ] CNAME record added for panel.pvalue.one
- [ ] SSL certificate active (wait 15-60 min)
- [ ] App accessible at https://panel.pvalue.one
- [ ] Billing alerts configured
- [ ] Monitoring set up

## 📚 Full Documentation

- **Complete Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Domain Setup**: [DOMAIN_SETUP_pvalue.one.md](DOMAIN_SETUP_pvalue.one.md)
- **Google Cloud Run Docs**: https://cloud.google.com/run/docs

## 🎉 Success!

Once complete, your Panel Espresso app will be:
- ✅ Running on Google Cloud Run
- ✅ Auto-scaling based on traffic
- ✅ Secured with HTTPS
- ✅ Accessible at https://panel.pvalue.one

Share the URL with users and enjoy your deployed panel data analysis app!
