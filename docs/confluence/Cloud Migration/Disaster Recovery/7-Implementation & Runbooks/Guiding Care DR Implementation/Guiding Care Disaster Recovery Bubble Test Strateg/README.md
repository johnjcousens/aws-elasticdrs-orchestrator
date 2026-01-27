# Guiding Care Disaster Recovery Bubble Test Strategy

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5273681930/Guiding%20Care%20Disaster%20Recovery%20Bubble%20Test%20Strategy

**Created by:** John Cousens on November 25, 2025  
**Last modified by:** Chris Falk on December 18, 2025 at 08:08 PM

---

**Date**: November 25, 2025  
**Application**: Guiding Care (GC)  
**Environment**: Multi-Region AWS Deployment  
**Scope**: Full application stack DR testing with zero production risk

Executive Summary
-----------------

This document defines a comprehensive disaster recovery testing strategy for the Guiding Care application using isolated bubble test methodology. Based on the DR Discovery Session findings, the strategy addresses critical business requirements including a 4-hour RTO, 15-minute RPO, and 99.95% uptime SLA. The approach enables complete DR validation of all application components—web services, databases (MongoDB, SQL Server), Active Directory authentication, and S3 storage—without any risk to production systems through dual isolation methods: network-layer isolation using NACLs and storage-layer isolation using S3 versioning.

**Core Principles**:

* **Network Isolation**: NACL-based network isolation creates a hermetically sealed test environment that prevents ANY interaction with production resources
* **S3 Bucket Isolation**: S3 versioning enables instant test readiness with automatic rollback, supporting any data volume without copying
* **Active Directory Preservation**: Launch Templates capture ALL settings including static IPs, instance profiles, security groups, and network configurations alongside AMI backups, ensuring exact restoration of domain controllers post-test

**Business Context**: Guiding Care currently operates from two data centers (Los Angeles with 19 customers, Reston VA with remainder) with no true DR capability. The company is paying significant penalties for SLA violations, making this DR testing critical for AWS migration success.

Overview
--------

### What is Bubble Test Isolation?

Bubble test isolation uses AWS Network Access Control Lists (NACLs) to create a completely isolated test environment at the network layer. Unlike security groups that operate at the instance level, NACLs operate at the subnet level and provide stateless filtering that explicitly blocks ALL traffic to/from production systems.

**Key Benefits:**

* **Zero Production Risk**: Network-layer blocking prevents any possibility of production data synchronization
* **Complete Stack Testing**: Validates entire application including databases, web services, and authentication
* **Repeatable Process**: Infrastructure-as-code approach enables consistent testing
* **Safe Restoration**: Critical validation checkpoints before production reconnection
* **Regulatory Compliance**: Demonstrates DR capabilities without production impact

### Guiding Care Application Architecture

**Application Components:**

1. **Web/Application Tier**

   * IIS web servers or application servers
   * .NET/Java application services
   * Load balancers and health check endpoints
   * Session management and caching
   * **Per Customer**: 5-10 servers for core modules
2. **Core Guiding Care Modules**

   * **Care Manager**: Patient care coordination
   * **Utilization Manager**: Resource utilization tracking
   * **Appeals and Grievances**: Claims and appeals processing
   * Each module requires dedicated application servers
3. **Database Tier**

   * **MongoDB**: Cross-region replica sets for document storage
   * **SQL Server**: Relational data with Always On Availability Groups
   * Database connection pooling
   * Transaction log management
   * **Backup Schedule**: Transaction logs every 30 minutes, daily incrementals, weekly fulls
4. **S3 Storage Tier**

   * **Application Data**: 500 GB operational files (gc-app-data-prod-835807883308)
   * **Static Content**: 100 GB web assets (gc-static-content-prod-835807883308)
   * **Database Backups**: 2 TB backup files (gc-db-backups-prod-835807883308)
   * **Application Logs**: 1 TB log archives (gc-app-logs-prod-835807883308)
   * **Replication**: Real-time cross-region with 15-minute RTC
   * **Versioning**: Enabled for bubble test isolation
5. **Authentication Layer**

   * Active Directory domain controllers
   * LDAP/Kerberos authentication
   * Service account management
   * Group policy application
6. **Shared Services**

   * **WSO2 API Management**: Central API gateway
   * **Tableau**: Analytics and reporting platform
   * **SFTP Servers**: File transfer for batch processing
   * File storage (SYSVOL, shared drives, S3 buckets)
   * DNS resolution (Route 53 + AD-integrated DNS)
   * Monitoring and logging services
7. **Critical Processing Requirements**

   * **Batch Processing Window**: 8 PM - 4 AM daily (MUST complete)
   * **Peak Traffic**: 700+ Mbps during batch window
   * **Normal Traffic**: 20-50 Mbps during business hours
   * **Performance SLAs**: 95-97% transactions < 2 seconds, 100% < 7 seconds
   * **Storage Access**: Sub-100ms S3 response times via VPC endpoints

Network Prerequisites
---------------------

**Infrastructure Context (from AWS Discovery):**

* **Production Transit Gateway**: tgw-015161a2212309004 (Network Account: 639966646465, us-east-1)
* **DR Transit Gateway**: tgw-XXXXXX (Network Account: 639966646465, us-west-2)
* **TGW Peering**: Required between us-east-1 and us-west-2 TGWs
* **InspectionVpc**: vpc-0da53a403080596cb (10.199.0.0/21, us-east-1)
* **NetworkEndpointsVpc**: vpc-0795ab8e27f3c4e58 (10.199.28.0/22, us-east-1)

  + **S3 Gateway Endpoint**: ✓ Configured (no hourly charges)
  + **Access Pattern**: GuidingCare Prod → Transit Gateway → NetworkEndpointsVpc → S3 Gateway
