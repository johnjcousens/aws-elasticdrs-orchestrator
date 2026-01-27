# HealthEdge AWS Tagging Strategy for DR

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5352751162/HealthEdge%20AWS%20Tagging%20Strategy%20for%20DR

**Created by:** John Cousens on December 15, 2025  
**Last modified by:** Chris Falk on December 19, 2025 at 04:51 PM

---

**IRA:** [AWSM-1087](https://healthedge.atlassian.net/browse/AWSM-1087)

---

Executive Summary
-----------------

This document defines the additional DR-related AWS tagging strategy for HealthEdge. Additionally we have integrated the new DR (Disaster Recovery) taxonomy with existing organizational tagging requirements here. These tags are only required in Production accounts.

In addition to the tags below, the DR automation solution depends on `Customer` and `Environment` tags to drive which workloads will be automated for a failover or test.

---

1. Disaster Recovery
--------------------

| Tag Key | Allowed Values | Mandatory | Description |
| --- | --- | --- | --- |
| `dr:enabled` | `true`, `false` | **EC2 Instance, EKS Cluster** | DR orchestration enrollment |
| `dr:priority` | `critical`, `high`, `medium`, `low` | **If dr:enabled=true** | Recovery priority (maps to RTO) |
| `dr:wave` | `1`, `2`, `3`, `4`, `5` | **If dr:enabled=true** | Recovery wave number |
| `dr:recovery-strategy` | `drs`, `eks-dns`, `sql-ag`, `managed-service` | **If dr:enabled=true** | Recovery method |
| `dr:rto-target` | Integer (minutes) | Optional | Target RTO in minutes |
| `dr:rpo-target` | Integer (minutes) | Optional | Target RPO in minutes |

---

2. DR Priority to RTO Mapping
-----------------------------

| dr:priority | RTO Target | Wave | Use Case |
| --- | --- | --- | --- |
| `critical` | 15 minutes | 1 | Databases, Active Directory, DNS, core infrastructure |
| `high` | 30 minutes | 2 | Application servers |
| `medium` | 1 hour | 3 | Supporting services |
| `low` | 4 hours | 4-5 | Non-critical workloads |

---

3. Sample Tag Sets
------------------

### 3.1 Production Oracle Database Server (DR Critical - Wave 1)


```yaml
# Environment
Environment: Production

# Operational
Customer: ABCD

# Disaster Recovery
dr:enabled: true
dr:priority: critical
dr:wave: 1
dr:recovery-strategy: drs
dr:rto-target: 30
dr:rpo-target: 30
```


### 3.2 Production Application Server (DR High - Wave 2)


```yaml
# Environment
Environment: Production

# Operational
Customer: ABCD

# Disaster Recovery
dr:enabled: true
dr:priority: high
dr:wave: 2
dr:recovery-strategy: drs
dr:rto-target: 60
dr:rpo-target: 30
```


### 3.3 Production Web Server (DR Medium - Wave 3)


```yaml
# Environment
Environment: Production

# Operational
Customer: ABCD

# Disaster Recovery
dr:enabled: true
dr:priority: medium
dr:wave: 3
dr:recovery-strategy: drs
dr:rto-target: 120
dr:rpo-target: 30
```


### 3.4 Production Infrastructure - Active Directory (DR Critical - Wave 1)


```yaml
# Environment
Environment: Production

# Operational
Customer: ABCD

# Disaster Recovery
dr:enabled: False # already present in the DR region
```


### 3.5 EKS Cluster (DNS Failover - Not DRS)


```yaml
# Environment
Environment: Production

# Operational
Customer: ABCD

# Disaster Recovery (EKS uses DNS failover)
dr:enabled: true
dr:priority: critical
dr:wave: 1
dr:recovery-strategy: eks-dns
dr:rto-target: 30
```


4. DR Tag Migration (DRS → dr:enabled)
--------------------------------------

| Legacy Tag | New Tags | Value Mapping |
| --- | --- | --- |
| `DRS: True` | `dr:enabled: true` | Direct mapping |
| `DRS: False` | `dr:enabled: false` | Direct mapping |
| (none) | `dr:priority` | Assign based on RTO |
| (none) | `dr:wave` | Assign based on recovery order |

---

5. Tag Governance
-----------------

### 5.1 Enforcement Mechanisms

* **AWS Organizations Tag Policies** - Enforce compliance at organization level
* **Service Control Policies (SCPs)** - Deny resource creation without mandatory tags

### 5.2 Provisioning Requirements

* All AWS resources in Workloads OU must be provisioned via CDK or migrated using AWS Application Service where tags are provided
* CDK pipelines assume `CrossAccountDeploymentRole` for provisioning
* Resources missing mandatory tags will be denied creation by SCP
* Manual provisioning only allowed in Sandbox OU

### 5.3 New Tag Requests

Any tags not listed in this document must be submitted for approval and added to the HealthEdge Tag policies and SCPs before use.

---

6. Current State Analysis
-------------------------

### 6.1 AWS Account Tag Analysis (December 15, 2025)

| Account | Account ID | EC2 Count | DRS Tag | dr:enabled Tag |
| --- | --- | --- | --- | --- |
| HRP Production | 538127172524 | 25 | ✅ Yes (24 True, 1 False) | ❌ Not present |
| Guiding Care Production | 835807883308 | 0 (us-east-1) | N/A | N/A |

---

7. References
-------------

| Document | Confluence Link |
| --- | --- |
| Tag Management Design | Confluence |

* [AWSM-1087](https://healthedge.atlassian.net/browse/AWSM-1087) - DR Tagging Taxonomy (this document)
* [AWSM-1100](https://healthedge.atlassian.net/browse/AWSM-1100) - Tag Validation Implementation

---

**Document Control:**

* Created: December 15, 2025
* Version: 2.2 - Improved table formatting for Word/Confluence; added dr:rto-target and dr:rpo-target to Section 6
* Version: 2.1 - Aligned Non-Production mandatory tags with Tag-Management-Design source; fixed Confluence URLs
* Author: Cloud Infrastructure Team
* Sources: AWS Tagging Strategy, Tag Management Design, Guiding Care DR Implementation