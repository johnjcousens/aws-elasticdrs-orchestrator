# 3-Configuration-Files-Overview

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867033029/3-Configuration-Files-Overview

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:23 AM

---

**Purpose**
-----------

The purpose of this page is to describe the background and functionality of each respective configuration file. This also includes respective links to the API documentation for the resources that are mapped to its respective config file.

**Configuration Files**
-----------------------

### [Accounts Configuration File (accounts-config.yaml)](https://github.com/awslabs/landing-zone-accelerator-on-aws/blob/main/reference/sample-configurations/aws-best-practices/accounts-config.yaml)

The accounts configuration file will be used to manage all of the AWS accounts within the AWS Organization. Adding a new account to this configuration file will invoke the account creation process from the Landing Zone Accelerator. The configuration registers and requires the mandatory accounts that includes the root account of the AWS Organization, as well as the Logging and Security accounts that are designed. Workload accounts will be additional (optional accounts) that are managed by Landing Zone Accelerator

**Note:** If using AWS Control Tower, these will be the Logging and Audit/Security accounts created during the provisioning process of AWS Control Tower.

#### Documentation:

For Configuration of the accounts configuration, please reference the following documentation here for the parent [configuration](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.AccountConfig.html).

---

### [Global Configuration File (global-config.yaml)](https://github.com/awslabs/landing-zone-accelerator-on-aws/blob/main/reference/sample-configurations/aws-best-practices/global-config.yaml)

The global configuration file will be used to configure the management as it relates to region deployments of resources through Landing Zone Accelerator and the IAM Role used to perform administrator-level deployments.

#### Documentation:

For Configuration of the global configuration, please reference the following documentation here for the parent [configuration](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.GlobalConfig.html).

---

### [IAM Configuration File (iam-config.yaml)](https://github.com/awslabs/landing-zone-accelerator-on-aws/blob/main/reference/sample-configurations/aws-best-practices/iam-config.yaml)

The IAM configuration file will be used to configure resources around access-control management. This includes resources such as AWS Identity and Access Management (AWS IAM) Policies, Users, and Groups.

##### IAM Parent Configuration

To configure IAM resources, please reference the following documentation here for the parent [configuration](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.IamConfig.html).

##### IAM Resource Configurations

The IAM Configuration file contains configuration sets pertaining to each respective resource. For more details on each configuration, refer to the following mapping:

* [Policy Sets](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.GroupSetConfig.html)
* [Role Sets](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.RoleSetConfig.html)
* [Group Sets](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.GroupSetConfig.html)
* [User Sets](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.UserSetConfig.html)

---

### [Network Configuration File (network-config.yaml)](https://github.com/awslabs/landing-zone-accelerator-on-aws/blob/main/reference/sample-configurations/aws-best-practices/network-config.yaml)

The network configuration file will be used to managed and implement network resources to establish a WAN/LAN architecture to support cloud operations and application workloads in AWS.

#### Network Parent Configuration

To configure Network resources, please reference the following documentation here for the parent [configuration](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.NetworkConfig.html).

#### Network Resource Configurations

The Network Configuration file contains configuration sets pertaining to each respective resource. For more details on each configuration, refer to the following mapping:

* [Central Network Service Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.CentralNetworkServicesConfig.html)
* [DHCP Options Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.DhcpOptsConfig.html)
* [Default (Deletion) VPC Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.DefaultVpcsConfig.html)
* [Endpoint Policy Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.EndpointPolicyConfig.html)
* [Prefix List Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.PrefixListConfig.html)
* [Transit Gateway Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.TransitGatewayConfig.html)
* [VPC Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.VpcConfig.html)
* [VPC Peering Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.VpcPeeringConfig.html)
* [VPC Flow Log Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.VpcFlowLogsConfig.html)

---

### [Organization Configuration File (organization-config.yaml)](https://github.com/awslabs/landing-zone-accelerator-on-aws/blob/main/reference/sample-configurations/aws-best-practices/organization-config.yaml)

The Organization config file focuses on the configuration of AWS Organization features that allow customer's to apply policies at scale in AWS.

##### Organization Parent Configuration

To configure AWS Organization services, please reference the following documentation here for the parent [configuration](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.OrganizationConfig.html).

##### Organization Resource Configurations

The IAM Configuration file contains configuration sets pertaining to each respective resource. For more details on each configuration, refer to the following mapping:

* [Backup Policy Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.BackupPolicyConfig.html)
* [Organization Unit Config](https://tsd.pages.aws.dev/accelerators/aws-platform-accelerator/classes/_aws_accelerator_config.OrganizationalUnitConfig.html)
* [Quarantine New Account Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.QuarantineNewAccountsConfig.html)
* [Service Control Policy Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.ServiceControlPolicyConfig.html)
* [Tagging Policy Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.TaggingPolicyConfig.html)

---

### [Security Configuration File (security-config.yaml)](https://github.com/awslabs/landing-zone-accelerator-on-aws/blob/main/reference/sample-configurations/aws-best-practices/security-config.yaml)

The security configuration file will be used to create resources focused around detective and preventative mechanisms within AWS, along with delegated administration  of core security services.

##### Security Parent Configuration

To configure AWS native security related services, please reference the following documentation here for the parent [configuration](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.SecurityConfig.html).

##### Security Resource Configurations

The IAM Configuration file contains configuration sets pertaining to each respective resource. For more details on each configuration, refer to the following mapping:

* [Access Analyzer Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.AccessAnalyzerConfig.html)
* [AWS Config Rule Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.AwsConfig.html)
* [Central Security Services Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.CentralSecurityServicesConfig.html)
* [Cloud Watch Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.CloudWatchConfig.html)
* [IAM Password Policy Config](https://awslabs.github.io/landing-zone-accelerator-on-aws/classes/_aws_accelerator_config.SecurityConfig.html#iamPasswordPolicy)