# Database Portfolio-PDM|MRF|Source|Welframe|HE Hub

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5329420410/Database%20Portfolio-PDM%7CMRF%7CSource%7CWelframe%7CHE%20Hub

**Created by:** Sateesh Bammidi on December 10, 2025  
**Last modified by:** Senthil Ramasamy on December 15, 2025 at 11:00 PM

---

This document provides an high level overview of database landscaping for following BUs: PDM|MRF|Source|Welframe|HE Hub

### **Executive Summary**

* **Total Database Inventory**: 1,956 databases across 5 business units
* **Source Platforms**: Azure (1,922 databases) + GCP (29 databases)
* **Target Platform**: AWS (RDS, Aurora, DocumentDB, DynamoDB)
* **Migration Scope**: Multi-cloud consolidation strategy

### **Current State Inventory**

* **Source BU**: 1,896 Azure SQL PaaS Databases (966 Production, 930 Non-Production)
* ![image-20251215-225826.png](images/image-20251215-225826.png)
* **Source BU**: Databases on Azure managed VM
* ![image-20251215-225920.png](images/image-20251215-225920.png)

* **HE Hub**: 4 Azure SQL Databases (1 Production, 1 Non-Production, 2 Development)
* **MRF**: 22 Azure Cosmos databases (6 Production, 7 Non-Production, 9 Development)

**GCP Workloads** (29 databases):

* **Welframe**: 23 Cloud SQL instances (8 Production, 15 Non-Production)
* **Welframe**: 6 BigQuery databases (1 Production, 5 Non-Production)

**Other**:

* **PDM**: 5 Azure Postgres databases (1 Production, 1 Non-Production, 3 Development)

---

### **Target AWS Architecture**

**Azure SQL → AWS RDS SQL Server / Aurora PostgreSQL**

* 1,900 databases consolidated
* Multi-database per RDS instance for cost optimization
* Read replicas for HA/DR

**Azure Cosmos → AWS DocumentDB / DynamoDB**

* 22 NoSQL databases migrated
* Native MongoDB compatibility (DocumentDB)

**GCP Cloud SQL → AWS RDS MySQL / PostgreSQL**

* 23 databases with CDC replication
* Cross-cloud migration via DMS

**GCP BigQuery → AWS Redshift / Athena**

* 6 data warehouse migrations
* S3 data lake integration

**Postgres → AWS RDS PostgreSQL / Aurora PostgreSQL**

* 5 databases with native compatibility

The following document presents a comprehensive database inventory listing for the various business units. Please **NOTE** that this table doesn't include the GC and HRP inventory.

| **DB Type** | **Source** | **Welframe** | **MRF** | **PDM** | **HE-HUB** |
| --- | --- | --- | --- | --- | --- |
| **Azure SQL Databases** | 1896 [966-P, 930-NP] | NA | NA | NA | 4 [2-D,1-NP,1-P] |
| **Azure SQL MI** | NA | NA | NA | NA | NA |
| **Azure Managed Postgres** | NA | NA | NA | NA | NA |
| **Azure Redis** | NA | NA | NA | NA | NA |
| **Azure SQL VM** | NA | NA | NA | NA | NA |
| **Azure Cosmos** | NA | NA | 22 [9-D, 7-NP, 6-P] | NA | NA |
| **Google Cloud SQL(postgres,MySQL)** | NA | 23 [15-NP, 8-P] | NA | NA | NA |
| **Google Big Query** | NA | 6 [5-NP, 1-P] | NA | NA | NA |
| **Azure Postgres** | NA | NA | NA | 5 [3- D, 1-NP, 1-P] | NA |

Migration Strategy Matrix
-------------------------

| **Source Database** | **Target AWS Service** | **Migration Tool** | **Strategy** |
| --- | --- | --- | --- |
| Azure SQL Database (1,900) | RDS SQL Server / Aurora PostgreSQL | AWS DMS, .bacpac export , Qlik Replicate | Rehost / Replatform |
| Azure Cosmos (22) | DocumentDB / DynamoDB | mongodump/mongorestore, DMS | Replatform |
| GCP Cloud SQL (23) | RDS MySQL/PostgreSQL | AWS DMS with CDC | Rehost with CDC |
| GCP BigQuery (6) | Redshift / Athena + S3 | Data export + S3 transfer | Refactor |
| Postgres (5) | RDS PostgreSQL / Aurora | pgdump/pgrestore, DMS | Rehost |

References
==========

* <https://healthedgetrial.sharepoint.com/:w:/r/sites/AWSCloudMigration/_layouts/15/Doc.aspx?sourcedoc=%7BAA2F6F57-15A2-4D22-8BCA-2DE24593B7EA%7D&file=MigrationApproaches_AzureSQLServerPostgreSQL_AWSRDS.docx&action=default&mobileredirect=true>
* <https://healthedgetrial.sharepoint.com/:w:/r/sites/AWSCloudMigration/_layouts/15/Doc.aspx?sourcedoc=%7BDC9EE417-11C1-4120-A742-7D0161D31E9D%7D&file=MigrationApproaches_AzureSQLServerPostgreSQLManagedInstances_AWSRDS.docx&action=default&mobileredirect=true>