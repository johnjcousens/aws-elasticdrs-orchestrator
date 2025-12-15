# HealthEdge AWS Tagging Strategy - Consolidated Guide

**Version:** 2.2  
**Date:** December 15, 2025  
**Status:** Updated with Guiding Care DR Integration (AWSM-1087, AWSM-1100)

---

## Executive Summary

This document is the **source of truth** for HealthEdge's comprehensive AWS tagging strategy, combining business organization, compliance, operational, and disaster recovery requirements into a unified reference. Tags are the building blocks of cloud resource reporting and are functional for auto-scaling, license management, cost allocation, backup management, and DR orchestration.

The DR taxonomy tags (`dr:enabled`, `dr:priority`, `dr:wave`) are designed to support multiple DR orchestration systems across business units including HRP, Guiding Care, Wellframe, and Source. All DR solutions must consume tags as defined in this strategy. Use existing `Service` and `Application` tags for tier-based filtering in Protection Groups.

---

## 1. Tag Categories and Definitions

### 1.1 Business Organization Tags (Mandatory)

| Tag Key | Allowed Values | Description |
|---------|----------------|-------------|
| `BusinessUnit` | Source \| HRP \| GuidingCare \| Wellframe \| Security \| COE \| Infrastructure \| REO | Identifies the business unit owning the resource |
| `CostCenter` | [Cost center code] | Cost center code assigned to each business unit |
| `Owner` | [Email address] | Email of resource owner/team lead |

### 1.2 Environment Classification Tags (Mandatory)

| Tag Key | Allowed Values | Description |
|---------|----------------|-------------|
| `Environment` | Production \| NonProduction \| Development \| Sandbox \| AMSInfrastructure | Environment classification |

### 1.3 Data Classification Tags (Mandatory - Healthcare Critical)

| Tag Key | Allowed Values | Description |
|---------|----------------|-------------|
| `DataClassification` | PHI \| PII \| Clear \| Internal \| Confidential | Data sensitivity level |
| `ComplianceScope` | HIPAA \| SOC2 \| HITRUST \| AllThree \| None | Regulatory compliance requirements |

### 1.4 Operational Management Tags

| Tag Key | Allowed Values | Description |
|---------|----------------|-------------|
| `Customer` | [Customer name] | Customer this resource supports |
| `Application` | [Application name] | Application name this resource supports |
| `Service` | [Service name] | Microservice or component name |
| `Version` | [Version string] | Application/service version |
| `Project` | [Project name] | Project or initiative name |

### 1.5 Technical Classification Tags

| Tag Key | Allowed Values | Description |
|---------|----------------|-------------|
| `ResourceType` | Database \| Compute \| Storage \| Network \| Security \| Monitoring | Resource category |
| `Backup` | 1d14d \| 1h14d \| NotRequired | Backup frequency and retention |
| `Patching` | Automatic \| Manual \| Excluded | Patching strategy |
| `MonitoringLevel` | Critical \| Standard \| Basic \| None | Monitoring tier |

### 1.6 Financial Management Tags

| Tag Key | Allowed Values | Description |
|---------|----------------|-------------|
| `Budget` | [Budget code] | Budget allocation code |
| `ChargebackCode` | [Chargeback ID] | Internal chargeback identifier |
| `PurchaseOrder` | [PO number] | PO number if applicable |

### 1.7 Lifecycle Management Tags

| Tag Key | Allowed Values | Description |
|---------|----------------|-------------|
| `CreatedBy` | [Email or system] | Creator's email or automation system |
| `LastReviewed` | [YYYY-MM-DD] | Last review date |
| `ExpirationDate` | [YYYY-MM-DD] | Expiration for temporary resources |
| `LifecycleStage` | Active \| Deprecated \| Decommissioned | Current lifecycle stage |

### 1.8 Security & Compliance Tags

| Tag Key | Allowed Values | Description |
|---------|----------------|-------------|
| `SecurityZone` | DMZ \| Internal \| Restricted \| Public | Network security zone |
| `EncryptionRequired` | Yes \| No | Encryption requirement |
| `AccessLevel` | Public \| Internal \| Restricted \| Confidential | Access restriction level |
| `AuditScope` | Required \| NotRequired | Audit requirement |

### 1.9 Automation & Operations Tags

| Tag Key | Allowed Values | Description |
|---------|----------------|-------------|
| `AutoStart` | Yes \| No | Auto-start enabled |
| `AutoStop` | Yes \| No | Auto-stop enabled |
| `MaintenanceWindow` | [Day-Time, e.g., Sun-02:00] | Maintenance window |
| `DRS` | True \| False | **DEPRECATED** - Use `dr:enabled` instead. AWS DRS replication enabled |

### 1.10 Disaster Recovery (DR) Taxonomy Tags

