# Guiding Care DR Integration Compatibility Guide

**Version:** 2.0  
**Date:** December 15, 2025  
**Status:** Aligned with Authoritative Source  
**Purpose:** Ensure DRS Orchestration (HRP) aligns with Guiding Care DR Implementation tagging taxonomy

---

## Executive Summary

This document defines how DRS Orchestration (HRP) integrates with the **Guiding Care DR Implementation**, which is the **authoritative source** for DR tagging taxonomy across HealthEdge. The HealthEdge AWS Tagging Strategy has been updated to align with Guiding Care DR's tag-driven discovery approach.

---

## 1. Authoritative DR Tagging Taxonomy (Guiding Care DR)

The **Guiding Care DR Implementation** defines the official DR taxonomy. The HealthEdge AWS Tagging Strategy (v2.1) has been updated to align with this authoritative source.

### DR Orchestration Tags

| Tag | Values | Required | Purpose |
|-----|--------|----------|---------|
| `dr:enabled` | `true` \| `false` | **Yes** (Production EC2) | Identifies resources for DR orchestration |
| `dr:priority` | `critical` \| `high` \| `medium` \| `low` | **Yes** (DR-enabled) | Recovery priority classification |
| `dr:wave` | `1` \| `2` \| `3` \| `4` \| `5` | **Yes** (DR-enabled) | Wave number for ordered recovery |
| `dr:recovery-strategy` | `drs` \| `eks-dns` \| `sql-ag` \| `managed-service` | Optional | Recovery method for the resource |
| `dr:rto-target` | Integer (minutes) | Optional | Target recovery time objective |
| `dr:rpo-target` | Integer (minutes) | Optional | Target recovery point objective |

### Scoping Tags (Existing)

| Tag | Values | Purpose |
|-----|--------|---------|
| `Customer` | Customer identifier | Multi-tenant scoping |
| `Environment` | Production, NonProduction, etc. | Environment filtering |
| `Purpose` | `DatabaseServers` \| `AppServers` \| `WebServers` | Application tier classification |

### DR Priority to RTO Mapping

| dr:priority | RTO Target | Typical Wave |
|-------------|------------|--------------|
| `critical` | 30 minutes | Wave 1 |
| `high` | 1 hour | Wave 2 |
| `medium` | 2 hours | Wave 3 |
| `low` | 4 hours | Wave 4+ |

### Tag Usage by System

| Tag | DRS Orchestration (HRP) | Guiding Care DR | Notes |
|-----|-------------------------|-----------------|-------|
| `dr:enabled` | ✅ Required | ✅ Required | Identifies DR-enrolled resources |
| `dr:priority` | ✅ Informational | ✅ RTO-based prioritization | Maps to RTO targets |
| `dr:wave` | ℹ️ Not used (uses Recovery Plans) | ✅ Tag-driven wave discovery | Wave assignment |
| `dr:recovery-strategy` | ℹ️ Not used | ✅ Recovery method selection | drs, eks-dns, sql-ag, managed-service |
| `dr:rto-target` | ℹ️ Not used | ✅ RTO tracking | Target in minutes |
| `dr:rpo-target` | ℹ️ Not used | ✅ RPO tracking | Target in minutes |
| `Purpose` | ✅ Protection Group filtering | ✅ Resource classification | Existing tag |
| `Customer` | ✅ Protection Group filtering | ✅ Multi-tenant scoping | Existing tag |

---

## 2. Integration Approaches

Both systems consume the same tags but use different discovery mechanisms:

### 2.1 DRS Orchestration Approach (Protection Groups + Recovery Plans)

DRS Orchestration uses **Protection Groups** for server organization and **Recovery Plans** for wave execution:

```python
# Protection Groups filter servers by ANY tag
protection_group = {
    "GroupName": "CustomerA-Database-Tier",
    "ServerSelectionTags": {
        "dr:enabled": "true",
        "Purpose": "DatabaseServers",
        "Customer": "CustomerA"
    }
}

# Recovery Plans define wave order (NOT tags)
recovery_plan = {
    "PlanName": "CustomerA-Full-Recovery",
    "Waves": [
        {"WaveNumber": 1, "ProtectionGroupId": "pg-database"},
        {"WaveNumber": 2, "ProtectionGroupId": "pg-application"},
        {"WaveNumber": 3, "ProtectionGroupId": "pg-web"}
    ]
}
```

### 2.2 Guiding Care DR Approach (Tag-Driven Discovery)

Guiding Care DR uses **AWS Resource Explorer** for tag-driven discovery with aggregator region (us-east-1):

```python
# Tag-driven wave discovery using dr:wave
resources = resource_explorer.search(
    QueryString='tag.key:dr:enabled tag.value:true tag.key:dr:wave tag.value:1 tag.key:Customer tag.value:CustomerA',
    ViewArn=view_arn
)

# Priority-based ordering using dr:priority
critical_resources = resource_explorer.search(
    QueryString='tag.key:dr:priority tag.value:critical tag.key:dr:enabled tag.value:true',
    ViewArn=view_arn
)

# Recovery strategy filtering
drs_resources = resource_explorer.search(
    QueryString='tag.key:dr:recovery-strategy tag.value:drs tag.key:dr:enabled tag.value:true',
    ViewArn=view_arn
)
```

