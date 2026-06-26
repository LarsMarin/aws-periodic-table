import os, sys
# Add lib directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

import re, json, boto3, pystache, gzip
from datetime import datetime
from bs4 import BeautifulSoup
from requests import get

# Import embedded images
from base64_images import LOGO_DATA_URI, FAVICON_DATA_URI

# Optional: Wählen Sie Datenquelle und Verzeichnis-API-Größe über die Umgebung
# Unterstützte Quellen: scrape, directory, esc (merged verhält sich derzeit wie directory)
SUPPORTED_SOURCES = ['scrape', 'directory', 'esc']
DEFAULT_SOURCE = os.environ.get('PERIODIC_DATA_SOURCE', 'scrape')

# AWS Products Directory endpoint template
AWS_PRODUCTS_API = (
  "https://aws.amazon.com/api/dirs/items/search?"
  "item.directoryId=products-cards-interactive-aws-products-ams"
  "&item.locale=en_US"
  "&tags.id=GLOBAL%23local-tags-aws-products-type%23service%7CGLOBAL%23local-tags-aws-products-type%23feature"
  "&sort_by=item.dateCreated&sort_order=asc"
  f"&size={int(os.environ.get('PERIODIC_PRODUCTS_SIZE', '300'))}"
)

# Common HTTP headers to mimic a browser (helps aws.com endpoints return full data)
HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
  'Accept': 'application/json, text/plain, */*',
  'Accept-Language': 'en-US,en;q=0.9',
  'Referer': 'https://aws.amazon.com/products/',
}

bucket = os.environ.get('bucket', '')
key = os.environ.get('key', 'index.html')
key_prefix = key.rsplit('.', 1)[0] if '.' in key else key

# Initialisiere S3-Client
s3 = boto3.client('s3')

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