> **NEW in v2.0** - Standardized DR tagging taxonomy aligned with the **Guiding Care DR Implementation** (authoritative source).

| Tag Key | Allowed Values | Required | Description |
|---------|----------------|----------|-------------|
| `dr:enabled` | `true` \| `false` | **Yes** (Production EC2) | Identifies resources for DR orchestration. Replaces legacy `DRS` tag. |
| `dr:priority` | `critical` \| `high` \| `medium` \| `low` | **Yes** (DR-enabled) | Recovery priority classification mapping to RTO targets. |
| `dr:wave` | `1` \| `2` \| `3` \| `4` \| `5` (integer) | **Yes** (DR-enabled) | Wave number for ordered recovery execution. |
| `dr:recovery-strategy` | `drs` \| `eks-dns` \| `sql-ag` \| `managed-service` | Optional | Recovery method for the resource. |
| `dr:rto-target` | Integer (minutes) | Optional | Target recovery time objective in minutes. |
| `dr:rpo-target` | Integer (minutes) | Optional | Target recovery point objective in minutes. |

> **Note**: Use existing `Service` and `Application` tags for tier-based filtering. HRP Production uses `Service` tag (values: "Active Directory", "DNS").

#### DR Priority to RTO Mapping (Guiding Care DR Standard)

| dr:priority | RTO Target | Use Case |
|-------------|------------|----------|
| `critical` | 30 minutes | Wave 1 - Databases, core infrastructure |
| `high` | 1 hour | Wave 2 - Application servers |
| `medium` | 2 hours | Wave 3 - Web servers, supporting services |
| `low` | 4 hours | Wave 4+ - Non-critical workloads |

#### DR Tag Usage by System

| Tag | DRS Orchestration | Guiding Care DR | Description |
|-----|-------------------|-----------------|-------------|
| `dr:enabled` | ✅ Required | ✅ Required | Identifies resources for DR orchestration |
| `dr:priority` | ✅ Informational | ✅ RTO-based prioritization | Maps to RTO targets |
| `dr:wave` | ℹ️ Not used (waves in Recovery Plans) | ✅ Tag-driven wave discovery | Wave assignment for tag-driven discovery |
| `dr:recovery-strategy` | ℹ️ Not used | ✅ Recovery method selection | drs, eks-dns, sql-ag, managed-service |
| `dr:rto-target` | ℹ️ Not used | ✅ RTO tracking | Target recovery time in minutes |
| `dr:rpo-target` | ℹ️ Not used | ✅ RPO tracking | Target recovery point in minutes |

#### How DR Tags Work with DRS Orchestration (HRP)

The DRS Orchestration solution uses **Protection Groups** and **Recovery Plans** to manage DR:

1. **Protection Groups** organize servers by:
   - Explicit server selection (SourceServerIds)
   - Tag-based selection (`ServerSelectionTags`) - can filter on ANY tag including `dr:enabled`, `Service`, `Application`, `Customer`, etc.

2. **Recovery Plans** define wave execution order - waves are configured in the plan, NOT via `dr:wave` tags on servers.

3. **RTO/RPO targets** are documented in Recovery Plans. The `dr:priority` tag provides informational classification.

#### How DR Tags Work with Guiding Care DR (Authoritative Source)

Guiding Care DR uses **tag-driven discovery** via AWS Resource Explorer:

1. **`dr:enabled`** - Identifies resources for DR orchestration (required)
2. **`dr:priority`** - Maps to RTO targets for prioritization (required for DR-enabled)
3. **`dr:wave`** - Enables tag-based wave discovery (required for DR-enabled)
4. **`dr:recovery-strategy`** - Specifies recovery method (drs, eks-dns, sql-ag, managed-service)
5. **`dr:rto-target`** / **`dr:rpo-target`** - Explicit RTO/RPO targets in minutes

> **Note**: DRS Orchestration (HRP) ignores `dr:wave` tags - wave order is defined in Recovery Plans. However, applying `dr:wave` tags enables integration with Guiding Care DR's tag-driven discovery.

#### Tag-Based Protection Group Filtering

Use existing `Service` and `Application` tags for tier-based server selection:

| Tag Filter | Description | Example Protection Group Filter |
|------------|-------------|--------------------------------|
| `Service: Active Directory` | AD infrastructure servers | `{"Service": "Active Directory", "Customer": "CustomerA"}` |
| `Service: DNS` | DNS infrastructure servers | `{"Service": "DNS", "Environment": "Production"}` |
| `Application: PatientPortal` | Application-specific servers | `{"Application": "PatientPortal", "dr:enabled": "true"}` |
| `Application: AD` | AD application servers | `{"Application": "AD"}` |

> **Note**: HRP Production uses `Service` tag (values: "Active Directory", "DNS") and `Application` tag (values: "AD", "DNS") for tier-based filtering. These existing tags provide sufficient information for building tiered recovery plans.