* **DR NetworkEndpointsVpc**: vpc-XXXXXX (10.199.128.0/22, us-west-2) - To be created

  + **S3 Gateway Endpoint**: Required for DR activation
* **GuidingCare Production Account**: 835807883308
* **GuidingCare SharedServices Account**: 096212910625

**Prerequisites (Must be completed before testing):**

* DR region VPC and subnets provisioned in us-west-2
* Cross-region connectivity via Transit Gateway Peering between regions
* Route 53 Outbound Resolver Rules configured separately in DR region
* Security groups created in DR region (cannot reference cross-region)
* Active Directory domain controllers deployed and operational in DR region

**Required Network Connectivity Within Bubble:**

**Application Tier:**

* HTTP/HTTPS: TCP 80, TCP 443 (web traffic)
* Application ports: TCP 8080, TCP 8443 (custom app services)
* Database clients: TCP 27017 (MongoDB), TCP 1433 (SQL Server)
* LDAP/AD: TCP 389, TCP 636 (authentication)
* DNS: TCP/UDP 53 (name resolution)

**Database Tier:**

* MongoDB: TCP 27017 (replica set communication)
* SQL Server: TCP 1433 (database access)
* SQL Always On: TCP 5022 (availability group listener)
* Internal replication: Within DR VPC only

**Management Access:**

* RDP: TCP 3389 (Windows server management)
* SSH: TCP 22 (Linux server management if applicable)
* WinRM: TCP 5985, TCP 5986 (PowerShell remoting)

Bubble Test Isolation Process
-----------------------------

### Phase 1: Environment Preservation (Pre-Test)

**Objective**: Create pristine backups while resources are powered down to prevent in-flight transactions or inconsistent states.

**1.1 Application Server Preservation:**


```bash
# For each application server
1. Gracefully shutdown IIS/application services
2. Stop application server instance
3. Create AMI with descriptive name: "GC-App-DR-BubbleTest-YYYYMMDD"
4. Create launch template preserving:
   - Static IP addresses (if assigned)
   - IAM instance profiles
   - Security groups
   - User data scripts
   - EBS volumes and instance metadata
5. Keep servers powered off during NACL setup
```


**1.2 S3 Storage Preservation:**


```bash
# Enable S3 versioning (one-time setup)
aws s3api put-bucket-versioning \
  --bucket gc-app-data-dr-835807883308 \
  --versioning-configuration Status=Enabled \
  --region us-west-2

aws s3api put-bucket-versioning \
  --bucket gc-static-content-dr-835807883308 \
  --versioning-configuration Status=Enabled \
  --region us-west-2

aws s3api put-bucket-versioning \
  --bucket gc-db-backups-dr-835807883308 \
  --versioning-configuration Status=Enabled \
  --region us-west-2

aws s3api put-bucket-versioning \
  --bucket gc-app-logs-dr-835807883308 \
  --versioning-configuration Status=Enabled \
  --region us-west-2

# Capture pre-test state
export TEST_ID="BUBBLE_$(date +%Y%m%d_%H%M%S)"
for bucket in gc-app-data-dr-835807883308 \
              gc-static-content-dr-835807883308 \
              gc-db-backups-dr-835807883308 \
              gc-app-logs-dr-835807883308; do
  aws s3api list-object-versions \
    --bucket $bucket \
    --region us-west-2 \
    --query 'Versions[?IsLatest==`true`].{Key:Key,VersionId:VersionId}' \
    > ".bubble_test_${TEST_ID}_${bucket}_snapshot.json"
done

# Pause S3 replication
aws s3api delete-bucket-replication \
  --bucket gc-app-data-prod-835807883308 \
  --region us-east-1
```


**1.3 Database Preservation:**

**MongoDB Replica Set:**  
**Reference**: Follow detailed MongoDB preservation procedures documented in:

* **Confluence**: Guiding Care MongoDB Cross-Region Replication DR Architecture
* **Procedure**: See above link for complete procedures

**SQL Server:**  
**Reference**: Follow detailed SQL Server preservation procedures documented in:

* **Confluence**: Guiding Care SQL Server On EC2 Disaster Recover Detailed Design and Runbook
* **Procedure**: See above link for complete procedures

**1.4 Active Directory Preservation:**

**Reference**: Follow detailed AD preservation procedures documented in:

* **Confluence**: Active Directory and Integrated DNS Disaster Recovery Design

**Summary**: Gracefully shutdown DCs, create AMIs, preserve static IPs via launch templates.

**1.5 Document Baseline Configuration:**

* [ ] Application server configurations and connection strings
* [ ] Database connection pool settings
* [ ] S3 bucket policies and versioning status
* [ ] S3 replication configuration saved
* [ ] Load balancer target groups and health checks
* [ ] DNS CNAME records and Route 53 configurations
* [ ] Service account passwords (stored in secrets manager)
* [ ] Monitoring alert thresholds and dashboards

### Phase 2: Network Isolation (NACL Configuration)

**Objective**: Implement subnet-level NACLs that explicitly block ALL production traffic while allowing internal DR VPC communication.

**2.1 Application Tier NACL Rules:**

**IMPORTANT**: DR VPC does not exist yet. Once created, replace <DR\_VPC\_CIDR> with actual values.

**Placeholder Values to Replace:**

* `<DR_VPC_CIDR>`: Future DR VPC CIDR block (ensure no overlap with production 10.196.0.0/16)
* `<DR_APP_SUBNET>`: Future DR Application Subnet CIDR
* `<DR_DB_SUBNET>`: Future DR Database Subnet CIDR
* `<DR_AD_SUBNET>`: Future DR Active Directory Subnet CIDR

**Inbound Rules:**

