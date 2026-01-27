# Runbook - HRP Oracle Standalone Migration

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5325193248/Runbook%20-%20HRP%20Oracle%20Standalone%20Migration

**Created by:** Sai Krishna Namburu on December 09, 2025  
**Last modified by:** Sai Krishna Namburu on December 09, 2025 at 12:00 PM

---

Overview
--------

This runbook provides step-by-step guidance for migrating HRP Oracle standalone database servers from on-premises infrastructure to AWS using AWS Application Migration Service (MGN). The migration follows a re-host strategy with minimal downtime.

**Migration Approach:** Re-host using AWS MGN  
**Target Platform:** Amazon EC2  
**Database Type:** Oracle Standalone

Migration Phases:
-----------------

Phase 1: Assessment & Planning
------------------------------

### Objective

Evaluate the current environment and finalize migration strategy.

### Key Activities

**Environment Assessment**

* Evaluate current Oracle environment including servers, configurations, dependencies, and data
* Dive deep into Oracle VM configurations: database version, features used, and size
* Check for enterprise features usage in the Oracle environment
* Review current data archival, backup strategy, and third-party tools (RMAN, backup intervals, retention policies)

**Migration Planning**

* Define Recovery Time Objective (RTO) and Recovery Point Objective (RPO)
* Identify application dependencies and downstream jobs (ETL or shell scripts)
* Gather all network, firewall, and port requirements
* Evaluate migration options using MGN and present pros/cons for stakeholder signoff
* Finalize the MGN-based migration approach

**Resource Allocation**

* Identify and allocate resources from application and technical teams
* Confirm disposition for all servers in scope

---

Phase 2: Prerequisites
----------------------

### Objective

Establish foundational infrastructure, DB and access requirements.

**Infrastructure & DB Checks**

* Run Database HealthCheck Scripts on source servers (T-15 before migration)
* Confirm target AWS account subnets for Oracle DB placement
* Verify Active Directory connectivity/extension to AWS (if needed)
* Gather DB performance metrics from on-premises (30 days: IOPS, throughput, network performance)

---

Phase 3: Pre-Migration Tasks (Source Server)
--------------------------------------------

### Objective

Validate and document source environment configuration.

**Source Environment Verification**

* Verify source listener configurations and document status
* Verify disk space and document filesystem layout
* Document Oracle paths: *ORACLE\_BASE, ORACLE\_HOME, data files, archive logs, backup paths*
* Verify last DB backup availability (to satisfy RPO requirements)
* Verify network files: *tnsnames.ora, local listener parameters, customizations*
* Copy /etc/hosts and fstab files for reference

---

Phase 4: Pre-Cutover
--------------------

### Objective

Prepare and validate target AWS infrastructure.

### Database Checks


```
-- Verify the backups
LIST BACKUP;
CROSSCHECK BACKUP;
--
BACKUP CURRENT CONTROLFILE;
BACKUP SPFILE;
-- Version Check
SELECT * FROM v$version;

-- Patch Information
SELECT * FROM dba_registry_history;
SELECT patch_id, action, status, description
FROM dba_patches;

-- Overall Database Size
SELECT SUM(bytes)/1024/1024/1024 AS SIZE_GB
FROM dba_data_files;

-- Tablespace Usage
SELECT
    df.tablespace_name,
    df.bytes/1024/1024 "SIZE_MB",
    (df.bytes - sum(fs.bytes))/1024/1024 "USED_MB",
    sum(fs.bytes)/1024/1024 "FREE_MB",
    round(((df.bytes - sum(fs.bytes))/df.bytes)*100,2) "PCT_USED"
FROM dba_data_files df,
     dba_free_space fs
WHERE df.tablespace_name = fs.tablespace_name(+)
GROUP BY df.tablespace_name, df.bytes;

-- TEMP Tablespace Usage
SELECT * FROM v$temp_space_header;

-- Invalid Objects
SELECT owner, object_type, object_name, status
FROM dba_objects
WHERE status != 'VALID';

-- Fragmented Tables
SELECT
    table_name,
    blocks,
    empty_blocks,
    avg_space,
    chain_cnt
FROM dba_tables
WHERE chain_cnt > 0;

-- Stale Statistics
SELECT
    owner,
    table_name,
    last_analyzed,
    stale_stats
FROM dba_tab_statistics
WHERE stale_stats = 'YES';
-- RMAN Backup Status
SELECT
    session_key,
    input_type,
    status,
    start_time,
    end_time,
    elapsed_seconds
FROM v$rman_backup_job_details
ORDER BY start_time DESC;

-- Archive Log Status
SELECT * FROM v$archive_dest_status;
```


### Key Activities

**Target Infrastructure Validation**

* Verify target EC2 instance type metrics in launch template
* Verify target storage type configuration in launch template
* Verify security groups for inbound DB ports (1521) and integration traffic (e.g., Delphix)
* Verify AWS Network Firewall rules

