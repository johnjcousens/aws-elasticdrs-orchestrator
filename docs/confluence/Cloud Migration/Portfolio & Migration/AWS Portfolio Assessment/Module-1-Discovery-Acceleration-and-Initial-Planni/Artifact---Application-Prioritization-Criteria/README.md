# Artifact---Application-Prioritization-Criteria

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867066370/Artifact---Application-Prioritization-Criteria

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:53 AM

---

| GreenTemplate | Draft | In Review | Baseline |
| --- | --- | --- | --- |

---



---

Overview
========

The objective of application prioritization is to select the application attributes (typically 2 to 10) that will be used to establish the order in which the applications will be moved to AWS, and then assigning a corresponding score/weighting to the possible values of those attributes. Next, to define each attribute importance level for prioritization.

For example, if two attributes are being considered, such as Business Unit and Environment Type, the first step is to define the score for each possible value for those attributes. Let's assume in this example that there are three Business Units: Marketing, Retail, and Sales. Let's define what is the relative score of each of them. If the allowed scoring range is 0-100, a value in this range will be assigned to each Business Unit, let's assume 30 for Marketing, 50 for Retail, and 70 for Sales. For the Environment Type attribute, let's assume values Development, Test, and Production, with scores 20, 40, and 60 respectively. At this stage, these two attributes (Business Unit and Environment Type) will be considered equally important. That means that these two attributes will influence the ranking in the same way according to the score assigned to its values. However, there could be cases where it is more important to prioritize based on one of them. For this example, let's assume that it is more important to prioritize based on Environment Type rather than Business Unit. The next step will be to establish Environment Type as having more importance/relevance for prioritization of applications. The result of giving more relevance to an attribute than other is that all values of the Business Unit attribute (less important in this example), will be multiplied by a value that is less than 1 (e.g., 0.8) reducing the original score of its values and its position in the ranking. On the other hand, Environment Type (more important in this example) will be multiplied by 1, keeping its original score. The relevance factor helps to further differentiate the attributes when the raking does no produce a clear differentiation.

