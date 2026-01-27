# DR Wave and Priority Mapping Strategy

## Overview

This document defines how `dr:wave` and `dr:priority` are determined based on resource characteristics and dependencies.

## Mapping Logic

### Wave 1: Critical Priority - Database Tier
**Characteristics:**
- `ResourceType=Database`
- `MonitoringLevel=Critical`
- `Service=DatabaseServer`

**Rationale:**
- Databases must be recovered first as they are dependencies for all other tiers
- Data integrity is critical
- Application and web tiers cannot function without database access

**Tags:**
- `dr:wave=1`
- `dr:priority=critical`

**Example Servers:**
- hrp-core-db01-az1 (i-08079c6d44888cd37)
- hrp-core-db02-az1 (i-0ead3f8fb7d6a6745)

---

### Wave 2: High Priority - Application Tier
**Characteristics:**
- `ResourceType=Compute`
- `MonitoringLevel=Standard`
- `Service=ApplicationServer`

**Rationale:**
- Application servers depend on database tier (Wave 1)
- Business logic layer must be available before web tier
- High priority but not critical (can tolerate brief delay after DB recovery)

**Tags:**
- `dr:wave=2`
- `dr:priority=high`

**Example Servers:**
- WINAPPSRV01 (i-053654498d177ea0d)
- WINAPPSRV02 (i-0284e604b2cb3d9a4)

---

### Wave 3: Medium Priority - Web Tier
**Characteristics:**
- `ResourceType=Compute`
- `MonitoringLevel=Standard`
- `Service=WebServer`

**Rationale:**
- Web servers depend on application tier (Wave 2)
- Frontend presentation layer
- Can tolerate delay while backend services stabilize

**Tags:**
- `dr:wave=3`
- `dr:priority=medium`

**Example Servers:**
- WINWEBSRV01 (i-0a24e3429ec060c7e)
- WINWEBSRV02 (i-0f46d8897d2b98824)

---

## Decision Matrix

| ResourceType | Service | MonitoringLevel | dr:wave | dr:priority | Rationale |
|--------------|---------|-----------------|---------|-------------|-----------|
| Database | DatabaseServer | Critical | 1 | critical | Foundation tier - all others depend on this |
| Compute | ApplicationServer | Standard | 2 | high | Business logic - depends on database |
| Compute | WebServer | Standard | 3 | medium | Presentation - depends on application tier |
| Compute | APIServer | Standard | 2 | high | API layer - same tier as application |
| Storage | FileServer | Standard | 1 | high | Shared storage may be needed by multiple tiers |
| Network | LoadBalancer | Critical | 1 | critical | Traffic routing - needed for all tiers |

## Additional Influencing Factors

### Customer SLA Requirements
- `Customer` tag can override default priority
- Premium customers may require faster RTO → higher priority

### Application Criticality
- `Application` tag identifies business application
- Revenue-generating applications → higher priority
- Internal tools → lower priority

### Monitoring Level
- `MonitoringLevel=Critical` → Always wave 1 or 2
- `MonitoringLevel=Standard` → Wave 2 or 3
- `MonitoringLevel=Basic` → Wave 3 or 4
- `MonitoringLevel=None` → Wave 4 or 5 (lowest priority)

## Mock Data Applied

### Database Servers (Wave 1 - Critical)
```
Application: HRP-Core-Platform
Customer: CustomerA
MonitoringLevel: Critical
dr:wave: 1
dr:priority: critical
```

### Application Servers (Wave 2 - High)
```
Application: HRP-Core-Platform
Customer: CustomerA
MonitoringLevel: Standard
dr:wave: 2
dr:priority: high
```

### Web Servers (Wave 3 - Medium)
```
Application: HRP-Core-Platform
Customer: CustomerA
MonitoringLevel: Standard
dr:wave: 3
dr:priority: medium
```

## Recovery Sequence

```
Time 0:00 - DR Event Triggered
  ↓
Time 0:05 - Wave 1 Starts (Critical - Database Tier)
  ├─ WINDBSRV01 recovery initiated
  └─ WINDBSRV02 recovery initiated
  ↓
Time 0:35 - Wave 1 Complete (30 min RTO)
  ↓
Time 0:35 - Wave 2 Starts (High - Application Tier)
  ├─ WINAPPSRV01 recovery initiated
  └─ WINAPPSRV02 recovery initiated
  ↓
Time 1:05 - Wave 2 Complete (30 min RTO)
  ↓
Time 1:05 - Wave 3 Starts (Medium - Web Tier)
  ├─ WINWEBSRV01 recovery initiated
  └─ WINWEBSRV02 recovery initiated
  ↓
Time 1:35 - Wave 3 Complete (30 min RTO)
  ↓
Time 1:35 - Full Stack Recovery Complete
```

## Automation Rules

The DR orchestration system will:
1. Query resources by `dr:wave` tag (ascending order)
2. Within each wave, prioritize by `dr:priority` (critical → high → medium → low)
3. Wait for wave completion before starting next wave
4. Monitor recovery progress via DRS job status
5. Alert on wave failures or RTO violations
