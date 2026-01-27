# Guiding Care SFTP Disaster Recovery Detailed Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5286428782/Guiding%20Care%20SFTP%20Disaster%20Recovery%20Detailed%20Design

**Created by:** Venkata Kommuri on November 30, 2025  
**Last modified by:** Chris Falk on December 18, 2025 at 08:13 PM

---

**Document Version:** 2.0  
**Last Updated:** November 2025  
**Service:** AWS Transfer Family (SFTP/FTPS)  
**Target RTO:** 4 hours | **Target RPO:** 15 minutes  
**Primary Regions:** US-East-1 (Virginia), US-West-2 (Oregon)  
**DR Regions:** US-East-2 (Ohio), US-West-1 (N. California)  
**Traffic Management:** AWS Global Accelerator with health-based routing  
**Replication Method:** S3 Cross-Region Replication, Global Accelerator Health Checks, Secrets Manager Replication

**GUIDING CARE HEALTHCARE ENVIRONMENT - SFTP FILE TRANSFER WORKLOADS:** This runbook is specifically designed for the Guiding Care healthcare application environment where SFTP services support regulatory data exchange, inbound batch processing via Apache Airflow, outbound document delivery (faxes and letters), and integration with external healthcare systems. SFTP operations must maintain HIPAA compliance and support critical healthcare workflows.

#### ⚠️ IMPORTANT DISCLAIMER - GUIDING CARE CUSTOMIZATION REQUIRED

**All scripts and configurations in this runbook are TEMPLATES and must be customized for Guiding Care-specific requirements before implementation.**

Guiding Care SFTP Requirements Analysis
---------------------------------------

### Current SFTP Usage Patterns

#### Inbound Data Processing (Batch ETL)

* **Frequency:** Nightly batch processing via Apache Airflow
* **Data Types:** Healthcare claims, member data, provider information, clinical data
* **File Formats:** CSV, XML, HL7, X12 EDI formats
* **Processing:** Files trigger Airflow DAGs for ETL workflows
* **Intermediate Storage:** MongoDB used for temporary data storage during processing
* **Performance Impact:** Batch processing impacts system performance during execution

#### Outbound Document Delivery

* **Document Types:** Faxes, letters, reports, notifications
* **Recipients:** Healthcare providers, patients, regulatory agencies
* **Delivery Method:** SFTP push to external systems
* **Compliance:** Must maintain audit trail for regulatory compliance

#### Third-Party Integrations

* **Healthcare Partners:** Payers, providers, clearinghouses
* **Regulatory Agencies:** State and federal healthcare reporting
* **Service Providers:** Document generation, fax services

### DR Requirements

| Requirement | Target | Implementation |
| --- | --- | --- |
| Recovery Time Objective (RTO) | 4 hours | DNS failover with Route 53 health checks |
| Recovery Point Objective (RPO) | 15 minutes | S3 Cross-Region Replication (typically <15 minutes) |
| Data Integrity | 100% | S3 versioning and replication validation |
| Compliance | HIPAA, SOC 2 | Encryption at rest/transit, audit logging |
| Availability | 99.9% | Multi-region active-active architecture |

Multi-Region SFTP Architecture
------------------------------

### Regional Deployment Strategy with Global Accelerator

![GC-SFTP-DR-Design-GC-SFTP-DR-Architecture.drawio_(1).png](images/GC-SFTP-DR-Design-GC-SFTP-DR-Architecture.drawio_(1).png)


```

Key Features:
• Global Accelerator provides 2 static anycast IPs for simplified firewall rules
• Health checks monitor NLB endpoints in each region (30-second intervals)
• Automatic failover to healthy regions within 30 seconds
• Traffic weights control distribution (100 = active, 0 = standby)
• Client affinity ensures session persistence to same region
        
```


### Active-Active Configuration

All four regions maintain active SFTP servers that can accept connections at any time. This provides:

* **Geographic Load Distribution:** Clients can connect to nearest region for optimal performance
* **Instant Failover:** No warm-up time required during DR events
* **Testing Without Impact:** DR regions can be tested without affecting production
* **Regional Isolation:** Issues in one region don't affect others

Failover Procedures
-------------------

### Automatic Failover with Global Accelerator (Recommended)

**Automatic failover is the recommended approach for SFTP DR.** AWS Global Accelerator continuously monitors endpoint health and automatically redirects traffic to healthy regions when failures are detected.

* **Detection Time:** 30 seconds (health check interval)
* **Failover Time:** Immediate (no DNS propagation needed)
* **Total RTO:** 15 minutes (contractual)
* **Manual Intervention:** None required
* **Client Impact:** Transparent - clients continue using same static IPs

#### 13.1.1 How Automatic Failover Works

1. **Health Monitoring:** Global Accelerator performs TCP health checks every 30 seconds on NLB endpoints in each region
2. **Failure Detection:** If 3 consecutive health checks fail (90 seconds), endpoint is marked unhealthy
3. **Traffic Rerouting:** New connections are immediately routed to healthy endpoints in other regions
4. **Geographic Preference:** Traffic routes to nearest healthy region (East Coast → US-East-2, West Coast → US-West-1)
5. **Automatic Recovery:** When primary region recovers and passes health checks, traffic automatically returns

Failback Procedures
-------------------

### Planned Failback with Global Accelerator

**Failback should be performed during a maintenance window to minimize disruption.**

Recommended failback window: Low-traffic period (e.g., weekends or after batch processing completes)