# Decision - Landing Zone Accelerator Launch Parameters

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867000098/Decision%20-%20Landing%20Zone%20Accelerator%20Launch%20Parameters

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Gary Edwards on August 19, 2025 at 03:54 AM

---

### Document Lifecycle Status

**Purpose**
-----------

When initially deploying Landing Zone Accelerator on AWS, you will need to define the following parameter values.

### Decision

Determine Landing Zone Accelerator parameter values and fill out bottom table with expected values

**Landing Zone Accelerator on AWS Parameters**
----------------------------------------------

| Parameter | Default | Description |
| --- | --- | --- |
| **Source** **Location** | github | The location for the LZA source code. |
| **Repository Owner** | awslabs | The owner of the repository hosting the accelerator code. |
| **Repository Name** | landing-zone-accelerator-on-aws | The name of the repository hosting the accelerator code. |
| **Branch Name** | release/v1.12.5 | The name of the git branch to use for installation that will be defaulted to the newest release version when launching the template |
| **Enable Approval Stage** | Yes | Select `Yes` to add a manual approval stage to the accelerator pipeline. |
| **Manual Approval Stage notification email list** | aws@healthedge.com | Provide a comma (,) separated list of email ids to receive manual approval stage notification emails. |
| **Management Account Email** | aws@healthedge.com | The management (primary) account email. |
| **Log Archive Account Email** | aws+log-archive@healthedge.com | The log archive account email. |
| **Audit Account Email** | aws+audit@healthedge.com | The security audit account (also referred to as the audit account). |
| **Control Tower Environment** | Yes | LZA will be integrated with AWS Control Tower. |
| **Accelerator Resource Name Prefix** | AWSAccelerator | The prefix that will be used for deployed resource names. |
| **Enable Diagnostics Pack** | Yes | Enable the CloudFormation Diagnostics Pack. |
| **Configuration Repository Location** | codeconnection | The location of the LZA config repository. |
| **Use Existing Config Repository** | Yes | Use an existing LZA config repository. |
| **Existing Config Repository Name** | platform.devops.aws.lza-config | The name of the existing LZA config repository. |
| **Existing Config Repository Branch Name** | main | The branch name within the repository from which to pull the LZA configs. |
| **Existing Config Repository Owner** | HE-Core | The name space of the existing LZA config repository. |
| **Existing Config Repository CodeConnection ARN** | arn:aws:codeconnections:us-east-1:273354621797:connection/78809d6f-6174-480a-9d93-f55333481a04 | The ARN of an AWS CodeConnection referencing your existing LZA configuration repository. |