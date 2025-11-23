# AWS DRS Orchestration - Cross-Account Access Implementation Guide
## Step-by-Step Configuration for Multi-Account Disaster Recovery

---

## Notices

This document is provided for informational purposes only. It represents AWS's current product offerings and practices as of the date of issue of this document, which are subject to change without notice. Customers are responsible for making their own independent assessment of the information in this document and any use of AWS's products or services, each of which is provided "as is" without warranty of any kind, whether express or implied. This document does not create any warranties, representations, contractual commitments, conditions or assurances from AWS, its affiliates, suppliers or licensors. The responsibilities and liabilities of AWS to its customers are controlled by AWS agreements, and this document is not part of, nor does it modify, any agreement between AWS and its customers.

© 2025 Amazon Web Services, Inc. or its affiliates. All rights reserved.

---

## Abstract

This document provides step-by-step implementation guidance for configuring cross-account access in the AWS DRS Orchestration Solution, enabling centralized disaster recovery management across multiple AWS accounts. The methodology encompasses complete IAM role creation procedures, trust relationship configuration, Lambda function modifications, and end-to-end testing protocols. This document delivers production-ready IAM policy templates, CloudFormation code examples, and troubleshooting procedures for implementing hub-and-spoke disaster recovery architecture.

Target audience includes AWS architects, DevOps engineers, security engineers, and disaster recovery specialists who need to implement centralized DR orchestration across AWS Organizations or multiple standalone accounts. The analysis reveals implementation patterns for single-account expansion, multi-account organization deployment, and mixed deployment scenarios combining same-account and cross-account configurations.

---

## Introduction

When you deploy disaster recovery solutions across multiple AWS accounts, you face critical architectural decisions about cross-account access patterns, security controls, and operational complexity. The AWS DRS Orchestration Solution addresses these challenges through AWS Security Token Service (STS) AssumeRole patterns, enabling a centralized hub account to orchestrate disaster recovery operations across multiple spoke accounts while maintaining security boundaries and least-privilege access.

You need to understand the complete cross-account access implementation including IAM role creation in both hub and spoke accounts, trust relationship configuration with security conditions, Lambda function modifications for role assumption, and Protection Group configuration for cross-account server management. This document provides that understanding through detailed step-by-step procedures, complete IAM policy documents with inline explanations, and validation scripts to verify correct implementation.

The document structure guides you through prerequisites, hub account configuration, spoke account setup for each target account, Lambda code modifications, Protection Group configuration, and comprehensive testing procedures. You'll find complete IAM policies ready for production use, CloudFormation template examples for automated deployment, and troubleshooting guidance for common configuration errors. Security best practices section covers external ID usage, condition keys for enhanced security, and audit logging for cross-account operations.

Your success criteria include establishing functional cross-account access with least-privilege permissions, validating DRS source server discovery across accounts, executing test recovery operations, and confirming comprehensive audit trail in CloudTrail logs.

---

# Executive Summary

This implementation guide establishes centralized disaster recovery orchestration across multiple AWS accounts through the hub-and-spoke cross-account access pattern. The framework addresses multi-account DR requirements: centralized management, security isolation, least-privilege access, and operational simplicity while maintaining account autonomy.

**Key Technical Value:** The hub-and-spoke architecture deploys the DRS Orchestration Solution in a single central account while enabling disaster recovery operations across unlimited spoke accounts through STS AssumeRole. This eliminates duplicate infrastructure deployment, reduces operational complexity, and provides single-pane-of-glass visibility across all disaster recovery operations. The implementation uses AWS-native IAM roles with ExternalId conditions, resource-level permissions, and comprehensive CloudTrail auditing, ensuring enterprise-grade security without custom authentication systems.

**Operational Benefits:** Centralized deployment means you deploy and maintain the DRS Orchestration Solution once in the hub account while managing disaster recovery for dozens or hundreds of spoke accounts. Role assumption happens automatically through Lambda function code with no manual credential management or rotation. Each spoke account maintains complete control over what the hub can access through IAM policies. The architecture supports gradual rollout, enabling you to add spoke accounts incrementally without impacting existing operations. CloudWatch provides unified monitoring across all accounts from the hub account console.