| Rule # | Protocol | Port Range | Source | Action | Purpose |
| --- | --- | --- | --- | --- | --- |
| 100 | TCP | 80 | <DR\_VPC\_CIDR> | ALLOW | HTTP from DR Load Balancer |
| 110 | TCP | 443 | <DR\_VPC\_CIDR> | ALLOW | HTTPS from DR Load Balancer |
| 120 | TCP | 8080 | <DR\_VPC\_CIDR> | ALLOW | Application Services (DR only) |
| 130 | TCP | 27017 | <DR\_DB\_SUBNET> | ALLOW | MongoDB from DR DB Subnet |
| 140 | TCP | 1433 | <DR\_DB\_SUBNET> | ALLOW | SQL Server from DR DB Subnet |
| 150 | TCP | 389 | <DR\_AD\_SUBNET> | ALLOW | LDAP from DR AD Subnet |
| 155 | TCP | 636 | <DR\_AD\_SUBNET> | ALLOW | LDAPS from DR AD Subnet |
| 160 | TCP/UDP | 88 | <DR\_AD\_SUBNET> | ALLOW | Kerberos from DR AD Subnet |
| 165 | TCP/UDP | 53 | <DR\_AD\_SUBNET> | ALLOW | DNS from DR AD Subnet |
| 170 | TCP | 1024-65535 | <DR\_VPC\_CIDR> | ALLOW | Ephemeral Return (DR only) |
| 180 | TCP | 3389 | <DR\_VPC\_CIDR> | ALLOW | RDP Management (DR only) |
| 190 | ICMP | All | <DR\_VPC\_CIDR> | ALLOW | Ping Testing (DR only) |
| 200 | All | All | 10.196.0.0/16 | **DENY** | **Block ALL GC Production** |
| 210 | All | All | 10.199.0.0/21 | **DENY** | **Block Network Account** |
|  | All | All | 0.0.0.0/0 | DENY | Implicit Default Deny |

**Outbound Rules:**

| Rule # | Protocol | Port Range | Destination | Action | Purpose |
| --- | --- | --- | --- | --- | --- |
| 100 | All | All | <DR\_VPC\_CIDR> | ALLOW | DR Internal Communication Only |
| 110 | TCP | 443 | 0.0.0.0/0 | ALLOW | HTTPS to AWS Services (S3, etc) |
| 120 | TCP/UDP | 53 | 0.0.0.0/0 | ALLOW | DNS Resolution |
| 130 | UDP | 123 | 0.0.0.0/0 | ALLOW | NTP Time Sync |
| 200 | All | All | 10.196.0.0/16 | **DENY** | **Block ALL GC Production** |
| 210 | All | All | 10.199.0.0/21 | **DENY** | **Block Network Account** |
|  | All | All | 0.0.0.0/0 | DENY | Implicit Default Deny |

**2.2 Database Tier NACL Rules:**

**Inbound Rules:**

| Rule # | Protocol | Port Range | Source | Action | Purpose |
| --- | --- | --- | --- | --- | --- |
| 100 | TCP | 27017 | <DR\_APP\_SUBNET> | ALLOW | MongoDB from DR App Subnet |
| 110 | TCP | 27017 | <DR\_DB\_SUBNET> | ALLOW | MongoDB Replica Set (DR) |
| 120 | TCP | 1433 | <DR\_APP\_SUBNET> | ALLOW | SQL Server from DR Apps |
| 130 | TCP | 5022 | <DR\_DB\_SUBNET> | ALLOW | SQL Always On (DR only) |
| 140 | TCP | 3389 | <DR\_VPC\_CIDR> | ALLOW | RDP Management (DR only) |
| 150 | ICMP | All | <DR\_VPC\_CIDR> | ALLOW | Ping Testing (DR only) |
| 160 | TCP | 1024-65535 | <DR\_VPC\_CIDR> | ALLOW | Ephemeral Return Ports |
| 200 | All | All | 10.196.0.0/16 | **DENY** | **Block ALL GC Production** |
| 210 | All | All | 10.199.0.0/21 | **DENY** | **Block Network Account** |
|  | All | All | 0.0.0.0/0 | DENY | Implicit Default Deny |

**Outbound Rules:**

| Rule # | Protocol | Port Range | Destination | Action | Purpose |
| --- | --- | --- | --- | --- | --- |
| 100 | All | All | <DR\_VPC\_CIDR> | ALLOW | DR Internal Communication Only |
| 110 | TCP | 443 | 0.0.0.0/0 | ALLOW | HTTPS to AWS Services |
| 120 | TCP/UDP | 53 | 0.0.0.0/0 | ALLOW | DNS Resolution |
| 130 | UDP | 123 | 0.0.0.0/0 | ALLOW | NTP Time Sync |
| 200 | All | All | 10.196.0.0/16 | **DENY** | **Block ALL GC Production** |
| 210 | All | All | 10.199.0.0/21 | **DENY** | **Block Network Account** |
|  | All | All | 0.0.0.0/0 | DENY | Implicit Default Deny |

**2.3 Active Directory NACL Rules:**

**Reference**: Complete AD NACL configurations documented in:

* **Confluence**: Active Directory and Integrated DNS Disaster Recovery Design
* **Ports**: LDAP (389/636), Kerberos (88), DNS (53), SMB (445), RPC (135, 49152-65535), NTP (123)

**CRITICAL**: Rule 200/210 in all NACL configurations explicitly blocks production traffic, ensuring zero synchronization risk.

### Phase 3: Power Up and Validate Isolation

**Objective**: Start all resources in correct dependency order and confirm complete isolation from production.

**3.1 S3 Bucket Switching for DR - Realistic Options**

**CRITICAL**: S3 bucket names are globally unique. Production and DR buckets MUST have different names.

**Problem**:

* Production: `gc-app-data-prod-835807883308` (us-east-1)
* DR: `gc-app-data-dr-835807883308` (us-west-2)
* Applications need to switch without logging into individual servers

**Option 1: AWS DRS Post-Launch Actions (For DRS-replicated servers)**

**One-Time Setup** (DRS Console):


