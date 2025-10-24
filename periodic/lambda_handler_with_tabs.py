# coding=utf-8
import os, re, json, boto3, pystache
from bs4 import BeautifulSoup
from requests import get

# Unterstützte Datenquellen und ihre Labels
SOURCES = {
    'scrape': 'Web Scraping', 
    'directory': 'Directory API'
}

DEFAULT_SOURCE = os.environ.get('PERIODIC_DATA_SOURCE', 'scrape')  # Default-Quelle festlegen
PRODUCTS_SIZE = int(os.environ.get('PERIODIC_PRODUCTS_SIZE', '300'))

# AWS Products Directory endpoint template
AWS_PRODUCTS_API = (
    "https://aws.amazon.com/api/dirs/items/search?"
    "item.directoryId=products-cards-interactive-aws-products-ams"
    "&item.locale=en_US"
    "&tags.id=GLOBAL%23local-tags-aws-products-type%23service%7CGLOBAL%23local-tags-aws-products-type%23feature"
    "&sort_by=item.dateCreated&sort_order=asc"
    f"&size={PRODUCTS_SIZE}"
)

# Common HTTP headers to mimic a browser (helps aws.com endpoints return full data)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://aws.amazon.com/products/',
}

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