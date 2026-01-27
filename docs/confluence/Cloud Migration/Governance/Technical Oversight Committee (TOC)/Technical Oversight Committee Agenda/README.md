# Technical Oversight Committee Agenda

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5067636778/Technical%20Oversight%20Committee%20Agenda

**Created by:** Kaitlin Wieand on September 03, 2025  
**Last modified by:** Chris Falk on January 07, 2026 at 09:22 PM

---

Date
----

January 07, 2026

Discussion Topics
-----------------

| **Topic** | **Description** | **Owner** | **Notes** |
| --- | --- | --- | --- |
| HRP DB/App AZ Spread | Decision to colocate each customer in a single AZ | Chris | Review this decision and agree/disagree. Each HRP prod/nonprod customer will have all its instances in one AZ, but customers will be placed evenly in different AZs from each other.  APPROVED |
| WSO2 in public subnets |  | Chris | Until migration to API Gateway, WSO2 proxy will be in public subnets (usually reserved for LB only)  NOTE: Jim to talk to Mark about the WSO2 migration generally and if options exist to move APIGW |
| EKS Tiger Team | Identify a team to own EKS patterns and skill up to support internal needs | Jim | Handed to Ted’s team for now. |
| HRP Database DR |  | Chris F | Failback time and snapshot hydration preclude use of DRS for large DB workloads; recommend Oracle Dataguard replication to/from DR region |
| HYD access to DB backups | Copy some DB backups local to the Hyderabad teams |  | Global Accelerator for VPN, backup option for S3 bucket replication target in ap-south-2 (Hyderabad), with tooling to generate pre-signed URLs |
| Operations readiness |  | Cris G + Jim | Update on state of operations readiness for supporting AWS workloads, gaps to close before prod cutovers in March?  Examples: if Sutter needs a new server or scaling change after cutover, what is the process and owning team?  NOTE: For now, BU engineering teams own their own. Financial process involved as well. |
| LZA Ownership |  | Jim | Handed to Ted’s team for now. |

Action items
------------

* Chris to create Teams chats as forums for LZA, DevOps pipeline, and EKS topics; Ted’s team first line For LZA and EKS ownership, OK with Ted’s team for now, potential for change in re-org.

---

Date
----

November 26, 2025

Discussion topics
-----------------

| **Topic** | **Description** | **Owner** | **Notes** |
| --- | --- | --- | --- |
| Last meeting review | Check up on actions from last meeting | Chris Falk |  |
| EKS Tiger Team | Identify a team to own EKS patterns and skill up to support internal needs | Cris Grunca? | AWS has been handling requests outside our scope to support HRP but as we deploy more clusters and environments we need to hand off ownership fully |
| DR | Assumptions and automation process | Chris Falk | Also, consider what GC might need as that design is wrapping up |
| EKS Certs |  | Ted O’Hayer |  |

Action items
------------



---

Date
----

November 12, 2025

Discussion topics
-----------------

| **Topic** | **Description** | **Owner** | **Notes** |
| --- | --- | --- | --- |
| Backup Policy | Understand policies for backup requirements for BUs | Jim Fallon | 5-1-Backup-Management-Decision |
| Cloud Platform + Operations Team | What is the process to service post migration AWS infrastructure and support requests, and who is the team? | Cris Grunca | Requests need to go to Jim’s team for now as the org evolves. Cris’s team as a shadow and taking on more. |
| DevOps IaC Pipelines | Review remaining scope and final design | Mark Mucha |  |
| Elasticache for Valkey | Decision: Separate serverless Redis/Valkey clusters for each environment | Jim Kaplan | Need to be separate (lots of read only data) but each customer can have different versions of the code. |

Action items
------------

* ✅ Chris to connect with Gary and migration team on VPN/regular prod/nonprod accounts, can we drop the non VPN accounts?

  + Decision to drop the extra accounts and consolidate VPCs into the prod and nonprod accounts, Gary to complete by November 14, 2025
* ✅ Implement same backup policy for GC 14d retention daily backups; proceed with story for backup policies. Update documentation to reflect and communicate decision to GC team.

  + Documentation updated
  + Notified the group in the [Cloud Team channel](https://teams.microsoft.com/l/message/19:9438521c5af84e5bbe4d2ca7e625f38e@thread.v2/1763061939866?context=%7B%22contextType%22%3A%22chat%22%7D).
  + AWSM-3808ba6e06f-7495-3c95-8cfd-817d67fc0380System Jira updated for implementation next sprint
* Chris to schedule review of devops pipeline doc and architecture
* ✅ Ted/Jim to discuss and define a short term MVP process to intake AWS support and change requests tomorrow (+Cris G)

  + Ted O'Hayer, can you note the process link here?
* Jim to check with Marc on Redis separation of environments or namespaces

Date
----

October 29, 2025

Discussion topics
-----------------

| **Topic** | **Description** | **Owner** | **Notes** |
| --- | --- | --- | --- |
| AWS Resource Naming Scheme | Read, discuss, and potentially approve AWS resource naming scheme | Chris Falk |  |
| Cross-BU process discussion | Cross-BU process discussion on baseline security rules implementation status and ongoing PR review coordination | Chris Falk |  |
| VMware import to AMI for HRP |  | Ted O'Hayer |  |

Action items
------------

Date
----

September 03, 2025

Discussion topics
-----------------

| **Topic** | **Description** | **Owner** | **Notes** |
| --- | --- | --- | --- |
| AWS Native Decisions | Discuss some tenets around making decisions to adopt AWS native solutions in a way that doesn’t impact the migration timeline or scope | Chris Falk | * Consolidation while keeping timeline and staying on budget throughout migration |
| HRP/GC Dependencies - Decisions Needed | Review dependencies for any key decisions this group needs to consider | Chris Falk, | * Most if not all decisions were made in the moment |
| Lift and Shift | Identify pieces within migration that ARE and ARE-NOT lift and shift |  |  |

Action items
------------

Add action items to close the loop on open questions or discussion topics:

3
e535b96f-12be-4c84-88d2-4b90825e8ca9
incomplete