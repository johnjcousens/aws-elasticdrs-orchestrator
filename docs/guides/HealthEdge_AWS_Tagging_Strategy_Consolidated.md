# HealthEdge AWS Tagging Strategy - Consolidated Guide

**Version:** 2.1  
**Date:** December 15, 2025  
**Status:** Updated with Guiding Care DR Integration (AWSM-1087, AWSM-1100)

---

## Executive Summary

This document is the **source of truth** for HealthEdge's comprehensive AWS tagging strategy, combining business organization, compliance, operational, and disaster recovery requirements into a unified reference. Tags are the building blocks of cloud resource reporting and are functional for auto-scaling, license management, cost allocation, backup management, and DR orchestration.

The DR taxonomy tags (`dr:enabled`, `dr:tier`, `dr:priority`, `dr:wave`) are designed to support multiple DR orchestration systems across business units including HRP, Guiding Care, Wellframe, and Source. All DR solutions must consume tags as defined in this strategy.

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

> **NEW in v2.0** - Standardized DR tagging taxonomy for DRS enrollment, Protection Group filtering, and broader DR orchestration ecosystem integration.

| Tag Key | Allowed Values | Required | Description |
|---------|----------------|----------|-------------|
| `dr:enabled` | `true` \| `false` | **Yes** (Production EC2) | Indicates resource is enrolled in DRS replication. Replaces legacy `DRS` tag. |
| `dr:tier` | `database` \| `application` \| `web` \| `infrastructure` | Recommended | Application tier for Protection Group filtering via `ServerSelectionTags`. |
| `dr:priority` | `critical` \| `high` \| `medium` \| `low` | Optional | RTO priority classification for broader DR orchestration and reporting. |
| `dr:wave` | `1` \| `2` \| `3` \| `4` \| `5` (integer) | Optional | Wave assignment for external orchestration systems using tag-driven discovery. |

#### DR Tag Usage by System

| Tag | DRS Orchestration | External Orchestration | Purpose |
|-----|-------------------|------------------------|---------|
| `dr:enabled` | ✅ Required | ✅ Required | DRS enrollment indicator |
| `dr:tier` | ✅ Protection Group filtering | ✅ Resource classification | Application tier grouping |
| `dr:priority` | ℹ️ Informational only | ✅ RTO-based prioritization | Maps to RTO targets |
| `dr:wave` | ℹ️ Not used (waves in Recovery Plans) | ✅ Tag-driven wave discovery | External orchestration wave assignment |

#### How DR Tags Work with DRS Orchestration

The DRS Orchestration solution uses **Protection Groups** and **Recovery Plans** to manage DR:

1. **Protection Groups** organize servers by:
   - Explicit server selection (SourceServerIds)
   - Tag-based selection (`ServerSelectionTags`) - can filter on ANY tag including `dr:tier`, `Customer`, `Application`, etc.

2. **Recovery Plans** define wave execution order - waves are configured in the plan, NOT via tags on servers.

3. **RTO/RPO targets** are business requirements documented in Recovery Plans, not enforced via resource tags.

#### How DR Tags Work with External Orchestration (e.g., Guiding Care DR)

External orchestration systems may use tag-driven discovery via AWS Resource Explorer:

1. **`dr:priority`** - Maps to RTO targets for prioritization:
   - `critical` = 30 min RTO
   - `high` = 1 hour RTO
   - `medium` = 2 hour RTO
   - `low` = 4 hour RTO

2. **`dr:wave`** - Enables tag-based wave discovery for systems that don't use explicit Recovery Plans.

> **Note**: The DRS Orchestration solution ignores `dr:wave` tags - wave order is defined in Recovery Plans. However, applying `dr:wave` tags enables integration with external orchestration systems that use tag-driven discovery.

#### Tag-Based Protection Group Filtering

Use `dr:tier` (or existing tags like `Purpose`, `Application`) for tag-based server selection:

| dr:tier Value | Description | Example Protection Group Filter |
|---------------|-------------|--------------------------------|
| `database` | Database servers (SQL, Oracle, etc.) | `{"dr:tier": "database", "Customer": "CustomerA"}` |
| `application` | Application/API servers | `{"dr:tier": "application", "Environment": "Production"}` |
| `web` | Web/presentation tier | `{"dr:tier": "web"}` |
| `infrastructure` | AD, DNS, core services | `{"dr:tier": "infrastructure"}` |

