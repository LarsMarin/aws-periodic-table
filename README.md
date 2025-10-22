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
