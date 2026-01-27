# 1-2-1-Account-and-User-Management-Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866084068/1-2-1-Account-and-User-Management-Design

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Lei Shi on August 29, 2025 at 03:28 PM

---

Account and User Management Design
==================================

AWS Recommended Cloud Approach
==============================

Overview
--------

AWS recommends that enterprise customers take a multi-account approach for supporting multiple products/applications. The initial provisioning of accounts and users begins when a customer establishes a Landing Zone in AWS. The recommendations and options available for establishing a Landing Zone have evolved over the years, most recently with the introduction of the AWS Control Tower service. Additionally, many enterprise customers may have already established a multi-account approach either manually or with the help of AWS Solution Architects or Professional Services (e.g. [AWS Landing Zone](https://aws.amazon.com/solutions/aws-landing-zone/)). Once the initial Landing Zone is in place, customers will continue to provision / de-provision multiple accounts and users over time. Many customers may also choose to automate and support this process using their existing IT Service Management tools (e.g. ServiceNow). The recommended approach defined here for ongoing user and account management is scoped to customers using Control Tower or the AWS Landing Zone solution. However, these recommendations could also be applied to customers that have implemented a custom user and account provisioning process.

Both AWS Control Tower and AWS Landing Zone leverage the [AWS Single Sign-On (SSO) service](https://aws.amazon.com/single-sign-on/) integrated with AWS Organizations for multi-account user management. Most organizations will already have an identity management solution such as Active Directory (AD) in place. Customers can integrate with their existing AD implementation by using the AWS AD Connector.
The following relationship diagram provides a high level overview of AWS SSO with an AWS Directory Service Managed AD deployment:

User Management
---------------

By default, AWS SSO uses its own identity store for user / access management. However, for enterprises we recommend using the AWS SSO integration with Active Directory. Customers who don't have an existing identity store can use AWS Managed AD.

Management and access to AWS is driven through membership in the appropriate Active Directory groups. AD groups are associated to accounts with a permission set created in SSO [as detailed here](https://docs.aws.amazon.com/singlesignon/latest/userguide/useraccess.html). Users should not be assigned directly to accounts because if the user is deleted from Active Directory, they will need to be manually removed from SSO.

### Active Directory

User access should be managed by creating groups in Active Directory for each account and permission set you want to provide access.  For example, the following naming convention can be used for AD groups:
- AWS-<AccountNumber>-<Role><

After the AD group is created, users can be added and removed from the group using the existing processes for AD user / group management.  Finally, you should determine if a central group will be responsible for granting access to all users to the appropriate groups or if you will delegate control to the account owner by granting their AD user the ability to add / remove AD users from the AD groups associated with their account.

### Access Management

AWS SSO creates a default set of permission sets to support the broadest use cases:
- AWSReadOnlyAccess
- AWSPowerUserAccess
- AWSAdministratorAccess

These map to the ReadOnlyAccess, PowerUserAccess, and AdministratorAccess AWS managed IAM policies respectively.  You should try to minimize the creation of too many permission sets because each permission set will need to be separately managed and maintained and also complicates the uniform access control across your accounts.  Additionally, you should minimize the use of custom policies wherever possible and try to use managed policies to minimize the long term maintenance of permissions.  Finally, the principal of least privilege should be implemented where users are granted the minimal permission set required in order to satisfy their requirements.

If users require a different permission set than the default permission sets available, they should submit an exception request detailing the permissions needed.

A separate user in the SSO account should be created for AWS access and permission set management with MFA enabled limited to the appropriate permissions.

### AWS Control Tower Considerations

When you setup AWS Control Tower, it configures AWS SSO to use the internal SSO identity store and sets this up in the us-east-1 region. AWS Control Tower creates a number of SSO groups when it is first setup. If you intend to use Active Directory, then you must recreate the [default Control Tower groups](https://docs.aws.amazon.com/controltower/latest/userguide/sso.html) that you wish to use because AWS SSO deletes all preconfigured users and groups once AD is enabled.

Account Management
------------------

Ongoing account provisioning for both Control Tower and AWS Landing Zone (ALZ) is driven by AWS Service Catalog. Customers can integrate their existing ITSM tools such as ServiceNow with the Service Catalog portfolio / product used by Control Tower / ALZ to provision accounts. There are considerations depending on the landing zone solution detailed below.

Account names should align to the AD Organizational Unit (OU) if present or the application name depending on the approach for account segmentation. The account owner should be assigned to a management who has purchasing / spend authority for the account and who directly manage team members who will be using the account.

The process for account provisioning should be internally accessible to all users in the organization who may require an account, such as an internal wiki or portal page.

Account provisioning in an enterprise environment frequently requires additional configuration of the account (either automated or manual) such as:
- VPC / gateway configuration to integrate with transit and on premises networks
- [VPC endpoint](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-endpoints.html) configuration to connect privately to AWS services
- Governance controls such as AWS Config rules
- DNS and Route 53 zone zone configuration for name resolution of private networks and DNS forwarding for other private zones
- Sharing of approved AMIs with newly created account
- Shipping of logs such as CloudTrail and VPC Flow Logs to central account<
- Some of this configuration may be automated by the account provisioning solution implemented.

### New Account Request

The account request can be a spreadsheet, document, online form, or a service ticket type for the ITSM tool in use. There should be standards established for account creation approval and financial stewardship of the account. Separate process and intake forms may be established for non production vs production accounts.

One or more of the following fields may be applicable: 
- **Application Name:** will identify the domain and scope for the account. It will identify the services and applications that your team provisions in the account and may also include the functional boundary for the account (Dev, Test, QA, Production).  Account naming should follow the standards agreed upon for the customers multi-account approach. Many customers choose to create a separate account for each application / environment.
- **Application Business Description:**  Describes the purpose of the application.
- **Application Interconnectivity Requirements:**  Describes the systems / accounts / networks that the new account needs to be able to access. This can be a combination of existing AWS accounts, internet resources, and on premises systems.
- **Team Managed or Managed Service:**  Some customers may provide the option between allowing accounts to be team managed (most common) and allowing the account to be managed by a managed service provider such as Amazon Managed Services (AMS).
- **Sizing:** estimates for the account. Sizing includes both the number of hosts needed as well as the network bandwidth expected for both private(internal) traffic and external(public) traffic. Estimate the number of private IP's required by the application. This would include all VPC enabled services that require allocating private address's including internal load balancers, private RDS, VPC enabled lambda etc. A standard set of account sizes should be established for account sizing to align to the CIDR block size.  For example, using t-shirt sizes to establish total number of expected hosts.
- **Services** that you expect to implement or evaluate in the account.
- **Region(s)** that are approved and that the account should be created in.
- **Public facing** content introduces additional security requirements. Will your team be deploying information, applications, or services for B2B or B2C.
- **Contact Information** used to notify the team. Notifications will be sent out for any issues or information related to their account. An email distribution list is required.
- **Owner**: Technical contact for the account
- **Approver / Approval ID**:  Financial contact approving the spend generated in the account.  Approval identifier if there is a separate approval process prior to submitting request. 
- **Cost Center:**  If applicable to align to internal financial controls
- **Application ID**:  If your application is already an existing application and managed in CMDB, the identifier for the application.
- **Team Membership:**  List the users who should be given access to the account and what role they should have.  Reference back to the available roles established.
- **Environment:**  The environment for the account such as (Development, QA, Staging, or Production)

### De-provisioning / Removing An Account

Account de-provisioning and removal is not automated regardless of whether you use Control Tower or the ALZ solution.  Accounts must be de-provisioned using the [standard procedure for closing an account](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/close-account.html).  A management process should be define and approved for account de-provisioning / removal and can be automated / integrated with existing ITSM tools.  The account owner and their manager should be required for de-provisioning / removal of an account.

### AWS Control Tower Considerations

AWS Control Tower includes the [Account Factory](https://docs.aws.amazon.com/controltower/latest/userguide/account-factory.html) feature that creates a Service Catalog Product Portfolio and Service Catalog Product for the ongoing provisioning of new accounts to be managed by Control Tower in the master account. This Service Catalog product is managed by the Control Tower service and can't be updated or customized. Control Tower allows you to control certain predefined options for account provisioning such as the CIDR range for account VPCs from the Account Factory settings page in AWS Control Tower.  However, these settings remain the same for each account that is provisioned causing all accounts to have the same VPC CIDR ranges.  It is important for customers to consider their current and future networking requirements and the impact of overlapping CIDR blocks.

---

Operational Readiness State
---------------------------

For operational readiness, there should be a clearly defined process for requesting a new account, removing an account, and gaining / changing access to an existing account on a well known internal website / portal.

* The appropriate ITSM tools (e.g. ServiceNow) should implement the request process with the appropriate approvals.
* Each account owner should be trained on the default permission sets available for ongoing access requests for their teams.
* A separate process should be available for users that require a new permission set to be created along with the appropriate security reviews and approvals.
* The central cloud center of excellence team should be aligned to the ongoing account and user provisioning process and define an SLA for for the organization.

---

Recommendations for Future Enhancements
---------------------------------------

Future improvements are on improving the speed of account provisioning and depth of account management:
- Automated provisioning of new accounts via ITSM tools without manual intervention.
- Automated provisioning / access change requests  via ITSM tools without manual intervention.
- Automation of account configuration after the account has been provisionedsuch as the automatic configuration of gateways, AWS Config / Config Rules, etc.
- Automated notification and copy of AWS cost usage to account owners
- Automated provisioning of instances and resources via a separate / connected process to account provisioning

**Attachments:**

[AWS\_SSO\_AD.png](../../attachments/AWS_SSO_AD.png)