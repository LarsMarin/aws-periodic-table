# Graph Report - .  (2026-06-26)

## Corpus Check
- Corpus is ~24,223 words - fits in a single context window. You may not need a graph.

## Summary
- 111 nodes · 104 edges · 31 communities (19 shown, 12 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.8)
- Token cost: 13,250 input · 2,310 output

## Community Hubs (Navigation)
- [[_COMMUNITY_ESC Service Data|ESC Service Data]]
- [[_COMMUNITY_Lambda Handler Core|Lambda Handler Core]]
- [[_COMMUNITY_CloudFront & Security|CloudFront & Security]]
- [[_COMMUNITY_ESC Filtering Pipeline|ESC Filtering Pipeline]]
- [[_COMMUNITY_AWS Deployment Stack|AWS Deployment Stack]]
- [[_COMMUNITY_Deploy Script|Deploy Script]]
- [[_COMMUNITY_Bucket Setup Script|Bucket Setup Script]]
- [[_COMMUNITY_Directory API Debug|Directory API Debug]]
- [[_COMMUNITY_HTML Template Engine|HTML Template Engine]]
- [[_COMMUNITY_Data Source Scrapers|Data Source Scrapers]]
- [[_COMMUNITY_Project Documentation|Project Documentation]]
- [[_COMMUNITY_Claude Code Config|Claude Code Config]]
- [[_COMMUNITY_ESC Services Extractor|ESC Services Extractor]]
- [[_COMMUNITY_ESC Builder Fetcher|ESC Builder Fetcher]]
- [[_COMMUNITY_ESC Services Fetcher|ESC Services Fetcher]]
- [[_COMMUNITY_TecRacer Brand Assets|TecRacer Brand Assets]]
- [[_COMMUNITY_Kilocode Plugin|Kilocode Plugin]]
- [[_COMMUNITY_Symbol Generation|Symbol Generation]]
- [[_COMMUNITY_Lambda Build Script|Lambda Build Script]]
- [[_COMMUNITY_S3 Website Config|S3 Website Config]]
- [[_COMMUNITY_Route53 DNS|Route53 DNS]]
- [[_COMMUNITY_CloudFront Setup|CloudFront Setup]]
- [[_COMMUNITY_DNS Setup|DNS Setup]]
- [[_COMMUNITY_TecRacer Logo|TecRacer Logo]]