> **Note**: You can use ANY existing tags for Protection Group filtering. The `dr:tier` tag is optional and provided for consistency. Existing tags like `Purpose`, `Application`, `Customer`, and `Environment` work equally well.

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
| **DR Taxonomy** | `dr:tier` | EC2 (recommended for tag-based Protection Groups) |
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

> **IMPORTANT**: The legacy `DRS` tag is deprecated. Migrate to the new `dr:x` taxonomy by Q1 2026.

#### Migration Timeline

| Phase | Timeline | Actions |
|-------|----------|---------|
| **Phase 1: Dual Tagging** | Now - Jan 31, 2026 | Apply both `DRS` and `dr:enabled` tags to all DR-enrolled resources |
| **Phase 2: Validation** | Feb 1-15, 2026 | Validate all resources have new `dr:x` tags via AWS Config |
| **Phase 3: Deprecation** | Feb 16-28, 2026 | Remove `DRS` tag enforcement from SCPs |
| **Phase 4: Cleanup** | Mar 1-31, 2026 | Remove legacy `DRS` tags from all resources |

#### Migration Mapping

| Legacy Tag | New Tag | Value Mapping |
|------------|---------|---------------|
| `DRS: True` | `dr:enabled: true` | Direct mapping |
| `DRS: False` | `dr:enabled: false` | Direct mapping |
| `Purpose: DatabaseServers` | `dr:tier: database` | Optional - for tag-based Protection Groups |
| `Purpose: AppServers` | `dr:tier: application` | Optional - for tag-based Protection Groups |
| `Purpose: WebServers` | `dr:tier: web` | Optional - for tag-based Protection Groups |

> **Note**: The `Purpose` tag can continue to be used. The `dr:tier` tag is optional and only needed if you want a dedicated DR-specific tier tag for Protection Group filtering.

#### Migration Script Example

```bash
#!/bin/bash
# migrate-drs-tags.sh - Migrate legacy DRS tags to dr:enabled

REGION="${1:-us-east-1}"

# Find all EC2 instances with DRS=True
INSTANCES=$(aws ec2 describe-instances \
  --filters "Name=tag:DRS,Values=True" \
  --query 'Reservations[].Instances[].InstanceId' \
  --output text --region $REGION)

for INSTANCE_ID in $INSTANCES; do
  echo "Migrating tags for $INSTANCE_ID..."
  
  # Add new dr:enabled tag
  aws ec2 create-tags --resources $INSTANCE_ID \
    --tags Key=dr:enabled,Value=true --region $REGION
  
  # Optionally add dr:tier based on Purpose tag
  PURPOSE=$(aws ec2 describe-tags \
    --filters "Name=resource-id,Values=$INSTANCE_ID" "Name=key,Values=Purpose" \
    --query 'Tags[0].Value' --output text --region $REGION)
  
  case $PURPOSE in
    DatabaseServers) TIER=database ;;
    AppServers)      TIER=application ;;
    WebServers)      TIER=web ;;
    *)               TIER="" ;;
  esac
  
  if [ -n "$TIER" ]; then
    aws ec2 create-tags --resources $INSTANCE_ID \
      --tags Key=dr:tier,Value=$TIER --region $REGION
  fi
done
```

### 3.2 DR Tags by Customer and Environment

The DR taxonomy leverages existing `Customer` and `Environment` tags for multi-tenant scoping in Protection Groups:

