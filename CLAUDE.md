# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AWS Periodic Table generates an HTML "Periodic Table of Amazon Web Services" by scraping service information from AWS. The project creates a Lambda function that runs monthly to regenerate the table and upload it to an S3 bucket. All images are embedded as base64 to ensure self-contained HTML.

## Commands

### Local Development

```bash
# Install dependencies into periodic/lib/ (required before first local run)
cd periodic && pip install -r requirements.txt -t lib/ && cd ..

# Run the periodic table generator locally (outputs test_*.html in project root)
cd debug
python3 test_local.py --source directory  # Directory API (default)
python3 test_local.py --source scrape      # Web scraping
python3 test_local.py --source esc         # ESC filtered version

# Generate base64 images from img/ directory
cd periodic
python3 create_base64_images.py
```

### AWS Deployment

```bash
# Prerequisites: AWS CLI configured, deploy.config created from example:
cp deploy.config.example deploy.config  # then edit with your values

# Setup buckets (one-time, use your actual values):
./setup-buckets.sh -l your-lambda-bucket -w your-domain.com -r eu-central-1

# Deploy with configuration from deploy.config
./deploy.sh

# Override individual parameters:
./deploy.sh -r us-east-1 -l my-lambda-bucket -b my-website-bucket

# Force redeployment (useful when no changes detected):
./deploy.sh -f

# Deployment without Lambda invocation (manual invocation later):
./deploy.sh -n

# View Lambda logs:
aws logs tail /aws/lambda/<function-name> --region $REGION --follow
```

### Environment Variables

Configure these on the Lambda function via AWS Console or CLI:

- `bucket`: S3 bucket name for output (required)
- `key`: Main output file name (default: `index.html`)
- `PERIODIC_DATA_SOURCE`: Data source selection (`scrape` | `directory` | `esc` | `merged`)

### Infrastructure

```bash
# Build Lambda deployment package locally
cd infrastructure
./build.sh <region> <lambda-bucket> <stack-name> <output-bucket> <output-key>

# CloudFront setup (optional):
./infrastructure/setup-cloudfront.sh <region> <stack-name> <bucket-name> <certificate-arn> <domain>
./infrastructure/setup-dns.sh <region> <stack-name> <domain> <hosted-zone-id>
```

## Architecture

### Data Sources

The Lambda function generates four HTML files from different data sources:

1. **`index_scrape.html`**: AWS Global services via web scraping from `aws.amazon.com/products/`
2. **`index_directory.html`**: AWS Global services via AWS Directory API
3. **`index_esc.html`**: AWS European Sovereign Cloud services (filtered from Directory API)
4. **`index.html`**: Default source, determined by `PERIODIC_DATA_SOURCE` environment variable

Each source creates a tab in the UI allowing users to switch between views. The `merged` source currently behaves identically to `directory`.

### Data Source Implementation

**Directory API** (`get_data_from_directory`):

- Uses AWS products directory endpoint
- Services are auto-categorized via tags (`aws-technology-categories` > `aws-tech-category` > `badge`)
- Returns ~300 services with descriptions and links
- Primary data source for Global and ESC views

**Web Scraping** (`get_data_from_scrape`):

- Scrapes `https://aws.amazon.com/products/` navigation structure
- Legacy source, maintained for consistency
- Parses JSON from globalNav script tag

**ESC Filter** (`get_data_from_esc`):

- Loads ESC service list dynamically from `https://docs.aws.eu/`
- Falls back to `periodic/esc_services.json` if dynamic fetch fails
- Filters AWS Directory data to show only ESC-available services
- ESC links redirect to `https://www.aws.eu/`
- ESC service list is cached in `ESC_SERVICES` global — loaded once per Lambda execution

### Service Symbol Generation

The `create_symbol` function generates two-letter service symbols:

1. Uses reserved symbols for known services (e.g., EC2 → "Ec2", S3 → "S3")
2. Combines first letter of words for custom names (e.g., "Simple Storage Service" → "Ss")
3. Falls back to single letters for short names, then synthetic pairs

Reserved symbols are maintained in `lambda_handler.py` `reserved_symbols` dictionary.

### Periodic Table Grid Layout

`compute_positions` maps services to CSS grid coordinates using two hardcoded layout matrices:

- `vlayout` (9×19): vertical fill pattern for the upper rows (mirrors real periodic table shape — sparse top rows, dense middle)
- `hlayout` (3×19): horizontal fill for the lanthanide/actinide-style bottom rows

Services across all categories are assigned grid positions sequentially. If service count exceeds the predefined layout, extra rows are appended at 19 columns wide. `periodic['grid_rows']` is computed and passed to the template so CSS `grid-template-rows` matches actual content.

### Template Context

The mustache templates receive these key variables:

- `categories[].services[]` — service objects with `name`, `symbol`, `row`, `column`, `color`, `link`, `long`, `reallong`
- `grid_rows` — total row count for CSS grid
- `data_sources[]` — tab metadata (filename, label, active flag)
- `show_esc_filter` — true for scrape/directory tabs (enables JS ESC highlight toggle)
- `esc_services_json` — JSON array of ESC service names for client-side filtering
- `global_regions` / `esc_regions` — region lists for the collapsible region panels
- `logo_data_uri`, `favicon_data_uri` — base64 embedded images

### Deployment Flow

1. `deploy.sh` installs Python dependencies to `periodic/lib/`
2. CloudFormation template (`infrastructure/template.yaml`) is packaged to S3
3. Stack deploys Lambda function with execution role
4. Lambda function runs monthly on the 1st at 00:00 UTC via CloudWatch Events (`cron(0 0 1 * ? *)`)
5. Generated HTML files are uploaded to S3 and compressed with Gzip
6. CloudFront cache is invalidated if distribution ID is configured

### IAM Constraints

The Lambda execution role (`infrastructure/template.yaml`) only grants S3 `PutObject` to:

- `${Bucket}/${Key}` (the main index.html)
- `${Bucket}/index_*.html` (the per-source files)

Adding new output file patterns requires updating the IAM policy in the CloudFormation template.

### Output Structure

Lambda generates HTML with embedded:

- Base64 images (logo, favicon) in `base64_images.py`
- OpenGraph meta tags (`opengraph.mustache`)
- Twitter card meta tags (`twitter.mustache`)
- Google-specific meta tags (`google.mustache`)

The main template is `periodic/base_template.mustache`, which includes:

- `periodic/template.mustache` - Periodic table grid layout
- `periodic/opengraph.mustache` - Social media cards
- `periodic/twitter.mustache` - Twitter card styles
- `periodic/google.mustache` - Google search optimization

## Development Notes

- All images must be placed in `periodic/img/` and then encoded via `create_base64_images.py`
- Template changes should be tested locally first using `test_local.py`
- The ESC service list is automatically updated monthly by the Lambda function
- Lambda timeout is 60 seconds; complex scraping may need longer
- S3 buckets require proper IAM policies for Lambda write access and CloudFront OAI read access
- `output/` directory contains generated HTML files and is gitignored

## Security

Run `snyk_code_scan` on any new first-party code. If issues are found, fix them and rescan before considering the change complete.