# Load ESC services dynamically from docs.aws.eu
def load_esc_services():
    """
    Load the list of services available in AWS European Sovereign Cloud.
    Fetches dynamically from docs.aws.eu documentation page.
    Falls back to esc_services.json if dynamic fetch fails.
    """
    try:
        print("Fetching ESC services from docs.aws.eu...")
        
        import urllib.parse
        
        esc_url = 'https://docs.aws.eu/'
        response = get(esc_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        xml_input = soup.find('input', {'id': 'landing-page-xml'})
        if xml_input and xml_input.get('value'):
            xml_data = urllib.parse.unquote(xml_input['value'])
            
            title_pattern = r'<title>\s*([^<]+?)\s*</title>'
            matches = re.findall(title_pattern, xml_data)
            
            # Only filter out obvious non-service entries
            excluded_entries = {
                'Welcome to AWS Documentation', 'Featured content',
                'Getting started with AWS European Sovereign Cloud Regions'
            }
            
            esc_services = set()
            for match in matches:
                service_name = match.strip()
                # Clean up whitespace issues
                service_name = ' '.join(service_name.split())
                
                if (service_name and
                    len(service_name) < 100 and
                    service_name not in excluded_entries and
                    not service_name.startswith('Getting started')):
                    esc_services.add(service_name)
            
            if len(esc_services) >= 50:  # Expect at least 50 real services
                print(f"Fetched {len(esc_services)} ESC services dynamically")
                return esc_services
        
        print("Dynamic fetch returned insufficient data")
        
    except Exception as e:
        print(f"Dynamic fetch failed: {e}")
    
    # Fallback to esc_services.json
    print("Using fallback ESC service list from esc_services.json")
    try:
        esc_json_path = os.path.join(os.path.dirname(__file__), 'esc_services.json')
        with open(esc_json_path, 'r', encoding='utf-8') as f:
            esc_data = json.load(f)
            services = esc_data.get('services', [])
            if services:
                warning = check_esc_freshness(esc_data.get('updated', ''))
                if warning:
                    print(warning)
                print(f"Loaded {len(services)} services from esc_services.json")
                return set(services)
    except Exception as e:
        print(f"Failed to load esc_services.json: {e}")
    
    # Final fallback to minimal known list
    print("Using minimal fallback ESC service list")
    return {
        'Amazon EC2', 'AWS Lambda', 'Amazon ECS', 'Amazon EKS',
        'Amazon S3', 'Amazon EBS', 'Amazon RDS', 'Amazon Aurora',
        'Amazon DynamoDB', 'Amazon VPC', 'AWS KMS',
        'AWS Private Certificate Authority', 'Amazon Bedrock'
    }

# ESC services cache - will be populated when needed
ESC_SERVICES = None

# Default colors
colors = ["#834187", "#878541", "#458741", "#874145",
          "#c92d39", "#3ac92d", "#2d44c9", "#c9762d",
          "#ef8d22", "#2c22ef", "#ef22e5", "#e5ef22",
          "#fcc438", "#8d38fc", "#fc38a7", "#a7fc38",
          "#7ab648", "#b6487a", "#b66548", "#48adb6",
          "#3aa6dd", "#dd703a", "#ddc23a", "#a73add"]

# Parse prefix and name
def parse_name(name):
    search = re.search(r"(AWS|Amazon)*\s*(.*)", name)
    prefix = search.group(1) or 'AWS'
    name = search.group(2)
    name = name.split("(",2)[0].strip()
    return prefix, name

def strip_prefix(name):
    """Strip 'AWS ' or 'Amazon ' prefix for normalized ESC matching."""
    if not name:
        return name
    return re.sub(r'^\s*(AWS|Amazon)\s+', '', name).strip()


def check_esc_freshness(updated_str):
    """Return warning string if esc_services.json fallback is >30 days old, else None."""
    if not updated_str:
        return None
    try:
        from datetime import date
        updated_date = date.fromisoformat(updated_str)
        days_old = (date.today() - updated_date).days
        if days_old > 30:
            return (f"WARNING: esc_services.json fallback is {days_old} days old "
                    f"(updated: {updated_str}). Refresh the file.")
    except ValueError:
        pass
    return None


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
      cleaned = re.sub(r"[&,-/.]", '', name)
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

# Funktion zum Sammeln von Daten aus der Verzeichnis-API
def get_data_from_directory():
    periodic = {'categories': [], 'title': "Periodic Table of Amazon Web Services",
              'description': "AWS Services from Directory API"}
    
    # Symbols already used
    symbols = {}
    
    # Services already processed
    names = {}
    
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
            'full_name': name,  # Original full name for ESC filtering
            'desc': desc,
            'link': link or '',
            'prefix': prefix,
            'symbol': symbol,
            'category': cclass,
            'long': len(clean_name) > 11,
            'reallong': len(clean_name) > 20
        })

    # Append categories in insertion order
    for cat in categories_by_name.values():
        if cat['services']:
            periodic['categories'].append(cat)
            
    return periodic

# Funktion zum Sammeln von Daten durch Scraping
def get_data_from_scrape():
    periodic = {'categories': [], 'title': "Periodic Table of Amazon Web Services",
              'description': "AWS Services from Web Scraping"}
    
    # Symbols already used
    symbols = {}
    
    # Services already processed
    names = {}
    
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
        
        if not nav_data:
            print("Could not find product data in page")
            return periodic
        
        # Parse the navigation data
        ccount = 0
        products_menu = None
        for item in nav_data['items']:
            if item['name'] == 'Products':
                products_menu = item
                break
        
        if not products_menu or 'subNav' not in products_menu:
            print("Could not find Products menu")
            return periodic
        
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
                        "full_name": name,  # Original full name for ESC filtering
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
    
    except Exception as e:
        print(f"Error during scraping: {e}")
        
    return periodic

