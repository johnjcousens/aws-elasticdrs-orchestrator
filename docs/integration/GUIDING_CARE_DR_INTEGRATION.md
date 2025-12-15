# Guiding Care DR Integration Compatibility Guide

**Version:** 1.1  
**Date:** December 15, 2025  
**Status:** Updated  
**Purpose:** Ensure Guiding Care DR Implementation aligns with HealthEdge AWS Tagging Strategy

---

## Executive Summary

This document defines how the Guiding Care DR Implementation aligns with the HealthEdge AWS Tagging Strategy. The tagging strategy document is the **source of truth** for all DR tagging taxonomy. Both DRS Orchestration and Guiding Care DR consume tags as defined in that strategy.

---

## 1. Authoritative Tagging Strategy

The **HealthEdge AWS Tagging Strategy** (v2.1) defines the official DR taxonomy:

| Tag | Values | Required | Purpose |
|-----|--------|----------|---------|
| `dr:enabled` | `true` \| `false` | **Yes** (Production EC2) | DRS enrollment indicator |
| `Purpose` | `DatabaseServers` \| `AppServers` \| `WebServers` | Recommended | Application tier classification (existing tag) |
| `dr:priority` | `critical` \| `high` \| `medium` \| `low` | Optional | RTO priority for Guiding Care DR |
| `dr:wave` | `1` \| `2` \| `3` \| `4` \| `5` | Optional | Tag-driven wave discovery for Guiding Care DR |

### Tag Usage by System

| Tag | DRS Orchestration | Guiding Care DR | Notes |
|-----|-------------------|-----------------|-------|
| `dr:enabled` | ✅ Required | ✅ Required | DRS enrollment indicator |
| `Purpose` | ✅ Protection Group filtering | ✅ Resource classification | Existing tag - no new tag needed |
| `dr:priority` | ℹ️ Informational only | ✅ RTO-based prioritization | Maps to RTO targets |
| `dr:wave` | ℹ️ Not used (waves in Recovery Plans) | ✅ Tag-driven wave discovery | For systems using tag-driven discovery |

### Tags NOT Supported

| Tag | Reason | Alternative |
|-----|--------|-------------|
| `dr:tier` | Redundant with existing `Purpose` tag | Use `Purpose` (DatabaseServers, AppServers, WebServers) |
| `dr:rto-target` | RTO is a business requirement, not a resource attribute | Use `dr:priority` for classification |
| `dr:rpo-target` | RPO is a business requirement, not a resource attribute | Document in Recovery Plan metadata |
| `dr:recovery-strategy` | Recovery strategy is defined at Recovery Plan level | Configure in Recovery Plan |

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

Guiding Care DR uses **Resource Explorer** for tag-driven discovery:

```python
# Tag-driven wave discovery using dr:wave
servers = resource_explorer.search(
    QueryString="tag:dr:wave:1 AND tag:dr:enabled:true AND tag:BusinessUnit:GuidingCare"
)

# Priority-based ordering using dr:priority
critical_servers = resource_explorer.search(
    QueryString="tag:dr:priority:critical AND tag:dr:enabled:true"
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

### 4.1 Tags Guiding Care Must Apply

When Guiding Care provisions EC2 instances for DR:

```python
# Required tags (enforced by SCP)
tags = {
    'dr:enabled': 'true',           # Required for Production
    'Environment': 'Production',     # Required
    'BusinessUnit': 'GuidingCare',   # Required
    'Owner': 'team@healthedge.com',  # Required
    'Customer': customer_name,       # Required for Production
    
    # Recommended for tier classification and filtering
    'Purpose': 'AppServers',         # DatabaseServers|AppServers|WebServers
    'Application': 'GuidingCare',
    
    # Optional - for Guiding Care DR tag-driven discovery
    'dr:priority': 'high',           # critical|high|medium|low
    'dr:wave': '2',                  # 1|2|3|4|5
}
```

### 4.2 Tags Guiding Care Must NOT Apply

```python
# DO NOT USE - These tags are deprecated or not supported
invalid_tags = {
    'dr:tier': 'application',  # Use Purpose tag instead
    'dr:rto-target': '30min',  # Document in Recovery Plan
    'dr:rpo-target': '15min',  # Document in Recovery Plan
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

## 6. Migration Path for Guiding Care DR

### Phase 1: Tag Alignment (Immediate)

1. Remove any `dr:tier` tags - use existing `Purpose` tag instead
2. Ensure all Production EC2 have `dr:enabled: true`
3. Add `Purpose` tag (DatabaseServers, AppServers, WebServers) where missing

### Phase 2: Discovery Integration (Q1 2026)

1. Update Resource Explorer queries to use `dr:enabled` and `Purpose`
2. Optionally use `dr:priority` and `dr:wave` for Guiding Care-specific discovery
3. Integrate with DRS Orchestration API for wave execution (optional)

### Phase 3: Full Integration (Q2 2026)

1. Guiding Care DR can use either:
   - Tag-driven discovery (`dr:wave`, `dr:priority`) for standalone operation
   - DRS Orchestration API for integrated operation
2. Guiding Care DR focuses on:
   - Infrastructure provisioning (CDK)
   - Bubble test network setup
   - Pre-cached inventory management
   - Customer-specific customizations

---

## 7. Validation Checklist

Before Guiding Care DR deployment, verify:

- [ ] No `dr:tier` tags on any resources (use `Purpose` instead)
- [ ] All Production EC2 have `dr:enabled: true` or `dr:enabled: false`
- [ ] `Purpose` values are: `DatabaseServers`, `AppServers`, `WebServers`
- [ ] `dr:priority` values (if used) are: `critical`, `high`, `medium`, `low`
- [ ] `dr:wave` values (if used) are: `1`, `2`, `3`, `4`, `5`
- [ ] Recovery Plans define wave order (for DRS Orchestration integration)
- [ ] API integration uses DRS Orchestration endpoints (if integrated)

---

## 8. References

- [HealthEdge AWS Tagging Strategy v2.1](../guides/HealthEdge_AWS_Tagging_Strategy_Consolidated.md)
- [DRS Orchestration API Reference](../guides/ORCHESTRATION_INTEGRATION_GUIDE.md)
- [Product Requirements Document](../requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md)

---

**Document Control:**
- Created: December 15, 2025
- Author: DRS Orchestration Team
- Related JIRA: AWSM-1087, AWSM-1100
