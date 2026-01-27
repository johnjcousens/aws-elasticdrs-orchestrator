# HRP SQL Server On EC2 Disaster Recover Detailed Design and Runbook

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5171216573/HRP%20SQL%20Server%20On%20EC2%20Disaster%20Recover%20Detailed%20Design%20and%20Runbook

**Created by:** Venkata Kommuri on October 15, 2025  
**Last modified by:** Chris Falk on December 18, 2025 at 08:18 PM

---

Standalone SQL Server on EC2 using AWS Elastic Disaster Recovery Service (DRS)
------------------------------------------------------------------------------

**Document Version:** 1.0

**Last Updated:** November 2025

**Author:** AWS Migration Team

**Target Audience:** DBAs, Infrastructure Engineers, DR Coordinators

### Table of Contents

* [1. Executive Summary](#)
* [2. Architecture Overview](#)
* [3. Prerequisites](#)
* [4. Phase 1: AWS DRS Setup and Configuration](#)
* [5. Phase 2: SQL Server Source Configuration](#)
* [6. Phase 3: Replication Setup](#)
* [7. Phase 4: DR Testing Procedures](#)
* [8. Phase 5: Failover Procedures](#)
* [9. Phase 6: Failback Procedures](#)
* [10. Monitoring and Alerting](#)
* [11. Troubleshooting Guide](#)
* [12. Appendices](#)

1. Executive Summary
--------------------

### 1.1 Purpose

This runbook provides comprehensive step-by-step procedures for implementing disaster recovery for standalone SQL Server instances running on Amazon EC2 using AWS Elastic Disaster Recovery Service (AWS DRS). The solution supports HRP's multi-region architecture with primary regions in US-East-1 and US-West-2, and DR regions in US-East-2 and US-West-1.

### 1.2 Solution Overview

AWS DRS provides continuous block-level replication of SQL Server EC2 instances from primary to DR regions, enabling:

* **RTO Target:** 4 hours
* **RPO Target:** 15 minutes
* **Recovery Strategy:** Automated failover with one-click recovery
* **Replication Method:** Continuous block-level replication
* **Cost Efficiency:** Pay only for staging resources until failover

### 1.3 Key Benefits

| Benefit | Description |
| --- | --- |
| Continuous Data Protection | Block-level replication with minimal performance impact on production |
| Automated Recovery | One-click recovery process reducing manual intervention and human error |
| Point-in-Time Recovery | Multiple recovery points with granular recovery options |
| Non-Disruptive Testing | Test DR procedures without impacting production workloads |
| Cost-Effective | Lower cost compared to Always On solutions; no SQL Server Enterprise licensing required |

### 1.4 HRP Requirements Alignment

Based on analysis of HRP DR documentation, this solution addresses the following requirements:

#### Current State Requirements

* **Storage-Level Replication:** Maintains current EDRS approach using AWS DRS
* **All-or-Nothing Failover:** Entire customer environment fails over as coordinated unit
* **RTO/RPO Targets:** Meets 4-hour RTO and 15-minute RPO requirements
* **Quarterly DR Testing:** Supports non-disruptive testing without customer impact
* **Multi-Region Support:** Primary (US-East-1, US-West-2) and DR (US-East-2, US-West-1)
* **Customer Isolation:** Dedicated infrastructure per customer with security group isolation

2. Architecture Overview
------------------------

### 2.1 Regional Architecture

![HRP-SQL-DR-Design.drawio.png](images/HRP-SQL-DR-Design.drawio.png)


```

Primary Regions:
├── US-East-1 (N. Virginia)
│   ├── Production SQL Server EC2 Instances
│   ├── AWS DRS Replication Agents
│   └── DR Region: US-East-2 (Ohio)
│
└── US-West-2 (Oregon)
    ├── Production SQL Server EC2 Instances
    ├── AWS DRS Replication Agents
    └── DR Region: US-West-1 (N. California)
        
```


### 2.2 Component Architecture

#### Primary Region Components

| Component | Description | Purpose |
| --- | --- | --- |
| SQL Server EC2 Instances | Memory-optimized instances (r6i.xlarge to r6i.8xlarge) | Production database workloads |
| EBS Volumes - Data | gp3 or io2 volumes | SQL Server data files |
| EBS Volumes - Logs | gp3 volumes optimized for sequential writes | SQL Server transaction logs |
| Instance Store - TempDB | NVMe SSD (not replicated) | Temporary database operations |
| AWS DRS Agent | Installed on each SQL Server instance | Continuous block-level replication |
| Application Load Balancer | ALB for application connectivity | Traffic distribution and health checks |
| Route 53 | DNS management with health checks | Automated DNS failover |

#### DR Region Components

| Component | Description | Cost Model |
| --- | --- | --- |
| DRS Staging Area | Low-cost instances (t3.small) for continuous replication | Always running - minimal cost |
| Recovery Instances | Launched during DR events (same specs as primary) | Only during failover/testing |
| EBS Volumes | Replicated from primary region | Storage costs only |
| VPC Infrastructure | Pre-configured network matching primary | No additional cost |
| Route 53 | Failover DNS configuration | Standard Route 53 pricing |

### 2.3 Network Architecture


```

Primary Region (US-East-1):
VPC: 10.10.0.0/16
├── Database Subnet (Private): 10.10.2.0/24
│   └── SQL Server Instances
├── Application Subnet (Private): 10.10.1.0/24
│   └── WebLogic Servers
├── DRS Replication Subnet (Private): 10.10.10.0/24
│   └── DRS Staging Instances
└── Public Subnet: 10.10.0.0/24
    └── NAT Gateway

DR Region (US-East-2):
VPC: 10.20.0.0/16
├── Database Subnet (Private): 10.20.2.0/24
│   └── SQL Server Recovery Instances
├── Application Subnet (Private): 10.20.1.0/24
│   └── WebLogic Recovery Instances
├── DRS Staging Subnet (Private): 10.20.10.0/24
│   └── DRS Staging Instances
└── Public Subnet: 10.20.0.0/24
    └── NAT Gateway
        
```


### 2.4 Data Flow

#### Normal Operations

1. Applications connect to SQL Server in primary region via Route 53 DNS
2. DRS agent captures block-level changes in real-time
3. Changes replicated to DR region staging area over AWS backbone
4. Staging instances apply changes continuously
5. Recovery points created per PIT (Point-in-Time) policy

#### Failover Operations

1. Disaster declared and failover initiated
2. DRS launches full-spec recovery instances from staging data
3. EBS volumes attached to recovery instances
4. SQL Server starts automatically on recovery instances
5. Route 53 health checks detect primary failure
6. DNS automatically redirects traffic to DR region
7. Applications reconnect to DR SQL Server instances

3. Prerequisites
----------------

### 3.1 AWS Account Requirements

#### IAM Permissions

Required IAM policies for AWS DRS implementation:


```
{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "drs:*",
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeSnapshots",
        "ec2:CreateSnapshot",
        "ec2:CreateTags",
        "ec2:DescribeImages",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:ModifyInstanceAttribute",
        "iam:PassRole",
        "iam:CreateServiceLinkedRole",
        "kms:CreateGrant",
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:Encrypt",
        "kms:GenerateDataKey",
        "kms:ReEncrypt"
      ],
      "Resource": "*"
    }
  ]
}
```


#### Service-Linked Roles

AWS DRS automatically creates required service-linked roles:

* `AWSServiceRoleForElasticDisasterRecovery`
* `AWSElasticDisasterRecoveryReplicationServerRole`
* `AWSElasticDisasterRecoveryConversionServerRole`
* `AWSElasticDisasterRecoveryRecoveryInstanceRole`

### 3.2 Network Requirements

#### Primary Region Network Configuration

| Component | Requirement | Purpose |
| --- | --- | --- |
| VPC CIDR | Non-overlapping with DR region | Enable cross-region connectivity |
| Private Subnets | Database tier isolation | Security and network segmentation |
| Security Groups | SQL Server: Port 1433 DRS Agent: Port 443 (HTTPS outbound) DRS Replication: Port 1500 | Allow required traffic |
| NAT Gateway | Required for DRS agent internet connectivity | Agent communication with DRS service |
| VPC Endpoints | Optional: S3, EC2, CloudWatch | Reduce data transfer costs |

#### Bandwidth Requirements

| Phase | Bandwidth | Duration |
| --- | --- | --- |
| Initial Replication | 100 Mbps minimum (recommended) | Depends on database size |
| Ongoing Replication | 10-50 Mbps (based on change rate) | Continuous |
| Recommended | AWS Direct Connect or VPN | Predictable performance |

### 3.3 SQL Server Requirements

#### Supported SQL Server Versions

* SQL Server 2012 and later
* All editions: Enterprise, Standard, Web, Express
* Windows Server 2012 R2 and later

#### SQL Server Configuration

| Setting | Requirement | Reason |
| --- | --- | --- |
| Recovery Model | Full | Required for transaction log protection |
| Authentication | Mixed mode or Windows | Application connectivity |
| SQL Server Agent | Running | Backup automation |
| Disk Space | Minimum 20% free on all volumes | Replication overhead |
| Permissions | Local Administrator access | DRS agent installation |

#### EC2 Instance Requirements

Match On-prem servers

| Component | Specification |
| --- | --- |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |

### 3.4 Backup Requirements

#### Pre-Migration Backups

* Full database backup to S3
* Incremental database backup to S3
* Transaction log backup to local ebs
* System state backup
* SQL Server configuration backup (logins, jobs, linked servers)

#### Backup Retention

| Backup Type | Retention | Location |
| --- | --- | --- |
| Backups | 30 days | S3 with cross-region replication |
| DRS Recovery Points | Per PIT policy | DR region staging area |

4. Phase 1: AWS DRS Setup and Configuration
-------------------------------------------

### 4.1 Initialize AWS DRS in Primary Region

#### Console Steps

1. **Navigate to AWS DRS Console**

   
```
AWS Console → Services → AWS Elastic Disaster Recovery
```

2. **Initialize DRS Service**

   * Click "Get started" or "Initialize service"
   * Select primary region (US-East-1 or US-West-2)
   * Review and accept service terms
   * Wait for initialization (2-3 minutes)
3. **Verify Service Initialization**

   
```
aws drs describe-source-servers --region us-east-1
```


   Expected output: Empty list (no servers yet)

#### CLI Steps


```
# Set environment variables
export PRIMARY_REGION="us-east-1"
export DR_REGION="us-east-2"

# Initialize DRS in primary region
aws drs initialize-service --region $PRIMARY_REGION

# Verify initialization
aws drs describe-source-servers --region $PRIMARY_REGION
```


### 4.2 Configure DRS Replication Settings

#### Create Replication Configuration Template


```
aws drs create-replication-configuration-template \
  --region $PRIMARY_REGION \
  --associate-default-security-group \
  --bandwidth-throttling 0 \
  --create-public-ip false \
  --data-plane-routing PRIVATE_IP \
  --default-large-staging-disk-type GP3 \
  --ebs-encryption CUSTOM \
  --ebs-encryption-key-arn "arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID" \
  --replication-server-instance-type t3.small \
  --replication-servers-security-groups-ids sg-xxxxxxxxx \
  --staging-area-subnet-id subnet-xxxxxxxxx \
  --staging-area-tags Key=Environment,Value=DRS Key=Purpose,Value=Staging \
  --use-dedicated-replication-server false \
  --pit-policy '[
    {
      "enabled": true,
      "interval": 10,
      "retentionDuration": 60,
      "ruleID": 1,
      "units": "MINUTE"
    },
    {
      "enabled": true,
      "interval": 1,
      "retentionDuration": 24,
      "ruleID": 2,
      "units": "HOUR"
    },
    {
      "enabled": true,
      "interval": 1,
      "retentionDuration": 7,
      "ruleID": 3,
      "units": "DAY"
    }
  ]'
```


#### Configuration Parameters Explained

| Parameter | Value | Rationale |
| --- | --- | --- |
| bandwidth-throttling | 0 (unlimited) | Maximize replication speed; adjust if network impact observed |
| create-public-ip | false | Use private networking for security |
| data-plane-routing | PRIVATE\_IP | Route replication through private network |
| default-large-staging-disk-type | GP3 | Cost-effective with good performance |
| ebs-encryption | CUSTOM | Use customer-managed KMS keys for compliance |
| replication-server-instance-type | t3.small | Adequate for most SQL Server workloads |
| use-dedicated-replication-server | false | Share replication servers for cost optimization |

#### Point-in-Time (PIT) Policy Configuration

The PIT policy defines recovery point granularity:

1. **Rule 1:** Every 10 minutes for last 60 minutes (RPO: 10 minutes)
2. **Rule 2:** Hourly for last 24 hours
3. **Rule 3:** Daily for last 7 days

### 4.3 Configure KMS Encryption Keys

#### Create KMS Keys for DRS


```
# Create KMS key in primary region
aws kms create-key \
  --region $PRIMARY_REGION \
  --description "DRS encryption key for SQL Server replication" \
  --key-policy file://kms-key-policy.json

# Create alias for the key
aws kms create-alias \
  --region $PRIMARY_REGION \
  --alias-name alias/drs-sqlserver-primary \
  --target-key-id <key-id-from-previous-command>

# Create KMS key in DR region
aws kms create-key \
  --region $DR_REGION \
  --description "DRS encryption key for SQL Server DR" \
  --key-policy file://kms-key-policy.json

# Create alias for DR key
aws kms create-alias \
  --region $DR_REGION \
  --alias-name alias/drs-sqlserver-dr \
  --target-key-id <key-id-from-previous-command>
```


#### KMS Key Policy


```
{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Sid": "Enable IAM User Permissions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "Allow DRS to use the key",
      "Effect": "Allow",
      "Principal": {
        "Service": "drs.amazonaws.com"
      },
      "Action": [
        "kms:Decrypt",
        "kms:Encrypt",
        "kms:GenerateDataKey",
        "kms:CreateGrant",
        "kms:DescribeKey",
        "kms:ReEncrypt*"
      ],
      "Resource": "*"
    }
  ]
}
```


### 4.4 Configure Security Groups

#### Primary Region Security Groups

Please Refer to Network design

### 4.5 Verification Checklist

#### Phase 1 Completion Checklist

* DRS service initialized in both primary and DR regions
* Replication configuration templates created
* KMS keys created and accessible
* Security groups configured with proper rules
* Network connectivity verified between regions
* VPC endpoints configured (if using)
* NAT Gateway operational in both regions

5. Phase 2: SQL Server Source Configuration
-------------------------------------------

### 5.1 Pre-Installation SQL Server Assessment

#### Database Health Check


```
-- Check SQL Server version and edition
SELECT 
    SERVERPROPERTY('ProductVersion') AS Version,
    SERVERPROPERTY('ProductLevel') AS ServicePack,
    SERVERPROPERTY('Edition') AS Edition,
    SERVERPROPERTY('EngineEdition') AS EngineEdition;

-- Check database recovery model
SELECT 
    name AS DatabaseName,
    recovery_model_desc AS RecoveryModel,
    state_desc AS State,
    compatibility_level AS CompatibilityLevel
FROM sys.databases
WHERE database_id > 4;

-- Check database sizes
SELECT 
    DB_NAME(database_id) AS DatabaseName,
    type_desc AS FileType,
    CAST(size * 8.0 / 1024 / 1024 AS DECIMAL(10,2)) AS SizeGB,
    CAST(FILEPROPERTY(name, 'SpaceUsed') * 8.0 / 1024 / 1024 AS DECIMAL(10,2)) AS UsedGB,
    physical_name AS FilePath
FROM sys.master_files
WHERE database_id > 4
ORDER BY database_id, type;

-- Check disk space
EXEC xp_fixeddrives;
```


#### Set Recovery Model to Full


```
-- Set all user databases to FULL recovery model
DECLARE @DatabaseName NVARCHAR(128);
DECLARE @SQL NVARCHAR(MAX);

DECLARE db_cursor CURSOR FOR
SELECT name 
FROM sys.databases 
WHERE database_id > 4 
  AND recovery_model_desc != 'FULL'
  AND state_desc = 'ONLINE';

OPEN db_cursor;
FETCH NEXT FROM db_cursor INTO @DatabaseName;

WHILE @@FETCH_STATUS = 0
BEGIN
    SET @SQL = 'ALTER DATABASE [' + @DatabaseName + '] SET RECOVERY FULL;';
    PRINT 'Setting ' + @DatabaseName + ' to FULL recovery model';
    EXEC sp_executesql @SQL;
    
    FETCH NEXT FROM db_cursor INTO @DatabaseName;
END;

CLOSE db_cursor;
DEALLOCATE db_cursor;
```


### 5.2 Perform Full Backup Before DRS Installation

**Important:** Always perform a full backup before installing DRS agent. This provides a rollback point if needed.


```
-- Backup all user databases to local disk
DECLARE @DatabaseName NVARCHAR(128);
DECLARE @BackupPath NVARCHAR(500);
DECLARE @SQL NVARCHAR(MAX);
DECLARE @Timestamp VARCHAR(20);

SET @Timestamp = CONVERT(VARCHAR(20), GETDATE(), 112) + '_' + 
                 REPLACE(CONVERT(VARCHAR(20), GETDATE(), 108), ':', '');

DECLARE db_cursor CURSOR FOR
SELECT name 
FROM sys.databases 
WHERE database_id > 4 
  AND state_desc = 'ONLINE';

OPEN db_cursor;
FETCH NEXT FROM db_cursor INTO @DatabaseName;

WHILE @@FETCH_STATUS = 0
BEGIN
    SET @BackupPath = 'D:\SQLBackups\PreDRS_' + @DatabaseName + '_' + @Timestamp + '.bak';
    SET @SQL = 'BACKUP DATABASE [' + @DatabaseName + '] TO DISK = ''' + @BackupPath + 
               ''' WITH COMPRESSION, CHECKSUM, STATS = 10;';
    
    PRINT 'Backing up ' + @DatabaseName + ' to ' + @BackupPath;
    EXEC sp_executesql @SQL;
    
    FETCH NEXT FROM db_cursor INTO @DatabaseName;
END;

CLOSE db_cursor;
DEALLOCATE db_cursor;
```


#### Copy Backups to S3


```
# PowerShell script to copy backups to S3
$BackupPath = "D:\SQLBackups"
$S3Bucket = "s3://hrp-sqlserver-backups-primary"
$Region = "us-east-1"

# Copy all backup files to S3
Get-ChildItem -Path $BackupPath -Filter "PreDRS_*.bak" | ForEach-Object {
    Write-Host "Uploading $($_.Name) to S3..."
    Write-S3Object -BucketName "hrp-sqlserver-backups-primary" `
                   -File $_.FullName `
                   -Key "pre-drs-backups/$($_.Name)" `
                   -Region $Region `
                   -StorageClass STANDARD_IA
}

Write-Host "Backup upload completed"
```


### 5.3 Configure SQL Server for Optimal DRS Performance

#### Optimize Transaction Log Management


```
-- Check transaction log size and usage
SELECT 
    DB_NAME(database_id) AS DatabaseName,
    name AS LogFileName,
    CAST(size * 8.0 / 1024 AS DECIMAL(10,2)) AS LogSizeMB,
    CAST(FILEPROPERTY(name, 'SpaceUsed') * 8.0 / 1024 AS DECIMAL(10,2)) AS LogUsedMB,
    CAST((size - FILEPROPERTY(name, 'SpaceUsed')) * 8.0 / 1024 AS DECIMAL(10,2)) AS LogFreeMB,
    CAST(FILEPROPERTY(name, 'SpaceUsed') * 100.0 / size AS DECIMAL(5,2)) AS PercentUsed
FROM sys.master_files
WHERE type_desc = 'LOG'
  AND database_id > 4;

-- Set appropriate transaction log autogrowth
ALTER DATABASE [DatabaseName] 
MODIFY FILE (
    NAME = LogFileName,
    FILEGROWTH = 512MB  -- Fixed size growth instead of percentage
);

-- Optimize checkpoint frequency for DRS
EXEC sp_configure 'recovery interval (min)', 5;
RECONFIGURE;

-- Enable backup compression
EXEC sp_configure 'backup compression default', 1;
RECONFIGURE;
```


### 5.4 Create SQL Server Maintenance Jobs

#### Transaction Log Backup Job (Every 15 Minutes)


```
USE msdb;
GO

-- Create job
EXEC dbo.sp_add_job
    @job_name = N'DRS - Transaction Log Backup',
    @enabled = 1,
    @description = N'Transaction log backups every 15 minutes for DRS RPO';

-- Add job step
EXEC dbo.sp_add_jobstep
    @job_name = N'DRS - Transaction Log Backup',
    @step_name = N'Backup All Transaction Logs',
    @subsystem = N'TSQL',
    @command = N'
DECLARE @DatabaseName NVARCHAR(128);
DECLARE @BackupPath NVARCHAR(500);
DECLARE @SQL NVARCHAR(MAX);
DECLARE @Timestamp VARCHAR(20);

SET @Timestamp = CONVERT(VARCHAR(20), GETDATE(), 112) + ''_'' + 
                 REPLACE(CONVERT(VARCHAR(20), GETDATE(), 108), '':'', '''');

DECLARE db_cursor CURSOR FOR
SELECT name 
FROM sys.databases 
WHERE database_id > 4 
  AND recovery_model_desc = ''FULL''
  AND state_desc = ''ONLINE'';

OPEN db_cursor;
FETCH NEXT FROM db_cursor INTO @DatabaseName;

WHILE @@FETCH_STATUS = 0
BEGIN
    SET @BackupPath = ''D:\SQLBackups\Logs\'' + @DatabaseName + ''_'' + @Timestamp + ''.trn'';
    SET @SQL = ''BACKUP LOG ['' + @DatabaseName + ''] TO DISK = '''''' + @BackupPath + 
               '''''' WITH COMPRESSION, CHECKSUM;'';
    EXEC sp_executesql @SQL;
    FETCH NEXT FROM db_cursor INTO @DatabaseName;
END;

CLOSE db_cursor;
DEALLOCATE db_cursor;
',
    @retry_attempts = 3,
    @retry_interval = 5;

-- Create schedule (every 15 minutes)
EXEC dbo.sp_add_schedule
    @schedule_name = N'Every 15 Minutes',
    @freq_type = 4,  -- Daily
    @freq_interval = 1,
    @freq_subday_type = 4,  -- Minutes
    @freq_subday_interval = 15,
    @active_start_time = 0;

-- Attach schedule to job
EXEC dbo.sp_attach_schedule
    @job_name = N'DRS - Transaction Log Backup',
    @schedule_name = N'Every 15 Minutes';

-- Add job to local server
EXEC dbo.sp_add_jobserver
    @job_name = N'DRS - Transaction Log Backup',
    @server_name = N'(LOCAL)';
GO
```


### 5.5 Phase 2 Completion Checklist

* SQL Server health check completed
* All databases set to FULL recovery model
* Full backups completed and uploaded to S3
* Transaction log management optimized
* SQL Server Agent jobs created
* SQL Server configuration documented
* Sufficient disk space verified (20% free minimum)

6. Phase 3: Replication Setup
-----------------------------

### 6.1 Download and Install AWS DRS Agent

#### Download DRS Agent Installer


```
# PowerShell script to download DRS agent
$Region = "us-east-1"
$OutputPath = "C:\Temp\DRS"
$InstallerUrl = "https://aws-elastic-disaster-recovery-$Region.s3.$Region.amazonaws.com/latest/windows/AwsReplicationWindowsInstaller.exe"

# Create directory
New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null

# Download installer
Write-Host "Downloading AWS DRS agent installer..."
Invoke-WebRequest -Uri $InstallerUrl -OutFile "$OutputPath\AwsReplicationWindowsInstaller.exe"

Write-Host "Download completed: $OutputPath\AwsReplicationWindowsInstaller.exe"
```


#### Install DRS Agent


```
# Install DRS agent with parameters
$InstallerPath = "C:\Temp\DRS\AwsReplicationWindowsInstaller.exe"
$Region = "us-east-1"
$AwsAccessKeyId = "AKIAIOSFODNN7EXAMPLE"
$AwsSecretAccessKey = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# Installation parameters
$InstallArgs = @(
    "--region", $Region,
    "--aws-access-key-id", $AwsAccessKeyId,
    "--aws-secret-access-key", $AwsSecretAccessKey,
    "--no-prompt"
)

Write-Host "Installing AWS DRS agent..."
Write-Host "This may take 5-10 minutes..."

# Run installer
Start-Process -FilePath $InstallerPath -ArgumentList $InstallArgs -Wait -NoNewWindow

# Verify installation
$Service = Get-Service -Name "AwsReplicationAgent" -ErrorAction SilentlyContinue

if ($Service -and $Service.Status -eq "Running") {
    Write-Host "✓ AWS DRS agent installed and running successfully"
} else {
    Write-Host "✗ AWS DRS agent installation failed or service not running"
}
```


### 6.2 Configure Source Server in AWS DRS

#### Verify Source Server Registration


```
# Check if source server is registered
aws drs describe-source-servers \
  --region $PRIMARY_REGION \
  --query "items[?hostname=='$SQL_SERVER_HOSTNAME']" \
  --output table

# Get source server ID
SOURCE_SERVER_ID=$(aws drs describe-source-servers \
  --region $PRIMARY_REGION \
  --query "items[?hostname=='$SQL_SERVER_HOSTNAME'].sourceServerID" \
  --output text)

echo "Source Server ID: $SOURCE_SERVER_ID"
```


#### Configure Launch Settings


```
# Update launch configuration for SQL Server
aws drs update-launch-configuration \
  --region $PRIMARY_REGION \
  --source-server-id $SOURCE_SERVER_ID \
  --copy-private-ip false \
  --copy-tags true \
  --launch-disposition STARTED \
  --licensing '{"osByol": false}' \
  --name "SQL-Server-DR-Instance" \
  --target-instance-type-right-sizing-method BASIC
```


### 6.3 Update Replication Configuration

#### Disk Configuration for SQL Server as per On-Prem servers

| Disk | Device | Purpose | Type | IOPS | Throughput |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

### 6.4 Monitor Initial Replication

#### Check Replication Status

### 6.5 Validate Replication Health

#### Replication Health Checks

#### SQL Server Performance Impact Assessment

### 6.6 Phase 3 Completion Checklist

* DRS agent installed and running
* Source server registered in DRS
* Replication state is "CONTINUOUS"
* All disks showing 100% replicated
* Backlog is near zero (<1 GB)
* Recovery points being created per PIT policy
* No errors in DRS agent logs
* SQL Server performance within normal range
* No impact on application performance

7. Phase 4: DR Testing Procedures
---------------------------------

### 7.1 Pre-Test Planning

#### DR Test Planning Checklist

#### DR Test Plan Template

| Item | Details |
| --- | --- |
| Test Date | [YYYY-MM-DD] |
| Test Window | [Start Time] - [End Time] |
| Test Type | ☐ Non-Disruptive ☐ Full Failover |
| Primary Region | us-east-1 / us-west-2 |
| DR Region | us-east-2 / us-west-1 |

#### Test Objectives

* Verify RTO target (4 hours)
* Verify RPO target (15 minutes)
* Validate SQL Server functionality
* Test application connectivity
* Verify data integrity
* Document lessons learned

### 7.2 Non-Disruptive DR Test

#### Initiate Recovery Drill


```
# Start recovery drill (non-disruptive test)
aws drs start-recovery \
  --region $PRIMARY_REGION \
  --source-servers '[
    {
      "sourceServerID": "'$SOURCE_SERVER_ID'",
      "recoverySnapshotID": "pit-xxxxx"
    }
  ]' \
  --is-drill true \
  --tags Key=TestType,Value=NonDisruptive Key=TestDate,Value=$(date +%Y%m%d)

# Get recovery job ID
RECOVERY_JOB_ID=$(aws drs describe-recovery-instances \
  --region $PRIMARY_REGION \
  --filters "sourceServerIDs=$SOURCE_SERVER_ID" \
  --query "items[0].recoveryInstanceID" \
  --output text)

echo "Recovery Job ID: $RECOVERY_JOB_ID"
```


#### Monitor Recovery Progress


```
# Monitor recovery job status
watch -n 10 'aws drs describe-recovery-instances \
  --region $PRIMARY_REGION \
  --recovery-instance-ids $RECOVERY_JOB_ID \
  --query "items[0].{
    State: dataReplicationInfo.dataReplicationState,
    RecoveryState: recoveryInstanceProperties.recoveryState,
    InstanceID: ec2InstanceID,
    PrivateIP: recoveryInstanceProperties.networkInterfaces[0].privateIp
  }" \
  --output table'
```


### 7.3 Validate Recovered SQL Server Instance

#### SQL Server Health Checks


```
-- Connect to recovered SQL Server instance
-- Run comprehensive health checks

-- 1. Verify SQL Server is running
SELECT 
    SERVERPROPERTY('ProductVersion') AS Version,
    SERVERPROPERTY('Edition') AS Edition,
    SERVERPROPERTY('MachineName') AS MachineName,
    SERVERPROPERTY('ServerName') AS ServerName,
    GETDATE() AS CurrentTime;

-- 2. Check all databases are online
SELECT 
    name AS DatabaseName,
    state_desc AS State,
    recovery_model_desc AS RecoveryModel,
    compatibility_level AS CompatibilityLevel
FROM sys.databases
ORDER BY name;

-- 3. Verify database integrity
DBCC CHECKDB WITH NO_INFOMSGS, ALL_ERRORMSGS;

-- 4. Verify logins
SELECT 
    name,
    type_desc,
    is_disabled,
    create_date,
    modify_date
FROM sys.server_principals
WHERE type IN ('S', 'U', 'G')
ORDER BY name;

-- 5. Check SQL Agent jobs
SELECT 
    j.name AS JobName,
    j.enabled,
    j.date_created,
    j.date_modified
FROM msdb.dbo.sysjobs j
ORDER BY j.name;
```


### 7.4 Application Connectivity Testing

#### Test Connection


```
# PowerShell - Test application connectivity to recovered SQL Server
$RecoveryServerIP = "10.20.2.10"
$DatabaseName = "HRP_Production"
$TestQuery = "SELECT @@VERSION, GETDATE()"

$ConnectionString = "Server=$RecoveryServerIP;Database=$DatabaseName;Integrated Security=True;"

try {
    $Connection = New-Object System.Data.SqlClient.SqlConnection($ConnectionString)
    $Connection.Open()
    
    $Command = $Connection.CreateCommand()
    $Command.CommandText = $TestQuery
    $Reader = $Command.ExecuteReader()
    
    Write-Host "✓ Connection successful!" -ForegroundColor Green
    
    while ($Reader.Read()) {
        Write-Host "SQL Version: $($Reader[0])"
        Write-Host "Current Time: $($Reader[1])"
    }
    
    $Reader.Close()
    $Connection.Close()
    
} catch {
    Write-Host "✗ Connection failed: $($_.Exception.Message)" -ForegroundColor Red
}
```


### 7.5 DR Test Report Template

#### DR Test Report

| Metric | Target | Actual | Status |
| --- | --- | --- | --- |
| RTO | 5-10 minutes | [X] minutes | ☐ Met ☐ Not Met |
| RPO | 15 minutes | [X] minutes | ☐ Met ☐ Not Met |
| Recovery Success | 100% | [X]% | ☐ Success ☐ Failure |

#### Test Results Summary

* Recovery instance launched successfully
* All EBS volumes attached correctly
* SQL Server service started automatically
* All databases online and accessible
* No database corruption detected
* Application connectivity successful
* Performance within acceptable limits

### 7.6 Cleanup After DR Test

#### Terminate Recovery Instances


```
# Terminate recovery instances after successful test
aws drs terminate-recovery-instances \
  --region $PRIMARY_REGION \
  --recovery-instance-ids $RECOVERY_JOB_ID

# Verify termination
aws drs describe-recovery-instances \
  --region $PRIMARY_REGION \
  --recovery-instance-ids $RECOVERY_JOB_ID \
  --query "items[0].recoveryInstanceProperties.recoveryState"
```


### 7.7 Phase 4 Completion Checklist

* DR test plan documented
* Non-disruptive test completed successfully
* RTO/RPO targets met
* SQL Server validated in DR region
* Application connectivity tested
* Test report completed
* Recovery instances terminated
* Primary region operations unaffected
* Lessons learned documented

8. Phase 5: Failover Procedures
-------------------------------

### 8.1 Failover Decision and Communication

#### Disaster Declaration Criteria

**Initiate failover when one or more of the following conditions occur:**

1. **Primary Region Outage**

   * Complete AWS region unavailability
   * Extended network connectivity loss (>30 minutes)
   * Multiple availability zone failures
2. **Data Center Disaster**

   * Natural disaster affecting primary region
   * Extended power outage
   * Physical security breach
3. **Critical Infrastructure Failure**

   * Unrecoverable SQL Server corruption
   * Catastrophic storage failure
   * Irrecoverable network infrastructure failure
4. **Planned Failover**

   * Scheduled maintenance requiring extended downtime
   * Primary region migration
   * Compliance or regulatory requirements

#### Failover Communication Template

#### [URGENT] DR Failover Initiated - SQL Server Environment

| Field | Details |
| --- | --- |
| Incident ID | [INC-XXXXX] |
| Severity | Critical |
| Primary Region | [us-east-1 / us-west-2] |
| DR Region | [us-east-2 / us-west-1] |
| Affected Systems | SQL Server Production Environment |
| Estimated Impact | [Duration] |

**Situation:** [Brief description of the disaster/outage]

**Actions Taken:**

* [Timestamp] - Disaster declared
* [Timestamp] - DR team assembled
* [Timestamp] - Failover initiated
* [Timestamp] - Recovery in progress

### 8.2 Pre-Failover Verification

#### Pre-Failover Checklist


```
#!/bin/bash
# Pre-failover verification script

PRIMARY_REGION="us-east-1"
DR_REGION="us-east-2"
SOURCE_SERVER_ID="s-xxxxxxxxx"

echo "=== Pre-Failover Verification ==="
echo "Timestamp: $(date)"

# 1. Verify replication status
REPLICATION_STATE=$(aws drs describe-source-servers \
  --region $PRIMARY_REGION \
  --source-server-ids $SOURCE_SERVER_ID \
  --query "items[0].dataReplicationInfo.dataReplicationState" \
  --output text)

echo "Replication State: $REPLICATION_STATE"

# 2. Check replication lag
LAG=$(aws drs describe-source-servers \
  --region $PRIMARY_REGION \
  --source-server-ids $SOURCE_SERVER_ID \
  --query "items[0].dataReplicationInfo.lagDuration" \
  --output text)

echo "Replication Lag: $LAG"

# 3. Verify latest recovery point
LATEST_SNAPSHOT=$(aws drs describe-recovery-snapshots \
  --region $PRIMARY_REGION \
  --source-server-id $SOURCE_SERVER_ID \
  --query "items[0].timestamp" \
  --output text)

echo "Latest Recovery Point: $LATEST_SNAPSHOT"

echo "=== Pre-Failover Verification Complete ==="
```


### 8.3 Execute Failover

#### Initiate Production Failover


```
#!/bin/bash
# Production failover script

PRIMARY_REGION="us-east-1"
DR_REGION="us-east-2"
SOURCE_SERVER_ID="s-xxxxxxxxx"
FAILOVER_TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== PRODUCTION FAILOVER INITIATED ==="
echo "Timestamp: $(date)"
echo "Source Server: $SOURCE_SERVER_ID"
echo "Primary Region: $PRIMARY_REGION"
echo "DR Region: $DR_REGION"

# 1. Select recovery point
RECOVERY_SNAPSHOT=$(aws drs describe-recovery-snapshots \
  --region $PRIMARY_REGION \
  --source-server-id $SOURCE_SERVER_ID \
  --query "items[0].snapshotID" \
  --output text)

echo "Selected Recovery Point: $RECOVERY_SNAPSHOT"

# 2. Initiate recovery
RECOVERY_JOB=$(aws drs start-recovery \
  --region $PRIMARY_REGION \
  --source-servers "[{\"sourceServerID\": \"$SOURCE_SERVER_ID\", \"recoverySnapshotID\": \"$RECOVERY_SNAPSHOT\"}]" \
  --is-drill false \
  --tags Key=FailoverType,Value=Production Key=FailoverTimestamp,Value=$FAILOVER_TIMESTAMP \
  --output json)

RECOVERY_JOB_ID=$(echo $RECOVERY_JOB | jq -r '.job.jobID')
echo "Recovery Job ID: $RECOVERY_JOB_ID"

# 3. Monitor recovery progress
echo "Monitoring recovery progress..."
while true; do
    RECOVERY_STATE=$(aws drs describe-recovery-instances \
      --region $PRIMARY_REGION \
      --filters "sourceServerIDs=$SOURCE_SERVER_ID" \
      --query "items[0].recoveryInstanceProperties.recoveryState" \
      --output text)
    
    echo "$(date): Recovery State: $RECOVERY_STATE"
    
    if [ "$RECOVERY_STATE" == "RECOVERY_COMPLETE" ]; then
        echo "✓ Recovery completed successfully"
        break
    elif [ "$RECOVERY_STATE" == "RECOVERY_FAILED" ]; then
        echo "✗ Recovery failed"
        exit 1
    fi
    
    sleep 30
done

# 4. Get recovery instance details
RECOVERY_INSTANCE_ID=$(aws drs describe-recovery-instances \
  --region $PRIMARY_REGION \
  --filters "sourceServerIDs=$SOURCE_SERVER_ID" \
  --query "items[0].ec2InstanceID" \
  --output text)

RECOVERY_PRIVATE_IP=$(aws drs describe-recovery-instances \
  --region $PRIMARY_REGION \
  --filters "sourceServerIDs=$SOURCE_SERVER_ID" \
  --query "items[0].recoveryInstanceProperties.networkInterfaces[0].privateIp" \
  --output text)

echo "Recovery Instance ID: $RECOVERY_INSTANCE_ID"
echo "Recovery Private IP: $RECOVERY_PRIVATE_IP"

# 5. Wait for instance to be fully running
echo "Waiting for instance to be fully operational..."
aws ec2 wait instance-status-ok \
  --region $DR_REGION \
  --instance-ids $RECOVERY_INSTANCE_ID

echo "✓ Instance is fully operational"

echo "=== FAILOVER RECOVERY COMPLETE ==="
```


### 8.4 Post-Failover SQL Server Validation

#### SQL Server Health Validation


```
-- Connect to recovered SQL Server instance in DR region

-- 1. Verify SQL Server is running
SELECT 
    SERVERPROPERTY('ProductVersion') AS Version,
    SERVERPROPERTY('Edition') AS Edition,
    SERVERPROPERTY('MachineName') AS MachineName,
    SERVERPROPERTY('ServerName') AS ServerName,
    GETDATE() AS CurrentTime;

-- 2. Check all databases are online
SELECT 
    name AS DatabaseName,
    state_desc AS State,
    recovery_model_desc AS RecoveryModel,
    user_access_desc AS UserAccess
FROM sys.databases
WHERE database_id > 4
ORDER BY name;

-- 3. Bring any databases online if needed
DECLARE @DatabaseName NVARCHAR(128);
DECLARE @SQL NVARCHAR(MAX);

DECLARE db_cursor CURSOR FOR
SELECT name 
FROM sys.databases 
WHERE state_desc IN ('RECOVERING', 'RECOVERY_PENDING')
  AND database_id > 4;

OPEN db_cursor;
FETCH NEXT FROM db_cursor INTO @DatabaseName;

WHILE @@FETCH_STATUS = 0
BEGIN
    SET @SQL = 'ALTER DATABASE [' + @DatabaseName + '] SET ONLINE;';
    PRINT 'Bringing ' + @DatabaseName + ' online';
    EXEC sp_executesql @SQL;
    
    FETCH NEXT FROM db_cursor INTO @DatabaseName;
END;

CLOSE db_cursor;
DEALLOCATE db_cursor;

-- 4. Verify database integrity
DBCC CHECKDB WITH NO_INFOMSGS;

-- 5. Check for any errors in error log
EXEC xp_readerrorlog 0, 1, N'error';
EXEC xp_readerrorlog 0, 1, N'fail';
```


### 8.5 Update DNS and Network Configuration

#### Update Route 53 DNS Records


```
#!/bin/bash
# Update Route 53 DNS to point to DR region

HOSTED_ZONE_ID="Z1234567890ABC"
SQL_SERVER_DNS="sqlserver.hrp.internal"
DR_PRIVATE_IP="10.20.2.10"
TTL=60

echo "=== Updating DNS Records ==="
echo "DNS Name: $SQL_SERVER_DNS"
echo "New IP: $DR_PRIVATE_IP"

# Create change batch JSON
cat > /tmp/dns-change.json <
```


### `8.6 Post-Failover Validation`

#### `Comprehensive Validation Checklist`

#### `Infrastructure`

* `Recovery instance running in DR region`
* `All EBS volumes attached and accessible`
* `Network connectivity verified`
* `Security groups applied correctly`
* `Instance tagged appropriately`

#### `SQL Server`

* `SQL Server service running`
* `All databases online`
* `No database corruption`
* `Logins and permissions intact`
* `SQL Agent running`
* `Critical jobs started`
* `Linked servers accessible`

#### `Network and DNS`

* `DNS records updated`
* `DNS propagation complete`
* `Load balancer health checks passing`
* `Application connectivity verified`

#### `Application`

* `Application services started`
* `Connection strings updated`
* `Read operations successful`
* `Write operations successful`
* `Business processes functional`

`9. Phase 6: Failback Procedures`
---------------------------------

### `9.1 Failback Planning`

#### `Failback Decision Criteria`

`Initiate failback when:`

1. `Primary Region Restored`

   * `AWS confirms primary region fully operational`
   * `All services restored and stable`
   * `Network connectivity verified`
2. `Root Cause Resolved`

   * `Issue causing original failover completely resolved`
   * `Preventive measures implemented`
   * `No risk of recurrence`
3. `Business Approval`

   * `Stakeholder approval obtained`
   * `Maintenance window scheduled`
   * `Customer notification completed (if required)`
4. `Technical Readiness`

   * `Primary region infrastructure validated`
   * `Failback procedures tested`
   * `Rollback plan prepared`

### `9.2 Establish Reverse Replication`

#### `Configure DRS for Reverse Replication`


```
#!/bin/bash
# Configure DRS to replicate from DR region back to primary region

CURRENT_ACTIVE_REGION="us-east-2"  # DR region (currently active)
TARGET_REGION="us-east-1"  # Primary region (failback target)
DR_INSTANCE_ID="i-xxxxxxxxx"

echo "=== Configuring Reverse Replication ==="
echo "Source (Current Active): $CURRENT_ACTIVE_REGION"
echo "Target (Failback): $TARGET_REGION"

# 1. Initialize DRS in current DR region
aws drs initialize-service --region $CURRENT_ACTIVE_REGION

# 2. Install DRS agent on current active instance
echo "Install DRS agent on active instance: $DR_INSTANCE_ID"
echo "Run installer with --region $CURRENT_ACTIVE_REGION"

# 3. Verify source server registration
sleep 60
SOURCE_SERVER_ID=$(aws drs describe-source-servers \
  --region $CURRENT_ACTIVE_REGION \
  --query "items[?ec2InstanceID=='$DR_INSTANCE_ID'].sourceServerID" \
  --output text)

echo "Source Server ID: $SOURCE_SERVER_ID"

# 4. Monitor initial replication
while true; do
    REPLICATION_STATE=$(aws drs describe-source-servers \
      --region $CURRENT_ACTIVE_REGION \
      --source-server-ids $SOURCE_SERVER_ID \
      --query "items[0].dataReplicationInfo.dataReplicationState" \
      --output text)
    
    echo "$(date): Replication State: $REPLICATION_STATE"
    
    if [ "$REPLICATION_STATE" == "CONTINUOUS" ]; then
        echo "✓ Replication established"
        break
    fi
    
    sleep 60
done

echo "✓ Reverse replication established successfully"
```


### `9.3 Execute Failback`

#### `Initiate Failback Recovery`


```
#!/bin/bash
# Execute failback to primary region

SOURCE_REGION="us-east-2"  # Current active (DR)
TARGET_REGION="us-east-1"  # Failback target (Primary)
SOURCE_SERVER_ID="s-xxxxxxxxx"
FAILBACK_TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== FAILBACK TO PRIMARY REGION ==="
echo "Timestamp: $(date)"

# 1. Verify replication is current
REPLICATION_STATE=$(aws drs describe-source-servers \
  --region $SOURCE_REGION \
  --source-server-ids $SOURCE_SERVER_ID \
  --query "items[0].dataReplicationInfo.dataReplicationState" \
  --output text)

if [ "$REPLICATION_STATE" != "CONTINUOUS" ]; then
    echo "✗ Replication not in CONTINUOUS state"
    exit 1
fi

# 2. Select latest recovery point
RECOVERY_SNAPSHOT=$(aws drs describe-recovery-snapshots \
  --region $SOURCE_REGION \
  --source-server-id $SOURCE_SERVER_ID \
  --query "items[0].snapshotID" \
  --output text)

# 3. Initiate failback recovery
RECOVERY_JOB=$(aws drs start-recovery \
  --region $SOURCE_REGION \
  --source-servers "[{\"sourceServerID\": \"$SOURCE_SERVER_ID\", \"recoverySnapshotID\": \"$RECOVERY_SNAPSHOT\"}]" \
  --is-drill false \
  --tags Key=RecoveryType,Value=Failback Key=FailbackTimestamp,Value=$FAILBACK_TIMESTAMP \
  --output json)

RECOVERY_JOB_ID=$(echo $RECOVERY_JOB | jq -r '.job.jobID')
echo "Recovery Job ID: $RECOVERY_JOB_ID"

# 4. Monitor recovery progress
while true; do
    RECOVERY_STATE=$(aws drs describe-recovery-instances \
      --region $SOURCE_REGION \
      --filters "sourceServerIDs=$SOURCE_SERVER_ID" \
      --query "items[0].recoveryInstanceProperties.recoveryState" \
      --output text)
    
    echo "$(date): Recovery State: $RECOVERY_STATE"
    
    if [ "$RECOVERY_STATE" == "RECOVERY_COMPLETE" ]; then
        echo "✓ Failback recovery completed"
        break
    fi
    
    sleep 30
done

echo "=== FAILBACK RECOVERY COMPLETE ==="
```


### `9.4 Switch Traffic Back to Primary Region`

#### `Update DNS to Primary Region`


```
#!/bin/bash
# Update DNS to point back to primary region

HOSTED_ZONE_ID="Z1234567890ABC"
SQL_SERVER_DNS="sqlserver.hrp.internal"
PRIMARY_PRIVATE_IP="10.10.2.10"
TTL=60

echo "=== Updating DNS to Primary Region ==="

cat > /tmp/dns-failback.json <
```


### `9.5 Decommission DR Region Resources`

#### `Graceful Shutdown of DR Instance`


```
#!/bin/bash
# Gracefully decommission DR region resources

DR_REGION="us-east-2"
DR_INSTANCE_ID="i-xxxxxxxxx"

echo "=== Decommissioning DR Region Resources ==="

# 1. Create final backup
SNAPSHOT_DESC="Final backup before decommission - $(date +%Y%m%d_%H%M%S)"

aws ec2 create-snapshots \
  --region $DR_REGION \
  --instance-specification InstanceId=$DR_INSTANCE_ID \
  --description "$SNAPSHOT_DESC"

# 2. Stop DR instance
aws ec2 stop-instances \
  --region $DR_REGION \
  --instance-ids $DR_INSTANCE_ID

aws ec2 wait instance-stopped \
  --region $DR_REGION \
  --instance-ids $DR_INSTANCE_ID

# 3. Tag for decommission
aws ec2 create-tags \
  --region $DR_REGION \
  --resources $DR_INSTANCE_ID \
  --tags \
    Key=Status,Value=Decommissioned \
    Key=DecommissionDate,Value=$(date +%Y%m%d) \
    Key=FailbackComplete,Value=true

echo "✓ DR resources prepared for decommission"
```


`10. Monitoring and Alerting`
-----------------------------

### `10.1 CloudWatch Monitoring Setup`

#### `Create CloudWatch Dashboard`


```
#!/bin/bash
# Create CloudWatch dashboard for DRS and SQL Server monitoring

PRIMARY_REGION="us-east-1"
SOURCE_SERVER_ID="s-xxxxxxxxx"
INSTANCE_ID="i-xxxxxxxxx"

# Create dashboard
aws cloudwatch put-dashboard \
  --region $PRIMARY_REGION \
  --dashboard-name "SQL-Server-DRS-Monitoring" \
  --dashboard-body file://drs-dashboard.json

echo "✓ CloudWatch dashboard created"
```


### `10.2 Configure CloudWatch Alarms`

#### `Critical Alarms`

| `Alarm Name` | `Metric` | `Threshold` | `Action` |
| --- | --- | --- | --- |
| `DRS-Replication-Lag-High` | `ReplicationLag` | `> 15 minutes` | `SNS notification to DR team` |
| `DRS-Replication-Not-Continuous` | `ReplicationState` | `!= CONTINUOUS` | `SNS notification to DR team` |
| `SQL-Server-High-CPU` | `CPUUtilization` | `> 80%` | `SNS notification to DBA team` |
| `SQL-Server-High-Disk-Latency` | `VolumeTotalReadTime` | `> 20ms` | `SNS notification to DBA team` |
| `SQL-Server-Memory-Pressure` | `MemoryAvailable` | `< 2 GB` | `SNS notification to DBA team` |

#### `Create Alarms`


```
#!/bin/bash
# Create CloudWatch alarms

PRIMARY_REGION="us-east-1"
SOURCE_SERVER_ID="s-xxxxxxxxx"
INSTANCE_ID="i-xxxxxxxxx"
SNS_TOPIC_ARN="arn:aws:sns:us-east-1:ACCOUNT_ID:drs-alerts"

# DRS Replication Lag Alarm
aws cloudwatch put-metric-alarm \
  --region $PRIMARY_REGION \
  --alarm-name "DRS-Replication-Lag-High" \
  --alarm-description "Alert when DRS replication lag exceeds 15 minutes" \
  --metric-name ReplicationLag \
  --namespace AWS/DRS \
  --statistic Average \
  --period 300 \
  --threshold 900 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions $SNS_TOPIC_ARN \
  --dimensions Name=SourceServerID,Value=$SOURCE_SERVER_ID

# SQL Server CPU Alarm
aws cloudwatch put-metric-alarm \
  --region $PRIMARY_REGION \
  --alarm-name "SQL-Server-High-CPU" \
  --alarm-description "Alert when SQL Server CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 3 \
  --alarm-actions $SNS_TOPIC_ARN \
  --dimensions Name=InstanceId,Value=$INSTANCE_ID

echo "✓ All CloudWatch alarms created successfully"
```


### `10.3 SQL Server Performance Monitoring`

#### `Key Performance Metrics`

| `Metric Category` | `Metrics` | `Normal Range` |
| --- | --- | --- |
| `CPU` | `% Processor Time` | `< 70%` |
| `Memory` | `Available MBytes` `Page Life Expectancy` | `> 2 GB` `> 300 seconds` |
| `Disk I/O` | `Avg Disk Read/Write Latency` `Disk Queue Length` | `< 20ms` `< 2` |
| `SQL Server` | `Batch Requests/sec` `Buffer Cache Hit Ratio` `User Connections` | `Baseline dependent` `> 95%` `Baseline dependent` |
| `Database` | `Transaction Log Usage` `Database Size Growth` | `< 80%` `Monitor trends` |

#### `SQL Server Monitoring Queries`


```
-- Create monitoring stored procedure
CREATE OR ALTER PROCEDURE dbo.usp_MonitorSQLServerHealth
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Database status
    SELECT 
        'DatabaseStatus' AS MetricType,
        name AS DatabaseName,
        state_desc AS State,
        CASE state_desc WHEN 'ONLINE' THEN 1 ELSE 0 END AS IsOnline
    FROM sys.databases
    WHERE database_id > 4;
    
    -- Blocking sessions
    SELECT 
        'BlockingSessions' AS MetricType,
        COUNT(*) AS BlockedSessionCount
    FROM sys.dm_exec_requests
    WHERE blocking_session_id > 0;
    
    -- Long-running queries
    SELECT 
        'LongRunningQueries' AS MetricType,
        COUNT(*) AS LongRunningCount
    FROM sys.dm_exec_requests
    WHERE status = 'running'
      AND DATEDIFF(SECOND, start_time, GETDATE()) > 300;
    
    -- Transaction log usage
    SELECT 
        'TransactionLogUsage' AS MetricType,
        DB_NAME(database_id) AS DatabaseName,
        CAST(used_log_space_in_percent AS DECIMAL(5,2)) AS UsedLogPercent
    FROM sys.dm_db_log_space_usage
    WHERE database_id > 4;
END;
GO
```


### `10.4 DRS Health Check Automation`

#### `Automated Health Check Script`


```
#!/bin/bash
# Automated DRS health check script (run via cron every 5 minutes)

PRIMARY_REGION="us-east-1"
SOURCE_SERVER_ID="s-xxxxxxxxx"
LOG_FILE="/var/log/drs-health-check.log"
ALERT_THRESHOLD_SECONDS=900  # 15 minutes

echo "$(date): Starting DRS health check" >> $LOG_FILE

# Get replication status
REPLICATION_DATA=$(aws drs describe-source-servers \
  --region $PRIMARY_REGION \
  --source-server-ids $SOURCE_SERVER_ID \
  --output json)

REPLICATION_STATE=$(echo $REPLICATION_DATA | jq -r '.items[0].dataReplicationInfo.dataReplicationState')
LAG_DURATION=$(echo $REPLICATION_DATA | jq -r '.items[0].dataReplicationInfo.lagDuration // "PT0S"')

echo "$(date): State=$REPLICATION_STATE, Lag=$LAG_DURATION" >> $LOG_FILE

# Check if replication is healthy
if [ "$REPLICATION_STATE" != "CONTINUOUS" ]; then
    echo "$(date): ALERT - Replication not in CONTINUOUS state" >> $LOG_FILE
    aws sns publish \
      --region $PRIMARY_REGION \
      --topic-arn "arn:aws:sns:$PRIMARY_REGION:ACCOUNT_ID:drs-alerts" \
      --subject "DRS Alert: Replication Not Continuous" \
      --message "DRS replication for $SOURCE_SERVER_ID is in state: $REPLICATION_STATE"
fi

echo "$(date): Health check completed" >> $LOG_FILE
```


`11. Troubleshooting Guide`
---------------------------

### `11.1 Common Issues and Resolutions`

#### `Issue 1: DRS Agent Installation Fails`

`Symptoms:`

* `Agent installer fails with error`
* `Service not starting after installation`
* `Cannot connect to DRS service`

`Diagnosis:`


```
# Check agent logs
Get-Content "C:\Program Files (x86)\AWS Replication Agent\logs\agent.log" -Tail 50

# Check service status
Get-Service -Name "AwsReplicationAgent"

# Test network connectivity
Test-NetConnection -ComputerName "drs.us-east-1.amazonaws.com" -Port 443
```


`Resolution:`

1. `Verify IAM credentials have correct permissions`
2. `Check security group allows outbound HTTPS (port 443)`
3. `Verify NAT Gateway or Internet Gateway configured`
4. `Check Windows Firewall settings`
5. `Reinstall agent with verbose logging`

#### `Issue 2: Replication Stuck in INITIAL_SYNC`

`Symptoms:`

* `Replication state remains in INITIAL_SYNC for extended period`
* `Progress not advancing`
* `High network utilization`

`Resolution:`

1. `Check network bandwidth availability`
2. `Verify no bandwidth throttling configured`
3. `Check for high I/O on source server`
4. `Consider scheduling initial sync during off-peak hours`
5. `If stuck for >24 hours, contact AWS Support`

#### `Issue 3: High Replication Lag`

`Symptoms:`

* `Replication lag exceeds RPO target (15 minutes)`
* `Backlog bytes continuously increasing`
* `Recovery points not being created`

`Diagnosis:`


```
-- Check SQL Server write activity
SELECT 
    DB_NAME(database_id) AS DatabaseName,
    num_of_writes,
    io_stall_write_ms,
    num_of_bytes_written / 1024 / 1024 AS WrittenMB
FROM sys.dm_io_virtual_file_stats(NULL, NULL)
WHERE database_id > 4
ORDER BY num_of_bytes_written DESC;
```


`Resolution:`

1. `Check for high write activity on SQL Server`
2. `Verify network bandwidth sufficient for change rate`
3. `Consider increasing replication server instance type`
4. `Check for long-running transactions`
5. `Optimize SQL Server workload if possible`

#### `Issue 4: Recovery Instance Fails to Start`

`Symptoms:`

* `Recovery job completes but instance not accessible`
* `Instance stuck in "pending" state`
* `Status checks failing`

`Diagnosis:`


```
# Check instance status
aws ec2 describe-instance-status \
  --region us-east-2 \
  --instance-ids $RECOVERY_INSTANCE_ID

# Check system log
aws ec2 get-console-output \
  --region us-east-2 \
  --instance-id $RECOVERY_INSTANCE_ID
```


`Resolution:`

1. `Check EC2 service limits in DR region`
2. `Verify subnet has available IP addresses`
3. `Check security group rules allow necessary traffic`
4. `Review console output for boot errors`
5. `Verify EBS volumes attached correctly`
6. `If persistent, terminate and retry recovery`

#### `Issue 5: SQL Server Databases in RECOVERING State`

`Symptoms:`

* `Databases stuck in RECOVERING state after failover`
* `Cannot access databases`
* `Transaction logs not applying`

`Diagnosis:`


```
-- Check database state
SELECT 
    name,
    state_desc,
    recovery_model_desc,
    log_reuse_wait_desc
FROM sys.databases
WHERE state_desc = 'RECOVERING';

-- Check error log
EXEC xp_readerrorlog 0, 1, N'RECOVERING';
```


`Resolution:`

1. `Wait for recovery to complete (may take time for large databases)`
2. `Check for sufficient disk space for transaction logs`
3. `If stuck, try bringing database online manually:`

   
```
ALTER DATABASE [DatabaseName] SET ONLINE;
```

4. `If corruption suspected, restore from backup`

#### `Issue 6: DNS Not Resolving to DR Region`

`Symptoms:`

* `Applications still connecting to primary region`
* `DNS queries returning old IP address`
* `Failover appears successful but traffic not redirected`

`Diagnosis:`


```
# Check DNS resolution
nslookup sqlserver.hrp.internal

# Check Route 53 record
aws route53 list-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --query "ResourceRecordSets[?Name=='sqlserver.hrp.internal.']"
```


`Resolution:`

1. `Verify Route 53 record updated correctly`
2. `Check TTL value (lower TTL for faster propagation)`
3. `Clear DNS cache on client machines:`

   
```
ipconfig /flushdns
```

4. `Verify health checks passing for DR endpoint`
5. `Consider using weighted routing for gradual cutover`

### `11.2 Emergency Contacts`

#### `Emergency Contact List`

| `Role` | `Contact` | `Phone` | `Email` |
| --- | --- | --- | --- |
| `DR Lead` | `[Name]` | `[Phone]` | `[Email]` |
| `SQL Server DBA` | `[Name]` | `[Phone]` | `[Email]` |
| `Network Team` | `[Name]` | `[Phone]` | `[Email]` |
| `Application Team` | `[Name]` | `[Phone]` | `[Email]` |
| `Operations Manager` | `[Name]` | `[Phone]` | `[Email]` |

#### `AWS Support`

* `Support Portal: https://console.aws.amazon.com/support`
* `Phone: 1-866-243-8852 (US)`
* `Enterprise Support: [Your TAM contact]`

#### `Escalation Path`

1. `Level 1: On-call DBA`
2. `Level 2: DR Lead + Operations Manager`
3. `Level 3: VP of Infrastructure + AWS TAM`
4. `Level 4: CTO + AWS Account Team`

`12. Appendices`
----------------

### `12.1 Glossary`

| `Term` | `Definition` |
| --- | --- |
| `AWS DRS` | `AWS Elastic Disaster Recovery Service - Continuous block-level replication service` |
| `RTO` | `Recovery Time Objective - Maximum acceptable downtime` |
| `RPO` | `Recovery Point Objective - Maximum acceptable data loss` |
| `PIT` | `Point-in-Time - Specific moment for recovery` |
| `Staging Area` | `Low-cost instances in DR region that continuously receive replicated data` |
| `Recovery Instance` | `Full-spec instance launched during DR event from staging data` |
| `Failover` | `Process of switching from primary to DR region` |
| `Failback` | `Process of returning from DR region to primary region` |