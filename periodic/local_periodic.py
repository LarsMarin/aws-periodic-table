# coding=utf-8
import os, sys
# Add lib directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

import re, json, boto3, pystache

from bs4 import BeautifulSoup
from requests import get

# Optional: Wählen Sie Datenquelle und Verzeichnis-API-Größe über die Umgebung
DATA_SOURCE = os.environ.get('PERIODIC_DATA_SOURCE', 'scrape')  # scrape | directory | merged (merged behaves like directory for now)
PRODUCTS_SIZE = int(os.environ.get('PERIODIC_PRODUCTS_SIZE', '300'))
OUTPUT_PATH = os.environ.get('OUTPUT_PATH', 'output.html')

# AWS Products Directory endpoint template
AWS_PRODUCTS_API = (
  "https://aws.amazon.com/api/dirs/items/search?"
  "item.directoryId=products-cards-interactive-aws-products-ams"
  "&item.locale=en_US"
  "&tags.id=GLOBAL%23local-tags-aws-products-type%23service%7CGLOBAL%23local-tags-aws-products-type%23feature"
  "&sort_by=item.dateCreated&sort_order=asc"
  f"&size={PRODUCTS_SIZE}"
)

# Common HTTP headers to mimic a browser (helps aws.com endpoints return full data)
HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
  'Accept': 'application/json, text/plain, */*',
  'Accept-Language': 'en-US,en;q=0.9',
  'Referer': 'https://aws.amazon.com/products/',
}

# Set up dummy S3 client for local use
s3 = boto3.client('s3', 
                  aws_access_key_id='dummy', 
                  aws_secret_access_key='dummy',
                  region_name='us-east-1',
                  endpoint_url='http://localhost:8000')

# Reserve keywords for special cases, including single and 3-letter symbols
reserved_symbols = {
  "Mx"  : "Apache MXNet on AWS", 
  "Tf"  : "TensorFlow on AWS", 
  "Eks" : "Elastic Container Service for Kubernetes", 
  "Ecs" : "Elastic Container Service", 
  "Db"  : "DocumentDB", 
  "53"  : "Route 53", 
  "X"   : "X-Ray", 
  "Ami" : "Deep Learning AMIs", 
  "Phd" : "Personal Health Dashboard", 
  "Cs"  : "CloudSearch", 
  "L"   : "Lambda", 
  "S3"  : "Simple Storage Service", 
  "A"   : "Athena", 
  "Vpc" : "VPC", 
  "Ec2" : "EC2", 
  "C9"  : "Cloud9", 
  "Gt"  : "SageMaker Ground Truth", 
  "Sns" : "Simple Notification Service", 
  "Sqs" : "Simple Queue Service", 
  "Hsm" : "CloudHSM", 
  "Ebs" : "Elastic Block Store", 
  "Cli" : "Command Line Interface", 
  "Cf"  : "CloudFront", 
  "Cm"  : "Cloud Map", 
  "Gl"  : "S3 Glacier", 
  "Sdk" : "Tools and SDKs", 
  "Lx"  : "Lex", 
  "M"   : "Macie", 
  "K"   : "Managed Streaming for Kafka", 
  "Emr" : "EMR", 
  "F"   : "Fargate"
}

# For reverse lookup  
reserved_services = dict(map(reversed, reserved_symbols.items()))

# Some names are just to long to display, shorten them here
preferred_names = {
  "Elastic Container Service for Kubernetes": "ECS for Kubernetes", 
  "Serverless Application Repository":"Serverless App Repo" 
}

# Default colors
colors = ["#834187", "#878541", "#458741", "#874145", 
          "#c92d39", "#3ac92d", "#2d44c9", "#c9762d", 
          "#ef8d22", "#2c22ef", "#ef22e5", "#e5ef22", 
          "#fcc438", "#8d38fc", "#fc38a7", "#a7fc38", 
          "#7ab648", "#b6487a", "#b66548", "#48adb6", 
          "#3aa6dd", "#dd703a", "#ddc23a", "#a73add"]

