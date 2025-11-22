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
cp lambda_handler.py "$TMP_DIR/periodic.py"
cp base64_images.py "$TMP_DIR/base64_images.py"
# Verwende die aktualisierte Basisvorlage (inkl. Favicon und Tabs) als Template für den Handler
cp base_template.mustache "$TMP_DIR/base_template.mustache"
# Kopiere das img-Verzeichnis mit Logo
cp -r img "$TMP_DIR/"

# Wechsle ins temporäre Verzeichnis
cd "$TMP_DIR"

# Installiere Abhängigkeiten
echo "Installiere Abhängigkeiten..."
mkdir -p lib
pip install -t lib pystache beautifulsoup4 requests

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

# Lambda-Funktion aufrufen, um HTML-Dateien zu generieren
echo ""
echo "Rufe Lambda-Funktion auf, um HTML-Dateien zu generieren..."
aws lambda invoke \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --region "$REGION" \
    --log-type Tail \
    --query 'LogResult' \
    --output text response.json | base64 --decode

echo ""
echo "Lambda-Funktion erfolgreich ausgeführt!"
echo "Die folgenden Dateien wurden in S3 erstellt:"
echo "  - index.html (Hauptdatei, verweist auf die Standard-Datenquelle)"
echo "  - index_scrape.html (Web Scraping-Version)"
echo "  - index_directory.html (Directory API-Version)"

# Aufräumen der Response-Datei
rm -f response.json

# CloudFront Cache invalidieren
echo ""
echo "Invalidiere CloudFront Cache..."
CLOUDFRONT_DISTRIBUTION_ID="ENS7ISNEWF40O"
aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
    --paths "/index.html" "/index_scrape.html" "/index_directory.html" \
    --query 'Invalidation.{Id:Id,Status:Status,CreateTime:CreateTime}' \
    --output table

echo "CloudFront Cache-Invalidierung gestartet!"
