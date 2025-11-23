# Lambda Deployment Instructions

This document describes how to deploy and update the AWS Periodic Table Lambda function.

## Initial Deployment

### Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.9+
- S3 bucket for Lambda deployment package staging
- S3 bucket for HTML output

### Empfohlene Methode: Automatisches Deployment Script mit Konfigurationsdatei

Das Projekt enthält ein `deploy.sh` Script, das alle Schritte automatisiert und eine Konfigurationsdatei verwendet:

**1. Konfiguration erstellen:**
```bash
# Beispiel-Konfiguration kopieren
cp deploy.config.example deploy.config

# Eigene Werte eintragen (Region, Buckets, CloudFront ID)
nano deploy.config  # oder ein anderer Editor
```

**Konfigurationsdatei (`deploy.config`):**
```bash
REGION="eu-central-1"
LAMBDA_BUCKET="your-lambda-staging-bucket"
STACK_NAME="aws-periodic-table"
OUTPUT_BUCKET="your-website-bucket.com"
OUTPUT_KEY="index.html"
CLOUDFRONT_ID="YOUR_DISTRIBUTION_ID"
```

**2. Deployment ausführen:**
```bash
# Einfaches Deployment (verwendet deploy.config)
./deploy.sh

# Mit Force-Flag (nützlich bei "No changes to deploy")
./deploy.sh -f

# Deployment ohne Lambda-Ausführung
./deploy.sh -n
```

**Optionale Command-Line Parameter** (überschreiben deploy.config):
- `-r, --region REGION`: AWS Region
- `-l, --lambda-bucket BUCKET`: S3 Bucket für CloudFormation Package Staging
- `-s, --stack-name NAME`: CloudFormation Stack Name
- `-b, --output-bucket BUCKET`: S3 Bucket für generierte HTML-Dateien
- `-k, --output-key KEY`: Output-Dateiname
- `-c, --cloudfront-id ID`: CloudFront Distribution ID
- `-i, --invoke`: Lambda nach Deployment ausführen (Standard: true)
- `-n, --no-invoke`: Lambda nicht ausführen
- `-f, --force`: Erzwinge Redeployment auch ohne Änderungen
- `-h, --help`: Zeige Hilfe

**Beispiele:**
```bash
# Standard-Deployment (verwendet deploy.config)
./deploy.sh

# Override einzelne Werte
./deploy.sh -r us-east-1

# Force Redeployment
./deploy.sh -f

# Deployment ohne Lambda-Ausführung und CloudFront
./deploy.sh -n
```

**Das Script führt automatisch aus:**
1. ✓ Lädt Konfiguration aus `deploy.config`
2. ✓ Validierung der AWS Credentials
3. ✓ Installation der Python Dependencies
4. ✓ Paketierung des CloudFormation Templates
5. ✓ Deployment des Stacks
6. ✓ Anzeige der Lambda-Funktionsdetails
7. ✓ Lambda-Ausführung (Standard) - generiert HTML-Dateien sofort
8. ✓ CloudFront Cache-Invalidierung (wenn konfiguriert) - Updates werden sofort sichtbar

### Alternative: Manuelles Deployment

**Step 1: Install Dependencies**
```bash
cd periodic
pip install -r requirements.txt -t lib/
cd ..
```

**Step 2: Deploy via CloudFormation**
```bash
./infrastructure/build.sh <region> <lambda-bucket> <stack-name> <output-bucket> <output-key>
```

**Parameters:**
- `region`: AWS region (e.g., `us-east-1`)
- `lambda-bucket`: S3 bucket for CloudFormation package staging
- `stack-name`: CloudFormation stack name (e.g., `aws-periodic-table`)
- `output-bucket`: S3 bucket for generated HTML files
- `output-key`: Default output filename (e.g., `index.html`)

**Example:**
```bash
./infrastructure/build.sh us-east-1 my-lambda-bucket aws-periodic-table my-website-bucket index.html
```

## Updating the Lambda Function

### Method 1: Update via CloudFormation (Recommended)

After making changes to the code, redeploy the entire stack:

```bash
./infrastructure/build.sh <region> <lambda-bucket> <stack-name> <output-bucket> <output-key>
```

### Method 2: Update Function Code Only

Create a deployment package and update the function directly:

```bash
cd periodic

# Create deployment package
zip -r ../lambda-deployment.zip lambda_handler.py *.mustache base64_images.py lib/

# Update function
aws lambda update-function-code \
  --function-name <function-name> \
  --zip-file fileb://../lambda-deployment.zip
```

### Method 3: Update via AWS Console

1. Navigate to AWS Lambda Console
2. Select your function
3. Click "Upload from" → ".zip file"
4. Upload the deployment package
5. Ensure handler is set to `lambda_handler.lambda_handler`

## Environment Variables

Configure these environment variables on the Lambda function:

| Variable | Description | Default |
|----------|-------------|---------|
| `bucket` | S3 bucket for output | *Required* |
| `key` | Main output filename | `index.html` |
| `PERIODIC_DATA_SOURCE` | Data source: `scrape`, `directory`, or `merged` | `scrape` |
| `PERIODIC_PRODUCTS_SIZE` | Max items from Directory API | `300` |

### Setting Environment Variables

**Via AWS CLI:**
```bash
aws lambda update-function-configuration \
  --function-name <function-name> \
  --environment "Variables={bucket=my-bucket,key=index.html,PERIODIC_DATA_SOURCE=directory,PERIODIC_PRODUCTS_SIZE=300}"
```

**Via AWS Console:**
1. Go to Lambda function Configuration tab
2. Select Environment variables
3. Add or edit variables
4. Save changes

## Testing the Lambda Function

### Invoke Manually

```bash
aws lambda invoke \
  --function-name <function-name> \
  --payload '{}' \
  response.json

cat response.json
```

### View Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/<function-name> --follow

# View recent logs
aws logs tail /aws/lambda/<function-name> --since 1h
```

### Test Locally

```bash
cd debug
python3 test_local.py --source directory --size 300
# Output: ../output/output.html
```

## Output Files

The Lambda function generates three HTML files:

1. **index.html** - Uses default `PERIODIC_DATA_SOURCE` setting
2. **index_scrape.html** - Web scraping version
3. **index_directory.html** - Directory API version

Verify files in S3:
```bash
aws s3 ls s3://<bucket-name>/
```

## Troubleshooting

### Check Lambda Function Status

```bash
aws lambda get-function --function-name <function-name>
```

### View Function Configuration

```bash
aws lambda get-function-configuration --function-name <function-name>
```

### Common Issues

**Issue: Lambda timeout**
- Increase timeout in `infrastructure/template.yaml` (default: 300 seconds)
- Reduce `PERIODIC_PRODUCTS_SIZE` if using Directory API

**Issue: Missing dependencies**
- Ensure all dependencies are in `lib/` directory
- Verify `requirements.txt` includes all needed packages

**Issue: S3 permissions error**
- Check Lambda execution role has `s3:PutObject` permission
- Verify bucket policy allows Lambda to write

**Issue: Empty or malformed HTML**
- Check CloudWatch Logs for errors
- Test locally with `debug/test_local.py`
- Verify templates are included in deployment package

## Scheduled Execution

The Lambda function runs daily via CloudWatch Events (defined in CloudFormation template).

### Modify Schedule

Edit `infrastructure/template.yaml`:

```yaml
ScheduledEvent:
  Type: AWS::Events::Rule
  Properties:
    ScheduleExpression: rate(1 day)  # Change this
```

Common schedule expressions:
- `rate(1 day)` - Daily
- `rate(12 hours)` - Twice daily
- `rate(1 hour)` - Hourly
- `cron(0 0 * * ? *)` - Daily at midnight UTC

After modifying, redeploy:
```bash
./infrastructure/build.sh <region> <lambda-bucket> <stack-name> <output-bucket> <output-key>
```

## Manual Trigger

### Via AWS Console
1. Go to Lambda function
2. Click "Test" tab
3. Create test event with empty JSON: `{}`
4. Click "Test"

### Via AWS CLI
```bash
aws lambda invoke \
  --function-name <function-name> \
  --invocation-type Event \
  --payload '{}' \
  response.json
```

## Monitoring

### View Execution History

```bash
# List recent invocations
aws lambda list-functions --query 'Functions[?FunctionName==`<function-name>`]'

# CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=<function-name> \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

### Set Up Alarms

Create a CloudWatch Alarm for failures:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name lambda-periodic-table-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=<function-name> \
  --evaluation-periods 1
