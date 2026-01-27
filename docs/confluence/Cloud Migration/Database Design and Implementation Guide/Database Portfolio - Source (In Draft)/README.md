# Database Portfolio : Source (In Draft)

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5369298945/Database%20Portfolio%20%3A%20Source%20%28In%20Draft%29

**Created by:** Sai Krishna Namburu on December 18, 2025  
**Last modified by:** Sateesh Bammidi on December 19, 2025 at 04:00 PM

---

This document provides an high level overview of database landscaping for following BUs: Source

### **Executive Summary**

* **Total Database Inventory**: 1,896 SQL PaaS Databases (966 Production, 930 Non-Production)
* **Source Platforms**: Azure
* **Target Platform**: AWS (RDS For SQL Server)
* **Migration Scope**: Multi-cloud consolidation strategy

### **Current State Inventory**

* **Source BU**: 1,896 Azure SQL PaaS Databases (966 Production, 930 Non-Production)
* ![image-20251215-225826.png](images/image-20251215-225826.png)
* **Source BU**: Databases on Azure managed VM
* ![image-20251215-225920.png](images/image-20251215-225920.png)

---

### **Target AWS Architecture**

**Azure SQL → AWS RDS SQL Server / Aurora PostgreSQL**

* 1,900 databases consolidated
* Multi-database per RDS instance for cost optimization
* Read replicas for HA/DR

**GCP BigQuery → AWS Redshift / Athena**

* 6 data warehouse migrations
* S3 data lake integration

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

Notes
=====

* Azure Managed Postgres instance for Azure OpenAI are relatively small in GB’s (5-10GB). Currently, it has only one customer.
* Azure Managed Postgres instance for Azure OpenAI stores configs and request/response data.
* No Postgres extensions being used.

References
==========

* <https://healthedgetrial.sharepoint.com/:w:/r/sites/AWSCloudMigration/_layouts/15/Doc.aspx?sourcedoc=%7BAA2F6F57-15A2-4D22-8BCA-2DE24593B7EA%7D&file=MigrationApproaches_AzureSQLServerPostgreSQL_AWSRDS.docx&action=default&mobileredirect=true>
* <https://healthedgetrial.sharepoint.com/:w:/r/sites/AWSCloudMigration/_layouts/15/Doc.aspx?sourcedoc=%7BDC9EE417-11C1-4120-A742-7D0161D31E9D%7D&file=MigrationApproaches_AzureSQLServerPostgreSQLManagedInstances_AWSRDS.docx&action=default&mobileredirect=true>