**DB Readiness**

* Verify Source Listener configurations
* Verify Disk Space
* Environment Verification
* Verify Last DB Backup availability ( on-premises)
* Verify Network Files (on-premises)
* hosts & fstab (on-premises)
* Verify all Internal HE Network FW tickets are implemented prior to migration

---

Phase 5: Migration Cutover
--------------------------

### Objective

Execute the migration with minimal downtime.

### Key Activities

**Pre-Cutover Validation**

* Verify target readiness: EC2 3/3 status checks in MGN Console
* Verify cloud replication status
* Mute monitoring tools (SolarWinds, AppDynamics)
* Send customer communications

**Source Shutdown**

* Take latest archive log backup on source (if applicable)
* Stop Oracle DB and listener services on-premises
* Shutdown source database server
* Update on-premises server tag to "DO NOT START"

**Target Launch & Configuration**

* Once target server is available, start Oracle DB and Listener services.
* Run HealthCheck Scripts post cutover.

**HealthCheck Script, validates the following areas:**

* 
```
Execute automated post-launch scripts:

verify_hostname: Validate server hostname

check_hosts_file: Review /etc/hosts configuration

backup_hosts_file: Create backup of existing hosts file

get_current_ip: Obtain current AWS instance IP

update_hosts_file: Update hosts file with AWS IP (if entry exists)

check_filesystem: Verify filesystem mounts and space

check_oratab: Validate database entries in oratab

restart_databases: Perform controlled database restart

handle_listener: Manage listener configuration and restart

perform_tnsping: Validate database connectivity

perform_rman_checks: Verify RMAN configuration


```


**Application Integration**

* Verify backup volume availability (accommodate two full backups)
* Recreate database links with new DNS names (if required)
* Run Database HealthCheck Scripts on AWS
* Update application connection strings (if IP addresses are used)
* Validate third-party connections (Delphix, other integrations)

**Testing & Validation**

* Perform additional sanity checks for DB connectivity and dependencies
* Validate application and user connectivity
* Verify server configuration: tags, encryption, security groups, subnets, AZ, IAM roles
* Trigger full backup on AWS (if applicable)

**Cutover Completion**

* Application testing by application team
* Integration testing (upstream and downstream dependencies)
* Validate network aspects (NFS, latency requirements)
* Perform smoke testing
* Obtain application validation agreement
* Enable Amazon EC2 termination protection
* Close change record

---

Phase 6: Rollback Procedures ( If Needed)
-----------------------------------------

### Objective

Provide contingency plan if migration fails.

### Key Activities

**Rollback Steps** (Execute only if migration fails)

1. Shutdown AWS EC2 instances
2. Bring source servers back online
3. Start Oracle DB and listener services on-premises
4. Update DNS with original source server IPs
5. Update application connection strings to point to on-premises
6. Verify connectivity and dependencies
7. Schedule root cause analysis meeting

---

Phase 7: Post-Migration & Handover
----------------------------------

### Objective

Validate successful migration and transition to operations.

### Key Activities

**Database Validation**

* Perform database health check (verify database status, tablespaces, services)
* Verify backup jobs and schedules are configured
* Verify DB monitoring setup (OEM integration for new DB)
* Validate third-party connectivity (Delphix and other integrations)

**Scripts**

HealthCheck Automation Script

Above script validates the following areas post cutover.

|  |
| --- |
| verify\_hostname |
| check\_hosts\_file |
| backup\_hosts\_file |
| get\_current\_ip |
| update\_hosts\_file (only if the IP entry exists: update to AWS DB server IP) |
| check\_filesystem |
| check\_oratab |
| restart\_databases |
| handle\_listener |
| perform\_tnsping |
| perform\_rman\_checks |

**Application Testing**

* Performance baseline validation post-migration
* PDV smoke test: End-to-end application connectivity validation
* PTT for selected customers: Critical claims adjudication workflow validation

**Operational Handover**

* Verify AWS Systems Manager Agent (SSM Agent) installation
* Update DNS TTL to original value
* Update documentation (Confluence & CMDB) with AWS server details
* Remove local admin user after validation period
* Hand over to support teams
* Plan decommissioning of source infrastructure

References:
-----------

[Migration Run book Link](https://healthedgetrial.sharepoint.com/:x:/r/sites/AWSCloudMigration/_layouts/15/Doc.aspx?sourcedoc=%7B914AEBC5-F229-4162-961F-1F027C01F03D%7D&file=Wave%201%20Migration%20Run%20book.xlsx&action=default&mobileredirect=true)

HealthCheck Automation Script

[AWS Blog](https://aws.amazon.com/blogs/database/migrate-oracle-applications-and-databases-using-aws-application-migration-service/)

Database Design and Implementation Guide