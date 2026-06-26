#!/usr/bin/env python3
"""
Audit reserved_symbols for stale entries and list auto-generated symbols.

Run from repo root:
    cd periodic && pip install -r requirements.txt -t lib/ && cd ..
    python debug/audit_symbols.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'periodic'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'periodic', 'lib'))

from lambda_handler import get_data_from_directory, reserved_symbols


def audit():
    print("Fetching live services from Directory API...")
    data = get_data_from_directory()
    all_services = [svc for cat in data['categories'] for svc in cat['services']]
    live_names = {svc['name'] for svc in all_services}

    # Stale: in reserved_symbols but not in live data
    stale = {sym: name for sym, name in reserved_symbols.items() if name not in live_names}
    print(f"\n=== Stale reserved_symbols ({len(stale)}) ===")
    print("(These entries no longer match any live service — consider removing)")
    for sym, name in sorted(stale.items()):
        print(f"  {sym!r:10s} -> {name!r}")

    # Auto-generated: live services not covered by reserved_symbols
    reserved_names = set(reserved_symbols.values())
    auto = [(svc['name'], svc['symbol']) for svc in all_services if svc['name'] not in reserved_names]
    print(f"\n=== Auto-generated symbols ({len(auto)}) ===")
    print("(Review these — add important ones to reserved_symbols in lambda_handler.py)")
    for name, sym in sorted(auto, key=lambda x: x[0]):
        print(f"  {sym!r:10s} -> {name!r}")

    print(f"\nTotal live services: {len(all_services)}")


if __name__ == '__main__':
    audit()
