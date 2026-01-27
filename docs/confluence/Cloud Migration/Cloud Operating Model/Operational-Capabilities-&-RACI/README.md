# Operational-Capabilities-&-RACI

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866051202/Operational-Capabilities-%26-RACI

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:04 AM

---

---

title: Operational Capabilities & RACI
--------------------------------------

Definitions
===========

* "**Customer**" is used when referencing the overall customer organization.
* "**MSP (or Central IT)**" is used when referencing the organizational unit responsible for managing the foundational shared resources in AWS.
* "**User**" is used when referencing business unit dev teams or other users that are customers of Central IT.
* An “**Alert**” is created whenever an Event from a supported AWS service exceeds a threshold and triggers an alarm.
* A “**Critical Security Update**” means a security update rated as “Critical” by the vendor of a Supported Operating System.
* An “**Event**” indicates a change in your environment.
* An “**Important Update**” means an update rated as “Important” or a non-security update rated as “Critical” by the vendor of a Supported Operating System.
* An “**Incident**” is an Event or any other AWS service performance issue within the customer’s environment that results in a customer impact as determined by AWS support or the MSP (or Central IT).
* “**Landing Zone**” refers to one or more AWS accounts and the resources within those accounts owned by the customer and used to manage resources deployed on AWS.
* A “**Problem**” is a shared underlying root cause of one or more Incidents.
* A “**Request for Change**” or “**RFC**” is a request created by the user to make a change in the customer’s Landing Zone.
* A “**Stack**” is a group of one or more AWS resources that are managed as a single unit.

**Operational Roles & Responsibilities**
========================================

MSP (or Central IT) manages user’s AWS infrastructure. The section below provides descriptions or each capability and an overview of the responsibilities of user and MSP (or Central IT) for activities in the lifecycle of an application running within the Managed Environment.

* “R” stands for a responsible party that does the work to achieve the task.
* “C” stands for consulted; a party whose opinions are sought, typically as subject matter experts; and with whom there is bilateral communication.
* “I” stands for informed; a party which is informed on progress, often only on completion of the task or deliverable.

**Operational Capability Definitions**
======================================

**Application Lifecycle**

Application Lifecycle Management (ALM) refers to the capability to integrate, coordinate and manage the different phases of the software delivery process. From development to deployment, ALM is a set of defined process and tools that include definition, design, development, testing, deployment and management. Throughout the ALM process, each of these steps are closely monitored and controlled.

**Change Management**

MSP (or Central IT) offers Change Management, which is the mechanism for users to get access to or affect any changes in their Managed Environment. The user creates RFCs using the MSP (or Central IT) Interface. Most RFCs requested by the user will be executed automatically.  MSP (or Central IT) also creates RFCs to access user resources or make changes. All RFCs follow a defined Change Management process. Access to user resources within a Landing Zone is authorized only through RFCs. An RFC created by the user must be approved by MSP (or Central IT) before it is actioned.  An RFC created by MSP (or Central IT) must be approved by the user before it is actioned. MSP (or Central IT) will only approve and execute RFCs that can be executed using the features or functionalities of AWS services. The user may designate a start time for the requested change to be performed through the RFC process. users can also use Change Management to configure AWS Service Offerings in the Managed Environment.

**Provisioning Management**

MSP (or Central IT) allows users to create Stacks by choosing appropriate change types from a change type catalog provided through the MSP (or Central IT) Interface. MSP (or Central IT) will provide Amazon Machine Images (AMIs) for users to install applications.  User-provided AMIs can be used to launch Stacks upon being approved by MSP (or Central IT). Application deployment and application configuration management tools will be managed by the user and integrated into the MSP (or Central IT) environment. Users can also install their applications on an approved AMI and create a new AMI, inclusive of the application, for launching Stacks. MSP (or Central IT) will install tooling on EC2 instances for its own use to manage operating system configurations and interactions.

**Logging Monitoring and Event Management**

MSP (or Central IT) configures your Landing Zone for logging activity and Alerts based on different health checks. MSP (or Central IT) will monitor and investigate Alerts that are created whenever one or more alarms from applicable AWS services are triggered. Alerts will be investigated by MSP (or Central IT) to determine if they qualify as an Incident. MSP (or Central IT) will aggregate and store all logs generated as a result of all operations in CloudWatch Logs and CloudTrail.

**Incident & Problem Management**

MSP (or Central IT) proactively notifies users of Incidents detected by MSP (or Central IT). MSP (or Central IT) responds to Incidents and resolves Incidents in a time bound manner based on the Incident priority. Unless otherwise instructed by the user, Incidents that are determined by MSP (or Central IT) to be a risk to the security of the user’s Landing Zone and Incidents relating to the availability of MSP (or Central IT) and other AWS services will be proactively actioned. MSP (or Central IT) requires user authorization before taking action on all other Incidents. Recurring Incidents will be addressed by the Problem Management Process.

**Patch Management**

