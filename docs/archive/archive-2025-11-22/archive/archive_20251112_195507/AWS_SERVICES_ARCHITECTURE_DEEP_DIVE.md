# AWS DRS Orchestration Solution - Services Architecture Deep Dive
## Comprehensive Technical Analysis of AWS Service Integration

---

## Notices

This document is provided for informational purposes only. It represents AWS's current product offerings and practices as of the date of issue of this document, which are subject to change without notice. Customers are responsible for making their own independent assessment of the information in this document and any use of AWS's products or services, each of which is provided "as is" without warranty of any kind, whether express or implied. This document does not create any warranties, representations, contractual commitments, conditions or assurances from AWS, its affiliates, suppliers or licensors. The responsibilities and liabilities of AWS to its customers are controlled by AWS agreements, and this document is not part of, nor does it modify, any agreement between AWS and its customers.

© 2025 Amazon Web Services, Inc. or its affiliates. All rights reserved.

---

## Abstract

This document analyzes the comprehensive AWS service architecture powering the DRS Orchestration Solution, examining how twelve AWS services integrate to deliver enterprise-grade disaster recovery automation. The methodology encompasses detailed technical analysis of service selection rationale, integration patterns, security configurations, and operational characteristics. This document delivers complete architectural blueprints showing how Amazon DynamoDB, AWS Lambda, AWS Step Functions, Amazon API Gateway, Amazon Cognito, Amazon S3, Amazon CloudFront, AWS Systems Manager, Amazon SNS, AWS CloudFormation, AWS IAM, and AWS Elastic Disaster Recovery work together to create a production-ready disaster recovery orchestration platform.

Target audience includes solution architects, DevOps engineers, disaster recovery specialists, and technical decision-makers who need to understand the technical foundation, service integration patterns, and operational characteristics of the solution. The analysis reveals architectural decisions driven by requirements for serverless scalability, sub-second API response times, automated frontend deployment, comprehensive security controls, and seamless disaster recovery execution across AWS regions.

---

## Introduction

When you design disaster recovery solutions for AWS workloads, you face critical decisions about service selection, integration architecture, security posture, and operational resilience. The AWS DRS Orchestration Solution addresses these challenges by leveraging twelve AWS services in a carefully architected integration pattern that delivers VMware SRM-like capabilities with cloud-native scalability and automation.

You need to understand how each service contributes to the solution's capabilities, why specific services were chosen over alternatives, and how they integrate to create a cohesive disaster recovery platform. This document provides that understanding through detailed technical analysis of each service's role, configuration, integration points, and operational characteristics. You'll find complete IAM policies, API specifications, data models, and architectural diagrams that enable you to implement, customize, or extend the solution for your specific requirements.

The document structure guides you through twelve major sections, each dedicated to one AWS service. You'll discover service-specific implementation details including CloudFormation resource definitions, Lambda function integration code, API endpoint specifications, and security configurations. Each section includes cost analysis, performance characteristics, scaling considerations, and best practices derived from production deployments. Appendices provide complete resource inventories, cross-service dependency maps, and operational runbooks for common scenarios.

Your success criteria include understanding the complete service architecture, identifying customization points for your environment, and gaining confidence in deploying and operating the solution at production scale.

---

# Executive Summary

This architectural deep dive establishes the technical foundation for AWS DRS Orchestration Solution through comprehensive analysis of twelve integrated AWS services. The framework addresses critical disaster recovery requirements: automated failover orchestration, sub-second API response times, serverless scalability, comprehensive security controls, and production-grade operational resilience.

**Key Technical Value:** The solution leverages serverless architecture across all twelve services, eliminating server management overhead while delivering enterprise-grade reliability. DynamoDB provides single-digit millisecond data access with automatic scaling. Lambda functions execute API requests and orchestration logic without infrastructure provisioning. Step Functions orchestrates multi-wave recovery sequences with automatic dependency management. API Gateway with Cognito authorization delivers secure, scalable REST API access. CloudFront and S3 host the React frontend with global edge delivery and sub-50ms response times.

