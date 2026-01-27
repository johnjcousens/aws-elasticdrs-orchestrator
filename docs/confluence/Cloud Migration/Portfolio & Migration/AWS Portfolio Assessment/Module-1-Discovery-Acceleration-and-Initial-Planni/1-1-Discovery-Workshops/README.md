# 1-1-Discovery-Workshops

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867099014/1-1-Discovery-Workshops

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:53 AM

---

---

title: 1.1 Discovery Workshops
------------------------------

Goals and Pre-Requisites
========================

**Note:** depending the customer context, workshops might not be the most effective way to conduct discovery activities. If this is the case, consider splitting the workshop into n working sessions with relevant stakeholders instead.

The primary outcome of the Discovery Workshop is to level-up on discovery process, identify the migration scope, introduce an initial application prioritization criteria, and the installation, configuration, and testing of Discovery Tooling (if applicable), including rolling-out data collection. In order to do so, it is necessary that the sources of data are clearly identified (e.g, if discovery tooling is necessary, then a suitable Discovery Tool has been procured and approved for deployment). Also, it is key that the requirements for tooling deployment, as well as the technical aspects of the environment, are considered in advance. For example, deployment methods, authentication requirements, security zones, firewall rules, infrastructure provisioning, etc.

It is recommended to conduct a ~2-hour workshop, 2 to 3 weeks in advance of engagement kick-off (if possible), in order to explore existent sources of data, discuss tooling requirements, alternative approaches and customer procurement cycles. Also, to obtain an extract of an existent application and infrastructure inventory, such as a CMDB export. A gap analysis on preliminary information will be key to determine whether a discovery tool is required at this stage and what are the recommended options. Discovery tooling differs in terms of the platforms and operating systems they support. It is key to ensure the tooling choice is suitable for the migration scope.

Pre-discovery workshops
-----------------------

