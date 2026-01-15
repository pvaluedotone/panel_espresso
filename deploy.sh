#!/bin/bash
# Quick deployment script for Panel Espresso to Google Cloud Run
# Usage: ./deploy.sh [PROJECT_ID] [REGION]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DEFAULT_REGION="us-central1"

# Parse arguments
PROJECT_ID=${1:-}
REGION=${2:-$DEFAULT_REGION}

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first:"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID if not provided
if [ -z "$PROJECT_ID" ]; then
    print_warning "No project ID provided. Using current gcloud project..."
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    
    if [ -z "$PROJECT_ID" ]; then
        print_error "No project ID found. Please provide one as argument:"
        echo "Usage: ./deploy.sh PROJECT_ID [REGION]"
        exit 1
    fi
fi

print_info "Deploying to project: $PROJECT_ID"
print_info "Region: $REGION"

# Confirm deployment
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled."
    exit 0
fi

# Set project
print_info "Setting active project..."
gcloud config set project "$PROJECT_ID"

# Enable required APIs
print_info "Enabling required Google Cloud APIs..."
gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    compute.googleapis.com

# Build and deploy
print_info "Building and deploying application..."
print_info "This may take 5-10 minutes..."

gcloud builds submit --config cloudbuild.yaml

# Get service URL
print_info "Deployment complete!"
SERVICE_URL=$(gcloud run services describe panel-espresso --region="$REGION" --format='value(status.url)' 2>/dev/null)

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Deployment Successful!${NC}"
echo "=========================================="
echo ""
echo "Your Panel Espresso app is now live at:"
echo -e "${GREEN}$SERVICE_URL${NC}"
echo ""
echo "Next steps:"
echo "1. Visit the URL above to test your app"
echo "2. To set up a custom domain, see DEPLOYMENT.md"
echo "3. Monitor your app: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo ""
echo "To view logs:"
echo "  gcloud run services logs read panel-espresso --region=$REGION"
echo ""
echo "To update deployment:"
echo "  ./deploy.sh $PROJECT_ID $REGION"
echo ""
