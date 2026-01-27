# Decision--Human-IAM-Roles-and-Policies-Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4966973490/Decision--Human-IAM-Roles-and-Policies-Design

**Created by:** Lei Shi on July 29, 2025  
**Last modified by:** Lei Shi on July 29, 2025 at 05:04 PM

---

### Document Lifecycle Status

**Purpose**
-----------

Outline the core federated IAM roles, and policies which will be used within accounts. This is not a definitive list and may grow as cloud adoption maturity grows. Defining human identity and access management requirements aligns to Well-Architected best practices. It is important to define requirements that will help control human access with appropriate defined, limited and segregated access. This requires the identification of compliance requirements, compliance resources, and defining roles and responsibilities.

### Decision

Define human identity and access management requirements

**Implementation**
------------------

### IAM Roles and Polices Definition

Each IAM Role need to be defined with responsibilities and based on those responsibilities the access permissions are allowed or denied with the help of IAM Policy.  An IAM Policy is a JSON formatted document that provides a list of ‘Allow’ or ‘Deny’ permissions. It consists of one or more statements, each of which describes the set of permissions. The following roles and policies will be deployed in each account.

#### Federated Roles

Document customer information here.

| Role | Purpose | Capabilities | Access Policy |
| --- | --- | --- | --- |
| <Namespace>-saml-administrator | Perform administration tasks including IAM | Full access to AWS services and resources | AdministratorAccess (AWS managed policy) |
| <Namespace>-saml-readonly | Perform monitoring tasks | Read-only access to AWS services and resources (no data read) | ReadOnly(AWS managed policy ) |
| <Namespace>-saml-billing | Perform billing and cost management tasks | Full access to account usage and viewing and modifying budgets and payment methods | Billing (AWS managed policy) |
| <Namespace>-saml-poweruser | Perform application administration tasks | Full access to AWS services and resources, except for Accounts, Orgs, and VPCs | <Namespace>-policy-poweruser { "Version": "October 17, 2012", "Statement": \[ { "Effect": "Allow", "NotAction": \[ "organizations:\\*", "account:\\*" \], "Resource": "\\*" }, { "Effect": "Allow", "Action": \[ "organizations:DescribeOrganization", "account:ListRegions" \], "Resource": "\\*" } \] }   <Namespace>-policy-vpc-restricted { "Version": "October 17, 2012", "Statement": \[ { "Effect": "Deny", "Action": \[ "ec2:RejectVpc\\*", "ec2:CreateVpc\\*", "ec2:ModifyVpc\\*", "ec2:Accept\\*", "ec2:AttachClassicLinkVpc\\*", "ec2:CreateDefaultVpc", "ec2:DeleteVpc\\*", "ec2:AssociateVpc\\*", "ec2:DisassociateVpc\\*", "ec2:AdvertiseByoipCidr", "ec2:DeprovisionByoipCidr", "ec2:DescribeByoipCidrs", "ec2:ProvisionByoipCidr", "ec2:WithdrawByoipCidr", "ec2:AssociateSubnetCidrBlock", "ec2:DisassociateSubnetCidrBlock", "ec2:CreateTransitGatewayRouteTable", "ec2:CreateNatGateway", "ec2:AttachInternetGateway", "ec2:AcceptTransitGatewayVpcAttachment", "ec2:CreateTransitGateway", "ec2:ReplaceTransitGatewayRoute", "ec2:DeleteTransitGatewayVpcAttachment", "ec2:DeleteVpnGateway", "ec2:CreateInternetGateway", "ec2:CreateVpnGateway", "ec2:AssociateTransitGatewayRouteTable", "ec2:DeleteInternetGateway", "ec2:RejectTransitGatewayVpcAttachment", "ec2:DisassociateTransitGatewayRouteTable", "ec2:ModifyTransitGatewayVpcAttachment", "ec2:DisableTransitGatewayRouteTablePropagation", "ec2:DeleteEgressOnlyInternetGateway", "ec2:AttachVpnGateway", "ec2:DetachInternetGateway", "ec2:CreateCustomerGateway", "ec2:DeleteTransitGatewayRouteTable", "ec2:CreateTransitGatewayRoute", "ec2:DetachVpnGateway", "ec2:DeleteTransitGatewayRoute", "ec2:CreateTransitGatewayVpcAttachment", "ec2:DeleteCustomerGateway", "ec2:DeleteNatGateway", "ec2:CreateEgressOnlyInternetGateway", "ec2:EnableTransitGatewayRouteTablePropagation", "ec2:DeleteTransitGateway" \], "Resource": \[ "\\*" \] } \] } |
| <Namespace>-saml-systemadministrator | Application and development operations | Permissions to create and maintain resources across a large variety of AWS services, including AWS CloudTrail, Amazon CloudWatch, AWS CodeCommit, AWS CodeDeploy, AWS Config, AWS Directory Service, Amazon EC2, AWS Identity and Access Management (viewing ) , AWS Key Management Service, AWS Lambda, Amazon RDS, Route 53, Amazon S3, Amazon SES, Amazon SQS, AWS Trusted Advisor, and Amazon VPC. | SystemAdministrator (AWS managed policy) |
| <Namespace>-saml-securityaudit | Conduct account auditing and compliance assessments | Read-only access to AWS services and resources | SecurityAudit (AWS managed policy ) |
| <Namespace>-saml-securityresponse | Conduct security incidents investigation and mitigation | Full access to AWS services | AdministratorAccess (AWS managed policy) |

