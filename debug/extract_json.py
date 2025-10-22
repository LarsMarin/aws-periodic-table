#!/usr/bin/env python3
import json
import re
from bs4 import BeautifulSoup
from requests import get

raw = get('https://aws.amazon.com/products/')
soup = BeautifulSoup(raw.content, 'html.parser')

# Find all script tags
scripts = soup.find_all('script')
for idx, script in enumerate(scripts):
    if script.string and 'globalNav' in script.string and len(script.string) > 10000:
        text = script.string
        # Find the start of the JSON object
        start_idx = text.find('{"data":{"items"')
        if start_idx != -1:
            # Extract the full JSON object
            brace_count = 0
            for i in range(start_idx, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_text = text[start_idx:i+1]
                        data = json.loads(json_text)
                        # globalNav is a JSON string inside the JSON
                        nav_json_str = data['data']['items'][0]['fields']['globalNav']
                        nav_data = json.loads(nav_json_str)
                        
                        # Find Products menu
                        for item in nav_data['items']:
                            if item['name'] == 'Products':
                                print(f"Found {len(item['subNav'])} product categories")
                                for cat in item['subNav'][:3]:
                                    print(f"\nCategory: {cat['name']}")
                                    if 'columns' in cat:
                                        for col in cat['columns']:
                                            if 'items' in col:
                                                print(f"  {len(col['items'])} services")
                                                for svc in col['items'][:2]:
                                                    print(f"    - {svc['title']}")
                                break
                        break
        break
