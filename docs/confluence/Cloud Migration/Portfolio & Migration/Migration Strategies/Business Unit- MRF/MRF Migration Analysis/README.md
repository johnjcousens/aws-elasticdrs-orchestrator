# MRF Migration Analysis

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5360615425/MRF%20Migration%20Analysis

**Created by:** Sreenivas Algoti on December 16, 2025  
**Last modified by:** Sreenivas Algoti on December 30, 2025 at 06:31 PM

---

1. Executive Summary
====================

1.1 Project Overview
--------------------

MRF (Machine-Readable Files) is a healthcare price transparency platform currently hosted on Microsoft Azure. The system enables healthcare providers and payers to comply with federal transparency requirements by processing, managing, and publishing pricing information through machine-readable files.

1.2 Current Environment Summary
-------------------------------

The MRF system comprises:

| Component Category | Count | Migration Approach |
| --- | --- | --- |
| Virtual Machines | 1 | Rehost |
| AKS Clusters | 3 | Re-architect |
| CosmosDB Instances | 20 | Replatform |
| Storage Accounts | 6 | Replatform |
| Service Bus Namespaces | 4 | Re-architect |
| Container Registry | 1 | Replatform |
| **Total Resources** | **35** | Mixed |

1.3 Environments in Scope
-------------------------

* **Production (prod)** - High criticality
* **Non-Production** - Medium criticality
* **Development (dev)** - Low criticality

2. Service-to-Service Mapping (Azure to AWS)
============================================

2.1 Service Mapping Summary Table
---------------------------------

| Azure Service | AWS Primary | AWS Alternative | Migration Approach |
| --- | --- | --- | --- |

| Azure Service | AWS Primary | AWS Alternative | Migration Approach |
| --- | --- | --- | --- |
| Cloudflare DNS | Keep Cloudflare | Route 53 | Retain/Replatform |
| Azure VMs | Amazon EC2 |  | Re-architect |
| AKS | EKS |  | Re-architect |
| React SPA | Keep on EKS |  | Re-architect |
| MRF Requester Microservice | Keep on EKS |  | Re-architect |
| MRF Processor Microservice | Keep on EKS |  | Re-architect |
| MRF Pricer Mircroservice | Keep on EKS |  | Re-architect |
| Azure Service Bus | Amazon SNS + Amazon SQS (Fan-out Pattern) | MSK (Kafka) | Re-architect |
| Azure Cosmos DB | Amazon DocumentDB |  | Replatform |
| Blob Storage | Amazon S3 |  | Replatform |
| Key Vault | Secrets Manager | Parameter Store | Replatform |
| Log Analytics | CloudWatch Logs | OpenSearch | Replatform |
| App Insights | CloudWatch + X-Ray | Datadog | Replatform |
| Artifacts | CodeArtifact |  | Replatform |

---

3. Assumptions & Dependencies
=============================

3.1 Assumptions
---------------

* Application code can be modified to use AWS SDK for SQS/SNS
* DocumentDB supports all required MongoDB features currently used
* No functional changes to MRF application during migration (code freeze)
* Customer team available for testing and validation activities
* Existing container images are compatible with EKS
* Network bandwidth sufficient for data migration within planned timeline
* Customer can provide a 4-8 hour maintenance window for production cutover

3.2 Dependencies
----------------

| Dependency | Dependent Activity | Owner | Status |
| --- | --- | --- | --- |
| Site-to-Site VPN Setup | Post-cutover connectivity | Customers and HE Network Team | Pending |
| Internal team’s coordination | Integration testing with HE Hosted Payor Customer OLTP service | HE MRF Team | Pending |
| Cloudflare configuration | DNS updates for AWS | HE Network Team | Pending |