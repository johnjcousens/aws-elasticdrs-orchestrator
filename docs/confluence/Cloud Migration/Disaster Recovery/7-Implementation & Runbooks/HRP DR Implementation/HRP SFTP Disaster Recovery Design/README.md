# HRP SFTP Disaster Recovery Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5231640751/HRP%20SFTP%20Disaster%20Recovery%20Design

**Created by:** Venkata Kommuri on November 13, 2025  
**Last modified by:** Chris Falk on December 18, 2025 at 08:21 PM

---

AWS Disaster Recovery Implementation Runbook
============================================

SFTP Services using AWS Transfer Family
---------------------------------------

**Document Version:** 1.0

**Last Updated:** November 2025

**Author:** AWS Migration Team

**Classification:** Internal Use

**Target Audience:** Infrastructure Engineers, File Transfer Administrators, DR Coordinators

### Table of Contents

* [1. Executive Summary](#)
* [2. Architecture Overview](#)
* [3. Prerequisites](#)
* [4. Phase 1: AWS Transfer Family Setup](#)
* [5. Phase 2: S3 Storage Configuration](#)
* [6. Phase 3: User and Access Management](#)
* [7. Phase 4: DR Configuration](#)
* [8. Phase 5: Testing Procedures](#)
* [9. Phase 6: Failover Procedures](#)
* [10. Phase 7: Failback Procedures](#)
* [11. Monitoring and Alerting](#)
* [12. Troubleshooting Guide](#)
* [13. Appendices](#)

1. Executive Summary
--------------------

### 1.1 Purpose

This runbook provides comprehensive step-by-step procedures for implementing disaster recovery for SFTP services using AWS Transfer Family. The solution supports HRP's multi-region architecture with primary regions in US-East-1 and US-West-2, and DR regions in US-East-2 and US-West-1.

### 1.2 Solution Overview

AWS Transfer Family provides fully managed SFTP, FTPS, and FTP services with S3 as the backend storage. This solution enables:

* **RTO Target:** 4 hours
* **RPO Target:** 15 minutes
* **Recovery Strategy:** Active-Passive with automated DNS failover
* **Data Replication:** S3 Cross-Region Replication (CRR)
* **Cost Efficiency:** Pay only for active transfers and storage

### 1.3 Key Benefits

| Benefit | Description |
| --- | --- |
| Fully Managed Service | No server management, patching, or maintenance required |
| Scalable and Elastic | Automatically scales to handle any number of concurrent connections |
| Near Real-Time Replication | S3 CRR provides sub-second to minutes replication |
| Customer Isolation | Separate S3 buckets and IAM policies per customer |
| Automated Failover | Route 53 health checks with automatic DNS failover |
| Compliance Ready | Encryption at rest and in transit, audit logging, versioning |

### 1.4 HRP Requirements Alignment

Based on analysis of HRP DR documentation, this solution addresses the following requirements:

#### Current State Requirements

* **Shared SFTP Services:** Maintains shared service model with customer-specific folders
* **Customer Isolation:** Logical separation through S3 bucket policies and IAM
* **No Major Rewrites:** Lift and shift approach maintaining current operational patterns
* **Multi-Region Support:** Primary (US-East-1, US-West-2) and DR (US-East-2, US-West-1)
* **Quarterly DR Testing:** Non-disruptive testing without customer impact
* **Audit and Compliance:** CloudTrail logging and S3 access logs

### 1.5 Migration Strategy

**Phased Approach:**

1. **Phase 1 (Current):** Maintain existing SFTP infrastructure on EC2 with AWS DRS for DR
2. **Phase 2 (Future):** Migrate to AWS Transfer Family with S3 backend (this runbook)
3. **Phase 3 (Optimization):** Implement advanced features (automation, monitoring, cost optimization)

**Note:** This runbook covers Phase 2 - the migration to AWS Transfer Family for enhanced DR capabilities.

2. Architecture Overview
------------------------

### 2.1 Regional Architecture


```

Primary Regions:
├── US-East-1 (N. Virginia)
│   ├── AWS Transfer Family SFTP Endpoint
│   ├── S3 Bucket (Primary Storage)
│   ├── S3 Cross-Region Replication → US-East-2
│   └── Route 53 Health Checks
│
└── US-West-2 (Oregon)
    ├── AWS Transfer Family SFTP Endpoint
    ├── S3 Bucket (Primary Storage)
    ├── S3 Cross-Region Replication → US-West-1
    └── Route 53 Health Checks

DR Regions:
├── US-East-2 (Ohio)
│   ├── AWS Transfer Family SFTP Endpoint (Standby)
│   ├── S3 Bucket (Replica)
│   └── Route 53 Failover Configuration
│
└── US-West-1 (N. California)
    ├── AWS Transfer Family SFTP Endpoint (Standby)
    ├── S3 Bucket (Replica)
    └── Route 53 Failover Configuration
        
```


### 2.2 Component Architecture

#### Primary Region Components

| Component | Service | Purpose |
| --- | --- | --- |
| SFTP Endpoint | AWS Transfer Family | Managed SFTP service with VPC endpoint |
| Storage Backend | Amazon S3 | Scalable object storage for files |
| User Authentication | AWS Secrets Manager / IAM | Secure credential storage and management |
| Access Control | IAM Policies | Fine-grained access control per customer |
| Encryption | AWS KMS | Server-side encryption for data at rest |
| DNS Management | Route 53 | Custom domain with health checks |
| Logging | CloudWatch Logs / CloudTrail | Audit trails and operational logs |

#### DR Region Components

| Component | Service | State |
| --- | --- | --- |
| SFTP Endpoint | AWS Transfer Family | Standby (pre-configured) |
| Storage Backend | Amazon S3 (Replica) | Active replication |
| User Authentication | AWS Secrets Manager (Replica) | Replicated secrets |
| DNS Failover | Route 53 | Health check monitoring |

### 2.3 Customer Isolation Model

#### Multi-Tenant Architecture

Each customer has isolated resources:

| Resource | Isolation Method |
| --- | --- |
| S3 Bucket | Dedicated bucket per customer: `hrp-sftp-customer-{customer-id}` |
| IAM Role | Customer-specific role with bucket-scoped permissions |
| Home Directory | Logical home directory mapping to S3 prefix |
| Users | Customer-specific usernames with Secrets Manager credentials |
| Logging | Separate CloudWatch log streams per customer |

### 2.4 Data Flow

#### Normal Operations

1. Customer connects to SFTP endpoint via custom domain ([sftp.hrp.example.com](http://sftp.hrp.example.com))
2. Route 53 resolves to primary region Transfer Family endpoint
3. User authenticates using SSH key or password (stored in Secrets Manager)
4. Transfer Family assumes customer-specific IAM role
5. Files uploaded/downloaded to/from customer's S3 bucket
6. S3 Cross-Region Replication automatically replicates to DR region
7. CloudWatch Logs and CloudTrail capture all activities

#### Disaster Recovery Operations

1. Route 53 health check detects primary endpoint failure
2. DNS automatically fails over to DR region endpoint
3. Customers reconnect to DR endpoint (transparent to users)
4. Files accessed from replicated S3 bucket in DR region
5. New uploads stored in DR region bucket
6. After primary recovery, reverse replication configured
7. Failback to primary region when ready

### 2.5 Network Architecture


```

Primary Region (US-East-1):
VPC: 10.10.0.0/16
├── Public Subnet: 10.10.0.0/24
│   └── NAT Gateway
├── Private Subnet: 10.10.1.0/24
│   └── VPC Endpoint for Transfer Family
└── S3 VPC Endpoint (Gateway)

Transfer Family Configuration:
├── Endpoint Type: VPC
├── Security Group: Allow port 22 from customer IPs
├── Elastic IP: Static IP for customer firewall rules
└── Custom Hostname: sftp.hrp.example.com

DR Region (US-East-2):
VPC: 10.20.0.0/16
├── Public Subnet: 10.20.0.0/24
│   └── NAT Gateway
├── Private Subnet: 10.20.1.0/24
│   └── VPC Endpoint for Transfer Family
└── S3 VPC Endpoint (Gateway)

Transfer Family Configuration:
├── Endpoint Type: VPC
├── Security Group: Allow port 22 from customer IPs
├── Elastic IP: Static IP for customer firewall rules
└── Custom Hostname: sftp-dr.hrp.example.com
        
```


3. Prerequisites
----------------

### 3.1 AWS Account Requirements

#### IAM Permissions

Required IAM policies for AWS Transfer Family implementation:


```
{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "transfer:*",
        "s3:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PassRole",
        "secretsmanager:*",
        "kms:CreateKey",
        "kms:CreateAlias",
        "kms:DescribeKey",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:CreateSecurityGroup",
        "ec2:AllocateAddress",
        "route53:*",
        "cloudwatch:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```


#### Service Quotas

| Service | Quota | Default | Recommended |
| --- | --- | --- | --- |
| Transfer Family Servers | Servers per region | 10 | 20 (request increase) |
| Transfer Family Users | Users per server | 10,000 | Sufficient for most cases |
| S3 Buckets | Buckets per account | 100 | 200+ (one per customer) |
| Secrets Manager | Secrets per region | 500,000 | Sufficient |

### 3.2 Network Requirements

#### VPC Configuration

| Component | Requirement |
| --- | --- |
| VPC | Existing VPC in each region |
| Subnets | At least 2 private subnets in different AZs |
| NAT Gateway | For outbound internet access (optional) |
| Security Groups | Allow inbound port 22 from customer IPs |
| Elastic IPs | Static IPs for customer firewall rules |

#### Customer IP Whitelist

**Important:** Collect customer IP addresses for security group configuration:

* Customer on-premises data center IPs
* Customer VPN endpoint IPs
* Third-party vendor IPs (if applicable)
* Document IP ranges in CIDR notation

### 3.3 DNS Requirements

#### Domain Configuration

| Item | Requirement |
| --- | --- |
| Domain Name | Custom domain for SFTP service (e.g., [sftp.hrp.example.com](http://sftp.hrp.example.com)) |
| Route 53 Hosted Zone | Hosted zone for the domain |
| SSL Certificate | ACM certificate for custom hostname (optional for SFTP) |
| Health Check | Route 53 health check configuration |

### 3.4 Customer Data Requirements

#### Customer Information Needed

For each customer, collect the following information:

| Information | Purpose |
| --- | --- |
| Customer ID | Unique identifier for resource naming |
| Customer Name | Tagging and documentation |
| SFTP Users | List of usernames and authentication method |
| SSH Public Keys | For SSH key-based authentication |
| IP Whitelist | Source IP restrictions |
| Storage Quota | S3 bucket size limits (if applicable) |
| Retention Policy | File lifecycle management |

### 3.5 Migration Prerequisites

#### Current SFTP Server Assessment

* Document current SFTP server configuration
* Export user accounts and SSH keys
* Inventory all customer folders and permissions
* Document current file retention policies
* Identify integration points (applications, scripts)
* Backup all current SFTP data
* Test data migration process

4. Phase 1: AWS Transfer Family Setup
-------------------------------------

### 4.1 Create Transfer Family Server - Primary Region

#### Step 1: Create SFTP Server via Console

1. Navigate to AWS Transfer Family console in US-East-1
2. Click "Create server"
3. Configure server settings:

   * **Protocols:** SFTP
   * **Identity provider:** Service managed
   * **Endpoint type:** VPC
   * **Logging role:** Create new role

#### Step 2: Create SFTP Server via CLI


```
#!/bin/bash
# Create Transfer Family SFTP server in primary region

PRIMARY_REGION="us-east-1"
VPC_ID="vpc-xxxxxxxxx"
SUBNET_IDS="subnet-xxxxxxx1,subnet-xxxxxxx2"
SECURITY_GROUP_ID="sg-xxxxxxxxx"

# Create CloudWatch Logs role
LOGGING_ROLE_ARN=$(aws iam create-role \
  --role-name TransferFamilyLoggingRole \
  --assume-role-policy-document '{
    "Version": "October 17, 2012",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "transfer.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  --query 'Role.Arn' \
  --output text)

# Attach CloudWatch Logs policy
aws iam attach-role-policy \
  --role-name TransferFamilyLoggingRole \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess

# Create Transfer Family server
SERVER_ID=$(aws transfer create-server \
  --region $PRIMARY_REGION \
  --endpoint-type VPC \
  --endpoint-details VpcId=$VPC_ID,SubnetIds=$SUBNET_IDS,SecurityGroupIds=$SECURITY_GROUP_ID \
  --protocols SFTP \
  --identity-provider-type SERVICE_MANAGED \
  --logging-role $LOGGING_ROLE_ARN \
  --tags Key=Environment,Value=Production Key=Region,Value=Primary Key=Application,Value=HRP-SFTP \
  --query 'ServerId' \
  --output text)

echo "Transfer Family Server ID: $SERVER_ID"

# Wait for server to be online
aws transfer wait server-online \
  --region $PRIMARY_REGION \
  --server-id $SERVER_ID

echo "✓ Transfer Family server created and online"
```


### 4.2 Configure VPC Endpoint

#### Create Security Group for Transfer Family


```
# Create security group for Transfer Family endpoint
SG_ID=$(aws ec2 create-security-group \
  --region $PRIMARY_REGION \
  --group-name hrp-sftp-transfer-family-sg \
  --description "Security group for HRP SFTP Transfer Family endpoint" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

# Add inbound rules for customer IPs
# Example: Allow SFTP from customer IP ranges
aws ec2 authorize-security-group-ingress \
  --region $PRIMARY_REGION \
  --group-id $SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr 203.0.113.0/24 \
  --group-rule-description "Customer A SFTP access"

aws ec2 authorize-security-group-ingress \
  --region $PRIMARY_REGION \
  --group-id $SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr 198.51.100.0/24 \
  --group-rule-description "Customer B SFTP access"

echo "✓ Security group created: $SG_ID"
```


### 4.3 Assign Elastic IPs

#### Allocate and Associate Elastic IPs


```
# Allocate Elastic IPs for each AZ
EIP1=$(aws ec2 allocate-address \
  --region $PRIMARY_REGION \
  --domain vpc \
  --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=hrp-sftp-eip-az1}]' \
  --query 'AllocationId' \
  --output text)

EIP2=$(aws ec2 allocate-address \
  --region $PRIMARY_REGION \
  --domain vpc \
  --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=hrp-sftp-eip-az2}]' \
  --query 'AllocationId' \
  --output text)

echo "Elastic IP 1: $EIP1"
echo "Elastic IP 2: $EIP2"

# Update Transfer Family server with Elastic IPs
aws transfer update-server \
  --region $PRIMARY_REGION \
  --server-id $SERVER_ID \
  --endpoint-details VpcId=$VPC_ID,SubnetIds=$SUBNET_IDS,SecurityGroupIds=$SG_ID,AddressAllocationIds=$EIP1,$EIP2

echo "✓ Elastic IPs assigned to Transfer Family server"
```


### 4.4 Configure Custom Hostname

#### Create Custom Hostname with Route 53


```
# Get Transfer Family endpoint hostname
TRANSFER_ENDPOINT=$(aws transfer describe-server \
  --region $PRIMARY_REGION \
  --server-id $SERVER_ID \
  --query 'Server.EndpointDetails.VpcEndpointId' \
  --output text)

# Create Route 53 CNAME record
HOSTED_ZONE_ID="Z1234567890ABC"
CUSTOM_HOSTNAME="sftp.hrp.example.com"

cat > /tmp/route53-change.json <
```


### `4.5 Create DR Region Transfer Family Server`

#### `Replicate Configuration in DR Region`


```
#!/bin/bash
# Create Transfer Family SFTP server in DR region

DR_REGION="us-east-2"
DR_VPC_ID="vpc-yyyyyyyyy"
DR_SUBNET_IDS="subnet-yyyyyyy1,subnet-yyyyyyy2"
DR_SECURITY_GROUP_ID="sg-yyyyyyyyy"

# Create logging role in DR region (if not exists)
DR_LOGGING_ROLE_ARN=$(aws iam create-role \
  --role-name TransferFamilyLoggingRoleDR \
  --assume-role-policy-document '{
    "Version": "October 17, 2012",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "transfer.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  --query 'Role.Arn' \
  --output text 2>/dev/null || \
  aws iam get-role --role-name TransferFamilyLoggingRoleDR --query 'Role.Arn' --output text)

aws iam attach-role-policy \
  --role-name TransferFamilyLoggingRoleDR \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess

# Create Transfer Family server in DR region
DR_SERVER_ID=$(aws transfer create-server \
  --region $DR_REGION \
  --endpoint-type VPC \
  --endpoint-details VpcId=$DR_VPC_ID,SubnetIds=$DR_SUBNET_IDS,SecurityGroupIds=$DR_SECURITY_GROUP_ID \
  --protocols SFTP \
  --identity-provider-type SERVICE_MANAGED \
  --logging-role $DR_LOGGING_ROLE_ARN \
  --tags Key=Environment,Value=DR Key=Region,Value=Secondary Key=Application,Value=HRP-SFTP \
  --query 'ServerId' \
  --output text)

echo "DR Transfer Family Server ID: $DR_SERVER_ID"

# Wait for server to be online
aws transfer wait server-online \
  --region $DR_REGION \
  --server-id $DR_SERVER_ID

# Allocate Elastic IPs for DR
DR_EIP1=$(aws ec2 allocate-address \
  --region $DR_REGION \
  --domain vpc \
  --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=hrp-sftp-dr-eip-az1}]' \
  --query 'AllocationId' \
  --output text)

DR_EIP2=$(aws ec2 allocate-address \
  --region $DR_REGION \
  --domain vpc \
  --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=hrp-sftp-dr-eip-az2}]' \
  --query 'AllocationId' \
  --output text)

# Update DR server with Elastic IPs
aws transfer update-server \
  --region $DR_REGION \
  --server-id $DR_SERVER_ID \
  --endpoint-details VpcId=$DR_VPC_ID,SubnetIds=$DR_SUBNET_IDS,SecurityGroupIds=$DR_SECURITY_GROUP_ID,AddressAllocationIds=$DR_EIP1,$DR_EIP2

echo "✓ DR Transfer Family server created and configured"
```


### `4.6 Phase 1 Completion Checklist`

* `Transfer Family server created in primary region`
* `Transfer Family server created in DR region`
* `VPC endpoints configured in both regions`
* `Security groups configured with customer IP whitelist`
* `Elastic IPs allocated and assigned`
* `Custom hostname configured with Route 53`
* `CloudWatch logging enabled`
* `Servers in ONLINE state`

`5. Phase 2: S3 Storage Configuration`
--------------------------------------

### `5.1 Create S3 Buckets for Each Customer`

#### `S3 Bucket Naming Convention`

`Naming Pattern: hrp-sftp-{region}-{customer-id}`

`Examples:`

* `Primary: hrp-sftp-useast1-customer001`
* `DR: hrp-sftp-useast2-customer001`

#### `Create Customer S3 Buckets`


```
#!/bin/bash
# Create S3 buckets for customer SFTP storage

CUSTOMER_ID="customer001"
CUSTOMER_NAME="Customer A"
PRIMARY_REGION="us-east-1"
DR_REGION="us-east-2"

# Create primary bucket
PRIMARY_BUCKET="hrp-sftp-useast1-${CUSTOMER_ID}"

aws s3api create-bucket \
  --bucket $PRIMARY_BUCKET \
  --region $PRIMARY_REGION \
  --create-bucket-configuration LocationConstraint=$PRIMARY_REGION

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket $PRIMARY_BUCKET \
  --versioning-configuration Status=Enabled

# Enable server-side encryption
aws s3api put-bucket-encryption \
  --bucket $PRIMARY_BUCKET \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "arn:aws:kms:'$PRIMARY_REGION':ACCOUNT_ID:key/KEY_ID"
      },
      "BucketKeyEnabled": true
    }]
  }'

# Add bucket tags
aws s3api put-bucket-tagging \
  --bucket $PRIMARY_BUCKET \
  --tagging 'TagSet=[
    {Key=Customer,Value="'$CUSTOMER_NAME'"},
    {Key=CustomerID,Value="'$CUSTOMER_ID'"},
    {Key=Environment,Value=Production},
    {Key=Application,Value=SFTP}
  ]'

echo "✓ Primary bucket created: $PRIMARY_BUCKET"

# Create DR bucket
DR_BUCKET="hrp-sftp-useast2-${CUSTOMER_ID}"

aws s3api create-bucket \
  --bucket $DR_BUCKET \
  --region $DR_REGION \
  --create-bucket-configuration LocationConstraint=$DR_REGION

# Enable versioning on DR bucket
aws s3api put-bucket-versioning \
  --bucket $DR_BUCKET \
  --versioning-configuration Status=Enabled

# Enable server-side encryption on DR bucket
aws s3api put-bucket-encryption \
  --bucket $DR_BUCKET \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "arn:aws:kms:'$DR_REGION':ACCOUNT_ID:key/KEY_ID"
      },
      "BucketKeyEnabled": true
    }]
  }'

# Add bucket tags
aws s3api put-bucket-tagging \
  --bucket $DR_BUCKET \
  --tagging 'TagSet=[
    {Key=Customer,Value="'$CUSTOMER_NAME'"},
    {Key=CustomerID,Value="'$CUSTOMER_ID'"},
    {Key=Environment,Value=DR},
    {Key=Application,Value=SFTP}
  ]'

echo "✓ DR bucket created: $DR_BUCKET"
```


### `5.2 Configure S3 Cross-Region Replication`

#### `Create Replication IAM Role`


```
# Create IAM role for S3 replication
cat > /tmp/s3-replication-trust-policy.json < /tmp/s3-replication-policy.json <
```


#### `Enable Cross-Region Replication`


```
# Configure replication from primary to DR bucket
cat > /tmp/replication-config.json <
```


### `5.3 Configure S3 Lifecycle Policies`

#### `Create Lifecycle Policy for File Retention`


```
# Configure lifecycle policy for automatic file cleanup
cat > /tmp/lifecycle-policy.json <
```


### `5.4 Configure S3 Access Logging`

#### `Create Logging Bucket and Enable Access Logs`


```
# Create logging bucket
LOGGING_BUCKET="hrp-sftp-logs-${PRIMARY_REGION}"

aws s3api create-bucket \
  --bucket $LOGGING_BUCKET \
  --region $PRIMARY_REGION \
  --create-bucket-configuration LocationConstraint=$PRIMARY_REGION

# Enable logging on customer bucket
aws s3api put-bucket-logging \
  --bucket $PRIMARY_BUCKET \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "'$LOGGING_BUCKET'",
      "TargetPrefix": "'$CUSTOMER_ID'/"
    }
  }'

echo "✓ S3 access logging enabled"
```


### `5.5 Phase 2 Completion Checklist`

* `S3 buckets created for each customer in primary region`
* `S3 buckets created for each customer in DR region`
* `Versioning enabled on all buckets`
* `Server-side encryption configured with KMS`
* `Cross-region replication enabled and tested`
* `Lifecycle policies configured`
* `Access logging enabled`
* `Bucket tags applied for cost allocation`

`6. Phase 3: User and Access Management`
----------------------------------------

### `6.1 Create IAM Roles for Transfer Family Users`

#### `Create Customer-Specific IAM Role`


```
#!/bin/bash
# Create IAM role for Transfer Family user access

CUSTOMER_ID="customer001"
PRIMARY_BUCKET="hrp-sftp-useast1-${CUSTOMER_ID}"
DR_BUCKET="hrp-sftp-useast2-${CUSTOMER_ID}"

# Create trust policy for Transfer Family
cat > /tmp/transfer-trust-policy.json < /tmp/transfer-s3-policy.json <
```


### `6.2 Create SFTP Users with SSH Keys`

#### `Store SSH Public Keys in Secrets Manager`


```
# Store SSH public key in Secrets Manager
USERNAME="customer001-user1"
SSH_PUBLIC_KEY="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC... user@example.com"

# Create secret for SSH key
aws secretsmanager create-secret \
  --region $PRIMARY_REGION \
  --name "sftp/${CUSTOMER_ID}/${USERNAME}/ssh-key" \
  --description "SSH public key for $USERNAME" \
  --secret-string "$SSH_PUBLIC_KEY" \
  --tags Key=Customer,Value=$CUSTOMER_ID Key=Username,Value=$USERNAME

# Replicate secret to DR region
aws secretsmanager replicate-secret-to-regions \
  --region $PRIMARY_REGION \
  --secret-id "sftp/${CUSTOMER_ID}/${USERNAME}/ssh-key" \
  --add-replica-regions Region=$DR_REGION

echo "✓ SSH key stored in Secrets Manager and replicated to DR"
```


#### `Create Transfer Family User`


```
# Create user in Transfer Family server
HOME_DIRECTORY="/$PRIMARY_BUCKET"

aws transfer create-user \
  --region $PRIMARY_REGION \
  --server-id $SERVER_ID \
  --user-name $USERNAME \
  --role $ROLE_ARN \
  --home-directory $HOME_DIRECTORY \
  --home-directory-type LOGICAL \
  --home-directory-mappings '[
    {
      "Entry": "/",
      "Target": "/'$PRIMARY_BUCKET'"
    }
  ]' \
  --ssh-public-key-body "$SSH_PUBLIC_KEY" \
  --tags Key=Customer,Value=$CUSTOMER_ID Key=Username,Value=$USERNAME

echo "✓ Transfer Family user created: $USERNAME"

# Create same user in DR region
aws transfer create-user \
  --region $DR_REGION \
  --server-id $DR_SERVER_ID \
  --user-name $USERNAME \
  --role $ROLE_ARN \
  --home-directory "/$DR_BUCKET" \
  --home-directory-type LOGICAL \
  --home-directory-mappings '[
    {
      "Entry": "/",
      "Target": "/'$DR_BUCKET'"
    }
  ]' \
  --ssh-public-key-body "$SSH_PUBLIC_KEY" \
  --tags Key=Customer,Value=$CUSTOMER_ID Key=Username,Value=$USERNAME

echo "✓ DR Transfer Family user created: $USERNAME"
```


### `6.3 Create Users with Password Authentication`

#### `Store Password in Secrets Manager`


```
# Generate secure password
PASSWORD=$(openssl rand -base64 32)

# Store password in Secrets Manager
aws secretsmanager create-secret \
  --region $PRIMARY_REGION \
  --name "sftp/${CUSTOMER_ID}/${USERNAME}/password" \
  --description "Password for $USERNAME" \
  --secret-string "$PASSWORD" \
  --tags Key=Customer,Value=$CUSTOMER_ID Key=Username,Value=$USERNAME

# Replicate to DR region
aws secretsmanager replicate-secret-to-regions \
  --region $PRIMARY_REGION \
  --secret-id "sftp/${CUSTOMER_ID}/${USERNAME}/password" \
  --add-replica-regions Region=$DR_REGION

echo "✓ Password stored securely"
echo "Password: $PASSWORD"  # Share securely with customer
```


### `6.4 Bulk User Creation Script`

#### `Create Multiple Users from CSV`


```
#!/bin/bash
# Bulk create Transfer Family users from CSV file
# CSV format: customer_id,username,ssh_public_key

CSV_FILE="users.csv"

while IFS=',' read -r customer_id username ssh_key; do
    echo "Creating user: $username for customer: $customer_id"
    
    # Skip header row
    if [ "$customer_id" == "customer_id" ]; then
        continue
    fi
    
    # Set bucket names
    PRIMARY_BUCKET="hrp-sftp-useast1-${customer_id}"
    DR_BUCKET="hrp-sftp-useast2-${customer_id}"
    ROLE_NAME="TransferFamilyRole-${customer_id}"
    
    # Get role ARN
    ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
    
    # Create user in primary region
    aws transfer create-user \
      --region $PRIMARY_REGION \
      --server-id $SERVER_ID \
      --user-name $username \
      --role $ROLE_ARN \
      --home-directory "/$PRIMARY_BUCKET" \
      --home-directory-type LOGICAL \
      --home-directory-mappings "[{\"Entry\":\"/\",\"Target\":\"/$PRIMARY_BUCKET\"}]" \
      --ssh-public-key-body "$ssh_key" \
      --tags Key=Customer,Value=$customer_id Key=Username,Value=$username
    
    # Create user in DR region
    aws transfer create-user \
      --region $DR_REGION \
      --server-id $DR_SERVER_ID \
      --user-name $username \
      --role $ROLE_ARN \
      --home-directory "/$DR_BUCKET" \
      --home-directory-type LOGICAL \
      --home-directory-mappings "[{\"Entry\":\"/\",\"Target\":\"/$DR_BUCKET\"}]" \
      --ssh-public-key-body "$ssh_key" \
      --tags Key=Customer,Value=$customer_id Key=Username,Value=$username
    
    echo "✓ User created: $username"
    
done < "$CSV_FILE"

echo "✓ Bulk user creation completed"
```


### `6.5 Test User Access`

#### `Test SFTP Connection`


```
# Test SFTP connection from client
sftp -i ~/.ssh/id_rsa customer001-user1@sftp.hrp.example.com

# Once connected, test operations:
# sftp> ls
# sftp> put testfile.txt
# sftp> get testfile.txt
# sftp> rm testfile.txt
# sftp> exit

# Verify file in S3
aws s3 ls s3://hrp-sftp-useast1-customer001/

# Verify replication to DR
aws s3 ls s3://hrp-sftp-useast2-customer001/
```


### `6.6 Phase 3 Completion Checklist`

* `IAM roles created for each customer`
* `S3 access policies configured`
* `SFTP users created in primary region`
* `SFTP users created in DR region`
* `SSH keys stored in Secrets Manager`
* `Secrets replicated to DR region`
* `User access tested successfully`
* `File upload/download verified`
* `Cross-region replication verified`

`7. Phase 4: DR Configuration`
------------------------------

### `7.1 Configure Route 53 Health Checks`

#### `Create Health Check for Primary Endpoint`


```
# Create health check for primary Transfer Family endpoint
PRIMARY_EIP_ADDRESS=$(aws ec2 describe-addresses \
  --region $PRIMARY_REGION \
  --allocation-ids $EIP1 \
  --query 'Addresses[0].PublicIp' \
  --output text)

HEALTH_CHECK_ID=$(aws route53 create-health-check \
  --caller-reference "sftp-primary-$(date +%s)" \
  --health-check-config '{
    "Type": "TCP",
    "IPAddress": "'$PRIMARY_EIP_ADDRESS'",
    "Port": 22,
    "RequestInterval": 30,
    "FailureThreshold": 3
  }' \
  --health-check-tags '[
    {"Key": "Name", "Value": "HRP-SFTP-Primary-HealthCheck"},
    {"Key": "Application", "Value": "SFTP"}
  ]' \
  --query 'HealthCheck.Id' \
  --output text)

echo "✓ Health check created: $HEALTH_CHECK_ID"
```


### `7.2 Configure Route 53 Failover`

#### `Create Failover DNS Records`


```
# Create primary failover record
cat > /tmp/route53-failover-primary.json < /tmp/route53-failover-secondary.json <
```


### `7.3 Configure CloudWatch Alarms`

#### `Create Alarms for Transfer Family Metrics`


```
# Create SNS topic for alerts
SNS_TOPIC_ARN=$(aws sns create-topic \
  --region $PRIMARY_REGION \
  --name hrp-sftp-alerts \
  --tags Key=Application,Value=SFTP \
  --query 'TopicArn' \
  --output text)

# Subscribe email to topic
aws sns subscribe \
  --region $PRIMARY_REGION \
  --topic-arn $SNS_TOPIC_ARN \
  --protocol email \
  --notification-endpoint ops-team@example.com

# Create alarm for failed logins
aws cloudwatch put-metric-alarm \
  --region $PRIMARY_REGION \
  --alarm-name "SFTP-FailedLogins-High" \
  --alarm-description "Alert on high number of failed SFTP logins" \
  --metric-name UserAuthenticationFailures \
  --namespace AWS/Transfer \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions $SNS_TOPIC_ARN \
  --dimensions Name=ServerId,Value=$SERVER_ID

# Create alarm for bytes transferred
aws cloudwatch put-metric-alarm \
  --region $PRIMARY_REGION \
  --alarm-name "SFTP-BytesTransferred-Low" \
  --alarm-description "Alert when no data transferred (possible outage)" \
  --metric-name BytesIn \
  --namespace AWS/Transfer \
  --statistic Sum \
  --period 3600 \
  --threshold 1000 \
  --comparison-operator LessThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions $SNS_TOPIC_ARN \
  --dimensions Name=ServerId,Value=$SERVER_ID

echo "✓ CloudWatch alarms configured"
```


### `7.4 Configure S3 Event Notifications`

#### `Set Up S3 Event Notifications for File Uploads`


```
# Create Lambda function for file processing (optional)
# Or configure SNS notifications for file uploads

cat > /tmp/s3-notification-config.json <
```


### `7.5 Test DR Failover`

#### `Simulate Primary Region Failure`


```
# Test failover by stopping primary server
echo "Testing DR failover..."

# Stop primary Transfer Family server
aws transfer stop-server \
  --region $PRIMARY_REGION \
  --server-id $SERVER_ID

echo "Primary server stopped. Waiting for health check to fail..."

# Wait for health check to detect failure (90 seconds)
sleep 90

# Test DNS resolution
echo "Testing DNS resolution..."
nslookup sftp.hrp.example.com

# Should now resolve to DR region endpoint

# Test SFTP connection to DR
echo "Testing SFTP connection to DR endpoint..."
sftp -i ~/.ssh/id_rsa customer001-user1@sftp.hrp.example.com <
```


### `7.6 Phase 4 Completion Checklist`

* `Route 53 health checks configured`
* `Failover DNS records created`
* `CloudWatch alarms configured`
* `SNS notifications set up`
* `S3 event notifications configured`
* `DR failover tested successfully`
* `DNS failover verified`
* `File access in DR region confirmed`

`8. Phase 5: Testing Procedures`
--------------------------------

### `8.1 Functional Testing`

#### `Test Checklist`

| `Test Case` | `Expected Result` | `Status` |
| --- | --- | --- |
| `User Authentication - SSH Key` | `Successful login with SSH key` | `☐ Pass ☐ Fail` |
| `User Authentication - Password` | `Successful login with password` | `☐ Pass ☐ Fail` |
| `File Upload` | `File uploaded to S3 successfully` | `☐ Pass ☐ Fail` |
| `File Download` | `File downloaded successfully` | `☐ Pass ☐ Fail` |
| `File Delete` | `File deleted from S3` | `☐ Pass ☐ Fail` |
| `Directory Listing` | `Correct files listed` | `☐ Pass ☐ Fail` |
| `Cross-Region Replication` | `File replicated to DR within 15 minutes` | `☐ Pass ☐ Fail` |
| `Customer Isolation` | `Users cannot access other customer files` | `☐ Pass ☐ Fail` |

#### `Automated Testing Script`


```
#!/bin/bash
# Automated SFTP testing script

SFTP_HOST="sftp.hrp.example.com"
SFTP_USER="customer001-user1"
SSH_KEY="~/.ssh/id_rsa"
TEST_FILE="test-$(date +%s).txt"

echo "=== SFTP Functional Testing ==="
echo "Timestamp: $(date)"

# Create test file
echo "Test data - $(date)" > /tmp/$TEST_FILE

# Test 1: Upload file
echo "Test 1: Uploading file..."
sftp -i $SSH_KEY $SFTP_USER@$SFTP_HOST <
```


### `8.2 Performance Testing`

#### `Load Testing Script`


```
#!/bin/bash
# SFTP performance and load testing

SFTP_HOST="sftp.hrp.example.com"
SFTP_USER="customer001-user1"
SSH_KEY="~/.ssh/id_rsa"
CONCURRENT_CONNECTIONS=10
FILES_PER_CONNECTION=100

echo "=== SFTP Performance Testing ==="
echo "Concurrent connections: $CONCURRENT_CONNECTIONS"
echo "Files per connection: $FILES_PER_CONNECTION"

# Function to upload files
upload_files() {
    local connection_id=$1
    local start_time=$(date +%s)
    
    for i in $(seq 1 $FILES_PER_CONNECTION); do
        local filename="perf-test-${connection_id}-${i}.txt"
        echo "Test data" > /tmp/$filename
        
        sftp -i $SSH_KEY $SFTP_USER@$SFTP_HOST < /dev/null 2>&1
put /tmp/$filename
exit
EOF
        
        rm /tmp/$filename
    done
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    echo "Connection $connection_id completed in $duration seconds"
}

# Start concurrent uploads
for i in $(seq 1 $CONCURRENT_CONNECTIONS); do
    upload_files $i &
done

# Wait for all background jobs to complete
wait

echo "✓ Performance test completed"
```


### `8.3 DR Testing Procedures`

#### `Quarterly DR Test Plan`

#### `DR Test Schedule`

`Frequency: Quarterly`

`Duration: 2-4 hours`

`Participants: Infrastructure team, Application team, Customer representatives (if required)`

#### `Test Phases`

1. `Pre-Test (30 minutes)`

   * `Verify all systems healthy`
   * `Notify stakeholders`
   * `Document current state`
2. `Failover Test (1 hour)`

   * `Simulate primary region failure`
   * `Verify DNS failover`
   * `Test user connectivity to DR`
   * `Verify file access in DR`
3. `Validation (1 hour)`

   * `Test all customer connections`
   * `Verify file operations`
   * `Check monitoring and alerts`
   * `Document any issues`
4. `Failback (1 hour)`

   * `Restore primary region`
   * `Verify reverse replication`
   * `Failback to primary`
   * `Confirm normal operations`
5. `Post-Test (30 minutes)`

   * `Document results`
   * `Update runbooks`
   * `Communicate outcomes`

### `8.4 Phase 5 Completion Checklist`

* `Functional tests completed successfully`
* `Performance tests completed`
* `Load testing validated`
* `DR test plan documented`
* `Quarterly DR test scheduled`
* `Test results documented`
* `Issues identified and resolved`

`9. Phase 6: Failover Procedures`
---------------------------------

### `9.1 Failover Decision Criteria`

#### `Initiate Failover When:`

1. `Primary Region Outage`

   * `Complete AWS region unavailability`
   * `Extended network connectivity loss (>30 minutes)`
   * `Multiple availability zone failures`
2. `Transfer Family Service Failure`

   * `SFTP endpoint unresponsive`
   * `Persistent authentication failures`
   * `Service degradation affecting multiple customers`
3. `S3 Storage Issues`

   * `S3 bucket inaccessible`
   * `Data corruption detected`
   * `Replication lag exceeding RPO`
4. `Planned Maintenance`

   * `Scheduled region maintenance`
   * `Infrastructure upgrades`
   * `Network changes`

### `9.2 Failover Communication`

#### `Notification Template`

#### `[URGENT] SFTP Service Failover - DR Activation`

| `Field` | `Details` |
| --- | --- |
| `Incident ID` | `[INC-XXXXX]` |
| `Severity` | `High` |
| `Affected Service` | `SFTP File Transfer` |
| `Primary Region` | `[us-east-1 / us-west-2]` |
| `DR Region` | `[us-east-2 / us-west-1]` |
| `Impact` | `Automatic failover - No customer action required` |

`Status: DR failover initiated. SFTP service automatically redirected to DR region.`

`Customer Action: None required. Existing connections will reconnect automatically.`

### `9.3 Automatic Failover Process`

#### `Failover Flow`

1. `Detection (0-3 minutes)`

   * `Route 53 health check detects primary endpoint failure`
   * `Health check fails 3 consecutive times (90 seconds)`
   * `CloudWatch alarm triggered`
2. `DNS Failover (3-5 minutes)`

   * `Route 53 automatically updates DNS to DR endpoint`
   * `TTL of 60 seconds ensures quick propagation`
   * `New connections route to DR region`
3. `Service Continuity (5+ minutes)`

   * `Customers reconnect to DR endpoint`
   * `Files accessed from replicated S3 bucket`
   * `Normal operations resume in DR region`

### `9.4 Manual Failover Procedure`

#### `Forced Failover Script`


```
#!/bin/bash
# Manual failover to DR region

PRIMARY_REGION="us-east-1"
DR_REGION="us-east-2"
HOSTED_ZONE_ID="Z1234567890ABC"
FAILOVER_TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== MANUAL SFTP FAILOVER TO DR ==="
echo "Timestamp: $(date)"
echo "Primary Region: $PRIMARY_REGION"
echo "DR Region: $DR_REGION"

# Step 1: Verify DR region readiness
echo "Step 1: Verifying DR region readiness..."

DR_SERVER_STATE=$(aws transfer describe-server \
  --region $DR_REGION \
  --server-id $DR_SERVER_ID \
  --query 'Server.State' \
  --output text)

if [ "$DR_SERVER_STATE" != "ONLINE" ]; then
    echo "✗ DR server not online. Current state: $DR_SERVER_STATE"
    exit 1
fi

echo "✓ DR server is online"

# Step 2: Verify S3 replication status
echo "Step 2: Checking S3 replication status..."

REPLICATION_STATUS=$(aws s3api get-bucket-replication \
  --bucket $PRIMARY_BUCKET \
  --query 'ReplicationConfiguration.Rules[0].Status' \
  --output text)

if [ "$REPLICATION_STATUS" != "Enabled" ]; then
    echo "⚠ Warning: Replication not enabled"
fi

echo "✓ Replication status: $REPLICATION_STATUS"

# Step 3: Update Route 53 to point to DR
echo "Step 3: Updating DNS to DR region..."

# Disable primary health check
aws route53 update-health-check \
  --health-check-id $HEALTH_CHECK_ID \
  --disabled

echo "✓ Primary health check disabled"

# Wait for DNS propagation
echo "Waiting 60 seconds for DNS propagation..."
sleep 60

# Step 4: Verify failover
echo "Step 4: Verifying failover..."

DNS_RESULT=$(nslookup sftp.hrp.example.com | grep "server.transfer.$DR_REGION.amazonaws.com")

if [ -n "$DNS_RESULT" ]; then
    echo "✓ DNS now points to DR region"
else
    echo "⚠ DNS may not have propagated yet"
fi

# Step 5: Test connectivity
echo "Step 5: Testing SFTP connectivity to DR..."

timeout 10 bash -c "echo 'exit' | sftp -i ~/.ssh/id_rsa customer001-user1@sftp.hrp.example.com" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ SFTP connectivity to DR confirmed"
else
    echo "⚠ SFTP connectivity test inconclusive"
fi

# Step 6: Log failover event
echo "Step 6: Logging failover event..."

aws cloudwatch put-metric-data \
  --region $DR_REGION \
  --namespace "SFTP/DR" \
  --metric-name FailoverEvent \
  --value 1 \
  --timestamp $(date -u +%Y-%m-%dT%H:%M:%S)

echo "=== FAILOVER COMPLETED ==="
echo "SFTP service now running in DR region: $DR_REGION"
echo "Failover timestamp: $FAILOVER_TIMESTAMP"
```


### `9.5 Post-Failover Validation`

#### `Validation Checklist`

* `DR Transfer Family server online and accessible`
* `DNS resolving to DR region endpoint`
* `All customer users can authenticate`
* `File upload/download operations working`
* `S3 buckets accessible in DR region`
* `CloudWatch logs capturing activities`
* `Monitoring and alerts functional`
* `Customer notifications sent`
* `Incident documented`

`10. Phase 7: Failback Procedures`
----------------------------------

### `10.1 Failback Planning`

#### `Failback Decision Criteria`

`Initiate failback when:`

1. `Primary Region Restored`

   * `AWS confirms primary region fully operational`
   * `All services restored and stable for 24+ hours`
   * `Network connectivity verified`
2. `Root Cause Resolved`

   * `Issue causing failover completely resolved`
   * `Preventive measures implemented`
   * `No risk of recurrence`
3. `Business Approval`

   * `Stakeholder approval obtained`
   * `Maintenance window scheduled`
   * `Customer notification completed`

### `10.2 Configure Reverse Replication`

#### `Enable Replication from DR to Primary`


```
#!/bin/bash
# Configure reverse replication from DR to Primary

echo "=== Configuring Reverse Replication ==="

# Step 1: Enable versioning on primary bucket (if not already)
aws s3api put-bucket-versioning \
  --bucket $PRIMARY_BUCKET \
  --versioning-configuration Status=Enabled

# Step 2: Configure replication from DR to Primary
cat > /tmp/reverse-replication-config.json <
```


### `10.3 Execute Failback`

#### `Failback Script`


```
#!/bin/bash
# Failback to primary region

echo "=== FAILBACK TO PRIMARY REGION ==="
echo "Timestamp: $(date)"

# Step 1: Verify primary region readiness
echo "Step 1: Verifying primary region readiness..."

PRIMARY_SERVER_STATE=$(aws transfer describe-server \
  --region $PRIMARY_REGION \
  --server-id $SERVER_ID \
  --query 'Server.State' \
  --output text)

if [ "$PRIMARY_SERVER_STATE" != "ONLINE" ]; then
    echo "✗ Primary server not online"
    exit 1
fi

echo "✓ Primary server is online"

# Step 2: Verify reverse replication complete
echo "Step 2: Verifying reverse replication..."

# Check replication metrics
REPLICATION_COMPLETE=$(aws s3api get-bucket-replication \
  --bucket $DR_BUCKET \
  --query 'ReplicationConfiguration.Rules[0].Status' \
  --output text)

if [ "$REPLICATION_COMPLETE" == "Enabled" ]; then
    echo "✓ Reverse replication is active"
else
    echo "⚠ Warning: Reverse replication status unclear"
fi

# Step 3: Re-enable primary health check
echo "Step 3: Re-enabling primary health check..."

aws route53 update-health-check \
  --health-check-id $HEALTH_CHECK_ID \
  --no-disabled

echo "✓ Primary health check re-enabled"

# Step 4: Wait for health check to pass
echo "Waiting for health check to pass..."
sleep 90

HEALTH_STATUS=$(aws route53 get-health-check-status \
  --health-check-id $HEALTH_CHECK_ID \
  --query 'HealthCheckObservations[0].StatusReport.Status' \
  --output text)

if [ "$HEALTH_STATUS" == "Success" ]; then
    echo "✓ Health check passing"
else
    echo "⚠ Health check status: $HEALTH_STATUS"
fi

# Step 5: DNS will automatically failback
echo "Step 5: DNS automatically failing back to primary..."
echo "Waiting 60 seconds for DNS propagation..."
sleep 60

# Step 6: Verify failback
DNS_RESULT=$(nslookup sftp.hrp.example.com | grep "server.transfer.$PRIMARY_REGION.amazonaws.com")

if [ -n "$DNS_RESULT" ]; then
    echo "✓ DNS now points to primary region"
else
    echo "⚠ DNS may not have propagated yet"
fi

# Step 7: Test connectivity
echo "Step 7: Testing SFTP connectivity to primary..."

timeout 10 bash -c "echo 'exit' | sftp -i ~/.ssh/id_rsa customer001-user1@sftp.hrp.example.com" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ SFTP connectivity to primary confirmed"
fi

# Step 8: Disable reverse replication
echo "Step 8: Disabling reverse replication..."

aws s3api delete-bucket-replication \
  --bucket $DR_BUCKET

echo "✓ Reverse replication disabled"

# Step 9: Re-enable forward replication
echo "Step 9: Re-enabling forward replication..."

cat > /tmp/forward-replication-config.json <
```


### `10.4 Post-Failback Validation`

* `Primary Transfer Family server online`
* `DNS resolving to primary region`
* `All customer users can authenticate`
* `File operations working normally`
* `Forward replication re-enabled`
* `Reverse replication disabled`
* `Monitoring and alerts functional`
* `Customer notifications sent`
* `Incident closed and documented`

`11. Monitoring and Alerting`
-----------------------------

### `11.1 CloudWatch Metrics`

#### `Key Metrics to Monitor`

| `Metric` | `Namespace` | `Description` | `Threshold` |
| --- | --- | --- | --- |
| `BytesIn` | `AWS/Transfer` | `Bytes uploaded to server` | `Monitor trends` |
| `BytesOut` | `AWS/Transfer` | `Bytes downloaded from server` | `Monitor trends` |
| `UserAuthenticationFailures` | `AWS/Transfer` | `Failed login attempts` | `> 10 in 5 minutes` |
| `UserAuthenticationSuccesses` | `AWS/Transfer` | `Successful logins` | `Monitor trends` |
| `ReplicationLatency` | `AWS/S3` | `S3 replication lag` | `> 15 minutes` |
| `HealthCheckStatus` | `AWS/Route53` | `Endpoint health` | `< 1 (unhealthy)` |

### `11.2 CloudWatch Dashboard`

#### `Create Comprehensive Dashboard`


```
# Create CloudWatch dashboard for SFTP monitoring
cat > /tmp/sftp-dashboard.json <<'EOF'
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/Transfer", "BytesIn", { "stat": "Sum" } ],
          [ ".", "BytesOut", { "stat": "Sum" } ]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "Data Transfer Volume",
        "yAxis": {
          "left": {
            "label": "Bytes"
          }
        }
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/Transfer", "UserAuthenticationSuccesses", { "stat": "Sum" } ],
          [ ".", "UserAuthenticationFailures", { "stat": "Sum", "color": "#d62728" } ]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "Authentication Metrics"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/S3", "ReplicationLatency", { "stat": "Average" } ]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "S3 Replication Latency"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/Route53", "HealthCheckStatus", { "stat": "Minimum" } ]
        ],
        "period": 60,
        "stat": "Minimum",
        "region": "us-east-1",
        "title": "Health Check Status"
      }
    }
  ]
}
EOF

aws cloudwatch put-dashboard \
  --dashboard-name "HRP-SFTP-Monitoring" \
  --dashboard-body file:///tmp/sftp-dashboard.json

echo "✓ CloudWatch dashboard created"

rm /tmp/sftp-dashboard.json
```


### `11.3 Automated Monitoring Script`

#### `Health Check Script (Run via Cron)`


```
#!/bin/bash
# SFTP health monitoring script (run every 5 minutes)

LOG_FILE="/var/log/sftp-health-check.log"
ALERT_EMAIL="ops-team@example.com"

echo "$(date): Starting SFTP health check" >> $LOG_FILE

# Check Transfer Family server status
SERVER_STATE=$(aws transfer describe-server \
  --region us-east-1 \
  --server-id $SERVER_ID \
  --query 'Server.State' \
  --output text)

if [ "$SERVER_STATE" != "ONLINE" ]; then
    echo "$(date): ALERT - Server not online: $SERVER_STATE" >> $LOG_FILE
    aws sns publish \
      --region us-east-1 \
      --topic-arn $SNS_TOPIC_ARN \
      --subject "SFTP Alert: Server Not Online" \
      --message "Transfer Family server is in state: $SERVER_STATE"
fi

# Check S3 replication lag
REPLICATION_LAG=$(aws cloudwatch get-metric-statistics \
  --region us-east-1 \
  --namespace AWS/S3 \
  --metric-name ReplicationLatency \
  --dimensions Name=SourceBucket,Value=$PRIMARY_BUCKET \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 600 \
  --statistics Maximum \
  --query 'Datapoints[0].Maximum' \
  --output text)

if [ "$REPLICATION_LAG" != "None" ] && [ $(echo "$REPLICATION_LAG > 900" | bc) -eq 1 ]; then
    echo "$(date): ALERT - High replication lag: $REPLICATION_LAG seconds" >> $LOG_FILE
    aws sns publish \
      --region us-east-1 \
      --topic-arn $SNS_TOPIC_ARN \
      --subject "SFTP Alert: High Replication Lag" \
      --message "S3 replication lag is $REPLICATION_LAG seconds (threshold: 900)"
fi

# Check failed authentication attempts
FAILED_AUTHS=$(aws cloudwatch get-metric-statistics \
  --region us-east-1 \
  --namespace AWS/Transfer \
  --metric-name UserAuthenticationFailures \
  --dimensions Name=ServerId,Value=$SERVER_ID \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --query 'Datapoints[0].Sum' \
  --output text)

if [ "$FAILED_AUTHS" != "None" ] && [ $(echo "$FAILED_AUTHS > 10" | bc) -eq 1 ]; then
    echo "$(date): ALERT - High failed authentication attempts: $FAILED_AUTHS" >> $LOG_FILE
    aws sns publish \
      --region us-east-1 \
      --topic-arn $SNS_TOPIC_ARN \
      --subject "SFTP Alert: High Failed Authentication Attempts" \
      --message "Failed authentication attempts: $FAILED_AUTHS in last 5 minutes"
fi

echo "$(date): Health check completed" >> $LOG_FILE
```


`12. Troubleshooting Guide`
---------------------------

### `12.1 Common Issues and Resolutions`

#### `Issue 1: User Cannot Connect`

`Symptoms:`

* `Connection timeout`
* `Authentication failures`
* `Permission denied errors`

`Diagnosis:`


```
# Check server status
aws transfer describe-server --server-id $SERVER_ID --query 'Server.State'

# Check user exists
aws transfer describe-user --server-id $SERVER_ID --user-name $USERNAME

# Check security group rules
aws ec2 describe-security-groups --group-ids $SECURITY_GROUP_ID

# Test connectivity
telnet sftp.hrp.example.com 22
```


`Resolution:`

1. `Verify server is ONLINE`
2. `Check user exists and SSH key is correct`
3. `Verify security group allows source IP`
4. `Check DNS resolution`
5. `Verify IAM role permissions`

#### `Issue 2: Files Not Replicating to DR`

`Symptoms:`

* `Files uploaded but not appearing in DR bucket`
* `High replication lag`
* `Replication errors in CloudWatch`

`Diagnosis:`


```
# Check replication configuration
aws s3api get-bucket-replication --bucket $PRIMARY_BUCKET

# Check replication metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name ReplicationLatency \
  --dimensions Name=SourceBucket,Value=$PRIMARY_BUCKET \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Maximum

# Check IAM role permissions
aws iam get-role-policy --role-name S3ReplicationRole-SFTP --policy-name S3ReplicationPolicy
```


`Resolution:`

1. `Verify replication configuration is enabled`
2. `Check IAM role has correct permissions`
3. `Verify KMS key permissions for encryption`
4. `Check S3 bucket versioning is enabled`
5. `Review CloudWatch Logs for replication errors`

#### `Issue 3: DNS Not Failing Over`

`Symptoms:`

* `Primary endpoint down but DNS still pointing to it`
* `Health check not detecting failure`
* `Users unable to connect during outage`

`Diagnosis:`


```
# Check health check status
aws route53 get-health-check-status --health-check-id $HEALTH_CHECK_ID

# Check DNS records
aws route53 list-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --query "ResourceRecordSets[?Name=='sftp.hrp.example.com.']"

# Test DNS resolution
nslookup sftp.hrp.example.com
dig sftp.hrp.example.com
```


`Resolution:`

1. `Verify health check is enabled and configured correctly`
2. `Check health check is associated with primary DNS record`
3. `Verify failover routing policy is configured`
4. `Check TTL is set appropriately (60 seconds recommended)`
5. `Manually trigger failover if needed`

#### `Issue 4: High Latency or Slow Transfers`

`Symptoms:`

* `Slow file uploads/downloads`
* `Connection timeouts`
* `High transfer times`

`Diagnosis:`


```
# Check Transfer Family metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Transfer \
  --metric-name BytesIn \
  --dimensions Name=ServerId,Value=$SERVER_ID \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# Check S3 performance
aws s3api get-bucket-metrics-configuration --bucket $PRIMARY_BUCKET

# Test network latency
ping sftp.hrp.example.com
traceroute sftp.hrp.example.com
```


`Resolution:`

1. `Check network connectivity and bandwidth`
2. `Verify S3 bucket is in correct region`
3. `Check for S3 throttling or rate limits`
4. `Consider using S3 Transfer Acceleration`
5. `Review client-side network configuration`

### `12.2 Emergency Contacts`

#### `Emergency Contact List`

| `Role` | `Contact` | `Phone` | `Email` |
| --- | --- | --- | --- |
| `SFTP Administrator` | `[Name]` | `[Phone]` | `[Email]` |
| `Infrastructure Lead` | `[Name]` | `[Phone]` | `[Email]` |
| `Network Team` | `[Name]` | `[Phone]` | `[Email]` |
| `Operations Manager` | `[Name]` | `[Phone]` | `[Email]` |

`13. Appendices`
----------------

### `13.1 Glossary`

| `Term` | `Definition` |
| --- | --- |
| `AWS Transfer Family` | `Fully managed service for SFTP, FTPS, and FTP file transfers` |
| `S3 CRR` | `S3 Cross-Region Replication - automatic replication of objects across regions` |
| `RTO` | `Recovery Time Objective - Maximum acceptable downtime` |
| `RPO` | `Recovery Point Objective - Maximum acceptable data loss` |
| `VPC Endpoint` | `Private connection between VPC and AWS services` |
| `Elastic IP` | `Static public IPv4 address for AWS resources` |
| `Route 53` | `AWS DNS and traffic management service` |
| `Health Check` | `Automated monitoring of endpoint availability` |