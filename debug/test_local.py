#!/usr/bin/env python3
import sys
import os

# Mock environment variables
os.environ['bucket'] = 'test-bucket'
os.environ['key'] = 'test.html'

# Change to periodic directory for file access
os.chdir('../periodic')

# Mock S3 before any imports
import boto3
from unittest.mock import MagicMock

mock_s3 = MagicMock()
def save_html(**kwargs):
    print("Saving HTML to output.html...")
    with open('../output.html', 'w', encoding='utf-8') as f:
        f.write(kwargs['Body'])
    print(f"Saved {len(kwargs['Body'])} bytes")
    return {}
mock_s3.put_object = save_html

# Load the periodic.py file directly with __file__ set
code = open('periodic.py').read()
exec(code, {'__file__': os.path.abspath('periodic.py'), '__name__': '__main__'})

# Get the lambda_handler from the executed code
import types
module = types.ModuleType('periodic')
module.__file__ = os.path.abspath('periodic.py')
exec(code, module.__dict__)

# Replace s3 in the module
module.s3 = mock_s3

try:
    module.lambda_handler({}, None)
    print("\nSuccess! Check output.html")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
