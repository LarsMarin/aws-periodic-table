# Funktion zum Hinzufügen von Tabs zu HTML
def add_tabs_to_html(html_content, source_id):
    source_label = SOURCES.get(source_id, source_id.capitalize())
    
    # Parse HTML mit BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Titel aktualisieren
    title_tag = soup.find('title')
    if title_tag:
        title_tag.string = f"Periodic Table of Amazon Web Services ({source_label})"
    
    # CSS für Tab-Navigation und verbesserte Legende hinzufügen
    style_tag = soup.find('style')
    if style_tag:
        style_tag.string = style_tag.string + TABS_CSS + LEGEND_CSS
    
    # Tab-Navigation HTML erstellen
    tabs_html = '<div class="tabs">'
    for tab_id, tab_label in SOURCES.items():
        active = "active" if tab_id == source_id else ""
        tabs_html += f'<a href="index_{tab_id}.html" class="tab {active}">{tab_label}</a>'
    tabs_html += '</div>'
    
    # Source-Info HTML erstellen
    source_info_html = f'<div class="source-info">Datenquelle: <strong>{source_label}</strong></div>'
    
    # Wrapper finden und Tabs hinzufügen
    wrapper = soup.find('div', class_='Wrapper')
    if wrapper:
        wrapper.insert(0, BeautifulSoup(source_info_html, 'html.parser'))
        wrapper.insert(0, BeautifulSoup(tabs_html, 'html.parser'))
    
    return str(soup)

# Lambda-Handler-Funktion
def lambda_handler(event, context):
    bucket = os.environ.get('bucket', '')
    key_prefix = os.environ.get('key', 'index').rsplit('.', 1)[0]
    
    if not bucket:
        print("Bucket name not provided in environment variables")
        return {'statusCode': 400, 'body': 'Bucket name is required'}
    
    s3 = boto3.client('s3')
    
    try:
        # Daten für alle Quellen generieren
        data_sources = {}
        data_sources['scrape'] = get_data_from_scrape()
        data_sources['directory'] = get_data_from_directory()
        
        # Template laden
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template.mustache')
        with open(template_path, 'r') as f:  
            template = f.read()
        
        # HTML für jede Quelle generieren und mit Tabs versehen
        for source_id, periodic_data in data_sources.items():
            # Positionen berechnen
            periodic_data = compute_positions(periodic_data)
            
            # HTML rendern
            html = pystache.render(template, periodic_data)
            
            # Tabs hinzufügen
            html_with_tabs = add_tabs_to_html(html, source_id)
            
            # HTML für diese Quelle zu S3 hochladen
            filename = f"index_{source_id}.html"
            s3.put_object(
                ContentType='text/html',
                Body=html_with_tabs,
                Bucket=bucket,
                Key=filename
            )
            print(f"HTML für {source_id} hochgeladen: {filename}")
        
        # Die Hauptindex-Datei (standardmäßig die Scraping-Version)
        default_source = DEFAULT_SOURCE
        default_file = f"index_{default_source}.html"
        
        # Kopiere den Inhalt der Default-Quelle als Hauptindex
        s3_response = s3.get_object(Bucket=bucket, Key=default_file)
        default_html = s3_response['Body'].read().decode('utf-8')
        
        # Hauptindex hochladen
        main_index_key = key_prefix + ".html"
        s3.put_object(
            ContentType='text/html',
            Body=default_html,
            Bucket=bucket,
            Key=main_index_key
        )
        print(f"Hauptindex hochgeladen: {main_index_key}")
        
        return {
            'statusCode': 200,
            'body': f"Erfolgreich: Periodentabellen mit Tabs wurden nach S3 hochgeladen"
        }
        
    except Exception as e:
        print(f"Fehler: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Fehler: {str(e)}"
        }

# Für lokale Tests
if __name__ == "__main__":
    print(lambda_handler(None, None))