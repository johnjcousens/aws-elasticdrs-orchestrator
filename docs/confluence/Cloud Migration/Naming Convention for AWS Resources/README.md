# Naming Convention for AWS Resources

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5170594154/Naming%20Convention%20for%20AWS%20Resources

**Created by:** Himanshu Gupta on October 15, 2025  
**Last modified by:** Himanshu Gupta on October 15, 2025 at 02:28 PM

---

Document version: v0.2

Status: Draft

This document defines the standardized naming convention for AWS resources during HealthEdge's migration to AWS. The naming convention ensures consistency, clarity, and operational efficiency across all environments and service lines.

General naming convention
-------------------------

[service-line]-[resource-type]-[descriptor]-[environment]-[region]

**Alternative Format**

* **For global resources:** global-[resource-type]-[descriptor]

### **Component Definitions**

* Service Line: hrp, gc, source, wellframe
* Resource Type: AWS service abbreviation (see resource-specific sections)
* Descriptor: Functional description or purpose (including shared services like ad, monitoring)
* Environment: dev, uat, perf, prod
* Region: AWS region code (e.g., use1, use2, usw1, usw2)

### Service Lines

* HRP: hrp
* GC: gc
* Source: source
* WellFrame: wellframe

Note: Each service line manages its own shared services (AD, monitoring, etc.) within their respective accounts.

### Environments

* Development: dev
* User Acceptance Testing: uat
* Performance Testing: perf
* Production: prod

### AWS Regions (In Scope)

* US East 1 (N. Virginia): use1
* US East 2 (Ohio): use2
* US West 1 (N. California): usw1
* US West 2 (Oregon): usw2

### Resource Type

* Amazon VPC
* Amazon VPC Subnet
* Amazon VPC Endpoints
* Amazon EC2 instance
* Amazon S3 Bucket
* FSX for NetApp FSxN
* RDS
* IAM
* Security Group

Resource-Specific Naming Conventions
------------------------------------

### Amazon VPC (Virutal Private Cloud)

As the VPC are already deployed using LZA, we will use the existing naming convention.

**Format**: [Environment][Identifier][Region]

**Example**:

* DevelopmentWorkloadUsEast1
* ProductionWorkloadUsWest2

### Amazon VPC Subnets

As the subnets are already deployed using LZA, we will use the existing naming convention.

**Format:** [Identifier][Resource][AZ]

**Example:**

* PublicSubnet1
* PrivateSubnet2

### Amazon VPC Endpoints (Centralised)

All VPC Endpoints (except DataSync) are centerally managed in a networking AWS account and deployed using LZA, we will use the existing naming convention. Currently the VPCE doesn’t have a name and should be renamed via LZA.

**Format:** global-vpce-[service]-[region]

**Example:**

* global-vpce-s3-use1
* global-vpce-ec2-use1
* global-vpce-ssm-use1

Service Types for VPCE: s3, ec2, ssm, kms, logs, mgn

### Amazon VPC Endpoints (Distributed)

DataSync VPC Endpoint will be deployed as a distributed endpoint in individual AWS account that needs a DataSync agent to migrate the storage.

**Format**: [service-line]-vpce-[service]-[region]

**Example**:

* gc-vpce-datasync-use1
* hrp-vpce-datasync-use1

### Amazon S3 Buckets

**Format**: [service-line]-s3-[purpose]-[environment]-[region]

**Examples:**

hrp-s3-data-prod-use1

gc-s3-backup-uat-use1

S3-Specific Constraints:

* Must be globally unique across all AWS accounts
* 3-63 characters in length
* Lowercase letters, numbers, hyphens, and periods only
* Must start and end with letter or number
* Cannot be formatted as IP address

### Amazon EC2 Instances

**Format**: FQDN-[AZ]

**Examples**:

* ops-wl-st01-az1

### Amazon FSx for NetApp (FSxN)

**Format**: [service-line]-fsxn-[purpose]-[environment]-[region]

**Examples**:

* hrp-fsxn-data-prod-use1
* gc-fsxn-shared-uat-use1

Purpose Types: data, shared, backup, archive, home, binaries, config

### Amazon Relational Database Service (RDS)

**Format**: [service-line]-rds-[engine]-[purpose]-[environment]-[region]

**Examples**:

* hrp-rds-mysql-primary-prod-use1
* gc-rds-postgres-analytics-uat-use1

Engine Types: mysql, postgres, oracle, sqlserver, aurora

Purpose Types: primary, replica, reporting

RDS-Specific Constraints:  
- 1-63 characters in length  
- First character must be a letter  
- Lowercase letters, numbers, and hyphens only  
- Cannot end with hyphen or contain consecutive hyphens

### AWS Identity and Access Management (IAM)

**Format**: [service-line]-[iam-type]-[purpose]

**Examples**:

* *IAM Roles*

  + hrp-iamrole-ec2-baseline
  + gc-iamrole-rds-backup
* *IAM Policies*

  + hrp-iampolicy-s3-read
  + hrp-iampolicy-ec2-admin
* *IAM Groups*

  + hrp-iamgroup-developers
  + hrp-iamgroup-admins

IAM Types: role, policy, group, user

Purpose: Descriptive function (e.g., ec2-web, s3-read, developers)

### Amazon Security Groups

* **Format**: [service-line]-sg-[purpose]-[environment]-[region]
* **Example**

  + hrp-sg-linux-global
  + hrp-sg-payer-global
  + hrp-sg-jenkins-perf-use1