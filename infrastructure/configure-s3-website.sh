#!/bin/bash

# Usage: ./configure-s3-website.sh <bucket-name> <html-key> <region>

BUCKET=$1
KEY=$2
REGION=${3:-eu-central-1}

if [ -z "$BUCKET" ] || [ -z "$KEY" ]; then
    echo "Usage: ./configure-s3-website.sh <bucket-name> <html-key> [region]"
    exit 1
fi

echo "Configuring S3 bucket $BUCKET for website hosting..."

# Disable Block Public Access
aws s3api put-public-access-block \
    --bucket $BUCKET \
    --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" \
    --region $REGION

echo "Block Public Access disabled"

# Enable website hosting
aws s3 website s3://$BUCKET/ \
    --index-document $KEY \
    --region $REGION

# Set bucket policy for public read
cat > /tmp/bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BUCKET/*"
    }
  ]
}
EOF

aws s3api put-bucket-policy \
    --bucket $BUCKET \
    --policy file:///tmp/bucket-policy.json \
    --region $REGION

rm /tmp/bucket-policy.json

echo "S3 bucket configured for website hosting"
echo "Website endpoint: http://$BUCKET.s3-website.$REGION.amazonaws.com"
