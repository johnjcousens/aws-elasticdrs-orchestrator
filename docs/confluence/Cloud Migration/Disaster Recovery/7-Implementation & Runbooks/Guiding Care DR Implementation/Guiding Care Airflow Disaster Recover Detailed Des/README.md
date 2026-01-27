# Guiding Care Airflow Disaster Recover Detailed Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5287510036/Guiding%20Care%20Airflow%20Disaster%20Recover%20Detailed%20Design

**Created by:** Venkata Kommuri on December 01, 2025  
**Last modified by:** Chris Falk on December 18, 2025 at 08:14 PM

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Service:** AWS Elastic Disaster Recovery (DRS)  
**Application:** Apache Airflow (ETL Orchestration Platform)  
**Target RTO:** 4 hours | **Target RPO:** 15 minutes  
**Primary Regions:** US-East-1 (Virginia), US-West-2 (Oregon)  
**DR Regions:** US-East-2 (Ohio), US-West-1 (N. California)  
**Replication Method:** AWS DRS continuous block-level replication  
**Current Environment:** On-Premises (IAD3 Reston, LX3 Los Angeles)

**CRITICAL - HEALTHCARE DATA PROCESSING:** This runbook implements disaster recovery for Airflow deployed on EC2 instances using AWS DRS to ensure ETL workflow continuity during regional outages.

#### ⚠️ IMPORTANT - THIS DOCUMENT ASSUMES MIGRATED AIRFLOW INSTANCE IN AWS PRIMARY REGION MATCHES ON-PREMISES AIRFLOW CONFIGURATION

**All instance sizing, storage configuration, Airflow version, and software installation must match your current on-premises Airflow deployment.**

1. Apache Airflow + AWS DRS Overview
------------------------------------

### 1.1 Solution Overview

This runbook implements disaster recovery for **Apache Airflow ETL orchestration platform** using AWS Elastic Disaster Recovery (DRS).

#### Key Characteristics:

* **ETL Orchestration:** Manages nightly data loads from SFTP to MongoDB to SQL Server
* **Block-Level Replication:** Continuous replication of all EBS volumes
* **RPO: 15 minutes** - Point-in-time recovery with continuous snapshots
* **RTO: 4 hours** - Automated recovery to DR region
* **Multi-Region Support:** Primary (US-East-1/US-West-2) to DR (US-East-2/US-West-1)

2. Architecture & Design Rationale
----------------------------------

#### Apache Airflow with AWS DRS Architecture

![GC-Airflow-DR-Design.drawio.png](images/GC-Airflow-DR-Design.drawio.png)


```

                                                                                                        
│  INTEGRATION POINTS:                                RECOVERY FLOW:                                    │
│  1. SFTP Server (data ingestion)                    1. Initiate recovery from DRS console             │
│  2. MongoDB (intermediate storage)                  2. DRS launches recovery instance                 │
│  3. SQL Server (target database)                    3. All EBS volumes attached/mounted               │
│  4. External APIs (data sources)                    4. Promote Database read replica to primary       │
│  5. Secrets Manager (credentials)                   5. Update Airflow connection strings              │
│  6. CloudWatch (monitoring)                         6. Start Airflow services (webserver/scheduler)   │
│                                                     7. Update  DNS                                    │
│                                                     8. Resume DAG execution from last state           │
│                                                     9. Verify ETL pipeline connectivity               │

            
```


Prerequisites & Planning
------------------------

### AWS Account Prerequisites

#### This document assumes Airflow is setup with proper configuration and integration in us-east-1/us-west-2 regions.

DRS Service Setup & Configure And Monitor
-----------------------------------------

#### Please refer to AWS DRS Service for EC2 document : AWS Disaster Recovery Service Setup for EC2

Failover Procedures
-------------------

### Production Failover Procedure

#### Step 1: Declare DR Event

#### Step 2: Initiate Production Recovery

#### Step 3: Promote Database Read Replica

#### Step 4: Verify Recovery Instance

#### Step 5: Verify Airflow Services

#### Step 6: Update DNS and Network Configuration

#### Step 7: Validate ETL Pipeline

#### Step 8: Resume Production Operations

Failback Procedures
-------------------

### Failback Procedure

#### Step 1: Prepare Primary Region

#### Step 2: Pause DAGs in DR Region

#### Step 3: Cutover to Primary Region

#### Step 4: Validate Primary Region Operations

#### Step 5: Decommission DR Instance