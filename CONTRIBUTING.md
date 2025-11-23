# Contributing to AWS Periodic Table

Thank you for your interest in contributing to the AWS Periodic Table project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)

## Getting Started

### Prerequisites

- Python 3.9 or higher
- AWS CLI configured with appropriate credentials
- Git
- Basic knowledge of AWS Lambda, S3, and CloudFormation

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/aws-periodic-table.git
cd aws-periodic-table
```

3. Add upstream remote:
```bash
git remote add upstream https://github.com/ORIGINAL_OWNER/aws-periodic-table.git
```

## Development Setup

### 1. Install Python Dependencies

```bash
cd periodic
pip install -r requirements.txt -t lib/
cd ..
```

### 2. Set Up Local Testing Environment

The project includes debug utilities for local development:

```bash
cd debug
python3 test_local.py --source directory --size 300
```

This generates `output/output.html` which you can open in a browser.

## Project Structure

```
aws-periodic-table/
├── periodic/                   # Lambda function code
│   ├── lambda_handler.py      # Main handler
│   ├── *.mustache             # HTML templates
│   ├── base64_images.py       # Embedded images
│   ├── create_base64_images.py # Image encoder
│   └── requirements.txt       # Python dependencies
├── infrastructure/            # CloudFormation templates
│   ├── template.yaml         # Main stack
│   └── *.sh                  # Deployment scripts
├── debug/                     # Development utilities
│   ├── test_local.py         # Local testing
│   └── *.py                  # Data fetching tools
└── output/                    # Generated files (gitignored)
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

Focus on one feature or bug fix per branch. Keep changes atomic and well-documented.

### 3. Test Locally

Always test your changes locally before submitting:

```bash
cd debug

# Test with Directory API
python3 test_local.py --source directory --size 300

# Test with web scraping
python3 test_local.py --source scrape

# Open the generated HTML
open ../output/output.html
```

### 4. Update Documentation

If your changes affect usage or deployment:
- Update `README.md`
- Update `periodic/lambda_deployment_instructions.md` if deployment process changes
- Add inline code comments for complex logic

## Testing

### Local Testing

Use the debug utilities to test changes:

```bash
cd debug

# Test different data sources
python3 test_local.py --source scrape
python3 test_local.py --source directory --size 300

# Fetch and inspect service data
python3 fetch_all_services.py
python3 fetch_products_directory.py

# Debug scraping
python3 debug_scrape.py

# Validate services
python3 check_all_services.py
```

### Template Testing

After modifying Mustache templates:

1. Run local test to generate HTML
2. Open in browser and check:
   - Layout and styling
   - Responsive design (resize browser)
   - Service categorization
   - Links and tooltips
   - Social media cards (use debugger tools)

### Lambda Testing

Test the Lambda function in AWS:

```bash
# Deploy to test environment
./infrastructure/build.sh us-east-1 test-lambda-bucket test-stack test-output-bucket index.html

# Invoke manually
aws lambda invoke \
  --function-name test-periodic-table-function \
  --payload '{}' \
  response.json

# Check logs
aws logs tail /aws/lambda/test-periodic-table-function --follow
```

## Code Style

### Python

- Follow PEP 8 style guide
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Keep functions focused and small
- Use type hints where appropriate

Example:
```python
def fetch_services(source: str, size: int = 300) -> list:
    """
    Fetch AWS services from specified source.
    
    Args:
        source: Data source ('scrape', 'directory', or 'merged')
        size: Maximum number of items for directory API
        
    Returns:
        List of service dictionaries
    """
    # Implementation
    pass
```

### HTML/Templates

- Use semantic HTML5 elements
- Keep templates modular and reusable
- Maintain consistent indentation (2 spaces)
- Add comments for complex template logic

### Shell Scripts

- Add shebang: `#!/bin/bash`
- Add error handling: `set -e`
- Add usage documentation
- Use meaningful variable names

## Submitting Changes

### 1. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add feature: brief description

- Detailed point 1
- Detailed point 2
- Fixes #issue-number"
```

### 2. Keep Your Fork Updated

```bash
git fetch upstream
git rebase upstream/master
```

### 3. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 4. Create Pull Request

1. Go to GitHub and create a Pull Request
2. Fill out the PR template with:
   - Description of changes
   - Testing performed
   - Screenshots (if UI changes)
   - Related issues

### 5. Code Review

- Address reviewer feedback promptly
- Keep discussions respectful and constructive
- Make requested changes in new commits
- Squash commits before merge if requested

## Adding New Features

### Adding a New Data Source

1. Modify `lambda_handler.py`:
   - Add fetching logic for new source
   - Update `get_services()` function
   - Add new output file generation

2. Update environment variables handling

3. Test thoroughly with all sources

4. Update documentation

### Adding New Service Categories

1. Modify category mapping in `lambda_handler.py`
2. Update CSS in `base_template.mustache` for new colors
3. Test with various data sources
4. Document the new categories

### Modifying Templates

1. Edit the appropriate `.mustache` file
2. Test locally with `test_local.py`
3. Check responsive design
4. Verify social media cards
5. Update documentation if needed

## Image Updates

When adding or updating images:

```bash
# 1. Add image to periodic/img/
cp new-image.png periodic/img/

# 2. Generate base64 encoding
cd periodic
python3 create_base64_images.py

# 3. Commit both the image and updated base64_images.py
git add img/ base64_images.py
git commit -m "Add new image: new-image.png"
```

## CloudFormation Changes

When modifying infrastructure:

1. Update `infrastructure/template.yaml`
2. Test deployment in isolated AWS account
3. Document parameter changes
4. Update deployment scripts if needed
5. Test rollback scenarios

## Documentation

Good documentation helps everyone:

- Keep README.md up to date
- Document new features
- Add code comments for complex logic
- Update deployment instructions
- Include examples and use cases

## Getting Help

- Open an issue for bugs or feature requests
- Ask questions in discussions
- Review existing issues and PRs

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Recognition

Contributors will be recognized in the project. Thank you for helping make AWS Periodic Table better!
