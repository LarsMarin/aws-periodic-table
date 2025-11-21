#!/usr/bin/env python3
"""
Skript zur Erstellung mehrerer Versionen der Periodentabelle mit Tabs
"""
import os
import shutil
from bs4 import BeautifulSoup

# Eingabe- und Ausgabedateien
INPUT_HTML = "../output.html"
OUTPUT_DIR = "../output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Unterstützte Datenquellen und ihre Labels
SOURCES = {
    'scrape': 'Web Scraping',
    'directory': 'Directory API'
}

DEFAULT_SOURCE = 'scrape'

# CSS für Tab-Navigation
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

.source-info {
  text-align: center;
  margin-bottom: 20px;
  font-size: 1.2vw;
}
"""

# Lese die Original-HTML-Datei ein
if not os.path.exists(INPUT_HTML):
    print(f"Fehler: Eingabedatei {INPUT_HTML} nicht gefunden!")
    exit(1)

with open(INPUT_HTML, 'r', encoding='utf-8') as f:
    original_html = f.read()

# Für jede Datenquelle eine modifizierte Version erstellen
for source_id, source_label in SOURCES.items():
    # Parse HTML mit BeautifulSoup
    soup = BeautifulSoup(original_html, 'html.parser')
    
    # CSS für Tab-Navigation hinzufügen
    css_style = soup.find('style')
    if css_style:
        css_style.string = css_style.string + TABS_CSS
    
    # Finde den Wrapper für die Tabelle
    wrapper = soup.find('div', class_='Wrapper')
    if not wrapper:
        print(f"Warnung: Wrapper div nicht gefunden in {source_id}")
        continue
    
    # Erstelle Tab-Navigation HTML
    tabs_html = '<div class="tabs">'
    for tab_id, tab_label in SOURCES.items():
        active = "active" if tab_id == source_id else ""
        tabs_html += f'<a href="index_{tab_id}.html" class="tab {active}">{tab_label}</a>'
    tabs_html += '</div>'
    
    # Füge Tab-Navigation am Anfang des Wrappers ein
    wrapper.insert(0, BeautifulSoup(tabs_html, 'html.parser'))
    
    # Speichere die modifizierte HTML-Datei
    output_filepath = os.path.join(OUTPUT_DIR, f"index_{source_id}.html")
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f"Datei erstellt: {output_filepath}")

# Erstelle die Hauptindex-Datei (Kopie der Standarddatenquelle)
default_file = os.path.join(OUTPUT_DIR, f"index_{DEFAULT_SOURCE}.html")
index_file = os.path.join(OUTPUT_DIR, "index.html")

if os.path.exists(default_file):
    shutil.copy2(default_file, index_file)
    print(f"Hauptindex erstellt: {index_file}")
else:
    print(f"Fehler: Datei {default_file} nicht gefunden, kann index.html nicht erstellen.")

print("\nHinweis: Da wir keine verschiedenen Datenquellen verwenden konnten,")
print("enthalten alle Dateien die gleichen Daten, aber mit unterschiedlichen Tabs.")
print("Um tatsächlich verschiedene Daten anzuzeigen, müsste das periodic.py-Skript für")
print("jede Datenquelle separat ausgeführt werden.")