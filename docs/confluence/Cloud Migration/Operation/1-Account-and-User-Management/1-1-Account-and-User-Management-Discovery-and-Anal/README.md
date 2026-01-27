# 1-1-Account-and-User-Management-Discovery-and-Analysis

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866051110/1-1-Account-and-User-Management-Discovery-and-Analysis

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Lei Shi on August 07, 2025 at 08:28 PM

---

Account and User Management Discovery and Analysis
==================================================

Overview
========

Account and User Management addresses the ongoing process of onboarding and managing accounts and users in AWS. This becomes especially important if you are using AWS Organizations and multiple accounts.  Once your landing zone and AWS Organizations configuration has been established, you will need to provide operational processes that help users onboard with the necessary permissions onto AWS. You will also need to provide a method for them to decommission accounts and users once they are no longer needed. Your IT organization may already have onboarding and decomissioning processes for IT.  These processes will need to be expanded for the AWS Cloud.

AWS provides a number of services that are related to Account and User Management, including AWS Control Tower, AWS Identity and Access Management (IAM), AWS Single Sign-On, AWS Organizations, and AWS Directory Service. These services are used to varying degrees based in your AWS landing zone setup based on your requirements.  The ongoing management and usage of these services along with your own control processes establish your Account and User Management solution.

Question Bank
=============

The sample questions provided in this section are intended to help you solicit input that will shape your Tag Management approach on AWS. Questions may be eliminated if they aren’t applicable to your situation.  As you progress through answering the questions you may find that a question previously answered also covers another question listed. This is to be expected since a conversation may form around a particular area and answer a number of questions all at once.  Also, if an existing process or architecture is documented, it may answer a large number of questions upfront.  The existing documentation should be reviewed as long as it's accurate.

During the discovery meeting, AWS related context will be provided for the questions covered by the AWS consultant who guides the meeting.

---

Current State
=============

| TemplateGreen | Draft | In Review | Baseline |
| --- | --- | --- | --- |

Overview
--------

*One to two paragraphs that describe the current capability. This can also include diagrams/etc.*

* What are the prerequisites for gaining access to AWS?
* Do you have an intake form for new AWS users and accounts?
* Is there a wiki page that describes the AWS onboarding process?  Is there a description of the available roles that a user can request?

Policy
------

*Provide links to relevant company policies stored on the Hub, Sharepoint, or other locations. (Please grant access to AWS Team for links provided)*

* Are users required to take any training before access to AWS is granted?
* Can users request specific permissions to an AWS account and region or will they be required to use existing roles?
* What is the naming convention for Active Directory security groups?
* Are there different policies for access to production vs non production accounts?
* What is the SLA for a new AWS user access or new account creation?
* What is the policy for new production account creation?

Process
-------

*Include details on the process flow.*

* Have you thought about the onboarding process for new users to AWS?
* What is the process for creating new security groups for Active Directory?
* What are your existing processes for de-provisioning users and AWS resources?
* How does an existing AWS user request additional permissions to an account or to a new account?

Tools
-----

*Describe the tools/applications are being used to support/implement the process.*

* Do you have any tools that you use to manage Active Directory? (e.g. [One Identity Active Roles](https://www.oneidentity.com/products/active-roles/))
* Will use use your ITSM solution for new account and user requests for AWS?

People
------

*Who is involved in the various aspects of this process.*

* Who is required to approve requests for AWS access?
* Who is responsible for de-provisioning AWS accounts?
* Who is responsible for responding to new account requests?

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