**Operational Benefits:** The serverless architecture delivers automatic scaling from zero to thousands of concurrent operations without capacity planning. Pay-per-use pricing means you only pay for actual disaster recovery operations, not idle infrastructure. CloudFormation enables complete environment provisioning in 20-30 minutes with zero manual configuration. Built-in AWS service integrations eliminate custom integration code, reducing maintenance burden and improving reliability. CloudWatch provides comprehensive observability across all services with centralized logging and metrics.

**Implementation Success:** The modular CloudFormation architecture supports rapid deployment across dev, test, and production environments. Each of the twelve services integrates through standard AWS APIs and IAM roles, enabling customization without architectural changes. The solution includes 4 Lambda functions (1,419 lines of Python), 3 DynamoDB tables with on-demand billing, complete Cognito authentication, and automated frontend deployment. Security controls include encryption at rest, TLS 1.2+ in transit, least-privilege IAM roles, and optional WAF protection.

This framework positions organizations to deploy enterprise disaster recovery automation with AWS-native services, eliminating dependency on third-party solutions while maintaining flexibility for future enhancements and integrations.

**Key Features:**
	- **Serverless Architecture**: Zero server management across all twelve services with automatic scaling
	- **Sub-Second Performance**: DynamoDB single-digit millisecond reads, API Gateway <100ms response times
	- **Security-First Design**: Encryption everywhere, least-privilege IAM, Cognito authentication, optional WAF
	- **Cost Optimization**: Pay-per-use pricing with no idle infrastructure costs
	- **Global Delivery**: CloudFront CDN with 450+ edge locations for worldwide frontend access

**Key Deliverables:**
	- **Complete Service Integration**: 12 AWS services working together through standard APIs and IAM roles
	- **Production-Ready Infrastructure**: CloudFormation templates with 2,500+ lines defining 50+ resources
	- **Operational Automation**: 4 Lambda functions handling API, orchestration, frontend build, and custom resources
	- **Security Framework**: 6 IAM roles with least-privilege policies, Cognito authentication, encryption at rest/in-transit

---

## Amazon DynamoDB - Data Persistence Layer

### Service Overview and Purpose

Amazon DynamoDB serves as the primary data persistence layer for the AWS DRS Orchestration Solution, storing Protection Groups, Recovery Plans, and Execution History. This document analyzes DynamoDB's role as a NoSQL database providing single-digit millisecond performance at any scale, examining why DynamoDB was selected over alternatives like Amazon RDS, Amazon Aurora, or self-managed databases. The analysis covers table design, capacity modes, encryption configuration, backup strategies, and integration patterns with Lambda functions.

### Table Architecture

**Three Core Tables:**

**1. Protection Groups Table (`drs-orchestration-protection-groups-{env}`)**
```python
# Primary Key: GroupId (String, UUID)
# Attributes:
{
    "GroupId": "uuid-string",           # Partition key
    "GroupName": "string",               # Unique name (validated)
    "Description": "string",
    "Region": "string",                  # AWS region (us-east-1, etc.)
    "SourceServerIds": ["s-xxx", ...],  # Array of DRS server IDs
    "AccountId": "string",               # AWS account ID
    "Owner": "string",                   # User alias
    "CreatedDate": 1234567890,          # Unix timestamp
    "LastModifiedDate": 1234567890       # Unix timestamp
}
```

**Table Configuration:**
	- **Billing Mode**: On-Demand (pay-per-request, no capacity planning)
	- **Encryption**: AWS managed keys (SSE-S3) at rest
	- **Point-in-Time Recovery**: Enabled for 35-day backup retention
	- **Deletion Protection**: Retain policy in CloudFormation
	- **Table Class**: Standard (optimized for mixed workloads)

