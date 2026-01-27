# Template-Application-AWS-Architecture-Design-and-Migration-Strategy

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867065740/Template-Application-AWS-Architecture-Design-and-Migration-Strategy

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:50 AM

---

**A Word version of the Application Design and Migration Strategy template is also attached to this page (see alternative template section)**

---

README
======

This page is intended to provide a starting point to creating a target design and migration strategy document that can be reviewed/approved and stored in the customer knowledge or equivalent repository. However, part of the information in the resulting document will be key to inform the migration activities (e.g., security groups, region, account IDs, IAM roles, etc.). This specific information must be added into the

Template - Application and Infrastructure Inventory
in the relevant 'target attributes' in addition to any information about the current state.

Alternative Template
====================

The attached file contains a version of this template that can be downloaded for cases where a separate file is preferred as an alternative to confluence pages. Make sure to also download the

from this page, the diagram included within the document file cannot be edited. The same applies to the

Artifact - 7R Disposition Tree
template included in the migration strategy section of the document.

General Information
===================



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>
Application Name
</th>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<th colspan="1">Application ID</th>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<th colspan="1">SDLC Environment</th>
<td colspan="1">e.g., Production</td>
</tr>
<tr>
<th colspan="1">Region(s)</th>
<td colspan="1">intended target region(s) for this application</td>
</tr>
<tr>
<th colspan="1">Number of Availability Zones</th>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<th colspan="1">AWS Account #</th>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<th colspan="1">Business or Technical Function</th>
<td colspan="1">describe primary function for this application and any other secondary
                use case relevant to this design</td>
</tr>
<tr>
<th colspan="1">Primary Contacts</th>
<td colspan="1">
<ul>
<li>Application Owner</li>
<li>Application Architect</li>
<li>Enterprise Architect</li>
</ul>
</td>
</tr>
<tr>
<th colspan="1"><strong>Data Classification</strong>
</th>
<td colspan="1">Public | Non-Public | Confidential | Highly Confidential</td>
</tr>
<tr>
<th colspan="1"><strong>Service Characteristics</strong>
</th>
<td colspan="1">Internal Facing | External Facing </td>
</tr>
<tr>
<th colspan="1">Migration Strategy</th>
<td colspan="1">
Rehost / Relocate / Replatform / Refactor or Rearchitect
</td>
</tr>
<tr>
<th colspan="1">Migration Pattern</th>
<td colspan="1">
Fresh install, synchronous replication, snapshot import etc. 
</td>
</tr>
</tbody>
</table>



Context and Problem
===================

Background
----------

* Provide brief but relevant information so that readers have some context as to where and why the proposed changes will be made (which will be described later).
* Assume readers are not familiar with the systems.
* Define any needed terminology.

During discussion: Do we all understand the current state of things?

Motivation
----------

* Why have we decided to make the proposed changes?
* What are the benefits?
* Will there be any downsides to the changes? Why do we think the benefits outweigh the downsides?

During discussion: Do we agree that there is strong motivation for making a change? Is there something else we have not considered?

Scope
-----

Will the solution to this problem apply to other applications/services in the portfolio? How much are we willing to generalize the solution? Declare the limits in the scope and out of scope sections.

### In Scope

* List topics, processes, or systems that are in scope of this design

### Out of Scope

* List anything that may be related to the design but that will not be discussed, and why.

During discussion: Do we agree that we will only stick to the in-scope topics? If not, then now is the time to bring those topics up and provide reasons for why they are relevant. For example, should this solution apply to more problems?

Requirements

Document, at a high-level, the functional and non-functional requirements for this architecture.

### Functional

### Non-functional

AWS Architecture Design
=======================

This is where you describe the AWS architecture design for the application. This part can be quite long and it’s important to keep it clear and organized. The kind of organization will depend on what you are building. Unless necessary, try to keep one application per document.

Here are some tips on organization:

* If you are making changes across multiple systems, then make a secondary heading for each system and then describe system specific changes in that section. Where possible, try to use separate documents.
* Move any supporting material to the Appendices section.
* If you are considering multiple approaches and technologies then document them in the Architectural Decisions table.
* If the approach is to address the problem in multiple phases/steps, then clearly define those in the Migration Strategy section.
* Make sure to use appropriate headings. This builds an easy to navigate outline in Confluence and makes it easier to find the right section at a glance.

