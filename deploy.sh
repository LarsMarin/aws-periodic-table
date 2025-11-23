#!/bin/bash

# AWS Periodic Table Deployment Script
# This script packages and deploys the Lambda function with all dependencies

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy AWS Periodic Table Lambda function

Die Standardwerte werden aus deploy.config geladen.
Parameter können als Optionen überschrieben werden.

OPTIONS:
    -r, --region REGION              AWS region
    -l, --lambda-bucket BUCKET       S3 bucket for Lambda package staging (private)
    -b, --output-bucket BUCKET       S3 bucket for HTML output (private, CloudFront access)
    -s, --stack-name NAME            CloudFormation stack name
    -k, --output-key KEY             Output file name
    -c, --cloudfront-id ID           CloudFront distribution ID (for cache invalidation)
    -i, --invoke                     Invoke Lambda after deployment (default: true)
    -n, --no-invoke                  Skip Lambda invocation
    -f, --force                      Force redeployment even if no changes
    -h, --help                       Show this help message

EXAMPLES:
    # Einfaches Deployment (verwendet deploy.config)
    $0

    # Deployment mit Force-Flag
    $0 -f

    # Deployment ohne Lambda-Ausführung
    $0 -n

    # Override einzelne Werte
    $0 -r us-east-1 -l my-lambda-bucket -b my-website-bucket

CONFIGURATION:
    Editiere deploy.config um Standard-Werte zu setzen:
    - REGION
    - LAMBDA_BUCKET (privat)
    - OUTPUT_BUCKET (privat, CloudFront only)
    - STACK_NAME
    - OUTPUT_KEY
    - CLOUDFRONT_ID

SICHERHEIT:
    LAMBDA_BUCKET: PRIVAT (Lambda ZIP-Dateien)
    OUTPUT_BUCKET: PRIVAT (nur CloudFront kann lesen via OAI)
    
    Beide Buckets sind privat. CloudFront benötigt Origin Access Identity (OAI)
    um auf OUTPUT_BUCKET zugreifen zu können.

EOF
    exit 1
}

# Load configuration from deploy.config if it exists
if [ -f "deploy.config" ]; then
    print_info "Loading configuration from deploy.config..."
    source deploy.config
else
    print_warning "deploy.config not found. Using default values."
fi

# Default values (fallback if not in config)
REGION="${REGION:-us-east-1}"
STACK_NAME="${STACK_NAME:-awsperiodictable}"
OUTPUT_KEY="${OUTPUT_KEY:-index.html}"
LAMBDA_BUCKET="${LAMBDA_BUCKET:-}"
OUTPUT_BUCKET="${OUTPUT_BUCKET:-}"
CLOUDFRONT_ID="${CLOUDFRONT_ID:-}"
FORCE=false
INVOKE_LAMBDA=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -l|--lambda-bucket)
            LAMBDA_BUCKET="$2"
            shift 2
            ;;
        -b|--output-bucket)
            OUTPUT_BUCKET="$2"
            shift 2
            ;;
        -s|--stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        -k|--output-key)
            OUTPUT_KEY="$2"
            shift 2
            ;;
        -c|--cloudfront-id)
            CLOUDFRONT_ID="$2"
            shift 2
            ;;
        -i|--invoke)
            INVOKE_LAMBDA=true
            shift
            ;;
        -n|--no-invoke)
            INVOKE_LAMBDA=false
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
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

# Validate required parameters
if [ -z "$LAMBDA_BUCKET" ]; then
    print_error "Lambda bucket is required (set in deploy.config or use -l/--lambda-bucket)"
    usage
fi

if [ -z "$OUTPUT_BUCKET" ]; then
    print_error "Output bucket is required (set in deploy.config or use -b/--output-bucket)"
    usage
fi

# Print deployment configuration
print_info "Deployment Configuration:"
echo "  Region:           $REGION"
echo "  Lambda Bucket:    $LAMBDA_BUCKET (private)"
echo "  Output Bucket:    $OUTPUT_BUCKET (private, CloudFront only)"
echo "  Stack Name:       $STACK_NAME"
echo "  Output Key:       $OUTPUT_KEY"
if [ -n "$CLOUDFRONT_ID" ]; then
    echo "  CloudFront ID:    $CLOUDFRONT_ID"
fi
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check AWS credentials
print_info "Checking AWS credentials..."
if ! aws sts get-caller-identity --region $REGION &> /dev/null; then
    print_error "AWS credentials are not configured or invalid"
    exit 1
fi

# Install Python dependencies
print_info "Installing Python dependencies..."
cd periodic
if [ ! -d "lib" ]; then
    mkdir -p lib
fi

pip install -r requirements.txt -t lib/ -q

if [ $? -ne 0 ]; then
    print_error "Failed to install Python dependencies"
    exit 1
