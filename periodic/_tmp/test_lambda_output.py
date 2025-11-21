#!/usr/bin/env python3
"""
Test-Skript für die Lambda-Funktion
Generiert die HTML-Dateien lokal im output/ Verzeichnis
"""
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

import re, json, pystache
from bs4 import BeautifulSoup
from requests import get

# Importiere alle Funktionen aus complete_lambda_handler
from complete_lambda_handler import (
    get_data_from_scrape, 
    get_data_from_directory,
    compute_positions,
    add_tabs_to_html,
    SOURCES,
    DEFAULT_SOURCE
)

def test_local_generation():
    """
    Generiert die HTML-Dateien lokal im output/ Verzeichnis
    """
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 80)
    print("STARTE LOKALE GENERIERUNG DER PERIODIC TABLE")
    print("=" * 80)
    print()
    
    try:
        # Template laden
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template.mustache')
        print(f"📄 Lade Template von: {template_path}")
        with open(template_path, 'r') as f:  
            template = f.read()
        print("✅ Template erfolgreich geladen")
        print()
        
        # Daten für alle Quellen generieren
        data_sources = {}
        
        print("🌐 Sammle Daten aus Web Scraping...")
        data_sources['scrape'] = get_data_from_scrape()
        scrape_services = sum(len(cat.get("services", [])) for cat in data_sources['scrape']['categories'])
        print(f"✅ Web Scraping: {len(data_sources['scrape']['categories'])} Kategorien, {scrape_services} Services")
        print()
        
        print("📁 Sammle Daten aus Directory API...")
        data_sources['directory'] = get_data_from_directory()
        dir_services = sum(len(cat.get("services", [])) for cat in data_sources['directory']['categories'])
        print(f"✅ Directory API: {len(data_sources['directory']['categories'])} Kategorien, {dir_services} Services")
        print()
        
        # HTML für jede Quelle generieren
        print("=" * 80)
        print("GENERIERE HTML-DATEIEN")
        print("=" * 80)
        print()
        
        for source_id, periodic_data in data_sources.items():
            source_label = SOURCES.get(source_id, source_id.capitalize())
            print(f"🔨 Generiere HTML für: {source_label}")
            
            # Positionen berechnen
            periodic_data = compute_positions(periodic_data)
            print(f"   ➜ Grid Rows: {periodic_data['grid_rows']}")
            
            # HTML rendern
            html = pystache.render(template, periodic_data)
            print(f"   ➜ HTML gerendert: {len(html)} Zeichen")
            
            # Tabs hinzufügen
            html_with_tabs = add_tabs_to_html(html, source_id)
            print(f"   ➜ Tabs hinzugefügt: {len(html_with_tabs)} Zeichen")
            
            # HTML für diese Quelle lokal speichern
            filename = f"index_{source_id}.html"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_with_tabs)
            
            print(f"   ✅ Gespeichert: {filepath}")
            print()
        
        # Hauptindex-Datei erstellen (standardmäßig die Default-Quelle)
        print("=" * 80)
        print(f"ERSTELLE HAUPTINDEX (Quelle: {DEFAULT_SOURCE})")
        print("=" * 80)
        print()
        
        default_file = f"index_{DEFAULT_SOURCE}.html"
        default_filepath = os.path.join(output_dir, default_file)
        
        with open(default_filepath, 'r', encoding='utf-8') as f:
            default_html = f.read()
        
        main_index_path = os.path.join(output_dir, 'index.html')
        with open(main_index_path, 'w', encoding='utf-8') as f:
            f.write(default_html)
        
        print(f"✅ Hauptindex erstellt: {main_index_path}")
        print()
        
        # Zusammenfassung
        print("=" * 80)
        print("✨ GENERIERUNG ERFOLGREICH ABGESCHLOSSEN")
        print("=" * 80)
        print()
        print("Erstellte Dateien:")
        print(f"  • {os.path.join(output_dir, 'index.html')} (Hauptindex)")
        print(f"  • {os.path.join(output_dir, 'index_scrape.html')} ({scrape_services} Services)")
        print(f"  • {os.path.join(output_dir, 'index_directory.html')} ({dir_services} Services)")
        print()
        print("🌐 Zum Anzeigen im Browser:")
        print(f"   open {main_index_path}")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ FEHLER BEI DER GENERIERUNG")
        print("=" * 80)
        print()
        print(f"Fehlertyp: {type(e).__name__}")
        print(f"Fehlermeldung: {str(e)}")
        print()
        import traceback
        print("Traceback:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_local_generation()
    sys.exit(0 if success else 1)
