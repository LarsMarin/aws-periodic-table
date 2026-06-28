#!/usr/bin/env python3
"""Generate base64_images.py and resize favicon to PWA icon sizes.

Run from periodic/ directory:
    python3 create_base64_images.py
"""
import base64
from pathlib import Path
from PIL import Image

# ── Base64 encode logo and favicon ──────────────────────────────────────────

logo_path = Path('img/tecracer_logo_rakete.png')
with open(logo_path, 'rb') as f:
    logo_data = f.read()

favicon_path = Path('img/favicon.png')
with open(favicon_path, 'rb') as f:
    favicon_data = f.read()

logo_base64 = base64.b64encode(logo_data).decode('utf-8')
favicon_base64 = base64.b64encode(favicon_data).decode('utf-8')

output = f'''# Base64-encoded images as data URIs
LOGO_DATA_URI = "data:image/png;base64,{logo_base64}"

FAVICON_DATA_URI = "data:image/png;base64,{favicon_base64}"
'''

with open('base64_images.py', 'w') as f:
    f.write(output)

print(f"✓ Created base64_images.py (logo: {len(logo_base64)} chars, favicon: {len(favicon_base64)} chars)")

# ── Resize favicon to PWA icon sizes ────────────────────────────────────────

favicon_img = Image.open('img/favicon.png').convert('RGBA')
for size in [192, 512]:
    icon = favicon_img.resize((size, size), Image.LANCZOS)
    icon.save(f'img/icon-{size}.png')
    print(f"✓ Created img/icon-{size}.png")
