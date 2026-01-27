# Define-AWS-Config-Rules-and-Remediation-via-Landing-Zone-Accelerator

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867065543/Define-AWS-Config-Rules-and-Remediation-via-Landing-Zone-Accelerator

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:35 AM

---

**Purpose**
-----------

This document provides the procedures to enable AWS Security Hub and AWS Config rules through the Landing Zone Accelerator configuration files, specifically the `security-config.yaml`

**Prerequisites**
-----------------

* Completion of the decisions outlined on page

  Decision - Detective Controls Design
* Completion of the implementation of the solution using

  Landing Zone Accelerator on AWS Deployment

**Procedure**
-------------

### AWS Security Hub Standards

AWS Security Hub consumes, aggregates, and analyzes security findings from various supported AWS and third-party products. Security Hub also generates its own findings by running automated and continuous checks against the rules in a set of supported security standards. These rules determine whether controls within a standard are being adhered to. The checks provide a readiness score and identify specific accounts and resources that require attention.

#### Add Security Standards to Configuration File

1. Navigate to the AWS CodeCommit repository named `aws-accelerator-config`
2. All AWS Security Hub standards will be enabled within the `security-config.yaml` file located in the root of the repository
3. Add the `securityHub` key to the `security-config.yaml` file using the following block:
4. Under the `standards` key the specific standards can be added and any `controlsToDisable` can be provided
5. The above example enables the AWS Foundational Security Best Practices v1.0.0 standard without any exclusions
6. To **exclude specific controls** add the ID of the control in the following manner:
7. These IDs are notated in the title of the

   Decision - Detective Controls Design
   page within `[]` brackets

### AWS Config Custom Rules

Landing Zone Accelerator provides the ability to add AWS Config Custom Rules utilizing lambda packages within the `aws-accelerator-config` AWS CodeCommit repository.

#### Add AWS Config Managed Rules

1. Navigate to the AWS CodeCommit repository named `aws-accelerator-config` and access the `security-config.yaml` file
2. Enable AWS Config using the following block, providing empty `rulesets`
3. Within the `ruleSets` key it can be specified the `deploymentTargets` and specific `rules` to enable referencing local files within the repository
4. The following example provides an example AWS Config Managed rule

5. The above example will enable the AWS Config Managed rules across the `deploymentTargets`

#### Add AWS Config Custom Rules

1. Navigate to the AWS CodeCommit repository named `aws-accelerator-config` and access the `security-config.yaml` file
2. Enable AWS Config using the following block, providing empty `rulesets`
3. Within the `ruleSets` key it can be specified the `deploymentTargets` and specific `rules` to enable referencing local files within the repository
4. The following example provides an example AWS Config rule that includes remediation
5. After adding the above keys to the `security-config.yaml` file, the related assets need to also be added to the `aws-accelerator-config` repository in the following relative directories

   ![](../../../../attachments/Screen%20Shot%202022-05-27%20at%201.26.15%20PM.png)
6. Once the files have been added and the keys provided in the `security-config.yaml` configuration file, Landing Zone Accelerator will complete the process to deploy the custom AWS Config rule across the `deploymentTargets` specified.

**Attachments:**

[Screen%20Shot%202022-05-27%20at%201.26.15%20PM.png](../../../../attachments/Screen%20Shot%202022-05-27%20at%201.26.15%20PM.png)