# Encryption in Transit Validation and Verification Guide for HealthEdge and AWS Services

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5388632067/Encryption%20in%20Transit%20Validation%20and%20Verification%20Guide%20for%20HealthEdge%20and%20AWS%20Services

**Created by:** Alex Dixon on December 23, 2025  
**Last modified by:** Alex Dixon on January 06, 2026 at 03:51 PM

---

**Encryption In Transit for DR and Replication**
================================================

**Implementation and Verification Guide**

---

**1. Objective**
----------------

This document describes **how to implement and verify encryption in transit** for disaster recovery (DR), replication, and application communications within HealthEdge environments.

The goal is to ensure that all data transmitted between systems is:

* Encrypted using **TLS 1.2 or higher**
* Correctly configured at infrastructure and service boundaries
* Verifiable through **configuration inspection and service behavior**
* Clearly documented with defined responsibility boundaries

This guide is intended for **security engineers, platform engineers, and reviewers** responsible for validating encryption controls.

---

**2. Scope**
------------

This guide applies to:

* DR orchestration and control-plane communications
* Database replication traffic
* AWS Elastic Disaster Recovery (DRS)
* Application traffic through AWS load balancers
* API Gateway–managed APIs
* Certificate management for TLS termination
* External or non-AWS APIs used by HealthEdge systems

Out of scope:

* Client-side or application-level cryptography
* Cipher suite tuning beyond minimum TLS standards
* PKI design decisions beyond certificate usage

---

**3. Guiding Principles**
-------------------------

Encryption in transit implementation and validation follows these principles:

1. **TLS 1.2+ is the baseline**

   Any protocol below this standard is non-compliant.
2. **Encryption responsibility varies by service**

   Some services enforce encryption automatically; others require explicit configuration.
3. **Verification must be configuration-based or design-based**

   Controls are validated either by inspecting configuration or by relying on AWS service guarantees.
4. **Certificates are part of the control**

   Transport encryption is incomplete without valid, managed certificates.

---

**4. Identify Communication Paths**
-----------------------------------

Before validating encryption, identify all relevant communication paths:

* DR orchestration APIs
* Database replication connections
* DRS replication traffic
* Application ingress and egress
* API Gateway endpoints
* External or non-AWS APIs
* Load balancers to backend services

This inventory step ensures encryption validation is **complete and intentional**.

---

**5. Implementing and Verifying Encryption In Transit**
-------------------------------------------------------

### **5.1 DR Orchestration and AWS Service APIs**

**What This Covers**

* DR orchestration workflows
* AWS service control-plane APIs
* Service-to-service API calls

**How Encryption Is Implemented**

* AWS service APIs are accessed exclusively over HTTPS
* TLS 1.2+ is enforced by AWS service design

**How to Verify**

* Confirm DR orchestration relies on AWS-managed APIs
* Ensure no custom DR control endpoints are exposed over HTTP
* Where configuration is exposed, confirm deprecated TLS versions are not permitted

**What to Document**

* DR orchestration traffic uses AWS-managed APIs
* Encryption in transit is enforced by AWS

---

### **5.2 API Gateway and Application APIs**

**What This Covers**

* APIs exposed through API Gateway
* Application APIs consumed internally or externally

**How Encryption Is Implemented**

* API Gateway endpoints are HTTPS by default
* TLS termination occurs at the API Gateway edge
* Certificates are associated with custom domains where used

**How to Configure**

* Use HTTPS-only endpoints
* Attach valid certificates to custom domains
* Enforce modern TLS security policies

**How to Verify**

* Confirm APIs are not accessible over HTTP
* Validate TLS policy configuration
* Confirm certificates are valid and correctly associated

---

### **5.3 Database Replication Traffic**

**What This Covers**

* Cross-region replication
* Read replicas
* DR database synchronization

**How Encryption Is Implemented**

* AWS database services support TLS for replication traffic
* Encryption in transit must often be explicitly enforced

**How to Configure**

* Enable secure transport settings
* Configure database or cluster parameters to require TLS
* Ensure replication endpoints require encrypted connections

**How to Verify**

* Inspect database and replication configuration
* Review parameter groups or equivalent settings
* Confirm plaintext connections are rejected

**Common Pitfall**