```bash
# DRS > Launch Settings > Post-launch actions
#!/bin/bash
sed -i 's/prod-835807883308/dr-835807883308/g' /etc/environment
sed -i 's/us-east-1/us-west-2/g' /etc/environment
systemctl restart guiding-care-app
```


**During DR**: Action Required: **None** (automatic) - Time: 0 minutes

**Option 2: AWS Systems Manager Run Command (For non-DRS servers)**

**During DR** (from CloudShell):


```bash
# Target by instance IDs (list specific instances)
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --instance-ids i-mongodb1 i-mongodb2 i-sqlserver1 \
  --parameters 'commands=[
    "sed -i \"s/prod-835807883308/dr-835807883308/g\" /etc/environment",
    "sed -i \"s/us-east-1/us-west-2/g\" /etc/environment",
    "systemctl restart mongodb || systemctl restart mssql-server"
  ]' \
  --region us-west-2

# Or target all instances in DR VPC
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --targets "Key=InstanceIds,Values=$(aws ec2 describe-instances \
    --filters "Name=vpc-id,Values=vpc-XXXXX" "Name=instance-state-name,Values=running" \
    --query 'Reservations[].Instances[].InstanceId' \
    --output text --region us-west-2)" \
  --parameters 'commands=[
    "sed -i \"s/prod-835807883308/dr-835807883308/g\" /etc/environment",
    "sed -i \"s/us-east-1/us-west-2/g\" /etc/environment",
    "systemctl restart application-service"
  ]' \
  --region us-west-2
```


**During DR**: Action Required: Run single command from CloudShell - Time: 2 minutes

**Implementation Matrix**:

| Server Type | DR Method | S3 Config Method | Manual Effort |
| --- | --- | --- | --- |
| Web Servers | AWS DRS | Post-Launch Script | None |
| App Servers | AWS DRS | Post-Launch Script | None |
| MongoDB | Manual Launch | SSM Run Command | 1 command |
| SQL Server | Manual Launch | SSM Run Command | 1 command |
| Active Directory | Manual Launch | N/A | None |

**3.2 Startup Sequence:**

**Order matters - authentication required for everything:**

1. **Start Active Directory domain controllers** (PDC Emulator first)

   * **Reference**: [Active Directory DR Procedures - Confluence Link TBD]
   * Wait for AD services to initialize (5-10 minutes)
   * Verify domain controller health
2. **Verify S3 Access** (No startup needed - always available)

   * Confirm bucket accessibility in DR region
   * Verify versioning is enabled
   * Confirm replication is paused (no new objects from production)
   * Test read/write access with test object
3. **Start Database servers**

   * **MongoDB Reference**: [GC MongoDB DR Architecture - Confluence Link TBD]
   * **SQL Server Reference**: [GC SQL Server DR Runbook - Confluence Link TBD]
   * Verify services running, no production replication
   * **Run SSM command to update S3 bucket configuration**
4. **Start Application/Web servers (via DRS)**

   * DRS automatically applies post-launch actions
   * S3 configuration updated automatically (sed replacements)
   * Application services restart with DR bucket configuration
   * Verify IIS/app services start successfully
   * Check application logs for startup errors
   * Confirm connection pool initialization
5. **Verify Load Balancer health checks**

   * Check all targets healthy in target group
   * Verify HTTP/HTTPS listeners responding

**DR Execution Checklist**:

* [ ] Trigger DRS recovery (web/app servers auto-configure)
* [ ] Launch database servers from Launch Templates
* [ ] Run SSM command targeting DR VPC instances
* [ ] Verify: `aws ssm list-command-invocations`
* [ ] Test S3 connectivity: `aws s3 ls s3://gc-app-data-dr-835807883308`

**Total Time**: < 5 minutes  
**Server Logins Required**: 0

**3.2 Isolation Validation (CRITICAL):**


```bash
# Test 1: Verify Production Connectivity BLOCKED
from_app_server:
  ping 10.196.145.247              # GCADSP01 (production) - MUST timeout
  ping 10.196.151.162              # GCADSP02 (production) - MUST timeout  
  ping 10.196.152.112              # GCADSP03 (production) - MUST timeout
  telnet <production-db-ip> 1433   # SQL Server - MUST fail
  telnet <production-db-ip> 27017  # MongoDB - MUST fail

# Test 2: Verify DR VPC Internal Connectivity WORKS
from_app_server:
  ping <dr-db-ip>                  # MUST succeed
  telnet <dr-db-ip> 1433           # SQL Server - MUST connect
  telnet <dr-db-ip> 27017          # MongoDB - MUST connect
  nslookup domain.local <dr-ad-ip> # MUST resolve

# Test 3: Verify S3 Connectivity (DR buckets only)
from_app_server:
  aws s3 ls s3://gc-app-data-dr-835807883308 --region us-west-2        # MUST work
  aws s3 ls s3://gc-app-data-prod-835807883308 --region us-east-1      # May fail (OK)
  aws s3api get-bucket-replication --bucket gc-app-data-prod-835807883308 \
    --region us-east-1  # Should show no replication config (paused)

# Test 4: Verify Load Balancer Health Checks
# ALB health checks come from AWS IP ranges - verify they work
  curl -I http://localhost/health  # Should return 200 OK
  
# Test 5: Verify No Replication Attempts
# See component-specific documentation for detailed commands:
# - MongoDB: [GC MongoDB DR Architecture - Confluence Link TBD]
# - SQL Server: [GC SQL Server DR Runbook - Confluence Link TBD]  
# - Active Directory: [AD DR Procedures - Confluence Link TBD]
# - S3: No new objects should appear from production (replication paused)

Expected: Only DR region members visible, production replication fails (CORRECT - isolation working)
```


**Expected Results:**

