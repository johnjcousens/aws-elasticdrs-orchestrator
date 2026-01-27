# HealthEdge AWS Tag Validation Implementation

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5351899236/HealthEdge%20AWS%20Tag%20Validation%20Implementation

**Created by:** John Cousens on December 15, 2025  
**Last modified by:** John Cousens on December 15, 2025 at 08:07 PM

---

---

Executive Summary
-----------------

This document provides the implementation artifacts for enforcing tag compliance across HealthEdge AWS accounts, including existing organizational tags and new DR (Disaster Recovery) tags.

All recommendations follow the **exact patterns** already deployed in the HealthEdge AWS Organization to ensure consistency.

**Authoritative Sources:**

* Tag Management Design - Existing tag standards
* Guiding Care DR Implementation - DR tag taxonomy

---

1. Tag Policy Updates for DR Tags
---------------------------------

### 1.1 Current Production Tag Policy (tagPolicy\_Production - p-95ea3nu1e8)

The existing Production Tag Policy already enforces 16 tags. Add the following DR tags to the **existing policy** using the same pattern:

**Tags to ADD to tagPolicy\_Production:**


```json
{
  "dr:enabled": {
    "tag_key": {
      "@@assign": "dr:enabled"
    },
    "tag_value": {
      "@@assign": [
        "true",
        "false"
      ]
    },
    "enforced_for": {
      "@@assign": [
        "ec2:instance"
      ]
    }
  },
  "dr:priority": {
    "tag_key": {
      "@@assign": "dr:priority"
    },
    "tag_value": {
      "@@assign": [
        "critical",
        "high",
        "medium",
        "low"
      ]
    },
    "enforced_for": {
      "@@assign": [
        "ec2:instance"
      ]
    }
  },
  "dr:wave": {
    "tag_key": {
      "@@assign": "dr:wave"
    },
    "tag_value": {
      "@@assign": [
        "1",
        "2",
        "3",
        "4",
        "5"
      ]
    },
    "enforced_for": {
      "@@assign": [
        "ec2:instance"
      ]
    }
  },
  "dr:recovery-strategy": {
    "tag_key": {
      "@@assign": "dr:recovery-strategy"
    },
    "tag_value": {
      "@@assign": [
        "drs",
        "eks-dns",
        "sql-ag",
        "managed-service"
      ]
    },
    "enforced_for": {
      "@@assign": [
        "ec2:instance"
      ]
    }
  }
}
```


### 1.2 Update to Existing Backup Tag

Update the existing `Backup` tag to add `1h14d` value:


```json
"Backup": {
  "tag_key": {
    "@@assign": "Backup"
  },
  "tag_value": {
    "@@assign": [
      "1d14d",
      "1h14d",
      "NotRequired"
    ]
  },
  "enforced_for": {
    "@@assign": [
      "ec2:instance",
      "fsx:file-system",
      "s3:bucket"
    ]
  }
}
```


### 1.3 Update to Existing BusinessUnit Tag

Update the existing `BusinessUnit` tag to add `Infrastructure` and `REO` values:


```json
"BusinessUnit": {
  "tag_key": {
    "@@assign": "BusinessUnit"
  },
  "tag_value": {
    "@@assign": [
      "Source",
      "HRP",
      "GuidingCare",
      "Wellframe",
      "Security",
      "COE",
      "Infrastructure",
      "REO"
    ]
  },
  "enforced_for": {
    "@@assign": [
      "ec2:instance",
      "s3:bucket",
      "apigateway:restapis",
      "eks:cluster",
      "ecr:repository",
      "elasticloadbalancing:loadbalancer",
      "fsx:file-system",
      "lambda:function"
    ]
  }
}
```


---

2. SCP Updates for DR Tags
--------------------------

### 2.1 Add to Existing scPolicy\_Production\_1 (p-ypjuif0o)

Add the following statement to the **existing SCP** using the same pattern (one statement per tag, EC2-only for DR tags):

**Statement to ADD for dr:enabled enforcement:**


```json
{
  "Effect": "Deny",
  "Action": [
    "ec2:RunInstances"
  ],
  "Resource": [
    "arn:aws:ec2:*:*:instance/*"
  ],
  "Condition": {
    "Null": {
      "aws:RequestTag/dr:enabled": "true"
    }
  }
}
```