# Funktion zum Sammeln von ESC-Daten (filtert AWS Directory-Daten)
def get_data_from_esc():
    global ESC_SERVICES
    
    periodic = {'categories': [], 'title': "Periodic Table of AWS European Sovereign Cloud",
              'description': "AWS Services available in the European Sovereign Cloud"}
    
    # Hole zuerst alle AWS-Daten aus der Directory API
    aws_data = get_data_from_directory()
    
    # Lade ESC-Services dynamisch (nur einmal pro Lambda-Ausführung)
    if ESC_SERVICES is None:
        ESC_SERVICES = load_esc_services()
    
    esc_services = ESC_SERVICES
    
    if not esc_services:
        print("Warning: No ESC services loaded, returning empty periodic table")
        return periodic
    
    # Build normalized ESC set once for efficient matching
    normalized_esc = {strip_prefix(s) for s in esc_services}

    # Filtere die AWS-Daten basierend auf ESC-Verfügbarkeit
    for category in aws_data.get('categories', []):
        filtered_services = []

        for service in category.get('services', []):
            # Normalize both sides: strip AWS/Amazon prefix before comparing
            is_available = (
                strip_prefix(service.get('full_name', '')) in normalized_esc
                or strip_prefix(service['name']) in normalized_esc
            )
            
            if is_available:
                # Erstelle eine Kopie des Service-Objekts
                esc_service = service.copy()
                
                # Alle ESC-Links führen zur ESC-Hauptseite
                # ESC hat eine eigene Domain: https://www.aws.eu/
                esc_service['link'] = 'https://www.aws.eu/'
                
                filtered_services.append(esc_service)
        
        # Nur Kategorien mit Services hinzufügen
        if filtered_services:
            category['services'] = filtered_services
            periodic['categories'].append(category)
    
    # Füge ESC-spezifische Metadaten hinzu
    periodic['esc_region'] = 'eusc-de-east-1 (Brandenburg, Germany)'
    periodic['esc_note'] = 'European Sovereign Cloud - Operated exclusively by EU residents in the EU'
    
    # Lade Regionen-Informationen aus esc_services.json
    try:
        esc_json_path = os.path.join(os.path.dirname(__file__), 'esc_services.json')
        with open(esc_json_path, 'r', encoding='utf-8') as f:
            esc_data = json.load(f)
            regions_data = esc_data.get('regions', {})
            
            # Strukturiere die Regionen-Daten für das Template mit technischen Namen
            available_regions = []
            for region in regions_data.get('available', []):
                available_regions.append({
                    'name': 'Brandenburg, Germany',
                    'code': region
                })
            
            planned_regions = []
            planned_mapping = {
                'Belgium (Sovereign Local Zone)': 'eusc-be-*',
                'Netherlands (Sovereign Local Zone)': 'eusc-nl-*',
                'Portugal (Sovereign Local Zone)': 'eusc-pt-*'
            }
            for region in regions_data.get('planned', []):
                code = planned_mapping.get(region, 'TBD')
                planned_regions.append({
                    'name': region.replace(' (Sovereign Local Zone)', ''),
                    'code': code
                })
            
            periodic['esc_regions'] = {
                'available': {
                    'regions': available_regions
                },
                'planned': {
                    'regions': planned_regions
                }
            }
    except Exception as e:
        print(f"Failed to load regions from esc_services.json: {e}")
        # Fallback zu leeren Listen
        periodic['esc_regions'] = {
            'available': {'regions': []},
            'planned': {'regions': []}
        }
    
    return periodic

# Funktion zum Berechnen der Elementpositionen in der Tabelle
def compute_positions(periodic):
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
    vlayout = list(zip(*vlayout)) # transpose for easier handling
    
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
    
    # Compute required grid rows for template based on actual content
    periodic['grid_rows'] = max((pos[0] for pos in indices[:total_services]), default=10)
    
    return periodic

