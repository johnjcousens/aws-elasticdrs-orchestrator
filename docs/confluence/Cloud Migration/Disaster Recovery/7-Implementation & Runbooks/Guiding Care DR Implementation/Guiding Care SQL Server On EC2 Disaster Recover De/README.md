# Guiding Care SQL Server On EC2 Disaster Recover Detailed Design and Runbook

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5171216582/Guiding%20Care%20SQL%20Server%20On%20EC2%20Disaster%20Recover%20Detailed%20Design%20and%20Runbook

**Created by:** Venkata Kommuri on October 15, 2025  
**Last modified by:** Chris Falk on December 18, 2025 at 08:06 PM

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Technology:** SQL Server 2019/2022 Always On Availability Groups  
**Target RTO:** 4 hours | **Target RPO:** 15 minutes  
**Primary Regions:** US-East-1 (Virginia), US-West-2 (Oregon)  
**DR Regions:** US-East-2 (Ohio), US-West-1 (N. California)  
**DR Method:** SQL Server Always On Availability Groups with Cross-Region Asynchronous Replication

**GUIDING CARE HEALTHCARE ENVIRONMENT:** This runbook is specifically designed for the Guiding Care healthcare application environment with SQL Server Always On Availability Groups supporting critical patient data, provider information, and healthcare workflows requiring HIPAA compliance and 99.95% uptime SLA.

#### ⚠️ IMPORTANT DISCLAIMER - GUIDING CARE CUSTOMIZATION REQUIRED

**All scripts and configurations in this runbook are TEMPLATES and must be customized for Guiding Care-specific requirements before implementation.**

##### Required Guiding Care-Specific Customizations:

* **Environment Variables:** Update all placeholder values with actual Guiding Care AWS account IDs, region configurations, and resource identifiers
* **Network Configuration:** Replace VPC IDs, subnet IDs, and security group IDs with Guiding Care-specific network resources
* **SQL Server Configuration:** Modify database names, Always On AG names, and paths to match Guiding Care SQL Server installations (~50 dedicated instances per customer)
* **Healthcare Compliance:** Ensure all configurations meet HIPAA, SOC 2, and healthcare regulatory requirements
* **Customer Isolation:** Implement per-customer database isolation and security controls as required by Guiding Care multi-tenant architecture
* **Monitoring and Alerting:** Configure SNS topics, CloudWatch alarms, and notification endpoints for Guiding Care healthcare operations team
* **Backup and Recovery:** Align backup schedules (Weekly full, Nightly differential, Hourly transaction logs) with Guiding Care data governance requirements

Table of Contents
-----------------

