# Tag-Management-Discovery-and-Analysis

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866084104/Tag-Management-Discovery-and-Analysis

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:04 AM

---

Tag Management Discovery and Analysis
=====================================

Overview
========

Tag management is a fundamental activity that enables classification, support, cost allocation, resource identification, permissions management, and automation.  An effective tagging strategy can enable you to effectively manage your resources at scale.  Your existing servers and resources may already be tracked and classified as a part of your configuration management process.  You may also have systems in place to identify and classify your IT infrastructure.  Your existing classification methods will be an important source for your tag management approach in AWS.

It is important to establish an initial tag baseline for your AWS resources. You can use tags for [IAM permissions management](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_tags.html), [cost allocation tagging and reporting](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html), [resource grouping](https://docs.aws.amazon.com/ARG/latest/userguide/welcome.html), and many other use cases.

Question Bank
=============

The sample questions provided in this section are intended to help you solicit input that will shape your Tag Management approach on AWS. Questions may be eliminated if they aren’t applicable to your situation.  As you progress through answering the questions you may find that a question previously answered also covers another question listed.  This is to be expected since a conversation may form around a particular area and answer a number of questions all at once.  Also, if an existing process or architecture is documented, it may answer a large number of questions upfront.  The existing documentation should be reviewed as long as it's accurate.

During the discovery meeting, AWS related context will be provided for the questions covered by the AWS consultant who guides the meeting.

---



---

Current State
=============

| GreenTemplate | Draft | In Review | Baseline |
| --- | --- | --- | --- |

Overview
--------

*One to two paragraphs that describe the current capability. This can also include diagrams/etc.*

* What is your current naming convention today?
* Do you have a current tagging strategy?
* If you already have AWS resources deployed, do they follow a consistent tagging standard?
* If using other cloud service providers, is tagging used?

Policy
------

*Provide links to relevant company policies stored on the Hub, Sharepoint, or other locations. (Please grant access to AWS Team for links provided)*

* Do you capture any metadata today?
* How are tags applied to resources?
* What are the required tags and conditionally required tags?
* Do you have any resource specific tags?  (e.g. databases have their own unique set of tags)
* How will the tagging strategy be communicated to end users and account administrators?
* How long will administrators have to remediate missing / noncompliant tags?
  + How will non compliant resources be communicated?  To whom should they be reported?

Process
-------

*Include details on the process flow.*

* Do you leverage cost allocation tags today?
* What is your charge back/ show back model?
* What are the attributes that you need to report costs upon for AWS resource usage?  (e.g. Cost Center, Project ID, Executive Sponsor, Environment, etc)
* Is there any process for tag enforcement or remediating resources that aren't tagged?
* Are there any reports that are generated using tags?

Tools
-----

*Describe the tools/applications are being used to support/implement the process.*

* Does tagging trigger any automation?
* How do tags tie back into asset management?
* Do you have any applications you use to identify IT infrastructure owners, cost reporting, project identification, etc.?

People
------

*Who is involved in the various aspects of this process.*

* Who defines standard tags?
* Who manages tagging governance?
* Are users allowed to apply their own tags?
* Are permissions limited for organizational tag policy management?

---

AWS Operational Readiness State
===============================

| GreenTemplate | Draft | In Review | Baseline |
| --- | --- | --- | --- |

* Required tags documented, baselined, and available to all AWS end users
* Naming standards defined for specific AWS resources.
* Tag policies created in AWS Organizations to implement compliance reporting for required tags.
* Test implemented AWS Organization tag policies in each organization unit and region.
* Test organization wide reporting for tag policy compliance
* Establish a remediation plan and method for non-compliant resources
* End user documentation on how to use 
  [AWS Resource Groups Tag Policies](https://console.aws.amazon.com/resource-groups/tag-policies/) 
   
  feature to evaluate tag compliance.

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