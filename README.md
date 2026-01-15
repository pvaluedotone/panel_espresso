# Panel Data Analysis App

A Gradio-based web application for panel data analysis using **pyfixest**.

## Features

- **Fixed Effects Models**: Firm and year fixed effects with clustered standard errors
- **Pooled OLS**: With industry/country dummy variables
- **Interaction Terms**: Test moderating effects
- **Lagged Variables**: Include lagged dependent variables
- **Dynamic UI**: Automatic variable detection from uploaded CSV files
- **Diagnostics**: Comprehensive model diagnostics and balance checks
- **Reproducible Code**: Generate Python code for your analysis

## Installation

This project uses UV for dependency management.

```bash
# Install dependencies
uv sync

# Run the application
uv run python app.py
```

## Usage

1. Upload your panel data CSV file
2. Select your panel structure variables (Firm ID, Time)
3. Choose your dependent and independent variables
4. Select the estimation method (Fixed Effects or Pooled OLS)
5. Configure specifications (year FE, clustering, interactions)
6. Click "Run Analysis"

The app will open in your browser at http://127.0.0.1:7860

## Requirements

- Python >=3.11
- gradio
- pyfixest
- pandas
- numpy

## About pyfixest

This app uses [pyfixest](https://github.com/py-econometrics/pyfixest) for efficient estimation of panel data models with high-dimensional fixed effects.

## Deployment

### Deploy to Google Cloud Run

This application can be easily deployed to Google Cloud Run, making it accessible through your custom domain.

**Quick deployment**:
```bash
# Use the deployment script
chmod +x deploy.sh
./deploy.sh YOUR_PROJECT_ID

# Or deploy manually
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com
gcloud builds submit --config cloudbuild.yaml
```

**Documentation**:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment guide
- [DOMAIN_SETUP_pvalue.one.md](DOMAIN_SETUP_pvalue.one.md) - Specific setup for pvalue.one domain
- Quick start: Run `./deploy.sh YOUR_PROJECT_ID` and follow the prompts

**Access the app**:
- After deployment: Cloud Run URL (e.g., `https://panel-espresso-xxxxx-uc.a.run.app`)
- With custom domain: `https://panel.pvalue.one` (see domain setup guide)

## Available Versions

This workspace contains **three versions** of the app for different use cases:

### 1. **app.py** - Production Version (Recommended for G ≥ 50)
- Standard panel data analysis
- No bootstrap (fastest)
- CRV1 and CRV3 cluster-robust standard errors
- **Use when**: Sufficient clusters (50+)

### 2. **app_experiment.py** - Standard Bootstrap Version (Recommended for G < 30)
- All features from app.py PLUS:
- **Wild cluster bootstrap** for small clusters
- Automatic bootstrap when G < 30
- Bootstraps **main independent variable only** (standard practice)
- Webb weights for optimal small-sample properties
- **Use when**: Small clusters and testing primary hypothesis

### 3. **process/app_multi_bootstrap.py** - Advanced Multi-Variable Bootstrap
- All features from app_experiment.py PLUS:
- **User-selectable bootstrap variables** via UI
- Can bootstrap controls in addition to X
- Multiple testing warnings and guidance
- **Use when**: Small clusters AND need bootstrap for multiple variables
- **Advanced users only** - requires understanding of multiple testing

### Quick Decision Guide

```
Clusters ≥ 50?  → Use app.py
Clusters < 30?  → Use app_experiment.py (most users)
                  → Use process/app_multi_bootstrap.py (advanced)
```

### Documentation

- **Standard Bootstrap**: See `EXPERIMENTAL_BOOTSTRAP_NOTES.md` and `IMPLEMENTATION_SUMMARY.md`
- **Multi-Variable Bootstrap**: See `process/README.md`, `process/QUICKSTART.md`, `process/COMPARISON.md`
- **Bootstrap Theory**: Cameron et al. (2008), MacKinnon et al. (2023)
