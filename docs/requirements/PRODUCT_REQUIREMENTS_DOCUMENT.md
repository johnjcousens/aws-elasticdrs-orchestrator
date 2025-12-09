# Product Requirements Document
# AWS DRS Orchestration Solution

**Version**: 4.0  
**Date**: December 2025  
**Status**: Production Deployed  
**Document Owner**: AWS DRS Orchestration Team

---

## Executive Summary

AWS DRS Orchestration is an enterprise-grade, serverless disaster recovery orchestration platform built on AWS Elastic Disaster Recovery (DRS). The solution enables organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, real-time monitoring, and comprehensive audit trails.

### Problem Statement

AWS DRS provides continuous replication but lacks native orchestration for multi-tier applications requiring coordinated recovery sequences. Organizations need wave-based execution, dependency management, and automated monitoring capabilities.

### Solution Overview

AWS DRS Orchestration provides complete orchestration on top of AWS DRS:
- Protection Groups for logical server organization
- Recovery Plans with wave-based execution
- Step Functions-driven automation
- React + CloudScape UI with real-time updates
- Complete REST API for automation

---

## Architecture

### AWS Services

**Core**:
- DynamoDB: 3 tables (protection-groups, recovery-plans, execution-history)
- Lambda: 5 functions (API handler, orchestration-stepfunctions, execution-finder, execution-poller, frontend-builder)
- Step Functions: Workflow orchestration
- API Gateway: REST API with Cognito auth
- S3 + CloudFront: Static hosting
- AWS DRS: Core recovery service

**Infrastructure as Code**:
- CloudFormation: 7 nested stacks (master, database, lambda, api, step-functions, security, frontend)
- Single-command deployment
- Multi-region support (all AWS DRS-supported regions)

### Data Model

**Protection Groups**: `GroupId` (PK), `GroupName`, `Region`, `SourceServerIds[]`  
**Recovery Plans**: `PlanId` (PK), `PlanName`, `Waves[]`  
**Execution History**: `ExecutionId` (PK), `PlanId` (SK), `Status`, `Waves[]`

---

## Features

### 1. Protection Groups

Logical organization of DRS source servers.

**Capabilities**:
- Auto-discovery across all AWS DRS-supported regions
- Visual server selector with status indicators
- Single server per group constraint
- Real-time search and filtering

**UI**: CloudScape Table with CRUD operations, server assignment modal

**API**: `GET/POST/PUT/DELETE /protection-groups`, `GET /drs/source-servers`

### 2. Recovery Plans

Wave-based orchestration with dependencies.

**Capabilities**:
- Unlimited waves
- Sequential or parallel execution
- Wave dependencies with validation
- Drill and recovery modes

**UI**: Wave configuration form with Protection Group selection

**API**: `GET/POST/PUT/DELETE /recovery-plans`, `POST /executions`

### 3. Execution Engine

Step Functions-driven recovery automation.

**Flow**:
1. Validate plan and servers
2. For each wave: Start DRS recovery, poll job status, health checks
3. Update execution history
4. Move to next wave or complete

**Monitoring**: Real-time status polling every 3 seconds for active executions

**API**: `GET /executions`, `GET /executions/{id}`, `DELETE /executions/{id}`

### 4. User Interface

React 19.1 + TypeScript + CloudScape Design System

**Pages**:
- Login (Cognito)
- Getting Started (onboarding)
- Dashboard (metrics)
- Protection Groups (CRUD)
- Recovery Plans (wave config)
- History (execution monitoring)
- Execution Details (wave progress)

**Features**: Real-time updates, responsive design, WCAG 2.1 AA compliant

---

## Technical Specifications

### Frontend Stack
- React 19.1.1, TypeScript 5.9.3
- CloudScape 3.0.1148
- Vite 7.1.7
- AWS Amplify 6.15.8
- Axios 1.13.2
- React Router 7.9.5

### Backend Stack
- Python 3.12 Lambda runtime
- boto3 (AWS SDK)
- crhelper 2.0.11

