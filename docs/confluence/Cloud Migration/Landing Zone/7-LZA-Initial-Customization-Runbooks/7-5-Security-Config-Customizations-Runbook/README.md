# 7-5-Security-Config-Customizations-Runbook

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867097773/7-5-Security-Config-Customizations-Runbook

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:33 AM

---

---

title: 7.5 Security Config Customizations Runbook
-------------------------------------------------

**Purpose**
-----------

In this runbook we are applying the next set of customizations which configures security configuration for the solution. We will being to modify the template Rapid Migration LZA yaml configuration files using the decisions gathered and documented.

**Prerequisites**
-----------------

* Ensure that the Landing Zone Accelerator pipeline is green before continuing.
* Obtain the latest Rapid Migration default yaml configuration files for LZA.

**Steps**
---------

1. Open the Rapid Migration's `security-config.yaml` file in an editor
2. Replace the **iamPasswordPolicy** values with the proper documented policy
3. In the LZA CodeCommit, replace the existing `security-config.yaml` with the modified Rapid Migration version.
4. Push the change into LZA CodeCommit, which should trigger the pipeline
5. Monitor the LZA Pipeline and wait for it to go green

**Attachments:**

[image-20220323-193830.png](../../attachments/image-20220323-193830.png)

[image-20220323-193927.png](../../attachments/image-20220323-193927.png)

[image-20220323-194302.png](../../attachments/image-20220323-194302.png)

[image-20220323-194429.png](../../attachments/image-20220323-194429.png)

[image-20220519-202357.png](../../attachments/image-20220519-202357.png)

[image-20220519-202521.png](../../attachments/image-20220519-202521.png)

[image-20220519-211031.png](../../attachments/image-20220519-211031.png)