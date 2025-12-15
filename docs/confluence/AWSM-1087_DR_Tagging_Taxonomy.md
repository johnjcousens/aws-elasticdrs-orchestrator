# DR Tagging Taxonomy for AWS DRS Orchestration

**JIRA:** [AWSM-1087](https://healthedge.atlassian.net/browse/AWSM-1087)  
**Version:** 1.0  
**Date:** December 15, 2025  
**Status:** Ready for Implementation

---

## Executive Summary

This document defines the standardized DR tagging taxonomy for HealthEdge AWS resources, aligned with the **Guiding Care DR Implementation** (authoritative source). The taxonomy enables consistent disaster recovery orchestration across all business units (HRP, Guiding Care, Wellframe, Source).

---

## 1. DR Taxonomy Tags

### 1.1 Required Tags (Production EC2)

| Tag Key | Allowed Values | Required | Description |
|---------|----------------|----------|-------------|
| `dr:enabled` | `true` \| `false` | **Yes** | Identifies resources for DR orchestration. Replaces legacy `DRS` tag. |
| `dr:priority` | `critical` \| `high` \| `medium` \| `low` | **Yes** (DR-enabled) | Recovery priority classification mapping to RTO targets. |
| `dr:wave` | `1` \| `2` \| `3` \| `4` \| `5` | **Yes** (DR-enabled) | Wave number for ordered recovery execution. |

### 1.2 Optional Tags

| Tag Key | Allowed Values | Description |
|---------|----------------|-------------|
| `dr:recovery-strategy` | `drs` \| `eks-dns` \| `sql-ag` \| `managed-service` | Recovery method for the resource. |
| `dr:rto-target` | Integer (minutes) | Target recovery time objective in minutes. |
| `dr:rpo-target` | Integer (minutes) | Target recovery point objective in minutes. |

### 1.3 Existing Tags for Tier Classification

Use the existing `Purpose` tag for application tier classification:

| Purpose Value | Description | Typical Wave |
|---------------|-------------|--------------|
| `DatabaseServers` | Database servers (SQL, Oracle, etc.) | Wave 1 |
| `AppServers` | Application/API servers | Wave 2 |
| `WebServers` | Web/presentation tier | Wave 3 |

> **Note:** No new `dr:tier` tag is needed - use existing `Purpose` tag.

---

## 2. DR Priority to RTO Mapping

| dr:priority | RTO Target | Use Case |
|-------------|------------|----------|
| `critical` | 30 minutes | Wave 1 - Databases, core infrastructure |
| `high` | 1 hour | Wave 2 - Application servers |
| `medium` | 2 hours | Wave 3 - Web servers, supporting services |
| `low` | 4 hours | Wave 4+ - Non-critical workloads |

---

## 3. Tag Usage by DR System

| Tag | DRS Orchestration (HRP) | Guiding Care DR | Purpose |
|-----|-------------------------|-----------------|---------|
| `dr:enabled` | ✅ Required | ✅ Required | Identifies DR-enrolled resources |
| `dr:priority` | ✅ Informational | ✅ RTO-based prioritization | Maps to RTO targets |
| `dr:wave` | ℹ️ Not used (uses Recovery Plans) | ✅ Tag-driven wave discovery | Wave assignment |
| `dr:recovery-strategy` | ℹ️ Not used | ✅ Recovery method selection | drs, eks-dns, sql-ag, managed-service |
| `Purpose` | ✅ Protection Group filtering | ✅ Resource classification | Application tier grouping |
| `Customer` | ✅ Protection Group filtering | ✅ Multi-tenant scoping | Customer isolation |

---

## 4. Migration Plan (DRS → dr:enabled)

### 4.1 Timeline

| Phase | Timeline | Actions |
|-------|----------|---------|
| **Phase 1: Dual Tagging** | Now - Jan 31, 2026 | Apply both `DRS` and `dr:enabled` tags |
| **Phase 2: Full DR Taxonomy** | Jan 15-31, 2026 | Add `dr:priority` and `dr:wave` tags |
| **Phase 3: Validation** | Feb 1-15, 2026 | Validate via AWS Config |
| **Phase 4: Deprecation** | Feb 16-28, 2026 | Remove `DRS` tag enforcement |
| **Phase 5: Cleanup** | Mar 1-31, 2026 | Remove legacy `DRS` tags |

### 4.2 Migration Mapping

| Legacy Tag | New Tags | Value Mapping |
|------------|----------|---------------|
| `DRS: True` | `dr:enabled: true` | Direct mapping |
| `DRS: False` | `dr:enabled: false` | Direct mapping |
| (none) | `dr:priority` | Assign based on RTO (critical/high/medium/low) |
| (none) | `dr:wave` | Assign based on recovery order (1-5) |

### 4.3 Migration Script

```bash
#!/bin/bash
# migrate-drs-tags.sh - Migrate legacy DRS tags to dr:x taxonomy

REGION="${1:-us-east-1}"
DEFAULT_PRIORITY="${2:-medium}"
DEFAULT_WAVE="${3:-2}"

# Find all EC2 instances with DRS=True
INSTANCES=$(aws ec2 describe-instances \
  --filters "Name=tag:DRS,Values=True" \
  --query 'Reservations[].Instances[].InstanceId' \
  --output text --region $REGION)

for INSTANCE_ID in $INSTANCES; do
  echo "Migrating tags for $INSTANCE_ID..."
  
  aws ec2 create-tags --resources $INSTANCE_ID \
    --tags \
      Key=dr:enabled,Value=true \
      Key=dr:priority,Value=$DEFAULT_PRIORITY \
      Key=dr:wave,Value=$DEFAULT_WAVE \
    --region $REGION
done

echo "Migration complete. Review and adjust dr:priority and dr:wave values."
```

---

## 5. Sample Tag Sets

### 5.1 Production Database Server (Critical)

```
BusinessUnit: HRP
Environment: Production
Customer: CustomerName
Application: PatientPortal
Purpose: DatabaseServers
dr:enabled: true
dr:priority: critical
dr:wave: 1
dr:recovery-strategy: drs
dr:rto-target: 30
dr:rpo-target: 30
```

### 5.2 Production App Server (High)

```
BusinessUnit: GuidingCare
Environment: Production
Customer: CustomerName
Application: CareManagement
Purpose: AppServers
dr:enabled: true
dr:priority: high
dr:wave: 2
dr:recovery-strategy: drs
dr:rto-target: 60
dr:rpo-target: 30
```

### 5.3 Production Web Server (Medium)

```
BusinessUnit: GuidingCare
Environment: Production
Customer: CustomerName
Application: CareManagement
Purpose: WebServers
dr:enabled: true
dr:priority: medium
dr:wave: 3
dr:recovery-strategy: drs
dr:rto-target: 120
dr:rpo-target: 30
```

### 5.4 EKS Cluster (DNS Failover)

```
BusinessUnit: GuidingCare
Environment: Production
Application: CareManagement
dr:enabled: true
dr:priority: critical
dr:wave: 1
dr:recovery-strategy: eks-dns
dr:rto-target: 30
```

### 5.5 Development Server (No DR)

```
BusinessUnit: GuidingCare
Environment: Development
Application: CareManagement
dr:enabled: false
```

---

## 6. Current State Analysis

### 6.1 AWS Account Tag Analysis (December 15, 2025)

| Account | Account ID | EC2 Count | DRS Tag | dr:enabled Tag |
|---------|------------|-----------|---------|----------------|
| HRP Production | 538127172524 | 25 | ✅ Yes (24 True, 1 False) | ❌ Not present |
| Guiding Care Production | 835807883308 | 0 (us-east-1) | N/A | N/A |
| Guiding Care NonProduction | 315237946879 | 3 | ❌ Not present | ❌ Not present |

**Key Findings:**
- HRP Production uses legacy `DRS` tag - migration required
- No `dr:enabled` tag exists in any account yet
- HRP Production uses `Service` tag instead of `Purpose`

### 6.2 HealthEdge AWS Accounts

| Account Name | Account ID | Purpose |
|--------------|------------|---------|
| Guiding Care Development | 480442107714 | Development |
| Guiding Care NonProduction | 315237946879 | QA/Staging |
| Guiding Care Production | 835807883308 | Production |
| Guiding Care Shared Services | 096212910625 | Shared Services |
| HRP Development | 827859360968 | Development |
| HRP NonProduction | 769064993134 | QA/Staging |
| HRP Production | 538127172524 | Production |
| HRP Shared Services | 211234826829 | Shared Services |

---

## 7. References

### 7.1 Authoritative Source

| Document | Location |
|----------|----------|
| **Guiding Care DR Implementation** | [Confluence CP1/5327028252](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5327028252) |

### 7.2 Related Confluence Documents

| Document | Page ID |
|----------|---------|
| AWS Tagging Strategy | [4836950067](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4836950067) |
| Tag Types Reference | [4867035088](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867035088) |
| DRS Tags | [4930863374](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4930863374) |

### 7.3 Related JIRA

- [AWSM-1087](https://healthedge.atlassian.net/browse/AWSM-1087) - DR Tagging Taxonomy (this document)
- [AWSM-1100](https://healthedge.atlassian.net/browse/AWSM-1100) - Tag Validation Implementation

---

**Document Control:**
- Created: December 15, 2025
- Author: Cloud Infrastructure Team
- Data Sources: Guiding Care DR Implementation (Confluence), AWS Account Tag Analysis
