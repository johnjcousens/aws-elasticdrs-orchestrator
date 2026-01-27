# Template-Detailed-Application-Discovery-Questionnaire

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867098333/Template-Detailed-Application-Discovery-Questionnaire

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:50 AM

---

1. Consider using the [MPA tool](http://mpa-proserve.amazonaws.com/) (available to AWS Employees and Partners) customizable ingestion questionnaires to automate the application data ingestion process.
2. Utilize this template to conduct detailed application discovery for the Pilot Applications (typically in Mobilize phase) or Applications in a given Wave (typically in Migrate/Modernize phase)
3. Review and revise the templates below with the customer to capture any specific information that is unique to their environment and to remove unnecessary questions.
4. For each application targeted for migration, make a copy of the revised template and have the customer fill it out.
5. An alternative workbook is available as an attached file that can be downloaded. See Introduction section, alternative template.
6. After obtaining information, load specific asset information (e.g., applications, servers, databases, storage) into the

   Template - Application and Infrastructure Inventory
   .

---

Introduction
============

Welcome to the AWS Professional Services Application Discovery Template. This template can be used for entering key information about your application/workload to assist us in planning its migration to AWS. One template should be completed per application/workload; AWS Professional Services will leverage the collected information to assist the customer with future state design and migration strategy.

**Note:** 
depending on the migration strategy chosen for the applications, there could be significant variation in the level of detail required. For example, most Rehost strategies will focus on validating technology stack compatibility, operations, and security. On the other hand, a Refactor approach will require detailed designs and understanding of the application. Consider adapting the questionnaire to meet the level of complexity required by removing sections as needed.

Alternative Template
--------------------

The attached workbook contains the same questions as the questionnaire below. This is available to be used as an alternative to the Confluence page. Specially to gain ability to accelerate ingestion of data into the inventory.

System Overview Diagrams & Other Application Artifacts
======================================================

Linked Artifacts
----------------

| Name | Description | Link |
| --- | --- | --- |
|  |  |  |
|  |  |  |

Contacts
========

Note: an application owner (or workload owner, or product owner) is the team or individual that is responsible for the strategic view, development, test, and production of the application/workload.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>Primary contact name</th>
<th>Role</th>
<th>email address</th>
<th>phone number</th>
</tr>
<tr>
<td>
<br/>
</td>
<td>Application Owner</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
</tr>
<tr>
<td>
<br/>
</td>
<td>Application Developer</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
</tr>
<tr>
<td colspan="1">
<br/>
</td>
<td colspan="1">Application Operations</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">
<br/>
</td>
<td colspan="1">Infrastructure Operations</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
</tbody>
</table>



Application/Workload
====================

1 - Application Overview
------------------------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table><tbody><tr><th>1.1 Please provide an overview of the application/workload, business objective, its use case, its key purpose and any other information that is relevant to AWS understanding your application.</th></tr><tr><td><br/><br/></td></tr><tr><td class="highlight-grey" colspan="1"><span><strong>1.1.1 Have previous application discoveries been performed, and if so, is the result available to be shared?</strong></span></td></tr><tr><td colspan="1"><br/><br/></td></tr><tr><td class="highlight-grey" colspan="1"><span><strong>1.1.2 Does deep technical expertise in the application/workload exist with the current personnel resources, or are there gaps in knowledge? (ie - application was developed by a team no longer in the organization, insufficient documentation exists of the application, etc.)</strong></span></td></tr><tr><td colspan="1"><br/><br/></td></tr><tr><th>1.2 What is the mission value level of the workload? (How important is this application)</th></tr><tr><td><div>__TASKLIST_4__</div></td></tr><tr><th>1.3 What is the impact/blast radius of a failure in the application/workload? (e.g. who is affected if this goes down)</th></tr><tr><td><br/><br/></td></tr><tr><th>1.4 Who are the key users of the application/workload and how often do they utilize the application?</th></tr><tr><td><br/><br/></td></tr><tr><th>1.4.1 Please break down the users by region</th></tr><tr><td><br/><br/></td></tr><tr><th>1.5 What is your internal name/abbreviations for this application/workload? (What is this application commonly called)</th></tr><tr><td><em><span>(Please also provide a unique ID if known/available)</span></em><hr/><br/><br/></td></tr><tr><th>1.6 Is there any planned downtime or any outages anticipated for this application workload?</th></tr><tr><td><br/><br/></td></tr><tr><th>1.7 Is the workload approaching a technology refresh?</th></tr><tr><td><div class="content-wrapper"><div>__TASKLIST_2__</div><span>If yes, Anticipated technology refresh date:</span>  
<hr/><em><span>Please provide details of the planned technology refresh</span></em><hr/><br/><br/></div></td></tr><tr><th>1.8 How risky is this system? (Consider PII, data classification, public facing, internal only)</th></tr><tr><td><em><span>Please describe the rationale for the selected level</span></em><hr/><div>__TASKLIST_4__</div><br/></td></tr><tr><th>1.9 What is the complexity level of the workload? (e.g. how many other systems does this interface with) </th></tr><tr><td><em><span>Please describe the rationale for the selected level</span></em><hr/><div>__TASKLIST_4__</div><br/></td></tr><tr><th>1.10 Describe the number/type of environment(s) that exist to support this workload?</th></tr><tr><td><em><span>e.g. Dev, Test, Staging, Prod, Disaster Recovery, etc.</span></em><hr/><br/><br/></td></tr><tr><th><span>1.11 Please define all internal/external URLs affected by migration. Document the DNS Forward and Reverse<strong>, and provide a mapping of URL to end customer, if applicable.</strong></span></th></tr><tr><td><em><span>e.g. Forward DNS:</span></em> <a href="http://mydomain.doe.gov"><em><span>http://mydomain.doe.gov</span></em></a>
<br/><hr/><em><span>Windows: nslookup -type=ptr w.x.y.z (enter your IP address in w.x.y.z) / Linux: host w.x.y.z (enter your IP address in w.x.y.z)</span></em><hr/><br/></td></tr></tbody></table>



2 - Application Geography & Performance
---------------------------------------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>
2.1 P<span>lease provide</span> the location(s)
                    (City, State) of the data center(s) in which the application/workload is
                    deployed?
</th>
</tr>
<tr>
<td>

<br/>


<br/>

</td>
</tr>
<tr>
<th>
2.2 Does your application/workload utilize a content delivery network
                    to improve performance?
</th>
</tr>
<tr>
<td>
<em><span>(If so, please provide details) e.g. Akamai, Cloudfront</span></em>

<hr/>

<br/>

</td>
</tr>
<tr>
<th>
2.3 Describe the application usage cycles (e.g. Mostly business hours,
                    Monday through Friday)
</th>
</tr>
<tr>
<td>

<br/>


<br/>

</td>
</tr>
<tr>
<th colspan="1">2.4 What is the current application load like? (e.g., constant, spiky) </th>
</tr>
<tr>
<td colspan="1">

<br/>


<br/>


<br/>

</td>
</tr>
<tr>
<th colspan="1">2.5 How well can the application load be predicted? (e.g., can be predicted
                one year out, unpredictable)</th>
</tr>
<tr>
<td colspan="1">

<br/>


<br/>

</td>
</tr>
</tbody>
</table>



3 - Application/Workload Environment
------------------------------------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>
3.1 How does the user/client connect to the application/workload? 
</th>
</tr>
<tr>
<td>
<em><span>For example, is this a web application or is there a dedicated client application?</span></em>

<hr/>

<br/>


<br/>

</td>
</tr>
<tr>
<th>
3.2 How many concurrent users/clients use the application/workload?
</th>
</tr>
<tr>
<td>
Number of users: xx users

<br/>

</td>
</tr>
<tr>
<th>
3.3 Does the application use specific software for reporting purposes?
</th>
</tr>
<tr>
<td>
<em>Please list any specific reporting software or functionality used. For example, Crystal Reports, Microsoft SQL Server Reporting Services, Business Objects, or other business intelligence tools?</em>


<br/>


<br/>

</td>
</tr>
<tr>
<th>
3.4 What protocol is used to access the workload (e.g. HTTP, HTTPS, SSH,
                    RDP etc)?
</th>
</tr>
<tr>
<td>

<br/>


<br/>

</td>
</tr>
<tr>
<th colspan="1"><strong>3.5 Does the app have any batch jobs or any other jobs scheduled in the application or database servers?</strong>
</th>
</tr>
<tr>
<td colspan="1">
<div>
<div>__TASKLIST_2__</div>
</div>
<em><span>Please add any details as necessary:</span></em>

</td>
</tr>
</tbody>
</table>



4 - Application/Workload Architecture
-------------------------------------

| 4.1 Is the application n-tier by design? |
| --- |
| e.g. 2 tier = database & website, 3 tier, db, front end, application server  

- [ ] Yes
- [ ] No

 |
| 4.2 Please describe each application layer and its components. |
| Please provide architectural diagrams, if available. |
| 4.3 Does the application/workload have a tightly-coupled architecture or loosely-coupled service oriented architecture (SOA)? |
| *We are interested in understanding how your application/workload is architected as this allows us to make recommendations around the best use of compute, storage and network resource based on the particular application/workload design pattern in use.*   --- |
| 4.4 Is this application load balanced? If so, provide details. |
| *Is the load balanced application active/active or active/passive? Algorithm, SSL Offloading, Stickiness, etc.*   --- |
| 4.5 Does this application use any caching (object, database, common calls)? |
| Does it require any components such as Reddis, Memcache, Oracle In-Memory Database, Casandra, Times Ten, and Coherence   --- |

5 - Development and Deployment Approach
---------------------------------------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table><tbody><tr><th>5.1 what is the rate of change for this application? (e.g., is the application actively developed or is it maintained purely to meet operational requirements?</th></tr><tr><td><div>__TASKLIST_3__</div></td></tr><tr><th>5.2 Describe your approach to software development in relation to the application/workload.</th></tr><tr><td><em><span>We would like to understand your current approach to software development and how the application/workload is developed (if applicable). e.g. Agile, Waterfall</span></em><hr/><br/><br/></td></tr><tr><th>5.3 Does the application have an end-of-life plan?</th></tr><tr><td><div>__TASKLIST_2__</div><hr/><em><span>Please provide details</span></em> 
<hr/><br/><br/></td></tr><tr><th>5.4 Does the workload have fixed change/release cycle? (e.g. patched every Thursday or once a month)</th></tr><tr><td><div>__TASKLIST_2__</div><hr/><em><span>Please provide details</span></em><hr/><br/><br/></td></tr><tr><th>5.5 Please describe the application development cycles:</th></tr><tr><td> <em><span>For example, scheduled change freeze, maintenance window, blue/green</span></em><hr/><br/><br/></td></tr><tr><th>5.6 What is your App Teams availability to assist in migrating the application?</th></tr><tr><td> 
<em><span>Please explain</span></em><hr/><br/><br/></td></tr><tr><th>5.7 How is (Current Application Name) \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ deployed (Automated / Manually )?</th></tr><tr><td> 
<em><span>Please provide details and include information about internal code repositories</span></em><hr/><br/><br/></td></tr><tr><th>5.8 How are your <strong>database</strong> <strong>deployments</strong> done (Automated / Manually)?</th></tr><tr><td> <span>Are any specific tool chains used for database updates (ie – redgate, liquibase, flywheel, etc)?</span> <em><span>Please provide details.</span></em><hr/><br/><br/></td></tr><tr><th>5.9 What is the current tool chain used for first deployments/fresh <strong>Application</strong> <strong>Deployment</strong> (Continuous Integration / Continuous Delivery / Continuous Deployment)?</th></tr><tr><td> <span>Examples: TeamCity, Aritfactory, Gitlab, Github, Octopus, Final Builder</span><span>What branch strategy is used? Do you have a list; can we obtain a list of the branch strategy for application deployment</span><em><span>?</span></em><hr/><br/><br/></td></tr><tr><th>5.10 What is the current tool chain used for <strong>Application</strong> <strong>Updates (</strong>Code Updates, Code Changes, Releases/Patches<strong>)</strong> (Continuous Integration / Continuous Delivery / Continuous Deployment)?</th></tr><tr><td> <span>Examples: TeamCity, Aritfactory, Gitlab, Github, Octopus, Final Builder</span><span>What branch strategy is used? Do you have a list; can we obtain a list of the branch strategy for application deployment?</span><hr/><br/><br/></td></tr><tr><th>5.11 What is the current tool chain used for <strong>Infrastructure</strong> <strong>Deployment</strong> (Continuous Integration / Continuous Delivery / Continuous Deployment)?</th></tr><tr><td> <span>Examples: Chef, Puppet, Ansible, SALT</span> <span>What branch strategy is used? Do you have a list; can we obtain a list of the branch strategy for infrastructure deployment</span><hr/><br/><br/></td></tr><tr><th>5.12 Do your CI/CD tools have licensing constraints?</th></tr><tr><td> 
<em><span>Please explain</span></em><hr/><br/><br/></td></tr><tr><th>5.13 Is historical build information important to your application? (Yes/No)?</th></tr><tr><td> 
<em><span>Please explain</span></em><hr/><br/><br/></td></tr><tr><th>5.14 Where are your CI/CD Tools installed/running? Who owns CI/CD for this application?</th></tr><tr><td> <span>Are your CI/CD tools installed on a physical/virtual server you own or host? Is your CI/CD server in the CMDB? What is the current DNS name of your repositories that will be migrated to AWS?</span> <em><span>Please provide details</span></em><hr/><br/><br/></td></tr><tr><th>5.15 During your infrastructure / application deployments, are specific user accounts required?</th></tr><tr><td>  <span>Specify if special AD creds/dependencies are needed</span><hr/><br/><br/></td></tr><tr><th>5.16 For your application deployments, what steps are not or cannot be automated?</th></tr><tr><td> 
<em><span>Please explain</span></em><hr/><br/><br/></td></tr><tr><td class="highlight-grey" colspan="1"><span><strong>5.17 Is your application containerized?</strong></span></td></tr><tr><td colspan="1"><span><em><span>If yes, what is the current and desired ochestration method?</span></em></span><hr/><br/><br/></td></tr></tbody></table>



6 - Licensing
-------------

| 6.1 Please describe the software licensing requirements of the application/workload. |
| --- |
| *Please provide detail about software licenses required to run the application/workload in AWS as well as detail about any OS/database licensing requirements. Is the license portable? Licensed by core?*   --- |
| 6.2 Are there any other licensing considerations? |
| *For example, is there a requirement to upgrade versions of OSs as part of the migration?*   --- |
| 6.3 Please list any commercial off-the-shelf software used by the workload: |
| *Please list one application per line using the following structure: vendor, app, version, license expiry, update/update/retire due, due date (e.g. IBM, file net p8 content manager, 5.2,* 2017-12-25*, upgrade,*   --- |

7 - Migration
-------------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>
7.1 Please describe the preferred method of migration to AWS, if any.
</th>
</tr>
<tr>
<td>
<em><span>We would like to establish here how you would like your migration to take place. For example, is there a preferred method of migration such as refactor, replatform, rehost.</span></em>

<hr/>

<br/>


<br/>

</td>
</tr>
<tr>
<th>
7.2 Is downtime permitted for the application/migration to take place?
                    (e.g., any preferred dates/time)
</th>
</tr>
<tr>
<td>
<span><em>Please provide details as to regular downtime windows, if any extensions to regular windows are possible, and any contractual constraints.</em></span>

<hr/>

<br/>


<br/>

</td>
</tr>
<tr>
<th>
7.3 Please describe any considerations for the migration.
</th>
</tr>
<tr>
<td>

<br/>


<br/>

</td>
</tr>
<tr>
<td class="highlight-grey" colspan="1"><span><strong>7.4 Please list the owner(s) of customer communication/coordination in relation to application changes, upgrades, and migrations (UAT, Cutover planning, etc)</strong></span>
</td>
</tr>
<tr>
<td colspan="1">

<br/>


<br/>

</td>
</tr>
<tr>
<td class="highlight-grey" colspan="1"><span><strong>7.5 Please describe the Customer Communication/Coordination requirements and procedures during application changes, upgrades, and migrations. Please describe any anticipated/common challenges.</strong></span>
</td>
</tr>
<tr>
<td colspan="1">

<br/>


<br/>

</td>
</tr>
</tbody>
</table>



8 - Testing
-----------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>
8.1 What are the current test mechanisms?
</th>
</tr>
<tr>
<td>
Please provide details
<hr/>

<br/>


<br/>

</td>
</tr>
<tr>
<th>
8.2 Please describe the current test stages. (e.g., QA, UAT)
</th>
</tr>
<tr>
<td colspan="1">
Please provide details
<hr/>

<br/>


<br/>

</td>
</tr>
</tbody>
</table>



9 - Resources
-------------

| 9.1 Please provide a high-level summary of the key personnel you are able to make available to support the application migration. |
| --- |
| *Please include details of roles and responsibilities as well as any third party resources (non-AWS) that you anticipate requiring for the migration.*   --- |
| 9.2 What costs for these resources do you anticipate? |
| *Please provide as much detail as possible about anticipated resource costs. e.g. extra contractor hours*   --- |

10 - Service Level Agreement (SLA)

| 10.1 Does the application/workload currently operate to defined SLA's? |
| --- |
| 

- [ ] Yes
- [ ] No

   ---   *Please describe key performance requirements for the application (if any, total number of users, concurrent users, transactions per seconds, throughput, response time, processing time, minimum availability), and if these requirements are contractual or not.*   --- |
| 10.2 Does the application/workload have support provided internally or through a third party? |
| 

- [ ] Yes
- [ ] No

   ---   *Please provide details of the support being provided for the application/workload*   --- |
| 10.3 Have there been any workload/application/Infrastructure outages in the past 12 months? |
| 

- [ ] Yes
- [ ] No

   ---   *Please provide details e.g. system capacity issues, configuration issues, connectivity issues and identify the root cause*   --- |

11 - Compliance & Data Sovereignty
----------------------------------

| 11.1 Are there any compliance frameworks that the application/workload operates under? |
| --- |
| 

- [ ] Yes135incompleteApp will not work after domain change136incompleteApp uses domain user/computer as a service account and uses customized SPN137incompleteApp saves app info in AD object138incompleteApp uses AD configuration partition or schema extension139incompleteApp is dependent on cross-domain authentication & authorization140incompleteApp is dependent on the group policy141incompleteApp is dependent on startup/login script142incompleteApp uses certificates issued by Windows CA server
- [ ] App will not work after domain change
- [ ] App uses domain user/computer as a service account and uses customized SPN
- [ ] App saves app info in AD object
- [ ] App uses AD configuration partition or schema extension
- [ ] App is dependent on cross-domain authentication & authorization
- [ ] App is dependent on the group policy
- [ ] App is dependent on startup/login script
- [ ] App uses certificates issued by Windows CA server
- [ ] No

   ---   *Provide narrative here about the compliance frameworks that apply, for example, if PCI application, can you provide a network flow diagram of all credit card data?*   --- |
| 11.2 Please provide the dates of the last audits for each compliance framework (if applicable) |
| SOC1:   January 01, 2016  SOC2:    January 01, 2016  SOC3:    January 01, 2016  ISO 27001:   January 01, 2016  ISO 27017:   January 01, 2016  ISO 27018:   January 01, 2016  ISO 9001:   January 01, 2016  PCI:   January 01, 2016  FedRAMP:   January 01, 2016  HIPAA: |

12 - Dependencies
-----------------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>
12.1 Are there any dependencies on other centralized or shared services/applications
                    (e.g. DNS, AD Authentication, etc)?
</th>
</tr>
<tr>
<td>
<span>This is mean to gather what this application needs to operate.</span>


<br/>

</td>
</tr>
<tr>
<th>
12.2 Are there any application dependencies that this application has
                    in order to be migrated?
</th>
</tr>
<tr>
<td>
 <em><span>This is to gather what OTHER applications require this application to operate. <em>Please describe each dependency (real-time, batch) and provide any data (operations per second, bytes per second/operation, etc) if available.</em>
</span>
</em>

<em><span><em>Please specify whether the dependency is Soft (i.e., can continue over WAN links such as Direct Connect) or Hard (i.e., the dependency cannot be resolved and must migrate alongside the dependant application)</em>
</span>
</em>

<hr/>

<br/>


<br/>

</td>
</tr>
<tr>
<td class="highlight-grey" colspan="1"><span><strong>12.2.1 Are any of the above dependencies latency-sensitive? please specify the latency requirement</strong></span>
</td>
</tr>
<tr>
<td colspan="1">

<br/>


<br/>


<br/>

</td>
</tr>
<tr>
<td class="highlight-grey">
<strong>12.3 List of System Interfaces</strong>

</td>
</tr>
<tr>
<td>
<em><span>Please provide a list of systems with which this system interfaces and the interface protocol (i.e. Oracle database link, LDAP, SOAP, RESTFul, SCIM)</span></em>

<hr/>

<br/>

</td>
</tr>
<tr>
<td class="highlight-grey">
<strong>12.4 System Interconnection Agreements</strong>

</td>
</tr>
<tr>
<td>
<em><span>For each system listed in 11.3, do you have a security agreement with the interfaced system owner that would need modification?</span></em>

<hr/>

<br/>


<br/>

</td>
</tr>
<tr>
<td class="highlight-grey" colspan="1"><span><strong>12.5 Are there any dependencies with Active Directory?</strong></span>
</td>
</tr>
<tr>
<td colspan="1">
<div class="sc-kgAjT hTySGh">
<div>
<div class="sc-fQfKYo hgHMia">
<div>__TASKLIST_10__</div>
</div>
</div>
</div>
<span>Please Explain</span>


<br/>


<br/>

</td>
</tr>
</tbody>
</table>



13 - Data
---------

| 13.1 Does the application data contain PII data? |
| --- |
| 

- [ ] Yes
- [ ] No

 |
| 13.2 Does the application data contain sensitive data? (controlled unclassified / Official Use Only) |
| 

- [ ] Yes
- [ ] No

 |
| 13.3 What is the data classification of the data? |
| 

- [ ] Public
- [ ] For Official Use Only (FOUO)
- [ ] Personal Identifiable Information (PII)
- [ ] Unclassified Controlled Nuclear Information (UCNI)
- [ ] ITAR (International Traffic in Arms Regulations)

 |
| 13.4 How do you currently transfer files to the server? |
| 

- [ ] RDP
- [ ] FTP / SFTP
- [ ] SSH / SCP
- [ ] Network Shares
- [ ] Repositories
- [ ] Other: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

 |
| **13.5 From where do you currently transfer files to the server?** |
| 

- [ ] Non-Government Furnished Equipment (GFE)
- [ ] EITS Desktop
- [ ] Non-EITS Desktop
- [ ] Internet

 |

14 - Monitoring & Operations
----------------------------

| 14.1 Does the workload have a monitoring solution in place? |
| --- |
| 

- [ ] Yes
- [ ] No

   ---   *Please provide details of the monitoring solution used *and where logs are stored**   --- |
| 14.2 Does the workload have a backup process in place? |
| 

- [ ] Yes
- [ ] No

   ---   *Please provide details of the backup process used*   --- |
| 14.3 Are there change control procedures in place for this workload? |
| 

- [ ] Yes
- [ ] No

   ---   *Please provide details of the change control process used*   --- |

15 - Resiliency
---------------

| 15.1 Does your application have high availability and fault tolerance configurations? |
| --- |
| Please provide details   --- |
| 15.2 Does your application have Disaster Recovery configurations? |
| *Please provide details.*   --- |
| **15.2 What is the Recovery Point Objective (RPO) of the application?** |
| *Determines how often data should be backed up and how much data can be lost between backups if a crash occurs*   ---   RPO: xx minutes |
| **15.3 What is the Recovery Time Objective (RTO) of the application?** |
| *Determines the target time for the recovery of the application/workload after a system disaster has struck. How long til the system has to be up.*   ---   RTO: xx minutes |

16 - Application Security
-------------------------

| 16.1 Is your application currently encrypted in transit and at rest between all tiers? |
| --- |
| Is end-to-end encryption a requirement. |
| 16.2 Does your application use any insecure protocols between tiers? (FTP, HTTP) |
| *Please provide details.*   --- |
| **16.3 Does your application traverse traffic globally or just within a certain region?** |
| *Are restrictions required, is a CDN required, etc.*   --- |
| **16.4 Can you describe Client Authentication requirements? ( Server Certificates, Client Certificates, User Authentication, SAML)** |
| *How does the application perform AAA?   *If SAML, please list identity provider details.**   --- |

Assets
======

Consider loading the information directly into 

Template - Application and Infrastructure Inventory

Compute
-------

In this section please provide as much information as possible about the compute resources assigned to this application/workload.

### Physical Servers

Enter details below for each of the physical servers that make up the application/workload. Do not include physical hosts that run a virtual machine hypervisor.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>
Hostname
</th>
<th colspan="1">OS Name</th>
<th colspan="1">OS Version</th>
<th colspan="1">Role</th>
<th>
# CPUs
</th>
<th>
Cores per CPU
</th>
<th colspan="1">Threads per Core</th>
<th colspan="1">Peak CPU Usage</th>
<th>
Avg. CPU Usage
</th>
<th colspan="1">Total RAM (GB)</th>
<th colspan="1">Peak RAM</th>
<th colspan="1">Ave RAM</th>
<th colspan="1">Local Storage Total (GB)</th>
<th colspan="1">Local Storage Usage (%)</th>
</tr>
<tr>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
</tbody>
</table>



### Virtual Servers

Enter details below for each of the virtual servers that make up the application/workload.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>
Hostname
</th>
<th colspan="1">Hypervisor</th>
<th colspan="1">OS Name</th>
<th colspan="1">OS Version</th>
<th colspan="1">Role</th>
<th>
# CPUs
</th>
<th>
Cores per CPU
</th>
<th colspan="1">Threads per Core</th>
<th colspan="1">Peak CPU Usage</th>
<th>
Avg. CPU Usage
</th>
<th colspan="1">Total RAM (GB)</th>
<th colspan="1">Peak RAM</th>
<th colspan="1">Ave RAM</th>
<th colspan="1">Local Storage Total (GB)</th>
<th colspan="1">Local Storage Usage (%)</th>
</tr>
<tr>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
</tbody>
</table>



### Containers



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th colspan="1">Container ID</th>
<th>
<span>Container Name</span>

</th>
<th>
<span>Desc</span>

</th>
<th>
<span>Inbound (port)</span>

</th>
<th>
<span>Outbound (port)</span>

</th>
<th>
<span>Load Balancing (Y/N)</span>

</th>
<th>
<span>Filesystem Mounts</span>

</th>
<th>
<span>vCPU</span>

</th>
<th>
<span>Memory (MB)</span>

</th>
<th>
<span>\# Instances</span>

</th>
</tr>
<tr>
<td colspan="1"><em><span>unique ID</span></em>
</td>
<td>
<em><span>web-container</span></em>

</td>
<td>
<em><span>User Authentication, static web content service</span></em>

</td>
<td>
<em><span>Load Balancer (:8443)</span></em>

</td>
<td>
<em><span>web-container (8443)</span></em>

</td>
<td>
<em><span>Y</span></em>

</td>
<td>
<em><span>/opt/tomcat/volumes/ccdata</span></em>
<br/><em><span>/opt/tomcat/volumes/lucene</span></em>

</td>
<td>
<em><span>2.00</span></em>

</td>
<td>
<em><span>2460</span></em>

</td>
<td>
<em><span>4</span></em>

</td>
</tr>
<tr>
<td colspan="1"><em><span>unique ID</span></em>
</td>
<td>
<em><span>app-container</span></em>

</td>
<td>
<em><span>Real-time processing of web inputs</span></em>

</td>
<td>
<em><span>web-container (8443)</span></em>

</td>
<td>
<em><span>Oracle RDS (1563)</span></em>

</td>
<td>
<em><span>Y</span></em>

</td>
<td>
<em><span>/opt/tomcat/volumes/ccdata</span></em>
<br/><em><span>/opt/tomcat/volumes/lucene</span></em>

</td>
<td>
<em><span>2.00</span></em>

</td>
<td>
<em><span>2460</span></em>

</td>
<td>
<em><span>2</span></em>

</td>
</tr>
</tbody>
</table>



Clusters
--------

Enter details below about the storage your application/workload currently utilizes.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th colspan="1">Clsuter ID</th>
<th>
Cluster Name
</th>
<th>
Description
</th>
<th>
# Nodes
</th>
<th>
Operation Mode
</th>
<th>
Product Name
</th>
<th colspan="1">Product Version</th>
<th colspan="1">VIP IP Address</th>
</tr>
<tr>
<td colspan="1">unique ID</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">
<br/>
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
</tbody>
</table>



Databases
---------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>Database ID</th>
<th>Database Name</th>
<th>Environment</th>
<th>Primary Usage Type</th>
<th>Source Engine Type</th>
<th>Source Engne Version</th>
<th>License Model</th>
<th>Avg IOPS</th>
<th>Peak IOPS</th>
<th>DB Size (GB)</th>
<th>Throughput (MBps)</th>
<th>Replication (Y/N)</th>
<th colspan="1">Encryption (Y/N)</th>
</tr>
<tr>
<td><em><span>uniqueID</span></em>
</td>
<td>
<br/>
</td>
<td><em><span>Test,Dev,Prod</span></em>
</td>
<td><em><span>OLTP/OLAP/Other</span></em>
</td>
<td><em><span>Oracle, SQL, etc</span></em>
</td>
<td>
<br/>
</td>
<td><em><span>Ent, Std, etc</span></em>
</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td>
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
</tbody>
</table>



Storage
-------

Enter details below about the storage your application/workload currently utilizes.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th colspan="1">Storage ID</th>
<th>
Type
</th>
<th>
Provisioned (Gb)
</th>
<th>
Used (Gb)
</th>
<th>
Max IOPS
</th>
<th>
Average IOPS
</th>
<th colspan="1">Throughput (MBps)</th>
<th colspan="1">Replication (Y/N)</th>
</tr>
<tr>
<td colspan="1">unique ID</td>
<td>
Local
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">
<br/>
</td>
<td>
NAS
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">
<br/>
</td>
<td>
SAN
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">
<br/>
</td>
<td>
Object
</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
</tbody>
</table>



Networks
--------

Enter details about your current internet connectivity and used by the application/workload

| Network ID | Type | Provider | Description | Bandwidth (Mbps) | Peak Usage (%) | Average Usage (%) | Connection Point A | Connection Point B | Encryption (Y/N) | Encryption Method | Layer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| *uniqueID* | *WAN Link / VPN* |  |  |  |  |  | *DC 1* | *DC 2* |  | *IPSec* | *3* |
| *uniqueID* | *Internet* |  |  |  |  |  | *DC 1* | *Internet* |  |  |  |



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<td colspan="2">
<em>List any specific network capability required (i.e. connections to external services or data sources)</em>

<hr/>

<br/>


<br/>

</td>
</tr>
</tbody>
</table>



**Attachments:**