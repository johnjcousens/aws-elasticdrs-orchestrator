# Cross-Account Role Policy Document

## Overview

This document provides the complete IAM policy required for the cross-account role that enables AWS DRS Orchestration to manage disaster recovery operations across multiple AWS accounts. The hub account assumes this role in spoke accounts to perform DRS operations.

---

## Architecture Pattern

```
Hub Account (DRS Orchestration)
    │
    ├─ Assumes Role ──> Spoke Account 1 (DRS Source Servers)
    ├─ Assumes Role ──> Spoke Account 2 (DRS Source Servers)
    └─ Assumes Role ──> Spoke Account N (DRS Source Servers)
```

---

## Complete IAM Policy

### Policy Name: `DRSOrchestrationCrossAccountPolicy`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DRSCoreOperations",
      "Effect": "Allow",
      "Action": [
        "drs:DescribeSourceServers",
        "drs:DescribeJobs",
        "drs:DescribeJobLogItems",
        "drs:DescribeRecoveryInstances",
        "drs:DescribeRecoverySnapshots",
        "drs:GetLaunchConfiguration",
        "drs:GetReplicationConfiguration",
        "drs:StartRecovery",
        "drs:TerminateRecoveryInstances",
        "drs:UpdateLaunchConfiguration",
        "drs:UpdateReplicationConfiguration",
        "drs:TagResource",
        "drs:UntagResource",
        "drs:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EC2DescribeOperations",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeInstanceStatus",
        "ec2:DescribeVolumes",
        "ec2:DescribeSnapshots",
        "ec2:DescribeImages",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "ec2:DescribeAvailabilityZones",
        "ec2:DescribeLaunchTemplates",
        "ec2:DescribeLaunchTemplateVersions",
        "ec2:DescribeTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EC2LaunchTemplateManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateLaunchTemplate",
        "ec2:CreateLaunchTemplateVersion",
        "ec2:ModifyLaunchTemplate",
        "ec2:DeleteLaunchTemplate",
        "ec2:DeleteLaunchTemplateVersions"
      ],
      "Resource": [
        "arn:aws:ec2:*:*:launch-template/*"
      ],
      "Condition": {
        "StringLike": {
          "aws:RequestTag/ManagedBy": "DRSOrchestration"
        }
      }
    },
    {
      "Sid": "EC2RecoveryInstanceOperations",
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:CreateVolume",
        "ec2:AttachVolume",
        "ec2:CreateTags",
        "ec2:ModifyInstanceAttribute",
        "ec2:ModifyVolume"
      ],
      "Resource": [
        "arn:aws:ec2:*:*:instance/*",
        "arn:aws:ec2:*:*:volume/*",
        "arn:aws:ec2:*:*:network-interface/*",
        "arn:aws:ec2:*:*:security-group/*",
        "arn:aws:ec2:*:*:subnet/*"
      ],
      "Condition": {
        "StringEquals": {
          "ec2:CreateAction": [
            "RunInstances",
            "CreateVolume"
          ]
        }
      }
    },
    {
      "Sid": "IAMPassRoleForDRS",
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": [
        "arn:aws:iam::*:role/AWSElasticDisasterRecovery*"
      ],
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": [
            "drs.amazonaws.com",
            "ec2.amazonaws.com"
          ]
        }
      }
    },
    {
      "Sid": "CloudWatchMetricsAndLogs",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EventBridgeCrossAccountEvents",
      "Effect": "Allow",
      "Action": [
        "events:PutEvents"
      ],
      "Resource": [
        "arn:aws:events:*:*:event-bus/drs-orchestration-*"
      ]
    },
    {
      "Sid": "SNSNotifications",
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": [
        "arn:aws:sns:*:*:drs-orchestration-*"
      ]
    }
  ]
}
```

---

## Trust Relationship

### For Spoke Account Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<HUB_ACCOUNT_ID>:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "<UNIQUE_EXTERNAL_ID>"
        }
      }
    }
  ]
}
```