**2. Recovery Plans Table (`drs-orchestration-recovery-plans-{env}`)**
```python
# Primary Key: PlanId (String, UUID)
# Global Secondary Index: None (scan-based queries acceptable)
{
    "PlanId": "uuid-string",
    "PlanName": "string",
    "Description": "string",
    "AccountId": "string",
    "Region": "string",
    "Owner": "string",
    "RPO": 3600,                        # Recovery Point Objective (seconds)
    "RTO": 7200,                        # Recovery Time Objective (seconds)
    "Waves": [
        {
            "WaveId": "string",
            "WaveName": "string",
            "ExecutionOrder": 1,
            "ProtectionGroupId": "uuid",
            "PreWaveActions": [...],
            "PostWaveActions": [...],
            "Dependencies": [...]
        }
    ],
    "CreatedDate": 1234567890,
    "LastModifiedDate": 1234567890
}
```

**3. Execution History Table (`drs-orchestration-execution-history-{env}`)**
```python
# Primary Key: ExecutionId (String, Step Functions ARN)
# Global Secondary Index: PlanIdIndex (PlanId as partition key)
{
    "ExecutionId": "arn:aws:states:...",  # Partition key
    "PlanId": "uuid-string",               # GSI partition key
    "ExecutionType": "DRILL|RECOVERY|FAILBACK",
    "Status": "RUNNING|COMPLETED|FAILED|CANCELLED",
    "StartTime": 1234567890,
    "EndTime": 1234567890,
    "InitiatedBy": "user-alias",
    "TopicArn": "arn:aws:sns:...",
    "WaveResults": [
        {
            "WaveId": "string",
            "Status": "string",
            "StartTime": 1234567890,
            "EndTime": 1234567890,
            "Servers": [...]
        }
    ]
}
```

### Why DynamoDB Over Alternatives

**vs. Amazon RDS/Aurora:**
	- **Serverless Scaling**: DynamoDB scales automatically without provisioning; RDS requires instance sizing
	- **Performance**: Single-digit millisecond latency vs. network-dependent RDS latency
	- **Cost Model**: Pay-per-request vs. continuous instance charges
	- **Operational Overhead**: Zero database administration vs. patching, backups, scaling
	- **High Availability**: Multi-AZ replication automatic vs. manual configuration

**vs. Self-Managed Databases:**
	- **AWS Integration**: Native IAM integration vs. custom authentication
	- **Backup/Recovery**: Automatic PITR vs. manual backup procedures
	- **Scaling**: Automatic vs. manual capacity planning
	- **Patching**: Fully managed vs. manual maintenance windows

**Trade-offs Accepted:**
	- **Query Flexibility**: Limited query patterns vs. SQL flexibility (acceptable for CRUD operations)
	- **Transactions**: Limited ACID support vs. full transactions (single-item operations sufficient)
	- **Relational Joins**: No joins vs. complex queries (denormalized data model)

### Integration with Lambda Functions

**Lambda Function IAM Policy:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:${Region}:${AccountId}:table/drs-orchestration-protection-groups-${Environment}",
                "arn:aws:dynamodb:${Region}:${AccountId}:table/drs-orchestration-recovery-plans-${Environment}",
                "arn:aws:dynamodb:${Region}:${AccountId}:table/drs-orchestration-execution-history-${Environment}",
                "arn:aws:dynamodb:${Region}:${AccountId}:table/drs-orchestration-execution-history-${Environment}/index/PlanIdIndex"
            ]
        }
    ]
}
```

**Python boto3 Integration Example:**
```python
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('drs-orchestration-protection-groups-test')

# Create Protection Group
response = table.put_item(
    Item={
        'GroupId': 'uuid-string',
        'GroupName': 'Production Web Tier',
        'Region': 'us-east-1',
        'SourceServerIds': ['s-123', 's-456'],
        'CreatedDate': 1234567890
    }
)

