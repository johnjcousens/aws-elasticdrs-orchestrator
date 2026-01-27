# 8-2-Define-Budgets-and-CUR-via-AWS-Platform-Accelerator

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867098267/8-2-Define-Budgets-and-CUR-via-AWS-Platform-Accelerator

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:37 AM

---

---

title: 8.2 Define Budgets and CUR via AWS Platform Accelerator
--------------------------------------------------------------

**Purpose**
-----------

This document describes the process in deploying Budgets and Cost and Usage Reports (CUR) through the Landing Zone Accelerator.

**Prerequisites**
-----------------

Before deploying out these controls in an AWS environment, it’s important that the following pre-requisites are met.

* A notification email address has been established to receive notifications related to Budgets

**Add Budget to Configuration File**
------------------------------------

In this section you will add the **budgets** section to the *global-config.yaml* configuration file

1. Navigate to [AWS CodeCommit](https://console.aws.amazon.com/codesuite/codecommit/home) console
2. Select the ***aws-accelerator-config***
   repository.
3. Select the file ***global-config.yaml***
4. Click ***Edit***
5. At the bottom of the configuration file a reports section will need to be added, allowing for **budgets** properties to be provided. A sample of a budget with the included notification is provided below.

6. Fill in the fields under the *Commit changes to main* section and click *Commit changes*

**Add Cost and Usage Report (CUR) to Configuration File**
---------------------------------------------------------

In this section you will add the **costAndUsageReport** section to the *global-config.yaml* configuration file

1. Navigate to [AWS CodeCommit](https://console.aws.amazon.com/codesuite/codecommit/home) console
2. Select the ***aws-accelerator-config***
   repository.
3. Select the file ***global-config.yaml***
4. Click ***Edit***
5. At the bottom of the configuration file a *reports* section will need to be added (if it does not already exist, if the report section exists nest costAndUsageReport: under this), allowing for **costAndUsageReport** properties to be provided. A sample of a cost and usage report is provided below.

6. Fill in the fields under the *Commit changes to main* section and click *Commit changes*