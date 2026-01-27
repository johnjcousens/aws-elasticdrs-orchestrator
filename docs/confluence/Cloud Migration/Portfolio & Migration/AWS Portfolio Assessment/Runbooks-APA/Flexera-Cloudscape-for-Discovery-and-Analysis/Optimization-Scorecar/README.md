# Optimization-Scorecar

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867035065/Optimization-Scorecar

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:53 AM

---

---

title: Optimization Scorecard
-----------------------------

Overview
========

This document will provide guidance and best practices around using the RISC Networks ITOA Platform, and specifically the Optimization Scorecard, to support Cloud Readiness and Cloud Migration use cases.

Assumptions and Pre-requisites
==============================

The following outlines the assumptions and pre-requisites that this document and the guidance contained herein are based on.

* You must have a healthy assessment and follow all general best practices and standard processes that apply. This includes, but is not limited to, the following:
  + All in-scope assets must be fully discovered and accessible (i.e. Device Type of Windows Server, Virtual-Windows Server, Generic Server, or Virtual-Generic Server)
  + All in-scope assets must be licensed and successfully collecting data (Summary of Collection dashboard)
  + All in-scope assets must be organized and placed into Application Stacks that represent the customers environment in a manner that is aligned with the overall project goals
* You must determine and implement a tagging methodology / approach that will support the customers requirements and reflect the business and technical goals of the Cloud base initiative.

Customer Input (Tags)
=====================

The following types of data can be incorporated into the platform as tags. This allows incorporation of external attributes, or “soft data”, into Cloud Readiness or Cloud Migration decision criteria. The table below provides an example list of possible tags. Each customer will likely have a different set of priorities based on the specifics of their environment. For example, the customer may need to evacuate a specific location or data center before lease expiration. In this case location may be a primary factor in prioritization. Other customers may prioritize applications that are owned by infrastructure teams for the initial set of migrations.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th colspan="1">Tag Key</th>
<th colspan="1">Example Tag Value</th>
<th colspan="1">Tag Type</th>
<th colspan="1">Comment</th>
</tr>
<tr>
<td>
Department / Business Unit
</td>
<td>
IT, HR, Sales
</td>
<td>
Stack, Asset
</td>
<td>
Identifies which department or business unit owns the application or asset
</td>
</tr>
<tr>
<td>
Supported By
</td>
<td>
Business, Outsourced
</td>
<td>
Stack, Asset
</td>
<td>
Support Organization, Department, or Individual
</td>
</tr>
<tr>
<td>
Environment
</td>
<td>
Test, Dev, Prod
</td>
<td>
Stack, Asset
</td>
<td>
Identifies the application environment for the application or asset
</td>
</tr>
<tr>
<td>
Data Type
</td>
<td>
HIPPA, PII, PCI-DSS
</td>
<td>
Stack
</td>
<td>
Identifies if application data is subject to compliance requirements
</td>
</tr>
<tr>
<td>
Application Priority
</td>
<td>
Mission Critical, Mission Essential, Tactical
</td>
<td>
Stack
</td>
<td>
Identifies the criticality of the application to the business and inherent
                    risk associated with migration
</td>
</tr>
<tr>
<td>
Datacenter / Location
</td>
<td>
US-Virginia
</td>
<td>
Asset
</td>
<td>
Datacenter or Location designation
</td>
</tr>
<tr>
<td>
Application Lifecycle / Status
</td>
<td>
Deploy, Maintain, Retire, End of Support
</td>
<td>
Stack
</td>
<td>
Identifies the lifecycle stage or overall status for the application stack
</td>
</tr>
<tr>
<td>
Business Disposition
</td>
<td>
Retain, Replace, Refactor,Retire
</td>
<td>
Stack, Asset
</td>
<td>
Business decision for the disposition of application stack or asset
</td>
</tr>
<tr>
<td>
Risk
</td>
<td>
High, Medium, Low
</td>
<td>
Stack
</td>
<td>
Business disposition of application in terms on overall risk. Is application
                    stack well known / documented, is it revenue producing, etc..
</td>
</tr>
</tbody>
</table>



Rule Based Tags

Migration Strategy (rscore)
---------------------------

The RISC Networks ITOA Platform provides a default set of rscore tags that can be incorporated into Cloud suitability or migration decision criteria. The default set of rscore tags, and the rule logic behind them are documented within the glossary.

<https://portal.riscnetworks.com/app/documentation/?path=/using-the-platform/glossary/>

Because every customer can have a slightly different set of priorities, it is recommended that customers create a customized rscore or Migration Strategy tag. For example, some customers may want to prioritize opportunities to replatform based on the PaaS offerings of the Cloud provider in order to take advantage of the operational efficiencies and scale that these services provide. Other customers may choose to standardize on a minimum OS level as part of a migration effort. In this case the following approach can be used, and modified as needed, to support a custom rscore or Migration Strategy tag.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th colspan="1">Tag Key</th>
<th colspan="1">Tag Value</th>
<th colspan="1">Criteria</th>
<th colspan="1">Tag Type</th>
<th colspan="1">Comment</th>
</tr>
<tr>
<td>
Migration Strategy
</td>
<td>
Rehost
</td>
<td>
Use Assets page and filter for Windows (2012, 2016, 2019), Linux (EL6,
                    EL7)