> **Note:** This follows the exact pattern used for `DRS` and `Backup` tags in the existing SCP (no ArnNotLike exclusion for infrastructure roles).

### 2.2 Add to Existing scPolicy\_Production\_2 (p-2rt4m5dm)

Add the new DR tags to the tag deletion protection statement:

**Update the existing tag deletion protection statement to include:**


```json
{
  "Effect": "Deny",
  "Action": [
    "ec2:DeleteTags",
    "eks:UntagResource",
    "lambda:UntagResource",
    "s3:PutBucketTagging",
    "tag:UntagResources"
  ],
  "Resource": "*",
  "Condition": {
    "ForAnyValue:StringEquals": {
      "aws:TagKeys": [
        "BusinessUnit",
        "Owner",
        "Environment",
        "DataClassification",
        "ComplianceScope",
        "Customer",
        "Application",
        "Service",
        "Version",
        "Project",
        "CreatedBy",
        "LastReviewed",
        "ExpirationDate",
        "LifecycleStage",
        "DRS",
        "Backup",
        "dr:enabled",
        "dr:priority",
        "dr:wave",
        "dr:recovery-strategy"
      ]
    }
  }
}
```


---

3. Current AWS Implementation Reference
---------------------------------------

### 3.1 Existing Tag Policies

| Policy Name | Policy ID | Environment | Tags Enforced |
| --- | --- | --- | --- |
| tagPolicy\_Production | p-95ea3nu1e8 | Production OU | 16 tags |
| tagPolicy\_NonProduction | p-9548qaa9z6 | NonProduction OU | 16 tags |
| tagPolicy\_Development | p-95uwi3rspm | Development OU | 9 tags |
| tagPolicy\_Sandbox | p-95pwkfqm0z | Sandbox OU | 9 tags |

### 3.2 Existing SCPs

| Policy Name | Policy ID | Purpose |
| --- | --- | --- |
| scPolicy\_Production\_1 | p-ypjuif0o | Deny EC2/Lambda creation without mandatory tags |
| scPolicy\_Production\_2 | p-2rt4m5dm | Deny EKS creation without tags + tag deletion protection |

### 3.3 Pattern Analysis

**Tag Policy Pattern:**

* Uses `@@assign` for all values
* `enforced_for` specifies resource types
* Tags with restricted values include `tag_value` array
* Tags without restricted values (Owner, Customer) omit `tag_value`

**SCP Pattern (scPolicy\_Production\_1):**

* One statement per tag
* Uses `Null` condition with `"true"` to check for missing tags
* EC2/Lambda tags include `ArnNotLike` exclusion for infrastructure roles
* EC2-only tags (DRS, Backup) do NOT include role exclusions
* Resource ARN format: `arn:aws:ec2:*:*:instance/*`

**SCP Pattern (scPolicy\_Production\_2):**

* Single statement for tag deletion protection
* Uses `ForAnyValue:StringEquals` on `aws:TagKeys`
* Covers multiple untag actions across services

---

4. AWS Config Rules for Tag Compliance
--------------------------------------

### 4.1 Current Config Rule Patterns in Use

The HealthEdge AWS accounts use two patterns for Config rules:

| Pattern | Naming Convention | Source | Example |
| --- | --- | --- | --- |
| AMS Managed | `ams-*` or `AMSAlarmManager-*` | CUSTOM\_LAMBDA | `ams-nist-cis-encrypted-volumes` |
| SecurityHub | `securityhub-*` | AWS Managed | `securityhub-ec2-ebs-encryption-by-default` |

**Recommendation:** Deploy DR tag compliance rules using the **AMS custom Lambda pattern** to match existing infrastructure.

### 4.2 DR Tag Compliance Rule (Custom Lambda - AMS Pattern)

Deploy this rule following the existing `AMSAlarmManager-*` pattern:


