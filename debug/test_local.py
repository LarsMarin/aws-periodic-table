#!/usr/bin/env python3
import os
import argparse
import types
from unittest.mock import MagicMock

parser = argparse.ArgumentParser(description='Run periodic table generator locally and write output.html')
parser.add_argument('--source', default=os.environ.get('PERIODIC_DATA_SOURCE', 'directory'), choices=['scrape','directory','merged'], help='Data source to use (default: directory)')
parser.add_argument('--size', type=int, default=int(os.environ.get('PERIODIC_PRODUCTS_SIZE', '300')), help='Directory API size (default: 300)')
args = parser.parse_args()

# Set env variables expected by periodic.py (must be set BEFORE loading it)
os.environ.setdefault('bucket', 'test-bucket')
os.environ.setdefault('key', 'test.html')
os.environ['PERIODIC_DATA_SOURCE'] = args.source
os.environ['PERIODIC_PRODUCTS_SIZE'] = str(args.size)

# Work inside periodic directory so template path resolves
os.chdir('../periodic')

# Prepare mocked S3 client so the code writes to a local file instead of AWS
mock_s3 = MagicMock()

def save_html(**kwargs):
    out_path = '../output.html'
    print(f"Saving HTML to {out_path} (source={args.source}, size={args.size}) ...")
    body = kwargs.get('Body', '')
    if isinstance(body, bytes):
        body = body.decode('utf-8', errors='ignore')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(body)
    print(f"Saved {len(body)} bytes")
    return {}

mock_s3.put_object = save_html

# Load periodic.py as a module and override its S3 client
with open('periodic.py', 'r', encoding='utf-8') as fh:
    code = fh.read()

module = types.ModuleType('periodic')
module.__file__ = os.path.abspath('periodic.py')
exec(code, module.__dict__)

# Replace S3 client in the loaded module
module.s3 = mock_s3

try:
    module.lambda_handler({}, None)
    print("\nSuccess! Open output.html in your browser.")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