# Lambda-Handler-Funktion für multi_source_periodic.py
def lambda_handler(event, context):
    # Generiere die HTML für jede unterstützte Datenquelle
    html_files = {}
    
    # Generiere die Daten für alle Datenquellen
    data_by_source = {}
    
    # Daten aus Directory API (und Merged) holen
    dir_data = get_data_from_directory()
    data_by_source['directory'] = dir_data
    data_by_source['merged'] = dir_data  # Merged verwendet aktuell die Directory-Daten
    
    # Daten aus Web Scraping holen
    scrape_data = get_data_from_scrape()
    data_by_source['scrape'] = scrape_data
    
    # Daten aus ESC (filtert Directory-Daten)
    print("Generating ESC data...")
    esc_data = get_data_from_esc()
    data_by_source['esc'] = esc_data
    print(f"ESC data generated with {len(esc_data.get('categories', []))} categories")
    
    # Erstelle die Tab-Navigation für ALLE Quellen VOR der Schleife
    all_sources_meta = []
    for source in SUPPORTED_SOURCES:
        filename = f"{key_prefix}_{source}.html"
        base_filename = os.path.basename(filename)
        
        source_label = {
            'scrape': "AWS Global (Scraping)",
            'directory': "AWS Global (Directory)",
            'esc': "AWS European Sovereign Cloud"
        }.get(source, source.capitalize())
        
        all_sources_meta.append({
            'filename': base_filename, 
            'label': source_label,
            'source': source  # Merke die Quelle für die active-Prüfung
        })
    
    # Für jede Datenquelle eine HTML-Datei generieren
    for source in SUPPORTED_SOURCES:
        if source in data_by_source:
            # Berechne Positionen für die Elemente
            periodic_data = compute_positions(data_by_source[source])
            
            # Dateinamen für diese Quelle festlegen
            filename = f"{key_prefix}_{source}.html"
            
            # Erstelle eine Kopie der sources_meta mit korrektem active-Flag
            sources_meta = []
            for src_meta in all_sources_meta:
                sources_meta.append({
                    'filename': src_meta['filename'],
                    'label': src_meta['label'],
                    'active': src_meta['source'] == source  # Aktiv wenn es die aktuelle Quelle ist
                })
            
            # Erweiterung des Datenkontextes für Templating
            periodic_data['data_sources'] = sources_meta  # Tab-Informationen
            periodic_data['logo_data_uri'] = LOGO_DATA_URI  # Eingebettetes Logo
            periodic_data['favicon_data_uri'] = FAVICON_DATA_URI  # Eingebettetes Favicon
            periodic_data['last_update'] = datetime.now().strftime('%B %d, %Y')  # Aktuelles Datum
            
            # ESC Filter und Global Regions nur für Global-Tabs (scrape und directory)
            if source in ['scrape', 'directory']:
                periodic_data['show_esc_filter'] = True
                # ESC Services als JSON für JavaScript
                esc_services_list = list(load_esc_services())
                periodic_data['esc_services_json'] = json.dumps(esc_services_list)
                
                # Global Regions für Global-Tabs mit technischen Namen
                global_regions = [
                    {'name': 'US East (N. Virginia)', 'code': 'us-east-1'},
                    {'name': 'US East (Ohio)', 'code': 'us-east-2'},
                    {'name': 'US West (N. California)', 'code': 'us-west-1'},
                    {'name': 'US West (Oregon)', 'code': 'us-west-2'},
                    {'name': 'Africa (Cape Town)', 'code': 'af-south-1'},
                    {'name': 'Asia Pacific (Hong Kong)', 'code': 'ap-east-1'},
                    {'name': 'Asia Pacific (Hyderabad)', 'code': 'ap-south-2'},
                    {'name': 'Asia Pacific (Jakarta)', 'code': 'ap-southeast-3'},
                    {'name': 'Asia Pacific (Melbourne)', 'code': 'ap-southeast-4'},
                    {'name': 'Asia Pacific (Mumbai)', 'code': 'ap-south-1'},
                    {'name': 'Asia Pacific (Osaka)', 'code': 'ap-northeast-3'},
                    {'name': 'Asia Pacific (Seoul)', 'code': 'ap-northeast-2'},
                    {'name': 'Asia Pacific (Singapore)', 'code': 'ap-southeast-1'},
                    {'name': 'Asia Pacific (Sydney)', 'code': 'ap-southeast-2'},
                    {'name': 'Asia Pacific (Tokyo)', 'code': 'ap-northeast-1'},
                    {'name': 'Canada (Central)', 'code': 'ca-central-1'},
                    {'name': 'Canada West (Calgary)', 'code': 'ca-west-1'},
                    {'name': 'Europe (Frankfurt)', 'code': 'eu-central-1'},
                    {'name': 'Europe (Ireland)', 'code': 'eu-west-1'},
                    {'name': 'Europe (London)', 'code': 'eu-west-2'},
                    {'name': 'Europe (Milan)', 'code': 'eu-south-1'},
                    {'name': 'Europe (Paris)', 'code': 'eu-west-3'},
                    {'name': 'Europe (Spain)', 'code': 'eu-south-2'},
                    {'name': 'Europe (Stockholm)', 'code': 'eu-north-1'},
                    {'name': 'Europe (Zurich)', 'code': 'eu-central-2'},
                    {'name': 'Israel (Tel Aviv)', 'code': 'il-central-1'},
                    {'name': 'Middle East (Bahrain)', 'code': 'me-south-1'},
                    {'name': 'Middle East (UAE)', 'code': 'me-central-1'},
                    {'name': 'South America (São Paulo)', 'code': 'sa-east-1'},
                    {'name': 'AWS GovCloud (US-East)', 'code': 'us-gov-east-1'},
                    {'name': 'AWS GovCloud (US-West)', 'code': 'us-gov-west-1'}
                ]
                periodic_data['global_regions'] = {
                    'region_count': len(global_regions),
                    'regions': global_regions
                }
            else:
                periodic_data['show_esc_filter'] = False
                periodic_data['esc_services_json'] = '[]'
            
            # Debug: Print sources_meta für diese Datei
            print(f"Generiere {filename} mit {len(sources_meta)} Tabs:")
            for sm in sources_meta:
                print(f"  - {sm['label']} ({'aktiv' if sm.get('active') else 'inaktiv'})")
            
            # Template laden und HTML rendern
            template_path = os.path.join(os.path.dirname(__file__), 'base_template.mustache')
            with open(template_path, 'r') as f:  
                template = f.read()
                html = pystache.render(template, periodic_data)
                html_files[filename] = html
    
    # Speichern der generierten HTML-Dateien
    for filename, html_content in html_files.items():
        if bucket:  # Wenn S3-Bucket konfiguriert ist
            try:
                # Komprimiere HTML mit Gzip für schnellere Übertragung
                html_bytes = html_content.encode('utf-8')
                compressed_html = gzip.compress(html_bytes, compresslevel=9)
                
                s3.put_object(
                    ContentType='text/html',
                    ContentEncoding='gzip',
                    CacheControl='public, max-age=2592000',
                    Body=compressed_html,
                    Bucket=bucket,
                    Key=filename)
                
                # Berechne Komprimierungsrate
                compression_ratio = (1 - len(compressed_html) / len(html_bytes)) * 100
                print(f"Datei {filename} wurde in S3-Bucket {bucket} hochgeladen (komprimiert: {compression_ratio:.1f}% kleiner)")
            except Exception as e:
                print(f"Fehler beim Hochladen der Datei {filename} in S3: {e}")
        else:  # Lokale Speicherung, wenn kein Bucket konfiguriert ist
            try:
                # Stellen Sie sicher, dass das Zielverzeichnis existiert
                output_dir = os.path.dirname(filename)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"Datei {filename} wurde lokal gespeichert")
            except Exception as e:
                print(f"Fehler beim lokalen Speichern der Datei {filename}: {e}")
    
    # Zusätzlich eine index.html-Datei erstellen, die auf die Standardquelle verweist
    if DEFAULT_SOURCE in data_by_source:
        # Index ist identisch mit der HTML-Datei der Standardquelle, aber mit angepasstem Titel
        default_file = f"{key_prefix}_{DEFAULT_SOURCE}.html"
        if default_file in html_files:
            if bucket:
                # Komprimiere auch index.html mit Gzip
                html_bytes = html_files[default_file].encode('utf-8')
                compressed_html = gzip.compress(html_bytes, compresslevel=9)
                
                s3.put_object(
                    ContentType='text/html',
                    ContentEncoding='gzip',
                    CacheControl='public, max-age=2592000',
                    Body=compressed_html,
                    Bucket=bucket,
                    Key=key)  # Standarddateiname (meistens index.html)
                
                compression_ratio = (1 - len(compressed_html) / len(html_bytes)) * 100
                print(f"Standarddatei {key} wurde in S3-Bucket {bucket} hochgeladen (komprimiert: {compression_ratio:.1f}% kleiner)")
            else:
                try:
                    with open(key, 'w', encoding='utf-8') as f:
                        f.write(html_files[default_file])
                    print(f"Standarddatei {key} wurde lokal gespeichert")
                except Exception as e:
                    print(f"Fehler beim lokalen Speichern der Standarddatei {key}: {e}")

# Wenn das Skript direkt ausgeführt wird (nicht als Lambda)
if __name__ == "__main__":
    lambda_handler(None, None)
