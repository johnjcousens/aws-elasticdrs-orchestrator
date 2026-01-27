# 1-2-2-Sample starting point for permission-sets with AWS managed policies in AWS Identity Center

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5057052838/1-2-2-Sample%20starting%20point%20for%20permission-sets%20with%20AWS%20managed%20policies%20in%20AWS%20Identity%20Center

**Created by:** Lei Shi on August 29, 2025  
**Last modified by:** Lei Shi on August 29, 2025 at 03:27 PM

---

Below is a set of permission-sets with AWS managed policies in AWS Identity Center based on AWS best practices, it is a practical starting point for HealthEdge to form Identity Management in AWS with a hierarchical pattern. These can be picked and implemented at corporate level or BU level, please add additional namespace to differentiate the applied scope:

1. **<namespace>-View-Only**

* AWS managed policy: `ViewOnlyAccess`
* Best for: Auditors, Financial teams, Read-only users
* Allows viewing resources across AWS services without modification rights

2. **<namespace>-Security-Audit**

* AWS managed policy:
* `SecurityAudit`
* `AWSSecurityHubFullAccess`
* `AWSConfigRole`
* `AmazonGuardDutyFullAccess`
* …
* Best for: Security teams, Compliance officers
* Provides access to view security-related configurations

3. **<namespace>-Power-User**

* AWS managed policy: `PowerUserAccess`
* Best for: DevOps, Senior Developers
* Full access to AWS services except IAM/Organizations management

4. **<namespace>-Network-Administrator**

* AWS managed policies:

  + `AWSNetworkAdministrator`
  + `AWSVPCReadOnlyAccess`
  + …
* Best for: Network teams
* Manage VPC, Direct Connect, Route53, etc.

5. **<namespace>-Database-Administrator**

* AWS managed policies:

  + `AmazonRDSFullAccess`
  + `AmazonDynamoDBFullAccess`
  + `AmazonRedshiftFullAccess`
  + …
* Best for: DBAs
* Manage all database services

6. **<namespace>-Developer**

* AWS managed policies:

  + `AWSCodeBuildAdminAccess`
  + `AWSCodeDeployFullAccess`
  + `AWSCodePipelineFullAccess`
  + `AWSLambda_FullAccess`
  + …
* Best for: Development teams
* Access to development-related services

7. **<namespace>-Financial-Operations**

* AWS managed policies:

  + `AWSBillingReadOnlyAccess`
  + `AWSCostAndUsageReportAccess`
  + …
* Best for: Finance teams
* Access to billing and cost management

8. **<namespace>-Cloud-Operations**

* AWS managed policies:

  + `CloudWatchFullAccess`
  + `AWSSystemsManagerFullAccess`
  + `AWSCloudTrailReadOnlyAccess`
  + …
* Best for: Operations teams
* Monitor and manage AWS resources

1. **<namespace>-Administrator**

* AWS managed policy: `AdministratorAccess`
* Best for: Cloud Platform team
* Full access to all AWS services (use sparingly)

### Best Practices for Implementation:

1. Follow least privilege principle - start with minimal access and add as needed
2. Use groups in Identity Center to assign permission sets
3. Regularly review and audit permission sets
4. Consider creating custom permission sets for specific needs
5. Document all permission set assignments
6. Use AWS Organizations SCPs as guardrails
7. Enable AWS CloudTrail for all permission set usage monitoring
8. Consider compliance requirements
9. Implement proper break-glass procedures
10. Use AWS IAM Access Analyzer to review permissions