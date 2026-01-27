# Migration Decisions

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5069307919/Migration%20Decisions

**Created by:** Kaitlin Wieand on September 04, 2025  
**Last modified by:** Kaitlin Wieand on September 04, 2025 at 01:06 AM

---

Day 1 Migration (Immediate AWS Native)
--------------------------------------

| Component | Migration Strategy | Owner |
| --- | --- | --- |
| SFTP | AWS Native |  |
| SMTP Relay | AWS Native |  |
| Container Registry | AWS Native |  |
| Backup Strategy | AWS Native |  |
| Veeam | AWS Native |  |
| Database Backups | AWS Native |  |
| Proxy Servers | AWS Native |  |
| Provisioning Automation | AWS Native |  |
| VM Snapshots Automation | AWS Native |  |

Day 2 Migration (Phased Approach)
---------------------------------

| Component | Day 1 Strategy | Day 2 Strategy |
| --- | --- | --- |
| Linux Operating System | Continue as-is | AWS Native |
| Delphix | Continue as-is | AWS Native |
| MoveIT Automation | Continue as-is | AWS Native |
| Disaster Recovery Strategy | Continue as-is | AWS Native |

Maintain Current State
----------------------

| Component | Strategy |
| --- | --- |
| Jira Connectivity | Use as-is |
| Salesforce Connectivity | Use as-is |
| IBM ILMT | Use as-is |
| IBM MQueue | Use as-is |
| Active Directory | Use as-is |

Pending Decision
----------------

| Component | Current Status |
| --- | --- |
| RedHat Identity Manager | Continue as-is for Day 1 (Day 2 strategy TBD) |