# Salt Configuration Management – Architecture & Compliance Process Overview

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5296324631/Salt%20Configuration%20Management%20%E2%80%93%20Architecture%20%26%20Compliance%20Process%20Overview

**Created by:** Shreya Singh on December 02, 2025  
**Last modified by:** Shreya Singh on December 03, 2025 at 10:29 PM

---

**1. Salt System Architecture**
-------------------------------

### **1.1 Core Components**

Salt functions as both a configuration management and monitoring/drift-detection system. Its core components operate as follows:

* Salt Minion  
  Installed on all managed nodes (including golden AMIs) where it performs local execution of state files. Minions connect to the Salt Master using a [ZeroMQ message bus].
* Salt Master  
  A centralized orchestration point responsible for distributing configuration states, executing remote commands, and collecting compliance/detection results.
* State Definitions (Salt States)  
  All configuration definitions are written as declarative state files stored in a Git repository, which serves as the Salt Master's file system. Salt ensures systems match these defined states.

### **1.2 High Availability & Connectivity**

* Salt supports multi-master deployment, enabling minions to subscribe to multiple masters via a load balancer.
* Minions attempt reconnection every 5 minutes if a Master is unavailable.
* Failure of the Salt Master does not block VM provisioning; Minions operate independently until reconnected.

---

**2. Configuration Enforcement & Drift Management**
---------------------------------------------------

### **2.1 Enforcement Modes**

Salt provides both preventative and detective controls:

| Mode | Description |
| --- | --- |
| Detective (Dry-Run Mode) | Shows what changes would occur without enforcing them. Useful for assessing CIS benchmark impacts on migrated workloads. |
| Preventative (Enforcement Mode) | Automatically enforces state compliance and corrects drift. Salt runs reconciliation on a 30-minute interval. |

### **2.2 Drift Detection & Reporting**

Salt minions continuously monitor for deviation from defined configurations.  
The system can:

* Detect configuration drift
* Report drift events to the Salt Master
* Automatically correct drift through enforced state application
* Send audit events and system actions to external systems such as SIEMs

---

**3. Governance, Change Management, and Auditability**
------------------------------------------------------

### **3.1 Git-Based Change Workflow**

Salt enforces a formal change management workflow via Git:

* All Salt states reside in a GitHub repository.
* Branch protection requires reviews before merging.
* Pull Requests provide:

  + Change history
  + Peer approval workflow
  + Traceability for all configuration updates

### **3.2 Security & Segregation of Duties**

* A code owners file ensures security team approval for CIS benchmark-related changes.
* This enforces segregation of duties between:

  + Security (approval)
  + Operations (implementation)
  + Engineering (execution)

### **3.3 RBAC & Access Controls**

Salt supports granular access controls:

* Local system-level RBAC on the Salt Master
* Remote API-level RBAC
* Command-level filtering to prevent high-risk commands
* Ability to create read-only or query-only operational roles

### **3.4 Audit Logging**

Salt provides full auditability:

* All executed actions are tagged with user identity and a unique event ID.
* Events can be shipped to SIEM platforms for centralized monitoring.
* Audit trails with further visualization fulfills the requirements for HITRUST and future FedRAMP considerations.

---

**4. Compliance Strategy for CIS Benchmark Implementation**
-----------------------------------------------------------

### **4.1 New Workloads**

Salt enforces CIS Level 1 compliance immediately for new builds:

* CIS benchmark states are applied during provisioning.
* Automated 30-minute reconciliation ensures continuous compliance.
* Drift detection and remediation operate by default.

### **4.2 Migrated (Brownfield) Workloads**

For workloads originally built manually:

**Phase 1 – Assessment Mode**

* Salt operates in dry-run mode to identify non-compliant configurations.
* Drift is reported but not corrected.
* Wiz scanning is used as an additional detection layer to map compliance gaps.

**Phase 2 – Transition to Enforced Compliance**

* Once remediation plans are defined, CIS states are gradually enforced.
* Long-term strategy replaces manually-built servers with infrastructure-as-code hardened builds.

This multi-phase model reduces risk of breaking production systems while still achieving CIS compliance over time.