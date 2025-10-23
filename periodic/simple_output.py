#!/usr/bin/env python3
"""
Einfaches Test-Skript zum Generieren von HTML-Dateien für verschiedene Datenquellen
"""
import os

# Verzeichnis für Ausgabedateien
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Ausgabeverzeichnis: {OUTPUT_DIR}")

# Liste der Datenquellen
SOURCES = ['scrape', 'directory', 'merged']
DEFAULT_SOURCE = 'scrape'

# Einfaches HTML-Template mit Tabs
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>Periodische Tabelle der AWS-Dienste ({source})</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .tabs { display: flex; margin-bottom: 20px; }
        .tab { padding: 10px 20px; margin-right: 5px; background: #f0f0f0; cursor: pointer; }
        .tab.active { background: #007bff; color: white; }
        .content { padding: 20px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <h1>Periodische Tabelle der AWS-Dienste</h1>
    <p>Datenquelle: <strong>{source}</strong></p>
    
    <div class="tabs">
        {tabs}
    </div>
    
    <div class="content">
        <p>Dies ist eine Beispielseite für die Datenquelle <strong>{source}</strong>.</p>
        <p>In einer echten Implementierung würde hier die periodische Tabelle angezeigt.</p>
    </div>
</body>
</html>
"""

# Generieren der HTML-Dateien
for source in SOURCES:
    # Generieren der Tabs
    tabs_html = ""
    for tab_source in SOURCES:
        active = "active" if tab_source == source else ""
        tabs_html += f'<a href="index_{tab_source}.html" class="tab {active}">{tab_source.capitalize()}</a>\n'
    
    # Füllen des Templates
    html_content = HTML_TEMPLATE.format(source=source, tabs=tabs_html)
    
    # Speichern der HTML-Datei
    filename = f"index_{source}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Datei erstellt: {filepath}")

# Erstellen der Hauptindex-Datei (Kopie der Standarddatenquelle)
default_file = f"index_{DEFAULT_SOURCE}.html"
default_filepath = os.path.join(OUTPUT_DIR, default_file)
index_filepath = os.path.join(OUTPUT_DIR, "index.html")

with open(default_filepath, 'r', encoding='utf-8') as src:
    with open(index_filepath, 'w', encoding='utf-8') as dest:
        dest.write(src.read())
print(f"Hauptindex erstellt: {index_filepath}")