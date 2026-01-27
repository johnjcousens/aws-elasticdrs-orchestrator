# Decision---Log-Storage-and-Retention-Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867098131/Decision---Log-Storage-and-Retention-Design

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:35 AM

---

### Document Lifecycle Status

**Purpose**
-----------

This document outlines AWS logging services which will be enabled in each AWS account and which will emit their respective logs to the consolidated logging (Log Archive) account. This document also outlines a strategy for AWS logs retention and access. Configuring service and application logging, and analyzing logs centrally follow AWS Well-Architected Framework best practices.

**Implementation**
------------------

Use the following table to document the sources that will be logged and location of where those logs will reside

### **Logging Sources**

| Log Source | Description | Implementation Details | Location |
| --- | --- | --- | --- |
| [CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html) | Provides event history of AWS accounts activity, including actions taken through the AWS Management Console, AWS SDKs, command line tools, and other AWS services. | CloudTrail will be enabled in each region for each account and will send the logs to the consolidated Log Archive account S3 bucket. Additionally, CloudTrail logs will be streamed to CloudWatch Log Groups in local accounts to ensure that application administrators can utilize them for their day-to-day operations. | S3 bucket (Log Archive account)  CloudWatch Log Group (local accounts) |
| [VPC Flow Logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html) | Captures information about the IP traffic going to and from network interfaces in AWS VPCs. | VPC Flow Logs will be enabled for VPCs in each account and will send network logs to the consolidated Log Archive account S3 bucket. Additionally, VPC Flow Logs will be streamed to CloudWatch Log Groups in local accounts to ensure that application administrators can utilize them for their day-to-day operations. | S3 bucket (Log Archive account)  CloudWatch Log Group (local accounts) |
| [Config](https://docs.aws.amazon.com/config/latest/developerguide/WhatIsConfig.html) | Continuously monitors and records AWS resources configurations and allows to automate the evaluation of recorded configurations against desired configurations. | Config will be enabled in each account and will send configuration history logs to the consolidated Log Archive account S3 bucket. Additionally, configuration history will be accessible through the local and Log Archive account Config Console/API. | S3 bucket (Log Archive account)  Config Console (local accounts) |

Other logging sources may optionally include the following logs based on an account provisioning configuration and workload specifics:

* AWS services logs (e.g. ALB logs);
* Operating system logs;
* Application logs (e.g. authentication logs, firewall logs).

### **Logs Retention Policy**

Use the following table to log the storage type and related lifecycle policies to be enabled via Landing Zone Accelerator

| Storage Type | Transition | Expiration |
| --- | --- | --- |
| S3 bucket (Log Archive account) | Transition to Glacier after 90 days after the creation of an object | Expire after 365 days after the creation of an object |
| CloudWatch Log Group (local accounts) | N/A | Expire after 30 days |