### 1.11 Patient Data Handling Tags (Healthcare-Specific)

| Tag Key | Allowed Values | Description |
|---------|----------------|-------------|
| `DataRetention` | 7Years \| 5Years \| 3Years \| 1Year \| 30Days | Data retention period |
| `DataSubject` | Patient \| Provider \| Employee \| Public | Data subject type |

---

## 2. Mandatory Tags by Environment (OU)

### 2.1 Production Workloads

| Category | Tag Key | Mandatory For |
|----------|---------|---------------|
| Business Organization | `BusinessUnit` | All resources |
| Business Organization | `Owner` | All resources |
| Environment | `Environment` | All resources |
| Data Classification | `DataClassification` | All resources |
| Data Classification | `ComplianceScope` | All resources |
| Operational | `Customer` | All resources |
| Operational | `Application` | EC2, EKS, Lambda, ELB, APIGW |
| Operational | `Service` | EC2, EKS, Lambda, ELB, APIGW |
| Operational | `Version` | EC2, EKS, Lambda, ELB, APIGW |
| Operational | `Project` | EC2, EKS, Lambda, ELB, APIGW |
| Lifecycle | `CreatedBy` | S3 |
| Lifecycle | `LastReviewed` | S3 |
| Lifecycle | `ExpirationDate` | S3 |
| Lifecycle | `LifecycleStage` | S3 |
| Automation | `DRS` | EC2 | *(DEPRECATED - use dr:enabled)* |
| **DR Taxonomy** | `dr:enabled` | EC2 |
| Technical | `Backup` | EC2, S3, FSx |

### 2.2 Non-Production Workloads

| Category | Tag Key | Mandatory For |
|----------|---------|---------------|
| Business Organization | `BusinessUnit` | All resources |
| Business Organization | `Owner` | All resources |
| Environment | `Environment` | All resources |
| Data Classification | `DataClassification` | All resources |
| Data Classification | `ComplianceScope` | All resources |
| Operational | `Customer` | All resources |
| Operational | `Application` | EC2, EKS, Lambda, ELB, APIGW |
| Technical | `Backup` | EC2, S3, FSx |
| Lifecycle | `CreatedBy` | S3 |

### 2.3 Development Workloads

| Category | Tag Key | Mandatory For |
|----------|---------|---------------|
| Business Organization | `BusinessUnit` | All resources |
| Business Organization | `Owner` | All resources |
| Environment | `Environment` | All resources |
| Data Classification | `DataClassification` | All resources |
| Data Classification | `ComplianceScope` | All resources |
| Technical | `Backup` | EC2, S3, FSx |

### 2.4 Sandbox Workloads

| Category | Tag Key | Mandatory For |
|----------|---------|---------------|
| Business Organization | `BusinessUnit` | All resources |
| Business Organization | `Owner` | All resources |
| Environment | `Environment` | All resources |
| Data Classification | `DataClassification` | All resources |
| Data Classification | `ComplianceScope` | All resources |

---

## 3. DR Tagging Taxonomy and Migration

### 3.1 DR Tag Migration Plan (DRS → dr:enabled)

> **IMPORTANT**: The legacy `DRS` tag is deprecated per the Guiding Care DR Implementation (authoritative source). Migrate to the new `dr:x` taxonomy by Q1 2026.

#### Migration Timeline

| Phase | Timeline | Actions |
|-------|----------|---------|
| **Phase 1: Dual Tagging** | Now - Jan 31, 2026 | Apply both `DRS` and `dr:enabled` tags to all DR-enrolled resources |
| **Phase 2: Full DR Taxonomy** | Jan 15-31, 2026 | Add `dr:priority` and `dr:wave` tags to all DR-enabled resources |
| **Phase 3: Validation** | Feb 1-15, 2026 | Validate all resources have new `dr:x` tags via AWS Config |
| **Phase 4: Deprecation** | Feb 16-28, 2026 | Remove `DRS` tag enforcement from SCPs |
| **Phase 5: Cleanup** | Mar 1-31, 2026 | Remove legacy `DRS` tags from all resources |

#### Migration Mapping

| Legacy Tag | New Tags | Value Mapping |
|------------|----------|---------------|
| `DRS: True` | `dr:enabled: true` | Direct mapping |
| `DRS: False` | `dr:enabled: false` | Direct mapping |
| (none) | `dr:priority` | Assign based on RTO requirements (critical/high/medium/low) |
| (none) | `dr:wave` | Assign based on recovery order (1-5) |

> **Note**: Use existing `Service` and `Application` tags for tier-based Protection Group filtering. HRP Production uses `Service` tag (values: "Active Directory", "DNS").

### 3.2 DR Tags by Customer and Environment

