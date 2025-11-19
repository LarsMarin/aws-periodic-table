#!/bin/bash

# Skript zum Generieren von HTML-Dateien für verschiedene Datenquellen

# Verzeichnis für Ausgabedateien
OUTPUT_DIR="../output"
mkdir -p "$OUTPUT_DIR"

# Aufruf des Python-Skripts für verschiedene Datenquellen
echo "Generiere Tabelle für Web Scraping (ca. 100 Services)..."
PERIODIC_DATA_SOURCE=scrape PERIODIC_PRODUCTS_SIZE=300 OUTPUT_PATH="$OUTPUT_DIR/raw_scrape.html" python3 local_periodic.py

echo "Generiere Tabelle für Directory API (ca. 300 Services)..."
PERIODIC_DATA_SOURCE=directory PERIODIC_PRODUCTS_SIZE=300 OUTPUT_PATH="$OUTPUT_DIR/raw_directory.html" python3 local_periodic.py



echo "Füge Tab-Navigation zu den Tabellen hinzu..."

# Python-Skript zum Hinzufügen der Tab-Navigation
cat > "$OUTPUT_DIR/add_tabs.py" << 'EOL'
#!/usr/bin/env python3
import os
import sys
from bs4 import BeautifulSoup

# Verzeichnis für Ausgabedateien
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Unterstützte Datenquellen und ihre Labels
SOURCES = {
    'scrape': 'Web Scraping', 
    'directory': 'Directory API'
}

DEFAULT_SOURCE = 'scrape'

# CSS für die Tab-Navigation
TABS_CSS = """
/* Tab Navigation Styles */
.tabs {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 5px;
}

.tab {
  padding: 10px 20px;
  margin: 0 5px;
  background-color: #333;
  color: white;
  border-radius: 5px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s;
}

.tab:hover {
  background-color: #555;
}

.tab.active {
  background-color: #c92d39;
}
"""

def add_tabs_to_html(source_id):
    source_label = SOURCES.get(source_id, source_id.capitalize())
    input_file = os.path.join(OUTPUT_DIR, f"raw_{source_id}.html")
    output_file = os.path.join(OUTPUT_DIR, f"index_{source_id}.html")
    
    if not os.path.exists(input_file):
        print(f"Warnung: Datei {input_file} nicht gefunden")
        return False
    
    # Lese die HTML-Datei
    with open(input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse HTML mit BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # CSS für Tab-Navigation hinzufügen
    style_tag = soup.find('style')
    if style_tag:
        style_tag.string = style_tag.string + TABS_CSS
    
    # Tab-Navigation HTML erstellen
    tabs_html = '<div class="tabs">'
    for tab_id, tab_label in SOURCES.items():
        active = "active" if tab_id == source_id else ""
        tabs_html += f'<a href="index_{tab_id}.html" class="tab {active}">{tab_label}</a>'
    tabs_html += '</div>'
    
    # Wrapper finden und Tabs hinzufügen
    wrapper = soup.find('div', class_='Wrapper')
    if wrapper:
        wrapper.insert(0, BeautifulSoup(tabs_html, 'html.parser'))
    
    # Speichern der modifizierten HTML-Datei
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"Tab-Navigation zu {source_id} hinzugefügt: {output_file}")
    return True

# Tabs zu jeder Datenquelle hinzufügen
for source in SOURCES.keys():
    add_tabs_to_html(source)

# Erstellen der index.html (Kopie der Standardquelle)
default_file = os.path.join(OUTPUT_DIR, f"index_{DEFAULT_SOURCE}.html")
index_file = os.path.join(OUTPUT_DIR, "index.html")

if os.path.exists(default_file):
    with open(default_file, 'r', encoding='utf-8') as src:
        content = src.read()
        with open(index_file, 'w', encoding='utf-8') as dest:
            dest.write(content)
    print(f"Hauptindex erstellt: {index_file}")
else:
    print(f"Fehler: Standarddatei {default_file} nicht gefunden")

print("\nVerarbeitung abgeschlossen!")
EOL

# Führe das Python-Skript zur Tab-Integration aus
cd "$OUTPUT_DIR" && python3 add_tabs.py

echo "\nDie HTML-Dateien wurden im Verzeichnis $OUTPUT_DIR erstellt:"
ls -la "$OUTPUT_DIR"/*.html