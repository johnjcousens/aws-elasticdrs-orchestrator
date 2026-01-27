# Database Portfolio : PDM (In Draft)

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5369233409/Database%20Portfolio%20%3A%20PDM%20%28In%20Draft%29

**Created by:** Sai Krishna Namburu on December 18, 2025  
**Last modified by:** Senthil Ramasamy on January 09, 2026 at 08:49 PM

---

This document provides an high level overview of database landscaping for following BUs: PDM

### **Executive Summary**

* **Total Database Inventory**: 5 Azure Postgres databases (1 Production, 1 Non-Production, 3 Development)
* **Source Platforms**: Azure
* **Target Platform**: AWS (RDS & Aurora)
* **Migration Scope**: Multi-cloud consolidation strategy

### **Current State Inventory**

* 5 Azure Postgres databases (1 Production, 1 Non-Production, 3 Development)

---

### **Target AWS Architecture**

<https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5369233409/Database+Portfolio+PDM+In+Draft#Target-AWS-Architecture>

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
| Postgres (5) | RDS PostgreSQL | pgdump/pgrestore, DMS | Re-platform (Azure to AWS RDS) |

Notes
=====

* Q1 Planning and Development, Development migration in Q2, Non-Prod Migration in Q3 and Prod Migration in Q4.
* PDM and MRF can go with HRP BU.
* Azure Postgres extensions currently in use: pg\_trgm and fuzzystrmatch.
* Production Managed Postgres is multi-AZ and non-prod are single AZ. 7 day backups is retained.
* The production database is currently uses 30% of the allocated size (512 GB). The database is expected to grow as new customers are on-boarded in near future.
* Point of contact  
  Weston Skeans, - PDM overall  
  [@Monkar Pathak](mailto:mpathak@healthedge.com) – Postgres, Airflow, data questions  
  [@Andrew Witkowski](mailto:andrew.witkowski@healthedge.com) – AI platform questions  
  [@Yogesh Uttarwar](mailto:yuttarwar@healthedge.com) – DevOps questions  
  [@Yogesh Uttarwar](mailto:yuttarwar@healthedge.com) / [@Todd Matton](mailto:tmatton@healthedge.com) / [@Aravind Rao](mailto:arao@healthedge.com) – Networking questions

References
==========

* <https://healthedgetrial.sharepoint.com/:w:/r/sites/AWSCloudMigration/_layouts/15/Doc.aspx?sourcedoc=%7BAA2F6F57-15A2-4D22-8BCA-2DE24593B7EA%7D&file=MigrationApproaches_AzureSQLServerPostgreSQL_AWSRDS.docx&action=default&mobileredirect=true>
* <https://healthedgetrial.sharepoint.com/:w:/r/sites/AWSCloudMigration/_layouts/15/Doc.aspx?sourcedoc=%7BDC9EE417-11C1-4120-A742-7D0161D31E9D%7D&file=MigrationApproaches_AzureSQLServerPostgreSQLManagedInstances_AWSRDS.docx&action=default&mobileredirect=true>
* <https://healthedgetrial.sharepoint.com/:x:/r/sites/AWSCloudMigration/_layouts/15/Doc.aspx?sourcedoc=%7B3F099370-4039-46B7-A636-CEC4CCBFAFA3%7D&file=PDM-Migration-Plan.xlsx&action=default&mobileredirect=true&wdOrigin=TEAMS-MAGLEV.null_ns.rwc&wdExp=TEAMS-TREATMENT&wdhostclicktime=1767803474112&web=1>
* [Master Sheet](https://healthedgetrial.sharepoint.com/:x:/r/sites/AWSCloudMigration/_layouts/15/Doc.aspx?sourcedoc=%7B3F099370-4039-46B7-A636-CEC4CCBFAFA3%7D&file=PDM-Migration-Plan.xlsx&action=default&mobileredirect=true&wdOrigin=TEAMS-MAGLEV.null_ns.rwc&wdExp=TEAMS-TREATMENT&wdhostclicktime=1767803474112&web=1)