```yaml
AWSTemplateFormatVersion: 'September 09, 2010'
Description: Custom AWS Config rule for DR tag compliance (AMS pattern)

Resources:
  DRTagComplianceLambda:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: AMSDRTagValidation
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
            
              # Skip if not an EC2 instance or deleted
              if configuration_item['resourceType'] != 'AWS::EC2::Instance':
                  return
              if configuration_item['configurationItemStatus'] == 'ResourceDeleted':
                  compliance = 'NOT_APPLICABLE'
                  annotation = 'Resource deleted'
              else:
                  tags = configuration_item.get('tags', {})
                  dr_enabled = tags.get('dr:enabled', '').lower()
                
                  # Check if dr:enabled tag exists
                  if 'dr:enabled' not in tags:
                      compliance = 'NON_COMPLIANT'
                      annotation = 'Missing required tag: dr:enabled'
                  elif dr_enabled not in ['true', 'false']:
                      compliance = 'NON_COMPLIANT'
                      annotation = 'Invalid dr:enabled value. Must be true or false'
                  elif dr_enabled == 'true':
                      # If dr:enabled=true, check for dr:priority and dr:wave
                      dr_priority = tags.get('dr:priority', '')
                      dr_wave = tags.get('dr:wave', '')
                    
                      if not dr_priority:
                          compliance = 'NON_COMPLIANT'
                          annotation = 'Missing dr:priority tag (required when dr:enabled=true)'
                      elif dr_priority not in ['critical', 'high', 'medium', 'low']:
                          compliance = 'NON_COMPLIANT'
                          annotation = 'Invalid dr:priority value. Must be critical, high, medium, or low'
                      elif not dr_wave:
                          compliance = 'NON_COMPLIANT'
                          annotation = 'Missing dr:wave tag (required when dr:enabled=true)'
                      elif dr_wave not in ['1', '2', '3', '4', '5']:
                          compliance = 'NON_COMPLIANT'
                          annotation = 'Invalid dr:wave value. Must be 1, 2, 3, 4, or 5'
                      else:
                          compliance = 'COMPLIANT'
                          annotation = 'All required DR tags present and valid'
                  else:
                      compliance = 'COMPLIANT'
                      annotation = 'dr:enabled=false, additional DR tags not required'
            
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
        Version: 'October 17, 2012'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
        - arn:aws:iam::aws:policy/service-role/AWSConfigRulesExecutionRole

  DRTagComplianceRule:
    Type: AWS::Config::ConfigRule
    Properties:
      ConfigRuleName: AMSDRTagValidation-EC2Instance
      Description: Config rule to evaluate if EC2 instances have required DR tags (dr:enabled, dr:priority, dr:wave)
      Scope:
        ComplianceResourceTypes:
          - AWS::EC2::Instance
      Source:
        Owner: CUSTOM_LAMBDA
        SourceIdentifier: !GetAtt DRTagComplianceLambda.Arn
        SourceDetails:
          - EventSource: aws.config
            MessageType: ConfigurationItemChangeNotification
          - EventSource: aws.config
            MessageType: OversizedConfigurationItemChangeNotification
    DependsOn: LambdaPermission

  LambdaPermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref DRTagComplianceLambda
      Action: lambda:InvokeFunction
      Principal: config.amazonaws.com

Outputs:
  ConfigRuleArn:
    Value: !GetAtt DRTagComplianceRule.Arn
  LambdaArn:
    Value: !GetAtt DRTagComplianceLambda.Arn
```


### 4.3 Naming Convention Alignment

| Component | Naming Pattern | Example |
| --- | --- | --- |
| Lambda Function | `AMSDRTagValidation` | Matches `AMSAlarmManagerValidation` |
| Config Rule | `AMSDRTagValidation-{ResourceType}` | Matches `AMSAlarmManager-EC2Instance` |

### 4.4 Deployment Target Accounts

Deploy to all Production accounts:

* HRP Production (538127172524)
* Guiding Care Production (835807883308)

---

5. Validation Test Cases
------------------------

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

6. Deployment Order
-------------------

| Order | Component | Scope | Behavior |
| --- | --- | --- | --- |
| 1 | Tag Policies | Organization | Non-blocking, reports only |
| 2 | AWS Config Rules | All accounts | Detects and reports non-compliant resources |
| 3 | SCPs | Production Workloads OU | Blocking - denies non-compliant resource creation |

**Recommended Rollout:**

1. Deploy Tag Policies and Config Rules first
2. Monitor compliance for 2-4 weeks
3. Communicate requirements to teams
4. Deploy SCPs after validation period

---

7. Allowed Tag Values Summary
-----------------------------

### 7.1 DR Tags (from Guiding Care DR Implementation)

