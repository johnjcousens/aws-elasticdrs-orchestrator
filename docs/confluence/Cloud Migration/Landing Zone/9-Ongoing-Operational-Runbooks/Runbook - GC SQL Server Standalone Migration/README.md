# Runbook - GC SQL Server Standalone Migration

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5323489473/Runbook%20-%20GC%20SQL%20Server%20Standalone%20Migration

**Created by:** Sai Krishna Namburu on December 09, 2025  
**Last modified by:** Lakshmi Bhavya Kondamadugula on December 09, 2025 at 12:10 PM

---

Overview
--------

This runbook provides step-by-step guidance for migrating SQL Server standalone database servers from on-premises infrastructure to AWS using AWS Application Migration Service (MGN). The migration follows a rehost strategy with minimal downtime.

**Migration Approach:** Rehost using AWS MGN  
**Target Platform:** Amazon EC2  
**Database Type:** SQL Server Standalone

Migration Phases
----------------

Phase 1: Assessment & Planning
------------------------------

### Objective

Evaluate the current SQL Server environment and finalize migration strategy.

### Key Activities

**Environment Assessment**

* Evaluate current environment including servers, configurations, dependencies, and data
* Dive deep into SQL Server VM configurations and details (version, edition, features, database sizes)
* Check for enterprise features usage in the current VM environment (Always On, Replication, SSIS, SSRS, SSAS)
* Review current data archival, backup strategy, and third-party tools usage (backup software, monitoring tools)

**Migration Planning**

* Define Recovery Time Objective (RTO) and Recovery Point Objective (RPO) for the migration
* Identify application dependencies of the database in the current scope
* Evaluate migration options for the existing SQL Server VM scenario using MGN
* Present migration options with pros and cons for stakeholder signoff
* Finalize the MGN-based migration approach for SQL Server VM

**Resource Allocation**

* Identify and allocate resources from application and database teams
* Confirm disposition for all servers in scope

---

Phase 2: Prerequisites
----------------------

### Objective

Establish foundational requirements and validate readiness.

### Key Activities

**Database Health Checks**

* Run Database HealthCheck Scripts on T-15 (15 days before migration)

  + DB connectivity checks
  + Database health assessment
  + Latest backup verification
  + Storage and free space analysis
  + SQL Server Agent jobs inventory
  + Regular DBA checks (error logs, performance metrics)

**AWS Infrastructure Preparation**

* In the AWS target account, confirm the subnets that will be used for SQL Server
* Verify Active Directory connectivity/extension to AWS (if needed)
* Confirm AWS account access for migration and database teams
* Verify VPN connectivity between on-premises and AWS

**Network & Security**

* Gather all network, firewall, and port requirements
* Submit firewall requests for database connectivity
* Verify VPN CIDR is allowed on both on-premises and AWS end

---

Phase 3: Pre-Migration Tasks
----------------------------

### Objective

Document source environment configuration and prepare for migration.

### Key Activities

**Source Environment Documentation**

* Document current SQL Server version, patch level, and configuration
* Verify and document disk spaces and filesystem layout
* Document SQL Server directories: Data, Log, and Backup paths
* Document existing backup schedules and verify latest backups
* Identify any third-party backup tools in use

**High Availability Configuration Review**

* Verify HADR (High Availability and Disaster Recovery) configuration if exists
* Verify AOAG (Always On Availability Groups) configuration if exists:

  + AOAG nodes
  + Listener port
  + Databases in AG
  + AG dashboard health

**MGN Agent Installation**

* Install AWS MGN replication agent on source servers
* Verify data replication initialization
* Monitor replication progress

---

Phase 4: Pre-Cutover
--------------------

### Objective

Validate target infrastructure and prepare for cutover.

### Key Activities

**Backup Validation**

* Verify recent DB backup is available (to satisfy RPO requirements)
* Backup required users and logins (other than AD users)
* Document SQL Server logins and permissions

**SQL Server Components Verification**

* If exists, verify and document SQL Agent jobs
* If exists, verify and document Linked Servers
* Document any custom scripts or scheduled tasks

**Target Infrastructure Validation**