**Implementation Success:** The guide provides complete IAM policy templates for both hub and spoke accounts with inline explanations of every permission. Step-by-step procedures cover IAM role creation via console and CLI, trust relationship configuration with ExternalId generation, Lambda function modifications (25 lines of code), and Protection Group configuration updates. Validation procedures include DRS server discovery testing, cross-account recovery simulation, and CloudTrail audit verification. Security controls include external IDs for anti-confused deputy protection, condition keys restricting role usage, and principle of least privilege with resource-level ARNs.

This framework positions organizations to deploy enterprise disaster recovery automation with centralized management, distributed execution, and comprehensive security controls meeting compliance requirements for financial services, healthcare, and government sectors.

**Key Features:**
	- **Hub-and-Spoke Architecture**: Single central orchestration account managing DR across unlimited spoke accounts
	- **STS AssumeRole Pattern**: Native AWS cross-account access with automatic credential management
	- **Least-Privilege IAM**: Resource-level permissions with service-specific access controls
	- **ExternalId Security**: Anti-confused deputy attack protection with unique identifiers
	- **Comprehensive Auditing**: CloudTrail logging of all cross-account operations

**Key Deliverables:**
	- **Complete IAM Policies**: Production-ready role policies for hub and spoke accounts with inline documentation
	- **Step-by-Step Procedures**: Console and CLI instructions for role creation and trust configuration
	- **Lambda Code Examples**: Modified Python code for cross-account DRS API calls (25 lines)
	- **Validation Scripts**: Testing procedures to verify correct cross-account access
	- **Security Best Practices**: External ID generation, condition keys, audit logging, and compliance guidance

---

## Architecture Overview

### Hub-and-Spoke Pattern

**Centralized Hub Account:**
	- **Purpose**: Hosts the DRS Orchestration Solution (all CloudFormation stacks)
	- **Components**: API Gateway, Lambda functions, DynamoDB tables, Step Functions, Cognito, CloudFront/S3
	- **Outbound Access**: Assumes roles in spoke accounts to call DRS APIs
	- **Data Storage**: Protection Groups store spoke account IDs and role ARNs

**Distributed Spoke Accounts:**
	- **Purpose**: Host DRS source servers and recovery infrastructure
	- **Components**: DRS source servers, recovery EC2 instances, DRS service
	- **Inbound Access**: Trust hub account to assume DRS orchestration role
	- **Permissions**: Grant hub account access to DRS, EC2, SSM APIs

### Cross-Account Access Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                        HUB ACCOUNT                                  │
│                      (777788889999)                                 │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  DRS Orchestration Solution                                  │  │
│  │                                                                │  │
│  │  [API Gateway] → [Lambda] → [Step Functions]                 │  │
│  │       ↓              ↓                                         │  │
│  │  [DynamoDB]    [Assume Role]                                  │  │
│  │   (stores       (STS:AssumeRole)                              │  │
│  │    spoke          ↓                                            │  │
│  │    account     [Temporary                                      │  │
│  │    roles)       Credentials]                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           ↓                                          │
└───────────────────────────┼──────────────────────────────────────┘
                            │ AssumeRole
                            │ (with ExternalId)
                            ↓
┌────────────────────────────────────────────────────────────────────┐
│                      SPOKE ACCOUNT 1                                │
│                      (123456789012)                                 │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  IAM Role: DRSOrchestrationCrossAccountRole                  │  │
│  │                                                                │  │
│  │  Trust Policy:                                                 │  │
│  │  - Principal: arn:aws:iam::777788889999:root                  │  │
│  │  - Condition: ExternalId = "unique-id-12345"                  │  │
│  │                                                                │  │
│  │  Permissions:                                                  │  │
│  │  - drs:DescribeSourceServers                                  │  │
│  │  - drs:StartRecovery                                           │  │
│  │  - ec2:DescribeInstances                                       │  │
│  │  - ssm:SendCommand                                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           ↓                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  DRS Source Servers                                           │  │
│  │  - s-3c1730a9e0771ea14 (EC2AMAZ-4IMB9PN)                     │  │
│  │  - s-3d75cdc0d9a28a725 (EC2AMAZ-RLP9U5V)                     │  │
│  │  - s-3afa164776f93ce4f (EC2AMAZ-H0JBE4J)                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                      SPOKE ACCOUNT 2                                │
│                      (987654321098)                                 │
│                                                                      │
│  [Same pattern repeated]                                            │
└────────────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

