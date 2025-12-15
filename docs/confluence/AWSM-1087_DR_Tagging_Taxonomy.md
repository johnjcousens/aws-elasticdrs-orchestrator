# DR Tagging Taxonomy for AWS DRS Orchestration

**JIRA:** [AWSM-1087](https://healthedge.atlassian.net/browse/AWSM-1087)  
**Version:** 1.1  
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

### 1.3 Tier-Based Filtering (Using Existing Tags)

For tier-based Protection Group filtering, use existing operational tags:

| Tag Key | Example Values | Use Case |
|---------|----------------|----------|
| `Service` | `Active Directory`, `DNS`, `SQL Server`, `Web Server` | Filter by service/component type |
| `Application` | `AD`, `DNS`, `PatientPortal`, `CareManagement` | Filter by application |
| `Customer` | Customer name | Filter by customer for multi-tenant |

> **Note:** The `dr:wave` tag provides recovery ordering. Use `Service` or `Application` tags for tier-based grouping in Protection Groups.

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

| Tag | DRS Orchestration (HRP) | Guiding Care DR | Description |
|-----|-------------------------|-----------------|-------------|
| `dr:enabled` | ✅ Required | ✅ Required | Identifies DR-enrolled resources |
| `dr:priority` | ✅ Informational | ✅ RTO-based prioritization | Maps to RTO targets |
| `dr:wave` | ℹ️ Not used (uses Recovery Plans) | ✅ Tag-driven wave discovery | Wave assignment |
| `dr:recovery-strategy` | ℹ️ Not used | ✅ Recovery method selection | drs, eks-dns, sql-ag, managed-service |
| `Service` | ✅ Protection Group filtering | ✅ Resource classification | Service/component type |
| `Application` | ✅ Protection Group filtering | ✅ Resource classification | Application grouping |
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

---

## 5. Sample Tag Sets

### 5.1 Infrastructure Server - Active Directory (Critical)

```
BusinessUnit: HRP
Environment: Production
Customer: CustomerName
Application: AD
Service: Active Directory
dr:enabled: true
dr:priority: critical
dr:wave: 1
```

### 5.2 Database Server (Critical)

```
BusinessUnit: HRP
Environment: Production
Customer: CustomerName
Application: PatientPortal
Service: SQL Server
dr:enabled: true
dr:priority: critical
dr:wave: 1
dr:recovery-strategy: drs
dr:rto-target: 30
dr:rpo-target: 30
```

### 5.3 Application Server (High)

```
BusinessUnit: GuidingCare
Environment: Production
Customer: CustomerName
Application: CareManagement
Service: Application Server
dr:enabled: true
dr:priority: high
dr:wave: 2
dr:recovery-strategy: drs
dr:rto-target: 60
dr:rpo-target: 30
```

### 5.4 Web Server (Medium)

```
BusinessUnit: GuidingCare
Environment: Production
Customer: CustomerName
Application: CareManagement
Service: Web Server
dr:enabled: true
dr:priority: medium
dr:wave: 3
dr:recovery-strategy: drs
dr:rto-target: 120
dr:rpo-target: 30
```

### 5.5 EKS Cluster (DNS Failover)

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

### 5.6 Development Server (No DR)

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
- HRP Production uses `Service` tag (values: "Active Directory", "DNS")
- HRP Production uses `Application` tag (values: "AD", "DNS")

### 6.2 HRP Production Current Tags (Available for Protection Group Filtering)

| Tag | Values in Use | Can Filter By |
|-----|---------------|---------------|
| `Service` | Active Directory, DNS | Service type |
| `Application` | AD, DNS | Application |
| `Customer` | axm, wip, frso, alh, citi, ust, atr, edif | Customer |
| `DRS` | True, False | DR enrollment |

### 6.3 HealthEdge AWS Accounts

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
| Tag Management Design | [Tag-Management-Design](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/Tag-Management-Design) |

### 7.3 Related JIRA

- [AWSM-1087](https://healthedge.atlassian.net/browse/AWSM-1087) - DR Tagging Taxonomy (this document)
- [AWSM-1100](https://healthedge.atlassian.net/browse/AWSM-1100) - Tag Validation Implementation

---

**Document Control:**
- Created: December 15, 2025
- Updated: December 15, 2025 - Removed dr:tier (use Service/Application tags instead)
- Author: Cloud Infrastructure Team
- Data Sources: Guiding Care DR Implementation (Confluence), AWS Account Tag Analysis
