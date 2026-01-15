# Setting Up Panel Espresso on pvalue.one

This guide provides specific instructions for deploying Panel Espresso to your domain **pvalue.one**.

## Recommended Setup Options

You have several options for how to host Panel Espresso on your domain:

### Option 1: Subdomain (Recommended)
Host at `panel.pvalue.one` or `app.pvalue.one`
- **Pros**: Clean separation, easier SSL management, doesn't affect main site
- **Example**: `https://panel.pvalue.one`

### Option 2: Path-based
Host at `pvalue.one/panel`
- **Pros**: Single domain, unified branding
- **Cons**: Requires additional configuration (reverse proxy)
- **Example**: `https://pvalue.one/panel`

### Option 3: Root Domain
Host at `pvalue.one` (replace main site)
- **Pros**: Shortest URL
- **Cons**: Replaces existing site content
- **Example**: `https://pvalue.one`

**We recommend Option 1** for most use cases.

---

## Step-by-Step Setup for pvalue.one

### Step 1: Deploy to Google Cloud Run

First, deploy the application to Cloud Run:

```bash
# Set your project ID (replace with your actual project ID)
export PROJECT_ID="your-project-id"

# Set project and enable services
gcloud config set project $PROJECT_ID
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com

# Deploy the application
gcloud builds submit --config cloudbuild.yaml

# Get your Cloud Run URL (you'll need this)
gcloud run services describe panel-espresso --region=us-central1 --format='value(status.url)'
```

You should get a URL like: `https://panel-espresso-xxxxx-uc.a.run.app`

### Step 2: Choose Your Domain Setup

#### Option A: Subdomain Setup (panel.pvalue.one) - RECOMMENDED

##### 1. Map the subdomain to Cloud Run

```bash
# Map panel.pvalue.one to your Cloud Run service
gcloud run domain-mappings create \
  --service panel-espresso \
  --domain panel.pvalue.one \
  --region us-central1
```

##### 2. Get DNS configuration

```bash
# Get the DNS records you need to add
gcloud run domain-mappings describe \
  --domain panel.pvalue.one \
  --region us-central1
```

This will show you DNS records like:
```
resourceRecords:
- name: panel.pvalue.one
  rrdata: ghs.googlehosted.com
  type: CNAME
```

##### 3. Update your DNS settings

Log in to your domain registrar (where you manage pvalue.one) and add:

**CNAME Record:**
- **Host/Name**: `panel`
- **Type**: `CNAME`
- **Value/Target**: `ghs.googlehosted.com`
- **TTL**: `3600` (or default)

**Example for common registrars:**

