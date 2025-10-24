# Lambda-Deployment-Anweisungen

## Zusammenführen der Lambda-Handler-Dateien

Öffnen Sie ein Terminal und führen Sie den folgenden Befehl aus, um alle erstellten Teile zu einem vollständigen Lambda-Handler zusammenzuführen:

```bash
cd periodic
cat lambda_handler_with_tabs.py lambda_handler_with_tabs_part2.py lambda_handler_with_tabs_part3.py lambda_handler_with_tabs_part4.py lambda_handler_with_tabs_part5.py lambda_handler_with_tabs_part6.py > complete_lambda_handler.py
```

## Vorbereiten des Lambda-Deployment-Pakets

1. Stellen Sie sicher, dass die `template.mustache`-Datei im selben Verzeichnis wie der Lambda-Handler liegt:

```bash
cp template.mustache /path/to/lambda/deployment/
```

2. Erstellen Sie ein ZIP-Archiv mit dem Lambda-Handler und allen Abhängigkeiten:

```bash
cd /path/to/lambda/deployment/
pip install -t . pystache beautifulsoup4 requests boto3
zip -r lambda_deployment.zip complete_lambda_handler.py template.mustache boto3/ pystache/ requests/ bs4/ urllib3/ soupsieve/ certifi/ charset_normalizer/ idna/
```

## Aktualisieren der Lambda-Funktion

1. **Über die AWS Console:**
   - Navigieren Sie zur Lambda-Funktionsseite
   - Wählen Sie "Hochladen von" > ".zip-Datei"
   - Laden Sie die erstellte ZIP-Datei hoch
   - Setzen Sie den Handler auf `complete_lambda_handler.lambda_handler`

2. **Über die AWS CLI:**

```bash
aws lambda update-function-code --function-name IhreFunktionsName --zip-file fileb://lambda_deployment.zip
```

## Umgebungsvariablen konfigurieren

Stellen Sie sicher, dass die folgenden Umgebungsvariablen in Ihrer Lambda-Funktion konfiguriert sind:

- `bucket`: Name des S3-Buckets für den Upload
- `key`: Standardname für die Hauptausgabedatei (default: 'index.html')
- `PERIODIC_DATA_SOURCE`: Standardquelle für die Hauptdatei (default: 'scrape')
- `PERIODIC_PRODUCTS_SIZE`: Maximale Anzahl von API-Produkten (default: '300')

## Testen der Lambda-Funktion

Invoke die Lambda-Funktion manuell, um zu überprüfen, ob alles korrekt funktioniert:

```bash
aws lambda invoke --function-name IhreFunktionsName --payload '{}' output.txt
```

Überprüfen Sie die S3-Ausgabedateien:
- `index.html` (Hauptdatei, entspricht der Standard-Datenquelle)
- `index_scrape.html` (Web Scraping-Version)
- `index_directory.html` (Directory API-Version)
