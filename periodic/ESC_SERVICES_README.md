# AWS European Sovereign Cloud (ESC) Services

Diese Datei dokumentiert die Verwaltung der ESC-Service-Liste für das AWS Periodensystem.

## Übersicht

Das System lädt **automatisch** die aktuellen ESC Services von docs.aws.eu. Die Datei `esc_services.json` dient als Fallback, falls die dynamische Abfrage fehlschlägt.

### Automatisches Update-System

1. **Primär:** Lambda-Funktion holt monatlich Services von docs.aws.eu (ca. 101 Services)
2. **Fallback 1:** Bei Fehler wird `esc_services.json` verwendet
3. **Fallback 2:** Minimale hart-codierte Liste als letzter Ausweg

Die Services werden automatisch gefiltert, um Kategorien, SDKs und Programmiersprachen auszuschließen.

**Ausführungsfrequenz:** Monatlich am 1. Tag des Monats um 00:00 UTC (identisch mit anderen Service-Seiten)

## Dateistruktur

```json
{
  "metadata": {
    "last_updated": "2026-01-28",
    "source": "AWS European Sovereign Cloud Documentation",
    "region": "eusc-de-east-1 (Brandenburg, Germany)",
    "total_services": 90,
    "description": "List of AWS services available in the European Sovereign Cloud"
  },
  "services": [
    "Amazon EC2",
    "AWS Lambda",
    ...
  ],
  "planned_services": {
    "Q1_2026": ["AWS SSO"],
    "future": ["Additional services to be announced"]
  },
  "regions": {
    "available": ["eusc-de-east-1"],
    "planned": [
      "Belgium (Sovereign Local Zone)",
      "Netherlands (Sovereign Local Zone)",
      "Portugal (Sovereign Local Zone)"
    ]
  }
}
```

## Aktualisierung der Service-Liste

### Automatische Aktualisierung (Standard)

Die Lambda-Funktion lädt **automatisch** bei jeder Ausführung die aktuellen Services von docs.aws.eu:

1. **Monatlich:** Lambda wird am 1. Tag des Monats um 00:00 UTC ausgeführt (via EventBridge)
2. **Dynamisch:** Holt aktuelle Services von docs.aws.eu (ca. 101 Services)
3. **Gefiltert:** Entfernt automatisch Kategorien, SDKs und Programmiersprachen
4. **Fallback:** Verwendet `esc_services.json` bei Fehlern

**Keine manuelle Aktualisierung erforderlich!** Das System bleibt automatisch aktuell (identisch mit anderen Service-Seiten).

### Manuelle Aktualisierung (nur bei Bedarf)

Falls Sie die Fallback-Liste manuell aktualisieren möchten:

1. Führe das Extraktions-Skript aus:
   ```bash
   cd debug
   python3 extract_real_esc_services.py
   ```
2. Teste lokal:
   ```bash
   python3 test_local.py --source esc
   ```
3. Deploye die Änderungen:
   ```bash
   cd ..
   ./deploy.sh
   ```

**Hinweis:** Dies ist nur nötig, wenn Sie die Fallback-Liste in `esc_services.json` aktualisieren möchten. Die Lambda-Funktion holt die Services automatisch von docs.aws.eu.

## Service-Namen-Format

Die Service-Namen in der Liste sollten dem offiziellen AWS-Format entsprechen:

- **Mit Präfix**: `Amazon EC2`, `AWS Lambda`, `Amazon S3`
- **Konsistent**: Verwende immer denselben Namen wie in der AWS-Dokumentation
- **Vollständig**: Keine Abkürzungen (außer offiziellen wie "EC2", "S3")

### Beispiele für korrekte Namen:

✅ `Amazon EC2`
✅ `AWS Lambda`
✅ `Amazon S3`
✅ `Amazon RDS`
✅ `AWS KMS`

### Beispiele für inkorrekte Namen:

❌ `EC2` (fehlt Präfix)
❌ `Lambda` (fehlt Präfix)
❌ `Simple Storage Service` (verwende "Amazon S3")

## Quellen für ESC-Service-Updates

