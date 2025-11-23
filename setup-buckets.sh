#!/bin/bash

# AWS Periodic Table - S3 Buckets Setup Script
# This script creates the required S3 buckets with appropriate security settings

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

usage() {
    cat << EOF
Usage: $0 -l <lambda-bucket> -w <website-bucket> -r <region>

Setup S3 buckets for AWS Periodic Table

OPTIONS:
    -l, --lambda-bucket NAME    Name for private Lambda staging bucket
    -w, --website-bucket NAME   Name for private website bucket (CloudFront access only)
    -r, --region REGION         AWS region (default: eu-central-1)
    -h, --help                  Show this help

EXAMPLES:
    $0 -l aws-periodic-lambda-staging -w awsperiodictable.com -r eu-central-1

SECURITY:
    Lambda bucket: Created as PRIVATE (for Lambda ZIP files)
    Website bucket: Created as PRIVATE (only CloudFront OAI can access)

EOF
    exit 1
}

# Parse arguments
REGION="eu-central-1"
LAMBDA_BUCKET=""
WEBSITE_BUCKET=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -l|--lambda-bucket)
            LAMBDA_BUCKET="$2"
            shift 2
            ;;
        -w|--website-bucket)
            WEBSITE_BUCKET="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate parameters
if [ -z "$LAMBDA_BUCKET" ] || [ -z "$WEBSITE_BUCKET" ]; then
    print_error "Both buckets are required"
    usage
fi

print_info "Setting up S3 buckets in region: $REGION"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed"
    exit 1
fi

# Check credentials
if ! aws sts get-caller-identity --region $REGION &> /dev/null; then
    print_error "AWS credentials are not configured"
    exit 1
fi

# Create Lambda bucket (PRIVATE)
print_info "Creating Lambda staging bucket: $LAMBDA_BUCKET (PRIVATE)"
if aws s3 ls "s3://$LAMBDA_BUCKET" 2>/dev/null; then
    print_warning "Lambda bucket already exists"
else
    aws s3 mb "s3://$LAMBDA_BUCKET" --region $REGION
    
    # Enable versioning (recommended for Lambda packages)
    aws s3api put-bucket-versioning \
        --bucket $LAMBDA_BUCKET \
        --versioning-configuration Status=Enabled \
        --region $REGION
    
    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket $LAMBDA_BUCKET \
        --server-side-encryption-configuration '{
            "Rules": [{
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }]
        }' \
        --region $REGION
    
    # Block all public access (IMPORTANT!)
    aws s3api put-public-access-block \
        --bucket $LAMBDA_BUCKET \
        --public-access-block-configuration \
            "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
        --region $REGION
    
    print_info "✓ Lambda bucket created and secured"
fi
echo ""

# Create Website bucket (PRIVATE - only CloudFront access)
print_info "Creating website bucket: $WEBSITE_BUCKET (PRIVATE - CloudFront access only)"
if aws s3 ls "s3://$WEBSITE_BUCKET" 2>/dev/null; then
    print_warning "Website bucket already exists"
else
    aws s3 mb "s3://$WEBSITE_BUCKET" --region $REGION
    
    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket $WEBSITE_BUCKET \
        --server-side-encryption-configuration '{
            "Rules": [{
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }]
        }' \
        --region $REGION
    
    print_info "✓ Website bucket created"
fi
echo ""

# Configure website bucket as PRIVATE
print_info "Configuring website bucket as PRIVATE (CloudFront-only access)..."

# Block public access (bucket stays private)
aws s3api put-public-access-block \
    --bucket $WEBSITE_BUCKET \
    --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
    --region $REGION

print_info "✓ Website bucket configured as private"
print_warning "Note: Lambda can write to this bucket, but it's NOT publicly accessible"
print_warning "You need to configure CloudFront with OAI to serve content from this bucket"
echo ""

# Summary
print_info "=========================================="
print_info "Bucket setup completed!"
print_info "=========================================="
echo ""
echo "Buckets created:"
echo "  1. $LAMBDA_BUCKET (PRIVATE)"
echo "     - Purpose: Lambda ZIP files"
echo "     - Access: Private only"
echo "     - Versioning: Enabled"
echo "     - Encryption: Enabled"
echo ""
echo "  2. $WEBSITE_BUCKET (PRIVATE)"
echo "     - Purpose: Website content"
echo "     - Access: Private (only CloudFront can access)"
echo "     - Encryption: Enabled"
echo "     - Lambda can write, but NO public access"
echo ""
echo "Next steps:"
echo "  1. Update deploy.config:"
echo "     LAMBDA_BUCKET=\"$LAMBDA_BUCKET\""
echo "     OUTPUT_BUCKET=\"$WEBSITE_BUCKET\""
echo ""
echo "  2. Deploy the application:"
echo "     ./deploy.sh"
echo ""

if [ "$WEBSITE_BUCKET" != "*.amazonaws.com" ]; then
    echo "  3. REQUIRED - Setup CloudFront with OAI (Origin Access Identity):"
    echo "     The website bucket is private and requires CloudFront to serve content."
    echo "     ./infrastructure/setup-cloudfront.sh -r $REGION -s awsperiodictable -b $WEBSITE_BUCKET"
    echo ""
    echo "  4. CloudFront will:"
    echo "     - Create an Origin Access Identity (OAI)"
    echo "     - Add bucket policy allowing only CloudFront OAI to read"
    echo "     - Provide HTTPS endpoint for your website"
    echo ""
fi