**Replace:**
- `<HUB_ACCOUNT_ID>`: Your hub account ID (e.g., `***REMOVED***`)
- `<UNIQUE_EXTERNAL_ID>`: A unique identifier for security (e.g., `drs-orch-spoke-<ACCOUNT_ID>`)

---

## Hub Account Permissions

### Hub Account Lambda Execution Role

The Lambda functions in the hub account need permission to assume the cross-account role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AssumeRoleInSpokeAccounts",
      "Effect": "Allow",
      "Action": [
        "sts:AssumeRole"
      ],
      "Resource": [
        "arn:aws:iam::*:role/DRSOrchestrationCrossAccountRole"
      ]
    }
  ]
}
```

---

## Policy Breakdown by Function

### 1. DRS Core Operations
**Used by:** All Lambda functions
**Purpose:** Core DRS API operations for orchestration

| Action | Purpose | Used In |
|--------|---------|---------|
| `drs:DescribeSourceServers` | Discover and validate source servers | API Handler, Orchestration |
| `drs:DescribeJobs` | Monitor recovery job status | Orchestration, Execution Poller |
| `drs:DescribeJobLogItems` | Get detailed job events | API Handler, Orchestration |
| `drs:DescribeRecoveryInstances` | Get recovery instance details | API Handler, Orchestration |
| `drs:GetLaunchConfiguration` | Read server launch settings | API Handler, Orchestration |
| `drs:StartRecovery` | Initiate recovery operations | API Handler, Orchestration |
| `drs:TerminateRecoveryInstances` | Clean up recovery instances | API Handler |
| `drs:UpdateLaunchConfiguration` | Apply launch settings | Orchestration |
| `drs:TagResource` | Tag DRS resources | API Handler |

### 2. EC2 Describe Operations
**Used by:** API Handler, Orchestration
**Purpose:** Gather EC2 instance and network information

| Action | Purpose |
|--------|---------|
| `ec2:DescribeInstances` | Get recovery instance details (IP, type, status) |
| `ec2:DescribeInstanceTypes` | Validate instance type availability |
| `ec2:DescribeSecurityGroups` | Validate security group configurations |
| `ec2:DescribeSubnets` | Validate subnet configurations |
| `ec2:DescribeLaunchTemplates` | Read EC2 launch template settings |

### 3. EC2 Launch Template Management
**Used by:** Orchestration
**Purpose:** Manage EC2 launch templates for recovery instances

**Condition:** Only allows operations on templates tagged with `ManagedBy: DRSOrchestration`

### 4. EC2 Recovery Instance Operations
**Used by:** DRS Service (via DRS API)
**Purpose:** DRS creates recovery instances during recovery operations

**Note:** These permissions are used by DRS service when `StartRecovery` is called.

### 5. IAM PassRole
**Used by:** DRS Service
**Purpose:** Allow DRS to pass IAM roles to EC2 instances

**Condition:** Only allows passing roles to DRS and EC2 services.

### 6. CloudWatch Metrics and Logs
**Used by:** All Lambda functions
**Purpose:** Monitoring and logging

### 7. EventBridge Cross-Account Events
**Used by:** Future cross-account monitoring feature
**Purpose:** Send events to central monitoring account

### 8. SNS Notifications
**Used by:** Future notification feature
**Purpose:** Send alerts to central notification topics

---

## Deployment Instructions

### Step 1: Create Role in Each Spoke Account

```bash
# Set variables
HUB_ACCOUNT_ID="***REMOVED***"
SPOKE_ACCOUNT_ID="<your-spoke-account-id>"
EXTERNAL_ID="drs-orch-spoke-${SPOKE_ACCOUNT_ID}"
ROLE_NAME="DRSOrchestrationCrossAccountRole"

# Create trust policy file
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${HUB_ACCOUNT_ID}:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "${EXTERNAL_ID}"
        }
      }
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name ${ROLE_NAME} \
  --assume-role-policy-document file://trust-policy.json \
  --description "Cross-account role for DRS Orchestration hub account"

