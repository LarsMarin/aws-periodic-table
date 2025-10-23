#!/usr/bin/env python3
"""
Skript zur Integration der Tab-Navigation in die existierende Periodentabelle
"""
import os
import re
from bs4 import BeautifulSoup

# Eingabe- und Ausgabedateien
INPUT_HTML = "../output.html"
OUTPUT_DIR = "../output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Unterstützte Datenquellen
SOURCES = ['scrape', 'directory', 'merged']
SOURCE_LABELS = {
    'scrape': "Web Scraping", 
    'directory': "Directory API",
    'merged': "Combined Sources"
}
DEFAULT_SOURCE = 'scrape'

# Lese die Original-HTML-Datei ein
with open(INPUT_HTML, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# CSS für Tab-Navigation hinzufügen
css_style = soup.find('style')
if css_style:
    tabs_css = """
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
    css_style.string = css_style.string + tabs_css

# Für jede Datenquelle eine Kopie mit Tab-Navigation erstellen
for source in SOURCES:
    # Soup-Kopie für diese Quelle erstellen
    source_soup = BeautifulSoup(str(soup), 'html.parser')
    
    # Titel aktualisieren für die spezifische Quelle
    title_tag = source_soup.find('title')
    if title_tag:
        title_tag.string = f"Periodic Table of Amazon Web Services ({source})"
    
    # Finde den Container für die Wrapper-Klasse
    wrapper = source_soup.find('div', class_='Wrapper')
    if not wrapper:
        print("Wrapper div nicht gefunden, überspringe...") 
        continue
    
    # Erstelle Tab-Navigation HTML
    tabs_html = '<div class="tabs">'
    for tab_source in SOURCES:
        active = "active" if tab_source == source else ""
        tab_label = SOURCE_LABELS.get(tab_source, tab_source.capitalize())
        tabs_html += f'<a href="index_{tab_source}.html" class="tab {active}">{tab_label}</a>'
    tabs_html += '</div>'
    
    # Erstelle Source-Info HTML
    source_label = SOURCE_LABELS.get(source, source.capitalize())
    source_info_html = f'<div class="source-info">Datenquelle: <strong>{source_label}</strong></div>'
    
    # Füge Tab-Navigation und Source-Info am Anfang des Wrappers ein
    wrapper.insert(0, BeautifulSoup(source_info_html, 'html.parser'))
    wrapper.insert(0, BeautifulSoup(tabs_html, 'html.parser'))
    
    # Speichere die modifizierte HTML-Datei
    filename = f"index_{source}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(source_soup))
    print(f"Datei erstellt: {filepath}")

# Erstelle die Hauptindex-Datei (Kopie der Standarddatenquelle)
default_file = f"index_{DEFAULT_SOURCE}.html"
default_filepath = os.path.join(OUTPUT_DIR, default_file)
index_filepath = os.path.join(OUTPUT_DIR, "index.html")

with open(default_filepath, 'r', encoding='utf-8') as src:
    with open(index_filepath, 'w', encoding='utf-8') as dest:
        dest.write(src.read())
print(f"Hauptindex erstellt: {index_filepath}")
