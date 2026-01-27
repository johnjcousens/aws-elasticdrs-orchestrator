# Change-Management-Discovery-and-Analysis

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866999024/Change-Management-Discovery-and-Analysis

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** David Helmuth on September 12, 2025 at 04:55 PM

---

---

---

Overview
========

IT Change Management from an ITIL perspective balances the need for organizations to introduce and modify IT services while minimizing the risk to Production Ready environments.  Change Management also focuses on the automated control of change in your cloud environment through policies and thresholds with visibility across services.  In high-velocity organizations, it is a common practice to decentralize change approval, making the peer review a top predictor of high performance.  Most IT organizations have processes for software deployment & release management, code reviews, code / software promotion, testing standards, software upgrades, and maintenance schedules.

Existing IT organization processes and solutions, for change management need to be reviewed and updated to include Cloud Operations so that the level of effort for workload and application owners is minimized for cloud deployments. Most customers will continue to utilize their existing change processes and expand them to support change management in AWS.

Your existing solution and tools for change management may include an IT Service Management solution (such as ServiceNow), an Agile Planning and Change Management tool (such as Jira), documented change processes, documented release schedules, documented change calendars, established change control board, and documented code review processes.  AWS provides a number of services that can complement and enhance your existing change management processes and solutions.  These services are mostly covered in the [Management & Governance category in AWS](https://aws.amazon.com/products/management-and-governance/) and include AWS Systems Manager Change Manager, AWS Systems Manager Change Calendar, AWS Systems Manager Maintenance Windows, AWS Systems Manager OpsCenter, AWS CloudFormation Change Sets, AWS Config, AWS AppConfig, AWS CodeDeploy, and AWS CodePipeline.

As a part of our working sessions, we'll first review the existing relevant change management processes, people, and tools involved. We will illicit input that will determine what AWS services and best practices should be integrated into the existing processes and tools.  We will address customer questions regarding change management processes specifically how they relate to the AWS Cloud

Below is the summary of this capability that was used to frame the conversation for the Current State Workshop Attendees.

![image-20250828-002956.png](images/image-20250828-002956.png)

Workshop Logistics
------------------

### **Current State Meeting Date Time**: 07/17/2025 - 2:00 PM Eastern

### Meeting Recap: [AWS Migrations Current State Workshop - Incident and Problem Management.loop](https://healthedgetrial-my.sharepoint.com/:fl:/g/personal/david_helmuth_healthedge_com/EUvjkDQhMQJDsHUdVIpkGuABuUEkwWPUChnDhncHRcuK0w?nav=cz0lMkZwZXJzb25hbCUyRmRhdmlkX2hlbG11dGhfaGVhbHRoZWRnZV9jb20mZD1iIURCX09mUS1XX2s2RG9PLWZTNkp3NFlvRTd2TktSZzFHdW4zWVJVN3dTX3NZYzZUUXlwM19RNEZia1Y2TUpoUGUmZj0wMUZIWU9XSVNMNE9JRElJSlJBSkIzQTVJNUtTRkdJR1hBJmM9JTJGJmZsdWlkPTEmYT1PbmVOb3RlTWVldGluZ3MmcD0lNDBmbHVpZHglMkZsb29wLXBhZ2UtY29udGFpbmVy)

HealthEdge Current State Summary
================================

HealthEdge has established a formal change management policy owned by the CISO, with well-defined processes for different types of changes (normal, standard, and emergency). The capability operates on a structured release schedule including pre-production releases, two-week cadence releases (moving to Sunday releases), and ad-hoc/hotfix releases. Change Management is owned by IT while Release Management is owned by the Product Team, with ServiceNow and Azure DevOps serving as primary tools for tracking and implementation. The process is highly governed and well-adhered to, requiring specific approvals based on change risk levels and timing. A Change Advisory Board (CAB) composed of infrastructure team managers oversees changes, with no business-hour system changes permitted between 6AM-9PM without Technical Leadership Team approval. The capability leverages cloud adoption practices, though currently not specifically AWS, and demonstrates a balance between maintaining operational stability and enabling business agility through structured change processes.

Policy
------

### Summary

The foundation is a formal Change Management Policy (#5.1) owned by the CISO, applying to all HealthEdge Source Associates and systems. It establishes strict governance with specific approval requirements for different change types, including restrictions on business-hour changes (6AM-9PM requiring Technical Leadership approval). The policy emphasizes documentation, risk management, and compliance with ITIL/ITSM standards.

### Headlines

* Aligned with ITIL/ITSM standards
* Formal Change Management Policy (Policy #5.1) owned by CISO
* Applies to all HealthEdge Source Associates, systems, and equipment
* No changes allowed from 6AM -9PM without Technical Leadership Team approval
* Documented in ADO (moving to Confluence)
* Well followed and enforced with high governance
* Three types of changes defined with specific approval requirements:

  + Normal Changes: Require formal management approval
  + Standard Changes: Pre-approved, low-risk changes
  + Emergency Changes: Require rapid evaluation

Process
-------

### Summary

The process framework encompasses three distinct release types: pre-production, two-week cadence releases (moving to Sunday-only), and ad-hoc/hotfix releases. It includes comprehensive steps for risk assessment, testing, implementation planning, documentation updates, and fallback procedures. Release management operates outside the ITSM process but maintains strong integration with change management procedures.

### Headlines

* Release Types:
* Pre-production (all customers)
* Two-week cadence releases (Thursday or Sunday, consolidating to Sunday)
* Ad hoc/Hot Fix/urgent releases
* Release management is outside ITSM Process
* Product Team owns release management
* Moving to GitHub for releases
* Requires risk and impact assessment
* Testing in controlled environment
* Change classification and prioritization
* Implementation planning
* Documentation updates
* Change monitoring
* Fall back procedures
* Business Continuity Plan updates

Tools
-----

### Summary

The toolset centers around ServiceNow for IT release tracking and Azure DevOps (ADO) for code/SDLC pipeline management. ServiceNow modules cover customer support, problem/incident, and change management, with integrations to email, PagerDuty, and Azure for alerting. The tools are configured but not heavily customized, allowing for automated ticket creation and workflow management.

### Headlines

Primary Tools

* HRP SFDC Ticket System
* ServiceNow for IT Release Tracking
* Azure DevOps (ADO) for code/SDLC pipeline
* ServiceNow modules include:

  + Customer Support
  + Problem/Incident
  + Change Management

Integrations

* Email
* PagerDuty
* Azure for Alerting
* Customer email auto-creates support tickets
* Tool is configured but not customized

People
------

### Summary

Divided responsibilities between IT (Change Management) and the Product Team (Release Management), with clear ownership and accountability. Key roles include the CISO, Change Advisory Board (CAB), Emergency Change Approval Board (eCAB), and dedicated release managers. The team commits 5-10 hours weekly to change management activities, with regular 30-minute change meetings, demonstrating a collaborative approach to change governance.

### Headlines

Key Roles

* Change Management owned by IT (Jim F.)
* Release Management owned by Product Team (Gina with dedicated release manager)
* Change Advisory Board (CAB) composed of infrastructure team managers
* CISO: Policy owner and approver for high-risk changes
* Change control champions from various teams

Workload

* Shared responsibility across Infrastructure Team
* Time commitment: 5-10 hours/week
* Change meetings approximately 30 minutes
* Team has current cloud experience but not specifically AWS
* Emergency Change Approval Board (eCAB) for emergency changes

AWS Operational Readiness State
===============================

| Template | DraftGreen | In Review | Baseline |
| --- | --- | --- | --- |

Summary
-------

HealthEdge's Change & Release Management capability will be enhanced through AWS AMS integration, implementing a robust framework that combines formal policies, structured processes, modern tools, and clear organizational roles.The operational readiness state will leverage AMS's enterprise operating model while maintaining existing ITIL/ITSM standards, ensuring changes are managed effectively while minimizing risk to production environments.

? How will AMS / HealthEdge interact around requests? HE uses SFDC not ServiceNow for customer request tracking?

---

The system will utilize AMS automation tools for common activities, integrate with existing ServiceNow workflows, and maintain strict governance through AMS-managed change control processes.

---

Policy Changes
--------------

* Implement AWS AMS two-person rule for production changes requiring dual approval
* Align with AWS AMS change control policies while maintaining existing ITIL/ITSM standards
* Maintain formal documentation requirements for all changes with updated compliance standards
* Enforce strict governance through AMS-managed change control processes
* Continue policy of no changes during critical business hours (6AM-9PM) unless approved by Technical Leadership

Process Changes
---------------

* Adopt AMS enterprise operating model for change management
* Maintain three types of changes with AMS oversight:
* Normal Changes: Require formal management and AMS approval
* Standard Changes: Pre-approved, low-risk changes
* Emergency Changes: Require rapid evaluation through AMS eCAB
* Required process elements:

  + Operational Excellence Dashboard
  + Metrics and KPIs monitoring
  + Regular change review meetings
  + Documented implementation planning
  + Testing in controlled environments
  + Fall back procedures
  + Business Continuity Plan updates

Tooling Changes
---------------

* Integrate with AWS AMS automation tools for common activities
* Leverage AMS tools for:

  + Change request tracking (HE Customer Requests in SFDC)
  + Monitoring
  + Patch management
  + Security services
  + Backup services
* Maintain existing ServiceNow integration with AMS tools
* Implement AMS-provided operational dashboards

People/Org Changes
------------------

* Establish partnership with AMS team for infrastructure operations
* Define clear roles between:

  + AMS Operations Team: Infrastructure management
  + HealthEdge IT Team: Application management
  + Product Team: Release management
  + Change Advisory Board: Change oversight
* Implement AMS training program for team members
* Maintain existing weekly rotation for on-call support with AMS backup
* Leverage AMS expertise for AWS-specific operations

Examples
--------

* Minimize change impact: Separate non production and production accounts, ideally for each major tier 1 application.
* ITSM / Change Tracking tool updated to support change requests for AWS resources.
* Approvers for changes identified and integrated with change request / tracking / notification. (e.g. database change approvers, infrastructure approvers, security change approvers)
* Gated review and approval process to deploy new AWS resources or change AWS resources in production environment
* Rollback process defined for each change applied to production. (Either manual or automated)
* Tests defined for each change applied to production. (Either manual or automated)
* Gated promotion process for new changes introduced into production. (Either via CI/CD or manually)
* Shared change calendar for each account that defines upcoming changes.
* Shared change calendar that defines upcoming changes for all accounts.
* Notification lists for each account and region to provide notification to all stakeholders of upcoming changes implemented as SNS topics.
* Automation runbooks defined for changes in Production (e.g. Stop Instance, Start Instance).
* Automation runbooks integrated with change calendar.
* Permissions to production account authorized and approved by security and management with MFA enabled for these identities.
* Validate least required privilege principle for all production account identities (including roles and credential keys used by automation, third parties, software).
* All configuration files for any standard platform and application software that will change on running instances, checked in and managed in version control.
* Release runbooks or CI/CD pipeline for all Tier 1 applications entering production.
* Defined catalog of standard AWS resources as infrastructure as code, managed in version control
* Published maintenance windows and notifications prior to maintenance windows for each account and region at a predetermined interval.