* Assuming storage encryption implies transport encryption (these are independent control

---

### **5.4 Disaster Recovery Replication (AWS Elastic Disaster Recovery)**

**What This Covers**

* Continuous replication from source systems to AWS staging environments

**How Encryption Is Implemented**

* AWS Elastic Disaster Recovery encrypts all replication traffic in transit by default
* TLS 1.2+ is enforced by the service and cannot be disabled

**How to Verify**

* Confirm replication is performed using AWS Elastic Disaster Recovery
* No TLS configuration or protocol inspection is required
* Replication activity can be confirmed through service usage and recovery tests

**What to Document**

* Encryption in transit is guaranteed by AWS service design

---

### **5.5 AWS Elastic Disaster Recovery (DRS) – KMS Key Preparation for Cross-Account and Cross-Region Deployments**

Although DRS encrypts data **in transit by default (TLS 1.2+)**, **proper KMS key preparation** is required to ensure encrypted operation of resources created during replication and recovery.

This section describes how to prepare **LZA-deployed KMS CMKs** for cross-account and cross-region DRS using HealthEdge standards.

---

#### **5.5.1 Why KMS Preparation Matters**

DRS uses KMS keys to encrypt:

* EBS volumes in the **staging area**
* EBS volumes created during **recovery instance launch**

In cross-account and cross-region scenarios:

* CMKs must exist in **each target region**
* Key policies must explicitly allow **cross-account usage**
* Keys must be accessible by **DRS and EC2**

DRS does **not** create or manage CMKs automatically.

---

#### **5.5.2 LZA KMS Key Requirements**

For each region participating in DRS:

* A **customer-managed CMK** must exist
* The key must be:

  + Region-local
  + Enabled
  + Provisioned via Landing Zone Accelerator (LZA)
* Automatic key rotation should be enabled where supported

Each region uses its **own CMK**.

---

#### **5.5.3 Cross-Account Key Policy Configuration**

When DRS operates across accounts, the KMS key policy in the **target account** must allow:

* The DRS service
* The source account (if applicable)
* Required AWS services that create encrypted resources (e.g., EC2)

Policies should:

* Follow least-privilege principles
* Avoid wildcard principals
* Be consistent across regions

---

#### **5.5.4 Example KMS Key Policy for Cross-Account, Cross-Region DRS**

The following example illustrates a **production-grade CMK policy** suitable for DRS in a HealthEdge environment. This is only a template and can be scoped to separation of duties if roles are used for certain actions.


```json
{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Sid": "AllowRootAccountAdministration",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::DR_ACCOUNT_ID:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "AllowDRSServiceUsage",
      "Effect": "Allow",
      "Principal": {
        "Service": "drs.amazonaws.com"
      },
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": "ec2.DR_REGION.amazonaws.com"
        }
      }
    },
    {
      "Sid": "AllowSourceAccountUsageForDRS",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::SOURCE_ACCOUNT_ID:root"
      },
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ],
      "Resource": "*"
    }
  ]
}
```


Policies will also need to be attached to the IAM Roles in the Destination accounts and regions.


```json
{
    "Sid": "AllowUseOfKeyInSourceAccount",
    "Effect": "Allow",
    "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
    ],
    "Resource": "arn:aws:kms:<Source_Region>:<Source_Account_ID>:key/<Key_ID>"
}
```


---

#### **5.5.5 Validation Steps**

To validate KMS readiness:

* Confirm LZA CMKs exist in all required regions
* Review key policies for cross-account access
* Perform a DRS test recovery
* Inspect EBS volumes created during staging and recovery
* Confirm the correct regional CMK is referenced

---

### **5.6 AWS Certificate Management**

**What This Covers**

* Certificates used for TLS termination in AWS
* ALB, NLB (TLS), and API Gateway custom domains

**How Certificates Are Managed**

* Certificates are issued or imported into AWS
* Certificates are attached to HTTPS or TLS endpoints
* Renewal and rotation must be planned and monitored

**How to Verify**

* Confirm certificates are:

  + Present
  + Valid and not expired
  + Correctly associated with endpoints
* Confirm TLS 1.2+ policies are enforced

**What to Document**

* Certificate ownership
* Renewal and rotation process
* Monitoring or alerting approach

---

### **5.7 External and Non-AWS APIs**

**What This Covers**

* Partner APIs
* On-premises services
* Third-party platforms

**Responsibility**

* Encryption in transit for these endpoints is a **HealthEdge responsibility**

**How to Verify**

* Architecture review
* Application configuration review
* Endpoint testing where appropriate

**What to Document**

* External endpoints
* Trust boundaries
* Validation approach outside AWS-native controls

---

**6. Validation Checklist**
---------------------------

* DR orchestration uses HTTPS-only APIs
* API Gateway endpoints enforce TLS 1.2+
* Database replication uses encrypted transport
* DRS replication confirmed and documented
* LZA CMKs prepared for cross-account DR
* Load balancers use HTTPS or TLS listeners only
* Certificates are valid and documented
* External APIs reviewed and accounted for

---

**7. Documentation Requirements**
---------------------------------

Final documentation must include:

* Identified communication paths
* Encryption enforcement points
* TLS and certificate configuration
* KMS readiness for DR
* External dependency responsibilities

---

**8. Review and Approval**
--------------------------

* **Security Review** – Confirms encryption coverage and standards
* **Architecture Review** – Confirms traffic flows and boundaries
* **Operations Review** – Confirms maintainability

Approval indicates encryption in transit is **implemented, verifiable, and documented**.

---