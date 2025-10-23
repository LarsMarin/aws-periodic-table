# aws-periodic-table
Generate an HTML "Periodic Table of Amazon Web Services" by scraping service information from https://aws.amazon.com/products/. The build steps below will create a Lambda function the fires daily to regenerate the table and upload to an S3 bucket of your choice.

TO BUILD:
```
cd periodic
pip install -r requirements.txt -t .

cd ..
./build.sh <region> <lambda-bucket> <stack-name> <bucket> <key>
```  
WHERE:
```
  region - is the AWS region you'll deploy this stack to
  lambda-bucket - is used by cloudformation as a staging area for the lambda function
  stack-name - is the name you'd like to use for the cloudformation stack
  bucket - which S3 bucket would you like to copy the resulting HTML file to
  key - the name for the resulting HTML file (the S3 key)
```  

Additional utilities:
- fetch_all_services.py: Uses the AWS Price List API to produce all_aws_services.json.
- fetch_products_directory.py: Uses the public aws.com directory API to produce products_services.json and can merge with all_aws_services.json.

Examples:
```
# Fetch services from the AWS Price List API
./fetch_all_services.py

# Fetch products/services from aws.com directory (services + features)
./fetch_products_directory.py

# Merge both sources into a unified list
./fetch_products_directory.py --merge  # writes merged_all_aws_services.json
```


Using the aws.com products directory in the periodic table
- The Lambda now supports using the public AWS products directory endpoint to list services/features.
- Control via environment variables on the Lambda function:
  - PERIODIC_DATA_SOURCE: scrape (default) | directory | merged
    - scrape: use the existing products page navigation (original behavior)
    - directory: use the aws.com directory API to include all services/features (size configurable)
    - merged: currently behaves like directory; future version can merge both sources
  - PERIODIC_PRODUCTS_SIZE: number of items requested from the directory API (default: 300)

Notes
- When using the directory or merged source, services are now automatically grouped by AWS technology categories (e.g., Analytics, Compute, Storage, Developer Tools, Management & Governance, AI, Databases, Application Integration, Media Services, IoT, Migration, EUC, Business Applications, etc.).
- The generator prefers the aws-technology-categories tag from the public directory API and falls back to aws-tech-category or the badge field when needed. If no category can be derived, the item is placed into "Other".


Local testing (generate HTML without deploying)
- A helper script writes the generated HTML to output.html locally by mocking S3.
- Requirements are vendored in the periodic/ folder, so you can run it without extra installs.

Examples:
```
# Run using the aws.com directory (all services/features). Writes ../output.html
cd debug
python3 test_local.py --source directory --size 300

# Run using the legacy scrape of the Products page navigation
python3 test_local.py --source scrape

# You can also control via environment variables
PERIODIC_DATA_SOURCE=directory PERIODIC_PRODUCTS_SIZE=300 python3 test_local.py
```
Open output.html in your browser to preview the table.