* [1. SQL Server Always On Multi-Region DR Overview](#)
* [2. Guiding Care Specific Requirements Analysis](#)
* [3. Multi-Region Always On Architecture](#)
* [4. Prerequisites & Planning](#)
* [5. Cross-Region Network Setup](#)
* [6. Windows Server Failover Clustering Configuration](#)
* [7. Always On Availability Groups Setup](#)
* [8. Cross-Region Asynchronous Replication](#)
* [9. Listener and DNS Configuration](#)
* [10. Backup and Recovery Strategy](#)
* [11. Monitoring & Health Checks](#)
* [12. Failover Procedures](#)
* [13. Failback Procedures](#)
* [14. DR Testing & Validation](#)
* [15. Automation Scripts](#)
* [16. Maintenance & Operations](#)
* [17. Troubleshooting Guide](#)
* [18. Best Practices for Healthcare](#)

1. SQL Server Always On Multi-Region DR Overview
------------------------------------------------

### 1.1 Guiding Care Healthcare Environment Context

The Guiding Care healthcare application relies on SQL Server Always On Availability Groups to provide high availability and disaster recovery for critical patient data, provider information, claims processing, and regulatory reporting. This runbook provides a comprehensive implementation guide for multi-region disaster recovery using native SQL Server Always On capabilities across AWS regions.

#### Current Guiding Care SQL Server Environment:

* **Database Servers:** dedicated SQL Server instances for some customer and shared instances
* **Current Setup:** Always On Availability Groups with synchronous commit within data centers
* **Customer Distribution:** 75% East Coast (Reston/IAD3), 25% West Coast (LA/LX3)
* **Database Sizes:** 100GB to 2TB per customer database
* **Transaction Volume:** High-volume OLTP with healthcare workflows
* **Current Backup:** Weekly full, nightly differential, hourly transaction logs
* **Current DR Gap:** No automated cross-site failover, longer recovery time
* ***OLTP cluster, Standalone Server ( Replicated readonly)***

### 1.2 Target Multi-Region Architecture

#### Guiding Care SQL Server Always On Multi-Region DR Architecture

Note: No DR required for replicated standalone servers (Readonly) as per previous discussions with GC team.

| ***For Top 5 Tier 1 customer production database (OLTP cluster)***  ***primary region: 2 nodes (on different AZ) + DR region: 2 nodes (on different AZ)***   image-20251024-202758.png ***For all other customer production database (OLTP cluster)***  primary region: 2 nodes (on different AZ) + DR region: 1 node   image-20251024-202837.png |
| --- |


```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                    SQL SERVER ALWAYS ON MULTI-REGION DISASTER RECOVERY                          │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                 │
│   │
│  REPLICATION CHARACTERISTICS:                     FAILOVER CHARACTERISTICS:                    │
│  - Within Region: Synchronous (0 data loss)      - RTO Target: 4 hours                        │
│  - Cross-Region: Asynchronous (15-min RPO)       - RPO Target: 15 minutes                     │
│  - Automatic failover within region              - Manual failover to DR region                │
│  - Manual failover to DR region                  - DNS update required                         │
│  - Continuous transaction log shipping           - Application reconnection                    │
│                                                                                                 │
│  HEALTHCARE COMPLIANCE:                           MONITORING & ALERTING:                        │
│  - HIPAA encryption at rest and in transit       - CloudWatch metrics                          │
│  - Audit logging via CloudTrail                  - SQL Server health monitoring                │
│  - Customer data isolation                       - Replication lag alerts                      │
│  - 60-day backup retention                       - 24/7 operations team notifications          │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
            
```


2. Guiding Care Specific Requirements Analysis
----------------------------------------------

### 2.1 Business Requirements from Guiding Care Documents

| Requirement Category | Current State | Target State | Implementation Approach |
| --- | --- | --- | --- |
| Recovery Time Objective (RTO) | Weeks to months (manual rebuild) | 4 hours maximum | Automated Always On failover with pre-configured DR replicas |
| Recovery Point Objective (RPO) | Hourly transaction logs | 15 minutes maximum | Asynchronous replication with continuous log shipping |
| Availability SLA | No formal SLA | 99.95% uptime | Multi-region Always On with automatic local failover |
| SLA Penalty | 10% monthly fees for breaches | Eliminate 90% of penalties | Automated DR with tested procedures |
| Customer Distribution | 75% East, 25% West | Maintain distribution | Region-specific AG configurations |
| Database Instances | ~50 per customer | Consolidated where possible | Multi-database AG groups per customer |
| Backup Strategy | Weekly full, nightly diff, hourly logs | Maintain + cross-region backup | Automated backups with S3 cross-region replication |
| Healthcare Compliance | HIPAA compliant | Maintain HIPAA + SOC 2 | Encryption, audit logging, access controls |

### 2.2 Technical Requirements

#### Guiding Care SQL Server Always On Requirements:

* ☐ SQL Server 2019/2022 Enterprise Edition (Always On requires Enterprise)
* ☐ Windows Server 2022 for all nodes
* ☐ Windows Server Failover Clustering (WSFC) across regions
* ☐ Minimum 3 replicas per AG (2 synchronous in primary region, 1 asynchronous in DR region)
* ☐ Dedicated network connectivity (AWS Direct Connect or VPN) between regions
* ☐ Minimum 10Gbps bandwidth for cross-region replication
* ☐ Network latency <50ms for optimal performance
* ☐ Separate subnets for SQL Server traffic
* ☐ Encrypted communication (TLS 1.2+) for all SQL traffic
* ☐ Customer-managed KMS keys for data encryption at rest
* ☐ CloudWatch monitoring integration
* ☐ Active Directory for DNS failover
* ☐ S3 for cross-region backup storage using s3 replication

3. Multi-Region Always On Architecture
--------------------------------------

### 3.1 Regional Deployment Strategy

#### Guiding Care Regional Architecture:

**East Coast Customers (75% of customer base):**

* **Primary Region:** US-East-1 (Virginia) - 2-node Always On cluster
* **DR Region:** US-East-2 (Ohio) - 1-node asynchronous replica
* **Replication:** Synchronous within US-East-1, Asynchronous to US-East-2

**West Coast Customers (25% of customer base):**

* **Primary Region:** US-West-2 (Oregon) - 2-node Always On cluster
* **DR Region:** US-West-1 (N. California) - 1-node asynchronous replica
* **Replication:** Synchronous within US-West-2, Asynchronous to US-West-1

### 3.2 Always On Availability Group Configuration

| Component | Primary Region Configuration | DR Region Configuration |
| --- | --- | --- |
| Primary Replica | Node 1 in AZ-a Synchronous commit Automatic failover Read-write access | N/A (becomes primary during failover) |
| Secondary Replica 1 | Node 2 in AZ-b Synchronous commit Automatic failover Read-only routing | N/A |
| DR Replica | N/A | Node 1 in DR region Asynchronous commit Manual failover Read-only routing (optional) |
| File share Witness Server | File share witness in AZ-a Quorum voting member. Fsx Netapp volume | Optional witness for DR testing ( If cluster exists)  File share witness in AZ-a Quorum voting member. Fsx Netapp volume |
| Listener | Virtual IP in primary region Port 1433 Multi-subnet configuration | Separate listener for DR region Activated during failover |

### 3.3 Instance Sizing for Guiding Care

Instance configuration has to match with on-premises servers as per Guiding Care DBAs.

| Server Role | Instance Type | vCPU | Memory | Storage | Network |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

4. Prerequisites & Planning
---------------------------

### 4.1 Software Requirements

#### Required Software Components:

* ☐ Windows Server 2022 Datacenter Edition (all nodes)
* ☐ SQL Server 2019 Enterprise Edition (Always On requires Enterprise)
* ☐ Latest Windows Server updates and patches
* ☐ Latest SQL Server Cumulative Updates
* ☐ .NET Framework 4.8 or later
* ☐ PowerShell 5.1 or later
* ☐ SQL Server Management Studio (SSMS) 19.0 or later
* ☐ AWS CLI v2
* ☐ AWS Systems Manager Agent
* ☐ CloudWatch Agent for Windows

### 4.2 Licensing Considerations

#### SQL Server Enterprise Licensing for HealthEdge :

Please refer to <https://healthedgetrial.sharepoint.com/:p:/r/sites/AWSCloudMigration/_layouts/15/Doc.aspx?sourcedoc=%7B47D4D8B5-B9E8-4D8B-89F6-F2FC6ABC247F%7D&file=Evolve-OLA-HealthEdge%20v1_4.pptx&action=edit&mobileredirect=true>

### 4.3 Network Prerequisites

Please refer to network design   
5.2 Network Data Flows

wide1800

### 4.4 Storage Configuration

Storage has to match with on-premises servers as per Guiding Care DBAs.

| Volume Type | Purpose | Size | EBS Type | IOPS | Throughput |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

### 4.5 Pre-Implementation Assessment Script


```
# PowerShell script to assess Guiding Care environment readiness
# File: Assess-GuidingCareSQLAlwaysOnReadiness.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$CustomerName,
    
    [string]$PrimaryRegion = "us-east-1",
    [string]$DRRegion = "us-east-2",
    [string]$OutputPath = "C:\GuidingCare\Assessment"
)

# Create output directory
if (!(Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force
}

$AssessmentResults = @{}
$Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$ReportFile = "$OutputPath\AlwaysOn_Readiness_Assessment_$CustomerName_$Timestamp.html"

Write-Host "Starting Guiding Care SQL Server Always On Readiness Assessment" -ForegroundColor Cyan
Write-Host "Customer: $CustomerName" -ForegroundColor Cyan
Write-Host "Primary Region: $PrimaryRegion, DR Region: $DRRegion" -ForegroundColor Cyan

# 1. Check Windows Server Version
Write-Host "`n[1/10] Checking Windows Server version..." -ForegroundColor Yellow
$OSInfo = Get-WmiObject -Class Win32_OperatingSystem
$AssessmentResults.WindowsVersion = @{
    Caption = $OSInfo.Caption
    Version = $OSInfo.Version
    BuildNumber = $OSInfo.BuildNumber
    Status = if ($OSInfo.Caption -like "*2022*" -or $OSInfo.Caption -like "*2019*") { "PASS" } else { "FAIL" }
    Recommendation = if ($OSInfo.Caption -like "*2022*" -or $OSInfo.Caption -like "*2019*") { "Windows Server version is compatible" } else { "Upgrade to Windows Server 2019 or 2022" }
}

# 2. Check SQL Server Version and Edition
Write-Host "[2/10] Checking SQL Server version and edition..." -ForegroundColor Yellow
try {
    $SQLVersion = Invoke-Sqlcmd -Query "SELECT @@VERSION as Version, SERVERPROPERTY('Edition') as Edition, SERVERPROPERTY('ProductLevel') as ProductLevel" -ServerInstance "localhost"
    $IsEnterprise = $SQLVersion.Edition -like "*Enterprise*"
    
    $AssessmentResults.SQLServer = @{
        Version = $SQLVersion.Version
        Edition = $SQLVersion.Edition
        ProductLevel = $SQLVersion.ProductLevel
        Status = if ($IsEnterprise) { "PASS" } else { "FAIL" }
        Recommendation = if ($IsEnterprise) { "SQL Server Enterprise Edition detected - Always On supported" } else { "Always On requires SQL Server Enterprise Edition - upgrade required" }
    }
} catch {
    $AssessmentResults.SQLServer = @{
        Status = "ERROR"
        Error = $_.Exception.Message
        Recommendation = "SQL Server not accessible or not installed"
    }
}

# 3. Check Failover Clustering Feature
Write-Host "[3/10] Checking Failover Clustering feature..." -ForegroundColor Yellow
$ClusterFeature = Get-WindowsFeature -Name "Failover-Clustering"
$AssessmentResults.FailoverClustering = @{
    Installed = $ClusterFeature.Installed
    Status = if ($ClusterFeature.Installed) { "PASS" } else { "WARN" }
    Recommendation = if ($ClusterFeature.Installed) { "Failover Clustering feature is installed" } else { "Install Failover Clustering feature: Install-WindowsFeature -Name Failover-Clustering -IncludeManagementTools" }
}

# 4. Check Network Connectivity
Write-Host "[4/10] Checking network connectivity..." -ForegroundColor Yellow
$NetworkTests = @()

# Test connectivity to AWS endpoints
$AWSEndpoints = @(
    "ec2.$PrimaryRegion.amazonaws.com",
    "ec2.$DRRegion.amazonaws.com",
    "s3.$PrimaryRegion.amazonaws.com"
)

foreach ($Endpoint in $AWSEndpoints) {
    $TestResult = Test-NetConnection -ComputerName $Endpoint -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
    $NetworkTests += @{
        Endpoint = $Endpoint
        Reachable = $TestResult
    }
}

$AllReachable = ($NetworkTests | Where-Object { -not $_.Reachable }).Count -eq 0
$AssessmentResults.NetworkConnectivity = @{
    Tests = $NetworkTests
    Status = if ($AllReachable) { "PASS" } else { "FAIL" }
    Recommendation = if ($AllReachable) { "All AWS endpoints are reachable" } else { "Check network connectivity and firewall rules" }
}

# 5. Check Available Disk Space
Write-Host "[5/10] Checking disk space..." -ForegroundColor Yellow
$Disks = Get-WmiObject -Class Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 }
$DiskInfo = @()
foreach ($Disk in $Disks) {
    $FreeSpaceGB = [math]::Round($Disk.FreeSpace / 1GB, 2)
    $TotalSpaceGB = [math]::Round($Disk.Size / 1GB, 2)
    $PercentFree = [math]::Round(($Disk.FreeSpace / $Disk.Size) * 100, 2)
    
    $DiskInfo += @{
        Drive = $Disk.DeviceID
        TotalGB = $TotalSpaceGB
        FreeGB = $FreeSpaceGB
        PercentFree = $PercentFree
        Status = if ($PercentFree -gt 20) { "PASS" } else { "WARN" }
    }
}

$AssessmentResults.DiskSpace = @{
    Disks = $DiskInfo
    Status = if (($DiskInfo | Where-Object { $_.Status -eq "WARN" }).Count -eq 0) { "PASS" } else { "WARN" }
    Recommendation = "Ensure adequate disk space for database growth and backups"
}

# 6. Check Memory Configuration
Write-Host "[6/10] Checking memory configuration..." -ForegroundColor Yellow
$TotalMemoryGB = [math]::Round((Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
$RecommendedMemory = 64  # Minimum recommended for production SQL Server

$AssessmentResults.Memory = @{
    TotalMemoryGB = $TotalMemoryGB
    RecommendedGB = $RecommendedMemory
    Status = if ($TotalMemoryGB -ge $RecommendedMemory) { "PASS" } else { "WARN" }
    Recommendation = if ($TotalMemoryGB -ge $RecommendedMemory) { "Memory configuration is adequate" } else { "Consider increasing memory to at least $RecommendedMemory GB for production workloads" }
}

# 7. Check CPU Configuration
Write-Host "[7/10] Checking CPU configuration..." -ForegroundColor Yellow
$CPUInfo = Get-WmiObject -Class Win32_Processor
$TotalCores = ($CPUInfo | Measure-Object -Property NumberOfCores -Sum).Sum
$TotalLogicalProcessors = ($CPUInfo | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum

$AssessmentResults.CPU = @{
    TotalCores = $TotalCores
    TotalLogicalProcessors = $TotalLogicalProcessors
    Status = if ($TotalCores -ge 8) { "PASS" } else { "WARN" }
    Recommendation = if ($TotalCores -ge 8) { "CPU configuration is adequate" } else { "Consider increasing to at least 8 cores for production workloads" }
}

# 8. Check SQL Server Configuration
Write-Host "[8/10] Checking SQL Server configuration..." -ForegroundColor Yellow
try {
    $SQLConfig = Invoke-Sqlcmd -Query @"
        SELECT 
            SERVERPROPERTY('IsHadrEnabled') as IsHadrEnabled,
            SERVERPROPERTY('HadrManagerStatus') as HadrManagerStatus,
            SERVERPROPERTY('IsClustered') as IsClustered
"@ -ServerInstance "localhost"
    
    $AssessmentResults.SQLConfiguration = @{
        IsHadrEnabled = $SQLConfig.IsHadrEnabled
        HadrManagerStatus = $SQLConfig.HadrManagerStatus
        IsClustered = $SQLConfig.IsClustered
        Status = "INFO"
        Recommendation = if ($SQLConfig.IsHadrEnabled -eq 1) { "Always On is already enabled" } else { "Always On needs to be enabled after WSFC setup" }
    }
} catch {
    $AssessmentResults.SQLConfiguration = @{
        Status = "ERROR"
        Error = $_.Exception.Message
    }
}

# 9. Check Database Recovery Model
Write-Host "[9/10] Checking database recovery models..." -ForegroundColor Yellow
try {
    $Databases = Invoke-Sqlcmd -Query "SELECT name, recovery_model_desc, state_desc FROM sys.databases WHERE name LIKE '$CustomerName%'" -ServerInstance "localhost"
    
    $NonFullRecovery = $Databases | Where-Object { $_.recovery_model_desc -ne "FULL" }
    
    $AssessmentResults.DatabaseRecoveryModel = @{
        TotalDatabases = $Databases.Count
        NonFullRecovery = $NonFullRecovery.Count
        Status = if ($NonFullRecovery.Count -eq 0) { "PASS" } else { "WARN" }
        Recommendation = if ($NonFullRecovery.Count -eq 0) { "All databases are in FULL recovery model" } else { "Set all databases to FULL recovery model for Always On: ALTER DATABASE [dbname] SET RECOVERY FULL" }
    }
} catch {
    $AssessmentResults.DatabaseRecoveryModel = @{
        Status = "ERROR"
        Error = $_.Exception.Message
    }
}

# 10. Check Backup Status
Write-Host "[10/10] Checking backup status..." -ForegroundColor Yellow
try {
    $BackupStatus = Invoke-Sqlcmd -Query @"
        SELECT 
            d.name as DatabaseName,
            MAX(b.backup_finish_date) as LastBackupDate,
            DATEDIFF(hour, MAX(b.backup_finish_date), GETDATE()) as HoursSinceLastBackup
        FROM sys.databases d
        LEFT JOIN msdb.dbo.backupset b ON d.name = b.database_name
        WHERE d.name LIKE '$CustomerName%'
        GROUP BY d.name
"@ -ServerInstance "localhost"
    
    $OldBackups = $BackupStatus | Where-Object { $_.HoursSinceLastBackup -gt 24 -or $_.LastBackupDate -eq $null }
    
    $AssessmentResults.BackupStatus = @{
        TotalDatabases = $BackupStatus.Count
        OldBackups = $OldBackups.Count
        Status = if ($OldBackups.Count -eq 0) { "PASS" } else { "WARN" }
        Recommendation = if ($OldBackups.Count -eq 0) { "All databases have recent backups" } else { "Ensure all databases have backups within 24 hours" }
    }
} catch {
    $AssessmentResults.BackupStatus = @{
        Status = "ERROR"
        Error = $_.Exception.Message
    }
}

# Generate HTML Report
Write-Host "`nGenerating assessment report..." -ForegroundColor Cyan

$HtmlReport = @"



    
    


    
```


`Guiding Care SQL Server Always On Readiness Assessment`
========================================================

`Customer: $CustomerName | Generated: $(Get-Date)`

`Assessment Summary`
--------------------

`This report provides a comprehensive assessment of the Guiding Care SQL Server environment for Always On Availability Groups implementation.`

5. Cross-Region Network Setup
-----------------------------

### 5.1 VPC and Subnet Configuration

Please refer to network design   
5.2 Network Data Flows

### 5.2 Transit Gateway Configuration for Cross-Region Connectivity

Please refer to network design   
5.2 Network Data Flows

6. Windows Server Failover Clustering Configuration
---------------------------------------------------

### 6.1 Install Failover Clustering Feature

Please Refer to Server migration document

### 6.2 Configure Cross-Region Cluster Nodes

#### Important: Multi-Region WSFC Considerations

Note : Migration team will configure the cluster nodes as part of the migration process.

Windows Server Failover Clustering across AWS regions requires special configuration.