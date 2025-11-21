"""
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
"""
