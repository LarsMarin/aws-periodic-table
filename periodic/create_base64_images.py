#!/usr/bin/env python3
import base64
from pathlib import Path

# Read the PNG image
logo_path = Path('img/tecracer_logo_rakete.png')
with open(logo_path, 'rb') as f:
    logo_data = f.read()

# Create base64 encoding
logo_base64 = base64.b64encode(logo_data).decode('utf-8')

# Create the Python file
output = f'''# Base64-encoded images as data URIs
LOGO_DATA_URI = "data:image/png;base64,{logo_base64}"

FAVICON_DATA_URI = "data:image/png;base64,{logo_base64}"
'''

# Write to file
with open('base64_images.py', 'w') as f:
    f.write(output)

print("✓ Created base64_images.py with proper base64-encoded PNG data")
print(f"✓ Logo size: {len(logo_base64)} characters")