MSP (or Central IT) applies and installs updates to EC2 instances for supported operating systems and software pre-installed with supported operating systems. Users chose a monthly one-hour maintenance window for MSP (or Central IT) to perform maintenance activities including patching activities. MSP (or Central IT) will apply Critical Security Updates outside of the selected maintenance window. MSP (or Central IT) will apply Important Updates during the selected maintenance window. Patch Management is limited to stacks in the Managed Environment, including all MSP (or Central IT) Managed Applications and supported AWS services with patching capabilities (e.g. RDS). In order to support all types of infrastructure configurations when an update is released, MSP (or Central IT) will a) update the EC2 instance and b) provide an updated MSP (or Central IT) AMI for the user to use. MSP (or Central IT) will notify the user in advance with the details of the upcoming updates. The user can exclude Stacks from Patch Management or reject updates as they deem fit. If the user rejects an update provided under Patch Management but later changes their mind, the user will be responsible for initiating the update using an RFC. It is the user’s responsibility to install, configure, patch, and monitor any additional applications not specifically covered above.

**Continuity Management**

MSP (or Central IT) provides backups of Stacks using standard, existing Amazon Elastic Block Store (EBS) and RDS snapshot functionality on a scheduled interval determined by the customer. Restore actions from specific snapshots can be performed by MSP (or Central IT) per user RFC. Data changes that occur between snapshot intervals are the responsibility of the user to backup. The user may submit an RFC for backup/snapshot requests outside of scheduled intervals.  In the case of Availability Zone (AZ) unavailability in a Region, with the user’s permission, MSP (or Central IT) will restore the Landing Zone by recreating new Stack(s) based on templates and available EBS snapshots of impacted Stacks.

**Reporting**

MSP (or Central IT) provides users with a monthly service report which summarizes key performance metrics of MSP (or Central IT). Reports are delivered by an MSP (or Central IT) Delivery Manager assigned to the user.

**Service Request Management**

Users can request information on their Managed Environment, MSP (or Central IT), or AWS Service Offerings by submitting Service Requests. Users can submit Service Requests using the MSP (or Central IT) Interface.

\*\*AWS Engagement RACI
=======================

\*\*



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th class="highlight-blue">
<strong>Application Lifecycle Management</strong>

</th>
<th class="highlight-blue">
<strong>BU (user)</strong>

</th>
<th class="highlight-blue">
<strong>MSP (or Central IT)</strong>

</th>
</tr>
<tr>
<td>
Application development
</td>
<td>
R
</td>
<td>
I
</td>
</tr>
<tr>
<td>
Application infrastructure requirements analysis and design
</td>
<td>
R
</td>
<td>
C
</td>
</tr>
<tr>
<td>
Design and optimization for non-standard stacks
</td>
<td>
R
</td>
<td>
C
</td>
</tr>
<tr>
<td>
Design and optimization of standard stacks
</td>
<td>
I
</td>
<td>
R
</td>
</tr>
<tr>
<td>
Application deployment
</td>
<td>
R
</td>
<td>
C
</td>
</tr>
<tr>
<td>
AWS Infrastructure deployment
</td>
<td>
C
</td>
<td>
R
</td>
</tr>
<tr>
<td>
Application monitoring
</td>
<td>
R
</td>
<td>
I
</td>
</tr>
<tr>
<td>
Application testing/optimization
</td>
<td>
R
</td>
<td>
I
</td>
</tr>
<tr>
<td>
AWS infrastructure optimization guidance
</td>
<td>
I
</td>
<td>
R
</td>
</tr>
<tr>
<td>
AWS shared infrastructure monitoring
</td>
<td>
I
</td>
<td>
R
</td>
</tr>
<tr>
<td>
Troubleshoot and resolve application issues
</td>
<td>
R
</td>
<td>
C
</td>
</tr>
<tr>
<td>
Troubleshoot and resolve operating system, AWS network, and infrastructure
                    issues
</td>
<td>
C
</td>
<td>
R
</td>
</tr>
<tr>
<td colspan="1">
Application integration with AWS Service Offerings
</td>
<td colspan="1">R</td>
<td colspan="1">C</td>
</tr>
</tbody>
</table>



| **AWS RDS Management** | **BU (user)** | **MSP (or Central IT)** |
| --- | --- | --- |
| Monitor parent/node/RO replication health | I | R |
| Identify RCA of parent failover | I | R |
| Automated snapshot (backup) configuration | C | R |
| Coordinate and schedule DB engine patch management | I | R |
| Recommend DB storage and PIOP capacity | C | R |
| Recommend instance sizing for running databases | C | R |
| Recommend RI optimization for Managed Environment | C | R |
| RDS performance monitoring (CloudWatch) | I | R |
| RDS event subscription configuration (SNS) | C | R |
| RDS security group configuration | C | R |
| RDS engine parameter/option configuration | R | C |
| DB table design | R | I |
| DB indexing | R | I |
| DB log analysis | R | I |

| **Change Management** | **BU (user)** | **MSP (or Central IT)** |
| --- | --- | --- |
| Creating user RFCs (E.g. access to resources, creating/updating/deleting managed Stacks, deploying/updating applications, changes to configuration of AWS Service Offerings) | R | I |
| Approving user RFCs | I | R |
| Creating MSP (or Central IT) RFCs (E.g. access to resources, creating resources on user’s behalf, applying updates to OS as part of Patch Management) | I | R |
| Approving non-automated RFCs | R | I |
| Submitting request for new Change Types | R | C |
| Creating new Change Types | I | R |
| Maintenance of application change calendar | R | C |
| Notifying for upcoming Maintenance Window | I | R |

