#!/usr/bin/env python3
"""
Fetch AWS products from the public aws.com directory API and optionally merge
with the existing Price List services file (all_aws_services.json).

Why: The Products directory includes services and features that may be missing
from the Price List API. This script lets you pull those and generate a
complementary list, or merge them into a unified output.

Usage:
  - Just fetch the products directory and save to products_services.json
      ./fetch_products_directory.py

  - Fetch and merge with all_aws_services.json (from fetch_all_services.py)
      ./fetch_products_directory.py --merge

Outputs:
  - products_services.json                # Raw list from aws.com directory API
  - merged_all_aws_services.json (--merge) # Unified list with "sources" info

Notes:
  - The endpoint and query params are taken from the user-provided URL and
    tuned to return up to 300 items, English locale, products+features types.
  - If more than 300 exist, you can adjust the size/pagination parameters.
"""
import argparse
import json
import sys
from typing import Dict, List

import requests

AWS_PRODUCTS_API = (
    "https://aws.amazon.com/api/dirs/items/search"
    "?item.directoryId=products-cards-interactive-aws-products-ams"
    "&item.locale=en_US"
    "&tags.id=GLOBAL%23local-tags-aws-products-type%23service%7C"
    "GLOBAL%23local-tags-aws-products-type%23feature"
    "&sort_by=item.dateCreated"
    "&sort_order=asc"
    "&size=300"
)

PRODUCTS_JSON = "products_services.json"
PRICE_LIST_JSON = "all_aws_services.json"
MERGED_JSON = "merged_all_aws_services.json"


def fetch_products() -> List[Dict]:
    resp = requests.get(AWS_PRODUCTS_API, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("items", [])

    normalized = []
    for it in items:
        fields = it.get("item", {}).get("additionalFields", {})
        # Prefer productTitle; fallback to cardTitle or item title
        name = (
            fields.get("productTitle")
            or fields.get("cardTitle")
            or it.get("item", {}).get("title")
        )
        # Create a stable id/code if possible
        code = (
            fields.get("productName")  # sometimes has an internal name
            or fields.get("skuCode")
            or fields.get("id")
            or it.get("id")
        )
        # Build a nice URL to the product if provided
        url = None
        if "url" in fields:
            url = fields.get("url")
        else:
            # Try to derive a URL from link text
            link = fields.get("link") or fields.get("learnMoreLink")
            if isinstance(link, dict):
                url = link.get("href")
            elif isinstance(link, str):
                url = link

        # Type (service/feature) from tag or additionalField
        ptype = fields.get("productType") or it.get("tags", [{}])[0].get("name")

        if not name:
            # Skip entries without a name
            continue

        normalized.append(
            {
                "code": str(code) if code else None,
                "name": name.strip(),
                "type": ptype or None,
                "url": url,
                "source": "aws_products_directory",
            }
        )

    # De-dupe by name (case-insensitive)
    seen = set()
    unique = []
    for n in normalized:
        key = n["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(n)

    return unique


def load_json(path: str) -> List[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def merge_lists(price_list: List[Dict], products: List[Dict]) -> List[Dict]:
    # Build index by lowercase name and by code for the price list
    by_name = { (x.get("name") or "").lower(): i for i, x in enumerate(price_list) }
    by_code = { (x.get("code") or "").lower(): i for i, x in enumerate(price_list) if x.get("code") }

    merged = price_list.copy()

    def add_source(entry: Dict, src: str):
        if "sources" not in entry:
            # migrate from single 'source'
            srcs = []
            if entry.get("source"):
                srcs.append(entry["source"])
                del entry["source"]
            entry["sources"] = srcs
        if src not in entry["sources"]:
            entry["sources"].append(src)

    # Prime sources for price list entries
    for e in merged:
        add_source(e, "aws_price_list")

    # Merge products: match by name first, then by code
    for p in products:
        name_key = (p.get("name") or "").lower()
        code_key = (p.get("code") or "").lower()

        idx = None
        if name_key in by_name:
            idx = by_name[name_key]
        elif code_key and code_key in by_code:
            idx = by_code[code_key]

        if idx is not None:
            # augment existing entry
            tgt = merged[idx]
            # Prefer keeping existing code/name, but fill missing fields
            for k in ("type", "url"):
                if not tgt.get(k) and p.get(k):
                    tgt[k] = p[k]
            add_source(tgt, "aws_products_directory")
        else:
            # Add as a new entry
            new_entry = {
                "code": p.get("code"),
                "name": p.get("name"),
                "type": p.get("type"),
                "url": p.get("url"),
                "sources": ["aws_products_directory"],
            }
            merged.append(new_entry)
            # update indices
            by_name[name_key] = len(merged) - 1
            if code_key:
                by_code[code_key] = len(merged) - 1

    # Sort for stable output by name
    merged.sort(key=lambda x: (x.get("name") or "").lower())
    return merged


def main():
    parser = argparse.ArgumentParser(description="Fetch AWS products directory and optionally merge with Price List services")
    parser.add_argument("--merge", action="store_true", help="Merge with all_aws_services.json and write merged_all_aws_services.json")
    args = parser.parse_args()

    products = fetch_products()

    with open(PRODUCTS_JSON, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(products)} products to {PRODUCTS_JSON}")

    if args.merge:
        price_list = load_json(PRICE_LIST_JSON)
        merged = merge_lists(price_list, products)
        with open(MERGED_JSON, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
        print(
            f"Merged {len(products)} products with {len(price_list)} price-list services -> {len(merged)} total (saved to {MERGED_JSON})"
        )


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
            print(f"HTTP error while fetching products: {e}", file=sys.stderr)
            sys.exit(2)
    except requests.RequestException as e:
            print(f"Network error while fetching products: {e}", file=sys.stderr)
            sys.exit(2)
