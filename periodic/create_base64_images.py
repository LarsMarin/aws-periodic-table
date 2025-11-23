#!/usr/bin/env python3
import base64
from pathlib import Path

# Read the logo PNG image
logo_path = Path('img/tecracer_logo_rakete.png')
with open(logo_path, 'rb') as f:
    logo_data = f.read()

# Read the favicon PNG image
favicon_path = Path('img/favicon.png')
with open(favicon_path, 'rb') as f:
    favicon_data = f.read()

# Create base64 encodings
logo_base64 = base64.b64encode(logo_data).decode('utf-8')
favicon_base64 = base64.b64encode(favicon_data).decode('utf-8')

# Create the Python file
output = f'''# Base64-encoded images as data URIs
LOGO_DATA_URI = "data:image/png;base64,{logo_base64}"

FAVICON_DATA_URI = "data:image/png;base64,{favicon_base64}"
'''

# Write to file
with open('base64_images.py', 'w') as f:
    f.write(output)

print("✓ Created base64_images.py with proper base64-encoded PNG data")
print(f"✓ Logo size: {len(logo_base64)} characters")
print(f"✓ Favicon size: {len(favicon_base64)} characters")
