# Panel Espresso Deployment Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Users                               │
│                         ↓                                    │
│              https://panel.pvalue.one                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   DNS (Your Registrar)                       │
│  CNAME: panel.pvalue.one → ghs.googlehosted.com            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Google Cloud Load Balancer                      │
│  • Automatic SSL/TLS (Let's Encrypt)                        │
│  • HTTPS enforcement                                         │
│  • Geographic distribution                                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  Google Cloud Run                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Panel Espresso Container                      │  │
│  │  • Python 3.11                                        │  │
│  │  • Gradio Web Interface                               │  │
│  │  • pyfixest for panel analysis                        │  │
│  │  • Auto-scaling (0-10 instances)                      │  │
│  │  • 2GB RAM, 2 CPU per instance                        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Flow

```
┌─────────────┐
│ Your Code   │
│ (GitHub)    │
└──────┬──────┘
       │ git push
       ↓
┌─────────────────────────────────────────┐
│        Google Cloud Build               │
│  1. Clone repository                    │
│  2. Build Docker image                  │
│  3. Push to Container Registry          │
│  4. Deploy to Cloud Run                 │
└─────────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│   Google Container Registry (GCR)       │
│   gcr.io/PROJECT_ID/panel-espresso      │
└─────────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│        Google Cloud Run Service         │
│   Name: panel-espresso                  │
│   Region: us-central1                   │
│   URL: panel-espresso-xxx.run.app       │
└─────────────────────────────────────────┘
```

## File Structure

```
panel_espresso/
├── app.py                      # Main application (modified for Cloud Run)
├── process/
│   └── bootstrap_ui_module.py  # Bootstrap UI components
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── cloudbuild.yaml            # Build configuration
├── deploy.sh                  # Deployment script
│
├── QUICKSTART.md              # Fast deployment guide
├── DEPLOYMENT.md              # Complete documentation
├── DOMAIN_SETUP_pvalue.one.md # Domain-specific guide
└── README.md                  # Updated with deployment info
```

## Key Components

### 1. Docker Container
- **Base**: Python 3.11-slim
- **Port**: 8080 (Cloud Run standard)
- **Entry**: `python app.py`
- **Size**: ~500MB (optimized)

### 2. Application Configuration
```python
# app.py detects Cloud Run environment
if "PORT" in os.environ:
    server_name = "0.0.0.0"      # Listen on all interfaces
    server_port = int(os.environ["PORT"])  # Cloud Run sets this
```

### 3. Cloud Run Service
```yaml
Service: panel-espresso
Region: us-central1
Memory: 2GB
CPU: 2
Timeout: 300s (5 minutes)
Max Instances: 10
Min Instances: 0 (scale to zero)
```

### 4. Domain Mapping
```
panel.pvalue.one → ghs.googlehosted.com (CNAME)
                 ↓
         Google Cloud Load Balancer
                 ↓
         panel-espresso service
```

## Auto-Scaling Behavior

```
No traffic:
┌─────────────────┐
│  0 instances    │  Cost: $0/hour
│  (scaled down)  │
└─────────────────┘

First request:
┌─────────────────┐
│  Cold start     │  ~5-10 seconds
│  Starting...    │
└─────────────────┘

Active traffic:
┌───┐ ┌───┐ ┌───┐
│ 1 │ │ 2 │ │ 3 │  Scale based on load
└───┘ └───┘ └───┘  Cost: Usage-based

High traffic:
┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐
│ 1 │ │ 2 │ │ 3 │ │ 4 │ │ 5 │  Up to max instances
└───┘ └───┘ └───┘ └───┘ └───┘
```

## Request Flow

```
1. User visits https://panel.pvalue.one
        ↓
2. DNS resolves to Google Cloud
        ↓
3. Load Balancer routes to Cloud Run
        ↓
4. Cloud Run starts/routes to container instance
        ↓
5. Gradio serves the web interface
        ↓
6. User uploads CSV file
        ↓
7. pyfixest processes panel data analysis
        ↓
8. Results displayed in browser
```

## Security Layers

```
┌──────────────────────────────────────────┐
│  1. HTTPS/TLS (Automatic)                │
│     • Let's Encrypt SSL certificate      │
│     • Automatic renewal                  │
└──────────────────────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│  2. Cloud Run IAM (Optional)             │
│     • Can require authentication         │
│     • User-level access control          │
└──────────────────────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│  3. Container Isolation                  │
│     • Each instance isolated             │
│     • No shared file system              │
└──────────────────────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│  4. Google Cloud Security                │
│     • DDoS protection                    │
│     • Network isolation                  │
└──────────────────────────────────────────┘
```

## Cost Structure

```
Cloud Run Pricing = (CPU × time) + (Memory × time) + Requests

Free Tier (monthly):
├── 2 million requests
├── 360,000 GB-seconds of memory
└── 180,000 vCPU-seconds

Example Calculation:
├── 1000 requests/day × 30 days = 30,000 requests
├── Avg 2s per request = 60,000 seconds
├── 2GB RAM × 60,000s = 120,000 GB-seconds
├── 2 CPU × 60,000s = 120,000 vCPU-seconds
└── Total: $3-5/month (well within free tier for light use)

Cost Optimization:
├── min-instances: 0 → Pay only when used
├── Right-size resources → Start with 2GB/2CPU
└── Set max-instances: 10 → Prevent runaway costs
```

## Deployment Timeline

```
First-time deployment:
├── 0 min: Run gcloud builds submit
├── 2 min: Build Docker image
├── 5 min: Deploy to Cloud Run
├── 7 min: Service ready at Cloud Run URL ✓
├── 8 min: Add CNAME to DNS
├── 10 min: DNS propagation begins
├── 30 min: SSL certificate provisioning
└── 60 min: https://panel.pvalue.one fully operational ✓

Subsequent deployments:
├── 0 min: Run gcloud builds submit
├── 3 min: Build and deploy (faster, uses cache)
└── 5 min: New version live (zero downtime) ✓
```

## Monitoring Dashboard

```
Cloud Console → Cloud Run → panel-espresso

Metrics to watch:
├── Request count
│   └── Track daily/weekly usage
├── Request latency
│   └── P50, P95, P99 response times
├── Container instances
│   └── Scaling behavior
├── Error rate
│   └── 4xx and 5xx errors
└── Memory/CPU utilization
    └── Right-sizing guidance
```

## Troubleshooting Decision Tree

```
Problem: Site not accessible
    ├── Check Cloud Run service status
    │   └── gcloud run services describe panel-espresso
    ├── Check DNS resolution
    │   └── nslookup panel.pvalue.one
    ├── Check SSL certificate
    │   └── gcloud run domain-mappings describe
    └── Check logs
        └── gcloud run services logs read

Problem: Slow performance
    ├── Increase memory (2GB → 4GB)
    ├── Increase CPU (2 → 4)
    ├── Set min-instances to 1 (avoid cold starts)
    └── Check application logs for bottlenecks

Problem: Build fails
    ├── Check Dockerfile syntax
    ├── Verify requirements.txt
    ├── Check build logs
    │   └── gcloud builds log BUILD_ID
    └── Test locally with Docker

Problem: High costs
    ├── Check request volume (set alerts)
    ├── Reduce max-instances
    ├── Optimize application (reduce processing time)
    └── Review instance count in metrics
```

## Backup and Recovery

```
Disaster Recovery:
├── Code: Stored in GitHub repository
├── Configuration: In cloudbuild.yaml, Dockerfile
├── Deployment: Repeatable with deploy.sh
└── User data: Temporary (not persisted)

To rollback:
├── List revisions
│   └── gcloud run revisions list
└── Route traffic to previous revision
    └── gcloud run services update-traffic
```

## Summary

This deployment provides:
- ✅ **Scalable**: Auto-scales from 0 to 10 instances
- ✅ **Secure**: HTTPS, IAM, container isolation
- ✅ **Cost-effective**: Pay per use, free tier available
- ✅ **Fast**: Global CDN, optimized container
- ✅ **Reliable**: Google's infrastructure, 99.95% SLA
- ✅ **Easy to update**: One command deployment
- ✅ **Professional**: Custom domain with SSL

Perfect for hosting your panel data analysis application! 🚀