**1. Single Direction Trust:**
	- Spoke accounts trust the hub account (not bidirectional)
	- Hub assumes roles in spoke accounts (hub never trusts spokes)
	- Temporary credentials expire after 1 hour (default)

**2. Least Privilege Access:**
	- Hub role can only call specific DRS/EC2/SSM APIs
	- Resource-level ARNs where possible (EC2, SSM)
	- No wildcard permissions except where AWS requires (DRS)

**3. Security Controls:**
	- ExternalId prevents confused deputy attacks
	- Condition keys restrict role usage
	- CloudTrail logs all AssumeRole calls
	- MFA optional for additional security

**4. Operational Simplicity:**
	- No VPC peering or Transit Gateway required
	- No custom credential management
	- Automatic credential rotation (STS)
	- Independent spoke account lifecycle

---

## Prerequisites

### Hub Account Requirements

**1. DRS Orchestration Solution Deployed:**
	- CloudFormation master stack deployed successfully
	- API Gateway endpoint functional
	- Lambda functions operational
	- DynamoDB tables created

**2. IAM Permissions:**
	- Ability to modify Lambda function code
	- Ability to update Lambda execution role policies
	- Access to CloudFormation console or CLI

**3. Information Gathering:**
	- Hub AWS Account ID: `777788889999` (example)
	- Lambda execution role ARN
	- DynamoDB table names

### Spoke Account Requirements

**1. AWS Elastic Disaster Recovery (DRS) Initialized:**
	- DRS service initialized in target region
	- Source servers replicating to AWS
	- Replication subnets configured
	- Staging area settings configured

**2. IAM Permissions:**
	- Ability to create IAM roles
	- Ability to create IAM policies
	- Access to IAM console or CLI

**3. Information Gathering:**
	- Spoke AWS Account ID(s)
	- DRS source server IDs (s-xxxxxxxxx format)
	- Target AWS region for DRS operations

### Security Planning

**1. External ID Generation:**
	- Generate unique External ID per spoke account
	- Use cryptographically secure random string
	- 32-64 characters recommended
	- Store securely (AWS Secrets Manager recommended)

**Example External ID Generation:**
```bash
# Linux/macOS
openssl rand -hex 32

# Output: a1b2c3d4e5f6...7890abcdef (64 characters)

# Alternative: Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**2. Documentation Requirements:**
	- Document spoke account ID → ExternalId mapping
	- Document IAM role ARNs per spoke account
	- Maintain cross-account access inventory
	- Plan for ExternalId rotation (annual recommended)

---

## Hub Account Configuration

### Step 1: Update Lambda Execution Role

The Lambda API handler needs additional permissions to assume roles in spoke accounts.

**Enhanced IAM Policy for Lambda Execution Role:**

**Policy Name**: `DRSOrchestrationLambdaAssumeRolePolicy`

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
                "arn:aws:iam::123456789012:role/DRSOrchestrationCrossAccountRole",
                "arn:aws:iam::987654321098:role/DRSOrchestrationCrossAccountRole"
            ],
            "Condition": {
                "StringEquals": {
                    "sts:ExternalId": [
                        "unique-external-id-for-account-123456789012",
                        "unique-external-id-for-account-987654321098"
                    ]
                }
            }
        }
    ]
}
```

**Instructions to Add Policy:**

**Console Method:**
1. Navigate to IAM Console → Roles
2. Search for `drs-orchestration-lambda-execution-role-{env}`
3. Click on the role name
4. Click "Add permissions" → "Create inline policy"
5. Switch to JSON editor
6. Paste the policy above (update account IDs and External IDs)
7. Click "Review policy"
8. Name: `AssumeRoleCrossAccount`
9. Click "Create policy"

**CLI Method:**
```bash
# Save policy to file: assume-role-policy.json
# Then execute:
aws iam put-role-policy \
    --role-name drs-orchestration-lambda-execution-role-test \
    --policy-name AssumeRoleCrossAccount \
    --policy-document file://assume-role-policy.json
```