The DR taxonomy leverages `Customer`, `Environment`, `Service`, and `Application` tags for multi-tenant scoping in Protection Groups:

```
# Example: Production database for CustomerA
Customer: CustomerA
Environment: Production
Application: PatientPortal
Service: Database
dr:enabled: true
```

```
# Example: Non-production app server (no DR)
Customer: CustomerB
Environment: NonProduction
dr:enabled: false
```

#### Protection Group Tag Filtering Examples

Protection Groups use `ServerSelectionTags` to filter DRS source servers:

| ServerSelectionTags | Use Case |
|---------------------|----------|
| `{"dr:enabled": "true", "Customer": "CustomerA"}` | All DR-enrolled servers for CustomerA |
| `{"Service": "Active Directory", "Environment": "Production"}` | All production AD servers |
| `{"Application": "PatientPortal", "dr:enabled": "true"}` | All DR-enrolled PatientPortal servers |
| `{"Customer": "CustomerA", "Service": "DNS"}` | CustomerA DNS servers |

### 3.3 DRS-Specific Tags (Legacy)

> **DEPRECATED**: Use Section 1.10 DR Taxonomy Tags instead.

The `DRS` tag remains supported during the migration period but will be removed in Q2 2026.

| Tag Key | Values | Purpose |
|---------|--------|---------|
| `DRS` | True \| False | *(DEPRECATED)* Indicates if EC2 instance is enrolled in DRS replication |

### 3.4 DRS Tag Synchronization Requirements

When EC2 instances are replicated to a DR region via AWS DRS, the following tags should be synchronized to DRS source servers to enable:
- Protection group filtering by tags
- Automated DR orchestration
- Cost allocation for DR resources

**Tags to Sync to DRS Source Servers:**
- `Name` - Instance friendly name
- `BusinessUnit` - For cost allocation
- `Environment` - For environment identification
- `Application` - For application grouping
- `Customer` - For customer identification
- `DRS` - To confirm DRS enrollment
- `Service` - For protection group filtering (e.g., "Active Directory", "DNS")

### 3.3 Protection Group Tag Filtering

DRS Protection Groups can filter source servers by tags. Common filter patterns using existing tags:

| Tag Filter | Description |
|------------|-------------|
| `Service: Active Directory` | AD infrastructure servers |
| `Service: DNS` | DNS infrastructure servers |
| `Application: PatientPortal` | Application-specific servers |
| `Customer: CustomerA` | Customer-specific servers |

---

## 4. Backup Tagging Strategy

### 4.1 Backup Tag Values

| Tag Key | Values | Description |
|---------|--------|-------------|
| `Backup` | `1h14d` | Hourly backups, 14-day retention |
| `Backup` | `1d14d` | Daily backups, 14-day retention |
| `Backup` | `NotRequired` | No backup required |

### 4.2 Backup Tier Classification

| Backup Tier | Frequency | Retention | Use Case |
|-------------|-----------|-----------|----------|
| Critical | Hourly | 14 days | Production databases, critical apps |
| Standard | Daily | 14 days | Production servers, important data |
| Archive | Weekly | 90 days | Long-term compliance data |
| None | N/A | N/A | Ephemeral/temporary resources |

---

## 5. Migration Strategy Tags (Cloudscape/RISC Networks)

For migration planning and assessment:

| Tag Key | Values | Description |
|---------|--------|-------------|
| `Migration Strategy` | Rehost \| Replatform \| Refactor \| Retire \| Retain | 6R migration strategy |
| `Database Type` | MSSQL \| Oracle \| MySQL \| PostgreSQL | Database engine type |
| `Cloud Criteria` | Cluster \| NFS Mount | Special infrastructure requirements |
| `Migration Wave` | Wave 1 \| Wave 2 \| Wave 3 | Migration wave assignment |
| `Business Disposition` | Retain \| Replace \| Refactor \| Retire | Business decision |

---

## 6. Tag Governance and Enforcement

### 6.1 Enforcement Mechanisms

1. **AWS Organizations Tag Policies** - Validate tag values at the organization level
2. **Service Control Policies (SCPs)** - Deny resource creation without mandatory tags
3. **AWS Config Rules** - Detect and report non-compliant resources (`required-tags` rule)
4. **CDK Pipeline Validation** - Enforce tags during deployment

### 6.2 Provisioning Requirements

- All AWS resources in Workloads OU must be provisioned via CDK
- CDK pipelines assume `CrossAccountDeploymentRole` for provisioning
- Resources missing mandatory tags will be denied creation
- Manual provisioning is only allowed in Sandbox OU

### 6.3 Tag Naming Conventions

- **Tag Keys**: PascalCase (e.g., `BusinessUnit`, `DataClassification`) or lowercase with colons for DR tags (`dr:enabled`)
- **Tag Values**: Standardized values only, no customization
- **New Tags**: Must be approved and added to HealthEdge Tag Types before use

