# Decision---Encryption-At-Rest-Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867034138/Decision---Encryption-At-Rest-Design

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:34 AM

---

### Document Lifecycle Status

**Purpose**
-----------

### Decision

Determine if data at rest will be encrypted

This document outlines a strategy for protecting data at rest. Defining data management requirements, implementing secure key management, enforcing access control and enforcing encryption at rest all align to Well-Architected best practices.

AWS KMS provides the following capabilities and benefits:

1. Handles the complexity and security of creating and managing cryptographic keys.
2. Customer managed keys (CMKs) are protected by hardware security modules (HSMs) which are validated by the [FIPS 140-2 Cryptographic Module Validation Program](https://csrc.nist.gov/projects/cryptographic-module-validation-program/Certificate/3139)
3. Uses FIPS approved encryption algorithm - AES-GCM with 256 keys.
4. Uses the encryption context as additional authenticated data (AAD) to support authenticated encryption.
5. Integrated with many AWS services for server-side encryption.
6. Integrates with AWS services encryption clients and AWS Encryption SDK for client-side encryption.
7. Integrates with CloudTrail and CloudWatch to provide auditable logs of key usage for regulatory and compliance activities.
8. Supports direct encryption using CMK for data less than 4KB in size and envelope encryption for larger data sets.
9. Supports granular access control using IAM policies and CMK resource-based policies with keys tagging capability.

**Example Implementation**
--------------------------

#### **Services**

You will use server-side encryption to protect data at rest. AWS KMS will be used as the key management solution. In cases where KMS integration is not natively supported by a service, You will determine the approach based on the data classification model.

You will take a ubiquitous encryption approach to data protection by enabling encryption for all services which natively support KMS encryption. Business justification will have to be provided to be exempt from this rule.

Default encryption will be enabled on S3 buckets and EBS volumes if [supported instance types](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSEncryption.html#EBSEncryption_supported_instances) are used.

KMS keys creation and management

If you do not have any organization policies and compliance requirements which would mandate the use of imported key material, You will be using KMS-generated key material for the CMKs.

* Customer-managed CMKs will be used to encrypt resources such as S3, EBS, and RDS;
* Automatic yearly rotation will be enabled for the CMKs.

KMS CMKs will be associated with an alias (or display name) and a description. To simplify multi-region applications management, applications code promotion through Dev/Test/Prod, and manual key rotation, the following CMK Naming Convention will be used.

|  |  |  |
| --- | --- | --- |
|  | **AWS managed CMKs (default)** | **Customer managed CMK** |
| Convention | alias/aws/{service}  ·       service: S3, EBS, RDS | alias/{name}/{service}-{dataclass}  ·       service: S3, EBS, RDS, CustomAppName  ·       dataclass (optional): Confidential, Internal Use, General |
| Example | alias/aws/lambda | alias/{name}/s3-confidential  alias/{name}/s3  alias/{name}/ebs  alias/{name}/rds  alias/{name}/secrets |

*Note: when creating CMKs using console, prefix “alias/” is automatically appended to the front of the key name. When creating CMKs/Aliases using KMS API/CLI, it is mandatory to include the prefix “alias/”.*

When creating KMS keys for each AWS account, you will consider the following aspects:

1. [KMS Service Limits](https://docs.aws.amazon.com/kms/latest/developerguide/limits.html)
2. Cost
3. Management complexity
4. Blast radius:

   1. Per Business Unit
   2. Per Class of Data
   3. Per Environment: Production / Development / etc.
   4. Per Application
   5. Per Service

As a general guidance, to best control the blast radius around individual keys, You should create one CMK per environment per service. That will isolate key compromise to a single service and environment. Additional CMKs can be created if multiple applications are deployed within a single account with different data protection requirements and data class.

KMS keys governance (Customer managed CMK)

Account owners will be responsible for defining policies for managing keys in their accounts with a strong recommendation to follow a principle of least privilege and separation of duties. The following template can be used to define CMK Administrators (who will be managing CMKs) and CMK Users (who will be performing cryptographical operations) within each account. CMK Administrators and CMK Users are represented by IAM Roles deployed in the accounts.

| **CMK** | **CMK Administrator** | **CMK User** |
| --- | --- | --- |
| {name}/s3 | <Namespace>-role-saml-poweruser | <EC2 instances/application roles> |
| {name}/ebs | <Namespace>-role-saml-poweruser | <Namespace>-role-saml-poweruser  <Namespace>-role-saml-securityresponse |
| {name}/rds | <Namespace>-role-saml-poweruser | <Namespace>-role-saml-poweruser  <Namespace>-role-saml-securityresponse |
| {name}/secrets  \\*Secrets Manager | <Namespace>-role-saml-poweruser | <EC2 instances/application roles> |

CMK key policy will be utilized to control access to the CMKs to allow for better access control and ease of auditing. Least privileges concept will be followed by limiting permissions based on the keys usage requirements. In addition to the above strategy, it is a Well-Architected best practice to keep users away from directly accessing sensitive data. For example, providing dashboards instead of direct access to a data store, and provide tools to indirectly manage the data.

Encryption Guardrails

You will enable a set of Config Rules to detect unencrypted resources and CloudWatch Alarms to monitor the lifecycle of the keys. The implementation details can be found here (link to Detective Controls page)

**Implementation Strategy**
---------------------------

### Decision

Document the customer's Encryption at Rest strategy.

| **CMK** | **CMK Administrator** | **CMK User** |
| --- | --- | --- |
|  |  |  |
|  |  |  |
|  |  |  |
|  |  |  |