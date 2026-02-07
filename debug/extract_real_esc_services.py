#!/usr/bin/env python3
"""
Extract real ESC services from docs.aws.eu
"""
import re
import json
import urllib.parse
from bs4 import BeautifulSoup
from requests import get

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def fetch_esc_services():
    """Fetch ESC services from docs.aws.eu"""
    try:
        print("Fetching ESC services from docs.aws.eu...")
        
        esc_url = 'https://docs.aws.eu/'
        response = get(esc_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the XML data in the hidden input field
        xml_input = soup.find('input', {'id': 'landing-page-xml'})
        if xml_input and xml_input.get('value'):
            xml_data = urllib.parse.unquote(xml_input['value'])
            
            # Extract service names from <title> tags
            title_pattern = r'<title>\s*([^<]+?)\s*</title>'
            matches = re.findall(title_pattern, xml_data)
            
            esc_services = set()
            for match in matches:
                service_name = match.strip()
                # Filter out non-service entries
                if (service_name and 
                    len(service_name) < 100 and 
                    service_name not in ['Welcome to AWS Documentation', 'Featured content']):
                    esc_services.add(service_name)
            
            return sorted(list(esc_services))
        else:
            print("Could not find XML data in page")
            return []
            
    except Exception as e:
        print(f"Error fetching services: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    services = fetch_esc_services()
    
    if services:
        print(f"\n✓ Found {len(services)} ESC services:\n")
        for i, service in enumerate(services, 1):
            print(f"{i:3d}. {service}")
        
        # Save to JSON
        output = {
            "metadata": {
                "last_updated": "2026-02-06",
                "source": "docs.aws.eu (dynamically fetched)",
                "region": "eusc-de-east-1 (Brandenburg, Germany)",
                "total_services": len(services),
                "description": "List of AWS services available in the European Sovereign Cloud"
            },
            "services": services,
            "planned_services": {
                "Q1_2026": [
                    "AWS IAM Identity Center (AWS SSO)"
                ],
                "future": [
                    "Additional services to be announced"
                ]
            },
            "regions": {
                "available": [
                    "eusc-de-east-1"
                ],
                "planned": [
                    "Belgium (Sovereign Local Zone)",
                    "Netherlands (Sovereign Local Zone)",
                    "Portugal (Sovereign Local Zone)"
                ]
            }
        }
        
        output_file = "../periodic/esc_services.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved {len(services)} services to {output_file}")
    else:
        print("\n✗ No services found")