# Parse prefix and name
def parse_name(name):

    search = re.search( r"(AWS|Amazon)*\s*(.*)", name )
    prefix = search.group(1) or 'AWS'
    name = search.group(2)
    name = name.split("(",2)[0].strip()

    return prefix, name

# Create a symbol, roughly:
# 1. Use a pre-defined symbol
# 2. Create a 2 letter symbol using first letters of words in name
# 3. Create a 2 letter symbol using fallback sequence if needed (handles 1-letter names)
def create_symbol(symbols, name):
  
    symbol = ""
    if name in reserved_services:
      # We have a specific symbol to use for this service
      symbol = reserved_services[name]
      symbols[symbol] = name
    else:
      cleaned = re.sub(r"[&,-/.]","",name)
      words = cleaned.split(' ')
      words = [ elem for elem in words if not elem.islower() ]

      # Build candidate character pool from words
      initials = [ w[0:1] for w in words if w ]
      tails = [ w[1:] for w in words if len(w) > 1 ]
      chars = "".join(initials + tails)

      # Primary strategy: combine first char with following chars from pool
      for idx, first in enumerate(chars):
        first_up = first.upper()
        # prefer combining with subsequent chars
        for char in chars[idx+1:]:
          candidate = first_up + char.lower()
          if candidate not in symbols:
            symbols[candidate] = name
            reserved_services[name] = candidate
            symbol = candidate
            break
        if symbol:
          break

      # Fallback for very short names, e.g., "Q": allow single-letter or synthesize pairs
      if not symbol and chars:
        first_up = chars[0].upper()
        # Try single-letter if free
        if first_up not in symbols:
          symbols[first_up] = name
          reserved_services[name] = first_up
          symbol = first_up
        else:
          # Try first letter + a fallback sequence
          for suf in list('abcdefghijklmnopqrstuvwxyz') + list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') + ['1','2','3']:
            candidate = first_up + suf
            if candidate not in symbols:
              symbols[candidate] = name
              reserved_services[name] = candidate
              symbol = candidate
              break

    if not symbol:
      print("Couldn't generate symbol for %s: %s" % (name, chars if 'chars' in locals() else name))

    return symbol
    
title = "Periodic Table of Amazon Web Services"
description = "Periodic Table of Amazon Web Services"

