# Runbook-New-AWS-Account

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867033815/Runbook-New-AWS-Account

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Gary Edwards on July 30, 2025 at 08:16 PM

---

**Purpose**
-----------

In this runbook we define the process to be executed to create a new AWS Account and onboard it to AMS Accelerate for management.

**AMS Onboarding**
------------------

To prepare the account for [AWS Managed Services (AMS) Accelerate prerequisites](https://docs.aws.amazon.com/managedservices/latest/accelerate-guide/acc-get-mgmt-resource-onboard.html), an IAM role named **ams-access-management** is created automatically in newly vended workload accounts via an LZA customization using CloudFormation stack **ams-management-role.yaml**. This role is used by your AMS account team to deploy AMS Accelerate features to your account. For a list of the resources created in your account for AMS Accelerate, you can refer to [Resource inventory for Accelerate](https://docs.aws.amazon.com/managedservices/latest/accelerate-guide/acc-resource-inventory.html).

**Steps**
---------

1. Obtain approval from <TBD> using <TOOL>
2. Document the required account information in the table below.

   1. Account name
   2. Account description
   3. Account email
   4. Account OU
3. Upon approval:

   1. Add the account details to the LZA accounts-config.yaml. For example:


```
- name: Network
  description: The Network account
  email: aws+network@healthedge.com
  organizationalUnit: Infrastructure
  warm: true # this property will temporarily deploy an EC2 instance for 15 minutes to increase the AWS containment score
```


1. Push the change into the healthEdge LZA Github repository which should trigger the LZA pipeline.

   1. Monitor the LZA Pipeline and wait for it to complete successfully.
2. Email the AWS account ID, account alias, and region(s) to your AMS account team at [aws-ams-healthedge@amazon.com](mailto:aws-ams-healthedge@amazon.com) requesting that they onboard the account. If providing multiple regions to onboard, indicate which region should be designed as primary region ([additional resources](https://docs.aws.amazon.com/managedservices/latest/accelerate-guide/acc-resource-inventory.html) are deployed to that region). A single email can be used to onboard multiple accounts.

| **Account Name** | **Account Description** | **Account Email** | **Account OU** |
| --- | --- | --- | --- |
|  |  |  |  |
|  |  |  |  |