### Step 2: Store External IDs Securely

**Option A: AWS Secrets Manager (Recommended)**

```bash
# Create secret for spoke account external IDs
aws secretsmanager create-secret \
    --name drs-orchestration/cross-account/external-ids \
    --description "External IDs for cross-account DRS access" \
    --secret-string '{
        "123456789012": "a1b2c3d4e5f6789...",
        "987654321098": "b2c3d4e5f6789ab..."
    }'

# Grant Lambda access to secret
aws secretsmanager put-resource-policy \
    --secret-id drs-orchestration/cross-account/external-ids \
    --resource-policy '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::777788889999:role/drs-orchestration-lambda-execution-role-test"
            },
            "Action": "secretsmanager:GetSecretValue",
            "Resource": "*"
        }]
    }'
```

**Option B: DynamoDB Attribute (Simple)**

Add `CrossAccountRoleArn` and `CrossAccountExternalId` attributes to Protection Groups table items:

```python
# Example Protection Group item with cross-account config
{
    "GroupId": "uuid-string",
    "GroupName": "Production Web Tier",
    "Region": "us-east-1",
    "AccountId": "123456789012",  # Spoke account ID
    "SourceServerIds": ["s-123", "s-456"],
    "CrossAccountRoleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationCrossAccountRole",
    "CrossAccountExternalId": "unique-external-id-for-account-123456789012"
}
```

### Step 3: Update Lambda Function Code

Modify `lambda/index.py` to support cross-account DRS API calls.

**Add Helper Function (insert after imports):**

```python
def get_cross_account_drs_client(account_id: str, region: str, 
                                  role_arn: str, external_id: str):
    """
    Create DRS client with cross-account credentials
    
    Args:
        account_id: Target AWS account ID
        region: AWS region for DRS operations
        role_arn: IAM role ARN in spoke account
        external_id: External ID for role assumption
    
    Returns:
        boto3 DRS client with assumed role credentials
    """
    sts_client = boto3.client('sts')
    
    # Assume role in spoke account
    response = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName=f'drs-orchestration-{account_id}',
        ExternalId=external_id,
        DurationSeconds=3600  # 1 hour
    )
    
    # Extract temporary credentials
    credentials = response['Credentials']
    
    # Create DRS client with temporary credentials
    drs_client = boto3.client(
        'drs',
        region_name=region,
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    
    return drs_client
```

**Modify `list_source_servers` Function:**

```python
def list_source_servers(region: str, current_pg_id: Optional[str] = None) -> Dict:
    """
    Discover DRS source servers with cross-account support
    """
    try:
        # Check if this is a cross-account request
        # (determined by Protection Group configuration)
        pg_response = protection_groups_table.scan()
        
        # Find if any PGs in this region use cross-account
        cross_account_config = None
        for pg in pg_response.get('Items', []):
            if pg.get('Region') == region and pg.get('CrossAccountRoleArn'):
                cross_account_config = {
                    'account_id': pg.get('AccountId'),
                    'role_arn': pg.get('CrossAccountRoleArn'),
                    'external_id': pg.get('CrossAccountExternalId')
                }
                break
        
        # Create DRS client (same-account or cross-account)
        if cross_account_config:
            print(f"Using cross-account access to {cross_account_config['account_id']}")
            drs_client = get_cross_account_drs_client(
                cross_account_config['account_id'],
                region,
                cross_account_config['role_arn'],
                cross_account_config['external_id']
            )
        else:
            # Same-account access (default)
            drs_client = boto3.client('drs', region_name=region)
        
        # Query DRS (rest of function unchanged)
        servers_response = drs_client.describe_source_servers(maxResults=200)
        # ... existing code continues
        
    except Exception as e:
        print(f"Error listing source servers: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {
            'error': 'INTERNAL_ERROR',
            'message': f'Failed to list source servers: {str(e)}'
        })
```

**Deploy Updated Lambda Function:**

```bash
# Package updated code
cd lambda
zip -r ../api-handler-updated.zip index.py

# Update Lambda function
aws lambda update-function-code \
    --function-name drs-orchestration-api-handler-test \
    --zip-file fileb://../api-handler-updated.zip

# Verify update
aws lambda get-function \
    --function-name drs-orchestration-api-handler-test \
    --query 'Configuration.LastModified'
```

