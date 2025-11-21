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