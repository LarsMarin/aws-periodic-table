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