---

## Spoke Account Configuration

### Step 1: Create IAM Role

Create the IAM role that the hub account will assume.

**Role Name**: `DRSOrchestrationCrossAccountRole`

**Trust Policy (Trust Relationship):**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::777788889999:root"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "sts:ExternalId": "unique-external-id-for-this-account"
                }
            }
        }
    ]
}
```

**Key Elements:**
	- **Principal**: Hub account ID (777788889999 in example)
	- **ExternalId**: Unique identifier generated in prerequisites
	- **Condition**: Prevents confused deputy attacks

**Console Method:**

1. Sign in to spoke account
2. Navigate to IAM Console → Roles
3. Click "Create role"
4. Select "AWS account" as trusted entity type
5. Select "Another AWS account"
6. Enter Hub Account ID: `777788889999`
7. Check "Require external ID"
8. Enter External ID: `[your-unique-external-id]`
9. Click "Next"
10. Click "Create policy" (opens new tab)
11. Continue to Step 2 to create the permissions policy
12. Return to role creation, refresh policies, select your new policy
13. Click "Next"
14. Role name: `DRSOrchestrationCrossAccountRole`
15. Description: "Cross-account role for DRS Orchestration in hub account"
16. Click "Create role"

**CLI Method:**

```bash
# Save trust policy to file: trust-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::777788889999:root"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "sts:ExternalId": "unique-external-id-for-this-account"
                }
            }
        }
    ]
}

# Create role
aws iam create-role \
    --role-name DRSOrchestrationCrossAccountRole \
    --assume-role-policy-document file://trust-policy.json \
    --description "Cross-account role for DRS Orchestration"

# Output includes role ARN - save this for hub account configuration
```

### Step 2: Create IAM Permission Policy

Create the permissions policy that defines what the hub account can do.

**Policy Name**: `DRSOrchestrationCrossAccountPermissions`

**Complete IAM Policy:**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DRSSourceServerDiscovery",
            "Effect": "Allow",
            "Action": [
                "drs:DescribeSourceServers",
                "drs:DescribeReplicationConfigurationTemplates",
                "drs:GetReplicationConfiguration"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:RequestedRegion": ["us-east-1", "us-west-2"]
                }
            }
        },
        {
            "Sid": "DRSRecoveryOperations",
            "Effect": "Allow",
            "Action": [
                "drs:StartRecovery",
                "drs:DescribeJobs",
                "drs:DescribeRecoveryInstances",
                "drs:DescribeRecoverySnapshots",
                "drs:TerminateRecoveryInstances",
                "drs:DisconnectRecoveryInstance"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:RequestedRegion": ["us-east-1", "us-west-2"]
                }
            }
        },
        {
            "Sid": "EC2InstanceDiscovery",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceStatus",
                "ec2:DescribeInstanceTypes",
                "ec2:DescribeImages",
                "ec2:DescribeVolumes",
                "ec2:DescribeSnapshots",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeSubnets",
                "ec2:DescribeVpcs",
                "ec2:DescribeLaunchTemplates",
                "ec2:DescribeLaunchTemplateVersions"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:RequestedRegion": ["us-east-1", "us-west-2"]
                }
            }
        },
        {
            "Sid": "SSMCommandExecution",
            "Effect": "Allow",
            "Action": [
                "ssm:SendCommand",
                "ssm:GetCommandInvocation",
                "ssm:ListCommandInvocations",
                "ssm:DescribeInstanceInformation"
            ],
            "Resource": [
                "arn:aws:ssm:*:*:document/AWS-RunShellScript",
                "arn:aws:ssm:*:*:document/AWS-RunPowerShellScript",
                "arn:aws:ec2:*:*:instance/*"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:RequestedRegion": ["us-east-1", "us-west-2"]
                }
            }
        },
        {
            "Sid": "CloudWatchLogsForAuditing",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams"
            ],
            "Resource": "arn:aws:logs:*:*:log-group:/aws/drs/orchestration/*"
        }
    ]
}
```

**Inline Policy Explanations:**