### API Authentication
- Cognito JWT tokens
- Auto-refresh on expiration
- 401 handling with re-auth

### DRS Integration

**Critical Discovery**: DRS uses calling role's IAM permissions for EC2 operations.

**Required Permissions**:
```yaml
EC2Access:
  - ec2:DescribeInstances
  - ec2:CreateLaunchTemplate
  - ec2:CreateLaunchTemplateVersion
  - ec2:ModifyLaunchTemplate
  - ec2:DeleteLaunchTemplate
  - ec2:StartInstances
  - ec2:RunInstances
  - ec2:CreateVolume
  - ec2:AttachVolume

DRSAccess:
  - drs:*
  - drs:CreateRecoveryInstanceForDrs  # Critical
```

**Recovery Flow**:
1. Snapshot Creation (1-2 min)
2. Conversion Server Launch (1-2 min)
3. Launch Template Creation (< 1 min)
4. Recovery Instance Launch (1-2 min)

Total: ~15-20 minutes per wave

---

## Deployment

### Prerequisites
- AWS Account with DRS enabled
- DRS source servers replicating
- S3 bucket for artifacts
- Admin email for Cognito

### Deploy Command
```bash
aws cloudformation deploy \
  --template-url https://aws-drs-orchestration.s3.us-east-1.amazonaws.com/cfn/master-template.yaml \
  --stack-name drs-orchestration-dev \
  --parameter-overrides \
    ProjectName=drs-orchestration \
    Environment=dev \
    SourceBucket=aws-drs-orchestration \
    AdminEmail=admin@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Stack Outputs
- `CloudFrontURL`: Frontend URL
- `ApiEndpoint`: REST API
- `UserPoolId`: Cognito pool
- `UserPoolClientId`: App client

### Post-Deployment
1. Create Cognito admin user
2. Configure DRS source servers
3. Access CloudFront URL

---

## Success Metrics

### Operational
- RTO: <15 minutes
- RPO: <5 minutes (DRS native)
- Success Rate: >99.5%
- API Availability: >99.9%

### Cost
- Monthly: $12-40
- Per Server: <$0.50/month

### User Satisfaction
- Create Protection Group: <5 min
- Create Recovery Plan: <15 min
- Execute Drill: <30 min

---

## Known Issues & Solutions

### Issue: DRS Recovery Failures

**Symptom**: `UnauthorizedOperation` on EC2 actions

**Root Cause**: DRS uses calling role's permissions, not service-linked role

**Solution**: OrchestrationRole needs comprehensive EC2 permissions (see Technical Specifications)

**Reference**: DRS_COMPLETE_IAM_ANALYSIS.md

---

## Future Enhancements

### Phase 2
- Pre/post-wave automation (SSM, Lambda)
- VPC test isolation
- Automated drill scheduling
- PDF report generation

### Phase 3
- Reprotection workflows
- Multi-account hub-and-spoke
- Advanced CloudWatch dashboards
- Cost optimization

---

## Appendix

### AWS DRS Regional Availability

The solution supports disaster recovery orchestration in all AWS regions where Elastic Disaster Recovery (DRS) is available:

**Americas (5 regions)**: US East (N. Virginia, Ohio), US West (Oregon, N. California), Canada (Central)  
**Europe (6 regions)**: Ireland, London, Frankfurt, Paris, Stockholm, Milan  
**Asia Pacific (3 regions)**: Tokyo, Sydney, Singapore  

*Regional availability is determined by AWS DRS service, not the orchestration solution. As AWS expands DRS to additional regions, the solution automatically supports them.*

### Cost Breakdown
- Lambda: $1-5/month
- API Gateway: $3-10/month
- DynamoDB: $1-5/month
- CloudFront: $1-5/month
- S3: <$1/month
- Step Functions: $1-5/month
- Cognito: Free tier

### References
- [Deployment Guide](../guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md)
- [Architecture Design](../architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md)
- [DRS IAM Analysis](../../DRS_COMPLETE_IAM_ANALYSIS.md)
- [Testing Guide](../guides/TESTING_AND_QUALITY_ASSURANCE.md)
