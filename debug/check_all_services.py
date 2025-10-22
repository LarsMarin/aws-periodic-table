#!/usr/bin/env python3
import json
from bs4 import BeautifulSoup
from requests import get

raw = get('https://aws.amazon.com/products/')
soup = BeautifulSoup(raw.content, 'html.parser')

scripts = soup.find_all('script')
for script in scripts:
    if script.string and 'globalNav' in script.string and len(script.string) > 10000:
        text = script.string
        start_idx = text.find('{"data":{"items"')
        if start_idx != -1:
            brace_count = 0
            for i in range(start_idx, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_text = text[start_idx:i+1]
                        data = json.loads(json_text)
                        nav_json_str = data['data']['items'][0]['fields']['globalNav']
                        nav_data = json.loads(nav_json_str)
                        
                        for item in nav_data['items']:
                            if item['name'] == 'Products':
                                total = 0
                                for cat in item['subNav']:
                                    if 'columns' in cat:
                                        cat_count = 0
                                        for col in cat['columns']:
                                            if 'items' in col:
                                                cat_count += len(col['items'])
                                            if 'sections' in col:
                                                for sec in col['sections']:
                                                    if 'items' in sec:
                                                        cat_count += len(sec['items'])
                                        print(f"{cat['name']}: {cat_count} services")
                                        total += cat_count
                                print(f"\nTotal: {total} services")
                                break
                        break
        break
