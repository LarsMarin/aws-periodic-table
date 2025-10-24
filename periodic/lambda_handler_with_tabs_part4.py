# Funktion zum Sammeln von Daten durch Scraping
def get_data_from_scrape():
    periodic = {'categories': [], 'title': "Periodic Table of Amazon Web Services (Scrape)",
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