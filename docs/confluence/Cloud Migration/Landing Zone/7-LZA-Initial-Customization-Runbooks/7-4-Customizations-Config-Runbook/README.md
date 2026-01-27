# 7-4-Customizations-Config-Runbook

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867065188/7-4-Customizations-Config-Runbook

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:33 AM

---

---

title: 7.4 Customizations Config Runbook
----------------------------------------

**Purpose**
-----------

In this runbook we are applying the next set of customizations which configures CloudFormation scripts required for the solution. We will being to modify the template Rapid Migration LZA yaml configuration files using the decisions gathered and documented.

**Prerequisites**
-----------------

* Ensure that the Landing Zone Accelerator pipeline is green before continuing.
* Obtain the latest Rapid Migration default yaml configuration files for LZA.

**Steps**
---------

1. Pause the LZA Pipeline stages to prevent changes from triggering the pipeline
2. Open the Rapid Migration's `customizations-config.yaml` file in an editor
3. Replace the **homeRegion** with the proper documented region
4. Replace the **ManagementAccountId** value with the Account Id for the management account
5. In the LZA CodeCommit, replace the existing `customizations-config.yaml` with the modified Rapid Migration version. (Note: this file may not exist yet in CodeCommit)
6. In the LZA CodeCommit, upload the `cloudformation` folder and sub-files from the Rapid Migration version
7. Re-enable the LZA Pipeline and release a change
8. Monitor the LZA Pipeline and wait for it to go green

**Attachments:**

[image-20220323-193830.png](../../attachments/image-20220323-193830.png)

[image-20220323-193927.png](../../attachments/image-20220323-193927.png)

[image-20220323-194302.png](../../attachments/image-20220323-194302.png)

[image-20220323-194429.png](../../attachments/image-20220323-194429.png)

[image-20220519-202357.png](../../attachments/image-20220519-202357.png)

[image-20220519-202521.png](../../attachments/image-20220519-202521.png)

[image-20220519-211031.png](../../attachments/image-20220519-211031.png)