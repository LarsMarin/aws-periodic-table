#!/usr/bin/env python3
"""
Fetch all AWS services from the AWS Price List API
This provides a more complete list than the navigation menu
"""
import json
import requests

# AWS Price List Service API
url = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json"

print("Fetching AWS services from Price List API...")
response = requests.get(url)
data = response.json()

services = []
for service_code, service_info in data['offers'].items():
    service_name = service_info.get('offerName', service_code)
    services.append({
        'code': service_code,
        'name': service_name,
        'version': service_info.get('currentVersionUrl', '')
    })

services.sort(key=lambda x: x['name'])

print(f"\nFound {len(services)} AWS services:\n")
for svc in services[:20]:  # First 20
    print(f"  - {svc['name']}")

print(f"\n... and {len(services) - 20} more")

# Save to file
with open('all_aws_services.json', 'w') as f:
    json.dump(services, f, indent=2)

print(f"\nFull list saved to all_aws_services.json")
