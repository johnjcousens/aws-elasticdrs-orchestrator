# Security-Governance-and-Strategy-Overview

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867033902/Security-Governance-and-Strategy-Overview

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:33 AM

---

When customers first move to the cloud, their instinct might be to build a cloud security governance model based on one or more regulatory frameworks that are relevant to their industry. Although this can be a helpful first step, it’s also critically important that organizations understand what the control objectives for their workloads should be.

In this post, we discuss what you need to do both organizationally and technically with Amazon Web Services (AWS) to build an efficient and effective governance model. People who are taking their first steps in cloud can use this post to guide their thinking. It can also act as useful context for folks who have been running in the cloud for a while to evaluate their current governance approach.

But before you can build that model, it’s important to understand what governance is and to consider why you need it. Governance is how an organization ensures the consistent application of policies across all teams. The best way to implement consistent governance is by codifying as much of the process as possible. Security governance in particular is used to support business objectives by defining policies and controls to manage risk.

Moving to the cloud provides you with an opportunity to deliver features faster, react to the changing world in a more agile way, and return some decision making to the hands of the people closest to the business. In this fast-paced environment, it’s important to have a way to maintain consistency, scaleability, and security. This is where a strong governance model helps.

Creating the right governance model for your organization may seem like a complex task, but it doesn’t have to be.

Frameworks
----------

Many customers use a standard framework that’s relevant to their industry to inform their decision-making process. Some frameworks that are commonly used to develop a security governance model include: [**NIST Cybersecurity Framework (CSF)**](https://d1.awsstatic.com/whitepapers/compliance/NIST_Cybersecurity_Framework_CSF.pdf), [**Information Security Registered Assessors Program (IRAP)**](https://aws.amazon.com/compliance/irap/), [**Payment Card Industry Data Security Standard (PCI DSS)**](https://aws.amazon.com/compliance/pci-dss-level-1-faqs/), or [**ISO/IEC 27001:2013**](https://aws.amazon.com/compliance/iso-27001-faqs/)

Some of these standards provide requirements that are specific to a particular regulator, or region and others are more widely applicable—you should choose one that fits the needs of your organization.

While frameworks are useful to set the context for a security program and give guidance on governance models, you shouldn’t build either one only to check boxes on a particular standard. It’s critical that you should build for security first and then use the compliance standards as a way to demonstrate that you’re doing the right things.

Control objectives
------------------

After you’ve selected a framework to use, the next considerations are controls. A control is a technical- or process-based implementation that’s designed to ensure that the likelihood or consequences of an identified risk are reduced to a level that’s acceptable to the organization’s risk appetite. Examples of controls include firewalls, logging mechanisms, access management tools, and many more.

Controls will evolve over time; sometimes they do so very quickly in the early stages of cloud adoption. During this rapid evolution, it’s easy to focus purely on the implementation of a control rather than the objective of it. However, if you want to build a robust and useful governance model, you must not lose sight of control objectives.

Consider the example of the firewall. When you use a firewall, you implement a control. The objective is to make sure that only traffic that should reach your environment is able to reach it. Although a firewall is one way to meet this objective, you can achieve the same outcome with a layered approach using [**Amazon Virtual Private Cloud (Amazon VPC)**](https://aws.amazon.com/vpc/) Security Groups, [**AWS WAF**](https://aws.amazon.com/waf/) and Amazon VPC [**network access control lists (ACLs)**](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html). Splitting the control implementation into multiple places can enable workload owners to have greater flexibility in how they configure resources while the baseline posture is delivered automatically.

Not all areas of a business necessarily have the same cloud maturity level, or use the same methods to deploy or run workloads. As a security architect, your job is to help those different parts of the business deliver outcomes in the way that is appropriate for their maturity or particular workload.

The best way to help drive this goal is for the security part of your organization to clearly communicate the necessary control objectives. As a security architect, it’s easier to have a discussion about the things that need tweaking in an application if the objectives are well communicated. It is much harder if the workload owner doesn’t know they have to meet certain security expectations.

### What is the job of security?

At AWS, we talk to customers across a range of industries. One thing that consistently comes up in conversation is how to help customers understand the role of their security team in a distributed cloud-aware environment. The answer is always the same: we as security people are here to help the business deploy and run applications securely. Our job is to guide and educate the rest of the organization on the best way to meet the business objectives while meeting the security, risk, and compliance requirements.

### Want to learn more?

<https://aws.amazon.com/blogs/security/how-to-think-about-cloud-security-governance/>