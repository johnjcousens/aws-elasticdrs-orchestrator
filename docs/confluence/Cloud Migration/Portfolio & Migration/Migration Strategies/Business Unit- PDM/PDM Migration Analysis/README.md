# PDM Migration Analysis

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5329649725/PDM%20Migration%20Analysis

**Created by:** Sreenivas Algoti on December 10, 2025  
**Last modified by:** Sreenivas Algoti on December 30, 2025 at 06:35 PM

---

1. Executive Summary
====================

1.1 Project Overview
--------------------

This document outlines the comprehensive migration plan for HealthEdge's Provider Data Management (PDM) application from Microsoft Azure to Amazon Web Services (AWS). The PDM system is a multi-tenant SaaS platform that serves as a centralized provider data management solution for healthcare payers, handling data ingestion, processing, quality management, and distribution workflows.

1.2 Current Environment Summary
-------------------------------

The PDM system comprises:

| Component Category | Count | Migration Approach |
| --- | --- | --- |
| Virtual Machines | 14 | Rehost |
| AKS Clusters | 5 | Re-architect |
| PostgreSQL Databases | 5 | Replatform |
| Storage Accounts | 14 | Replatform |
| Event Hubs | 5 | Replatform |
| API Management | 5 | Replatform |
| Other | 1 | Retire |
| **Total Resources** | **49** | Mixed |

1.3 Environments in Scope
-------------------------

* **Production (prod)** - High criticality
* **Non-Production (custnp)** - Medium criticality
* **QA** - Low criticality
* **Development (dev)** - Low criticality
* **Feature** - Low criticality
* **Sandbox** - Medium criticality

---

2. Current State Analysis
=========================

2.1 Architecture Components Identified
--------------------------------------

### 2.1.1 API & Integration Layer

| Component | Azure Service | Purpose |
| --- | --- | --- |
| API Management | Azure API Management | API gateway, rate limiting, security |
| Event Hubs | Azure Event Hubs | Real-time event streaming |
| Azure SFTP | SFTP Integration | Secure file transfer |
| MOVEit (**Out of Scope**) | SFTP Integration | MOVEit is no longer used. |

### 2.1.2 Compute Layer

| Component | Azure Service | Purpose |
| --- | --- | --- |
| React SPA | Pods on AKS | Single Page Application for user interface |
| Spring Microservices | Pods on AKS | Java-based business logic |
| Python Microservices | Pods on AKS | Data processing, AI/ML |
| Kogito Workflow | Pods on AKS | Business process automation |
| Airflow | Pods on AKS | Airflow jobs |
| Informatica MDM (2 Virtual Machines) | Azure VMs | MDM |
| DB Monitoring (1 Virtual Machine) | Azure VM | Database monitoring |

### 2.1.4 Data Layer

| Component | Azure Service | Purpose |
| --- | --- | --- |
| Primary Database | Azure PostgreSQL (Managed) | Provider data storage |
| Blob Storage | Azure Blob Storage | File storage, artifacts |

### 2.1.5 AI/ML

| Component | Azure Service | Purpose |
| --- | --- | --- |
| AI Engine | External to PDM (Separate AI infrastructure) | Data extraction from unstructured documents |

### 2.1.6 Security & Identity

| Component | Azure Service | Purpose |
| --- | --- | --- |
| Identity Provider | Azure AD | User authentication |
| Customer AD | Federation | Customer identity integration |
| WAF | Cloudflare WAF | Web application firewall |
| Secrets | Azure Key Vault | Secrets management |

### 2.1.7 Observability

| Component | Azure Service | Purpose |
| --- | --- | --- |
| Logging | Azure Log Analytics | Centralized logging |
| APIM | Azure App Insights | Application performance monitoring |
| Artifacts | Azure Artifacts | Build artifact storage |

### 2.1.8 AKS Clusters

