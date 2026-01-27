# 1-2-Decision-Naming-Conventions

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867033792/1-2-Decision-Naming-Conventions

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on November 03, 2025 at 12:36 PM

---

---

1.2 Decision Naming Conventions
-------------------------------

**Purpose**
-----------

AWS Account, OU, and AWS resource naming conventions are documented below.

**Organization Units**
----------------------

AWS Organization Unit (OU) names will be in camel case. For example:

* Infrastructure
* MyOrganizationUnit

**AWS Accounts**
----------------

### AWS Account Email

Each AWS Account requires a globally unique email address across AWS. The email should follow a predictable pattern, be all lowercase, and include the account name (separating words with dashes). For example, you may have the following pattern: `aws-lz-<accountname>@example.com`, where <accountname> is replaced with the name of the AWS account. (e.g., aws-lz-shared-services@example.com).

Email [sub-addressing](https://learn.microsoft.com/en-us/exchange/recipients-in-exchange-online/plus-addressing-in-exchange-online) allows the user to append a tag to a local email address using a '+' delimiter (e.g., aws+<accountname>@example.com). The email server strips off the tag and forwards all received email to the local email address. Email sub-addresses act like aliases to the local email address. They avoid the requirement to create separate unique email addresses on the email server. HealthEdge will use the following account email naming convention:

* aws@healthedge.com # local management email account for the AWS Control Tower Management account
* aws+log-archive@healthedge.com # email sub-addressing account for the AWS Control Tower LogArchive account
* aws+audit@healthedge.com # email sub-addressing account for the AWS Control Tower Audit account
* aws+<account-name>@healthedge.com # email sub-addressing account for a typical non-foundational account

**NOTE:** The **management** email account should be either a distribution list or a “shared mailbox” allowing multiple authorized user access. This will avoid potential account lockout if management staff leave the organization. This account should also allow 'send-as' permissions. AWS may require an email from the management account directly to approve certain types of changes (billing for example).

### Account Name

All account names, and account aliases, will be in camel case. For example:

* Management
* LogArchive
* Audit
* SharedServices

AWS Resources General Naming Convention
---------------------------------------

`[business-unit]-[customer]-[resource-type]-[descriptor]-[environment]-[region]`

#### Examples

`hrp-mcho-ec2-db`001`-dev-use1`  
`gc-internal-ec2-ad1-prod-usw2`

### Business Unit

* HRP: `hrp`
* GC: `gc`
* Source: `src`
* Wellframe: `wf`
* None/Global: `he`

### Customer

Include the applicable customer code e.g. `mcho` or `none`.

### Resource Type

* Amazon EC2 instance: `ec2`
* Amazon S3 Bucket: `s3`
* VPC Endpoints: `vpce`
* FSX for NetApp ONTAP: `fsxn`
* RDS: `rds`
* Security Group: `sg`
* etc.

### Descriptor

Functional description or purpose. For EC2 instances this might be used to indicate OS, role, hostname, or similar information for easy reference, e.g. `src-internal-ec2-webserver01-uat-usw1`.

### Environment

The commonly used abbreviation for environment e.g. `dev`, `sit`, `uat`, `preprod`, `prod` etc.

### AWS Region

* US East 1 (N. Virginia): `use1`
* US East 2 (Ohio): `use2`
* US West 1 (N. California): `usw1`
* US West 2 (Oregon): `usw2`
* Global resources (e.g. Route53 hosted zone): `global`

**Alternative Formats & Special Cases**
---------------------------------------

**Global resources:**  
Replace `[region]` with `global` for example `hrp-internal-r53-healthedgeinternal-prod-global` for a Route53 private hosted zone.

### S3 Buckets

Since the S3 namespace is global across all AWS customers, include the account id where possible for uniqueness, e.g. `hrp-internal-s3-dbbackups-prod-use1-1111222233334444`

S3-specific constraints to consider:

* Must be globally unique across all AWS customers and accounts
* 3-63 characters in length
* Lowercase letters, numbers, hyphens, and periods only
* Must start and end with letter or number
* Cannot be formatted as an IP address

### AWS Identity and Access Management (IAM)

IAM roles and policies are global resources and should use CamelCase e.g. `CrowdStrikeCloudTrailRole` or `HRPRDSServerRole`.