| **Provisioning** | **BU (user)** | **MSP (or Central IT)** |
| --- | --- | --- |
| User specific additions to MSP (or Central IT) baseline AMI | R | C |
| Configure additional approved Change Types used to provision Stack templates | C | R |
| Launch managed Stacks and associated AWS resources | I | R |
| Install/Update custom and 3rd party applications on Instances | R | I |
| **Provisioning - Stack Architecture** | **BU (user)** | **MSP (or Central IT)** |
| Providing OS licenses (including usage fees for the applicable AWS services – e.g. EC2 and RDS) | I | R |
| Define baseline infrastructure templates (Stacks) for application deployment | I | R |
| Creating baseline approved AMIs | I | R |
| Evaluate user application inventory and determine fit with available infrastructure templates (Stacks) | R | C |
| Define unique Stacks that are in addition to the baseline template offerings | R | C |

| **Logging, Monitoring and Event Management** | **BU (user)** | **MSP (or Central IT)** |
| --- | --- | --- |
| Recording AWS infrastructure change logs | I | R |
| Recording all application change logs | R | C |
| Installation and configuration of agents and scripts for patching, security, monitoring, etc. of AWS infrastructure | I | R |
| Define user specific monitoring and incident requirements | R | C |
| Configuring AWS alarms for Managed Environment | I | R |
| Monitoring all AWS alarms | I | R |
| Investigating infrastructure Alerts for Incident notification | I | R |
| Investigating application alarms | R | C |

| **Incident Management** | **BU (user)** | **MSP (or Central IT)** |
| --- | --- | --- |
| Proactively notify Incidents on AWS infrastructure based on monitoring | I | R |
| Handle application performance issues and outages | R | I |
| Categorize Incident priority | I | R |
| Provide Incident response within SLA | I | R |
| Provide Incident resolution / infrastructure restore within SLA | C | R |
| Identify Problems in Managed Environment | C | R |
| Perform RCA for Problems in Managed Environment | C | R |
| Remediation of Problems in Managed Environment | C | R |
| Identify and remediate application problems | R | I |

| **Security Management** | **BU (user)** | **MSP (or Central IT)** |
| --- | --- | --- |
| User infrastructure security and/or establishing baseline for security compliance process as determined and agreed to during user onboarding. | C | R |
| Maintaining valid licenses for Managed Security Software | R | C |
| Configure Managed Security Software | I | R |
| Update Managed Security Software | I | R |
| Monitoring malware on instances | I | R |
| Maintaining and updating virus signatures | I | R |
| Remediating instances infected with malware | C | R |
| Security event management | C | R |
| **Security - Access Management** | **BU (user)** | **MSP (or Central IT)** |
| Manage the lifecycle of users, and their permissions for local directory services, which are used to access MSP (or Central IT) | R | I |
| Operate federated authentication system(s) for user access to AWS console/APIs | R | C |
| Accept and maintain Active Directory (AD) trust from MSP (or Central IT) AD to user managed AD | R | C |
| During on-boarding, create cross-account IAM Admin roles within each managed account | R | C |
| Secure the AWS root credential for each account | I | R |
| Define IAM resources for Managed Environment | C | R |
| Manage privileged credentials for OS access for MSP / Central IT engineers | I | R |
| Manage privileged credentials for OS access provided to customer by MSP / Central IT | R | I |

| **Patch Management** | **BU (user)** | **MSP (or Central IT)** |
| --- | --- | --- |
| Monitor for applicable updates to supported OS and software pre-installed with supported OS for EC2 instances | I | R |
| Notify user of upcoming updates | I | R |
| Exclude certain updates and/or certain Stacks from patching activities | R | I |
| Apply updates to EC2 instances | I | R |
| Patch development software (.NET, PHP, Perl, Python) | R | I |
| Patch, and monitor middleware applications (e.g. BizTalk, JBoss, WebSphere) | R | C |
| Patch, and monitor custom and 3rd party applications | R | C |

| **Continuity Management** | **BU (user)** | **MSP (or Central IT)** |
| --- | --- | --- |
| Specify backup schedules | R | I |
| Execute backups per schedule | I | R |
| Validate backups | R | I |
| Request backup restoration activities | R | I |
| Execute backup restoration activities | I | R |
| Restore affected Stacks and VPCs | I | R |
| Restore affected custom/3rd party application | R | C |

| **Reporting** | **BU (user)** | **MSP (or Central IT)** |
| --- | --- | --- |
| Prepare and deliver monthly service report | I | R |
| Configure and retrieve API audit history on demand (CloudTrail) | I | R |
| Provide access to incident history through MSP (or Central IT) Interface | I | R |
| Provide access to change history through MSP (or Central IT) Interface | I | R |

| **Service Request Management** | **BU (user)** | **MSP (or Central IT)** |
| --- | --- | --- |
| Request information using service requests | R | I |
| Reply to service requests | I | R |