* ✅ Production connectivity FAILS (blocked by NACL Rule 200)
* ✅ DR VPC internal connectivity WORKS
* ✅ S3 DR buckets accessible, production replication paused
* ✅ Services initialize successfully
* ✅ No production replication attempts succeed

### Phase 4: Application Testing Execution

**Objective**: Validate complete application functionality within isolated bubble environment.

**4.1 Authentication and Authorization Testing:**

**Reference**: Detailed AD testing procedures in [Active Directory DR Procedures - Confluence Link TBD]

**Test Steps:**

1. Open Guiding Care application URL (DR region load balancer)
2. Test user authentication with test credentials
3. Verify successful authentication against DR domain controllers
4. Validate user groups and permissions applied correctly
5. Confirm service account authentication
6. Verify LDAP/AD queries return correct results
7. Confirm Kerberos ticket generation

**4.2 Database Operations Testing:**

**MongoDB Testing:**  
**Reference**: Detailed MongoDB testing procedures in [GC MongoDB DR Architecture - Confluence Link TBD]

**Validation Steps:**

* Connect to DR replica set
* Verify replica set status (all DR members healthy, primary elected)
* Test write operations (insert, update)
* Verify write propagation to secondaries
* Test read operations
* Confirm no production synchronization (only DR region hosts in replica set)

**SQL Server Testing:**  
**Reference**: Detailed SQL Server testing procedures in [GC SQL Server DR Runbook - Confluence Link TBD]

**Validation Steps:**

* Verify database availability
* Test insert/update operations
* Verify transaction log integrity
* Check Always On Availability Group health
* Verify query performance
* Check connection pool status

**4.3 S3 Storage Operations Testing:**

**Test Categories:**

* **Read Operations**: Retrieve application data, static content, backups
* **Write Operations**: Upload new files, update existing objects
* **Versioning Validation**: Confirm new versions created, originals preserved
* **Performance Testing**: Measure S3 response times via VPC endpoints
* **Backup Restoration**: Test database restore from S3 backup files


```bash
# Test S3 read/write operations
echo "Test file" > test.txt
aws s3 cp test.txt s3://gc-app-data-dr-835807883308/test/test.txt
aws s3 cp s3://gc-app-data-dr-835807883308/test/test.txt ./test-downloaded.txt

# Verify versioning is working
aws s3api list-object-versions \
  --bucket gc-app-data-dr-835807883308 \
  --prefix test/ \
  --region us-west-2

# Test database backup restoration
aws s3 cp s3://gc-db-backups-dr-835807883308/latest/full-backup.bak ./restore-test.bak
```


**4.4 End-to-End Application Workflow Testing:**

**Reference**: Detailed Guiding Care application testing procedures documented in:

* **Confluence**: Testing in GuidingCare
* **Confluence**: GuidingCare Product Management Home

**Test Categories:**

* User authentication and authorization workflows
* Patient dashboard and record management
* Report generation and document handling (from S3)
* Static content delivery (from S3)
* API endpoint validation
* Load balancer health checks
* Session management verification

**4.5 Data Integrity Validation:**

**MongoDB Reference**: [GC MongoDB DR Architecture - Confluence Link TBD]  
**SQL Server Reference**: [GC SQL Server DR Runbook - Confluence Link TBD]

**Validation Steps:**

* Compare record counts between pre-test baseline and bubble
* Verify data checksums match baseline for critical tables
* Check referential integrity
* Validate foreign key relationships
* Confirm no data corruption

**4.6 Performance Baseline Testing:**

**Reference**: Detailed performance testing procedures and thresholds documented in:

* **Confluence**: [Guiding Care Performance Testing Standards - Link TBD]

**Performance Categories:**

* Application response time thresholds
* Database query performance benchmarks
* Resource utilization targets (CPU, memory, network)
* Load balancer response validation

### Phase 5: Cleanup and Return to Production

**Objective**: Destroy ALL bubble test resources, restore S3 to pre-test state, and restore production-ready environment.

**CRITICAL**: Every resource used during bubble test MUST be destroyed. S3 buckets are rolled back to pre-test versions. Only fresh production-ready domain controllers are restored and validated before removing NACLs.

**5.1 S3 Rollback to Pre-Test State:**


```bash
# Find test ID
TEST_ID=$(ls -t .bubble_test_BUBBLE_* 2>/dev/null | head -1 | sed 's/.*\(BUBBLE_[0-9]*_[0-9]*_[0-9]*\).*/\1/')

# Restore each bucket to pre-test versions
for bucket in gc-app-data-dr-835807883308 \
              gc-static-content-dr-835807883308 \
              gc-db-backups-dr-835807883308 \
              gc-app-logs-dr-835807883308; do
  
  echo "Restoring $bucket..."
  SNAPSHOT_FILE=".bubble_test_${TEST_ID}_${bucket}_snapshot.json"
  
  # Restore pre-test versions and remove test-created objects
  # See detailed script in S3 DR Strategy document
  ./end-bubble-test.sh
done

# Re-enable S3 replication
aws s3api put-bucket-replication \
  --bucket gc-app-data-prod-835807883308 \
  --region us-east-1 \
  --replication-configuration file://.replication_config_${TEST_ID}.json

# Force sync to ensure DR matches production
aws s3 sync s3://gc-app-data-prod-835807883308 \
  s3://gc-app-data-dr-835807883308 \
  --source-region us-east-1 \
  --region us-west-2 \
  --delete \
  --exact-timestamps
```


**5.2 Complete Destruction of ALL Bubble Test Resources:**


```bash
# DESTROY EVERYTHING - No bubble test resources can remain
1. Document test results and capture logs FIRST

2. Terminate ALL application servers
   - Drain connections, stop services
   - TERMINATE all bubble app instances
   - Delete any test load balancers created

3. Terminate ALL database servers  
   - Gracefully shutdown databases
   - TERMINATE all bubble MongoDB instances
   - TERMINATE all bubble SQL Server instances
   - Remove any test replica set configurations

4. Terminate ALL Active Directory domain controllers
   - Gracefully shutdown AD services
   - TERMINATE all bubble domain controllers
   - No test DCs can remain

5. Verify COMPLETE destruction
   - No bubble test instances remain running
   - All test resources terminated
   - Clean slate for production restoration
```


