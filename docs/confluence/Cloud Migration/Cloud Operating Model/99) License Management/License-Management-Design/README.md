# License-Management-Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866051152/License-Management-Design

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:04 AM

---

| **AWS Recommended Cloud Approach** |
| --- |
| Overview Many customers migrate Commercial Off The Shelf (COTS) products to AWS from Independent Software Vendors (ISVs) from their on premises environments to AWS. These products have licensing terms that must be adhered as the workloads run in the cloud.  Some vendors have implemented unique restrictions when their products run in cloud environments that must be observed.  Many ISVs also offer their products via the AWS Marketplace as license included products.  These products don't require a separate license and the licensing cost is a part of using the AMI / Marketplace offering. Many customers have already purchased licenses for COTS products they intend to migrate to AWS. The licenses for these products may be licensed based upon on virtual cores (vCPUs), physical cores, sockets, or number of machines. When migrated, these products may run on EC2 instances, dedicated instances, dedicated hosts, or Spot Instances and Spot Fleet.  Effective software license management relies on the following:   * An expert understanding of language in enterprise licensing agreements * Appropriately restricted access to operations that consume licenses * Accurate tracking of license inventory   The following diagram illustrates the distinct but coordinated duties of license administrators, who manage permissions and configure License Manager, and users, who create, manage, and delete resources through the Amazon EC2 console: ![](../..../../attachmentslicense\_mgr\_aws.png) |

---

| **Operational Readiness State** |
| --- |
| For the Operational Readiness state, customer will evaluate their current licensing for COTS software that is being migrated to AWS as well as licenses for products such as operating systems (Windows / Linux), databases, etc. An inventory of current software licenses and products should be made as a part of the migration. This can be done in a spreadsheet or from a customers existing CMDB. The license compliance and management team for \[Customer\] is responsible for determining what licenses are in use and whether additional licenses will need to be purchased while the software is in transition and running on premise as well as AWS. The existing enterprise agreements such as Microsoft Software Assurance / Mobility should be reviewed for options to reuse existing licenses in AWS.  ISV's should be consulted about license usage in the transition to AWS and license portability.  \[Customer\] will leverage the control elements within their existing toolset for license management of COTS products. Licensed software that is being migrated to AWS can use the same mechanisms for license management that is in place. Licenses are usually managed as authorized / named user, licensed per host, or a floating license management method (such as FlexLM) with a central license server.  License keys and floating licenses are the responsibility of the customer and should be planned / managed through the migration.  License Manager can be used to support license management activities in AWS. License Manager supports tracking any software that is licensed based on  **virtual cores (vCPUs)**,  **physical cores**,  **sockets**, or  **number of machines**. This includes a variety of software products from Microsoft, IBM, SAP, Oracle, and other vendors.  Effective software license management relies on the following:   * An expert understanding of language in enterprise licensing agreements * Appropriately restricted access to operations that consume licenses * Accurate tracking of license inventory |

---

| **Recommendations for Future Enhancements** |
| --- |
| Improvements in future license management can include:   * Automated provisioning of new licenses from ISVs using API integration. * Automated check in / check out / reuse of license keys as part of instance   automation. * Reporting of COTS product / licensing to consumers to validate continued   need and automated de-provisioning of licenses based on thresholds and   continued business need. |

**Attachments:**

[AWS\_SSO\_AD.png](../../attachments/AWS_SSO_AD.png)

[image2019-6-23\_11-24-32.png](../../attachments/image2019-6-23_11-24-32.png)

[image2019-6-23\_11-25-15.png](../../attachments/image2019-6-23_11-25-15.png)

[image2019-6-23\_11-31-6.png](../../attachments/image2019-6-23_11-31-6.png)

[image2020-3-12\_17-58-14.png](../../attachments/image2020-3-12_17-58-14.png)

[license\_mgr\_aws.png](../../attachments/license_mgr_aws.png)