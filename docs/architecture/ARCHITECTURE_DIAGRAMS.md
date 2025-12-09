# Architecture Diagrams

Complete visual reference for AWS DRS Orchestration architecture, data flows, and component interactions.

## Overall Architecture

![AWS DRS Orchestration Architecture](AWS-DRS-Orchestration-Architecture.png)

*[View/Edit Source Diagram](AWS-DRS-Orchestration-Architecture.drawio)*

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Lambda Functions Architecture](#lambda-functions-architecture)
3. [Data Flow Diagrams](#data-flow-diagrams)
4. [DRS Integration Flow](#drs-integration-flow)
5. [Step Functions Orchestration](#step-functions-orchestration)
6. [Pause/Resume Flow](#pauseresume-flow)
7. [Deployment Architecture](#deployment-architecture)

---

## High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        User[User Browser]
        CF[CloudFront CDN]
        S3Frontend[S3 Static Hosting]
    end
    
    subgraph "Authentication"
        Cognito[Cognito User Pool<br/>45-min session timeout]
    end
    
    subgraph "API Layer"
        APIGW[API Gateway REST]
        CognitoAuth[Cognito Authorizer]
    end
    
    subgraph "Compute Layer - Lambda Functions"
        APIHandler[api-handler<br/>index.py]
        OrchSF[orchestration-stepfunctions<br/>orchestration_stepfunctions.py]
        ExecFinder[execution-finder<br/>execution_finder.py]
        ExecPoller[execution-poller<br/>execution_poller.py]
        FEBuilder[frontend-builder<br/>build_and_deploy.py]
    end
    
    subgraph "Orchestration"
        StepFn[Step Functions<br/>State Machine<br/>waitForTaskToken]
    end
    
    subgraph "Scheduling"
        EventBridge[EventBridge Rule<br/>1 minute schedule]
    end

    subgraph "Data Layer"
        DDBProtection[(protection-groups)]
        DDBPlans[(recovery-plans)]
        DDBHistory[(execution-history<br/>StatusIndex GSI)]
    end
    
    subgraph "AWS DRS Integration"
        DRS[AWS DRS Service]
        EC2Recovery[EC2 Recovery Instances]
    end
    
    subgraph "Monitoring"
        CWLogs[CloudWatch Logs]
        CWMetrics[CloudWatch Metrics]
    end
    
    User --> CF
    CF --> S3Frontend
    CF --> APIGW
    User --> Cognito
    Cognito --> CognitoAuth
    APIGW --> CognitoAuth
    CognitoAuth --> APIHandler
    
    APIHandler --> DDBProtection
    APIHandler --> DDBPlans
    APIHandler --> DDBHistory
    APIHandler --> StepFn
    APIHandler --> EC2Recovery
    
    StepFn --> OrchSF
    OrchSF --> DRS
    OrchSF --> DDBHistory
    
    EventBridge --> ExecFinder
    ExecFinder --> DDBHistory
    ExecFinder --> ExecPoller
    ExecPoller --> DRS
    ExecPoller --> DDBHistory
    
    DRS --> EC2Recovery
    
    APIHandler --> CWLogs
    OrchSF --> CWLogs
    ExecPoller --> CWLogs
    ExecPoller --> CWMetrics
    
    style APIHandler fill:#FF9900
    style OrchSF fill:#FF9900
    style ExecFinder fill:#FF9900
    style ExecPoller fill:#FF9900
    style StepFn fill:#E7157B
    style DRS fill:#527FFF
```

**Key Components:**

- **5 Lambda Functions**: API handler, orchestration-stepfunctions, execution finder, execution poller, frontend builder
- **3 DynamoDB Tables**: Protection groups, recovery plans, execution history (with StatusIndex GSI)
- **1 Step Functions State Machine**: Wave-based orchestration with `waitForTaskToken` for pause/resume
- **1 EventBridge Rule**: Triggers execution finder every 1 minute
- **Cognito User Pool**: JWT authentication with 45-minute session timeout

---

## Lambda Functions Architecture

```mermaid
graph LR
    subgraph "API Handler Lambda"
        API[api-handler<br/>120s timeout<br/>512 MB]
        APIRole[ApiHandlerRole]
    end
    
    subgraph "Orchestration Lambda"
        OrchSF[orchestration-stepfunctions<br/>120s timeout<br/>512 MB]
        OrchRole[OrchestrationRole]
    end
    
    subgraph "Execution Monitoring"
        Finder[execution-finder<br/>60s timeout<br/>256 MB]
        Poller[execution-poller<br/>120s timeout<br/>256 MB]
        FinderRole[ExecutionFinderRole]
        PollerRole[ExecutionPollerRole]
    end
    
    subgraph "Frontend Deployment"
        Builder[frontend-builder<br/>900s timeout<br/>2048 MB]
        BuilderRole[CustomResourceRole]
    end
    
    API --> APIRole
    OrchSF --> OrchRole
    Finder --> FinderRole
    Poller --> PollerRole
    Builder --> BuilderRole
    
    APIRole -.->|DynamoDB| Tables[(3 Tables)]
    APIRole -.->|DRS| DRSService[AWS DRS]
    APIRole -.->|Step Functions| SF[State Machine]
    APIRole -.->|EC2 Terminate| EC2[EC2 API]
    
    OrchRole -.->|DynamoDB| Tables
    OrchRole -.->|DRS| DRSService
    OrchRole -.->|EC2| EC2
    
    FinderRole -.->|DynamoDB Query| Tables
    FinderRole -.->|Invoke| Poller
    
    PollerRole -.->|DynamoDB Update| Tables
    PollerRole -.->|DRS| DRSService
    PollerRole -.->|CloudWatch| Metrics[Metrics]
    
    BuilderRole -.->|S3| S3Bucket[Frontend Bucket]
    BuilderRole -.->|CloudFront| CFDist[Distribution]
    
    style API fill:#FF9900
    style OrchSF fill:#FF9900
    style Finder fill:#FF9900
    style Poller fill:#FF9900
    style Builder fill:#FF9900
```

### Lambda Function Details

| Function | File | Timeout | Memory | Purpose |
|----------|------|---------|--------|---------|
| api-handler | index.py | 120s | 512 MB | REST API endpoints, DRS integration, EC2 terminate |
| orchestration-stepfunctions | orchestration_stepfunctions.py | 120s | 512 MB | Step Functions orchestration, wave execution, pause/resume |
| execution-finder | poller/execution_finder.py | 60s | 256 MB | Query StatusIndex GSI, invoke poller |
| execution-poller | poller/execution_poller.py | 120s | 256 MB | Poll DRS job status, update execution records |
| frontend-builder | build_and_deploy.py | 900s | 2048 MB | CloudFormation custom resource for frontend deployment |

---

## Data Flow Diagrams

### User Request Flow

```mermaid
sequenceDiagram
    participant User
    participant CloudFront
    participant S3
    participant APIGateway
    participant Cognito
    participant Lambda
    participant DynamoDB
    
    User->>CloudFront: HTTPS Request
    CloudFront->>S3: Fetch Static Assets
    S3-->>CloudFront: HTML/JS/CSS
    CloudFront-->>User: Frontend App
    
    User->>Cognito: Authenticate
    Cognito-->>User: JWT Token
    
    User->>APIGateway: API Request + JWT
    APIGateway->>Cognito: Validate Token
    Cognito-->>APIGateway: Token Valid
    APIGateway->>Lambda: Invoke Handler
    Lambda->>DynamoDB: Query/Update
    DynamoDB-->>Lambda: Data
    Lambda-->>APIGateway: Response
    APIGateway-->>User: JSON Response
```

### Execution Start Flow

```mermaid
sequenceDiagram
    participant User
    participant API as api-handler
    participant DDB as DynamoDB
    participant SF as Step Functions
    participant Orch as orchestration-stepfunctions
    participant DRS as AWS DRS
    
    User->>API: POST /executions
    API->>DDB: Validate Plan Exists
    DDB-->>API: Plan Data
    API->>DDB: Create Execution Record (PENDING)
    API->>SF: StartExecution
    SF-->>API: ExecutionArn
    API-->>User: ExecutionId
    
    SF->>Orch: Execute Wave 1
    Orch->>DDB: Update Status (INITIATED)
    Orch->>DRS: StartRecovery
    DRS-->>Orch: JobId
    Orch->>DDB: Store JobId, Update Status (POLLING)
```

---

## DRS Integration Flow

### Recovery Job Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: StartRecovery Called
    PENDING --> STARTED: Job Created
    STARTED --> LAUNCH_START: Conversion Begins
    LAUNCH_START --> LAUNCHING: Instance Launching
    LAUNCHING --> LAUNCHED: Recovery Complete
    LAUNCHING --> LAUNCH_FAILED: Error
    LAUNCH_FAILED --> [*]
    LAUNCHED --> [*]
```

### DRS API Integration

```mermaid
sequenceDiagram
    participant Lambda as orchestration-stepfunctions
    participant DRS as AWS DRS
    participant EC2 as EC2 Service
    
    Lambda->>DRS: StartRecovery(sourceServerIds)
    DRS->>EC2: Create Conversion Server
    EC2-->>DRS: Conversion Server Ready
    DRS->>EC2: CreateLaunchTemplate
    EC2-->>DRS: Template Created
    DRS->>EC2: RunInstances (Recovery)
    EC2-->>DRS: Instance Launched
    DRS-->>Lambda: JobId
    
    loop Poll Until Complete
        Lambda->>DRS: DescribeJobs(jobId)
        DRS-->>Lambda: Job Status
    end
```

**Critical IAM Note**: DRS uses the calling Lambda role's IAM permissions for all EC2 operations. The Lambda execution role must include:

- `drs:CreateRecoveryInstanceForDrs` (often missing)
- `ec2:CreateLaunchTemplate`, `ec2:CreateLaunchTemplateVersion`
- `ec2:RunInstances`, `ec2:TerminateInstances`
- Full list in [PRD Technical Specifications](../requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md#drs-integration)

---

## Step Functions Orchestration

### State Machine Definition

```mermaid
stateDiagram-v2
    [*] --> ValidatePlan
    ValidatePlan --> InitializeExecution
    InitializeExecution --> ProcessWave
    
    state ProcessWave {
        [*] --> CheckPauseConfig
        CheckPauseConfig --> WaitForResume: pauseBeforeWave=true
        CheckPauseConfig --> StartDRSRecovery: pauseBeforeWave=false
        WaitForResume --> StartDRSRecovery: Resume Signal
        StartDRSRecovery --> PollJobStatus
        PollJobStatus --> CheckJobComplete
        CheckJobComplete --> PollJobStatus: Not Complete
        CheckJobComplete --> WaveComplete: All LAUNCHED
        CheckJobComplete --> WaveFailed: Any FAILED
    }
    
    ProcessWave --> NextWave: More Waves
    NextWave --> ProcessWave
    ProcessWave --> ExecutionComplete: No More Waves
    ProcessWave --> ExecutionFailed: Wave Failed
    
    ExecutionComplete --> [*]
    ExecutionFailed --> [*]
```

### Execution Status Transitions

```mermaid
stateDiagram-v2
    [*] --> PENDING: Execution Created
    PENDING --> INITIATED: Step Functions Started
    INITIATED --> POLLING: DRS Job Started
    POLLING --> LAUNCHING: Servers Launching
    POLLING --> PAUSED: Pause Before Wave
    PAUSED --> POLLING: User Resumes
    LAUNCHING --> COMPLETED: All Waves Done
    LAUNCHING --> PARTIAL: Some Waves Failed
    LAUNCHING --> FAILED: Critical Failure
    POLLING --> CANCELLED: User Cancels
    PAUSED --> CANCELLED: User Cancels
    
    COMPLETED --> [*]
    PARTIAL --> [*]
    FAILED --> [*]
    CANCELLED --> [*]
```

---

## Pause/Resume Flow

The pause/resume mechanism uses Step Functions `waitForTaskToken` callback pattern, allowing executions to pause indefinitely (up to 1 year) until user intervention.

### Pause/Resume Sequence

```mermaid
sequenceDiagram
    participant SF as Step Functions
    participant Orch as orchestration-stepfunctions
    participant DDB as DynamoDB
    participant API as api-handler
    participant User
    
    Note over SF,Orch: Wave configured with pauseBeforeWave=true
    
    SF->>Orch: Execute Wave (with taskToken)
    Orch->>DDB: Store taskToken in execution record
    Orch->>DDB: Update status = PAUSED
    Orch-->>SF: (Lambda returns, SF waits for callback)
    
    Note over SF: Step Functions waiting for SendTaskSuccess
    Note over SF: Max wait: 1 year (31536000 seconds)
    
    User->>API: POST /executions/{id}/resume
    API->>DDB: Get execution record
    DDB-->>API: taskToken
    API->>SF: SendTaskSuccess(taskToken)
    SF->>Orch: Continue wave execution
    Orch->>DDB: Update status = POLLING
```

### Task Token Storage

```mermaid
flowchart LR
    subgraph "Step Functions"
        SF[State Machine]
        Token[taskToken generated]
    end
    
    subgraph "Lambda"
        Orch[orchestration-stepfunctions]
    end
    
    subgraph "DynamoDB"
        Exec[(execution-history)]
    end
    
    SF -->|"Invoke with taskToken"| Orch
    Orch -->|"Store taskToken"| Exec
    Orch -->|"Return (no callback yet)"| SF
    
    style Token fill:#E7157B
```

**Key Implementation Details**:

- Task token passed to Lambda via Step Functions context
- Token stored in DynamoDB `execution-history` table
- Maximum pause duration: 1 year (31536000 seconds)
- Resume triggers `SendTaskSuccess` with stored token
- Cancel triggers `SendTaskFailure` with stored token

---

## Terminate Instances Flow

After drill completion, users can terminate recovery EC2 instances to manage costs.

```mermaid
sequenceDiagram
    participant User
    participant API as api-handler
    participant DDB as DynamoDB
    participant EC2 as EC2 Service
    
    User->>API: POST /executions/{id}/terminate-instances
    API->>DDB: Get execution record
    DDB-->>API: Execution (status, instanceIds)
    
    alt Status not terminal
        API-->>User: 400 Bad Request
    else Already terminated
        API-->>User: 400 Already Terminated
    else Valid request
        API->>EC2: TerminateInstances(instanceIds)
        EC2-->>API: Termination Initiated
        API->>DDB: Update instancesTerminated=true
        API-->>User: 200 Success
    end
```

**Constraints**:

- Only available for terminal states: COMPLETED, FAILED, CANCELLED
- Prevents duplicate termination attempts
- Updates execution record with `instancesTerminated: true`

---

## Deployment Architecture

### S3 Deployment Bucket Structure

```text
s3://{deployment-bucket}/
├── cfn/                              # CloudFormation templates
│   ├── master-template.yaml
│   ├── database-stack.yaml
│   ├── lambda-stack.yaml
│   ├── api-stack.yaml
│   ├── step-functions-stack.yaml
│   ├── security-stack.yaml
│   └── frontend-stack.yaml
├── lambda/                           # Function deployment packages
│   ├── api-handler.zip
│   ├── orchestration-stepfunctions.zip
│   ├── execution-finder.zip
│   ├── execution-poller.zip
│   └── frontend-builder.zip
└── frontend/                         # Frontend build artifacts
    ├── index.html
    ├── assets/
    └── aws-config.json
```

### Nested Stack Architecture

```mermaid
graph TB
    subgraph "CloudFormation Deployment"
        Master[master-template.yaml]
        
        subgraph "Nested Stacks"
            DB[database-stack]
            LambdaStk[lambda-stack]
            API[api-stack]
            SF[step-functions-stack]
            Sec[security-stack]
            FE[frontend-stack]
        end
    end
    
    Master --> DB
    Master --> LambdaStk
    Master --> API
    Master --> SF
    Master --> Sec
    Master --> FE
    
    DB -.->|TableNames| LambdaStk
    LambdaStk -.->|FunctionArns| API
    LambdaStk -.->|FunctionArns| SF
    API -.->|UserPoolId| FE
    
    style Master fill:#E7157B
    style DB fill:#C925D1
    style LambdaStk fill:#ED7100
    style API fill:#E7157B
    style SF fill:#E7157B
    style FE fill:#8C4FFF
```

**Stack Dependencies**:

1. **database-stack**: Creates DynamoDB tables (no dependencies)
2. **lambda-stack**: Creates Lambda functions (depends on database-stack outputs)
3. **api-stack**: Creates API Gateway + Cognito (depends on lambda-stack outputs)
4. **step-functions-stack**: Creates state machine (depends on lambda-stack outputs)
5. **security-stack**: Creates WAF + CloudTrail (optional, no dependencies)
6. **frontend-stack**: Creates S3 + CloudFront (depends on api-stack outputs)

---

## Technology Stack Versions

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.1.1 | UI framework with hooks |
| TypeScript | 5.9.3 | Type safety |
| CloudScape Design System | 3.0.1148 | AWS-native UI components |
| Vite | 7.1.7 | Build tool and dev server |
| AWS Amplify | 6.15.8 | Cognito authentication |
| Axios | 1.13.2 | HTTP client |
| React Router | 7.9.5 | Client-side routing |
| react-hot-toast | 2.6.0 | Toast notifications |
| date-fns | 4.1.0 | Date formatting |
| ESLint | 9.36.0 | Code quality |

### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Lambda runtime |
| boto3 | (runtime) | AWS SDK |
| crhelper | 2.0.11 | CloudFormation custom resources |

### AWS Services

| Service | Purpose |
|---------|---------|
| API Gateway | REST API with Cognito authorizer |
| Cognito | User authentication (45-minute session timeout) |
| Step Functions | Orchestration with waitForTaskToken |
| DynamoDB | NoSQL database (3 tables + GSI) |
| S3 | Static hosting + deployment artifacts |
| CloudFront | CDN for frontend distribution |
| CloudFormation | Infrastructure as Code (7 nested stacks) |
| Lambda | Serverless compute (5 functions) |
| EventBridge | Scheduled polling (1-minute intervals) |
| CloudWatch | Logging and metrics |
| IAM | Least-privilege access control |
| AWS DRS | Elastic Disaster Recovery integration |

---

## Component Interaction Matrix

| Component | Reads From | Writes To | Invokes |
|-----------|------------|-----------|---------|
| api-handler | DynamoDB (all 3 tables), DRS | DynamoDB, CloudWatch Logs | Step Functions, EC2 |
| orchestration-stepfunctions | DynamoDB, DRS | DynamoDB, CloudWatch Logs | DRS StartRecovery |
| execution-finder | DynamoDB (StatusIndex GSI) | CloudWatch Logs | execution-poller |
| execution-poller | DynamoDB, DRS | DynamoDB, CloudWatch Metrics | - |
| frontend-builder | S3 (deployment bucket) | S3 (frontend bucket), CloudFront | - |
| Step Functions | - | CloudWatch Logs | orchestration-stepfunctions |
| EventBridge | - | - | execution-finder |
| Frontend | API Gateway | - | Cognito Auth |

---

## Summary

This architecture provides:

- **Serverless**: No servers to manage, pay-per-use pricing
- **Scalable**: Handles multiple concurrent executions
- **Resilient**: Built-in retry logic, error handling
- **Secure**: Cognito JWT auth, IAM least-privilege, encryption at rest
- **Observable**: CloudWatch logs and metrics for all components
- **Maintainable**: Modular nested stacks, Infrastructure as Code

**Key Patterns**:

- `waitForTaskToken` for pause/resume capability
- StatusIndex GSI for efficient execution polling
- EventBridge scheduled triggers for background processing
- CloudFront + S3 for global frontend distribution
- API Gateway + Cognito for secure API access
