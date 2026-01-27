# 7-2-Account-Customization-Runbook

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867097794/7-2-Account-Customization-Runbook

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:33 AM

---

---

title: 7.2 Account Customization Runbook
----------------------------------------

**Purpose**
-----------

In this runbook we are applying the first set of customizations which sets up new accounts. We will being to modify the template Rapid Migration LZA yaml configuration files using the decisions gathered and documented.

**Prerequisites**
-----------------

* Ensure that the Landing Zone Accelerator pipeline is green before continuing.
* Obtain the latest Rapid Migration default yaml configuration files for LZA.

**Create Organizational Units with AWS Control Tower**
------------------------------------------------------

If you are using AWS Control Tower you will need to register the new OU in Control Tower for it to be a valid target OU for newly created account. If you are not using Control Tower, you can skip this part.

1. Navigate to [AWS ControlTower](https://console.aws.amazon.com/controltower/home) console
2. Select **Organizational units** from the left menu
3. Choose create OU for each of the OUs required: Management, Infrastructure, and Workloads.
4. In Control Tower, move the management account to the newly created Management OU

**LZA Customization Steps**
---------------------------

1. Pause the LZA Pipeline stages to prevent changes from triggering the pipeline
2. Open the Rapid Migration's `accounts-config.yaml` file in an editor
3. Replace all **email** addresses with the proper documented email addresses for each account
4. In the LZA CodeCommit, replace the existing `accounts-config.yaml` with the modified Rapid Migration version
5. In the LZA CodeCommit, replace the existing `organization-config.yaml` with the Rapid Migration version
6. In the LZA CodeCommit, upload the `service-control-policies` folder and files from the Rapid Migration version
7. Re-enable the LZA Pipeline and release a change
8. Monitor the LZA Pipeline and wait for it to go green (This may take some time because it will be creating 3 new accounts)

**Attachments:**

[image-20220323-193830.png](../../attachments/image-20220323-193830.png)

[image-20220323-193927.png](../../attachments/image-20220323-193927.png)

[image-20220323-194302.png](../../attachments/image-20220323-194302.png)

[image-20220323-194429.png](../../attachments/image-20220323-194429.png)

[image-20220519-202357.png](../../attachments/image-20220519-202357.png)

[image-20220519-202521.png](../../attachments/image-20220519-202521.png)

[image-20220519-211031.png](../../attachments/image-20220519-211031.png)