### 2.3 Use Existing Tags for Tier Classification

Both systems use the existing `Purpose` tag for tier classification:

| Purpose Value | Description | Typical Wave |
|---------------|-------------|--------------|
| `DatabaseServers` | Database tier (SQL, Oracle, etc.) | Wave 1 |
| `AppServers` | Application/API tier | Wave 2 |
| `WebServers` | Web/presentation tier | Wave 3 |

```json
{
  "ServerSelectionTags": {
    "dr:enabled": "true",
    "Purpose": "DatabaseServers",
    "Customer": "CustomerA",
    "Environment": "Production"
  }
}
```

> **Note:** Use existing tags (`Purpose`, `Customer`, `Environment`, `Application`) for filtering. No need for a separate `dr:tier` tag.

---

## 3. Integration Architecture

### 3.1 How Guiding Care DR Integrates with DRS Orchestration

```
┌─────────────────────────────────────────────────────────────────┐
│                    Guiding Care DR Solution                      │
│  (CDK Infrastructure, Resource Discovery, Bubble Test Network)   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Uses
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DRS Orchestration Solution                     │
│         (Protection Groups, Recovery Plans, Execution)           │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ Protection Groups │  │  Recovery Plans  │  │  Executions   │  │
│  │ - Tag filtering   │  │  - Wave order    │  │  - Drill mode │  │
│  │ - Server lists    │  │  - Pause points  │  │  - Recovery   │  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Orchestrates
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AWS DRS Service                           │
│              (Replication, Recovery Jobs, Instances)             │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Responsibility Matrix

| Capability | Owner | Notes |
|------------|-------|-------|
| Tag taxonomy definition | DRS Orchestration | Authoritative source |
| Protection Group management | DRS Orchestration | Tag-based or explicit server selection |
| Recovery Plan definition | DRS Orchestration | Wave order, pause points, dependencies |
| Wave execution order | DRS Orchestration | Defined in Recovery Plans, NOT tags |
| Drill/Recovery execution | DRS Orchestration | Step Functions orchestration |
| Resource discovery | Guiding Care DR | Can use Resource Explorer with `dr:enabled` |
| Bubble test network | Guiding Care DR | Network isolation for testing |
| CDK infrastructure | Guiding Care DR | Infrastructure provisioning |
| Pre-cached inventory | Guiding Care DR | Primary region failure scenarios |

---

## 4. Tag Synchronization

### 4.1 Required Tags for DR-Enabled Resources

Per the Guiding Care DR Implementation (authoritative source):

```python
# Required tags for DR-enabled EC2 instances
tags = {
    # DR Taxonomy Tags (Guiding Care DR standard)
    'dr:enabled': 'true',                    # Required - identifies DR resources
    'dr:priority': 'high',                   # Required - critical|high|medium|low
    'dr:wave': '2',                          # Required - 1|2|3|4|5
    'dr:recovery-strategy': 'drs',           # Optional - drs|eks-dns|sql-ag|managed-service
    'dr:rto-target': '60',                   # Optional - minutes
    'dr:rpo-target': '30',                   # Optional - minutes
    
    # Scoping Tags (existing)
    'Customer': customer_name,               # Required for multi-tenant scoping
    'Environment': 'Production',             # Required
    
    # Business Tags (existing)
    'BusinessUnit': 'GuidingCare',           # Required
    'Owner': 'team@healthedge.com',          # Required
    
    # Classification Tags (existing)
    'Purpose': 'AppServers',                 # Recommended - DatabaseServers|AppServers|WebServers
    'Application': 'GuidingCare',            # Recommended
}
```

### 4.2 Tags NOT Supported

```python
# DO NOT USE - These tags are deprecated
invalid_tags = {
    'DRS': 'True',             # DEPRECATED - Use dr:enabled instead
    'dr:tier': 'application',  # Use existing Purpose tag instead
}
```

---

## 5. API Integration Points

### 5.1 Guiding Care → DRS Orchestration API

Guiding Care can integrate with DRS Orchestration via REST API:

```python
# Example: Start a drill for a customer
import requests

API_ENDPOINT = "https://api.drs-orchestration.healthedge.com/prod"
headers = {"Authorization": f"Bearer {cognito_token}"}

# Get recovery plans for customer
response = requests.get(
    f"{API_ENDPOINT}/recovery-plans",
    headers=headers,
    params={"customer": "CustomerA"}
)
plans = response.json()

