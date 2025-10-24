#!/bin/bash

# Konfigurationswerte
LAMBDA_FUNCTION_NAME="awsperiodictable-ProductScraper-OX9mIcqbc1I3"
REGION="eu-central-1" # Region anpassen
BUCKET_NAME="awsperiodictable.com" # S3-Bucket anpassen

# Verzeichnis für temporäre Dateien
TMP_DIR="./lambda_build"
mkdir -p "$TMP_DIR"

echo "Erstelle Lambda-Deployment-Paket..."

# Kopiere die notwendigen Dateien
cp complete_lambda_handler.py "$TMP_DIR/periodic.py"
cp template.mustache "$TMP_DIR/"

# Wechsle ins temporäre Verzeichnis
cd "$TMP_DIR"

# Installiere Abhängigkeiten
echo "Installiere Abhängigkeiten..."
pip install -t . pystache beautifulsoup4 requests

# Erstelle ZIP-Archiv
echo "Erstelle ZIP-Archiv..."
zip -r ../lambda_deployment.zip . > /dev/null

# Zurück zum Hauptverzeichnis
cd ..

# Aktualisiere die Lambda-Funktion
echo "Aktualisiere Lambda-Funktion $LAMBDA_FUNCTION_NAME..."
aws lambda update-function-code \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --zip-file fileb://lambda_deployment.zip \
    --region "$REGION"

# Konfiguriere Umgebungsvariablen
echo "Konfiguriere Umgebungsvariablen..."
aws lambda update-function-configuration \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --environment "Variables={bucket=$BUCKET_NAME,key=index.html,PERIODIC_DATA_SOURCE=scrape,PERIODIC_PRODUCTS_SIZE=300}" \
    --region "$REGION"

# Aufräumen
echo "Räume temporäre Dateien auf..."
rm -rf "$TMP_DIR"

echo "Lambda-Funktion erfolgreich aktualisiert!"
echo "Die folgenden Dateien werden nach dem nächsten Aufruf in S3 erstellt:"
echo "  - index.html (Hauptdatei, verweist auf die Standard-Datenquelle)"
echo "  - index_scrape.html (Web Scraping-Version)"
echo "  - index_directory.html (Directory API-Version)"