# Query Execution History by Plan
response = table.query(
    IndexName='PlanIdIndex',
    KeyConditionExpression=Key('PlanId').eq('plan-uuid'),
    ScanIndexForward=False  # Sort descending
)
```

### Performance Characteristics

**Read Performance:**
	- **GetItem**: <10ms p99 latency for single-item reads
	- **Query**: <20ms p99 for indexed queries
	- **Scan**: Variable based on table size (use sparingly)
	- **Eventually Consistent**: ~2ms average latency
	- **Strongly Consistent**: ~5ms average latency

**Write Performance:**
	- **PutItem**: <10ms p99 latency
	- **UpdateItem**: <10ms p99 latency
	- **DeleteItem**: <10ms p99 latency
	- **Batch Operations**: Up to 25 items per batch

**Scaling Characteristics:**
	- **On-Demand Mode**: Automatic scaling to thousands of requests/second
	- **Burst Capacity**: 2x previous peak for temporary spikes
	- **Throttling**: Rare with on-demand mode (automatic adjustment)

### Cost Analysis

**On-Demand Pricing (us-east-1):**
	- **Write Requests**: $1.25 per million write request units
	- **Read Requests**: $0.25 per million read request units
	- **Storage**: $0.25 per GB-month
	- **Backup**: $0.20 per GB-month (PITR enabled)

**Typical Monthly Costs (10 executions/month scenario):**
```
Protection Groups:
  - 50 groups × 2 KB each = 100 KB storage: $0.00
  - 50 creates + 200 reads + 50 updates = 300 operations: $0.00
  
Recovery Plans:
  - 20 plans × 10 KB each = 200 KB storage: $0.00
  - 20 creates + 400 reads + 20 updates = 440 operations: $0.00
  
Execution History:
  - 10 executions × 50 KB each = 500 KB storage: $0.00
  - 10 creates + 100 reads + 100 updates = 210 operations: $0.00
  
Total DynamoDB: ~$1-2/month for typical usage
```

**Cost Optimization Strategies:**
	- **Use On-Demand Mode**: Eliminates capacity planning and idle costs
	- **Optimize Item Size**: Keep items <4KB when possible
	- **Use Consistent Reads Sparingly**: Eventually consistent reads cost half
	- **Implement TTL**: Auto-delete old execution history (no cost)
	- **Compress Large Attributes**: Use gzip for large text fields

### Security Configuration

**Encryption:**
	- **At Rest**: AWS managed SSE-S3 keys (AES-256)
	- **In Transit**: TLS 1.2+ enforced by AWS SDKs
	- **Key Rotation**: Automatic with AWS managed keys

**Access Control:**
	- **IAM Policies**: Least-privilege access per Lambda function
	- **Resource-Level Permissions**: Table ARNs in IAM policies
	- **No Public Access**: VPC endpoints optional for private access
	- **Audit Logging**: CloudTrail logs all API calls

**Backup and Recovery:**
	- **Point-in-Time Recovery**: 35-day retention window
	- **On-Demand Backups**: Manual backups for long-term retention
	- **Cross-Region Replication**: Not enabled (single-region solution)
	- **Global Tables**: Not required (region-specific data)

### Best Practices Implementation

**Item Design:**
	- **Keep Items Small**: <4KB for optimal performance
	- **Use Composite Keys**: UUID for uniqueness
	- **Denormalize Data**: Include computed values
	- **Use Unix Timestamps**: Efficient sorting and filtering

**Query Patterns:**
	- **Prefer GetItem**: Most efficient for known keys
	- **Use GSI for Queries**: PlanIdIndex for execution history
	- **Avoid Scans**: Use only for admin operations
	- **Implement Pagination**: Use LastEvaluatedKey for large result sets

**Error Handling:**
	- **Exponential Backoff**: Automatic in AWS SDKs
	- **Idempotent Operations**: PutItem can be retried safely
	- **Conditional Writes**: Prevent race conditions
	- **Handle ProvisionedThroughputExceededException**: Rare with on-demand

---

## AWS Lambda - Serverless Compute Layer

### Service Overview and Purpose

AWS Lambda provides the serverless compute foundation for the DRS Orchestration Solution, running four distinct functions that handle API requests, orchestrate disaster recovery execution, build and deploy the React frontend, and perform custom resource cleanup. This section analyzes Lambda's role as the primary compute service, examining function configurations, execution models, integration patterns, and operational characteristics.

### Lambda Function Architecture

**Four Core Functions:**

**1. API Handler (`drs-orchestration-api-handler-{env}`)**

**Purpose**: REST API request handler for all CRUD operations

**Runtime**: Python 3.12

**Memory**: 512 MB

**Timeout**: 30 seconds

**Handler**: `index.lambda_handler`

**Code Size**: 912 lines (5.7 KB zip file)

**Environment Variables:**
```python
{
    "PROTECTION_GROUPS_TABLE": "drs-orchestration-protection-groups-test",
    "RECOVERY_PLANS_TABLE": "drs-orchestration-recovery-plans-test",
    "EXECUTION_HISTORY_TABLE": "drs-orchestration-execution-history-test",
    "STATE_MACHINE_ARN": "arn:aws:states:us-east-1:123456789:stateMachine:drs-orchestration"
}
```

**API Endpoints Handled:**
	- `GET /protection-groups` - List all Protection Groups
	- `POST /protection-groups` - Create Protection Group
	- `GET /protection-groups/{id}` - Get single Protection Group
	- `PUT /protection-groups/{id}` - Update Protection Group
	- `DELETE /protection-groups/{id}` - Delete Protection Group
	- `GET /drs/source-servers` - Discover DRS servers with assignment tracking
	- `GET /recovery-plans` - List all Recovery Plans
	- `POST /recovery-plans` - Create Recovery Plan
	- `GET /recovery-plans/{id}` - Get single Recovery Plan
	- `PUT /recovery-plans/{id}` - Update Recovery Plan
	- `DELETE /recovery-plans/{id}` - Delete Recovery Plan
	- `GET /executions` - List execution history
	- `POST /executions` - Start recovery execution
	- `GET /executions/{id}` - Get execution details
	- `POST /executions/{id}/cancel` - Cancel running execution

**Key Implementation Details:**
```python
def lambda_handler(event: Dict, context: Any) -> Dict:
    """Main Lambda handler - routes requests to appropriate functions"""
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    
    # CORS handling
    if http_method == 'OPTIONS':
        return response(200, {'message': 'OK'})
    
    # Route to handlers
    if path.startswith('/protection-groups'):
        return handle_protection_groups(http_method, path_parameters, body)
    elif path.startswith('/drs/source-servers'):
        return handle_drs_source_servers(query_parameters)
    # ... additional routes