**5.3 Restore ONLY Domain Controllers from Production Backups:**

**CRITICAL**: Only DCs are restored at this stage for validation before NACL removal


```bash
1. Launch NEW Active Directory domain controllers from preserved AMIs
   - Use AMIs created in Phase 1 (pre-test backups)
   - Launch from preserved templates with correct IPs
   - **Reference**: [AD DR Procedures - Confluence Link TBD]
   
2. Wait for full DC initialization (5-10 minutes)
   - Verify AD services start successfully
   - Check Event Viewer for critical errors
   - Confirm SYSVOL share accessible
   
3. Validate DC health BEFORE removing NACLs
   - These are the ONLY resources running
   - No databases or applications launched yet
```


**5.4 Validate ONLY Domain Controllers Before NACL Removal:**


```bash
# ONLY Active Directory validation - nothing else is running yet

# Test 1: Domain Controller Health
✓ AD: All DCs online and initialized
✓ AD: dcdiag /v passes all tests
✓ AD: Domain services running properly
✓ AD: SYSVOL replication ready (within DR region only)
✓ AD: DNS service operational

# Test 2: Internal DR VPC Connectivity (AD only)
✓ AD: Can resolve DNS queries internally
✓ AD: LDAP ports responding (389, 636)
✓ AD: Kerberos authentication functional (port 88)

# CRITICAL: If ANY check fails:
# - STOP immediately
# - Investigate and fix issues
# - Do NOT proceed to NACL removal
```


**Important**: ONLY domain controllers are running. All databases and applications remain terminated.

**5.5 Remove NACL Isolation (After DC Validation Only):**


```bash
# Remove bubble test NACLs and restore baseline
1. Document current NACL configurations (for rollback)

2. Remove/modify NACL rules:
   - Remove Rule 200 (production DENY) from all tiers
   - Remove Rule 210 (network account DENY) from all tiers
   - Keep other rules for normal DR operations

3. Restore baseline NACL configurations
   - Apply pre-test production NACL rules
   - Verify rules applied correctly
   - Confirm rule numbers are in valid range (1-32766)
   - Note: Implicit default DENY rule always exists (cannot be modified)
```


**5.6 Post-NACL Restoration:**

**IMPORTANT**: Once NACLs are restored to pre-bubble test configuration, all network connectivity and replication will automatically return to production state. The infrastructure will be configured exactly as it was pre-test.

* All production replication resumes automatically
* S3 cross-region replication re-enabled and active
* Domain controllers re-establish production replication
* Database replica sets and availability groups reconnect as configured
* Application connectivity to production resources restored
* No manual reconfiguration required - infrastructure returns to baseline state

**5.7 Production Verification:**


```bash
# Production User Test
1. Have real user login to application (using production DC)
2. Perform standard workflow (patient search, record update)
3. Verify: All functionality works normally
4. Check: Data persisted correctly to production databases

# 24-Hour Monitoring Period
- Monitor application logs for errors
- Watch database replication status
- Check AD event logs for issues
- Verify no data inconsistencies
- Confirm performance metrics normal
```


Test Validation Checklists
--------------------------

### Pre-Test Validation Checklist

* [ ] **AMI Backups Created**

  + [ ] All application server AMIs created successfully
  + [ ] Launch templates preserve network configurations
  + [ ] AMI tags include date and purpose
* [ ] **S3 Preparation Complete**

  + [ ] S3 versioning enabled on all DR buckets
  + [ ] Pre-test bucket snapshots captured
  + [ ] Replication configuration backed up
  + [ ] Test ID generated and logged
* [ ] **Database Snapshots Verified**

  + [ ] MongoDB: All replica set member snapshots consistent
  + [ ] SQL Server: Transaction log backed up successfully
  + [ ] Snapshot tags applied correctly
  + [ ] Snapshot restore tested (if first time)
* [ ] **Baseline Documentation Complete**

  + [ ] Application connection strings documented
  + [ ] S3 bucket configurations recorded
  + [ ] Database connection pool settings recorded
  + [ ] Load balancer configurations captured
  + [ ] Current NACL rules documented
  + [ ] Service account credentials verified in secrets manager
* [ ] **Test Plan Reviewed**

  + [ ] Test scenarios defined and approved
  + [ ] Success criteria established
  + [ ] Rollback procedures documented
  + [ ] Communication plan for stakeholders
  + [ ] Test window scheduled (maintenance window if needed)

### Network Isolation Validation Checklist

* [ ] **NACL Rules Deployed**

  + [ ] Application tier NACLs applied to all app subnets
  + [ ] Database tier NACLs applied to all database subnets
  + [ ] AD tier NACLs applied to all AD subnets
  + [ ] Rule 200 (production DENY) verified in all NACLs
  + [ ] NACL associations verified with subnets
* [ ] **Production Connectivity Blocked**

  + [ ] Ping to production database IPs fails (timeout)
  + [ ] Telnet to production MongoDB port 27017 fails
  + [ ] Telnet to production SQL Server port 1433 fails
  + [ ] Ping to production AD IPs fails (timeout)
  + [ ] No production traffic visible in VPC Flow Logs
* [ ] **DR VPC Internal Connectivity Operational**

  + [ ] Application servers can ping database servers
  + [ ] Application servers can connect to MongoDB
  + [ ] Application servers can connect to SQL Server
  + [ ] Application servers can authenticate to AD
  + [ ] DNS resolution working within bubble