1. **AWS ESC Dokumentation**: https://www.aws.eu/
2. **AWS ESC Service-Ankündigungen**: AWS Blog und What's New
3. **AWS ESC Roadmap**: Geplante Services und Features
4. **AWS Capabilities Matrix**: Offizielle Service-Verfügbarkeit (wenn verfügbar)

## Geplante Services

Services, die für ESC angekündigt aber noch nicht verfügbar sind, sollten im `planned_services`-Abschnitt aufgeführt werden:

```json
"planned_services": {
  "Q1_2026": [
    "AWS SSO"
  ],
  "Q2_2026": [
    "Weitere Services..."
  ],
  "future": [
    "Additional services to be announced"
  ]
}
```

## Filter-Logik

Die Filter-Funktion in `lambda_handler.py` (`get_data_from_esc()`) vergleicht Service-Namen mit mehreren Varianten:

1. Vollständiger Name mit Präfix: `AWS Lambda`
2. Name ohne Präfix: `Lambda`
3. Mit "Amazon"-Präfix: `Amazon Lambda`
4. Mit "AWS"-Präfix: `AWS Lambda`

Dies stellt sicher, dass Services auch dann gefunden werden, wenn die Namensformate leicht variieren.

## Regionen

Die ESC-Regionen werden im `regions`-Abschnitt verwaltet:

```json
"regions": {
  "available": [
    "eusc-de-east-1"
  ],
  "planned": [
    "Belgium (Sovereign Local Zone)",
    "Netherlands (Sovereign Local Zone)",
    "Portugal (Sovereign Local Zone)"
  ]
}
```

## Bekannte ESC-Services (Stand: Februar 2026)

Die AWS European Sovereign Cloud startete am 15. Januar 2026 und bietet aktuell ca. **101 Services**:

**Hinweis:** Die genaue Anzahl wird automatisch von docs.aws.eu abgerufen und kann sich täglich ändern.

### Compute
- Amazon EC2, AWS Lambda, Amazon ECS, Amazon EKS, AWS Fargate

### Storage
- Amazon S3, Amazon EBS, Amazon S3 Glacier, Amazon EFS

### Databases
- Amazon RDS, Amazon Aurora, Amazon DynamoDB, Amazon DocumentDB, Amazon Neptune

### AI/ML
- Amazon SageMaker, Amazon Bedrock, Amazon Q

### Security
- AWS KMS, AWS Private Certificate Authority, Amazon GuardDuty, AWS CloudHSM, Amazon Macie

### Management & Governance
- AWS CloudTrail, AWS Config, AWS Organizations, AWS Control Tower, AWS Systems Manager

### Networking
- Amazon VPC, AWS Direct Connect, Amazon Route 53, AWS Transit Gateway, AWS PrivateLink

### Developer Tools
- AWS CodeCommit, AWS CodeBuild, AWS CodeDeploy, AWS CodePipeline, AWS CodeArtifact

### Analytics
- Amazon Kinesis, AWS Glue, Amazon Athena, Amazon EMR, Amazon Redshift, Amazon QuickSight

### Application Integration
- Amazon SNS, Amazon SQS, AWS Step Functions, Amazon EventBridge, Amazon API Gateway

Und viele weitere...

## Wartung

### Automatische Wartung
- **Monatlich:** Lambda-Funktion holt automatisch aktuelle Services von docs.aws.eu (1. Tag des Monats, 00:00 UTC)
- **Keine manuelle Intervention nötig:** System bleibt automatisch aktuell
- **Identisch mit anderen Service-Seiten:** Gleiche Ausführungsfrequenz wie AWS Global

### Manuelle Wartung (optional)
- **Quartalsweise:** Überprüfe die Fallback-Liste in `esc_services.json`
- **Bei Problemen:** Führe `debug/extract_real_esc_services.py` aus
- **Monitoring:** Prüfe CloudWatch Logs für Fehler beim dynamischen Laden

## Support

Bei Fragen oder Problemen:
1. Prüfe die AWS ESC-Dokumentation
2. Teste lokal mit `python3 test_local.py --source esc`
3. Überprüfe die Lambda-Logs in CloudWatch