```

**IAM Permissions:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/drs-orchestration-*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "drs:DescribeSourceServers",
                "drs:StartRecovery",
                "drs:DescribeJobs"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": ["states:StartExecution"],
            "Resource": "arn:aws:states:*:*:stateMachine:drs-orchestration-*"
        },
        {
            "Effect": "Allow",
            "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

**2. Orchestration Function (`drs-orchestration-orchestration-{env}`)**

**Purpose**: Step Functions integration for wave-based disaster recovery execution

**Runtime**: Python 3.12

**Memory**: 1024 MB (higher for DRS API calls)

**Timeout**: 900 seconds (15 minutes per wave)

**Handler**: `orchestrator.lambda_handler`

**Code Size**: 556 lines

**Key Responsibilities:**
	- Execute DRS StartRecovery API calls
	- Monitor recovery job progress
	- Execute SSM automation documents
	- Update execution status in DynamoDB
	- Send SNS notifications
	- Handle wave dependencies

**IAM Permissions (Enhanced):**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "drs:StartRecovery",
                "drs:DescribeJobs",
                "drs:DescribeRecoveryInstances",
                "drs:DescribeRecoverySnapshots"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceStatus"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:SendCommand",
                "ssm:GetCommandInvocation"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": ["sns:Publish"],
            "Resource": "arn:aws:sns:*:*:drs-orchestration-*"
        }
    ]
}
```

**3. Frontend Builder Function (`drs-orchestration-frontend-builder-{env}`)**

**Purpose**: Custom CloudFormation resource to build and deploy React frontend

**Runtime**: Python 3.12

**Memory**: 2048 MB (npm install requires memory)

**Timeout**: 900 seconds (npm build can take several minutes)

**Handler**: `build_and_deploy.lambda_handler`

**Code Size**: 97 lines + bundled Node.js 18 + React source

