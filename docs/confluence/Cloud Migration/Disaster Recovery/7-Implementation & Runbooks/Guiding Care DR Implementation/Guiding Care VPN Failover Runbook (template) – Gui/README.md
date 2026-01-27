# Guiding Care VPN Failover Runbook (template) – Guiding Care Customer Access

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5272600593/Guiding%20Care%20VPN%20Failover%20Runbook%20%28template%29%20%E2%80%93%20Guiding%20Care%20Customer%20Access

**Created by:** Alex Dixon on November 24, 2025  
**Last modified by:** Alex Dixon on November 26, 2025 at 01:45 PM

---

### **Purpose**

This runbook describes the steps and validation procedures required to initiate and verify VPN failover for a customer during a regional outage or planned DR event.

---

### **Scope**

☑ Applies to all GuidingCare customer-facing VPN connectivity

☑ Includes AWS region-to-region failover

☑ Includes validation steps for customer access and platform reachability

---

### **Runbook Owner**

| **Field** | **Value** |
| --- | --- |
| Primary Owner | (Team/Name) |
| Backup Owner | (Team/Name) |
| Escalation Path | Unknown |

---

**Procedure**
-------------

### **Step 1 — Confirm Failover Trigger**

| **Condition** | **Yes/No** |
| --- | --- |
| Primary region outage confirmed? |  |
| Customer workload active or restored in DR region? |  |
| Application and database passed DR validation? |  |

\*Failover **must not begin** until workloads are restored.(?)

---

### **Step 2 — Enable DR VPN Tunnel**

| **Action** | **Notes** |
| --- | --- |
| Activate VPN tunnel on Palo Alto firewalls in DR region | Pre-configured |
| Apply corresponding NAT mapping | Confirm correct customer mapping; should be precongifured as network design |
| Disable primary region tunnel (optional depending on design?) | Avoid asymmetric routing |

---

### **Step 3 — Routing Updates**

☑ Update route table entries (TGW, firewall policies as required)

☑ Validate no overlapping route advertisements

If BGP-enabled customers exist, apply:


```
BGP preference update → DR region higher priority metric
```


---

### **Step 4 — Validation Checklist**

| **Test** | **Status** |
| --- | --- |
| VPN tunnel established |  |
| Ping test from customer endpoint |  |
| Application URL accessible |  |
| API integration validation |  |
| Database access validation |  |
| Performance baseline test |  |

---

### **Step 5 — Customer Notification**

Template (example):

“Connectivity has been shifted to the disaster recovery region. Please validate access. We will notify you when the primary region is restored.”

---

### **Step 6 — Monitoring**

Suggested: Minimum 4-hour observation window:

* Palo Alto VPN uptime
* Latency vs baseline
* Error rates and session drops

---

### **Rollback Procedure**

Reverse steps:

1. Restore tunnel to primary region
2. Drop priority/disable DR tunnel
3. Confirm routing normalization
4. Validate connectivity

---

### **Evidence Logging (if required?)**

Store in (Confluence placeholder):


```
Confluence → DR Evidence Repository → YYYY-MM-DD event folder
```


Include:

* Screenshots
* Network logs
* Validation results
* Stakeholder signoff