</td>
<td>
Asset
</td>
<td rowspan="3">
Used to establish "level of effort" for a given app stack. Devices are
                    tagged based on listed criteria and rolled up at an app stack level to
                    show distribution of the different rscore tags. A device could have multiple
                    tags depending on the approach. For example 1 tag for rehost because of
                    OS compatibility and 1 tag for replatform because its running MySQL.

<br/>

<br/>
<br/>
</td>
</tr>
<tr>
<td>
Migration Strategy
</td>
<td>
Replatform
</td>
<td>
Use Assets page and filter for Windows (2000, 2003, 2008), Linux (EL5)
</td>
<td>
Asset
</td>
</tr>
<tr>
<td>
Migration Strategy
</td>
<td>
Refactor or Replatform
</td>
<td>
Use Assets page and filter for AIX, HPUX, or Solaris
</td>
<td>
Asset
</td>
</tr>
<tr>
<td>
Migration Strategy
</td>
<td>
Replatform or Replatform-PaaS
</td>
<td>
Use Advanced Rulesets / Application Runpath and search for processes associated
                    with MySQL, MSSQL, PostgreSQL, Oracle, Memcached, Redis, MongoDB etc…
</td>
<td>
Asset
</td>
<td>
Can be used to identify opportunities for moving to PaaS solutions like
                    RDS, NoSQL (e.g. DynamoDB), Cache (Redis, Memcached) etc… This would need
                    customer / partner input.
</td>
</tr>
</tbody>
</table>



Cloud Criteria
--------------

There are many factors that indicate an applications readiness for Cloud migration and the level of effort required to migrate it. For example, applications that use shared NFS file systems may require special consideration to determine how to support this shared storage dependency in the Cloud. File system data can be migrated to AWS EFS or the application can be reconfigured to use AWS S3. For this miscellaneous set of criteria, we can implement a Cloud Criteria tagging methodology. The following table includes examples of this tagging methodology.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th colspan="1">Tag Key</th>
<th colspan="1">Tag Value</th>
<th colspan="1">Criteria</th>
<th colspan="1">Tag Type</th>
<th colspan="1">Comment</th>
</tr>
<tr>
<td>
Cloud Criteria
</td>
<td>
Cluster
</td>
<td>
Use Advanced Rulesets / Application Context and search for Microsoft Cluster
                    Services
</td>
<td>
Asset
</td>
<td>
Used to identify assets / application stacks with running HA solutions
</td>
</tr>
<tr>
<td>
Cloud Criteria
</td>
<td>
NFS Mount
</td>
<td>
Use Advanced Rulesets / Filesystem and search for NFS
</td>
<td>
Asset
</td>
<td>
Used to identify assets / application stacks with NFS mounts
</td>
</tr>
</tbody>
</table>



Tag Consumption
===============

Now that we have thought through and implemented a tagging methodology the question becomes “now what?”. How can these tags be leveraged to support the desired outcome?

On a basic level the tags and tag values can be consumed in several places within the platform. For example, you can view device and stack level tags from the View Individual Application Stack (VIAS) page thus providing additional context when reviewing an application with the Application Owner. Device tags can be viewed in the Server table and the Tag Distribution option can be used to visualize the tag value composition of that stack. In other words, does the stack have multiple tiers, is it completely rehostable or are there replatform elements as well. Lastly, stack level tags are included in the VIAS summary report.

The Consume Intelligence >> Application Classification page provides a way to visualize how the tag values are distributed across the environment at a high level. For example, you can visualize the customers use of different Database systems (MSSQL, Oracle, MySQL, etc.) when filtering on the Database Type tag assuming it was implemented.

The remainder of this document will focus on using these tags in the context of the Optimization Scorecard.

Optimization Scorecard
======================

The Migration Scorecard provides an automated way to rank your application stacks for Cloud migration priority based on criteria of your choosing. The Migration Scorecard can also be used to rank for Cloud readiness or other use cases depending on the criteria used and how each criterion is weighed. This document will focus on creating a prioritized list of applications for migration.

Example - RISC Basic Scorecard
------------------------------

We will start with a basic use of the scorecard to establish rank and prioritization of application stacks. This basic approach will incorporate standard criterion that should exist in any assessment. The following table describes the criteria that can be used, and the associated weight applied.

| **Category** | **Tag Key** | **Tag Value** | **Weight** |
| --- | --- | --- | --- |
| Predictive Cloud Run Cost | NA | NA | 50 |
| Low Connectivity | NA | NA | 75 |
| Low Device Count | NA | NA | 30 |
| Small Storage Footprint | NA | NA | 30 |
| Device Tags | Rscore or Migration Strategy | Rehost | 60 |

Example - RISC Advanced Scorecard
---------------------------------

A more advanced use of the scorecard will incorporate customer input and rule-based tags for a broader approach to establishing rank and prioritization of application stacks. The following table describes the criteria that can be used and the associated weight applied.

| **Category** | **Tag Key** | **Tag Value** | **Weight** |
| --- | --- | --- | --- |
| Predictive Cloud Run Cost | NA | NA | 50 |
| Low Connectivity | NA | NA | 75 |
| Low Device Count | NA | NA | 30 |
| Small Storage Footprint | NA | NA | 30 |
| Device Tags | Rscore or Migration Strategy | Rehost | 60 |
| Device Tags | Environment | Test, Development, QA | 50 |
| Stack Tags | Risk | Low | 75 |
| Stack Tags | Risk | Medium | 60 |