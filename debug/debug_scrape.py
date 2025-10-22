#!/usr/bin/env python3
from bs4 import BeautifulSoup
from requests import get

raw = get('https://aws.amazon.com/products/')
soup = BeautifulSoup(raw.content, 'html.parser')

print("=== Checking for div.lb-item-wrapper ===")
items = soup.select("div.lb-item-wrapper")
print(f"Found {len(items)} items")

if len(items) == 0:
    print("\n=== Checking alternative selectors ===")
    
    # Try different selectors
    selectors = [
        "div.lb-content-item",
        "div[class*='lb']",
        "div[class*='product']",
        "div[class*='service']",
    ]
    
    for selector in selectors:
        items = soup.select(selector)
        print(f"{selector}: {len(items)} items")
        if len(items) > 0 and len(items) < 10:
            print(f"  First item classes: {items[0].get('class')}")
    
    print("\n=== Saving HTML for manual inspection ===")
    with open('aws_products_page.html', 'w', encoding='utf-8') as f:
        f.write(str(soup.prettify()))
    print("Saved to aws_products_page.html")