*During discussion:*

1. *Does the design make sense? Will you be able to provide support for this feature once it’s implemented and you’re on-call? Or will you be able to make changes to it?*
2. *Is this the right design? Are there other options that are better? Are there any important downsides that make this solution not viable? Are the new APIs necessary? Do they have the right structure? Same for new data stores. Etc.*
3. *Is this architecture well-architected? (Use the AWS well architected framework)*
4. *Is this architecture secure? Ensure security/compliance/regulatory requirements are met*

Current Application Documentation
---------------------------------

List documentation for the current implementation (on-premises, colocation, other)



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th class="highlight-blue">Version</th>
<th class="highlight-blue" colspan="1">Document type</th>
<th class="highlight-blue">Title</th>
<th class="highlight-blue" colspan="1">Links</th>
</tr>
<tr>
<th>
1.1
</th>
<td colspan="1">design/diagram/other</td>
<td>

<br/>

</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<th colspan="1">
<br/>
</th>
<td colspan="1">infrastructure inventory</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<th colspan="1">
<br/>
</th>
<td colspan="1">performance report</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">
<br/>
</td>
</tr>
</tbody>
</table>



Architectural Decisions
-----------------------

When more than one option for a given architecture has been considered, document here the options that were analyzed and the rational for selecting one of them.

| Reference ID | Architectural Pillar | Options | Rationale |
| --- | --- | --- | --- |
| AD001 | Security | * Option A (selected) – describe option * Option B – describe option * Option C – describe option | Describe motivation for selected option |

To-Be Architecture Diagram
--------------------------

