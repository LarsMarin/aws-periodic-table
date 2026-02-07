# AWS European Sovereign Cloud (ESC) - Verfügbare Services

**Stand:** 6. Februar 2026  
**Region:** eusc-de-east-1 (Brandenburg, Germany)  
**Quelle:** docs.aws.eu (dynamisch abgerufen)  
**Anzahl Services:** 101 echte AWS Services

## Übersicht

Die AWS European Sovereign Cloud wurde am 15. Januar 2026 gestartet und bietet derzeit **101 AWS Services** an. Das System holt die Services dynamisch von docs.aws.eu, wobei Kategorien und Programmiersprachen herausgefiltert werden.

## Verfügbare Services (alphabetisch)

### AWS Services (50)

1. AWS Account Management
2. AWS AppConfig
3. AWS Artifact
4. AWS Backup
5. AWS Batch
6. AWS Billing and Cost Management
7. AWS Certificate Manager
8. AWS CLI
9. AWS Cloud Development Kit (AWS CDK)
10. AWS Cloud Map
11. AWS CloudFormation
12. AWS CloudTrail
13. AWS CodeDeploy
14. AWS Compute Optimizer
15. AWS Config
16. AWS Control Tower
17. AWS Database Migration Service
18. AWS DataSync
19. AWS Direct Connect
20. AWS Directory Service
21. AWS End User Messaging SMS
22. AWS Fargate
23. AWS Glue
24. AWS Health
25. AWS Identity and Access Management
26. AWS Key Management Service
27. AWS Lake Formation
28. AWS Lambda
29. AWS License Manager
30. AWS Management Console
31. AWS Marketplace
32. AWS Organizations
33. AWS Pricing Calculator
34. AWS Private Certificate Authority
35. AWS Resource Access Manager
36. AWS Resource Groups
37. AWS Secrets Manager
38. AWS Security Hub
39. AWS Shield
40. AWS Signer
41. AWS Step Functions
42. AWS Storage Gateway
43. AWS Support
44. AWS Systems Manager
45. AWS Transfer Family
46. AWS Trusted Advisor
47. AWS User Notifications
48. AWS Virtual Private Network
49. AWS WAF
50. AWS X-Ray

### Amazon Services (48)

1. Amazon API Gateway
2. Amazon Application Recovery Controller (ARC)
3. Amazon Athena
4. Amazon Aurora
5. Amazon Bedrock
6. Amazon CloudWatch
7. Amazon Cognito
8. Amazon Data Firehose
9. Amazon DocumentDB (with MongoDB compatibility)
10. Amazon DynamoDB
11. Amazon EC2 Auto Scaling
12. Amazon EKS
13. Amazon ElastiCache
14. Amazon Elastic Block Store
15. Amazon Elastic Compute Cloud
16. Amazon Elastic Container Registry
17. Amazon Elastic Container Service
18. Amazon Elastic File System
19. Amazon Elastic Kubernetes Service
20. Amazon EMR
21. Amazon EventBridge
22. Amazon FSx
23. Amazon GuardDuty
24. Amazon Kinesis
25. Amazon Linux
26. Amazon Managed Service for Apache Flink
27. Amazon Managed Streaming for Apache Kafka
28. Amazon MQ
29. Amazon Neptune
30. Amazon OpenSearch Service
31. Amazon Q
32. Amazon Redshift
33. Amazon Relational Database Service
34. Amazon Route 53
35. Amazon SageMaker AI
36. Amazon Simple Email Service
37. Amazon Simple Notification Service
38. Amazon Simple Queue Service
39. Amazon Simple Storage Service
40. Amazon Simple Workflow Service
41. Amazon Virtual Private Cloud

### Weitere Services (3)

1. EC2 Image Builder
2. Elastic Load Balancing
3. Service Quotas

## Service-Kategorien

Die Services decken folgende Bereiche ab:

- **Compute:** EC2, Lambda, ECS, EKS, Fargate, Batch
- **Storage:** S3, EBS, EFS, FSx, Storage Gateway
- **Database:** RDS, Aurora, DynamoDB, DocumentDB, Neptune, Redshift, ElastiCache
- **Networking:** VPC, Route 53, Direct Connect, VPN, CloudFront (via CloudFormation)
- **Security:** IAM, KMS, Secrets Manager, GuardDuty, Security Hub, WAF, Shield
- **Analytics:** Athena, EMR, Kinesis, Glue, OpenSearch, QuickSight
- **AI/ML:** Bedrock, SageMaker, Q
- **Developer Tools:** CodeDeploy, CDK, CLI, X-Ray
- **Management:** CloudFormation, CloudTrail, Config, Systems Manager, Organizations
- **Application Integration:** API Gateway, EventBridge, SNS, SQS, Step Functions

## Geplante Services

### Q1 2026
- AWS IAM Identity Center (AWS SSO)

### Zukünftig
- Weitere Services werden angekündigt

## Regionen

### Verfügbar
- **eusc-de-east-1** (Brandenburg, Germany)

### Geplant
- Belgium (Sovereign Local Zone)
- Netherlands (Sovereign Local Zone)
- Portugal (Sovereign Local Zone)

## Technische Details

### Dynamisches Laden
Das System lädt die Services automatisch von docs.aws.eu:
- Die Lambda-Funktion ruft täglich die aktuelle Liste ab
- Fallback auf `esc_services.json` bei Fehlern
- Automatische Filterung von Kategorien und Nicht-Services

### Datei-Struktur
```json
{
  "metadata": {
    "last_updated": "2026-02-06",
    "source": "docs.aws.eu",
    "region": "eusc-de-east-1",
    "total_services": 101
  },
  "services": [...]
}
```

## Aktualisierung

Die Service-Liste wird automatisch aktualisiert:
1. **Täglich:** Lambda-Funktion holt aktuelle Daten von docs.aws.eu
2. **Fallback:** Bei Fehlern wird `esc_services.json` verwendet
3. **Manuell:** Mit `debug/extract_real_esc_services.py` kann die Liste manuell aktualisiert werden

```bash
cd debug
python3 extract_real_esc_services.py
```

## Hinweise

- Die Liste enthält nur echte AWS Services (keine Kategorien oder SDKs)
- Service-Namen entsprechen der offiziellen AWS-Dokumentation
- Einige Services haben längere Namen (z.B. "Amazon DocumentDB (with MongoDB compatibility)")
- Die Anzahl der Services kann sich mit neuen Releases ändern
