# 7-3-IAM-and-Global-Config-Customization-Runbook

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867033858/7-3-IAM-and-Global-Config-Customization-Runbook

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:33 AM

---

---

title: 7.3 IAM and Global Config Customization Runbook
------------------------------------------------------

**Purpose**
-----------

In this runbook we are applying the next set of customizations which configures IAM and other global settings for LZA. We will being to modify the template Rapid Migration LZA yaml configuration files using the decisions gathered and documented.

**Prerequisites**
-----------------

* Ensure that the Landing Zone Accelerator pipeline is green before continuing.
* Obtain the latest Rapid Migration default yaml configuration files for LZA.
* Ensure that Control Tower Organization Trails are disabled.

**Steps**
---------

1. Pause the LZA Pipeline stages to prevent changes from triggering the pipeline
2. Open the Rapid Migration's `global-config.yaml` file in an editor
3. Replace the **homeRegion** with the proper documented region
4. Replace the **cloudwatchLogRetentionInDays** with the proper duration
5. In the LZA CodeCommit, replace the existing `global-config.yaml` with the modified Rapid Migration version
6. In the LZA CodeCommit, replace the existing `iam-config.yaml` with the Rapid Migration version
7. In the LZA CodeCommit, upload the `iam-policies` folder and sub-files from the Rapid Migration version
8. Re-enable the LZA Pipeline and release a change
9. Monitor the LZA Pipeline and wait for it to go green

**Attachments:**

[image-20220323-193830.png](../../attachments/image-20220323-193830.png)

[image-20220323-193927.png](../../attachments/image-20220323-193927.png)

[image-20220323-194302.png](../../attachments/image-20220323-194302.png)

[image-20220323-194429.png](../../attachments/image-20220323-194429.png)

[image-20220519-202357.png](../../attachments/image-20220519-202357.png)

[image-20220519-202521.png](../../attachments/image-20220519-202521.png)

[image-20220519-211031.png](../../attachments/image-20220519-211031.png)