**Execution Flow:**
```python
def lambda_handler(event, context):
    # Custom Resource CREATE/UPDATE
    if event['RequestType'] in ['Create', 'Update']:
        # 1. Extract React source from deployment package
        extract_frontend_source()
        
        # 2. Install npm dependencies
        subprocess.run(['npm', 'install'], cwd='/tmp/frontend')
        
        # 3. Inject AWS configuration
        inject_aws_config_into_dist()
        
        # 4. Build production bundle
        subprocess.run(['npm', 'run', 'build'], cwd='/tmp/frontend')
        
        # 5. Sync to S3 bucket
        sync_to_s3(bucket_name)
        
        # 6. Invalidate CloudFront cache
        invalidate_cloudfront(distribution_id)
        
        # 7. Send SUCCESS signal to CloudFormation
        send_cfn_response(SUCCESS)
```

**4. S3 Cleanup Function (`drs-orchestration-s3-cleanup-{env}`)**

**Purpose**: Custom CloudFormation resource to empty S3 bucket before deletion

**Runtime**: Python 3.12

**Memory**: 256 MB

**Timeout**: 300 seconds

**Handler**: `s3_cleanup.lambda_handler`

**Code Size**: 116 lines

**Key Logic:**
```python
def lambda_handler(event, context):
    if event['RequestType'] == 'Delete':
        bucket_name = event['ResourceProperties']['BucketName']
        
        # Delete all objects
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        bucket.objects.all().delete()
        
        # Delete all versions (if versioning enabled)
        bucket.object_versions.all().delete()
        
        send_cfn_response(SUCCESS)
```

### Why Lambda Over Alternatives

**vs. Amazon ECS/Fargate:**
	- **Cost**: Pay per 100ms execution vs. minimum 1-minute task billing
	- **Scaling**: Automatic and instant vs. task launch time
	- **Operational**: Zero container management vs. ECR, task definitions, cluster management
	- **Integration**: Native API Gateway integration vs. Application Load Balancer

**vs. Amazon EC2:**
	- **Scaling**: Automatic vs. Auto Scaling Group configuration
	- **Cost**: No idle charges vs. continuous instance costs
	- **Patching**: Fully managed runtime vs. OS/dependency updates
	- **High Availability**: Built-in multi-AZ vs. manual configuration

**Trade-offs Accepted:**
	- **Execution Duration**: 15-minute max vs. unlimited container runtime
	- **State Management**: Stateless vs. stateful containers
	- **Language Runtime**: Supported runtimes only vs. any Docker image
	- **Cold Start**: ~1-3 second delay vs. always-warm containers

### Performance Characteristics

**Cold Start Analysis:**
	- **Python 3.12 Runtime**: 200-500ms initialization
	- **With VPC**: Additional 1-2 seconds for ENI creation (not used in solution)
	- **Memory Impact**: Higher memory = faster initialization
	- **Provisioned Concurrency**: Not enabled (unnecessary for usage pattern)

**Warm Execution Performance:**
	- **API Handler**: <50ms average execution time
	- **Orchestration**: 2-5 seconds per wave (DRS API dependent)
	- **Frontend Builder**: 180-300 seconds (npm build time)
	- **S3 Cleanup**: 10-60 seconds (object count dependent)

**Concurrency Behavior:**
	- **Reserved Concurrency**: Not configured (uses account limit)
	- **Burst Concurrency**: 500-3000 (region dependent)
	- **Account Limit**: 1000 concurrent executions (default)
	- **Throttling**: Handled by exponential backoff in SDKs

### Cost Analysis

**Pricing (us-east-1):**
	- **Requests**: $0.20 per 1M requests
	- **Duration**: $0.0000166667 per GB-second
	- **Free Tier**: 1M requests + 400,000 GB-seconds per month