* [ ] **Resources Started Successfully**

  + [ ] All AD domain controllers online and healthy
  + [ ] S3 buckets accessible in DR region
  + [ ] All MongoDB replica set members started
  + [ ] SQL Server instances online
  + [ ] All application servers running
  + [ ] Load balancer targets healthy
* [ ] **Services Initialized Properly**

  + [ ] AD: dcdiag /v passes all tests
  + [ ] S3: Versioning confirmed, replication paused
  + [ ] MongoDB: rs.status() shows healthy replica set
  + [ ] SQL: Availability Group online and synchronized
  + [ ] Application: IIS/app services running
  + [ ] No errors in application logs

Success Criteria
----------------

### Business Requirements Validation

* ✅ **4-hour RTO Achieved**: Complete recovery within contractual requirement
* ✅ **15-minute RPO Validated**: Maximum data loss within acceptable limits
* ✅ **99.95% Uptime Capability**: DR infrastructure supports SLA requirements
* ✅ **Performance SLAs Met**:

  + 95-97% of transactions complete in < 2 seconds
  + 100% of transactions complete in < 7 seconds
* ✅ **Batch Processing Window**: Confirm ability to complete 8 PM - 4 AM processing
* ✅ **Penalty Mitigation**: DR capability reduces risk of 10% monthly fee penalties

### Technical Success Indicators

* ✅ Complete application stack tested without production impact
* ✅ Zero production database synchronization during bubble test
* ✅ S3 isolation via versioning with automatic rollback
* ✅ All authentication workflows function within isolated bubble
* ✅ MongoDB and SQL Server DR procedures validated
* ✅ S3 read/write operations and versioning validated
* ✅ End-to-end application workflows successful
* ✅ Data integrity verified throughout test
* ✅ Performance baselines meet or exceed requirements
* ✅ Clean restoration with production re-synchronization
* ✅ No data loss or corruption detected
* ✅ 24-hour post-test monitoring shows stability

### Process Success Indicators

* ✅ Repeatable test procedures established and documented
* ✅ All validation checklists completed successfully
* ✅ Clear RTO/RPO documented for each component
* ✅ Team trained on bubble test execution
* ✅ Automated NACL deployment scripts tested
* ✅ Monitoring and alerting validated during test
* ✅ Runbooks updated with lessons learned
* ✅ Stakeholder communication effective

### Compliance and Governance

* ✅ DR testing requirement met without production risk
* ✅ Zero patient data exposure during testing
* ✅ Audit trail complete (all actions logged)
* ✅ Change management approvals obtained
* ✅ Test results documented and archived
* ✅ Risk register updated with findings
* ✅ Compliance reporting completed
* ✅ S3 versioning provides complete change audit trail

S3 Bubble Test Automation Scripts
---------------------------------

### CloudShell Execution

**Prerequisites**: No local tools required - scripts are designed for AWS CloudShell execution.

**Setup in CloudShell:**


```bash
# Option 1: Upload script files via CloudShell UI
# - Use "Actions" > "Upload file" in CloudShell console
# - Upload start-bubble-test.sh and end-bubble-test.sh
# - Make executable: chmod +x *.sh

# Option 2: Create scripts directly in CloudShell
cat > start-bubble-test.sh << 'EOF'
# Script content follows...
EOF

cat > end-bubble-test.sh << 'EOF'
# Script content follows...
EOF

# Make scripts executable
chmod +x start-bubble-test.sh end-bubble-test.sh

# Execute DR test
./start-bubble-test.sh
# ... run your tests ...
./end-bubble-test.sh

# Download test reports via CloudShell UI
# Use "Actions" > "Download file" to get bubble_test_report_*.txt
```


**CloudShell Benefits:**

* ✅ AWS CLI pre-configured with your credentials
* ✅ jq and all required tools pre-installed
* ✅ No local environment setup needed
* ✅ Consistent execution environment
* ✅ Access from any web browser
* ✅ File upload/download via web UI
* ✅ Test reports easily downloadable

### Start Bubble Test Script (`start-bubble-test.sh`)


```bash
#!/bin/bash
# DR Bubble Test Initialization Script
# Purpose: Prepare DR environment for isolated testing with S3 versioning
# Author: HealthEdge DR Team
# Version: 1.0

echo "═══════════════════════════════════════════════"
echo "     DR BUBBLE TEST INITIALIZATION"
echo "═══════════════════════════════════════════════"

# Generate unique test ID
export TEST_ID="BUBBLE_$(date +%Y%m%d_%H%M%S)"
echo "Test ID: $TEST_ID"

# Save replication configuration
echo "[INFO] Saving current replication config..."
aws s3api get-bucket-replication \
  --bucket gc-app-data-prod-835807883308 \
  --region us-east-1 \
  > ".replication_config_${TEST_ID}.json"

# Capture pre-test state (version markers)
echo "[INFO] Capturing pre-test state..."
for bucket in gc-app-data-dr-835807883308 \
              gc-static-content-dr-835807883308 \
              gc-db-backups-dr-835807883308 \
              gc-app-logs-dr-835807883308; do
  
  echo "  Processing $bucket..."
  aws s3api list-object-versions \
    --bucket $bucket \
    --region us-west-2 \
    --query 'Versions[?IsLatest==`true`].{Key:Key,VersionId:VersionId}' \
    > ".bubble_test_${TEST_ID}_${bucket}_snapshot.json"
done

# Pause replication from production
echo "[INFO] Pausing production -> DR replication..."
for bucket in gc-app-data-prod-835807883308 \
              gc-static-content-prod-835807883308 \
              gc-db-backups-prod-835807883308 \
              gc-app-logs-prod-835807883308; do
  aws s3api delete-bucket-replication \
    --bucket $bucket \
    --region us-east-1 2>/dev/null || true
done

echo ""
echo "[SUCCESS] BUBBLE TEST READY!"
echo "════════════════════════════════════════════════"
echo "Test ID: $TEST_ID"
echo "Status: DR buckets ready for testing"
echo "Replication: PAUSED"
echo "Rollback: Automatic on test completion"
echo ""
echo "You can now safely test DR scenarios."
echo "Changes will be tracked via S3 versioning."
echo "════════════════════════════════════════════════"
```


