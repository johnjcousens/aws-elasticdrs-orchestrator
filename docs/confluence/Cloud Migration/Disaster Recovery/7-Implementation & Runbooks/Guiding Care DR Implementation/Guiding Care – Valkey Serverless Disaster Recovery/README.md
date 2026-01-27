# Guiding Care – Valkey Serverless Disaster Recovery Strategy

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5294096446/Guiding%20Care%20%E2%80%93%20Valkey%20Serverless%20Disaster%20Recovery%20Strategy

**Created by:** Alex Dixon on December 02, 2025  
**Last modified by:** Chris Falk on December 18, 2025 at 08:16 PM

---

This document assumes that the RTO and RPO from the DR assessment applies to Valkey. It also is making assumptions based on the CDK build out for Valkey. Also, assumes that no application modification is needed other than Route 53 being maintained to the proper endpoint. Caching is used for sessions only. Data does not need to transverse to secondary, thus RPO is N/A.

**1. Purpose**
--------------

This document defines the disaster recovery (DR) approach for the **Valkey Serverless** cache component supporting the Guiding Care platform. The strategy aligns to being the first requirement for the documented **RTO of 4 hours** and **RPO is N/A** due to no data replication needed, prioritizing controlled recovery and cost efficiency rather than continuous replication.

---

**2. Current State**
--------------------

The Valkey cache is provisioned using AWS CDK through a reusable construct (CfnServerlessCache). The construct already supports:

* Backup retention (snapshot\_retention\_limit)
* Optional snapshot restore (snapshot\_arns\_to\_restore)
* Security and networking controls (KMS, SGs, subnets)

---

**3. DR Strategy Recommendation**
---------------------------------

### **Recommended Model: Build In DR Region via CDK**

Based on the RTO and RPO requirements, using CDK (IaC) as a recovery model is the most suitable approach. Continuous replication (such as Global Datastore or active/active patterns) is unnecessary and cost-inefficient for the stated objectives.

The recommended pattern:

* **Primary Region:** Experiences an outage, no snapshots needed as only caching sessions.
* **DR Region:** create a new Valkey Serverless via CDK and having customer restart sessions.

This approach ensures the cache can be rebuilt within the allowed four-hour window, only taking as long as CDK takes to run.

---

**4. Architecture Summary**
---------------------------

### **Primary Region Components**

| **Component** | **Requirement** |
| --- | --- |
| Valkey Serverless Cache | Existing CDK implementation retained |
| Backup Retention | Managed via snapshot\_retention\_limit |
| Snapshot Copy | Not needed at this time for just caching sessions |
| Automation | EventBridge + Lambda (Future state where CDK can be automated.) |

### **DR Region Component**

| **Component** | **Requirement** |
| --- | --- |
| DR Cache Stack | Created via CDK deployment when required |
| Restore Source | Not needed, no data other sessions in Valkey |
| Networking & Security | Same configuration structure as primary region (parameterized via CDK context) |

### **Endpoint Abstraction and DNS Strategy**

Valkey Serverless generates a unique hostname with each deployment. To prevent application configuration changes during failover, a DNS abstraction layer must be used.

A Route 53 DNS entry serves as the **main Valkey endpoint** for all Guiding Care services. This DNS entry is a **CNAME** (or Alias) pointing to the active Valkey Serverless endpoint.

During DR activation:

* A new Valkey instance is deployed in the DR region.
* The CNAME value is updated to point to the DR endpoint.
* Applications automatically reconnect after DNS TTL expires.

#### **DNS Requirements**

* TTL: **30–60 seconds** for rapid failover.
* DNS must be hosted in Route 53 private hosted zones.
* Applications must honor DNS TTL.
* No application code changes are required when DNS abstraction is used.

Healtchecks could also be considered for automating failover.

---

**5. Failover Workflow**
------------------------


```
1. Detect primary region failure
2. Deploy Valkey Serverless cache using CDK 
4. Wait for cache status = AVAILABLE
5. Update application routing (DNS / internal service references / network paths), if applicable
6. Validate operations and resume service
```


Expected duration: **.5-1.5 hours** mainly accounting for CDK, cache provisioning, Routing/DNS resolution, and application validation.

---

**6. CDK Integration Requirements**
-----------------------------------

The existing construct is compatible with the DR model and requires only the following additions:

| **Enhancement** | **Description** |
| --- | --- |
| Scheduled Snapshot Logic (Only future state if caching more than customer sessions\*) | Implemented via EventBridge rule + Lambda |
| Cross-Region Copy (Only future state if caching more than customer sessions\*) | Automated snapshot transfer to DR region |
| DR Stack Parameters | Context-based configuration for region, snapshot ARN, SGs, and subnets |
| Pipeline Integration | Optional execution through CI/CD or Step Functions |

---

**7. Testing and Validation**
-----------------------------

To maintain DR readiness, the following validation schedule is recommended:

| **Test Type** | **Frequency** |
| --- | --- |
| Snapshot creation and replication verification (Only future state if caching more than customer sessions\*) | Monthly |
| DR restore test (CDK deployment + recovery) | Quarterly |
| End-to-end application failover exercise | Annually or after major release |

---

**8. Risks and Considerations**
-------------------------------

| **Area** | **Consideration** | **Mitigation** |
| --- | --- | --- |
| Restore Time Variability(Only future state if caching more than customer sessions\*) | Restore duration depends on dataset size | DR test timing and baseline tracking |
| Routing Dependencies | Cache failover must align with broader Guiding Care connectivity model | Coordination with VPN failover design |
| Operational Drift | Primary and DR configuration must remain consistent | CDK-driven deployments prevent divergence |

---

**9. Summary**
--------------

A snapshot-based Backup and Restore model provides an efficient, repeatable, and cost-effective disaster recovery solution for Valkey Serverless in the Guiding Care platform. This model fully supports the required **RTO (4 hours)** and **RPO (N/A)** with a CDK-driven restore process.