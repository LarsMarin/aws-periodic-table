#!/usr/bin/env python3
"""
Fetch ESC services from AWS Builder Capabilities API
"""
import requests
import json

def fetch_esc_services():
    """Fetch services available in eusc-de-east-1 from AWS Builder API"""
    
    # AWS Builder Capabilities API endpoint
    api_url = "https://ext-prod-api.cloudbuilder.region-services.aws.a2z.com/listServiceFeatureAvailability"
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Request body - try without regions filter first
    payload = {}
    
    esc_services = set()
    
    print("Fetching ESC services from AWS Builder API...")
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        items = data.get('items', [])
        print(f"Found {len(items)} total items")
        
        for item in items:
            # Check if available in eusc-de-east-1
            regions = item.get('regions', [])
            if 'eusc-de-east-1' in regions:
                # Get service name
                name = item.get('serviceName') or item.get('name')
                if name:
                    esc_services.add(name)
                    print(f"  - {name}")
                
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []
    
    return sorted(list(esc_services))

if __name__ == "__main__":
    services = fetch_esc_services()
    
    print(f"\n\nFound {len(services)} ESC services")
    
    # Save to JSON
    output = {
        "metadata": {
            "last_updated": "2025-01-28",
            "source": "AWS Builder Capabilities API",
            "region": "eusc-de-east-1 (Brandenburg, Germany)",
            "total_services": len(services),
            "description": "List of AWS services available in the European Sovereign Cloud"
        },
        "services": services,
        "planned_services": {
            "2025": ["Additional services to be announced"]
        },
        "regions": {
            "available": ["eusc-de-east-1"],
            "planned": []
        }
    }
    
    output_file = "../periodic/esc_services.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved to {output_file}")
