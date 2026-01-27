# Database Design and Implementation Guide

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5149425782/Database%20Design%20and%20Implementation%20Guide

**Created by:** Sai Krishna Namburu on October 06, 2025  
**Last modified by:** Lakshmi Bhavya Kondamadugula on November 21, 2025 at 09:34 AM

---

This area explains about overall database landscaping details for BUs : **HealthPayer Rules (HRP) and Guiding Care (GC)**, different use cases and strategies used for migrating database servers and clusters from on-premises / Azure / GCP to AWS.

1. HE Database Landscape
------------------------

**Types of Databases:**

* Relational Databases (SQL Server, Oracle, PostgreSQL, MySQL)
* NoSQL Databases (Cosmos DB, MongoDB)
* Data Virtualization and Masking (Delphix)

**Assessment and Discovery:**

* Current infrastructure inventory
* Database dependencies mapping
* Performance baseline metrics
* Licensing and compliance requirements

2. HRP Databases Landscape
--------------------------

* **Oracle** - Standalone
* **Delphix**

3. GC Databases Landscape
-------------------------

**a. SQL Server:**

* **Standalone:** Single instance deployments
* **Cluster with AOAG:** Always On Availability Groups for high availability
* **Cluster with AOAG + Transaction Replication (TR):** Hybrid setup for HA and data distribution
* **TR Distribution Server Configuration:** Centralized distribution architecture
* **Deployment Options:** Azure Managed Instance, Azure SQL Databases, On-premises

**b. Cosmos DB:** Globally distributed, multi-model database service

**c. PostgreSQL:** Open-source relational database

**d. MongoDB:** Document-oriented NoSQL database

**e. MySQL:** Open-source relational database management system

**f. Delphix:** Data virtualization and masking platform

4. Migration Strategies
-----------------------

**a. Standalone → Rehost (AWS Application Migration Service):**

* Lift-and-shift using AWS Application Migration Service (MGN)
* Minimal changes to application architecture

**b. Cluster with AOAG → Replatform (Distributed Availability Groups** - **DAG):**

* Distributed Availability Groups (DAG) for cross-environment synchronization
* Maintains high availability during migration

**c. Cluster with AOAG + Transaction Replication (TR) → Replatform (DAG) + TR Reconfiguration:**

* Migrate availability groups first
* Reconfigure transaction replication post-migration

**d. Storage → AWS DataSync + S3 Storage Gateway:**

* Automated data transfer using DataSync
* Hybrid cloud storage with S3 Gateway

5. Automation
-------------

**a. Target Infrastructure Creation:**

**i. Using CDK Constructs:**

* EC2 instance provisioning with pre-built AMI
* Pre-installed SQL Server
* Windows Server Failover Cluster (WSFC) features enabled

**ii. PowerShell Scripts:**

* **WSFC Creation:** Automated cluster setup
* **SQL Server Custom Configuration:**

  + Database Mail setup
  + Maintenance jobs configuration
  + TempDB optimization
  + MaxDOP (Max Degree of Parallelism) settings
  + MaxMem (Maximum Memory) allocation
  + Monitoring scripts deployment
* **Always On Availability Groups (AG) Setup:** Automated AG configuration with Listener

6. Performance Improvements
---------------------------

**a. EBS Volume Optimization:**

**i. Throughput Improvements:**

* Select appropriate EBS volume types (gp3, io2)
* Analyze on-prem storage metrics for EC2 volume baseline:

  + Extract current storage metrics from on-premises monitoring tools (Foglight, or server-level monitoring)  
    Gather key performance indicators including:  
     a. IOPS (Input/Output Operations Per Second)  
     b. Throughput rates  
     c. Peak usage patterns
* Optimize IOPS and throughput settings as per the instance type .
* Right-size volumes based on workload

**ii. GPT Format with 64K Allocation:**

* GPT (GUID Partition Table) format for volumes >2TB
* 64K allocation unit size for SQL Server workloads
* Improved I/O performance for database operations

References :
------------