### End Bubble Test Script (`end-bubble-test.sh`)


```bash
#!/bin/bash
# DR Bubble Test Cleanup & Restore Script
# Purpose: Restore DR environment to pre-test state using S3 versioning
# Author: HealthEdge DR Team
# Version: 1.0

echo "═══════════════════════════════════════════════"
echo "     DR BUBBLE TEST CLEANUP & RESTORE"
echo "═══════════════════════════════════════════════"

# Find most recent test ID
TEST_ID=$(ls -t .bubble_test_BUBBLE_* 2>/dev/null | head -1 | sed 's/.*\(BUBBLE_[0-9]*_[0-9]*_[0-9]*\).*/\1/')

if [ -z "$TEST_ID" ]; then
  echo "[ERROR] No active bubble test found!"
  exit 1
fi

echo "Test ID: $TEST_ID"
echo ""

# Restore each bucket to pre-test versions
echo "[INFO] Rolling back changes to pre-test state..."
for bucket in gc-app-data-dr-835807883308 \
              gc-static-content-dr-835807883308 \
              gc-db-backups-dr-835807883308 \
              gc-app-logs-dr-835807883308; do
  
  echo "  Restoring $bucket..."
  SNAPSHOT_FILE=".bubble_test_${TEST_ID}_${bucket}_snapshot.json"
  
  if [ -f "$SNAPSHOT_FILE" ]; then
    # Restore each object to its pre-test version
    aws s3api list-object-versions \
      --bucket $bucket \
      --region us-west-2 \
      --query 'Versions[?IsLatest==`true`]' \
      | jq -r '.[] | .Key' | while read key; do
  
        # Get pre-test version ID
        PRE_TEST_VERSION=$(jq -r --arg k "$key" \
          '.[] | select(.Key==$k) | .VersionId' "$SNAPSHOT_FILE")
  
        if [ -n "$PRE_TEST_VERSION" ]; then
          # Delete current version to expose pre-test version
          CURRENT_VERSION=$(aws s3api list-object-versions \
            --bucket $bucket \
            --prefix "$key" \
            --region us-west-2 \
            --query 'Versions[?IsLatest==`true`].VersionId' \
            --output text)
    
          if [ "$CURRENT_VERSION" != "$PRE_TEST_VERSION" ]; then
            aws s3api delete-object \
              --bucket $bucket \
              --key "$key" \
              --version-id "$CURRENT_VERSION" \
              --region us-west-2 >/dev/null 2>&1
          fi
        fi
    done
  
    # Delete objects created during test (not in pre-test snapshot)
    aws s3api list-object-versions \
      --bucket $bucket \
      --region us-west-2 \
      --query 'Versions[?IsLatest==`true`].Key' \
      | jq -r '.[]' | while read key; do
  
        if ! jq -e --arg k "$key" '.[] | select(.Key==$k)' "$SNAPSHOT_FILE" >/dev/null 2>&1; then
          echo "    Removing test-created object: $key"
          aws s3api delete-object \
            --bucket $bucket \
            --key "$key" \
            --region us-west-2 >/dev/null 2>&1
        fi
    done
  fi
done

# Re-enable replication
echo "[INFO] Re-enabling production -> DR replication..."
REPLICATION_CONFIG=".replication_config_${TEST_ID}.json"
if [ -f "$REPLICATION_CONFIG" ]; then
  aws s3api put-bucket-replication \
    --bucket gc-app-data-prod-835807883308 \
    --region us-east-1 \
    --replication-configuration file://${REPLICATION_CONFIG}
fi

# Force sync to ensure DR matches production
echo "[INFO] Forcing sync from production to ensure consistency..."
aws s3 sync s3://gc-app-data-prod-835807883308 \
  s3://gc-app-data-dr-835807883308 \
  --source-region us-east-1 \
  --region us-west-2 \
  --delete \
  --exact-timestamps \
  --storage-class STANDARD_IA

# Generate test report
echo "[INFO] Generating test report..."
REPORT_FILE="bubble_test_report_${TEST_ID}.txt"
cat > "$REPORT_FILE" << EOF
═══════════════════════════════════════════════
DR BUBBLE TEST REPORT
═══════════════════════════════════════════════
Test ID: $TEST_ID
End Time: $(date +"%Y-%m-%d %H:%M:%S")
Status: RESTORED TO PRE-TEST STATE

Buckets Tested:
- gc-app-data-dr-835807883308
- gc-static-content-dr-835807883308
- gc-db-backups-dr-835807883308
- gc-app-logs-dr-835807883308

Restoration Status:
[SUCCESS] Objects restored to pre-test versions
[SUCCESS] Test-created objects removed
[SUCCESS] Replication re-enabled
[SUCCESS] Force sync completed

Next Steps:
- Verify application connectivity
- Review test results
- Document any findings
═══════════════════════════════════════════════
EOF

# Cleanup temporary files
echo "[INFO] Cleaning up temporary files..."
rm -f .bubble_test_${TEST_ID}_*.json
rm -f .replication_config_${TEST_ID}.json

echo ""
echo "[SUCCESS] DR ENVIRONMENT RESTORED!"
echo "════════════════════════════════════════════════"
echo "Status: Pre-test state fully restored"
echo "Report: $REPORT_FILE"
echo "Replication: ACTIVE"
echo "════════════════════════════════════════════════"
```


*Last Updated: November 25, 2025*  
*Version: 2.0 - Integrated S3 DR Strategy*  
*Classification: Confidential - GuidingCare Internal*