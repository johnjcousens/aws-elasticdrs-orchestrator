# AWS Dev Sandbox & Access Requests

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5025104028/AWS%20Dev%20Sandbox%20%26%20Access%20Requests

**Created by:** Kaitlin Wieand on August 19, 2025  
**Last modified by:** Kaitlin Wieand on November 12, 2025 at 11:40 PM

---

AWS Dev Sandbox: Your Safe Space for Development
================================================

What is an AWS Dev Sandbox?
---------------------------

An AWS development sandbox is an isolated cloud environment where developers can experiment, test, and build applications without affecting production systems. Think of it as your personal playground in the cloud – you get access to AWS services with controlled permissions and spending limits, allowing you to learn and develop safely.

How to Request Access:
----------------------

### Step 1: Check Prerequisites

* Valid company email address
* Manager approval
* Follow flow chart (below)

### Step 2a: Submit Your Request for NEW Sandbox

1. Fill out the "New AWS Sandbox Request" [ticket](https://healthedge.atlassian.net/browse/PINF-511):

   1. Include:

      1. Subject: New AWS Sandbox Request - **TEAM**
      2. Project name and description
      3. Expected duration of use
      4. Required AWS services
      5. Expected owner, if not you
2. Obtain necessary approvals from your manager/team lead as a comment.
3. Submit the request

### Step 2b: Submit Your Request for Existing Sandbox:

1. Ensure you have access to [Conductor One](https://healthedge.conductor.one)
2. Find Sandbox and role you need and fill out justification
3. Submit the request

### Step 3: Wait for Provisioning

* Typical turnaround: 3-5 business days (requires Security approval) (still adjusting time)
* You will receive an AWS Okta tile, signing into AWS will allow you to assume an admin role in the sandbox account

### Step 4: Grant access to your team

* Ensure your team has access to [Conductor One](https://healthedge.conductor.one)
* Give any users that would like access the link to the access profile, mentioned above
* If you are a manager requesting access for your team. Please provide a list as a comment in your Jira ticket. **Do not reach out directly to Security.**
* ***\*\*NOT READY YET, STILL WIP, USE STEP ABOVE**\*\***:*** When users request access, you will get an email and the task will appear in the ConductorOne dashboard. Approving the request will grant their Okta tile and sandbox access. Access is admin by default. Additional IAM roles in sandbox will need to be created by you, and noted to the security team so provisioning is available through ConductorOne.

🚨 Critical Requirements: NO PHI/PII
-----------------------------------

**Absolutely no Protected Health Information (PHI) or Personally Identifiable Information (PII) is allowed in sandbox environments.**

### What's Prohibited:

* Real customer data
* Social Security Numbers
* Medical records or health information
* Credit card numbers
* Real names, addresses, phone numbers
* Any data covered by HIPAA, GDPR, or other privacy regulations

**Violation of this policy can result in immediate account suspension and disciplinary action.**

Best Practices for Sandbox Use
------------------------------

### Resource Management

* Always tag your resources with your name and project
* Set up CloudWatch billing alerts
* Use smallest instance sizes that meet your needs
* Stop/terminate resources when not in use

### Security

* Never share your sandbox credentials
* Regularly rotate access keys

### Cost Control

* Monitor your spending through the billing dashboard
* Use AWS Free Tier eligible services when possible
* Set up budget alerts for your account
* Clean up unused resources weekly

Common Sandbox Use Cases
------------------------

* **Application Development**: Build and test new applications
* **Infrastructure as Code**: Practice with AWS CDK
* **Service Integration**: Test API connections and third-party integrations
* **Performance Testing**: Load test applications in a cloud environment
* **Learning & Training**: Hands-on experience with AWS services
* **Proof of Concepts**: Validate technical approaches before production

Service Account Access Requests