fi

cd ..
print_info "Dependencies installed successfully"

# Package CloudFormation template
print_info "Packaging CloudFormation template..."
aws --region $REGION cloudformation package \
    --template-file infrastructure/template.yaml \
    --s3-bucket $LAMBDA_BUCKET \
    --output-template-file infrastructure/package.yaml

if [ $? -ne 0 ]; then
    print_error "Failed to package CloudFormation template"
    exit 1
fi

# Deploy CloudFormation stack
print_info "Deploying CloudFormation stack: $STACK_NAME"
DEPLOY_CMD="aws --region $REGION cloudformation deploy \
    --template-file infrastructure/package.yaml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides Bucket=$OUTPUT_BUCKET Key=$OUTPUT_KEY"

if [ "$FORCE" = true ]; then
    DEPLOY_CMD="$DEPLOY_CMD --no-fail-on-empty-changeset"
fi

eval $DEPLOY_CMD

if [ $? -ne 0 ]; then
    print_error "Failed to deploy CloudFormation stack"
    exit 1
fi

print_info "Stack deployed successfully!"

# Get Lambda function name
print_info "Retrieving Lambda function details..."
FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --region $REGION \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunction`].OutputValue' \
    --output text 2>/dev/null)

if [ -n "$FUNCTION_NAME" ]; then
    print_info "Lambda Function: $FUNCTION_NAME"
    
    # Show current environment variables
    print_info "Current environment variables:"
    aws lambda get-function-configuration \
        --region $REGION \
        --function-name $FUNCTION_NAME \
        --query 'Environment.Variables' \
        --output table
else
    print_warning "Could not retrieve Lambda function name from stack outputs"
fi

# Invoke Lambda if requested
if [ "$INVOKE_LAMBDA" = true ] && [ -n "$FUNCTION_NAME" ]; then
    echo ""
    print_info "Invoking Lambda function to generate HTML files..."
    
    aws lambda invoke \
        --function-name "$FUNCTION_NAME" \
        --region "$REGION" \
        --log-type Tail \
        --query 'LogResult' \
        --output text \
        response.json 2>/dev/null | base64 --decode
    
    if [ $? -eq 0 ]; then
        print_info "Lambda function executed successfully!"
        echo ""
        echo "Generated files in S3:"
        echo "  - index.html (main file, uses default data source)"
        echo "  - index_scrape.html (web scraping version)"
        echo "  - index_directory.html (directory API version)"
        
        # List files in S3
        aws s3 ls "s3://$OUTPUT_BUCKET/" --region "$REGION" 2>/dev/null | grep "index"
    else
        print_warning "Lambda invocation may have failed. Check CloudWatch Logs."
    fi
    
    rm -f response.json
fi

# CloudFront cache invalidation if distribution ID provided
if [ -n "$CLOUDFRONT_ID" ]; then
    echo ""
    print_info "Invalidating CloudFront cache..."
    
    INVALIDATION_OUTPUT=$(aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_ID" \
        --paths "/index.html" "/index_scrape.html" "/index_directory.html" \
        --query 'Invalidation.{Id:Id,Status:Status,CreateTime:CreateTime}' \
        --output table 2>&1)
    
    if [ $? -eq 0 ]; then
        print_info "CloudFront cache invalidation started!"
        echo "$INVALIDATION_OUTPUT"
    else
        print_warning "CloudFront invalidation failed. Check distribution ID."
        echo "$INVALIDATION_OUTPUT"
    fi
fi

# Success message
echo ""
print_info "=========================================="
print_info "Deployment completed successfully!"
print_info "=========================================="
echo ""

if [ "$INVOKE_LAMBDA" = false ]; then
    echo "Next steps:"
    echo "  1. Invoke Lambda to generate HTML files:"
    echo "     aws lambda invoke --region $REGION --function-name $FUNCTION_NAME --payload '{}' response.json"
    echo ""
fi

if [ -z "$CLOUDFRONT_ID" ]; then
    echo "CloudFront cache invalidation:"
    echo "  Add CLOUDFRONT_ID to deploy.config to enable automatic cache invalidation"
    echo ""
fi

echo "Additional commands:"
echo "  - View logs:"
echo "    aws logs tail /aws/lambda/$FUNCTION_NAME --region $REGION --follow"
echo ""
echo "  - Check S3 files:"
echo "    aws s3 ls s3://$OUTPUT_BUCKET/"
echo ""
echo "  - Configure environment variables:"
echo "    aws lambda update-function-configuration \\"
echo "      --region $REGION \\"
echo "      --function-name $FUNCTION_NAME \\"
echo "      --environment 'Variables={PERIODIC_DATA_SOURCE=directory,PERIODIC_PRODUCTS_SIZE=300}'"
echo ""
