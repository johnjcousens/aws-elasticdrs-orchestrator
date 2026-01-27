# Database Portfolio : Welframe( In Draft)

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5369266217/Database%20Portfolio%20%3A%20Welframe%28%20In%20Draft%29

**Created by:** Sai Krishna Namburu on December 18, 2025  
**Last modified by:** Lakshmi Bhavya Kondamadugula on December 19, 2025 at 09:25 AM

---

This document provides an high level overview of database landscaping for following BUs: Welframe

### **Executive Summary**

* **Total Database Inventory**: 29 databases
* **Source Platforms**: GCP
* **Target Platform**: AWS (RDS, Aurora, Redshift)
* **Migration Scope**: Multi-cloud consolidation strategy

### **Current State Inventory**

**GCP Workloads** (29 databases):

* **Welframe**: 23 Cloud SQL instances (8 Production, 15 Non-Production)
* **Welframe**: 6 BigQuery databases (1 Production, 5 Non-Production)

### Source configuration details:

questionnaire:


```markdown
1. Version & Configuration: What MySQL version and edition, instance type (vCPUs/RAM), and storage size (GB) are you currently using?

2. Database schema: How many databases do you have? and the largest DB size.

3. High Availability: What is your current HA setup (multi-zone/regional), and do you have read replicas?

4. Application Dependencies: How many applications connect to the database, where are they hosted (GCP/on-prem/AWS), and what is the typical concurrent connection count?

5. Are you using direct connections, connection pooling, SSL/TLS, or specific authentication methods (IAM, service accounts)?

6. Do you use encryption at rest/in transit, customer-managed keys, and what authentication mechanisms are in place (IAM, service accounts)?

7. RTO/RPO: What are your Recovery Time Objective and Recovery Point Objective requirements?
   Backup Strategy: What is your current backup frequency, retention period, and have you tested disaster recovery procedures?

8. What is the maximum acceptable downtime for migration (zero-downtime required, maintenance window acceptable)?
   Do you prefer snapshot/restore, AWS DMS with continuous replication, logical dump (mysqldump), or hybrid approach?

9. Audit & Logging: What audit logging and data retention policies are required?

10. Compliance Requirements: What standards must be met (HIPAA, PCI-DSS, GDPR, etc.), and are there data residency requirements?

11. Performance Baseline: What are your peak IOPS, average daily transactions, and current CPU/memory utilization during peak hours?

12. Connectivity VPN/Direct connect.


```


---

### **Target AWS Architecture**

**GCP Cloud SQL → AWS RDS MySQL / PostgreSQL**

* 23 databases with CDC replication
* Cross-cloud migration via DMS

**GCP BigQuery → AWS Redshift / Athena**

* 6 data warehouse migrations
* S3 data lake integration

The following document presents a comprehensive database inventory listing for the various business units. Please **NOTE** that this table doesn't include the GC and HRP inventory.

Migration Strategy Matrix
-------------------------

| **Source Database** | **Target AWS Service** | **Migration Tool** | **Strategy** |
| --- | --- | --- | --- |
| GCP Cloud SQL (23) | RDS MySQL/PostgreSQL | AWS DMS with CDC | Rehost with CDC |
| GCP BigQuery (6) | Redshift / Athena + S3 | Data export + S3 transfer | Refactor |

References
==========

* <https://healthedgetrial.sharepoint.com/:w:/r/sites/AWSCloudMigration/_layouts/15/Doc.aspx?sourcedoc=%7BAA2F6F57-15A2-4D22-8BCA-2DE24593B7EA%7D&file=MigrationApproaches_AzureSQLServerPostgreSQL_AWSRDS.docx&action=default&mobileredirect=true>
* <https://healthedgetrial.sharepoint.com/:w:/r/sites/AWSCloudMigration/_layouts/15/Doc.aspx?sourcedoc=%7BDC9EE417-11C1-4120-A742-7D0161D31E9D%7D&file=MigrationApproaches_AzureSQLServerPostgreSQLManagedInstances_AWSRDS.docx&action=default&mobileredirect=true>