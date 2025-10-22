#!/bin/bash

# Usage: ./setup-dns.sh <hosted-zone-id> <s3-bucket-name> <region>

HOSTED_ZONE_ID=$1
BUCKET_NAME=$2
REGION=$3

if [ -z "$HOSTED_ZONE_ID" ] || [ -z "$BUCKET_NAME" ] || [ -z "$REGION" ]; then
    echo "Usage: ./setup-dns.sh <hosted-zone-id> <s3-bucket-name> <region>"
    exit 1
fi

# S3 website endpoint
S3_ENDPOINT="${BUCKET_NAME}.s3-website.${REGION}.amazonaws.com"

echo "Configuring DNS for awsperiodictable.com"
echo "Hosted Zone ID: $HOSTED_ZONE_ID"
echo "S3 Endpoint: $S3_ENDPOINT"

# Check if stack exists and is in ROLLBACK_COMPLETE state
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name awsperiodictable-dns --region $REGION --query 'Stacks[0].StackStatus' --output text 2>/dev/null)

if [ "$STACK_STATUS" = "ROLLBACK_COMPLETE" ]; then
    echo "Deleting failed stack..."
    aws cloudformation delete-stack --stack-name awsperiodictable-dns --region $REGION
    aws cloudformation wait stack-delete-complete --stack-name awsperiodictable-dns --region $REGION
    echo "Stack deleted"
fi

# Deploy CloudFormation stack
aws cloudformation deploy \
    --template-file route53.yaml \
    --stack-name awsperiodictable-dns \
    --parameter-overrides \
        HostedZoneId=$HOSTED_ZONE_ID \
        S3BucketWebsiteEndpoint=$S3_ENDPOINT \
    --region $REGION

echo "DNS configuration complete"