---

## 7. Tag Validation Implementation

> **NEW in v2.0** - SCP and Tag Policy definitions for automated tag validation (AWSM-1100).

### 7.1 Tag Policy for DR Tags

Deploy this tag policy at the Organization level to validate DR tag values (aligned with Guiding Care DR Implementation):

```json
{
  "tags": {
    "dr:enabled": {
      "tag_key": {
        "@@assign": "dr:enabled"
      },
      "tag_value": {
        "@@assign": ["true", "false"]
      },
      "enforced_for": {
        "@@assign": ["ec2:instance"]
      }
    },
    "dr:priority": {
      "tag_key": {
        "@@assign": "dr:priority"
      },
      "tag_value": {
        "@@assign": ["critical", "high", "medium", "low"]
      },
      "enforced_for": {
        "@@assign": ["ec2:instance"]
      }
    },
    "dr:wave": {
      "tag_key": {
        "@@assign": "dr:wave"
      },
      "tag_value": {
        "@@assign": ["1", "2", "3", "4", "5"]
      },
      "enforced_for": {
        "@@assign": ["ec2:instance"]
      }
    },
    "dr:recovery-strategy": {
      "tag_key": {
        "@@assign": "dr:recovery-strategy"
      },
      "tag_value": {
        "@@assign": ["drs", "eks-dns", "sql-ag", "managed-service"]
      },
      "enforced_for": {
        "@@assign": ["ec2:instance"]
      }
    },
    "Environment": {
      "tag_key": {
        "@@assign": "Environment"
      },
      "tag_value": {
        "@@assign": ["Production", "NonProduction", "Development", "Sandbox", "AMSInfrastructure"]
      },
      "enforced_for": {
        "@@assign": ["ec2:instance", "s3:bucket", "rds:db", "lambda:function"]
      }
    }
  }
}
```

### 7.2 SCP for Mandatory DR Tags (Production EC2)