### **Database Setup & Architecture**

* **OLTP Cluster Setup Options** - Configuration options for Online Transaction Processing database clusters
* **Delphix Engine Architecture on AWS** - Architecture documentation for Delphix data management platform deployment on AWS

### **Oracle Database Management**

* **HRP: Oracle Standalone Database Backup and Disaster Recovery Strategy** - Comprehensive backup and DR strategy for standalone Oracle databases

### **SQL Server Management : Guiding Care**

* **GC - SQL Server Cluster Migration Strategy** - Migration approach for SQL Server clustered environments
* **GC: SQLserver Database Backup Strategy** - Backup procedures and best practices for SQL Server
* **GC: SQLserver Clustering & Disaster Recovery Strategies** - Clustering configurations and disaster recovery planning
* **GCPF: SQL Server Standalone Migration Strategy** - Migration methodology for standalone SQL Server instances

### [**Migration Runbooks**](https://healthedgetrial.sharepoint.com/:x:/s/AWSCloudMigration/IQAmrTgYmBroTb82N_Pul5aJAXJqFXBrQ6EknCI16rNVoDI?e=Y9RTW6)

### **Performance & Optimization**

* **GC: Database Backup Performance Improvement Analysis** - Analysis and recommendations for improving backup performance

### **Automations**

* **SQL Server Cluster Setup Automation** **-** SQL Server Cluster provisioning with SQL Server installation, Domain Joining and WSFC & AOAG configuration.

### **Quick Links : Confluence**

[Migration Share Point](https://healthedgetrial.sharepoint.com/sites/AWSCloudMigration/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FAWSCloudMigration%2FShared%20Documents%2FMigration&viewid=837a22cf%2D54ca%2D4a80%2D9d28%2D95cf64c9e530&newTargetListUrl=%2Fsites%2FAWSCloudMigration%2FShared%20Documents&viewpath=%2Fsites%2FAWSCloudMigration%2FShared%20Documents%2FForms%2FAllItems%2Easpx)

[Master Data](https://healthedgetrial.sharepoint.com/:x:/r/sites/AWSCloudMigration/_layouts/15/Doc.aspx?sourcedoc=%7B0839EB17-98AD-400C-BC26-D6025FDCD775%7D&file=Master%20Data.xlsx&wdLOR=c574FE702-BF73-EB40-8458-6EF111D76A5B&action=default&mobileredirect=true)

[GC : Migration Runbooks](https://healthedgetrial.sharepoint.com/sites/AWSCloudMigration/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FAWSCloudMigration%2FShared%20Documents%2FMigration%2FGC&viewid=837a22cf%2D54ca%2D4a80%2D9d28%2D95cf64c9e530&newTargetListUrl=%2Fsites%2FAWSCloudMigration%2FShared%20Documents&viewpath=%2Fsites%2FAWSCloudMigration%2FShared%20Documents%2FForms%2FAllItems%2Easpx)

[HRP : Migration Runbooks](https://healthedgetrial.sharepoint.com/sites/AWSCloudMigration/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FAWSCloudMigration%2FShared%20Documents%2FMigration%2FHRP&viewid=837a22cf%2D54ca%2D4a80%2D9d28%2D95cf64c9e530&newTargetListUrl=%2Fsites%2FAWSCloudMigration%2FShared%20Documents&viewpath=%2Fsites%2FAWSCloudMigration%2FShared%20Documents%2FForms%2FAllItems%2Easpx)

[Application Portfolio Analysis](https://healthedgetrial.sharepoint.com/sites/AWSCloudMigration/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FAWSCloudMigration%2FShared%20Documents%2FApplication%20Portfolio%20Analysis&viewid=837a22cf%2D54ca%2D4a80%2D9d28%2D95cf64c9e530&newTargetListUrl=%2Fsites%2FAWSCloudMigration%2FShared%20Documents&viewpath=%2Fsites%2FAWSCloudMigration%2FShared%20Documents%2FForms%2FAllItems%2Easpx)