| Cluster Name | Environment | Criticality | Migration Approach |
| --- | --- | --- | --- |
| PDMFEATURECLUSTER001 | Feature | Low | Re-architect |
| PDMDEVCLUSTER001 | Dev | Low | Re-architect |
| PDMQACLUSTER001 | QA | Low | Re-architect |
| PDMCUSTNPCLUSTER001 | NonProd | Medium | Re-architect |
| pdmaksprod001 | Prod | High | Re-architect |

### 2.1.9 PostgreSQL Databases

| Database Name | Environment | Version | Size | Criticality |
| --- | --- | --- | --- | --- |
| pdm-db-feature-001 | Feature | 16.8 | 128 GB | Low |
| pdm-db-dev-001 | Dev | 16.8 | 128 GB | Low |
| pdm-db-qa-001 | QA | 16.8 | 128 GB | Low |
| pdm-db-custnp-001 | NonProd | 16.8 | 128 GB | Medium |
| pdm-db-prod-001 | Prod | 16.8 | 512 GB | High |

---

3. Service-to-Service Mapping (Azure to AWS)
============================================

3.1 Service Mapping Summary Table
---------------------------------

| Azure Service | AWS Primary | AWS Alternative | Migration Approach |
| --- | --- | --- | --- |
| Azure AD | Amazon Cognito | IAM Identity Center | Replatform |
| Cloudflare WAF | AWS WAF | Keep Cloudflare | Retain/Replatform |
| API Management | API Gateway |  | Replatform |
| Azure VMs | Amazon EC2 |  | Re-architect |
| AKS | EKS |  | Re-architect |
| React SPA | Keep on EKS |  | Re-architect |
| Spring Microservices | Keep on EKS |  | Re-architect |
| Python Microservices | Keep on EKS |  | Re-architect |
| Kogito Workflow | Keep on EKS |  | Re-architect |
| Airflow | Keep on EKS | Amazon MWAA | Re-architect |
| Event Hubs | MSK (Kafka) | Kinesis | Replatform |
| PostgreSQL | Aurora PostgreSQL | RDS PostgreSQL | Replatform |
| Blob Storage | Amazon S3 |  | Replatform |
| Key Vault | Secrets Manager | Parameter Store | Replatform |
| Log Analytics | CloudWatch Logs | OpenSearch | Replatform |
| App Insights | CloudWatch + X-Ray | Datadog | Replatform |
| Artifacts | CodeArtifact |  | Replatform |
| SFTP | Transfer Family |  | Replatform |

---

4. Assumptions & Dependencies
=============================

4.1 Assumptions
---------------

| Assumption | Impact if Invalid | Validation Method |
| --- | --- | --- |
| Airflow DAGs use standard operators without Azure-specific dependencies | DAG rewrite required | DAG audit during discovery |
| Container images are architecture-agnostic (x86) | Image rebuild required | Image inspection; registry analysis |
| Current VM configurations can be mapped to equivalent EC2 instance types | Performance issues; resizing needed | Performance baseline comparison |
| Informatica MDM licenses are portable to AWS infrastructure | License renegotiation; additional costs | Vendor confirmation during discovery |
| MDM software supports deployment on Amazon Linux/RHEL on EC2 | Alternative deployment approach | Vendor documentation; testing |
| API Management policies can be recreated in AWS API Gateway | Feature gap analysis; alternative solutions | Policy review; feature comparison |
| Customer Azure AD tenants support SAML federation with Cognito | Alternative identity solution | Federation testing with sample customer |
| No major application changes planned during migration | Scope creep; moving target | Product roadmap review |

4.2 Dependencies
----------------

| Dependency | Dependent Activity | Owner | Status |
| --- | --- | --- | --- |
| Customer IdP SAML metadata | Cognito federation setup |  | Pending |
| Third-party IP allow-list updates (if any) | Post-cutover connectivity | External Vendors | Pending |
| Internal team’s coordination | Integration testing with HRP, GC and Wellframe | HE HRP, GC, Wellframe Product Team | Pending |
| Informatica MDM support | License transfer, installation support | HE Team, Informatica Vendor | Pending |
| Cloudflare configuration | DNS updates for AWS | HE Network Team | Pending |

---