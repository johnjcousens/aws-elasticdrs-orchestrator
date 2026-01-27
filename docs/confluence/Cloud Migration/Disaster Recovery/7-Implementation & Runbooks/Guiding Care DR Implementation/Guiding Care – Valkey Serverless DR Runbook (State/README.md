# Guiding Care – Valkey Serverless DR Runbook (Stateless Session Cache Mode)

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5297701333/Guiding%20Care%20%E2%80%93%20Valkey%20Serverless%20DR%20Runbook%20%28Stateless%20Session%20Cache%20Mode%29

**Created by:** Alex Dixon on December 03, 2025  
**Last modified by:** Alex Dixon on December 09, 2025 at 02:06 PM

---

**1. Purpose**
--------------

This runbook defines the disaster recovery (DR) procedure for the **Valkey Serverless** cache in the disaster recovery region when used strictly as a **stateless session caching layer**. In this mode, no data restore is required and the cache is recreated empty during DR activation.

This runbook supports the platform’s established **RTO of 4 hours** and reduces actual activation time to **approximately 30–90 minutes**.

---

**2. Scope**
------------

This runbook applies when:

* The primary region Valkey Serverless cache is unavailable.
* Cached session data does not require preservation during DR.
* A new, empty cache deployment is acceptable for continuity of service.

This procedure applies only to the cache tier; application failover procedures are handled separately.

---

**3. Prerequisites**
--------------------

| **Requirement** | **Expected State** |
| --- | --- |
| CDK support for DR deployment | Enabled and parameterized |
| DR region networking and security | Predefined in CDK context |
| IAM permissions | CDK deployment + Valkey operations |
| Routing update process | Coordinated with application and network teams |
| Application design | Capable of starting with an empty cache |

---

**4. Roles and Responsibilities**
---------------------------------

| **Role** | **Responsibility** |
| --- | --- |
| Cloud Operations | Deploy Valkey into DR region |
| Network Operations | Update routing (DNS, internal service references, VPN/TGW if applicable) |
| Application Team | Validate application behavior and session reinitialization |
| Incident/Change Management | Documentation, communications, approvals |

---

**5. DR Activation Criteria**
-----------------------------

Use this runbook when:

* Valkey in the primary region is unreachable or degraded beyond SLA tolerance.
* A full regional failover has been initiated.
* A DR test requires cache activation in the DR region.

Snapshots are **not** part of this runbook; any reference to backup or restore is intentionally excluded.

---

**6. DR Procedure**
-------------------

---

### **Step 1 — Prepare for Deployment**

Confirm that:

* DR region is designated and available.
* No snapshot restore is required.
* Appropriate CDK parameters are known (SGs, subnets, environment context).

---

### **Step 2 — Deploy Valkey Serverless into the DR Region**

Execute the DR deployment via CDK:


```
cdk deploy \
  --context environment=prod \
  --context region=<DR_REGION> \
  --context drMode=stateless
```


Monitor until the deployment completes with:

* Stack status: **CREATE\_COMPLETE**
* Cache status: **AVAILABLE**

**Estimated time:** 25–60 minutes

---

### **Step 3 — Update Application Routing (If Applicable)**

Update all components that reference the cache endpoint.

| **Component** | **Required Action** |
| --- | --- |
| Application config | Update to new Valkey endpoint |
| Route 53 / service discovery | Update internal DNS names (if used) |
| VPN/TGW routing | Follow the Guiding Care VPN DR runbook (if required) |

**Estimated time:** 5–20 minutes

---

### **Step 4 — Validation**

Perform the following checks after routing updates:

| **Test** | **Expected Result** |
| --- | --- |
| Endpoint connectivity | Cache endpoint reachable on assigned port |
| Application reconnect behavior | New sessions are created without errors |
| Basic cache operations | SET and GET operations succeed |
| Synthetic application tests | User login/session creation works |

**Estimated time:** 10–20 minutes

---

**7. Stabilization**
--------------------

After successful validation:

* Monitor cache metrics for error rates, connection counts, and latency.
* Confirm that new sessions initialize correctly.
* Notify stakeholders that service is now operating from the DR region.

---

**8. Failback (High-Level)**
----------------------------

When the primary region is restored:

1. Deploy a new Valkey Serverless instance in the primary region.
2. Validate application behavior with the primary cache.
3. Update routing back to the primary region.
4. Remove DR region resources as approved.

---

**9. Evidence and Documentation Requirements**
----------------------------------------------

Archive the following for audit and compliance:

| **Evidence Type** | **Storage Location** |
| --- | --- |
| CDK deployment logs | CI/CD artifact registry |
| Cache endpoint and deployment metadata | DR evidence folder |
| Validation results | DR event documentation |
| Routing changes | Change management record |

---

**10. Estimated DR Activation Time**
------------------------------------

| **Phase** | **Duration** |
| --- | --- |
| Deployment | 25–60 minutes |
| Routing changes | 5–20 minutes |
| Validation | 10–20 minutes |

### **Total Expected Time:**

### **30–90 minutes**