#!/bin/bash

HOSTED_ZONE_ID=$1
BUCKET_NAME=$2
OBJECT_KEY=${3:-index.html}

if [ -z "$HOSTED_ZONE_ID" ] || [ -z "$BUCKET_NAME" ]; then
    echo "Usage: ./setup-cloudfront.sh <hosted-zone-id> <bucket-name> [object-key]"
    exit 1
fi

echo "Setting up CloudFront with SSL for awsperiodictable.com"
echo "This will:"
echo "  - Create ACM certificate (requires DNS validation)"
echo "  - Create CloudFront distribution"
echo "  - Configure Origin Access Control"
echo "  - Update Route53 DNS records"
echo "  - Remove public bucket access"
echo ""
echo "Note: Certificate must be created in us-east-1 for CloudFront"
echo ""

# Check if stack exists and is in ROLLBACK_COMPLETE state
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name awsperiodictable-cloudfront --region us-east-1 --query 'Stacks[0].StackStatus' --output text 2>/dev/null)

if [ "$STACK_STATUS" = "ROLLBACK_COMPLETE" ]; then
    echo "Deleting failed stack..."
    aws cloudformation delete-stack --stack-name awsperiodictable-cloudfront --region us-east-1
    aws cloudformation wait stack-delete-complete --stack-name awsperiodictable-cloudfront --region us-east-1
    echo "Stack deleted"
fi

# Deploy stack in us-east-1 (required for CloudFront certificates)
aws cloudformation deploy \
    --template-file cloudfront.yaml \
    --stack-name awsperiodictable-cloudfront \
    --parameter-overrides \
        HostedZoneId=$HOSTED_ZONE_ID \
        BucketName=$BUCKET_NAME \
        ObjectKey=$OBJECT_KEY \
    --region us-east-1 \
    --capabilities CAPABILITY_IAM

echo ""
echo "CloudFront setup complete!"
echo "Note: CloudFront distribution deployment takes 15-20 minutes"
echo ""
echo "After deployment:"
echo "  1. Disable S3 website hosting"
echo "  2. Remove public bucket policy"
echo "  3. Delete old DNS stack: aws cloudformation delete-stack --stack-name awsperiodictable-dns --region eu-central-1"
