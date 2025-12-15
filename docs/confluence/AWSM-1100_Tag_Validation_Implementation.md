# Tag Validation Implementation for DR Tags

**JIRA:** [AWSM-1100](https://healthedge.atlassian.net/browse/AWSM-1100)  
**Version:** 1.3  
**Date:** December 15, 2025  
**Status:** Ready for Implementation

---

## Executive Summary

This document provides the implementation artifacts for enforcing DR tag compliance across HealthEdge AWS accounts. It includes Tag Policies, Service Control Policies (SCPs), and AWS Config rules to validate the DR tagging taxonomy aligned with the **Guiding Care DR Implementation** (authoritative source).

**Authoritative Source:** [Guiding Care DR Implementation](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5327028252)

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

## 4. AWS Config Rules for Tag Compliance

Deploy these CloudFormation templates to create AWS Config rules that detect non-compliant resources.

### 4.1 Basic DR Tag Compliance (All EC2)

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: AWS Config rule for basic DR tag compliance

Resources:
  DRTagComplianceRule:
    Type: AWS::Config::ConfigRule
    Properties:
      ConfigRuleName: dr-tag-compliance-basic
      Description: Checks that EC2 instances have dr:enabled tag
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
    Value: !GetAtt DRTagComplianceRule.Arn
```

### 4.2 DR-Enabled Tag Compliance (Custom Rule)

For resources with `dr:enabled=true`, validate that `dr:priority` and `dr:wave` are also present. This requires a custom Config rule since the AWS managed rule doesn't support conditional tag requirements.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Custom AWS Config rule for DR-enabled tag compliance

Resources:
  DREnabledComplianceLambda:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: dr-enabled-tag-compliance
      Runtime: python3.12
      Handler: index.handler
      Role: !GetAtt LambdaExecutionRole.Arn
      Code:
        ZipFile: |
          import boto3
          import json
          
          def handler(event, context):
              config = boto3.client('config')
              invoking_event = json.loads(event['invokingEvent'])
              configuration_item = invoking_event['configurationItem']
              
              # Get tags
              tags = configuration_item.get('tags', {})
              dr_enabled = tags.get('dr:enabled', '').lower()
              
              # If dr:enabled=true, check for dr:priority and dr:wave
              if dr_enabled == 'true':
                  dr_priority = tags.get('dr:priority', '')
                  dr_wave = tags.get('dr:wave', '')
                  
                  if not dr_priority or dr_priority not in ['critical', 'high', 'medium', 'low']:
                      compliance = 'NON_COMPLIANT'
                      annotation = 'Missing or invalid dr:priority tag (required when dr:enabled=true)'
                  elif not dr_wave or dr_wave not in ['1', '2', '3', '4', '5']:
                      compliance = 'NON_COMPLIANT'
                      annotation = 'Missing or invalid dr:wave tag (required when dr:enabled=true)'
                  else:
                      compliance = 'COMPLIANT'
                      annotation = 'All required DR tags present'
              else:
                  compliance = 'COMPLIANT'
                  annotation = 'dr:enabled is not true, additional DR tags not required'
              
              config.put_evaluations(
                  Evaluations=[{
                      'ComplianceResourceType': configuration_item['resourceType'],
                      'ComplianceResourceId': configuration_item['resourceId'],
                      'ComplianceType': compliance,
                      'Annotation': annotation,
                      'OrderingTimestamp': configuration_item['configurationItemCaptureTime']
                  }],
                  ResultToken=event['resultToken']
              )
      Timeout: 60

  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
        - arn:aws:iam::aws:policy/service-role/AWSConfigRulesExecutionRole

  DREnabledComplianceRule:
    Type: AWS::Config::ConfigRule
    Properties:
      ConfigRuleName: dr-enabled-tag-compliance
      Description: Checks that EC2 instances with dr:enabled=true have dr:priority and dr:wave tags
      Scope:
        ComplianceResourceTypes:
          - AWS::EC2::Instance
      Source:
        Owner: CUSTOM_LAMBDA
        SourceIdentifier: !GetAtt DREnabledComplianceLambda.Arn
        SourceDetails:
          - EventSource: aws.config
            MessageType: ConfigurationItemChangeNotification
    DependsOn: LambdaPermission

  LambdaPermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref DREnabledComplianceLambda
      Action: lambda:InvokeFunction
      Principal: config.amazonaws.com
```

---

## 5. Validation Test Cases

### 5.1 Compliant Resource Examples

```bash
# Compliant: Production EC2 with dr:enabled=true (requires dr:priority and dr:wave)
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.medium \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=dr:enabled,Value=true},
    {Key=dr:priority,Value=critical},
    {Key=dr:wave,Value=1},
    {Key=Environment,Value=Production},
    {Key=BusinessUnit,Value=HRP},
    {Key=Owner,Value=team@healthedge.com},
    {Key=Customer,Value=CustomerA}
  ]'
# Result: SUCCESS

# Compliant: Non-production EC2 (dr:enabled=false, no dr:priority/dr:wave required)
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

# Non-compliant: dr:enabled=true but missing dr:priority and dr:wave
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.medium \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=dr:enabled,Value=true},
    {Key=Environment,Value=Production},
    {Key=BusinessUnit,Value=HRP}
  ]'
# Result: NON_COMPLIANT (Config rule) - Missing dr:priority and dr:wave tags

# Non-compliant: Invalid dr:priority value
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.medium \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=dr:enabled,Value=true},
    {Key=dr:priority,Value=urgent},
    {Key=dr:wave,Value=1}
  ]'
# Result: NON_COMPLIANT - Invalid value for 'dr:priority'. Must be 'critical', 'high', 'medium', or 'low'

# Non-compliant: Invalid dr:wave value
aws ec2 run-instances \
  --image-id ami-12345678 \
  --instance-type t3.medium \
  --tag-specifications 'ResourceType=instance,Tags=[
    {Key=dr:enabled,Value=true},
    {Key=dr:priority,Value=critical},
    {Key=dr:wave,Value=6}
  ]'
# Result: NON_COMPLIANT - Invalid value for 'dr:wave'. Must be '1', '2', '3', '4', or '5'
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

### 7.1 DR Tags (from Guiding Care DR Implementation)

| Tag Key | Allowed Values | Required |
|---------|----------------|----------|
| `dr:enabled` | `true`, `false` | Yes (Production EC2) |
| `dr:priority` | `critical`, `high`, `medium`, `low` | Yes (if dr:enabled=true) |
| `dr:wave` | `1`, `2`, `3`, `4`, `5` | Yes (if dr:enabled=true) |
| `dr:recovery-strategy` | `drs`, `eks-dns`, `sql-ag`, `managed-service` | Optional |
| `dr:rto-target` | Integer (minutes) | Optional |
| `dr:rpo-target` | Integer (minutes) | Optional |

**Priority to RTO Mapping:**
- `critical`: 30 minutes RTO
- `high`: 1 hour RTO
- `medium`: 2 hours RTO
- `low`: 4 hours RTO

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

| Document | Location | Author | Date |
|----------|----------|--------|------|
| **Guiding Care DR Implementation** | [Confluence CP1/5327028252](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5327028252) | Chris Falk | December 9, 2025 |

**Key Architecture Elements from Authoritative Source:**
- Tag-driven resource discovery using AWS Resource Explorer
- Customer/Environment scoping for multi-tenant operations
- Wave-based recovery with priority mapping (critical→30min, high→1hr, medium→2hr, low→4hr)
- Recovery strategies: DRS (EC2), EKS-DNS (containers), SQL-AG (databases), managed-service

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
- Updated: December 15, 2025 - Added conditional tag validation for dr:priority/dr:wave (v1.3)
- Author: Cloud Infrastructure Team
- Authoritative Source: Guiding Care DR Implementation (Confluence CP1/5327028252)