def main():

  # Anzeige der aktuellen Konfiguration
  source_type = "Web Scraping" if DATA_SOURCE == "scrape" else "Directory API" 
  if DATA_SOURCE == "merged":
      source_type = "Combined Sources"
  
  print(f"Generiere Periodentabelle mit Datenquelle: {source_type}")
  print(f"Ausgabedatei: {OUTPUT_PATH}")

  periodic = {'categories':[], 'title':title, 'description':description}
  
  # Symbols already used
  symbols = {}
  
  # Services already processed
  names = {}

  
  if DATA_SOURCE in ('directory', 'merged'):
    # Use AWS Products Directory endpoint to get services/features
    try:
      dj = get(AWS_PRODUCTS_API, headers=HEADERS, timeout=20)
      dj.raise_for_status()
      data = dj.json()
    except Exception as e:
      print("Failed to fetch directory API: %s" % e)
      data = {"items": []}
    items = data.get('items', [])

    # Group items into categories using aws-technology-categories (preferred),
    # falling back to aws-tech-category / badge, else 'Other'.
    def friendly_from_slug(slug):
      mapping = {
        'analytics': 'Analytics', 'data-analytics': 'Analytics',
        'compute': 'Compute',
        'storage': 'Storage',
        'networking-content-dev': 'Networking', 'networking': 'Networking',
        'devtools': 'Developer Tools', 'developer-tools': 'Developer Tools',
        'mgmt-govern': 'Management & Governance', 'management-governance': 'Management & Governance',
        'ai-ml': 'Artificial Intelligence (AI)', 'machine-learning': 'Artificial Intelligence (AI)', 'ai': 'Artificial Intelligence (AI)',
        'databases': 'Databases',
        'app-integration': 'Application Integration', 'application-integration': 'Application Integration',
        'media-services': 'Media Services',
        'iot': 'Internet of Things',
        'migration': 'Migration',
        'euc': 'End-User Computing (EUC)', 'end-user-computing-euc': 'End-User Computing (EUC)',
        'business-apps': 'Business Applications', 'business-applications': 'Business Applications',
        'arch-strategy': 'Architecture Strategy', 'architecture-strategy': 'Architecture Strategy',
        'satellite': 'Aerospace & Satellite', 'aerospace-satellite': 'Aerospace & Satellite',
        'quantum': 'Quantum Technologies',
        'blockchain': 'Blockchain',
        'games': 'Game Tech', 'game-tech': 'Game Tech',
        'cost-mgmt': 'Cloud Financial Management', 'cloud-financial-management': 'Cloud Financial Management',
        'serverless': 'Serverless', 'mobile': 'Mobile'
      }
      return mapping.get(slug.strip().lower()) if isinstance(slug, str) else None

    def derive_category_name(item_obj):
      tags = item_obj.get('tags', [])
      # Prefer aws-technology-categories (proper cased names)
      for tg in tags:
        if tg.get('tagNamespaceId') == 'GLOBAL#aws-technology-categories':
          nm = tg.get('name') or ''
          if nm:
            return nm
      # Fallback: aws-tech-category slug → friendly
      for tg in tags:
        if tg.get('tagNamespaceId') == 'GLOBAL#aws-tech-category':
          fr = friendly_from_slug(tg.get('name', ''))
          if fr:
            return fr
      # Secondary fallback: additionalFields.badge JSON containing category labels
      af = item_obj.get('item', {}).get('additionalFields', {})
      badge = af.get('badge')
      if isinstance(badge, str):
        try:
          bj = json.loads(badge)
          vals = bj.get('value') if isinstance(bj, dict) else None
          if isinstance(vals, list) and vals:
            return vals[0]
        except Exception:
          pass
      # Default
      return 'Other'

    categories_by_name = {}
    color_index = 0

    for it in items:
      fields = it.get('item', {}).get('additionalFields', {})

      # Prefer human-readable title from additionalFields
      name = (
        fields.get('title')
        or fields.get('productTitle')
        or fields.get('cardTitle')
        or it.get('item', {}).get('title')
      )
      # Fallback: derive from the slug "item.name" if needed
      if not name:
        slug = it.get('item', {}).get('name')
        if isinstance(slug, str) and slug:
          name = slug.replace('-', ' ').replace('_', ' ').title()

      if not name:
        # Still no usable name, skip this entry
        continue

      if name in names:
        continue
      names[name] = 1

      # Description: prefer rich body text, strip HTML tags if present
      desc = fields.get('body') or fields.get('blurb') or fields.get('description') or ''
      if isinstance(desc, str) and '<' in desc and '>' in desc:
        try:
          desc = BeautifulSoup(desc, 'html.parser').get_text(" ", strip=True)
        except Exception:
          pass

      # Link: prefer CTA link, then other known link fields
      link = (
        fields.get('ctaLink')
        or fields.get('primaryCTALink')
        or fields.get('secondaryCTALink')
        or fields.get('url')
      )
      if not link:
        lnk = fields.get('link') or fields.get('learnMoreLink')
        if isinstance(lnk, dict):
          link = lnk.get('href')
        elif isinstance(lnk, str):
          link = lnk

      # Determine category
      cname = derive_category_name(it)
      cclass = re.sub(r"[&, ]",'',cname)
      if cname not in categories_by_name:
        categories_by_name[cname] = {"name": cname, "services": [], "color": colors[color_index % len(colors)], "class": cclass}
        color_index += 1

      prefix, clean_name = parse_name(name)
      symbol = create_symbol(symbols, clean_name)
      if clean_name in preferred_names:
        clean_name = preferred_names[clean_name]

      categories_by_name[cname]['services'].append({
        'name': clean_name,
        'desc': desc,
        'link': link or '',
        'prefix': prefix,
        'symbol': symbol,
        'category': cclass,
        'long': len(clean_name) > 11,
        'reallong': len(clean_name) > 20
      })

    # Append categories in insertion order; if empty, leave to fallback
    for cat in categories_by_name.values():
      if cat['services']:
        periodic['categories'].append(cat)

    # If directory API returned no services, fallback to scraping products page to avoid empty output
    if not periodic['categories']:
      print("Directory API returned no items, falling back to scrape path...")
      try:
        raw = get('https://aws.amazon.com/products/', headers=HEADERS, timeout=20)
        soup = BeautifulSoup(raw.content, 'html.parser')
        # Extract JSON data from the page
        scripts = soup.find_all('script')
        nav_data = None
        for script in scripts:
          if script.string and 'globalNav' in script.string and len(script.string) > 10000:
            text = script.string
            start_idx = text.find('{"data":{"items"')
            if start_idx != -1:
              brace_count = 0
              for i in range(start_idx, len(text)):
                if text[i] == '{':
                  brace_count += 1
                elif text[i] == '}':
                  brace_count -= 1
                  if brace_count == 0:
                    json_text = text[start_idx:i+1]
                    data = json.loads(json_text)
                    nav_json_str = data['data']['items'][0]['fields']['globalNav']
                    nav_data = json.loads(nav_json_str)
                    break
            break
        if nav_data:
          ccount = 0
          products_menu = None
          for item in nav_data['items']:
            if item['name'] == 'Products':
              products_menu = item
              break
          if products_menu and 'subNav' in products_menu:
            for cat_item in products_menu['subNav']:
              if cat_item['name'] == 'Featured Products' or 'columns' not in cat_item:
                continue
              cname = cat_item['name']
              cclass = re.sub(r"[&, ]",'',cname)
              category = {"name": cname, "services":[], "color": colors[ccount % len(colors)], "class":cclass}
              ccount += 1
              for column in cat_item['columns']:
                items_to_process = []
                if 'items' in column:
                  items_to_process.extend(column['items'])
                if 'sections' in column:
                  for section in column['sections']:
                    if 'items' in section:
                      items_to_process.extend(section['items'])
                for item in items_to_process:
                  name = item['title']
                  if name in names:
                    continue
                  names[name] = 1
                  desc = item.get('body', '')
                  link = item.get('hyperLink', '')
                  prefix, clean_name = parse_name(name)
                  symbol = create_symbol(symbols, clean_name)
                  if clean_name in preferred_names:
                    clean_name = preferred_names[clean_name]
                  category["services"].append({
                    "name": clean_name,
                    "desc": desc,
                    "link": link,
                    "prefix": prefix,
                    "symbol": symbol,
                    "category": cclass,
                    "long": len(clean_name) > 11,
                    "reallong": len(clean_name) > 20
                  })
              if category["services"]:
                periodic['categories'].append(category)
        else:
          print("Could not find product data in page during fallback scrape")
      except Exception as e:
        print("Fallback scrape failed: %s" % e)

  else:
    raw = get('https://aws.amazon.com/products/', headers=HEADERS, timeout=20)
    soup = BeautifulSoup(raw.content, 'html.parser')
    
    # Extract JSON data from the page
    scripts = soup.find_all('script')
    nav_data = None
    for script in scripts:
      if script.string and 'globalNav' in script.string and len(script.string) > 10000:
        text = script.string
        start_idx = text.find('{"data":{"items"')
        if start_idx != -1:
          brace_count = 0
          for i in range(start_idx, len(text)):
            if text[i] == '{':
              brace_count += 1
            elif text[i] == '}':
              brace_count -= 1
              if brace_count == 0:
                json_text = text[start_idx:i+1]
                data = json.loads(json_text)
                nav_json_str = data['data']['items'][0]['fields']['globalNav']
                nav_data = json.loads(nav_json_str)
                break
          break
    
    if not nav_data:
      print("Could not find product data in page")
      return
    
    # Parse the navigation data
    ccount = 0
    products_menu = None
    for item in nav_data['items']:
      if item['name'] == 'Products':
        products_menu = item
        break
    
    if not products_menu or 'subNav' not in products_menu:
      print("Could not find Products menu")
      return
    
    # Process each category
    for cat_item in products_menu['subNav']:
      if cat_item['name'] == 'Featured Products' or 'columns' not in cat_item:
        continue
      
      cname = cat_item['name']
      cclass = re.sub(r"[&, ]",'',cname)
      category = {"name": cname, "services":[], "color": colors[ccount % len(colors)], "class":cclass}
      ccount += 1
      
      # Process services in this category
      for column in cat_item['columns']:
        items_to_process = []
        
        if 'items' in column:
          items_to_process.extend(column['items'])
        
        if 'sections' in column:
          for section in column['sections']:
            if 'items' in section:
              items_to_process.extend(section['items'])
        
        for item in items_to_process:
          name = item['title']
          if name in names:
            continue
          names[name] = 1
          
          desc = item.get('body', '')
          link = item.get('hyperLink', '')
          
          prefix, clean_name = parse_name(name)
          symbol = create_symbol(symbols, clean_name)
          
          if clean_name in preferred_names:
            clean_name = preferred_names[clean_name]
          
          category["services"].append({
            "name": clean_name,
            "desc": desc,
            "link": link,
            "prefix": prefix,
            "symbol": symbol,
            "category": cclass,
            "long": len(clean_name) > 11,
            "reallong": len(clean_name) > 20
          })
      
      if category["services"]:
        periodic['categories'].append(category)
  
    
  # Vertical order for topmost rows
  vlayout = [
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
    [1,1,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1],
    [1,1,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
  ]
  vlayout  = list(zip(*vlayout)) # transpose for easier handling
  
  # Horizontal layout for bottom 3+ rows
  hlayout = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
  ]
  
  indices = []
  hrow = 0
  for row in range(0,len(vlayout)):
    for col in range(0, len(vlayout[row])):
      if vlayout[row][col]:
        indices.append([hrow+col+1, row+1])
        
  hrow = col + 2
  for row in range(0,len(hlayout)):
    for col in range(0, len(hlayout[row])):
      if hlayout[row][col]:
        indices.append([hrow+row+1, col+1])
  
  # Ensure we have enough indices for all services
  total_services = sum(len(cat.get("services", [])) for cat in periodic['categories'])
  if total_services > len(indices):
    extra = total_services - len(indices)
    # Determine starting row after the predefined layout
    start_row = (indices[-1][0] + 1) if indices else 1
    # Fill extra indices row-wise across 19 columns per row
    COLS = 19
    for i in range(extra):
      row = start_row + (i // COLS)
      col = (i % COLS) + 1
      indices.append([row, col])
  
  # Assign computed positions
  count = 0
  for category in periodic['categories']:
    for service in category["services"]:
      service['row'] = indices[count][0]
      service['column'] = indices[count][1]
      count = count + 1
  
  # Compute required grid rows for template (at least 18 to preserve original look)
  periodic['grid_rows'] = max(18, max((pos[0] for pos in indices[:total_services]), default=18))
  
  # Lade das Template und rendere das HTML
  template_path = os.path.join(os.path.dirname(__file__), 'template.mustache')
  with open(template_path, 'r') as f:  
    template = f.read()
    html = pystache.render(template, periodic)
    
    # Speichere das HTML in der Ausgabedatei
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as out_file:
      out_file.write(html)
      print(f"HTML wurde in {OUTPUT_PATH} gespeichert.")

if __name__ == "__main__":
  main()
