# 7-6-Network-Customizations-Runbook

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867000119/7-6-Network-Customizations-Runbook

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:33 AM

---

---

title: 7.6 Network Customizations Runbook
-----------------------------------------

**Purpose**
-----------

In this runbook we are applying the last set of customizations which configures network for the solution. We will being to modify the template Rapid Migration LZA yaml configuration files using the decisions gathered and documented.

**Prerequisites**
-----------------

* Ensure that the Landing Zone Accelerator pipeline is green before continuing.
* Obtain the latest Rapid Migration default yaml configuration files for LZA.

**Steps**
---------

1. Pause the LZA Pipeline stages to prevent changes from triggering the pipeline
2. Open the Rapid Migration's `network-config.yaml` 
   file in an editor
3. Replace the **homeRegion** with the proper documented region
4. Specify the transitGateways configuration to match the documented design
5. Specify the centralNetworkServices configuration to match the documented design
   1. ipam - adjust CIDRs and pools
   2. route53Resolver - adjust targetIps and domainNames for forwarding unknown private DNS requests back to on-prem
   3. networkFirewall - Adjust policies and rules, or remove if not used
6. Update the vpcs section to match the documented design
   1. network-endpoints: likely no changes
   2. network-boundary: centralized-egress without a firewall. Remove this VPC if you plan to use the network-boundary-firewall VPC.
   3. shared-services: likely no changes
   4. network-boundary-firewall: centralized-egress with a firewall (AWS NFW or 3rd Party). Remove this VPC if you plan to use the network-boundary VPC.
   5. migration: likely no changes
7. In the LZA CodeCommit, replace the existing `network-config.yaml` 
   with the modified Rapid Migration version
8. In the LZA CodeCommit, upload the 
   `vpc-endpoint-policies` folder and sub-files from the Rapid Migration version
9. Re-enable the LZA Pipeline and release a change
10. Monitor the LZA Pipeline and wait for it to go green

**Attachments:**

[image-20220323-193830.png](../../attachments/image-20220323-193830.png)

[image-20220323-193927.png](../../attachments/image-20220323-193927.png)

[image-20220323-194302.png](../../attachments/image-20220323-194302.png)

[image-20220323-194429.png](../../attachments/image-20220323-194429.png)

[image-20220519-202357.png](../../attachments/image-20220519-202357.png)

[image-20220519-202521.png](../../attachments/image-20220519-202521.png)

[image-20220519-211031.png](../../attachments/image-20220519-211031.png)