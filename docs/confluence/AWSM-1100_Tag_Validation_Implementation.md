# Tag Validation Implementation for DR Tags

**JIRA:** [AWSM-1100](https://healthedge.atlassian.net/browse/AWSM-1100)  
**Version:** 1.0  
**Date:** December 15, 2025  
**Status:** Ready for Implementation

---

## Executive Summary

This document provides the implementation artifacts for enforcing DR tag compliance across HealthEdge AWS accounts. It includes Tag Policies, Service Control Policies (SCPs), and AWS Config rules to validate the DR tagging taxonomy defined in [AWSM-1087](https://healthedge.atlassian.net/browse/AWSM-1087).

---

## 1. Tag Policy for DR Tags

Deploy this tag policy at the AWS Organization level to validate DR tag values.

```json
{
  "tags": {
    "dr:enabled": {
      "tag_key": {
        "@@assign": "dr:enabled"
      },
      "tag_value": {
        "@@assign": ["true", "false"]
      },
      "enforced_for": {
        "@@assign": ["ec2:instance"]
      }
    },
    "dr:priority": {
      "tag_key": {
        "@@assign": "dr:priority"
      },
      "tag_value": {
        "@@assign": ["critical", "high", "medium", "low"]
      },
      "enforced_for": {
        "@@assign": ["ec2:instance"]
      }
    },
    "dr:wave": {
      "tag_key": {
        "@@assign": "dr:wave"
      },
      "tag_value": {
        "@@assign": ["1", "2", "3", "4", "5"]
      },
      "enforced_for": {
        "@@assign": ["ec2:instance"]
      }
    },
    "dr:recovery-strategy": {
      "tag_key": {
        "@@assign": "dr:recovery-strategy"
      },
      "tag_value": {
        "@@assign": ["drs", "eks-dns", "sql-ag", "managed-service"]
      },
      "enforced_for": {
        "@@assign": ["ec2:instance"]
      }
    },
    "Environment": {
      "tag_key": {
        "@@assign": "Environment"
      },
      "tag_value": {
        "@@assign": ["Production", "NonProduction", "Development", "Sandbox", "AMSInfrastructure"]
      },
      "enforced_for": {
        "@@assign": ["ec2:instance", "s3:bucket", "rds:db", "lambda:function"]
      }
    }
  }
}
```

---

## 2. SCP for Mandatory DR Tags (Production EC2)

Deploy this SCP to the **Production Workloads OU** to enforce `dr:enabled` tag on EC2 instances.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyEC2WithoutDREnabled",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "Null": {
          "aws:RequestTag/dr:enabled": "true"
        }
      }
    },
    {
      "Sid": "DenyInvalidDREnabled",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances",
        "ec2:CreateTags"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestTag/dr:enabled": ["true", "false"]
        },
        "Null": {
          "aws:RequestTag/dr:enabled": "false"
        }
      }
    }
  ]
}
```

**Error Message When Blocked:**
```
User: arn:aws:iam::123456789012:user/developer is not authorized to perform: 
ec2:RunInstances on resource: arn:aws:ec2:us-east-1:123456789012:instance/* 
with an explicit deny in a service control policy.

Resolution: Add tag 'dr:enabled' with value 'true' or 'false' to your EC2 instance.
```

---

## 3. SCP for Mandatory Business Tags

Deploy this SCP to enforce core business tags on all supported resources.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyEC2WithoutBusinessUnit",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "Null": {
          "aws:RequestTag/BusinessUnit": "true"
        }
      }
    },
    {
      "Sid": "DenyEC2WithoutEnvironment",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "Null": {
          "aws:RequestTag/Environment": "true"
        }
      }
    },
    {
      "Sid": "DenyEC2WithoutOwner",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "Null": {
          "aws:RequestTag/Owner": "true"
        }
      }
    }
  ]
}
```

---

## 4. AWS Config Rule for Tag Compliance

Deploy this CloudFormation template to create an AWS Config rule that detects non-compliant resources.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: AWS Config rule for DR tag compliance

Resources:
  DRTagComplianceRule:
    Type: AWS::Config::ConfigRule
    Properties:
      ConfigRuleName: dr-tag-compliance
      Description: Checks that EC2 instances have required DR tags
      InputParameters:
        tag1Key: dr:enabled
        tag1Value: "true,false"
        tag2Key: Environment
        tag2Value: "Production,NonProduction,Development,Sandbox"
        tag3Key: BusinessUnit
      Scope:
        ComplianceResourceTypes:
          - AWS::EC2::Instance
      Source:
        Owner: AWS
        SourceIdentifier: REQUIRED_TAGS

Outputs:
  ConfigRuleArn:
    Description: ARN of the DR tag compliance Config rule
    Value: !GetAtt DRTagComplianceRule.Arn
```

---

## 5. Validation Test Cases

### 5.1 Compliant Resource Examples

```bash
# Compliant: Production EC2 with all required tags
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.medium \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=dr:enabled,Value=true},
    {Key=Environment,Value=Production},
    {Key=BusinessUnit,Value=HRP},
    {Key=Owner,Value=team@healthedge.com},
    {Key=Customer,Value=CustomerA}
  ]'
# Result: SUCCESS

# Compliant: Non-production EC2 (dr:enabled=false allowed)
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.small \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=dr:enabled,Value=false},
    {Key=Environment,Value=Development},
    {Key=BusinessUnit,Value=GuidingCare},
    {Key=Owner,Value=dev@healthedge.com}
  ]'
# Result: SUCCESS
```

### 5.2 Non-Compliant Resource Examples

```bash
# Non-compliant: Missing dr:enabled tag
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.medium \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=Environment,Value=Production},
    {Key=BusinessUnit,Value=HRP}
  ]'
# Result: DENIED - Missing required tag 'dr:enabled'

# Non-compliant: Invalid dr:enabled value
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.medium \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=dr:enabled,Value=yes},
    {Key=Environment,Value=Production}
  ]'
# Result: DENIED - Invalid value for 'dr:enabled'. Must be 'true' or 'false'

# Non-compliant: Invalid dr:priority value
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.medium \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=dr:enabled,Value=true},
    {Key=dr:priority,Value=urgent}
  ]'
# Result: DENIED - Invalid value for 'dr:priority'. Must be 'critical', 'high', 'medium', or 'low'
```

---

## 6. Deployment Order

| Order | Component | Scope | Behavior |
|-------|-----------|-------|----------|
| 1 | Tag Policies | Organization | Non-blocking, reports only |
| 2 | AWS Config Rules | All accounts | Detects and reports non-compliant resources |
| 3 | SCPs | Production Workloads OU | Blocking - denies non-compliant resource creation |

**Recommended Rollout:**
1. Deploy Tag Policies and Config Rules first
2. Monitor compliance for 2-4 weeks
3. Communicate requirements to teams
4. Deploy SCPs after validation period

---

## 7. Allowed Tag Values Summary

### 7.1 DR Tags

| Tag Key | Allowed Values |
|---------|----------------|
| `dr:enabled` | `true`, `false` |
| `dr:priority` | `critical`, `high`, `medium`, `low` |
| `dr:wave` | `1`, `2`, `3`, `4`, `5` |
| `dr:recovery-strategy` | `drs`, `eks-dns`, `sql-ag`, `managed-service` |
| `dr:rto-target` | Integer (minutes) |
| `dr:rpo-target` | Integer (minutes) |

### 7.2 Environment Tags

| Tag Key | Allowed Values |
|---------|----------------|
| `Environment` | `Production`, `NonProduction`, `Development`, `Sandbox`, `AMSInfrastructure` |

### 7.3 Business Tags

| Tag Key | Allowed Values |
|---------|----------------|
| `BusinessUnit` | `Source`, `HRP`, `GuidingCare`, `Wellframe`, `Security`, `COE`, `Infrastructure`, `REO` |

---

## 8. Current State Analysis

### 8.1 AWS Account Tag Analysis (December 15, 2025)

| Account | Account ID | EC2 Count | DRS Tag | dr:enabled Tag |
|---------|------------|-----------|---------|----------------|
| HRP Production | 538127172524 | 25 | ✅ Yes (24 True, 1 False) | ❌ Not present |
| Guiding Care Production | 835807883308 | 0 (us-east-1) | N/A | N/A |
| Guiding Care NonProduction | 315237946879 | 3 | ❌ Not present | ❌ Not present |

**Migration Required:** HRP Production has 25 EC2 instances using legacy `DRS` tag that need migration to `dr:enabled`.

### 8.2 Target Accounts for SCP Deployment

| Account Name | Account ID | SCP Target |
|--------------|------------|------------|
| Guiding Care Production | 835807883308 | Production Workloads OU |
| HRP Production | 538127172524 | Production Workloads OU |

---

## 9. References

### 9.1 Authoritative Source

| Document | Location |
|----------|----------|
| **Guiding Care DR Implementation** | [Confluence CP1/5327028252](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5327028252) |

### 9.2 Related Confluence Documents

| Document | Page ID |
|----------|---------|
| AWS Tagging Strategy | [4836950067](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4836950067) |
| Tag Types Reference | [4867035088](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867035088) |
| DRS Tags | [4930863374](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4930863374) |

### 9.3 AWS Documentation

- [AWS Organizations Tag Policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_tag-policies.html)
- [AWS Config Required Tags Rule](https://docs.aws.amazon.com/config/latest/developerguide/required-tags.html)
- [Service Control Policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)

### 9.4 Related JIRA

- [AWSM-1087](https://healthedge.atlassian.net/browse/AWSM-1087) - DR Tagging Taxonomy
- [AWSM-1100](https://healthedge.atlassian.net/browse/AWSM-1100) - Tag Validation Implementation (this document)

---

**Document Control:**
- Created: December 15, 2025
- Author: Cloud Infrastructure Team
- Data Sources: Guiding Care DR Implementation (Confluence), AWS Account Tag Analysis