Use the [MPA tool](http://mpa-proserve.amazonaws.com/) (available to AWS Employees and Partners) to prioritize applications. To use MPA, It will be required to export all application and infrastructure data from the discovery tool (or equivalent repository) and import it into MPA. Request permission from the data owner to upload their application and infrastructure data into MPA.

The result of prioritization will be a ranking of applications. If the scoring is correct, the top 20 applications should be good candidates to select from for initial migration and will be aligned to the desired criteria. If you do not generally agree with the outcome, adjust the criteria and recreate the list. It takes several iterations to obtain a baselined criteria.

Consider also the distribution of applications alongside the ranking, if too many applications (i.e., 10 or more) are clustered in the same ranking number, then review the criteria and consider using further attributes so that the result is an evenly distributed ranking with enough differentiation between small groups of workloads. Likewise, consider the complexity (e.g., number of dependencies, architecture, scale, compliance, etc.) of the applications being clustered together in the ranking. It is recommended to avoid migrating many business complex/critical applications at the same time. Adjust the criteria so that complex applications are also evenly distributed across the ranking.

Selected attributes for pioritization
=====================================

The following table contains a base model for prioritization. This model can be used for initial prioritization during the Portfolio Discovery and Initial Planning stage in order to prioritize simple workloads. Work with the relevant stakeholders on subsequent portfolio stages to iterate and update this model and to align prioritization to business drivers.

**Notes:**

* Add/Remove attributes if necessary.
* The possible values require to be updated as per actual data.
* Review and update score values.
* If the tool being used supports prioritization of applications based on infrastructure attributes such as OS, consider adding those as High relevance with higher scoring values for cloud supported versions.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>Attribute</th>
<th>Possible Values</th>
<th>Score</th>
<th colspan="1">Importance/relevance</th>
</tr>
<tr>
<td rowspan="3">Environment</td>
<td>test</td>
<td>60</td>
<td rowspan="3">

<br/>

High (1x)
</td>
</tr>
<tr>
<td colspan="1">dev</td>
<td colspan="1">40</td>
</tr>
<tr>
<td colspan="1">prod</td>
<td colspan="1">20</td>
</tr>
<tr>
<td rowspan="2">Regulatory Requirements</td>
<td colspan="1">None</td>
<td colspan="1">60</td>
<td rowspan="2">
High (1x)
</td>
</tr>
<tr>
<td colspan="1">other</td>
<td colspan="1">10</td>
</tr>
<tr>
<td rowspan="2">
<br/>Compliance Framework</td>
<td>none</td>
<td>60</td>
<td rowspan="2">

<br/>

High (1x)
</td>
</tr>
<tr>
<td>other</td>
<td>10</td>
</tr>
<tr>
<td rowspan="3">

<br/>

Business Criticality
</td>
<td colspan="1">Low</td>
<td colspan="1">60</td>
<td rowspan="3">

<br/>

High (1x)
</td>
</tr>
<tr>
<td colspan="1">Medium</td>
<td colspan="1">40</td>
</tr>
<tr>
<td colspan="1">High</td>
<td colspan="1">20</td>
</tr>
<tr>
<td rowspan="4">

<br/>

Number of known App to App Dependencies
</td>
<td colspan="1">0</td>
<td colspan="1">80</td>
<td rowspan="4">

<br/>


<br/>

Medium-High (0.8x)
</td>
</tr>
<tr>
<td colspan="1">1</td>
<td colspan="1">60</td>
</tr>
<tr>
<td colspan="1">2</td>
<td colspan="1">40</td>
</tr>
<tr>
<td colspan="1">3 or more</td>
<td colspan="1">20</td>
</tr>
<tr>
<td rowspan="3">Number of Compute Instances</td>
<td colspan="1">1 to 3</td>
<td colspan="1">60</td>
<td rowspan="3">

<br/>

Medium-High (0.8x)
</td>
</tr>
<tr>
<td colspan="1">4 to 10</td>
<td colspan="1">40</td>
</tr>
<tr>
<td colspan="1">11 or more</td>
<td colspan="1">20</td>
</tr>
<tr>
<td rowspan="3">Migration Strategy (if known)</td>
<td colspan="1">Rehost</td>
<td colspan="1">60</td>
<td rowspan="3">

<br/>

Medium-High (0.8x)
</td>
</tr>
<tr>
<td colspan="1">Replaftorm</td>
<td colspan="1">40</td>
</tr>
<tr>
<td colspan="1">Refactor</td>
<td colspan="1">20</td>
</tr>
<tr>
<td rowspan="2">Business Unit</td>
<td colspan="1">(early adopters, if applicable)</td>
<td colspan="1">60</td>
<td rowspan="2">
Medium-Low (0.4x)
</td>
</tr>
<tr>
<td colspan="1">(less likely to be early adopters)</td>
<td colspan="1">10</td>
</tr>
</tbody>
</table>



General Guidelines for Wave 1 or Pilot Application Selection
============================================================

This is to select the ~3-5 applications that will be migrated first and help validate the Landing Zone design.

* Web-based (accessed via web browsers)
* 2 or 3 tiered (web-app-database)
* Apps that have no dependency (or are loosely coupled) on other applications in data center/on-prem;
* Apps with no shared data storage (SAN/NAS) with other applications;
* Apps that can run on AWS RDS supported databases
* Apps with databases less than 1 TB;
* Apps running on 2-5 server instances;
* Preferably, stateless-architecture (can be deployed in a clustered mode using load balancer);
* Preferably, well understood and documented architecture;
* Can be easily rolled back;
* Apps running a supported operating system;
* Apps running a supported database;
* Apps/servers running a supported license;

Applications to avoid in Wave 1 or Pilot
========================================

* Apps serving highly available and geographically distributed e-commerce applications;
* Data warehousing workloads;
* ERP, CRM or Financial Reporting workloads;
* Middleware;
* Workloads requiring executive-level approval for security and/or compliance;
* Hardware/OS Examples

  + IBM Mainframes
  + Specialized Vendor Appliances
  + Solaris
* Application Examples

  + Information Lifecycle Management, ETL, B2B data exchanges,
  + Data Warehouse
  + ERPs and CRMs– SAP, PeopleSoft, Oracle ERP, Microsoft Dynamics, Siebel

Factors that could influence app selection for Wave 1 or Pilot
==============================================================

* Product Release Cycle
* Projects in-flight
* Business criticality
* Customer Impact
* Buy In from Product Owner
* QA Automation
* Architectural Complexity
* Application Dependencies
* Type of dependencies – real time, transactional, batch process, etc
* Allowable outage window on App
* Network bandwidth/connectivity back to DC
* Size of data/Storage
* MSP on-boarding
* Dev team in-house or outsourced
* Number of server instances per application
* Current License Agreements

Selection of Application for Wave 2 to Wave N
=============================================

Where possible, waves should be aligned to business outcomes (see

2-2 Wave Planning
). Iterate the prioritization criteria so that the resulting ranking creates groups of applications that align to your desired business outcomes.

References
==========



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr class="tablesorter-headerRow">
<th class="highlight-blue tablesorter-header sortableHeader tablesorter-headerUnSorted" scope="col">
<div class="tablesorter-header-inner">Name</div>
</th>
<th class="highlight-blue tablesorter-header sortableHeader tablesorter-headerUnSorted" scope="col">
<div class="tablesorter-header-inner">Description</div>
</th>
<th class="highlight-blue tablesorter-header sortableHeader tablesorter-headerUnSorted" scope="col">
<div class="tablesorter-header-inner">Link</div>
</th>
</tr>
<tr>
<th colspan="1">AWS Prescriptive Guidance</th>
<td colspan="1"><span>Portfolio discovery and analysis for migration</span>
</td>
<td colspan="1"><a href="https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-portfolio-discovery/prioritization.html">https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-portfolio-discovery/prioritization.html</a>
</td>
</tr>
</tbody>
</table>