#### Non-federated Roles

Document customer information here.

| Role | Purpose | Capabilities | Trust Policy | Access Policy |
| --- | --- | --- | --- | --- |
| <Namespace>-role-breakglass | Emergency access in case SAML is down | Full access to AWS services and resources | <Namespace>-role-breakglass Trust Policy "Version": "October 17, 2012",  "Statement": \[  {  "Effect": "Allow",  "Principal": {  "AWS": "arn:aws:iam::<ManagementAccountID>:user/<Namespace>-user-breakglass"  },  "Action": "sts:AssumeRole",  "Condition": {  "Bool": {  "aws:MultiFactorAuthPresent": "true"  }  }  }  \]  } | AdministratorAccess (AWS managed policy) |

#### AMS Accelerator Role

AMS follows an onboarding process that requires cross-account access. If [Customer] is using AMS Accelerate, the *aws\_managedservices\_onboarding\_role* is required to exist with the necessary policy.

**Note:** Customers have the choice of using the managed AWS Administrator access policy or can use the least privileged approach.

| Role | Purpose | Capabilities | Access Policy | Cross-Account Access |
| --- | --- | --- | --- | --- |
| aws\\_managedservices\\_onboarding\\_role | Admin level role that allows for AMS Accelerate Onboarding | Full access to AWS services and resources | AdministratorAccess (AWS managed policy) | 328792436863 |
| aws\\_managedservices\\_onboarding\\_role | Least privileged access for AMS Accelerate Onboarding | Read-only access to AWS services and resources (no data read) | Managed Policies:   * ViewOnlyAccess * SecurityAudit * AWSCloudShellFullAccess  Custom Policy**Policy** | 328792436863 |

#### Additional AMS Roles