**Google Domains:**
1. Go to [Google Domains](https://domains.google.com)
2. Click on pvalue.one
3. Go to DNS
4. Click "Manage custom records"
5. Add record:
   - Host name: `panel`
   - Type: `CNAME`
   - TTL: `1H`
   - Data: `ghs.googlehosted.com`

**Cloudflare:**
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select pvalue.one
3. Go to DNS → Records
4. Add record:
   - Type: `CNAME`
   - Name: `panel`
   - Target: `ghs.googlehosted.com`
   - Proxy status: ⚠️ **Set to "DNS only" (gray cloud)**
   - TTL: Auto

**GoDaddy:**
1. Go to [GoDaddy DNS Management](https://dcc.godaddy.com/)
2. Find pvalue.one
3. Click DNS → Add
4. Add record:
   - Type: `CNAME`
   - Host: `panel`
   - Points to: `ghs.googlehosted.com`
   - TTL: 1 Hour

**Namecheap:**
1. Go to Domain List → Manage
2. Advanced DNS → Add New Record
3. Add record:
   - Type: `CNAME Record`
   - Host: `panel`
   - Value: `ghs.googlehosted.com`
   - TTL: Automatic

##### 4. Wait for SSL certificate provisioning

Google Cloud automatically provisions a free SSL certificate:
- **Time**: 15-60 minutes
- **Status check**:
  ```bash
  gcloud run domain-mappings describe \
    --domain panel.pvalue.one \
    --region us-central1
  ```

Look for `certificateStatus: ACTIVE`

##### 5. Test your deployment

Once the SSL certificate is active:
```bash
# Test the endpoint
curl https://panel.pvalue.one

# Or just open in browser
open https://panel.pvalue.one
```

✅ **Your app is now live at https://panel.pvalue.one!**

---

#### Option B: Path-based Setup (pvalue.one/panel)

This requires additional infrastructure (load balancer or reverse proxy). 

##### Using Google Cloud Load Balancer:

```bash
# This is more complex and requires:
# 1. Setting up a Load Balancer
# 2. Configuring URL map for /panel path
# 3. Backend service pointing to Cloud Run

# Estimated setup time: 30-60 minutes
# Recommended only if you need multiple services under pvalue.one
```

**We recommend using a subdomain (Option A) instead** for simplicity.

---

#### Option C: Root Domain Setup (pvalue.one)

⚠️ **Warning**: This replaces your existing site at pvalue.one

```bash
# Map root domain
gcloud run domain-mappings create \
  --service panel-espresso \
  --domain pvalue.one \
  --region us-central1

# Get DNS records
gcloud run domain-mappings describe \
  --domain pvalue.one \
  --region us-central1
```

Update DNS with provided A records:
- **Type**: `A`
- **Host**: `@` (or leave blank for root)
- **Value**: IP addresses provided by Google Cloud
- **TTL**: `3600`

You may also need to add `www` subdomain:
```bash
gcloud run domain-mappings create \
  --service panel-espresso \
  --domain www.pvalue.one \
  --region us-central1
```

---

## Verification Checklist

After DNS configuration, verify your setup:

- [ ] DNS records added to registrar
- [ ] Wait 15-60 minutes for propagation
- [ ] SSL certificate status is ACTIVE
- [ ] `https://panel.pvalue.one` loads successfully
- [ ] File upload and analysis work correctly
- [ ] No mixed content warnings

### Troubleshooting DNS

```bash
# Check if DNS has propagated
nslookup panel.pvalue.one

# Check SSL certificate status
gcloud run domain-mappings describe \
  --domain panel.pvalue.one \
  --region us-central1 | grep certificateStatus

# View detailed status
gcloud run domain-mappings describe \
  --domain panel.pvalue.one \
  --region us-central1
```

**Common issues:**

1. **"DNS verification failed"**
   - Double-check CNAME record is exactly `ghs.googlehosted.com`
   - If using Cloudflare, disable proxy (set to DNS only)
   - Wait 10-15 minutes and try again

2. **"SSL certificate pending"**
   - This is normal, wait 15-60 minutes
   - Google automatically provisions Let's Encrypt certificate
   - Check status with command above

3. **"Domain already mapped to another service"**
   - Delete existing mapping first:
     ```bash
     gcloud run domain-mappings delete \
       --domain panel.pvalue.one \
       --region us-central1
     ```

---

## Adding www Subdomain (Optional)

If you want both `panel.pvalue.one` and `www.panel.pvalue.one` to work:

```bash
# Map www subdomain
gcloud run domain-mappings create \
  --service panel-espresso \
  --domain www.panel.pvalue.one \
  --region us-central1
```

Add another CNAME record:
- **Host**: `www.panel`
- **Type**: `CNAME`
- **Value**: `ghs.googlehosted.com`

Or set up a redirect at DNS level from `www.panel.pvalue.one` → `panel.pvalue.one`

---

## Branding and Customization

### Update App Title

Edit `app.py` to customize branding for pvalue.one:

```python
# Around line 1323-1327
gr.Markdown("""
# 📊 Panel Espresso
### Powered by pvalue.one
### Fixed effects and pooled OLS with standard errors clustering
""")
```

### Custom Favicon

Add a favicon for your domain:

1. Create a `favicon.ico` file
2. Place in `/app/` directory in Dockerfile
3. Update Dockerfile:
   ```dockerfile
   COPY favicon.ico .
   ```

---

## Monitoring Your Deployment

### Set Up Uptime Monitoring

```bash
# Create uptime check
gcloud monitoring uptime create \
  --display-name="Panel Espresso Uptime" \
  --resource-type="uptime-url" \
  --url="https://panel.pvalue.one"
```

### Enable Email Alerts

1. Go to [Cloud Console Monitoring](https://console.cloud.google.com/monitoring)
2. Create notification channel with your email
3. Set up alerts for:
   - Service downtime
   - High error rate
   - Memory/CPU limits

### View Analytics

```bash
# Request count in last 24 hours
gcloud run services describe panel-espresso \
  --region=us-central1 \
  --format='value(status.traffic[0].percent)'

# View recent logs
gcloud run services logs read panel-espresso \
  --region=us-central1 \
  --limit=50
```

---

## Cost Optimization for pvalue.one

### Expected Costs

For typical usage:
- **Light use** (< 100 requests/day): $0/month (free tier)
- **Moderate use** (1000 requests/day): $5-10/month
- **Heavy use** (10000 requests/day): $20-50/month

### Set Budget Alerts

```bash
# Set billing alert at $25/month
gcloud alpha billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT_ID \
  --display-name="Panel Espresso Budget" \
  --budget-amount=25USD
```

Or via Console:
1. Go to [Billing → Budgets](https://console.cloud.google.com/billing/budgets)
2. Create budget for $25, $50, $100
3. Set email alerts

---

## Updating Your Deployment

When you make code changes:

```bash
# From your local repository
git pull  # Get latest changes
gcloud builds submit --config cloudbuild.yaml

# Cloud Run automatically updates https://panel.pvalue.one
# Zero-downtime deployment (users stay connected)
```

---

## Security Recommendations for pvalue.one

### 1. Add Authentication (Optional)

For private access only:

```bash
gcloud run services update panel-espresso \
  --region us-central1 \
  --no-allow-unauthenticated

# Grant access to specific users
gcloud run services add-iam-policy-binding panel-espresso \
  --region=us-central1 \
  --member='user:email@example.com' \
  --role='roles/run.invoker'
```

### 2. Rate Limiting

Consider adding rate limiting at DNS level (Cloudflare) or application level.

### 3. File Upload Limits

Already configured in `app.py` via Gradio defaults. Adjust if needed.

---

## Complete Setup Commands

Here's the complete command sequence for panel.pvalue.one:

```bash
# 1. Set project
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# 2. Enable services
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com

# 3. Deploy app
gcloud builds submit --config cloudbuild.yaml

# 4. Map domain
gcloud run domain-mappings create \
  --service panel-espresso \
  --domain panel.pvalue.one \
  --region us-central1

# 5. Get DNS instructions
gcloud run domain-mappings describe \
  --domain panel.pvalue.one \
  --region us-central1

# 6. Add CNAME record at your registrar:
#    Host: panel
#    Type: CNAME
#    Value: ghs.googlehosted.com

# 7. Wait 15-60 minutes for SSL certificate

# 8. Test
curl https://panel.pvalue.one
```

---

## Support

- **Main Documentation**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Google Cloud Support**: [Cloud Console](https://console.cloud.google.com)
- **DNS Help**: Contact your domain registrar

---

## Summary

✅ Deploy app to Cloud Run  
✅ Map panel.pvalue.one to Cloud Run  
✅ Add CNAME record at registrar  
✅ Wait for SSL certificate (15-60 min)  
✅ Access app at https://panel.pvalue.one  

Your Panel Espresso app is now live for users to access via your domain! 🎉