Deploy this SCP to the Production Workloads OU to enforce `dr:enabled` tag on EC2 instances:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyEC2WithoutDREnabled",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "Null": {
          "aws:RequestTag/dr:enabled": "true"
        }
      }
    },
    {
      "Sid": "DenyInvalidDREnabled",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances",
        "ec2:CreateTags"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestTag/dr:enabled": ["true", "false"]
        },
        "Null": {
          "aws:RequestTag/dr:enabled": "false"
        }
      }
    }
  ]
}
```

**Error Message**: When blocked, users see:
```
User: arn:aws:iam::123456789012:user/developer is not authorized to perform: 
ec2:RunInstances on resource: arn:aws:ec2:us-east-1:123456789012:instance/* 
with an explicit deny in a service control policy.

Resolution: Add tag 'dr:enabled' with value 'true' or 'false' to your EC2 instance.
```

### 7.3 SCP for Mandatory Business Tags

Deploy this SCP to enforce core business tags on all supported resources:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyEC2WithoutMandatoryTags",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "Null": {
          "aws:RequestTag/BusinessUnit": "true"
        }
      }
    },
    {
      "Sid": "DenyEC2WithoutEnvironment",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "Null": {
          "aws:RequestTag/Environment": "true"
        }
      }
    },
    {
      "Sid": "DenyEC2WithoutOwner",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "Null": {
          "aws:RequestTag/Owner": "true"
        }
      }
    }
  ]
}
```

### 7.4 AWS Config Rule for Tag Compliance

Deploy this AWS Config rule to detect non-compliant resources:

```yaml
# CloudFormation template for required-tags Config rule
AWSTemplateFormatVersion: '2010-09-09'
Description: AWS Config rule for DR tag compliance

Resources:
  DRTagComplianceRule:
    Type: AWS::Config::ConfigRule
    Properties:
      ConfigRuleName: dr-tag-compliance
      Description: Checks that EC2 instances have required DR tags
      InputParameters:
        tag1Key: dr:enabled
        tag1Value: "true,false"
        tag2Key: Environment
        tag2Value: "Production,NonProduction,Development,Sandbox"
        tag3Key: BusinessUnit
      Scope:
        ComplianceResourceTypes:
          - AWS::EC2::Instance
      Source:
        Owner: AWS
        SourceIdentifier: REQUIRED_TAGS
```

### 7.5 Tag Validation Test Cases

#### Compliant Resource Examples

```bash
# Compliant: Production EC2 with all required tags
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.medium \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=dr:enabled,Value=true},
    {Key=Environment,Value=Production},
    {Key=BusinessUnit,Value=HRP},
    {Key=Owner,Value=team@healthedge.com},
    {Key=Customer,Value=CustomerA}
  ]'
# Result: SUCCESS

# Compliant: Non-production EC2 (dr:enabled=false allowed)
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.small \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=dr:enabled,Value=false},
    {Key=Environment,Value=Development},
    {Key=BusinessUnit,Value=GuidingCare},
    {Key=Owner,Value=dev@healthedge.com}
  ]'
# Result: SUCCESS
```

#### Non-Compliant Resource Examples

```bash
# Non-compliant: Missing dr:enabled tag
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.medium \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=Environment,Value=Production},
    {Key=BusinessUnit,Value=HRP}
  ]'
# Result: DENIED - Missing required tag 'dr:enabled'

# Non-compliant: Invalid dr:enabled value
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.medium \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=dr:enabled,Value=yes},
    {Key=Environment,Value=Production}
  ]'
# Result: DENIED - Invalid value for 'dr:enabled'. Must be 'true' or 'false'

# Non-compliant: Invalid dr:priority value
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.medium \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=dr:enabled,Value=true},
    {Key=dr:priority,Value=urgent}
  ]'
# Result: DENIED - Invalid value for 'dr:priority'. Must be 'critical', 'high', 'medium', or 'low'
```

### 7.6 Deployment Order

1. **Tag Policies** - Deploy first to validate tag values (non-blocking, reports only)
2. **AWS Config Rules** - Deploy to detect and report non-compliant resources
3. **SCPs** - Deploy last after validation period to enforce blocking

---

## 8. Sample Tag Sets

### 8.1 Production Database Server (DR Enabled - Critical)

```
BusinessUnit: HRP
Environment: Production
DataClassification: PHI
ComplianceScope: HIPAA
Customer: CustomerName
Application: PatientPortal
Service: UserDatabase
Owner: hrp-database-team@healthedge.com
Backup: 1h14d
MonitoringLevel: Critical
SecurityZone: Restricted
EncryptionRequired: Yes
dr:enabled: true
dr:priority: critical
dr:wave: 1
dr:recovery-strategy: drs
dr:rto-target: 30
dr:rpo-target: 30
```

### 8.2 Production Web Server (DR Enabled - Medium Priority)

```
BusinessUnit: GuidingCare
Environment: Production
DataClassification: PII
ComplianceScope: HITRUST
Customer: CustomerName
Application: CareManagement
Service: WebFrontend
Owner: guidingcare-team@healthedge.com
Backup: 1d14d
MonitoringLevel: Standard
dr:enabled: true
dr:priority: medium
dr:wave: 3
dr:recovery-strategy: drs
dr:rto-target: 120
dr:rpo-target: 30
```

### 8.3 Production App Server (DR Enabled - High Priority)

```
BusinessUnit: GuidingCare
Environment: Production
DataClassification: PII
ComplianceScope: HITRUST
Customer: CustomerName
Application: CareManagement
Service: APIServer
Owner: guidingcare-team@healthedge.com
Backup: 1d14d
MonitoringLevel: Standard
dr:enabled: true
dr:priority: high
dr:wave: 2
dr:recovery-strategy: drs
dr:rto-target: 60
dr:rpo-target: 30
```

### 8.4 EKS Cluster (DR Enabled - DNS Failover)

```
BusinessUnit: GuidingCare
Environment: Production
DataClassification: PII
ComplianceScope: HITRUST
Customer: CustomerName
Application: CareManagement
Service: EKSCluster
Owner: guidingcare-team@healthedge.com
dr:enabled: true
dr:priority: critical
dr:wave: 1
dr:recovery-strategy: eks-dns
dr:rto-target: 30
```

### 8.5 Development Server (No DR)

```
BusinessUnit: GuidingCare
Environment: Development
DataClassification: Clear
ComplianceScope: None
Application: CareManagement
Service: APIServer
Owner: guidingcare-dev@healthedge.com
AutoStop: Yes
dr:enabled: false
ExpirationDate: 2025-12-31
```

---

## 9. DR Orchestration Ecosystem Integration

### 9.1 Overview

This tagging strategy is the **source of truth** for DR tagging across all HealthEdge business units and DR orchestration systems. The DR taxonomy tags (`dr:enabled`, `dr:priority`, `dr:wave`) combined with existing tags like `Purpose` are designed to support multiple orchestration approaches used by different business units.

### 9.2 Business Unit DR Solutions

| Business Unit | DR Solution | Primary Approach | Tags Used |
|---------------|-------------|------------------|-----------|
| **HRP** | DRS Orchestration | Protection Groups + Recovery Plans | `dr:enabled`, `Service`, `Application`, `Customer` |
| **Guiding Care** | Guiding Care DR (CDK) | Tag-driven discovery via Resource Explorer | `dr:enabled`, `dr:priority`, `dr:wave` |
| **Wellframe** | TBD | TBD | `dr:enabled` (minimum) |
| **Source** | TBD | TBD | `dr:enabled` (minimum) |

### 9.3 Architecture Overview

The DR tagging strategy supports a layered orchestration architecture where multiple systems can consume the same tags:

```
┌─────────────────────────────────────────────────────────────┐
│              HealthEdge DR Tagging Strategy                 │
│                   (This Document - Source of Truth)         │
│  - Defines dr:enabled, dr:priority, dr:wave                 │
│  - Enforced via Tag Policies, SCPs, AWS Config              │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│   Guiding Care DR (CDK)     │ │   DRS Orchestration (CFN)   │
│   - Tag-driven discovery    │ │   - Protection Groups       │
│   - Resource Explorer       │ │   - Recovery Plans          │
│   - dr:priority, dr:wave    │ │   - Service/Application tags │
│   - Bubble test isolation   │ │   - Pause/resume execution  │
└─────────────────────────────┘ └─────────────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS DRS Service                          │
│  - Source server replication                                │
│  - Recovery job execution                                   │
│  - Launch templates and settings                            │
└─────────────────────────────────────────────────────────────┘
```

### 9.4 Tag Consumption by System

| Tag | Guiding Care DR | DRS Orchestration | Description |
|-----|-----------------|-------------------|-------------|
| `dr:enabled` | ✅ Resource discovery | ✅ Protection Group filter | DRS enrollment indicator |
| `Service` | ✅ Resource classification | ✅ Protection Group filter | Service/tier grouping |
| `Application` | ✅ Resource classification | ✅ Protection Group filter | Application grouping |
| `dr:priority` | ✅ RTO-based prioritization | ℹ️ Informational | Maps to RTO targets |
| `dr:wave` | ✅ Tag-driven wave discovery | ℹ️ Not used (uses Recovery Plans) | Wave assignment |
| `Customer` | ✅ Multi-tenant scoping | ✅ Protection Group filter | Customer isolation |
| `Environment` | ✅ Environment filtering | ✅ Protection Group filter | Environment scoping |
| `BusinessUnit` | ✅ BU filtering | ✅ BU filtering | Business unit ownership |

### 9.5 Integration Examples

#### Guiding Care DR: Tag-Driven Discovery

```python
# Guiding Care DR uses AWS Resource Explorer for tag-driven discovery
resources = resource_explorer.search(
    QueryString='tag.key:dr:enabled tag.value:true tag.key:BusinessUnit tag.value:GuidingCare',
    ViewArn=view_arn
)

# Filter by priority for RTO-based ordering
critical_resources = [r for r in resources if r.tags.get('dr:priority') == 'critical']
```

#### DRS Orchestration: Protection Group Filtering

```json
{
  "GroupName": "HRP-CustomerA-AD-Servers",
  "ServerSelectionTags": {
    "dr:enabled": "true",
    "Service": "Active Directory",
    "Customer": "CustomerA",
    "BusinessUnit": "HRP"
  }
}
```

### 9.6 Compatibility Requirements

For seamless integration across all DR systems:

1. **All DR-enrolled EC2 instances MUST have:**
   - `dr:enabled: true` - Required by all systems
   - `BusinessUnit` - Required for BU-level filtering
   - `Customer` - Required for multi-tenant operations
   - `Environment` - Required for environment filtering

2. **Recommended for full ecosystem support:**
   - `Service` - Enables service-based grouping (e.g., "Active Directory", "DNS")
   - `Application` - Enables application-based grouping (e.g., "AD", "DNS", "PatientPortal")
   - `dr:priority` - Enables RTO-based prioritization (Guiding Care DR)
   - `dr:wave` - Enables tag-driven wave discovery (Guiding Care DR)

3. **Tag synchronization:**
   - Tags must be synced to DRS source servers for Protection Group filtering
   - Use DRS Tag Synchronization feature or EventBridge automation

### 9.7 Multi-Region Deployment

Both HRP and Guiding Care support the same regional pairs:

| Primary Region | DR Region | Business Units |
|----------------|-----------|----------------|
| us-east-1 | us-east-2 | HRP, Guiding Care |
| us-west-2 | us-west-1 | HRP, Guiding Care |

Tags are region-agnostic and apply to resources in both primary and DR regions.

---

## 10. Future Enhancements

### 9.1 DRS Tag Synchronization Automation

**Requirement:** Implement automated synchronization of EC2 tags to DRS source servers for cross-region replication scenarios.

**Solution Components:**
1. **EventBridge Rule** - Trigger on DRS source server creation
2. **Lambda Function** - Sync tags from source EC2 to DRS source server
3. **Cross-Region IAM Role** - Allow Lambda to read EC2 tags from source region

**Implementation Priority:** High - Required for DRS protection group filtering

### 9.2 Tag Compliance Dashboard

- Real-time tag compliance monitoring
- Automated remediation for missing tags
- Cost allocation reporting by tag

### 9.3 Tag Policy Automation

- Automated tag policy updates via IaC
- Tag inheritance for nested resources
- Tag-based access control (ABAC) expansion

---

## 11. Data Sources and References

### 11.1 Authoritative Source for DR Taxonomy

| Document | Location | Author | Date |
|----------|----------|--------|------|
| **Guiding Care DR Implementation** | [Confluence CP1/5327028252](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5327028252) | Chris Falk | December 9, 2025 |

The DR tagging taxonomy (`dr:enabled`, `dr:priority`, `dr:wave`, `dr:recovery-strategy`, `dr:rto-target`, `dr:rpo-target`) is defined by the Guiding Care DR Implementation document. This tagging strategy has been updated to align with that authoritative source.

### 11.2 AWS Account Tag Analysis (December 15, 2025)

Current tag state observed via read-only AWS API queries:

| Account | Account ID | Profile | EC2 Count | DRS Tag | dr:enabled Tag | Purpose Tag |
|---------|------------|---------|-----------|---------|----------------|-------------|
| HRP Production | 538127172524 | `538127172524_AWSAdministratorAccess` | 25 | ✅ Yes (24 True, 1 False) | ❌ Not present | ❌ Not present |
| Guiding Care Production | 835807883308 | `835807883308_AWSAdministratorAccess` | 0 (us-east-1) | N/A | N/A | N/A |
| Guiding Care NonProduction | 315237946879 | `315237946879_AWSAdministratorAccess` | 3 | ❌ Not present | ❌ Not present | ❌ Not present |

**Key Findings:**
- HRP Production uses legacy `DRS` tag (24 instances True, 1 False)
- No `dr:enabled` tag exists in any account - migration required
- HRP Production uses `Service` tag (values: "Active Directory", "DNS") instead of `Purpose`
- HRP Production uses `Application` tag (values: "AD", "DNS")

### 11.3 HealthEdge AWS Accounts Reference

| Account Name | Account ID | Email | Purpose |
|--------------|------------|-------|---------|
| Guiding Care Development | 480442107714 | aws+guiding-care-development@healthedge.com | Development |
| Guiding Care NonProduction | 315237946879 | aws+guiding-care-non-production@healthedge.com | QA/Staging |
| Guiding Care Production | 835807883308 | aws+guiding-care-production@healthedge.com | Production |
| Guiding Care Shared Services | 096212910625 | aws+guiding-care-shared-services@healthedge.com | Shared Services |
| HRP Development | 827859360968 | aws+hrp-development@healthedge.com | Development |
| HRP NonProduction | 769064993134 | aws+hrp-vpn-non-production@healthedge.com | QA/Staging |
| HRP Production | 538127172524 | aws+hrp-vpn-production@healthedge.com | Production |
| HRP Shared Services | 211234826829 | aws+hrp-shared-services@healthedge.com | Shared Services |

### 11.4 Confluence Source Documents

| Document | Confluence Page ID | Purpose |
|----------|-------------------|---------|
| Guiding Care DR Implementation | [5327028252](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5327028252) | **Authoritative source** for DR tagging taxonomy |
| AWS Tagging Strategy | [4836950067](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4836950067) | Original tagging strategy |
| Tag Types Reference | [4867035088](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867035088) | Tag key/value definitions |
| Backup Tagging | [4866998899](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866998899) | Backup tag strategy |
| Environment Tags | [4866084104](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866084104) | Environment classification |
| Compliance Tags | [4867032393](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867032393) | HIPAA/HITRUST compliance |
| DRS Tags | [4930863374](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4930863374) | Original DRS tagging |
| Migration Tags | [4939415853](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4939415853) | Migration wave tagging |

### 11.5 AWS Documentation References

- [AWS Tagging Best Practices](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)
- [AWS Organizations Tag Policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_tag-policies.html)
- [AWS Config Required Tags Rule](https://docs.aws.amazon.com/config/latest/developerguide/required-tags.html)
- [AWS Tag Editor](https://docs.aws.amazon.com/ARG/latest/userguide/tag-editor.html)
- [AWS Resource Explorer](https://docs.aws.amazon.com/resource-explorer/latest/userguide/welcome.html)

---

**Document Control:**
- Created: December 15, 2025
- Updated: December 15, 2025 (v2.1 - Aligned with Guiding Care DR authoritative source)
- Data Sources: Guiding Care DR Implementation (Confluence), AWS Account Tag Analysis (read-only queries)
- Confluence Pages: 4836950067, 4867035088, 4866998899, 4866084104, 4867032393, 4930863374, 4939415853, 5327028252
- JIRA: AWSM-1087 (DR Taxonomy), AWSM-1100 (Tag Validation)