# Start drill execution
response = requests.post(
    f"{API_ENDPOINT}/executions",
    headers=headers,
    json={
        "recovery_plan_id": plans[0]["PlanId"],
        "execution_type": "DRILL",
        "invocation_source": "GUIDING_CARE_DR"
    }
)
execution = response.json()
```

### 5.2 Available API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/protection-groups` | GET, POST | Manage protection groups |
| `/recovery-plans` | GET, POST | Manage recovery plans |
| `/executions` | GET, POST | Start/monitor executions |
| `/executions/{id}/resume` | POST | Resume paused execution |
| `/executions/{id}/cancel` | POST | Cancel execution |
| `/drs/source-servers` | GET | List DRS source servers |

---

## 6. Migration Path (DRS Tag → dr:x Taxonomy)

### Phase 1: Dual Tagging (Now - Jan 31, 2026)

1. Apply both legacy `DRS` and new `dr:enabled` tags to all DR-enrolled resources
2. Add `dr:priority` and `dr:wave` tags to all DR-enabled resources
3. Optionally add `dr:recovery-strategy`, `dr:rto-target`, `dr:rpo-target`

### Phase 2: Validation (Feb 1-15, 2026)

1. Validate all resources have new `dr:x` tags via AWS Config
2. Update Resource Explorer queries to use `dr:enabled` (not `DRS`)
3. Test DRS Orchestration Protection Groups with new tags

### Phase 3: Deprecation (Feb 16-28, 2026)

1. Remove `DRS` tag enforcement from SCPs
2. Update all automation to use `dr:enabled`

### Phase 4: Cleanup (Mar 1-31, 2026)

1. Remove legacy `DRS` tags from all resources
2. Full migration to Guiding Care DR tag taxonomy complete

---

## 7. Validation Checklist

Before DR operations, verify tag compliance:

- [ ] All Production EC2 have `dr:enabled: true` or `dr:enabled: false`
- [ ] All DR-enabled resources have `dr:priority` (critical, high, medium, low)
- [ ] All DR-enabled resources have `dr:wave` (1, 2, 3, 4, 5)
- [ ] `dr:recovery-strategy` values (if used) are: `drs`, `eks-dns`, `sql-ag`, `managed-service`
- [ ] `Purpose` values are: `DatabaseServers`, `AppServers`, `WebServers`
- [ ] No legacy `DRS` tags without corresponding `dr:enabled` tag
- [ ] No deprecated `dr:tier` tags (use `Purpose` instead)
- [ ] AWS Config rule `dr-tag-compliance` is deployed and reporting
- [ ] Resource Explorer aggregator configured in us-east-1

---

## 8. Data Sources and References

### 8.1 Authoritative Source Document

| Document | Location | Author | Date |
|----------|----------|--------|------|
| **Guiding Care DR Implementation** | [Confluence CP1/5327028252](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5327028252) | Chris Falk | December 9, 2025 |

This document defines the DR tagging taxonomy (`dr:enabled`, `dr:priority`, `dr:wave`, `dr:recovery-strategy`, `dr:rto-target`, `dr:rpo-target`) and tag-driven discovery approach using AWS Resource Explorer.

### 8.2 AWS Account Tag Analysis (December 15, 2025)

Current tag state observed via read-only AWS API queries:

| Account | Account ID | Profile | EC2 Count | DRS Tag | dr:enabled Tag | Purpose Tag |
|---------|------------|---------|-----------|---------|----------------|-------------|
| HRP Production | 538127172524 | `538127172524_AWSAdministratorAccess` | 25 | ✅ Yes (24 True, 1 False) | ❌ Not present | ❌ Not present |
| Guiding Care Production | 835807883308 | `835807883308_AWSAdministratorAccess` | 0 (us-east-1) | N/A | N/A | N/A |
| Guiding Care NonProduction | 315237946879 | `315237946879_AWSAdministratorAccess` | 3 | ❌ Not present | ❌ Not present | ❌ Not present |

**Key Findings from HRP Production (538127172524):**
- Legacy `DRS` tag is in active use (24 instances with `True`, 1 with `False`)
- No `dr:enabled` tag exists yet - migration required
- No `Purpose` tag exists - uses `Service` tag instead (values: "Active Directory", "DNS")
- Uses `Application` tag (values: "AD", "DNS")
- Uses `Role` tag but values are generic ("WindowsServer")

**Migration Implication:** HRP Production requires dual-tagging phase to add `dr:enabled` alongside existing `DRS` tag before deprecation.

### 8.3 HealthEdge AWS Accounts Reference

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

### 8.4 Confluence Source Documents

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

### 8.5 Related Documents

- [HealthEdge AWS Tagging Strategy v2.1](../guides/HealthEdge_AWS_Tagging_Strategy_Consolidated.md) - Consolidated and aligned with Guiding Care DR
- [DRS Orchestration API Reference](../guides/ORCHESTRATION_INTEGRATION_GUIDE.md)
- [Product Requirements Document](../requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md)

---

**Document Control:**
- Created: December 15, 2025
- Updated: December 15, 2025 (v2.0 - Aligned with Guiding Care DR authoritative source)
- Author: DRS Orchestration Team
- Data Sources: Guiding Care DR Implementation (Confluence), AWS Account Tag Analysis (read-only queries)
- Related JIRA: AWSM-1087, AWSM-1100
