# AWS Periodic Table

Generate an HTML "Periodic Table of Amazon Web Services" by scraping service information from AWS. This project creates a Lambda function that fires daily to regenerate the table and upload it to an S3 bucket.

## Features

- **Multiple Data Sources**: 
  - Web scraping from AWS products page
  - AWS Directory API integration
  - Merged data from multiple sources
- **Automatic Categorization**: Services grouped by AWS technology categories
- **Responsive Design**: Mobile-friendly periodic table layout
- **Social Media Cards**: OpenGraph and Twitter card support
- **Base64 Embedded Images**: Self-contained HTML with no external image dependencies
- **CloudFront Distribution**: Optional CDN setup with custom domain support

## Project Structure

```
aws-periodic-table/
├── periodic/                      # Lambda function code
│   ├── lambda_handler.py         # Main Lambda handler
│   ├── base_template.mustache    # Base HTML template
│   ├── template.mustache         # Main periodic table template
│   ├── opengraph.mustache        # OpenGraph meta tags
│   ├── google.mustache           # Google-specific meta tags
│   ├── twitter.mustache          # Twitter card meta tags
│   ├── base64_images.py          # Base64-encoded images
│   ├── create_base64_images.py   # Script to generate base64 images
│   ├── requirements.txt          # Python dependencies
│   ├── img/                      # Source images
│   └── lib/                      # Vendored dependencies
├── infrastructure/               # CloudFormation templates
│   ├── template.yaml            # Main Lambda stack
│   ├── cloudfront.yaml          # CloudFront distribution
│   ├── route53.yaml             # DNS configuration
│   ├── build.sh                 # Deployment script
│   ├── setup-cloudfront.sh      # CloudFront setup
│   ├── setup-dns.sh             # DNS setup
│   └── configure-s3-website.sh  # S3 website configuration
├── debug/                        # Development and testing utilities
│   ├── test_local.py            # Local testing script
│   ├── fetch_all_services.py    # Fetch from Price List API
│   ├── fetch_products_directory.py  # Fetch from Directory API
│   ├── check_all_services.py    # Service validation
│   ├── debug_scrape.py          # Debug web scraping
│   └── extract_json.py          # Extract JSON data
└── output/                       # Generated HTML files (gitignored)
```

## Quick Start

### Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.9+
- An S3 bucket for the Lambda deployment package
- An S3 bucket for the generated HTML output

### Deployment

Das Projekt enthält ein einfaches Deployment-Script mit Konfigurationsdatei:

**1. S3 Buckets erstellen (einmalig):**

Die Buckets werden **NICHT** automatisch erstellt. Verwende das Setup-Script:

```bash
./setup-buckets.sh -l aws-periodic-lambda-staging -w awsperiodictable.com -r eu-central-1
```

Das Script erstellt:
- **Lambda Bucket** (PRIVAT) - für Lambda ZIP-Dateien mit Encryption & Versioning
- **Website Bucket** (PRIVAT) - für HTML-Dateien, nur CloudFront kann zugreifen
  - Lambda kann schreiben
  - CloudFront kann lesen (via OAI)
  - KEINE öffentliche Policy

**2. Konfiguration erstellen:**
```bash
# Beispiel-Konfiguration kopieren
cp deploy.config.example deploy.config

# Eigene Werte eintragen (Bucket-Namen vom Setup-Script verwenden)
nano deploy.config  # oder ein anderer Editor
```

**3. Deployment ausführen:**
```bash
# Einfaches Deployment (verwendet deploy.config)
./deploy.sh

# Mit Force-Flag (nützlich bei "No changes to deploy")
./deploy.sh -f

# Deployment ohne Lambda-Ausführung
./deploy.sh -n
```

**Konfigurationsdatei (`deploy.config`)**:
```bash
REGION="eu-central-1"
LAMBDA_BUCKET="your-lambda-staging-bucket"
STACK_NAME="aws-periodic-table"
OUTPUT_BUCKET="your-website-bucket.com"
OUTPUT_KEY="index.html"
CLOUDFRONT_ID="YOUR_DISTRIBUTION_ID"
```

**Optionale Command-Line Parameter** (überschreiben deploy.config):
- `-r, --region REGION`: AWS Region
- `-l, --lambda-bucket BUCKET`: S3 Bucket für CloudFormation Package Staging
- `-s, --stack-name NAME`: CloudFormation Stack Name
- `-b, --output-bucket BUCKET`: S3 Bucket für die generierten HTML-Dateien
- `-k, --output-key KEY`: Output-Dateiname
- `-c, --cloudfront-id ID`: CloudFront Distribution ID
- `-i, --invoke`: Lambda nach Deployment ausführen (Standard: true)
- `-n, --no-invoke`: Lambda nicht ausführen
- `-f, --force`: Erzwinge Redeployment auch ohne Änderungen
- `-h, --help`: Zeige Hilfe

