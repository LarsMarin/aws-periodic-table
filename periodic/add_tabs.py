#!/usr/bin/env python3
"""
Skript zum Hinzufügen der Tab-Navigation zu den generierten HTML-Dateien
"""
import os
import sys
from bs4 import BeautifulSoup

# Verzeichnis für Ausgabedateien
OUTPUT_DIR = "../output"

# Unterstützte Datenquellen und ihre Labels
SOURCES = {
    'scrape': 'Web Scraping', 
    'directory': 'Directory API'
}

DEFAULT_SOURCE = 'scrape'

# CSS für die Tab-Navigation - verbesserte Lesbarkeit
TABS_CSS = """
/* Tab Navigation Styles */
.tabs {
  display: flex;
  justify-content: center;
  margin-bottom: 25px;
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 8px;
}

.tab {
  padding: 15px 30px;
  margin: 0 10px;
  background-color: #333;
  color: white;
  border-radius: 8px;
  font-weight: bold;
  font-size: 18px;
  font-family: 'Yanone Kaffeesatz', Arial, sans-serif;
  cursor: pointer;
  transition: all 0.3s;
  text-decoration: none;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.tab:hover {
  background-color: #555;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

.tab.active {
  background-color: #c92d39;
  transform: translateY(0);
  box-shadow: 0 3px 6px rgba(201,45,57,0.4);
}

.source-info {
  text-align: center;
  margin-bottom: 20px;
  font-size: 20px;
  font-weight: bold;
  color: #333;
}
"""

# CSS für optimierte Legende mit mehr Platz
LEGEND_CSS = """
/* Legende mit mehr Platz für alle Einträge */
.Legend {
  grid-column-start: 4 !important;
  grid-column-end: span 9 !important;
  grid-row-start: 3 !important;
  grid-row-end: span 3 !important; /* Eine Zeile mehr */
  transform: none !important;
  margin-top: 0 !important;
  margin-bottom: 10px !important;
}

ul.LegendLabels {
  margin: 0 !important;
  padding: 0 !important;
  float: left !important;
  font-size: 0.76vw !important;
  font-weight: bold !important;
  list-style: none !important;
  /* 4 Spalten ohne Höhenbegrenzung */
  column-count: 4 !important;
  column-gap: 8px !important;
  columns: 4 !important;
  -moz-column-count: 4 !important;
  -moz-columns: 4 !important;
  -webkit-column-count: 4 !important;
  -webkit-columns: 4 !important;
  width: 100% !important;
  height: auto !important; /* Automatische Höhe */
  max-height: none !important; /* Keine Begrenzung */
  overflow: visible !important; /* Überlauf erlauben */
}
ul.LegendLabels li {
  line-height: 1.3 !important; /* Etwas kompakterer Zeilenabstand */
  margin-bottom: 3px !important; /* Etwas geringerer Abstand */
  white-space: nowrap !important;
  overflow: visible !important;
  display: block !important;
  break-inside: avoid !important; /* Verhindert Trennung von Elementen */
}
ul.LegendLabels li span {
  display: inline-block !important;
  height: 0.8vw !important;
  width: 0.8vw !important;
  margin-right: 0.4vw !important;
  margin-left: 0 !important;
  vertical-align: middle !important;
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