```
# Example: Production database for CustomerA
Customer: CustomerA
Environment: Production
Application: PatientPortal
dr:enabled: true
dr:tier: database
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
| `{"dr:tier": "database", "Environment": "Production"}` | All production database servers |
| `{"Application": "PatientPortal", "dr:enabled": "true"}` | All DR-enrolled PatientPortal servers |
| `{"Customer": "CustomerA", "dr:tier": "web"}` | CustomerA web tier servers |

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
- `Purpose` - For protection group filtering (AppServers, WebServers, DatabaseServers)

### 3.3 Protection Group Tag Filtering

DRS Protection Groups can filter source servers by tags. Common filter patterns:

| Purpose Tag Value | Description |
|-------------------|-------------|
| `AppServers` | Application tier servers |
| `WebServers` | Web/presentation tier servers |
| `DatabaseServers` | Database tier servers |

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

Deploy this tag policy at the Organization level to validate DR tag values:

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
    "dr:tier": {
      "tag_key": {
        "@@assign": "dr:tier"
      },
      "tag_value": {
        "@@assign": ["database", "application", "web", "infrastructure"]
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

# Non-compliant: Invalid dr:tier value
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.medium \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=dr:enabled,Value=true},
    {Key=dr:tier,Value=servers}
  ]'
# Result: DENIED - Invalid value for 'dr:tier'. Must be 'database', 'application', 'web', or 'infrastructure'
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
dr:tier: database
dr:priority: critical
dr:wave: 1
```

### 8.2 Production Web Server (DR Enabled - High Priority)

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
dr:tier: web
dr:priority: high
dr:wave: 3
```

### 8.3 Production App Server (DR Enabled - Medium Priority)

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
dr:tier: application
dr:priority: medium
dr:wave: 2
```

### 8.4 Development Server (No DR)

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

This tagging strategy is the **source of truth** for DR tagging across all HealthEdge business units and DR orchestration systems. The DR taxonomy tags (`dr:enabled`, `dr:tier`, `dr:priority`, `dr:wave`) are designed to support multiple orchestration approaches used by different business units.

### 9.2 Business Unit DR Solutions

| Business Unit | DR Solution | Primary Approach | Tags Used |
|---------------|-------------|------------------|-----------|
| **HRP** | DRS Orchestration | Protection Groups + Recovery Plans | `dr:enabled`, `dr:tier`, `Customer` |
| **Guiding Care** | Guiding Care DR (CDK) | Tag-driven discovery via Resource Explorer | `dr:enabled`, `dr:priority`, `dr:wave` |
| **Wellframe** | TBD | TBD | `dr:enabled` (minimum) |
| **Source** | TBD | TBD | `dr:enabled` (minimum) |

### 9.3 Architecture Overview

The DR tagging strategy supports a layered orchestration architecture where multiple systems can consume the same tags:

```
┌─────────────────────────────────────────────────────────────┐
│              HealthEdge DR Tagging Strategy                 │
│                   (This Document - Source of Truth)         │
│  - Defines dr:enabled, dr:tier, dr:priority, dr:wave        │
│  - Enforced via Tag Policies, SCPs, AWS Config              │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│   Guiding Care DR (CDK)     │ │   DRS Orchestration (CFN)   │
│   - Tag-driven discovery    │ │   - Protection Groups       │
│   - Resource Explorer       │ │   - Recovery Plans          │
│   - dr:priority, dr:wave    │ │   - dr:tier filtering       │
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

| Tag | Guiding Care DR | DRS Orchestration | Purpose |
|-----|-----------------|-------------------|---------|
| `dr:enabled` | ✅ Resource discovery | ✅ Protection Group filter | DRS enrollment indicator |
| `dr:tier` | ✅ Resource classification | ✅ Protection Group filter | Application tier grouping |
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
  "GroupName": "HRP-CustomerA-Database-Tier",
  "ServerSelectionTags": {
    "dr:enabled": "true",
    "dr:tier": "database",
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
   - `dr:tier` - Enables tier-based grouping (both systems)
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

## 10. References

- [AWS Tagging Best Practices](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)
- [AWS Organizations Tag Policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_tag-policies.html)
- [AWS Config Required Tags Rule](https://docs.aws.amazon.com/config/latest/developerguide/required-tags.html)
- [AWS Tag Editor](https://docs.aws.amazon.com/ARG/latest/userguide/tag-editor.html)

---

**Document Control:**
- Created: December 15, 2025
- Updated: December 15, 2025 (v2.1 - Guiding Care DR Integration)
- Source: Confluence pages 4836950067, 4867035088, 4866998899, 4866084104, 4867032393, 4930863374, 4939415853, 5327028252
- JIRA: AWSM-1087 (DR Taxonomy), AWSM-1100 (Tag Validation)