* Verify target EC2 instance type metrics are appropriate
* Verify target storage type is suitable (EBS volume types, IOPS, throughput)
* Validate launch template configuration in MGN
* Check VPN CIDR is allowed on on-premises and AWS end
* Verify security groups for database ports (default 1433)

**MGN Readiness**

* Verify MGN replication status shows "Ready for Cutover"
* Confirm all data is synchronized
* Validate launch template settings

---

Phase 5: Migration Cutover
--------------------------

### Objective

Execute the migration with minimal downtime.

### Key Activities

**Pre-Cutover Validation**

* Verify target readiness in MGN console
* Ensure latest Full/Diff/Transaction log backup availability for all databases

  + Based on migration strategy and DB size, verify appropriate backup type
  + Keep backups ready to restore in case of issues
* Verify data replication status is current
* Send customer communications about maintenance window

**Source Shutdown**

* Stop SQL Server services on on-premises server
* Shutdown on-premises server
* Update on-premises server tag to "DO NOT START"

**Target Launch & Configuration**

* Launch cutover instance from MGN
* Verify target instance boot-up status (3/3 status checks)
* Connect to AWS target server via RDP/SSM
* Ensure all required security groups are attached to the EC2 instance

**Network Configuration**

* Retrieve and document new IP address
* Update hostname resolution
* Perform DB network changes
* Update DNS records

**SQL Server Service Startup**

* Restart SQL Server services on AWS
* Verify SQL Server services are running
* Check SQL Server error logs for any issues

**Post-Launch Validation**

* Verify filesystem mounts and disk configuration
* Verify backup volume availability (S3/Storage Gateway)
* Validate DB connectivity ports (1433 or custom)
* Perform DB connection checks from application servers

**Database Validation**

* Verify all databases are online and accessible
* Check database integrity
* Validate Linked Servers (recreate if necessary)
* Verify SQL Agent jobs are present and functional

**Application Integration**

* Update application connection strings (if IP addresses are used)
* Validate application and user connectivity
* Test third-party connections (monitoring tools, backup software, etc.)
* Perform smoke testing

**Cutover Completion**

* Application testing by application team
* Integration testing (upstream and downstream dependencies)
* Validate network aspects and latency requirements
* Obtain application validation agreement
* Enable Amazon EC2 termination protection
* Close change record

---

Phase 6: Rollback Procedures
----------------------------

### Objective

Provide contingency plan if migration fails.

### Key Activities

**Rollback Steps** (Execute only if migration fails)

1. Shutdown AWS EC2 instance
2. Bring the source servers back online
3. Start SQL Server services on on-premises server
4. Update DNS with old source server IPs
5. Update application connection strings to point to on-premises
6. Verify connectivity and dependencies
7. Schedule root cause analysis meeting

---

Phase 7: Post-Migration & Handover
----------------------------------

### Objective

Validate successful migration and transition to operations.

### Key Activities

**Database Health Checks**

* Perform comprehensive database health checks
* Verify database status, file sizes, and growth settings
* Check SQL Server error logs
* Validate tempdb configuration
* Review database properties and settings

**Application Testing**

* Conduct thorough application testing
* Performance baseline validation
* End-to-end functionality testing
* User acceptance testing

**Backup Configuration**

* Configure backup jobs and schedules
* Verify backup destinations (S3, Storage Gateway)
* Test backup and restore procedures
* Document backup retention policies

**Monitoring Setup**

* Configure database monitoring
* Set up alerting for critical metrics
* Integrate with existing monitoring tools
* Verify CloudWatch metrics collection

**Operational Handover**

* Verify AWS Systems Manager Agent (SSM Agent) installation
* Update documentation (Confluence, CMDB) with AWS server details
* Configure third-party integrations (if required)
* Hand over to support teams
* Plan decommissioning of source infrastructure

References

[SQL Server Migration Runbooks](https://healthedgetrial.sharepoint.com/:x:/r/sites/AWSCloudMigration/_layouts/15/Doc.aspx?sourcedoc=%7B9760730E-4442-4845-901F-E0A2B6440F93%7D&file=Wave%201%20Migration%20Run%20book.xlsx&action=default&mobileredirect=true)

Database Design and Implementation Guide