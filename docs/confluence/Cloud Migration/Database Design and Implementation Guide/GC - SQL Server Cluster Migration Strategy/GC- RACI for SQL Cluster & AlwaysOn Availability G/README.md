# GC: RACI for SQL Cluster & AlwaysOn Availability Group setup

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5177409642/GC%3A%20RACI%20for%20SQL%20Cluster%20%26%20AlwaysOn%20Availability%20Group%20setup

**Created by:** Sai Krishna Namburu on October 17, 2025  
**Last modified by:** Sai Krishna Namburu on October 17, 2025 at 02:17 PM

---

Finalize the point of contact/ person responsible for the below high level tasks that are involved the GC SQL Server migration:

*In-Scope Systems (GC Pilot)*

**SQL Clusters (Replatform):**

* Cluster 1: gcpfsqle01-id3, gcpfsqle02-id3
* Cluster 2: SCLR-SPR03-LAX3, SCLR-SPR04-LAX3 (moved to wave 2a, not on wave 1)

**Standalone Servers:**

* SQL Server (MGN-rehost): UNHGSQLE02-LAX3
* **MongoDB nodes (MGN-rehost):** gcpfmone01-iad3, sclrmonp01-lax3, sclrpmp01-lax3

RACI Matrix

Recommendations : <https://docs.aws.amazon.com/prescriptive-guidance/latest/sql-server-ec2-best-practices/welcome.html>

|  | **AWS ProServe** | **GC Database Team** | **GC Infra/DevOps Team** | **Application Team** | **Devops** |
| --- | --- | --- | --- | --- | --- |

|  | **AWS ProServe** | **GC Database Team** | **GC Infra/DevOps Team** | **Application Team** | **Devops** |
| --- | --- | --- | --- | --- | --- |
| Performance metrics Gathering for  (for infra provisioning on AWS) | R | A | C | I |  |
| Compute provisioning | R | A | C | I |  |
| Storage provisioning | R | A | C | I |  |
| Network Requirements (AWS NFW/SG) | R | A | C | I |  |
| Disk Management (allocating storage drives) |  |  |  |  |  |
| HE internal N/W tickets |  |  |  |  | R ?? |
| Windows Cluster Installation (Witness - EFS? , S3? ) | C | A | R |  |  |
| AD/DNS works | C | A | R | I |  |
| SQL server DB software Installation | C | A/I | R |  |  |
| SQL Cluster configuration | C | A/I | R | I |  |
| SQL AOAG setup | C | R | A | I |  |
| DB Backup Storage setup (S3/SGW) | R | A | C | I |  |
| Failover DB tasks (cutover) | C/A | R | C/I | I |  |
| Post Migration DB tasks | C | A | A | I | R |
| Troubleshooting App/Db connections | C | A | A | I | R |
| Application Functionality & validation | I/A | I/A | I | R (QA team) |  |
| Data Interface Connectivity Test (Mongo etc) |  | C |  |  | R |
| Sql server monitoring (foglight on-premises, including FW rules) |  | R |  |  |  |

**IAC development (for infra provisioning) - for which setps? - Is home grown HE standard IAC available?**