# Attach the policy (create policy first from JSON above)
aws iam attach-role-policy \
  --role-name ${ROLE_NAME} \
  --policy-arn arn:aws:iam::${SPOKE_ACCOUNT_ID}:policy/DRSOrchestrationCrossAccountPolicy
```

### Step 2: Register Spoke Account in Hub

Use the API to register the spoke account:

```bash
# Get JWT token
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id ***REMOVED*** \
  --client-id ***REMOVED*** \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=***REMOVED***,PASSWORD=***REMOVED*** \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Register spoke account
curl -X POST "https://***REMOVED***.execute-api.us-east-1.amazonaws.com/test/accounts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "accountId": "'${SPOKE_ACCOUNT_ID}'",
    "accountName": "Production East",
    "region": "us-east-1",
    "roleArn": "arn:aws:iam::'${SPOKE_ACCOUNT_ID}':role/'${ROLE_NAME}'",
    "externalId": "'${EXTERNAL_ID}'"
  }'
```

### Step 3: Validate Cross-Account Access

```bash
# Test assume role
aws sts assume-role \
  --role-arn "arn:aws:iam::${SPOKE_ACCOUNT_ID}:role/${ROLE_NAME}" \
  --role-session-name "test-session" \
  --external-id "${EXTERNAL_ID}"

# If successful, test DRS access
aws drs describe-source-servers \
  --region us-east-1 \
  --profile spoke-account
```

---

## Security Best Practices

### 1. Use External ID
Always use a unique External ID for each spoke account to prevent confused deputy attacks.

### 2. Least Privilege
The policy includes only the minimum permissions required for DRS orchestration operations.

### 3. Condition Keys
- Launch template operations restricted to resources tagged with `ManagedBy: DRSOrchestration`
- IAM PassRole restricted to DRS and EC2 services only

### 4. Resource Restrictions
- Launch template operations: Only on launch templates
- SNS/EventBridge: Only on DRS orchestration resources

### 5. Audit Trail
All cross-account operations are logged in CloudTrail in both hub and spoke accounts.

---

## Troubleshooting

### Common Issues

#### 1. Access Denied on AssumeRole
**Symptom:** `AccessDenied` when hub account tries to assume role
**Solution:** 
- Verify trust relationship includes correct hub account ID
- Verify External ID matches
- Check hub account has `sts:AssumeRole` permission

#### 2. Access Denied on DRS Operations
**Symptom:** `AccessDenied` when calling DRS APIs
**Solution:**
- Verify policy is attached to role
- Check DRS service is initialized in spoke account
- Verify region is correct

#### 3. Access Denied on EC2 Operations
**Symptom:** `AccessDenied` when DRS tries to create recovery instances
**Solution:**
- Verify EC2 permissions in policy
- Check IAM PassRole permissions
- Verify DRS service role exists in spoke account

#### 4. Launch Template Creation Fails
**Symptom:** Cannot create launch templates
**Solution:**
- Verify launch template has `ManagedBy: DRSOrchestration` tag
- Check EC2 launch template permissions

---

## Monitoring and Compliance

### CloudTrail Events to Monitor

```json
{
  "eventName": "AssumeRole",
  "requestParameters": {
    "roleArn": "arn:aws:iam::*:role/DRSOrchestrationCrossAccountRole"
  }
}
```

### Key Metrics

- **Cross-Account API Calls**: Count of successful/failed assume role operations
- **DRS Operations**: Count of DRS API calls per spoke account
- **Error Rate**: Percentage of failed cross-account operations

### Compliance Checks

- [ ] External ID is unique per spoke account
- [ ] Trust relationship includes only hub account
- [ ] Policy follows least privilege principle
- [ ] CloudTrail logging enabled in all accounts
- [ ] Regular access reviews performed

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-14 | Initial comprehensive policy document |

---

## References

- [AWS DRS API Reference](https://docs.aws.amazon.com/drs/latest/APIReference/)
- [Cross-Account Features Implementation](./CROSS_ACCOUNT_FEATURES.md)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Preventing Confused Deputy](https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html)
