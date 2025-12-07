# Product Requirements Document
# AWS DRS Orchestration Solution

**Version**: 3.0  
**Date**: December 2025  
**Status**: Production Release  
**Document Owner**: AWS DRS Orchestration Team

---

## Executive Summary

AWS DRS Orchestration is a cloud-native, serverless disaster recovery orchestration platform for AWS Elastic Disaster Recovery Service (DRS). The solution enables organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks.

### Core Capabilities

- **Protection Groups**: Logical grouping of DRS source servers with automatic discovery
- **Recovery Plans**: Wave-based orchestration with unlimited flexibility
- **Execution Engine**: Step Functions-driven recovery automation with real-time monitoring
- **Modern UI**: React-based frontend with AWS CloudScape Design System
- **API-First Design**: Complete REST API for automation and integration

### Business Value

- **Cost Efficiency**: Pay-per-use cloud-native pricing ($12-40/month operational cost)
- **Cloud Native**: Leverages AWS-managed services for reliability and scale
- **Platform Agnostic**: Agent-based replication supports any source platform
- **Automation Ready**: API-first design enables full DevOps integration
- **Enterprise Grade**: Production-ready disaster recovery orchestration

---

## Target Users

### Primary: DR Administrator
- Manages disaster recovery for 50-500+ servers
- Responsible for quarterly DR testing and documentation
- Needs automated recovery plan execution and testing
- Success criteria: Create Protection Groups in <5 minutes, execute drills without production impact

### Secondary: DevOps Engineer
- Integrates DR automation into CI/CD pipelines
- Automates pre/post-recovery validation scripts
- Needs RESTful API for all DR operations
- Success criteria: Full API coverage, CloudWatch integration

### Tertiary: IT Manager
- Reviews DR readiness and compliance
- Reports on DR capabilities to leadership
- Needs execution history and audit trails
- Success criteria: Complete audit trail, success metrics

---

## Feature Specifications

### 1. Protection Groups

Protection Groups provide logical organization of DRS source servers for recovery.

**Capabilities**:
- Automatic discovery of DRS source servers by AWS region (13 regions)
- Visual server selector with assignment status indicators
- Single server per group constraint (conflict prevention)
- Real-time search by hostname, Server ID, or Protection Group name
- 30-second auto-refresh for server status
- Case-insensitive unique name enforcement

**User Flow**:
1. User selects AWS region from dropdown
2. System auto-discovers DRS source servers with replication status
3. User creates Protection Group with descriptive name
4. User assigns available servers using visual selector
5. System validates no conflicts, saves configuration

### 2. Recovery Plans

Recovery Plans define the execution sequence for recovering Protection Groups.

**Capabilities**:
- Unlimited waves (no artificial constraints)
- Wave dependencies with explicit relationships
- Sequential or Parallel execution per wave
- Configurable wait times between waves (0-3600 seconds)
- Drill mode for non-disruptive testing
- Multi-Protection Group support per plan

**Wave Configuration**:
```
Wave 1: Database Primary (SEQUENTIAL)
Wave 2: Database Replicas (depends on Wave 1, PARALLEL)
Wave 3: Application Servers (depends on Wave 2, PARALLEL)
Wave 4: Web Servers (depends on Wave 3, PARALLEL)
```

### 3. Execution Engine

The execution engine coordinates recovery operations using AWS Step Functions.

**Capabilities**:
- Wave-based orchestration with dependency checking
- DRS StartRecovery API integration
- Job status monitoring (polling every 30 seconds)
- EC2 instance health checks post-launch
- Execution history persistence in DynamoDB
- Real-time status updates via polling
- Cancel/pause in-progress executions

**Execution Flow**:
1. User clicks "Execute Recovery Plan"
2. API validates plan and server readiness
3. Step Functions state machine initiated
4. For each wave: launch recovery, monitor jobs, health checks, wait
5. Mark execution complete
6. Update execution history

### 4. User Interface

Modern, responsive web application for DR management.

**Technology Stack**:
- React 18.3 with TypeScript 5.5
- AWS CloudScape Design System
- Vite 5.4 build system
- S3 + CloudFront hosting
- AWS Amplify for Cognito integration

