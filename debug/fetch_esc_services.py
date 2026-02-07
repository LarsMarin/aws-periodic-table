#!/usr/bin/env python3
"""
Script to fetch AWS European Sovereign Cloud services from AWS Builder API
"""

import requests
import json

def fetch_esc_services():
    """Fetch ESC services from AWS Builder API"""
    
    # AWS Builder API endpoint (may need to be adjusted)
    url = "https://builder.aws.com/api/capabilities"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    params = {
        'region': 'eusc-de-east-1',
        'type': 'service'
    }
    
    try:
        print("Fetching ESC services from AWS Builder API...")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Extract service names
        services = []
        if isinstance(data, dict):
            # Try different possible data structures
            if 'services' in data:
                services = data['services']
            elif 'items' in data:
                services = [item.get('name') for item in data['items'] if item.get('name')]
        
        print(f"\nFound {len(services)} services")
        for service in services:
            print(f"  - {service}")
        
        return services
        
    except Exception as e:
        print(f"Error fetching services: {e}")
        return []

if __name__ == "__main__":
    services = fetch_esc_services()
    
    if services:
        output = {
            "metadata": {
                "last_updated": "2026-01-29",
                "source": "AWS Builder Center API",
                "region": "eusc-de-east-1 (Brandenburg, Germany)",
                "total_services": len(services),
                "description": "List of AWS services available in the European Sovereign Cloud"
            },
            "services": sorted(services)
        }
        
        with open('../periodic/esc_services.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Saved {len(services)} services to periodic/esc_services.json")
    else:
        print("\n✗ No services found. Please check the API endpoint or provide the list manually.")