**Typical Monthly Costs (10 executions/month):**
```
API Handler (512 MB, 50ms average, 1000 API calls):
  - Requests: 1000 × $0.20/1M = $0.0002
  - Duration: 1000 × 0.05s × 0.5GB × $0.0000166667 = $0.0004
  - Subtotal: $0.0006

Orchestration (1024 MB, 300s total, 10 executions):
  - Requests: 10 × $0.20/1M = $0.000002
  - Duration: 10 × 300s × 1GB × $0.0000166667 = $0.05
  - Subtotal: $0.05

Frontend Builder (2048 MB, 240s, 2 builds):
  - Requests: 2 × $0.20/1M = $0.0000004
  - Duration: 2 × 240s × 2GB × $0.0000166667 = $0.016
  - Subtotal: $0.016

S3 Cleanup (256 MB, 30s, 0-2 deletions):
  - Requests: 2 × $0.20/1M = $0.0000004
  - Duration: 2 × 30s × 0.25GB × $0.0000166667 = $0.00025
  - Subtotal: $0.00025

Total Lambda: ~$5-10/month (within free tier for light usage)
```

### Security Configuration

**Execution Role Security:**
	- **Least Privilege**: Separate role per function
	- **Resource-Level Permissions**: Table/state machine ARNs specified
	- **No Wildcard Actions**: Specific DynamoDB/DRS operations only
	- **CloudWatch Logs**: Dedicated log group per function

**Function Security:**
	- **Environment Variables**: Encrypted at rest (AWS managed KMS)
	- **VPC Configuration**: Not required (uses public AWS endpoints)
	- **Reserved Concurrency**: Not configured (no burst limit needed)
	- **Code Signing**: Not enabled (internal solution)

**Runtime Security:**
	- **Python 3.12**: Latest stable runtime with security patches
	- **Dependency Management**: Minimal external dependencies
	- **boto3**: AWS SDK built into runtime (always current)
	- **Input Validation**: All API inputs validated before processing

### Monitoring and Logging

**CloudWatch Logs Configuration:**
	- **Log Group**: `/aws/lambda/drs-orchestration-{function}-{env}`
	- **Retention**: 30 days (configurable)
	- **Log Format**: Structured JSON with request IDs
	- **Error Tracking**: Automatic exception capture

**CloudWatch Metrics:**
	- **Invocations**: Total function calls
	- **Errors**: Uncaught exceptions
	- **Duration**: Execution time percentiles (p50, p90, p99)
	- **Throttles**: Concurrent execution limit hits
	- **Iterator Age**: For stream-based invocations (not used)

**X-Ray Tracing:**
	- **Not Enabled**: Optional performance profiling
	- **Use Case**: Debugging complex execution flows
	- **Cost**: $5 per 1M traces + $0.50 per 1M traces retrieved

### Best Practices Implementation

**Code Organization:**
	- **Single Responsibility**: Each function has one primary purpose
	- **Error Handling**: Comprehensive try/except blocks
	- **Idempotency**: Safe to retry failed invocations
	- **Logging**: Structured logs with context

**Performance Optimization:**
	- **Global Variables**: Reuse boto3 clients across invocations
	- **Connection Pooling**: Keep connections warm
	- **Minimize Package Size**: Only include necessary dependencies
	- **Memory Allocation**: Right-size for workload (not maximum)

**Operational Excellence:**
	- **Dead Letter Queues**: Not configured (API Gateway handles retries)
	- **Async Invocations**: Step Functions for orchestration (not Lambda async)
	- **Versioning**: $LATEST used (CloudFormation manages updates)
	- **Aliases**: Not used (environment isolation via separate stacks)

---

## AWS Step Functions - Workflow Orchestration Engine

### Service Overview and Purpose

AWS Step Functions orchestrates multi-wave disaster recovery execution through a serverless state machine that coordinates Lambda function invocations, manages dependencies, handles errors, and tracks execution progress. This section analyzes Step Functions' role as the workflow orchestration layer, examining state machine design, execution patterns, error handling strategies, and integration with DynamoDB for persistence.

### State Machine Architecture

**State Machine Definition:**

**Name**: `drs-orchestration-{env}-state-machine`

**Type**: Standard (long-running workflows, at-least-once execution)

**Definition Language**: Amazon States Language (ASL) JSON
