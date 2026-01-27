# AMI-Management-Capability-Discovery-and-Analysis

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866051317/AMI-Management-Capability-Discovery-and-Analysis

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** David Helmuth on August 29, 2025 at 06:53 PM

---

AMI Management Discovery and Analysis
=====================================

Overview
========

Amazon Machine Image (AMI) management is an operational process for virtual machine (VM) image management for Amazon EC2.  If you are using virtual machines on-premises with VMWare or Microsoft Virtual Machines then you may already have an approach for managing these virtual machines.  It is important to consider how you will use AMIs and manage them to ensure that your virtual servers include common software components such as security software, agents, etc.  It is also important to consider how these VMs will be updated as new patches and updates are available.

You may have purpose built AMIs for particular workloads such as analytics, security, and custom developed applications.  These purpose built AMIs will need to align to general updates for the organization as well as updates specific to their purpose.  If you decide to use AutoScaling, then your EC2 instances will be current up to the latest AMI that they were configured to use.  In this case, it is important to establish an AMI update process that incorporates the necessary updates so that your autoscaled EC2 instances include the necessary updates.

Question Bank
=============

The sample questions provided in this section are intended to help you solicit input that will shape your AMI Management approach on AWS. Questions may be eliminated if they aren’t applicable to your situation.  As you progress through answering the questions you may find that a question previously answered also covers another question listed.  This is to be expected since a conversation may form around a particular area and answer a number of questions all at once.  Also, if an existing process or architecture is documented, it may answer a large number of questions upfront.  The existing documentation should be reviewed as long as it's accurate.

During the discovery meeting, AWS related context will be provided for the questions covered by the AWS consultant who guides the meeting.

---

---

Current State
=============

| TemplateGreen | Draft | In Review | Baseline |
| --- | --- | --- | --- |

Overview
--------

*One to two paragraphs that describe the current capability. This can also include diagrams/etc.*

* Do you currently use virtual machines today?  What is the scope of virtual machine usage?
* Do you run virtual machines in any cloud service provider today, including existing AWS workloads?  What images are used?  Are they customized and updated?
* Do you have virtual machines that were built for specific applications or workloads?
* Do you anticipate using any AMIs provided through the AWS marketplace or provided by an ISV?

Policy
------

*Provide links to relevant company policies stored on the Hub, Sharepoint, or other locations. (Please grant access to AWS Team for links provided)*

* Is there a defined policy for virtual machine management such as an update cycle?
* Is there a defined policy for virtual machine review before a workload enters production?
* How many virtual machines are maintained before they are deprecated and unavailable?
* Is there a policy in place that defines when workload owners must update their EC2 instances to use newly created AMIs?
* Are application teams allowed to build their own AMIs?

Process
-------

*Include details on the process flow.*

* How does your virtual machine update process align to your patch management process?  Is it automated?
* What are the automated and manual steps in producing a new virtual machine?  Is this documented somewhere?
* How do you decide what will go into your standard AMIs?  Is there a review process?
* What is the promotion process for an AMI from development to production use?
* Do you have a rollback process in place in case an issue is discovered with an AMI?
* Is there a notification process in place when new AMIs are available?
* Is there a notification process for teams that may be using a deprecated image?

Tools
-----

*Describe the tools/applications are being used to support/implement the process.*

* Do you have any automation in place for creating new AMIs such as an AMI build pipeline?
* Are you using any tools such as Packer or any automation tools such as Ansible / Chef as a part of your AMI management?
* Do you use any open source virtual machines or open source software?
* Do you use any tools to test your virtual machines after a new one is created?

People
------

*Who is involved in the various aspects of this process.*

* Who is responsible for updating virtual machines?  Are application teams responsible for updating their own VMs?
* Who is notified when an AMI is out of compliance or using an outdated version?  Is there an escalation?  Who is it escalated to?
* Who is allowed to update the AMI build process?

---

AWS Operational Readiness State
===============================

| TemplateGreen | Draft | In Review | Baseline |
| --- | --- | --- | --- |

Overview
--------

*Describe your initial thoughts.*

Policy Changes
--------------

* Standardize provisioning policies across all business units through AWS Service Catalog
* Implement unified tagging policies aligned with AWS standards and existing SFDC tracking requirements
* Maintain existing ITIL/ITSM processes through SFDC integration with AWS
* Establish clear policy boundaries between AMS-managed services and business unit-specific needs
* Define standard security and compliance policies that align with existing HRP audit requirements
* Maintain customer-specific provisioning policies through SFDC while leveraging AWS automation

Process
-------

* Maintain SFDC as the primary customer interface and tracking system
* Integrate AWS Service Catalog with SFDC for automated provisioning workflows
* Leverage AMS for standardized infrastructure provisioning while maintaining business unit-specific application deployments
* Transform existing VM-based templates into AWS AMIs and container images
* Implement automated environment creation through AWS CloudFormation with AMS
* Maintain existing customer communication and audit trails through SFDC
* Integrate existing monitoring and backup processes with AWS native services through AMS

Tooling Changes
---------------

* AWS Service Catalog for standardized resource provisioning
* AWS CloudFormation for infrastructure as code
* Continue using SFDC for service requests and tracking
* Integrate existing CI/CD pipelines with AWS services
* Leverage AWS Control Tower through AMS for multi-account management
* Maintain Kubernetes deployments through EKS for WellFrame and Source
* Use AWS Systems Manager for configuration management
* Implement AWS backup and monitoring tools through AMS

People/Org Changes
------------------

* AMS team handles infrastructure provisioning and management
* Existing teams focus on application-specific deployments:

  + HRP SaaS team maintains customer-specific configurations
  + WellFrame DevOps manages container deployments
  + Source DevOps handles cloud-native applications
  + Guiding Care teams manage application deployments
* Maintain current global delivery model with US/India teams
* Retrain existing teams on AWS services and AMS processes
* Clear definition of responsibilities between AMS and internal teams
* Maintain existing SFDC expertise for customer management