| Tag Key | Allowed Values | Required |
| --- | --- | --- |
| `dr:enabled` | `true`, `false` | Yes (Production EC2) |
| `dr:priority` | `critical`, `high`, `medium`, `low` | Yes (if dr:enabled=true) |
| `dr:wave` | `1`, `2`, `3`, `4`, `5` | Yes (if dr:enabled=true) |
| `dr:recovery-strategy` | `drs`, `eks-dns`, `sql-ag`, `managed-service` | Optional |
| `dr:rto-target` | Integer (minutes) | Optional |
| `dr:rpo-target` | Integer (minutes) | Optional |

**Priority to RTO Mapping:**

* `critical`: 30 minutes RTO
* `high`: 1 hour RTO
* `medium`: 2 hours RTO
* `low`: 4 hours RTO

### 7.2 Business & Environment Tags

| Tag Key | Allowed Values |
| --- | --- |
| `BusinessUnit` | `Source`, `HRP`, `GuidingCare`, `Wellframe`, `Security`, `COE`, `Infrastructure`, `REO` |
| `Environment` | `Production`, `NonProduction`, `Development`, `Sandbox`, `AMSInfrastructure` |

### 7.3 Data Classification Tags

| Tag Key | Allowed Values |
| --- | --- |
| `DataClassification` | `PHI`, `PII`, `Clear`, `Internal`, `Confidential` |
| `ComplianceScope` | `HIPAA`, `SOC2`, `HITRUST`, `AllThree`, `None` |

### 7.4 Technical Tags

| Tag Key | Allowed Values |
| --- | --- |
| `Backup` | `1d14d`, `1h14d`, `NotRequired` |
| `LifecycleStage` | `Active`, `Deprecated`, `Decommissioned` |

> **Note:** For complete tag reference, see [AWSM-1087 - HealthEdge AWS Tagging Strategy with DR Integration](https://healthedge.atlassian.net/browse/AWSM-1087)

---

8. Current State Analysis
-------------------------

### 8.1 AWS Account Tag Analysis (December 15, 2025)

| Account | Account ID | EC2 Count | DRS Tag | dr:enabled Tag |
| --- | --- | --- | --- | --- |
| HRP Production | 538127172524 | 25 | ✅ Yes (24 True, 1 False) | ❌ Not present |
| Guiding Care Production | 835807883308 | 0 (us-east-1) | N/A | N/A |
| Guiding Care NonProduction | 315237946879 | 3 | ❌ Not present | ❌ Not present |

**Migration Required:** HRP Production has 25 EC2 instances using legacy `DRS` tag that need migration to `dr:enabled`.

### 8.2 Target Accounts for SCP Deployment

| Account Name | Account ID | SCP Target |
| --- | --- | --- |
| Guiding Care Production | 835807883308 | Production Workloads OU |
| HRP Production | 538127172524 | Production Workloads OU |

---

9. References
-------------

### 9.1 Authoritative Source

| Document | Location | Author | Date |
| --- | --- | --- | --- |
| **Guiding Care DR Implementation** | Confluence | Chris Falk | December 9, 2025 |

**Key Architecture Elements from Authoritative Source:**

* Tag-driven resource discovery using AWS Resource Explorer
* Customer/Environment scoping for multi-tenant operations
* Wave-based recovery with priority mapping (critical→30min, high→1hr, medium→2hr, low→4hr)
* Recovery strategies: DRS (EC2), EKS-DNS (containers), SQL-AG (databases), managed-service

### 9.2 Related Confluence Documents

| Document | Confluence Link |
| --- | --- |
| AWS Tagging Strategy | Confluence |
| Tag Management Design | Confluence |
| Cloudscape Tagging Methodology | Confluence |
| Tag Management Discovery & Analysis | Confluence |
| Tag Management with AWS Organizations | Confluence |
| Business Continuity & Disaster Recovery | Confluence |
| Configuration Management | Confluence |
| Guiding Care: FSx NetApp ONTAP Implementation Guide | Confluence |

### 9.3 AWS Documentation

* [AWS Organizations Tag Policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_tag-policies.html)
* [AWS Config Required Tags Rule](https://docs.aws.amazon.com/config/latest/developerguide/required-tags.html)
* [Service Control Policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)