**Pages**:
1. **Login**: Cognito authentication
2. **Getting Started**: Onboarding guide for new users
3. **Dashboard**: Overview metrics and quick actions
4. **Protection Groups**: CRUD operations with server discovery
5. **Recovery Plans**: Wave configuration and execution
6. **Executions**: Real-time monitoring and history
7. **Execution Details**: Wave progress and server status

**Key Features**:
- CloudScape Table with sorting, filtering, pagination
- Real-time execution progress with wave stepper
- Responsive design (desktop, tablet, mobile)
- WCAG 2.1 AA accessibility compliance

### 5. REST API

Complete REST API for automation and integration.

**Endpoints**:
- `GET/POST /protection-groups` - List/Create Protection Groups
- `GET/PUT/DELETE /protection-groups/{id}` - CRUD operations
- `GET/POST /recovery-plans` - List/Create Recovery Plans
- `GET/PUT/DELETE /recovery-plans/{id}` - CRUD operations
- `GET/POST /executions` - List/Start executions
- `GET /executions/{id}` - Get execution status
- `DELETE /executions/{id}` - Cancel execution
- `GET /drs/source-servers` - Discover DRS servers

**Authentication**: AWS Cognito with JWT tokens
**Rate Limiting**: 500 burst, 1000 sustained requests/second

---

## Technical Architecture

### AWS Services

**Core Services**:
- Amazon DynamoDB: Data persistence (3 tables)
- AWS Lambda: Serverless compute (4 functions)
- AWS Step Functions: Workflow orchestration
- Amazon API Gateway: REST API
- Amazon Cognito: User authentication
- Amazon S3: Static hosting
- Amazon CloudFront: CDN
- AWS Elastic Disaster Recovery: Core DR service

**Infrastructure**:
- CloudFormation: 6 nested stacks (~2,400 lines YAML)
- Single-command deployment via master template
- Multi-region support (13 DRS-enabled regions)

### Data Model

**Protection Groups Table**:
- Primary Key: `GroupId` (UUID)
- Attributes: `GroupName`, `Region`, `SourceServerIds[]`, `CreatedDate`, `LastModifiedDate`

**Recovery Plans Table**:
- Primary Key: `PlanId` (UUID)
- Attributes: `PlanName`, `Waves[]`, `Dependencies`, `CreatedDate`

**Execution History Table**:
- Primary Key: `ExecutionId` (UUID), `PlanId` (Sort Key)
- GSI: `StatusIndex` (Status, StartTime)
- Attributes: `Status`, `Waves[]`, `StartTime`, `EndTime`, `ExecutionType`

---

## Success Metrics

### Operational Metrics
- Recovery Time Objective (RTO): <15 minutes for critical applications
- Recovery Point Objective (RPO): <5 minutes (leveraging DRS sub-second replication)
- Recovery Success Rate: >99.5%
- API Availability: >99.9%

### Cost Metrics
- Monthly Operational Cost: $12-40/month
- Cost Per Protected Server: <$0.50/month/server

### User Satisfaction Metrics
- Time to Create Protection Group: <5 minutes
- Time to Create Recovery Plan: <10 minutes
- DR Test Execution Time: <30 minutes for 3-tier application

---

## Deployment

### Prerequisites
- AWS Account with DRS enabled
- DRS source servers configured and replicating
- S3 bucket for CloudFormation templates and Lambda packages
- Valid email for Cognito admin user

### Deployment Command
```bash
aws cloudformation deploy \
  --template-url https://{bucket}.s3.{region}.amazonaws.com/cfn/master-template.yaml \
  --stack-name dr-orchestrator-{env} \
  --parameter-overrides \
    ProjectName=dr-orchestrator \
    Environment={env} \
    SourceBucket={bucket} \
    AdminEmail={email} \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region {region}
```

### Stack Outputs
- `CloudFrontURL`: Frontend application URL
- `ApiEndpoint`: REST API endpoint
- `CognitoUserPoolId`: Cognito User Pool ID
- `CognitoClientId`: Cognito App Client ID

---

## Future Enhancements

### Phase 2 (Planned)
- Pre/Post Recovery Scripts (Lambda hooks, SSM documents)
- VPC Test Isolation for drill mode
- Automated drill scheduling
- PDF test report generation

### Phase 3 (Planned)
- Reprotection and failback workflows
- Multi-account hub-and-spoke deployment
- Advanced CloudWatch dashboards
- Cost optimization recommendations
