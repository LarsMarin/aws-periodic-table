# Lambda-Handler-Funktion für multi_source_periodic.py
def lambda_handler(event, context):
    # Generiere die HTML für jede unterstützte Datenquelle
    html_files = {}
    sources_meta = []
    
    # Generiere die Daten für alle Datenquellen
    data_by_source = {}
    
    # Daten aus Directory API (und Merged) holen
    dir_data = get_data_from_directory()
    data_by_source['directory'] = dir_data
    data_by_source['merged'] = dir_data  # Merged verwendet aktuell die Directory-Daten
    
    # Daten aus Web Scraping holen
    scrape_data = get_data_from_scrape()
    data_by_source['scrape'] = scrape_data
    
    # Für jede Datenquelle eine HTML-Datei generieren
    for source in SUPPORTED_SOURCES:
        if source in data_by_source:
            # Berechne Positionen für die Elemente
            periodic_data = compute_positions(data_by_source[source])
            
            # Dateinamen für diese Quelle festlegen
            filename = f"{key_prefix}_{source}.html"
            base_filename = os.path.basename(filename)
            
            # Metadaten für Tab-Navigation aufbauen
            source_label = {
                'scrape': "Web Scraping",
                'directory': "Directory API",
                'merged': "Combined Sources"
            }.get(source, source.capitalize())
            
            sources_meta.append({
                'filename': base_filename, 
                'label': source_label,
                'active': source == DEFAULT_SOURCE  # Standardquelle ist aktiv
            })
            
            # Erweiterung des Datenkontextes für Templating
            periodic_data['data_sources'] = sources_meta  # Tab-Informationen
            periodic_data['current_source'] = source_label  # Aktuelle Quelle
            
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
                s3.put_object(
                    ContentType='text/html',
                    Body=html_content,
                    Bucket=bucket,
                    Key=filename)
                print(f"Datei {filename} wurde in S3-Bucket {bucket} hochgeladen")
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
                s3.put_object(
                    ContentType='text/html',
                    Body=html_files[default_file],
                    Bucket=bucket,
                    Key=key)  # Standarddateiname (meistens index.html)
                print(f"Standarddatei {key} wurde in S3-Bucket {bucket} hochgeladen")
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