Use the provided [drawio](https://app.diagrams.net/) template or provide your own. Ensure the diagram is clear and emphasizes the architectural decisions made. It is highly recommended to revisit the base template and adapt it to the specific base configuration of the Landing Zone.

Use Reference numbers in the diagram in order to link them to the Architectural Components details in the next section.

Architectural Component Details
-------------------------------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th class="highlight-blue" colspan="1">Reference Number</th>
<th class="highlight-blue">
Logical Component Name
</th>
<th class="highlight-blue">
Description
</th>
<th class="highlight-blue">
Details
</th>
</tr>
<tr>
<th colspan="1">1</th>
<th>
Internal Active Directory
</th>
<td>
Internal Authentication and DNS service
</td>
<td>
Domain will remain on-premises and will be transitioned to AWS at a later
                    stage
</td>
</tr>
<tr>
<th colspan="1">2</th>
<th>
External Active Directory
</th>
<td>
External Authentication and DNS service
</td>
<td>
Domain will remain on-premises and will be transitioned to AWS at a later
                    stage
</td>
</tr>
<tr>
<th colspan="1">3</th>
<th colspan="1">Virtual Machine - ServerA</th>
<td colspan="1">File Server</td>
<td colspan="1">Shared Service used by multiple applications. Will remain on-premises
                and migrated at a later stage.</td>
</tr>
<tr>
<th colspan="1">4</th>
<th colspan="1">Virtual Machine - ServerB</th>
<td colspan="1">File Server</td>
<td colspan="1">Shared Service used by multiple applications. Will remain on-premises
                and migrated at a later stage.</td>
</tr>
<tr>
<th colspan="1">5</th>
<th colspan="1">External access</th>
<td colspan="1">Access from external customers</td>
<td colspan="1">
DNS servers house public and Internal DNS zones that include records for
                    the following site:
<ul>
<li>api.acme.com
                        <ul>
<li>Public Routable address</li>
<li>Internally Routable address</li>
</ul>
</li>
</ul>
</td>
</tr>
<tr>
<th colspan="1">6</th>
<th colspan="1">Route53 (DNS)</th>
<td colspan="1">DNS Services in AWS</td>
<td colspan="1">
<ul>
<li>Domains</li>
<li>Usage</li>
</ul>
</td>
</tr>
<tr>
<th colspan="1">7</th>
<th colspan="1">KMS</th>
<td colspan="1">EBS Volume encryption</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<th colspan="1">8</th>
<th colspan="1">CloudTrail</th>
<td colspan="1">Logging and Monitoring</td>
<td colspan="1">AWS Account activity monitoring</td>
</tr>
<tr>
<th colspan="1">
9 / 11
</th>
<th colspan="1">Public Subnets</th>
<td colspan="1">Public subnet used for web services</td>
<td colspan="1">
Subnet - Subnet ID - AZ1
Subnet - Subnet ID - AZ2
</td>
</tr>
<tr>
<th colspan="1">10 / 12</th>
<th colspan="1">NAT Gateway</th>
<td colspan="1">Internet access for private subnets</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<th colspan="1">13</th>
<th colspan="1">Direct Connect</th>
<td colspan="1">10 Gbps link to on-premises DC 1</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<th colspan="1">14</th>
<th colspan="1">Transit Gateway</th>
<td colspan="1">Provides connectivity across VPCs and On-premises</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<th colspan="1">15</th>
<th colspan="1">VPC</th>
<td colspan="1">Primary VPC</td>
<td colspan="1">VPC ID and CIDR Range</td>
</tr>
<tr>
<th colspan="1">16 / 17</th>
<th colspan="1">Private Subnets</th>
<td colspan="1">Private subnet used for backend servers</td>
<td colspan="1">
Subnet - Subnet ID - AZ1
Subnet - Subnet ID - AZ2
</td>
</tr>
<tr>
<th colspan="1">18 / 19</th>
<th colspan="1">EC2 Database Instances</th>
<td colspan="1">Database</td>
<td colspan="1">
The primary database is deployed on an Amazon EC2 instance in one Availability
                    Zone and a secondary database is deployed on an Amazon EC2 instance in
                    a second Availability Zone. The databases require configuration to enable
                    the following:
<ul class="itemizedlist">
<li class="listitem">
A highly available architecture that spans two Availability Zones
</li>
<li>Async replication </li>
<li>KMS to encrypt all root and data volumes</li>
</ul>
Databased hosted on these instances:
<ul>
<li>Instance 1</li>
<li>Instance 2</li>
</ul>
</td>
</tr>
<tr>
<th colspan="1">20</th>
<th colspan="1">Load Balancer</th>
<td colspan="1">Application Load Balancer</td>
<td colspan="1">
The Load Balancer handles sticky sessions, ensuring that a single user's
                    requests are always processed by the same backend web server. The Load
                    Balancer works in conjunction with Auto Scaling to ensure that web requests
                    are routed to the correct backend EC2 instance based on various factors,
                    such as instance availability and load. The Application Load Balancer routes
                    traffic to the auto-scaling groups.
A Security Group is used to limit access to the ALB.
<ul>
<li>Security Group Name:</li>
</ul>
</td>
</tr>
<tr>
<th colspan="1">21 / 22</th>
<th colspan="1">Auto Scaling Groups</th>
<td colspan="1">Autoscaling groups are used to scale up and down according to demand</td>
<td colspan="1">
Example: Auto Scaling provides compute resources for web services. Auto-Scaling
                    ensures that the application can scale to accommodate various levels of
                    application load. Additionally, Auto-Scaling is used to ensure that at
                    least 1 instance is available at all times. The Auto Scaling group will
                    automatically replace any instances which are terminated due to failures.
Auto Scaling Group 1 - Name - characteristics 
A Security Group is used to limit access to the App Instances in the auto-scaling
                    group.
<ul>
<li>Security Group Name:</li>
</ul>
Auto Scaling Group 2 - Name - characteristics 
A Security Group is used to limit access to the App Instances in the auto-scaling
                    group.
<ul>
<li>Security Group Name:</li>
</ul>
</td>
</tr>
<tr>
<th colspan="1">22</th>
<th colspan="1">ALB TLS Certificate</th>
<td colspan="1">TLS Certificate used to terminate connections on the ALB</td>
<td colspan="1">
AWS Certificate Manager is used to provision, deploy, and rotate a public
                    TLC Certificate on the ALB. A separate wildcard TLS Certificate is used
                    for each environment.
<ul>
<li>Prod: \*.acme.com</li>
<li>Test: \*.test.acme.com</li>
<li>Dev: \*.dev.acme.com</li>
<li>Sandbox: \*.sbox.acme.com</li>
</ul>
</td>
</tr>
<tr>
<th colspan="1">23 / 24</th>
<th colspan="1">EC2 instances </th>
<td colspan="1">Backend services</td>
<td colspan="1">Instance names</td>
</tr>
<tr>
<th colspan="1">25</th>
<th colspan="1">AWS Region</th>
<td colspan="1">Region for this application</td>
<td colspan="1">us-east-1</td>
</tr>
</tbody>
</table>



Technical Operations Components
-------------------------------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th class="highlight-blue">Logical Component Name</th>
<th class="highlight-blue">Description</th>
<th class="highlight-blue">Details</th>
</tr>
<tr>
<th><span>Monitoring, Alerting, Inventory, and Change Control</span>
</th>
<td><span>Monitoring, Alerting, Inventory, and Change Control</span>
</td>
<td>
AWS Services provide monitoring, alerting, inventory, and change control
                    functionality.
<ul>
<li>CloudWatch &amp; CloudWatch Logs</li>
<li>Config &amp; Config Rules</li>
</ul>
</td>
</tr>
<tr>
<th><span>OS Patching &amp; Remote Access</span>
</th>
<td><span>Patching &amp; Remove Access</span>
</td>
<td><span>AWS Systems Manager (SSM) is used to provide patching and remote access to all EC2 instances.</span>
</td>
</tr>
<tr>
<th><span>Vulnerability Scanner</span>
</th>
<td><span>Vulnerability Scanning</span>
</td>
<td><span>Amazon Inspector is used to assess applications for exposure, vulnerabilities, and deviations from best practices. After performing an assessment, Amazon Inspector produces a detailed list of security findings prioritized by level of severity. These findings can be reviewed directly or as part of detailed assessment reports which are available via the Amazon Inspector console or API.</span>
</td>
</tr>
<tr>
<th colspan="1"><span>Security Audit Logging</span>
</th>
<td colspan="1"><span>Security Audit Logging</span>
</td>
<td colspan="1">
AWS Services provide additional security functionality.
<ul>
<li>CloudTrail provides Security Audit Logging</li>
<li>KMS <span>uses FIPS 140-2 validated hardware security modules to protect encryption keys used for volume and object encryption</span>
</li>
<li><span>Secrets Manager supports the <span>rotation, management, and retrieval of database credentials, API keys, and other secrets throughout their lifecycle</span></span>
</li>
</ul>
</td>
</tr>
</tbody>
</table>



Security Groups
---------------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th class="highlight-blue"><span>Name / ID</span>
</th>
<th class="highlight-blue"><span>Source/Destination</span>
</th>
<th class="highlight-blue" colspan="1"><span>Protocol</span>
</th>
<th class="highlight-blue" colspan="1"><span>Port Range</span>
</th>
<th class="highlight-blue"><span>Description</span>
</th>
</tr>
<tr>
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



SDLC Components
---------------

Software Development Life Cycle



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th class="highlight-blue">Resource</th>
<th class="highlight-blue">Link</th>
</tr>
<tr>
<th colspan="1">Jira Project</th>
<td colspan="1">
<div class="content-wrapper">
Insert link to Jira Project used to manage this application.
</div>
</td>
</tr>
<tr>
<th colspan="1">Source Repository</th>
<td colspan="1">
Insert link to source control repository for this application.
</td>
</tr>
<tr>
<th colspan="1"><span>CI/CD Pipeline Services</span>
</th>
<td colspan="1">
AWS Services are used to <span>store, build, and deploy infrastructure and application components</span> through
                    Sandbox, Dev, Test, and Prod environments.
<ul>
<li>CodeCommit</li>
<li>CodeBuild</li>
<li>CodeDeploy</li>
<li>CodePipeline</li>
<li>Cloudformation</li>
</ul>
</td>
</tr>
</tbody>
</table>



Mandatory Tags
--------------

These tags must be added to all application resources. This list is a subset of the system-wide tags defined for the Landing Zone.

**Note**: if tagging is defined in other repositories such as MPA, then delete the table below and add the relevant link.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<thead>
<tr>
<th class="highlight-blue">
Key
</th>
<th class="highlight-blue" colspan="1">
Value
</th>
<th class="highlight-blue">
Description
</th>
</tr>
</thead>
<tbody>
<tr>
<th class="highlight-grey" colspan="1">Location</th>
<td colspan="1">
<br/>
</td>
<td colspan="1">Physical location of the server</td>
</tr>
<tr>
<th class="highlight-grey" colspan="1">Organization</th>
<td colspan="1">
<br/>
</td>
<td colspan="1">Organizational code</td>
</tr>
<tr>
<th class="highlight-grey" colspan="1">ApplicationOwner</th>
<td colspan="1">TBD</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<th class="highlight-grey" colspan="1">TechnicalPOC</th>
<td colspan="1"><span>TBD</span>
</td>
<td colspan="1">Technical point of contact</td>
</tr>
<tr>
<th class="highlight-grey">Environment</th>
<td colspan="1"><span>TBD</span>
</td>
<td>Type of environment a given device belongs to.</td>
</tr>
<tr>
<th class="highlight-grey">ServerType</th>
<td colspan="1">Virtual</td>
<td>
Type of server.
<ul>
<li>EC2 instance</li>
<li>Managed Service</li>
<li>Container</li>
</ul>
</td>
</tr>
<tr>
<th class="highlight-grey">SoftwareProduct</th>
<td colspan="1">TBD</td>
<td>
Software that are running on the given server.
<ul>
<li>JVM</li>
<li>CustomApp</li>
<li>CustomDB</li>
</ul>
</td>
</tr>
</tbody>
</table>



Migration Strategy
==================

This is where you describe the ‘R’ Strategy chosen for this application and the associated Patterns. The R Strategy is the high-level approach (i.e., one of the 7 Rs) whilst the Pattern is the technique used to deliver the strategy. For example, an R Strategy of Refactor can utilize a Pattern of automated code refactoring with a given product or solution. Overall, this part can vary in complexity depending the path taken and It’s important to keep it clear and organized.

Here are some tips on organization:

* Review the standard AWS R Strategy definitions (included in this document). Make sure there is a common language that AWS, Customers and Partners understands and agree to.
* Review and update the 7R disposition tree. Include elements that are key to customer outcomes and decision-making process. The decision tree is to be used as a guide to help the customer understand the best path for an application. The outcome of an application passing through the tree can be overwritten. However, that is a good indication that tree might need to be updated.
* Move any supporting material to the Appendix section.
* If you are considering multiple approaches and technologies then document them in the Strategy Decisions table.
* If the approach is to address the problem in multiple phases/steps, then clearly define those in the Strategy section.
* Make sure to use appropriate headings. This builds an easy to navigate outline in Confluence and makes it easier to find the right section at a glance.

*During discussion:*

1. *Does the strategy make sense? Does it align to key business drivers? Will you be able to provide support for this strategy and patterns once it’s implemented during a cut-over or migration party?*
2. *Is this the right strategy/pattern? Are there other options that are better? Are there any important downsides that make this solution not viable?*
3. *Has this approach been used before?*
4. *Is this pattern secure? Ensure security/compliance/regulatory requirements are met when implementing the pattern and/or using specific tooling.*

Strategy Definitions and 7R Disposition Tree
--------------------------------------------

See 

Artifact - 7R Disposition Tree

Strategy
--------

Document the Migration Strategy chosen for this application. Include the rationale

Patterns & Tools
----------------

Document the techniques and tools available for delivering a given Strategy. If there is more than one option available document them including the rationale for the preferred choice.

| Pattern/Tool | Description | Link |
| --- | --- | --- |
| Example: CloudEndure | <Application components in scope of this pattern/tool> | <APG pattern guide link> |
| Example: Rebuild | <Application components in scope of this pattern/tool> | <Deployment document> |

Testing Considerations
----------------------

How will you ensure your changes are successful?

* You can break up the content here into a similar structure to your design implementation such as per phase or per system.
* Include what manual tests will be performed.

Cut-over Considerations
-----------------------

Document here any factors that need to be taken in consideration when planning for migration.

* Cut-over dates to avoid
* Skills required

Operational Considerations
--------------------------

How will you ensure you are ready to operate this application in AWS?

* What kind of issues do we expect to see come up as a result of this change?

Risks, Assumptions, Issues, and Dependencies
============================================

* What could go wrong and what will its impact be? How can we mitigate those risks?
* Is there any risk of data corruption?
* Are there security risks?
* Are there performance risks?
* What assumptions have we made?
* What dependencies do we have to implement this architecture and migration strategy?
* What Issues do we know about in the current implementation?
* What issues do we expect as a result of implementing this architecture?

| Type (R, A, I, D) | Description | Owner | Status |
| --- | --- | --- | --- |
|  |  |  |  |
|  |  |  |  |

Open Questions / Parking Lot
============================

List any part of the design that we have not been able to figure out. Could be requirements or risks we don’t know how to handle or parts of other systems we’re not familiar with that can impact our design. The goal here is to acknowledge these gaps and that they will be looked into later, or possibly during the discussion if the group has ideas.

*During discussion: Is it okay to proceed with the design given that we don’t know how some things?*

| Item | Description |
| --- | --- |
|  |  |
|  |  |

Annual Run Rate Estimate
========================



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th class="highlight-blue">Version</th>
<th class="highlight-blue" colspan="1">Annual Total Run Rate</th>
<th class="highlight-blue">One Time Fee</th>
<th class="highlight-blue" colspan="1">Monthly Fee</th>
<th class="highlight-blue">Change</th>
<th class="highlight-blue" colspan="1">Links</th>
</tr>
<tr>
<th>
0.1
</th>
<td colspan="1">$</td>
<td>
$
</td>
<td colspan="1">$</td>
<td>Initial estimate</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<th colspan="2">
This estimate is based on the following assumptions
(use <a href="undefined">TCO &amp; Annual Run Rate Estimates</a>to produce
                    the estimated Run Rate)
</th>
<td colspan="4">
<ol>
<li>One Year Partial Upfront Reserved Instances (RIs) are used for all Production
                        Instances</li>
<li>Daily Change for EBS Snapshots is 0.1%</li>
<li>Utilization for all Production instances (EC2/EBS) is 100%</li>
<li>Utilization for all Non-Prod instances is 5 days/week at 12hrs/day</li>
<li>Does not include Oracle Licensing</li>
<li>Includes Sandbox, Dev, Patch, QA, and Prod environments</li>
<li>Includes Windows OS licensing for all Windows instances</li>
<li>Includes RHEL Licensing for all Linux instances</li>
<li>All internal networking and security is provided by Security Groups</li>
<li>Pricing is for AWS us-east-1 Region</li>
<li>Includes HA and in Region DR capability</li>
</ol>
</td>
</tr>
</tbody>
</table>



References
==========



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th class="highlight-blue">Name</th>
<th class="highlight-blue">Description</th>
<th class="highlight-blue">Link</th>
</tr>
<tr>
<th colspan="1">AWS Prescriptive Guidance</th>
<td colspan="1"><span>The AWS Prescriptive Guidance (APG) Library is a platform for authoring, reviewing, and publishing strategies, guides, and patterns. These resources are created by AWS technology specialists and APN Partners to help customers accelerate their AWS Cloud migration, modernization, and optimization projects.</span>
</td>
<td colspan="1"><a href="https://aws.amazon.com/prescriptive-guidance/">https://aws.amazon.com/prescriptive-guidance/</a>
</td>
</tr>
<tr>
<th colspan="1">AWS Well-Architected Framework</th>
<td colspan="1">AWS Well-Architected helps cloud architects build secure, high-performing,
                resilient, and efficient infrastructure for their applications and workloads.
                Based on five pillars — operational excellence, security, reliability,
                performance efficiency, and cost optimization — AWS Well-Architected provides
                a consistent approach for customers and partners to evaluate architectures,
                and implement designs that can scale over time.</td>
<td colspan="1"><a href="https://aws.amazon.com/architecture/well-architected">https://aws.amazon.com/architecture/well-architected</a>
</td>
</tr>
</tbody>
</table>



Appendix N
==========

In general, all content should belong in a designated section.

If some content is not super relevant but may be useful to reference if desired, like a table or graph, then it can be included here. This is especially true for lengthy extra content.

**Attachments:**

[application-diagramV2.drawio.png](../../attachments/application-diagramV2.drawio.png)