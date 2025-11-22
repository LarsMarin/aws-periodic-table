#!/bin/bash

# Konfiguration
ROLE_NAME="awsperiodictable-ProductScraperRole-MylDKsViJsWw"
POLICY_NAME="S3PutObjectPolicy"
REGION="eu-central-1"

echo "Aktualisiere IAM-Berechtigungen für Lambda-Rolle $ROLE_NAME..."

# Erstelle die Richtlinie
POLICY_ARN=$(aws iam create-policy \
    --policy-name "$POLICY_NAME" \
    --policy-document file://s3_policy.json \
    --query 'Policy.Arn' \
    --output text)

if [ -z "$POLICY_ARN" ]; then
    echo "Fehler: Konnte Richtlinie nicht erstellen."
    exit 1
fi

echo "Richtlinie erstellt: $POLICY_ARN"

# Füge die Richtlinie zur Rolle hinzu
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN"

echo "Richtlinie an Rolle angehängt."
echo "Die Lambda-Funktion sollte jetzt Zugriff auf die erforderlichen S3-Operationen haben."