## God Nodes (most connected - your core abstractions)
1. `metadata` - 6 edges
2. `lambda_handler()` - 6 edges
3. `deploy.sh script` - 5 edges
4. `get_data_from_directory()` - 5 edges
5. `setup-buckets.sh script` - 5 edges
6. `ProductScraper (Lambda Function CF Resource)` - 5 edges
7. `main()` - 4 edges
8. `load_esc_services()` - 4 edges
9. `get_data_from_scrape()` - 4 edges
10. `get_data_from_esc()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `AWS Periodic Table README` --semantically_similar_to--> `AWS Periodic Table Project (CLAUDE.md)`  [INFERRED] [semantically similar]
  README.md → CLAUDE.md
- `esc_services.json (ESC Fallback JSON Cache)` --semantically_similar_to--> `esc_services.json (ESC Service List Fallback File)`  [INFERRED] [semantically similar]
  periodic/ESC_SERVICES_README.md → CLAUDE.md
- `AWS European Sovereign Cloud (ESC) Services Overview` --semantically_similar_to--> `ESC Name-Matching Filter Logic`  [INFERRED] [semantically similar]
  ESC_SERVICES_OVERVIEW.md → periodic/ESC_SERVICES_README.md
- `deploy.sh (Deployment Script)` --references--> `ProductScraper (Lambda Function CF Resource)`  [INFERRED]
  CLAUDE.md → infrastructure/template.yaml
- `Lambda Deployment Instructions` --references--> `ProductScraper (Lambda Function CF Resource)`  [INFERRED]
  periodic/lambda_deployment_instructions.md → infrastructure/template.yaml

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **ESC Service Filtering Pipeline** — claude_md_get_data_from_esc, periodic_esc_services_readme_esc_services_json, esc_services_overview_md_esc_cloud, periodic_esc_services_readme_filter_logic [EXTRACTED 0.95]
- **Lambda Deployment and Monthly Schedule Flow** — claude_md_deploy_sh, infrastructure_template_product_scraper, infrastructure_template_product_scraper_schedule, infrastructure_template_product_scraper_role [EXTRACTED 1.00]
- **CloudFront Secure Content Delivery Setup** — infrastructure_cloudfront_distribution, infrastructure_cloudfront_oac, infrastructure_cloudfront_bucket_policy, security_headers_md_config [INFERRED 0.85]

## Communities (31 total, 12 thin omitted)

### Community 0 - "ESC Service Data"
Cohesion: 0.14
Nodes (13): metadata, description, last_updated, region, source, total_services, planned_services, future (+5 more)

### Community 1 - "Lambda Handler Core"
Cohesion: 0.44
Nodes (9): compute_positions(), create_symbol(), get_data_from_directory(), get_data_from_esc(), get_data_from_scrape(), lambda_handler(), load_esc_services(), parse_name() (+1 more)

### Community 2 - "CloudFront & Security"
Cohesion: 0.25
Nodes (8): BucketPolicy (S3 OAC Access Policy CF Resource), Certificate (ACM TLS Certificate CF Resource), CloudFrontDistribution (CloudFront CF Resource), CloudFrontOAC (Origin Access Control CF Resource), Security Headers Configuration Guide, Content-Security-Policy Header, Strict-Transport-Security (HSTS) Header, Permissions-Policy Header

### Community 3 - "ESC Filtering Pipeline"
Cohesion: 0.29
Nodes (7): esc_services.json (ESC Service List Fallback File), get_data_from_esc (ESC Filter function), AWS European Sovereign Cloud (ESC) Services Overview, eusc-de-east-1 (ESC Region, Brandenburg Germany), esc_services.json (ESC Fallback JSON Cache), ESC Name-Matching Filter Logic, requests (HTTP Client Dependency)

### Community 4 - "AWS Deployment Stack"
Cohesion: 0.40
Nodes (6): deploy.sh (Deployment Script), ProductScraper (Lambda Function CF Resource), ProductScraperRole (IAM Execution Role CF Resource), ProductScraperSchedule (EventBridge Monthly Rule CF Resource), Lambda Deployment Instructions, boto3 (AWS Python SDK Dependency)

### Community 5 - "Deploy Script"
Cohesion: 0.60
Nodes (5): print_error(), print_info(), print_warning(), usage(), deploy.sh script

### Community 6 - "Bucket Setup Script"
Cohesion: 0.60
Nodes (5): print_error(), print_info(), print_warning(), usage(), setup-buckets.sh script

### Community 7 - "Directory API Debug"
Cohesion: 0.70
Nodes (4): fetch_products(), load_json(), main(), merge_lists()

### Community 8 - "HTML Template Engine"
Cohesion: 0.50
Nodes (4): base_template.mustache (Base HTML Template), compute_positions (Grid Layout Mapper), template.mustache (Periodic Table Grid Template), pystache (Mustache Template Engine Dependency)

### Community 9 - "Data Source Scrapers"
Cohesion: 0.67
Nodes (3): get_data_from_directory (Directory API fetch), get_data_from_scrape (Web Scraping fetch), beautifulsoup4 (Python HTML Parser Dependency)

### Community 10 - "Project Documentation"
Cohesion: 0.67
Nodes (3): AWS Periodic Table Project (CLAUDE.md), Contributing Guide, AWS Periodic Table README

### Community 15 - "TecRacer Brand Assets"
Cohesion: 1.00
Nodes (3): Favicon - tecRacer Orange Arrow Icon, tecRacer Brand, Orange Upper-Right Arrow Icon

## Knowledge Gaps
- **38 isolated node(s):** `allow`, `@kilocode/plugin`, `build.sh script`, `configure-s3-website.sh script`, `setup-cloudfront.sh script` (+33 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `allow`, `@kilocode/plugin`, `Fetch ESC services from docs.aws.eu` to the rest of the system?**
  _43 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ESC Service Data` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._