**Beispiele**:
```bash
# Standard-Deployment (verwendet deploy.config)
./deploy.sh

# Override einzelne Werte
./deploy.sh -r us-east-1

# Force Redeployment
./deploy.sh -f

# Deployment ohne Lambda-Ausführung
./deploy.sh -n
```

**Das Script führt folgende Schritte aus**:
1. ✓ Lädt Konfiguration aus `deploy.config`
2. ✓ Validiert AWS Credentials
3. ✓ Installiert Python Dependencies automatisch
4. ✓ Paketiert das CloudFormation Template
5. ✓ Deployt den Stack
6. ✓ Zeigt Lambda-Funktionsdetails an
7. ✓ Führt Lambda aus (Standard) um HTML-Dateien zu generieren
8. ✓ Invalidiert CloudFront Cache (wenn konfiguriert)

**Alternative: Manuelles Deployment**:
```bash
cd periodic
pip install -r requirements.txt -t lib/
cd ..
./infrastructure/build.sh <region> <lambda-bucket> <stack-name> <output-bucket> <output-key>
```

### Environment Variables

Configure these on the Lambda function:

- `bucket`: S3 bucket name for output (required)
- `key`: Main output file name (default: `index.html`)
- `PERIODIC_DATA_SOURCE`: Data source selection
  - `scrape`: Web scraping (original behavior, default)
  - `directory`: AWS Directory API (includes all services/features)
  - `merged`: Combined sources (future enhancement)
- `PERIODIC_PRODUCTS_SIZE`: Number of items from Directory API (default: `300`)

## Data Sources

### 1. Web Scraping (Legacy)
Scrapes the AWS products page navigation structure. This is the original implementation.

```bash
# Test locally
cd debug
python3 test_local.py --source scrape
```

### 2. Directory API
Uses the public AWS products directory endpoint to list all services and features. Supports automatic categorization.

```bash
# Test locally with Directory API
cd debug
python3 test_local.py --source directory --size 300

# Or use environment variables
PERIODIC_DATA_SOURCE=directory PERIODIC_PRODUCTS_SIZE=300 python3 test_local.py
```

### 3. Fetch Utilities

Fetch services from the AWS Price List API:
```bash
cd debug
python3 fetch_all_services.py
# Outputs: all_aws_services.json
```

Fetch from the AWS Directory API:
```bash
python3 fetch_products_directory.py
# Outputs: products_services.json
```

Merge both sources:
```bash
python3 fetch_products_directory.py --merge
# Outputs: merged_all_aws_services.json
```

## Local Testing

The `test_local.py` script generates HTML locally without deploying:

```bash
cd debug

# Test with Directory API (recommended)
python3 test_local.py --source directory --size 300

# Test with web scraping
python3 test_local.py --source scrape

# Output file will be in ../output/output.html
```

Open `output/output.html` in your browser to preview the table.

## CloudFront Setup (Optional)

Set up a CloudFront distribution with custom domain:

```bash
# 1. Configure S3 bucket for website hosting
./infrastructure/configure-s3-website.sh <bucket-name> <region>

# 2. Create CloudFront distribution
./infrastructure/setup-cloudfront.sh <region> <stack-name> <bucket-name> <certificate-arn> <domain-name>

# 3. Configure DNS
./infrastructure/setup-dns.sh <region> <stack-name> <domain-name> <hosted-zone-id>
```

## Output Files

The Lambda function generates three versions:

1. `index.html` - Main file (uses default PERIODIC_DATA_SOURCE)
2. `index_scrape.html` - Web scraping version
3. `index_directory.html` - Directory API version

## Service Categorization

When using the Directory API, services are automatically grouped by AWS technology categories:

- Analytics
- Compute
- Storage
- Developer Tools
- Management & Governance
- AI/ML
- Databases
- Application Integration
- Media Services
- IoT
- Migration & Transfer
- End User Computing
- Business Applications
- And more...

Categories are derived from:
1. `aws-technology-categories` tag (preferred)
2. `aws-tech-category` tag (fallback)
3. `badge` field (fallback)
4. "Other" (if no category found)

## Development

### Adding New Images

1. Place image files in `periodic/img/`
2. Run the base64 encoder:
```bash
cd periodic
python3 create_base64_images.py
```
3. This updates `base64_images.py` with the new images

### Modifying Templates

- `base_template.mustache` - HTML structure and styling
- `template.mustache` - Periodic table grid layout
- `opengraph.mustache` - OpenGraph meta tags
- `twitter.mustache` - Twitter card meta tags
- `google.mustache` - Google-specific meta tags

## Scheduled Execution

The Lambda function is configured to run daily via CloudWatch Events. The schedule can be modified in `infrastructure/template.yaml`.

## Troubleshooting

### Test Lambda locally
```bash
cd debug
python3 test_local.py --source directory
```

### Check service data
```bash
python3 debug/check_all_services.py
```

### Debug web scraping
```bash
python3 debug/debug_scrape.py
```

### View Lambda logs
```bash
aws logs tail /aws/lambda/<function-name> --follow