| Session | Agenda | Participants | Duration | Artifacts and Resources | Outcomes |
| --- | --- | --- | --- | --- | --- |
| Discovery Data Sources & Tooling Assessment | * Obtain CMDB/Inventory extracts * Discuss options for Programmatic Discovery Tooling and Initiate Security   Assessment (if required) * Review MRA/CART results (if applicable) * Analyze alternative sources of data (e.g., performance, monitoring, and   management tools) * Gap analysis * Discovery Tooling deployment requirements and overview of the customer   environment (e.g., authentication mechanisms, deployment methods, security   zones) | Customer:   * Customer Program/project Manager * Application / infrastructure teams   AWS:   * Portfolio Discovery Workstream Lead * Engagement Manager | 2 to 4 hours | Artifact - Data Sources and Tooling Assessment * [APG Discovery Tool Comparison Guide](https://aws.amazon.com/prescriptive-guidance/migration-tools/migration-discovery-tools/?migration-tools-all-cards.sort-by=item.additionalFields.headline&migration-tools-all-cards.sort-order=asc&awsf.migration-tools-discovery-vendor-product-filter=*all&awsf.migration-tools-discovery-tooldeploy-filter=*all&awsf.migration-tools-discovery-method-filter=*all&awsf.migration-tools-discovery-resources-filter=*all&awsf.migration-tools-discovery-resource-profile-filter=*all&awsf.migration-tools-discovery-resource-util-filter=*all&awsf.migration-tools-discovery-app-dependency-filter=*all&awsf.migration-tools-discovery-visualization-filter=*all&awsf.migration-tools-discovery-database-filter=*all&awsf.migration-tools-discovery-storage-filter=*all&awsf.migration-tools-discovery-file-system-filter=*all&awsf.migration-tools-discovery-software-filter=*all&awsf.migration-tools-discovery-container-filter=*all&awsf.migration-tools-discovery-license-filter=*all&awsf.migration-tools-discovery-data-sovereignty-filter=*all&awsf.migration-tools-discovery-data-export-filter=*all&awsf.migration-tools-discovery-compliance-filter=*all&awsf.migration-tools-discovery-service-model-filter=*all&awsf.migration-tools-discovery-pricing-model-filter=*all) | * Recommended Discovery Tool * Identified Data Sources * Discovery Tooling Deployment Requirements * CMDB extract |

Discovery Workshop Checklist
----------------------------

* Conduct pre-discovery workshops - Procure Discovery Tooling and/or obtain approval for deployment (if applicable) - Expectation setting with the customer

Review tactical and strategic goals of the event, discuss expected friction points



Establish the logistics (e.g., remote or office location)

* Set clear expectations to Security & Procurement on the target outcome (e.g., discovery tool procured) -

Confirm attendees from the customer who will represent roles and responsibilities listed in attendees (see agenda). These attendees should be a mix of doers and decision makers



Preview expectations with the attending leaders of each domain (security, applications, etc.)



Document assigned roles and expected attendees by session / tracks



Confirm logistics for the meeting (single meeting room for all participants or preferred customer tool for virtual collaboration)



Assist in obtaining security documentation on the tools that will be in focus

Discovery Workshop Sessions
===========================

Suggested Agenda
----------------

Activity Details
----------------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>
<br/>
</th>
<th>Session</th>
<th>Details / Guidance</th>
<th>Artifacts and Resources</th>
</tr>
<tr>
<td rowspan="6"><strong>Workshop 1</strong>
</td>
<td>Opening and Goal Setting</td>
<td>Level-up customer on the overall Portfolio Assessment methodology and
                the role of the Portfolio Workstream</td>
<td>

<ac:link>
<ri:page ri:content-title="Roadmap-PortfolioAssessment" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Portfolio Roadmap</ac:plain-text-link-body>
</ac:link>

</td>
</tr>
<tr>
<td>Business Drivers</td>
<td>Document (or Review) primary business drivers for the migration/modernization
                project. Use it to document the primary outcomes at a high-level. For example,
                Cost Reduction of X%, Transformation of X% of the scope, Risk reduction
                due to &lt;reasons&gt;. Where possible, avoid long discussions. This is
                a short session to discuss and document high-level drivers that can be
                iterated post-party if needed.</td>
<td>
<ac:link>
<ri:page ri:content-title="Artifact---Business-Drivers-and-Technical-Guiding-Principles" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Artifact - Business Drivers and Technical Guiding Principles</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
<tr>
<td colspan="1">Application/Infrastructure Data Requirements, and Data Repository</td>
<td colspan="1">
Use this session to socialize, review and clarify the application and
                    infrastructure information that will be required at each stage of discovery,
                    emphasizing which information is required now and which information will
                    be gathered in an iterative manner as the project progresses.
Educate the customer about the information that is not necessarily provided
                    by the discovery tool of choice. For example, proprietary application names,
                    business units, application owners, contact details, physical location,
                    criticality, and others. This is in order to prepare key stakeholders in
                    advance should they need to gather or prepare this information ahead of
                    the Preliminary Analysis.
In addition, use this session to establish a centralized repository for
                    all discovery data (e.g., 
                <ac:link>
<ri:page ri:content-title="Template---Application-and-Infrastructure-Inventory" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Template - Application and Infrastructure Inventory</ac:plain-text-link-body>
</ac:link>
                ,
                    <a href="https://mpa.accelerate.amazonaws.com/">an MPA portfolio</a>, or the discovery tool database). This will be the
                        single source of truth for all teams to refer to a common place where to
                        review and update data during the migration project. The established repository
                        will be a key artifact for managing the migration scope (e.g., control
                        scope changes).
The repository can take different shapes and forms depending the tooling
                    available. In some cases it will be advisable to keep the data in the discovery
                    tooling database, especially when this is flexible enough to include custom
                    attributes. In other cases, a CSV or Spreadsheet file can be used (see
                    template provided).
</td>
<td colspan="1">
<ac:link>
<ri:page ri:content-title="Data-Collection-Requirements-(all-stages)" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Data Collection Requirements (all stages)</ac:plain-text-link-body>
</ac:link>
<ac:link>
<ri:page ri:content-title="Template---Application-and-Infrastructure-Inventory" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Template - Application and Infrastructure Inventory</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
<tr>
<td>Application/Infrastructure Migration Scope</td>
<td>
In order to perform the preliminary analysis, it is key to understand
                    which systems are in scope for discovery. Likewise, when discovery tooling
                    is being used, it is key to understand which systems will be targeted for
                    data collection. This session is for the owner(s) of the target environment
                    for discovery to walk AWS/Partners through their application and infrastructure
                    scope.
For example, if there is a scope of 1000 servers but only 500 are in-scope
                    to be migrated it is likely that only those 500 need to be discovered at
                    this stage. This will accelerate data collection.
There could be situations in which there is no certainty about which applications
                    or servers are in a given data center. In these cases, obtaining bare metal
                    and hypervisor lists will be helpful. Connecting to hypervisors permits
                    to obtain lists of virtual machines to be targeted for data collection. Alternatively,
                    known network subnets could be targeted for automated discovery. Discovery
                    tools can scan those subnets and report those systems that respond to ping
                    or SNMP requests. Note that it is key to understand what the tooling requirements
                    are for this type of discovery given that not all network/systems configurations
                    will allow ping or SNMP traffic.
</td>
<td>
Obtain an updated CMDB extract and/or inventory
<ac:link>
<ri:page ri:content-title="Template---Application-and-Infrastructure-Inventory" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Template - Application and Infrastructure Inventory</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
<tr>
<td>Application Prioritization Criteria</td>
<td>
The goal of this session is to establish which key attributes will determine
                    the order in which applications should be migrated. This is a key input
                    for identifying initial migration candidates.
<span>If the Discovery Tool of choice lacks the capability/features to perform prioritization or if discovery tooling is not available, use the <a href="https://mpa.accelerate.amazonaws.com/">Migration Portfolio Assessment</a> (MPA) tool (available to AWS Employees and Partners). It will be required to export all application and infrastructure data from its current repository and import it into MPA. Request permission from the data owner(s) to upload inventory data to MPA.</span> 
When exporting data, consider exporting all assets (applications and infrastructure),
                    as well as Communication (or dependency) data. The communications data
                    will be required later on for analyzing dependency groups in MPA and constructing
                    wave plans. Once the data has been imported into MPA, navigate to the Plan
                    section, application prioritization.
Note: at this early stage of discovery, the objective is to use a default
                    application prioritization criteria and socialize it with the key stakeholders.
The result will be a ranking of applications. If the weighting/relevance
                    is correct, the top 5 should be good initial candidates for migration.
                    If the top applications do not make sense, adjust the criteria and recreate
                    the list.
</td>
<td>
Discovery Tool of choice
<a href="http://mpa-proserve.amazonaws.com/">Link to MPA</a>

<ac:link>
<ri:page ri:content-title="Artifact---Application-Prioritization-Criteria" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Artifact - Application Prioritization Criteria</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
<tr>
<td colspan="1">Wrap-up </td>
<td colspan="1">Review outcomes of the day and next steps</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td rowspan="4"><strong>Workshop 2</strong>
</td>
<td>Opening and Goal Setting</td>
<td>Establish goals for the day and address any open item</td>
<td>
<br/>
</td>
</tr>
<tr>
<td colspan="1">Data Collection Roll-out Plan</td>
<td colspan="1">
In general, data collection (and agent install, if required) will follow
                    a progressive approach throughout several days or weeks. Clarify these
                    aspects and plan for the roll-out accordingly. Data collection is a key
                    input for the upcoming Portfolio Analysis and it is recommended to obtain
                    at least 1 or 2 weeks of discovery data from all targeted systems before
                    baselining the data analysis.
</td>
<td colspan="1">
Obtain an updated CMDB extract or inventory 
<ac:link>
<ri:page ri:content-title="Template---Application-and-Infrastructure-Inventory" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Template - Application and Infrastructure Inventory</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
<tr>
<td>Discovery Tooling Installation &amp; Configuration (if required)</td>
<td>
The goal of this session is to work alongside the customer to install,
                    configure, and test the Discovery Tool of choice. This is applicable to
                    installation of the main tooling infrastructure and software. 
Where possible, start data collection during the workshop targeting the
                    first chunk of systems as defined in the roll-out plan. Consider that rolling
                    out discovery tooling requires troubleshooting, especially related to security
                    constraints such as authentication, permissions and firewall rules. Ensure
                    that key stakeholders such as InfoSec and Platform teams are actively engaged.
This guide includes runbooks for commonly used Discovery Tooling. However,
                    there are several other tools available. If the tool of choice is not included
                    in the provided artifact, please refer to the vendor installation guide.
</td>
<td>
<ac:link>
<ri:page ri:content-title="Runbooks-APA" ri:version-at-save="1"></ri:page>
<ac:plain-text-link-body>Portfolio Runbooks</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
<tr>
<td colspan="1">Wrap-up </td>
<td colspan="1">Review of workshop outcomes and next steps (e.g., ad-hoc sessions to iterate/finalize
                elements of the agenda)</td>
<td colspan="1">
<br/>
</td>
</tr>
</tbody>
</table>



Primary Outcomes
----------------

1. **Agreed Data Requirements and Data Repository**
2. **Identified Application/Infrastructure Scope**
3. **Data collection roll-out plan (including agent installation, if needed)**
4. **Discovery Tooling Installed & Configured (if applicable)**
5. **Data Collection complete**

**Attachments:**