If using AMS Accelerate, the following roles and their respective IAM policies will be deployed by AMS into the [Customer] environment. More information on these resources can be found in the zip file located in this [documentation](https://docs.aws.amazon.com/managedservices/latest/accelerate-guide/acc-resource-inventory.html).

These roles do not need to be deployed or managed by the customer.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table ac:local-id="64f5cd95-9fe9-4d73-993a-e4fea0196cf9" data-layout="default" data-table-width="1800"><tbody><tr><th><span>Role</span></th><th><span>Purpose</span></th><th>AWS Managed Policies</th><th>Custom Policies</th></tr><tr><th><span>ams-access-admin</span></th><td>AMS Access</td><td>AdministratorAccess</td><td><ac:structured-macro ac:macro-id="c604bad7-2ca0-4ae3-9eb3-71173700b3b8" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th><span>ams-access-management</span></th><td>AMS Access</td><td><br/></td><td><ac:structured-macro ac:macro-id="f6d3989e-57af-4f40-bc91-f2a883a4321d" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th><span>ams-access-operations</span></th><td>AMS Access</td><td><ul><li>IAMReadOnlyAccess</li><li>PowerUserAccess</li></ul></td><td><ac:structured-macro ac:macro-id="19895354-da6f-460a-bc3e-72df933a447b" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th><span>ams-access-read-only</span></th><td>AMS Access</td><td>ReadOnlyAccess</td><td><ac:structured-macro ac:macro-id="d3cc1494-93b6-4f52-93d4-1f55fcce0616" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th><span>ams-detective-controls-vpc-flow-logs-role</span></th><td>Compliance &amp; Conformance</td><td><br/></td><td><ac:structured-macro ac:macro-id="6c5ef9e7-cfdf-4658-a50f-5a6a734c643a" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th><span>AWSServiceRoleForConfigConforms</span></th><td>Compliance &amp; Conformance</td><td>ConfigConformsServiceRolePolicy</td><td></td></tr><tr><th><span>ams-opsitem-autoexecution-role</span></th><td>Auto-Execution</td><td><br/></td><td><ac:structured-macro ac:macro-id="620d3ef3-b604-49c8-bc4c-b85c07613b5f" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>ams-opscenter-role</th><td>AMSOpsItems</td><td><br/></td><td><ac:structured-macro ac:macro-id="2c3e3d47-43e7-4c71-aed0-bf89c807cb94" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>ams-opscenter-eventbridge-role</th><td>Config Remediation</td><td><br/></td><td><ac:structured-macro ac:macro-id="cea56e7d-ccd9-4e32-8a57-1327a66ae30f" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>ams-resource-tagger-AWSManagedServicesResourceTagg-\*</th><td>Tag Mgmt</td><td>AWSLambdaBasicExecutionRole</td><td><ac:structured-macro ac:macro-id="e6fc2185-7924-4bcf-890f-d771b1e4dcc6" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>ams-alarm-manager-AWSManagedServicesAlarmManager-\*</th><td>Tag-Based Alarm Mgr</td><td>AWSLambdaBasicExecutionRole</td><td rowspan="3"><ac:structured-macro ac:macro-id="9214dbdb-c65d-4820-a4f0-9a790faa0da9" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>ams-alarm-manager-AWSManagedServicesMonito-\*</th><td>Monitoring</td><td>AWSLambdaBasicExecutionRole</td></tr><tr><th>ams-monitoring-AWSManagedServicesLogGroupLimitLamb\*</th><td>Monitoring</td><td>AWSLambdaBasicExecutionRole</td></tr><tr><th>ams-monitoring-AWSManagedServicesRDSMonitoring\*</th><td>Monitoring</td><td>Lambda</td><td><ac:structured-macro ac:macro-id="d9ddc9ed-f47c-4ef3-a392-2276dc32d8dc" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>ams-log-managed-AWSManagedServicesCloudTrailLog\*</th><td>Log Mgmt</td><td><br/></td><td><ac:structured-macro ac:macro-id="d6b5831d-40e3-46f1-835d-31850732e8eb" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>ams\_os\_configuration\_event\_rule\_role-\[REGION\]</th><td>Auto Instance Config</td><td><br/></td><td><ac:structured-macro ac:macro-id="1c731874-0678-4070-9e94-2ddbfd79939c" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>AMSOSConfigurationCustomerInstanceRole</th><td>Auto Instance Config</td><td><ul><li>CloudWatchAgentServerPolicy</li><li>AmazonSSMManagedInstanceCore</li></ul></td><td><ac:structured-macro ac:macro-id="f7a049d0-24e4-49f4-bf42-50076a489454" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>ams-backup-iam-role</th><td>Backup Mgmt</td><td><ul><li>AWSBackupServiceRolePolicyForBackup</li><li>AWSBackupServiceRolePolicyForRestores</li><li>AWSBackupFullAccess</li></ul></td><td><ac:structured-macro ac:macro-id="4cc1e3c2-8436-4651-95d3-2ef10833b58b" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>ams-backup-config-rule-st-amsBackupPlanConfigRule-\*</th><td>Backup Mgmt</td><td><br/></td><td><ac:structured-macro ac:macro-id="962b57eb-07a7-48bb-9bd8-dadd753d59df" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>customer\_ssm\_automation\_role</th><td>SSM</td><td><br/></td><td><ac:structured-macro ac:macro-id="7c042e90-4966-4d07-9ce5-2199b76bc67b" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>ams\_ssm\_automation\_role</th><td>SSM</td><td><br/></td><td><ac:structured-macro ac:macro-id="5ffc22fd-c879-46a4-9b49-5eb1f27faf96" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>amspatchconfigrulerole</th><td>Patch Mgmt</td><td><br/></td><td><ac:structured-macro ac:macro-id="69b7abc5-1661-4383-8218-674112e96217" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>mc-patch-reporting-service</th><td>Patch Mgmt</td><td><br/></td><td><ac:structured-macro ac:macro-id="31c6c77c-d02a-42d3-8199-917f08ebbcf6" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>ams-patch-reporting-infra-amspatchreportingconfigr-\*</th><td>Patch Mgmt</td><td><br/></td><td><ac:structured-macro ac:macro-id="b36a29dd-46cb-41d0-b433-e9165b8ea5af" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>mc-patch-glue-service-role</th><td>Patch Mgmt</td><td>AWSGlueServiceRole</td><td><ac:structured-macro ac:macro-id="4d7e2341-dd6b-4df2-9e0d-9df52ee4dda8" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>ams-patch-infrastructure-amspatchservicebusamspat</th><td>Patch Mgmt</td><td><br/></td><td><ac:structured-macro ac:macro-id="76c22b33-3329-4824-942c-1ddd47bbbae1" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr><tr><th>customer\_ssm\_automation\_role</th><td>SSM</td><td><br/></td><td><ac:structured-macro ac:macro-id="34b63910-15fa-4e38-8db7-38715607624f" ac:name="expand" ac:schema-version="1"><ac:parameter ac:name="title">Custom Policy</ac:parameter><ac:rich-text-body></ac:rich-text-body></ac:structured-macro></td></tr></tbody></table>



#### IAM Roles and [Customer] Directory Store Groups/Users Matrix

The following IAM Roles and [Customer] Directory Store Groups mapping will be used to construct SAML assertion. Document customer information here.

| AWS Account | IAM Role | Directory Store Group |
| --- | --- | --- |
| All | <Namespace>-saml-administrator | AWS-AccountID-administrator |
| All | <Namespace>-saml-readonly | AWS-AccountID-readonly |
| All | <Namespace>-saml-billing | AWS-AccountID-billing |
| All | <Namespace>-saml-poweruser | AWS-AccountID-poweruser |
| All | <Namespace>-saml-systemadministrator | AWS-AccountID-systemadministrator |
| All | <Namespace>-saml-securityaudit | AWS-AccountID-securityaudit |
| All | <Namespace>-saml-securityresponse | AWS-AccountID-securityresponse |

#### IdP Metadata

The following IdP metadata will be used to configure trust between [Customer] IdP and AWS accounts.

* To download an up-to-data metadata file,  the following public URL will be used:
* Current Metadata file(If not public URL is available):
* Identity Provider name that will be configured and setup within the customer’s AWS accounts: