# License-Management-Discovery-and-Analysis

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866051176/License-Management-Discovery-and-Analysis

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:04 AM

---

License Management Discovery and Analysis
=========================================

Overview
========

License Management is a fundamental activity that aligns to cost management, compliance, and availability.  Most IT organizations use commercial off the shelf (COTS) software that has licensing requirements.  These COTS products may have their own license management and enforcement software or they may simply have licensing terms that the licensee is required to implement themselves.  If licenses are improperly managed, they can lead to license audits with fines and unexpected license bills. Licenses that are improperly managed may also lead to outdated software that is missing important security and feature updates that can't be applied until licenses are updated.  These missing updates may lead to unexpected outages due to reliability issues with software use. Your licensed software may also include license enforcement and when licenses expire unexpectedly the software may no longer function and result in an outage.

AWS uses a pay-as-you-go pricing model with licenses included. However, some AWS services allow you to bring your own licenses for use with the AWS service.  For example, you can use the “Bring-Your-Own-License (BYOL)” model with [Amazon RDS for Oracle](https://aws.amazon.com/rds/oracle/).  Many IT organizations migrating to the AWS cloud will want to move their COTS based workloads to Amazon EC2.  In this case, you will need to manage your license usage using the vendor provided licensing tools or track license usage on your own.  You can use [AWS License Manager](https://docs.aws.amazon.com/license-manager/latest/userguide/license-manager.html) to automate the license management and reporting process for on-premises workloads as well as AWS based workloads.

Question Bank
=============

The sample questions provided in this section are intended to help you solicit input that will shape your License Management approach on AWS. Questions may be eliminated if they aren’t applicable to your situation.  As you progress through answering the questions you may find that a question previously answered also covers another question listed.  This is to be expected since a conversation may form around a particular area and answer a number of questions all at once.  Also, if an existing process or architecture is documented, it may answer a large number of questions upfront.  The existing documentation should be reviewed as long as it's accurate.

During the discovery meeting, AWS related context will be provided for the questions covered by the AWS consultant who guides the meeting.

---



---

Current State
=============

Overview
--------

*One to two paragraphs that describe the current capability. This can also include diagrams/etc.*

* What COTS licensed software are you using today?
* How are licenses managed for your COTS products today?
* Do you have any enterprise license agreements for your COTS software?
* What are the licensing mechanisms for software today?  (e.g. per CPU, per instance, per user, etc)
* What reporting is in place for license management today?
* Are there any initiatives in place to utilize more open source software?
* Do you feel that your organization has an accurate picture of your current license inventory, usage, compliance?

Policy
------

*Provide links to relevant company policies stored on the Hub, Sharepoint, or other locations.*(Please grant access to AWS Team for links provided)\_\_

* Is there a policy for using licensed software such as an approved licensed software list?
* How is license usage enforced?
* Are there any initiatives in place to reduce license consumption?

Process
-------

*Include details on the process flow.*

* How is budget allocated for new software requests?
* How do you manage license expiration today?
* What happens if a license expires or is invalid?

Tools
-----

*Describe the tools/applications are being used to support/implement the process.*

* Do you have a license inventory system in place to track purchased software?
* Do you have an ITSM for approving requests for new licensed software?
* Do licenses need to be installed on your servers?
* Is there any license management software in use today?

People
------

*Who is involved in the various aspects of this process.*

* Is there anyone responsible for tracking license purchases and usage in the organization?
* Who is the point of contact for license purchasing or approvals?

---

AWS Operational Readiness State
===============================

| GreenTemplate | Draft | In Review | Baseline |
| --- | --- | --- | --- |

* Defined owner for license configuration management.
* Trusted access between AWS License Manager and AWS Organization enabled in management account or delegated administrator account.
* License configurations and rules created for each licensed software application entering AWS environment.
* Decision and configuration on enforcing license limits per license configuration.
* AWS Systems Manager Software Inventory configured in all accounts and regions.
* License tracking by software installation configured for licensed software applications.
* SNS topic(s) created and configured with license configurations for notifications
* AMIs created for each licensed software application entering AWS environment, as needed.
* Host Resource Groups created for licensed software applications that require dedicated hosts.
* Host Resource Groups shared across AWS organizations, as needed.
* Test host resource group utilization and allocation in each account and region.
* Test license utilization in each account and region.
* Test license limit enforcement in each account and region.
* Incorporate license reconfiguration into AMI production process for any licensed software tracked by AMI

*Describe your initial thoughts.*

Policy Changes
--------------

*Are any changes required?*

Process
-------

*Are any changes required?*

Tooling Changes
---------------

*Are any changes required?*

People/Org Changes
------------------

*Are any changes required?*