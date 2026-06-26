#!/usr/bin/env python3
"""
List all services with names that trigger SmallName or ReallySmallName rendering.

Run from repo root:
    python debug/audit_long_names.py

Review the REALLYLONG entries and add short aliases to `preferred_names`
in periodic/lambda_handler.py.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'periodic'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'periodic', 'lib'))

from lambda_handler import get_data_from_directory


def audit():
    print("Fetching live services...")
    data = get_data_from_directory()
    entries = [
        (len(svc['name']), svc['name'])
        for cat in data['categories']
        for svc in cat['services']
        if len(svc['name']) > 11
    ]
    entries.sort(reverse=True)

    print(f"\n=== Services with name > 11 chars ({len(entries)}) ===")
    print("SmallName = >11 chars, REALLYLONG = >20 chars (add alias to preferred_names)")
    for length, name in entries:
        tag = "  <-- REALLYLONG" if length > 20 else ""
        print(f"  {length:3d}  {name!r}{tag}")


if __name__ == '__main__':
    audit()
