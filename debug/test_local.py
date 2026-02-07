#!/usr/bin/env python3
import os
import argparse
import types
from unittest.mock import MagicMock

parser = argparse.ArgumentParser(description='Run periodic table generator locally and write output.html')
parser.add_argument('--source', default=os.environ.get('PERIODIC_DATA_SOURCE', 'directory'), choices=['scrape','directory','merged','esc'], help='Data source to use (default: directory)')
parser.add_argument('--size', type=int, default=int(os.environ.get('PERIODIC_PRODUCTS_SIZE', '300')), help='Directory API size (default: 300)')
args = parser.parse_args()

# Set env variables expected by periodic.py (must be set BEFORE loading it)
os.environ.setdefault('bucket', 'test-bucket')
os.environ.setdefault('key', 'test.html')
os.environ['PERIODIC_DATA_SOURCE'] = args.source
os.environ['PERIODIC_PRODUCTS_SIZE'] = str(args.size)

# Work inside periodic directory so template path resolves
periodic_dir = os.path.abspath('../periodic')
os.chdir(periodic_dir)

# Add periodic directory to Python path so imports work
import sys
if periodic_dir not in sys.path:
    sys.path.insert(0, periodic_dir)

# Prepare mocked S3 client so the code writes to a local file instead of AWS
mock_s3 = MagicMock()

def save_html(**kwargs):
    # Für lokale Tests: Dekomprimiere Gzip-Daten wenn nötig
    body = kwargs.get('Body', '')
    
    # Prüfe ob Body Gzip-komprimiert ist
    if isinstance(body, bytes):
        # Versuche zu dekomprimieren
        try:
            import gzip
            body = gzip.decompress(body).decode('utf-8')
        except:
            # Falls nicht komprimiert, einfach dekodieren
            body = body.decode('utf-8', errors='ignore')
    
    # Bestimme Ausgabedatei basierend auf dem Key
    key = kwargs.get('Key', 'output.html')
    if key.startswith('test_'):
        out_path = f'../{key}'
    else:
        out_path = '../output.html'
    
    print(f"Saving HTML to {out_path} (source={args.source}, size={args.size}) ...")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(body)
    print(f"Saved {len(body)} bytes")
    return {}

mock_s3.put_object = save_html

# Load lambda_handler.py as a module and override its S3 client
with open('lambda_handler.py', 'r', encoding='utf-8') as fh:
    code = fh.read()

module = types.ModuleType('lambda_handler')
module.__file__ = os.path.abspath('lambda_handler.py')
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