**Statement 1 - DRSSourceServerDiscovery:**
	- **Purpose**: Allow hub to discover DRS source servers in spoke account
	- **Actions**: Read-only DRS operations for server inventory
	- **Condition**: Restrict to specific regions only
	- **Why Needed**: Protection Group creation requires server discovery

**Statement 2 - DRSRecoveryOperations:**
	- **Purpose**: Allow hub to execute disaster recovery operations
	- **Actions**: DRS recovery initiation and monitoring
	- **Condition**: Restrict to specific regions only
	- **Why Needed**: Core disaster recovery execution functionality

**Statement 3 - EC2InstanceDiscovery:**
	- **Purpose**: Allow hub to discover EC2 instances post-recovery
	- **Actions**: Read-only EC2 operations for instance metadata
	- **Condition**: Restrict to specific regions only
	- **Why Needed**: Post-recovery validation and SSM command targeting

**Statement 4 - SSMCommandExecution:**
	- **Purpose**: Allow hub to execute post-recovery automation
	- **Actions**: SSM command execution on recovered instances
	- **Resource**: Specific SSM documents and EC2 instances only
	- **Why Needed**: Application startup, health checks, network validation

**Statement 5 - CloudWatchLogsForAuditing:**
	- **Purpose**: Allow hub to write audit logs in spoke account
	- **Actions**: CloudWatch Logs creation and writing
	- **Resource**: Specific log group prefix only
	- **Why Needed**: Centralized audit trail of cross-account operations

**Attach Policy to Role:**

**Console Method:**
1. In IAM Console, navigate to Policies
2. Click "Create policy"
3. Switch to JSON editor
4. Paste the policy above
5. Update region conditions to match your requirements
6. Click "Next"
7. Policy name: `DRSOrchestrationCrossAccountPermissions`
8. Description: "Permissions for DRS Orchestration hub account"
9. Click "Create policy"
10. Navigate to Roles → DRSOrchestrationCrossAccountRole
11. Click "Add permissions" → "Attach policies"
12. Search for `DRSOrchestrationCrossAccountPermissions`
13. Select and click "Attach policies"

**CLI Method:**

```bash
# Save policy to file: permissions-policy.json
# Then execute:

# Create policy
aws iam create-policy \
    --policy-name DRSOrchestrationCrossAccountPermissions \
    --policy-document file://permissions-policy.json \
    --description "Permissions for DRS Orchestration hub account"

# Attach policy to role
aws iam attach-role-policy \
    --role-name DRSOrchestrationCrossAccountRole \
    --policy-arn arn:aws:iam::123456789012:policy/DRSOrchestrationCrossAccountPermissions
```

### Step 3: Document Role ARN

After creating the role, document its ARN for hub account configuration.

**Retrieve Role ARN:**

**Console Method:**
1. Navigate to IAM Console → Roles
2. Click on `DRSOrchestrationCrossAccountRole`
3. Copy the "ARN" field from Summary section

**CLI Method:**
```bash
aws iam get-role \
    --role-name DRSOrchestrationCrossAccountRole \
    --query 'Role.Arn' \
    --output text

# Output: arn:aws:iam::123456789012:role/DRSOrchestrationCrossAccountRole
```

**Document in Secure Location:**
```
Spoke Account: 123456789012
Region: us-east-1
Role ARN: arn:aws:iam::123456789012:role/DRSOrchestrationCrossAccountRole
External ID: [store securely in Secrets Manager]
Created Date: 2025-01-15
Created By: admin@example.com
```

---

## Protection Group Configuration

### Step 1: Create Cross-Account Protection Group

Use the DRS Orchestration UI or API to create a Protection Group with cross-account configuration.

**Example API Request:**

```bash
curl -X POST https://your-api-gateway-url/protection-groups \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "GroupName": "Spoke Account Production Servers",
    "Description": "Production web tier in spoke account 123456789012",
    "Region": "us-east-1",
    "AccountId": "123456789012",
    "SourceServerIds": [
      "s-3c1730a9e0771ea14",
      "s-3d75cdc0d9a28a725"
    ],
    "CrossAccountRoleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationCrossAccountRole",
    "CrossAccountExternalId": "your-unique-external-id",
    "Owner": "dr-team@example.com"
  }'
