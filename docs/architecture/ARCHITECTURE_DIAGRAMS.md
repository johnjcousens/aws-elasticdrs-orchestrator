# Architecture Diagrams

Complete visual reference for AWS DRS Orchestration architecture, data flows, and component interactions.

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Lambda Functions Architecture](#lambda-functions-architecture)
3. [Data Flow Diagrams](#data-flow-diagrams)
4. [DRS Integration Flow](#drs-integration-flow)
5. [Step Functions Orchestration](#step-functions-orchestration)
6. [Deployment Architecture](#deployment-architecture)

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
        Cognito[Cognito User Pool]
    end
    
    subgraph "API Layer"
        APIGW[API Gateway REST]
        CognitoAuth[Cognito Authorizer]
    end
    
    subgraph "Compute Layer - Lambda Functions"
        APIHandler[api-handler<br/>index.py]
        OrchSF[orchestration-stepfunctions<br/>orchestration_stepfunctions.py]
        OrchLegacy[orchestration<br/>drs_orchestrator.py]
        ExecFinder[execution-finder<br/>execution_finder.py]
        ExecPoller[execution-poller<br/>execution_poller.py]
        FEBuilder[frontend-builder<br/>build_and_deploy.py]
    end
    
    subgraph "Orchestration"
        StepFn[Step Functions<br/>State Machine]
    end
    
    subgraph "Scheduling"
        EventBridge[EventBridge Rule<br/>1 minute schedule]
    end
    
    subgraph "Data Layer"
        DDBProtection[(protection-groups)]
        DDBPlans[(recovery-plans)]
        DDBHistory[(execution-history)]
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
- **6 Lambda Functions**: API handler, orchestration (2), execution monitoring (2), frontend builder
- **3 DynamoDB Tables**: Protection groups, recovery plans, execution history
- **1 Step Functions State Machine**: Wave-based orchestration engine
- **1 EventBridge Rule**: Triggers execution finder every 1 minute

---

## Lambda Functions Architecture

```mermaid
graph LR
    subgraph "API Handler Lambda"
        API[api-handler<br/>120s timeout<br/>512 MB]
        APIRole[ApiHandlerRole]
    end
    
    subgraph "Orchestration Lambdas"
        OrchSF[orchestration-stepfunctions<br/>120s timeout<br/>512 MB]
        OrchLegacy[orchestration<br/>120s timeout<br/>512 MB]
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
    OrchLegacy --> OrchRole
    Finder --> FinderRole
    Poller --> PollerRole
    Builder --> BuilderRole
    
    APIRole -.->|DynamoDB| Tables[(3 Tables)]
    APIRole -.->|DRS| DRSService[AWS DRS]
    APIRole -.->|Step Functions| SF[State Machine]
    
    OrchRole -.->|DynamoDB| Tables
    OrchRole -.->|DRS| DRSService
    OrchRole -.->|EC2| EC2[EC2 API]
    
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

**Lambda Function Details:**

| Function | Handler | Timeout | Memory | Role | Purpose |
|----------|---------|---------|--------|------|---------|
| api-handler | index.lambda_handler | 120s | 512 MB | ApiHandlerRole | REST API endpoints |
| orchestration-stepfunctions | orchestration_stepfunctions.handler | 120s | 512 MB | OrchestrationRole | Step Functions orchestration |
| orchestration | drs_orchestrator.lambda_handler | 120s | 512 MB | OrchestrationRole | Legacy orchestrator |
| execution-finder | execution_finder.lambda_handler | 60s | 256 MB | ExecutionFinderRole | Find POLLING executions |
| execution-poller | execution_poller.lambda_handler | 120s | 256 MB | ExecutionPollerRole | Poll DRS job status |
| frontend-builder | build_and_deploy.lambda_handler | 900s | 2048 MB | CustomResourceRole | Deploy frontend |

---

## Data Flow Diagrams

### Protection Group Creation Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API Gateway
    participant api-handler
    participant DRS
    participant DynamoDB
    
    User->>Frontend: Create Protection Group
    Frontend->>API Gateway: POST /protection-groups
    API Gateway->>api-handler: Invoke with JWT
    
    api-handler->>DRS: describe_source_servers(region)
    DRS-->>api-handler: Source server list
    
    api-handler->>api-handler: Validate server IDs exist
    api-handler->>api-handler: Check unique PG name
    
    api-handler->>DynamoDB: PutItem(protection-groups)
    DynamoDB-->>api-handler: Success
    
    api-handler-->>API Gateway: 201 Created
    API Gateway-->>Frontend: Protection Group created
    Frontend-->>User: Success notification
```

### Recovery Plan Execution Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API Gateway
    participant api-handler
    participant Step Functions
    participant orchestration-stepfunctions
    participant DRS
    participant DynamoDB
    
    User->>Frontend: Execute Recovery Plan
    Frontend->>API Gateway: POST /executions
    API Gateway->>api-handler: Invoke with plan ID
    
    api-handler->>DynamoDB: GetItem(recovery-plans)
    DynamoDB-->>api-handler: Plan details with waves
    
    api-handler->>DynamoDB: PutItem(execution-history)<br/>Status: PENDING
    api-handler->>Step Functions: StartExecution
    api-handler-->>Frontend: 202 Accepted<br/>Execution ID
    
    Step Functions->>orchestration-stepfunctions: Wave 1 execution
    orchestration-stepfunctions->>DynamoDB: GetItem(protection-groups)
    orchestration-stepfunctions->>DRS: start_recovery(server_ids)
    DRS-->>orchestration-stepfunctions: Job ID
    
    orchestration-stepfunctions->>DynamoDB: UpdateItem(execution-history)<br/>Status: RUNNING, JobId
    orchestration-stepfunctions-->>Step Functions: Wait for completion
    
    Step Functions->>orchestration-stepfunctions: Poll job status
    orchestration-stepfunctions->>DRS: describe_jobs(job_id)
    DRS-->>orchestration-stepfunctions: Job status: LAUNCHED
    
    orchestration-stepfunctions->>DynamoDB: UpdateItem(execution-history)<br/>Wave 1: COMPLETED
    orchestration-stepfunctions-->>Step Functions: Wave complete
    
    Step Functions->>orchestration-stepfunctions: Wave 2 execution
    Note over Step Functions,orchestration-stepfunctions: Repeat for each wave
    
    orchestration-stepfunctions->>DynamoDB: UpdateItem(execution-history)<br/>Status: COMPLETED
    orchestration-stepfunctions-->>Step Functions: Execution complete
```

### Execution Monitoring Flow

```mermaid
sequenceDiagram
    participant EventBridge
    participant execution-finder
    participant execution-poller
    participant DynamoDB
    participant DRS
    participant CloudWatch
    
    EventBridge->>execution-finder: Trigger (every 1 minute)
    
    execution-finder->>DynamoDB: Query(StatusIndex)<br/>Status = POLLING
    DynamoDB-->>execution-finder: List of executions
    
    loop For each execution
        execution-finder->>execution-poller: Invoke async
        
        execution-poller->>DynamoDB: GetItem(execution-history)
        DynamoDB-->>execution-poller: Execution details with JobIds
        
        execution-poller->>DRS: describe_jobs(job_ids)
        DRS-->>execution-poller: Job statuses
        
        alt All jobs LAUNCHED
            execution-poller->>DynamoDB: UpdateItem<br/>Status: COMPLETED
            execution-poller->>CloudWatch: PutMetricData<br/>ExecutionSuccess
        else Jobs still PENDING
            execution-poller->>DynamoDB: UpdateItem<br/>Status: POLLING
        else Timeout exceeded
            execution-poller->>DynamoDB: UpdateItem<br/>Status: FAILED
            execution-poller->>CloudWatch: PutMetricData<br/>ExecutionFailure
        end
    end
```

---

## DRS Integration Flow

### DRS Recovery Job Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: start_recovery() called
    
    PENDING --> SNAPSHOT: DRS creates EBS snapshots
    SNAPSHOT --> CONVERSION: Snapshots complete
    
    CONVERSION --> LAUNCH_TEMPLATE: DRS launches conversion server
    LAUNCH_TEMPLATE --> LAUNCHING: Creates launch template
    
    LAUNCHING --> LAUNCHED: EC2 instances launched
    LAUNCHED --> [*]: Recovery complete
    
    PENDING --> FAILED: Error during snapshot
    CONVERSION --> FAILED: Conversion server error
    LAUNCHING --> FAILED: EC2 launch error
    
    note right of SNAPSHOT
        Phase 1: Snapshot Creation
        - EBS snapshots of source volumes
        - Uses calling role's ec2:CreateSnapshot
    end note
    
    note right of CONVERSION
        Phase 2: Conversion Server
        - Temporary EC2 instance
        - Converts snapshots to AMI
        - Uses calling role's ec2:RunInstances
    end note
    
    note right of LAUNCH_TEMPLATE
        Phase 3: Launch Template
        - Creates EC2 launch template
        - Uses calling role's ec2:CreateLaunchTemplate
        - CRITICAL: Must have permissions
    end note
    
    note right of LAUNCHED
        Phase 4: Recovery Instances
        - Final EC2 instances launched
        - Uses launch template
        - Status: LAUNCHED (reliable)
    end note
```

### IAM Permission Flow for DRS Operations

```mermaid
graph TB
    subgraph "Lambda Execution"
        Lambda[orchestration-stepfunctions]
        LambdaRole[OrchestrationRole]
    end
    
    subgraph "DRS Service"
        DRSCall[drs:StartRecovery]
        DRSService[DRS Backend]
    end
    
    subgraph "EC2 Operations"
        Snapshot[ec2:CreateSnapshot]
        RunInstance[ec2:RunInstances]
        CreateLT[ec2:CreateLaunchTemplate]
        CreateLTV[ec2:CreateLaunchTemplateVersion]
        ModifyLT[ec2:ModifyLaunchTemplate]
    end
    
    Lambda -->|Assumes| LambdaRole
    Lambda -->|Calls| DRSCall
    
    DRSCall -->|Uses Lambda Role| DRSService
    
    DRSService -->|Phase 1| Snapshot
    DRSService -->|Phase 2| RunInstance
    DRSService -->|Phase 3| CreateLT
    DRSService -->|Phase 3| CreateLTV
    DRSService -->|Phase 3| ModifyLT
    
    LambdaRole -.->|Must have| Snapshot
    LambdaRole -.->|Must have| RunInstance
    LambdaRole -.->|Must have| CreateLT
    LambdaRole -.->|Must have| CreateLTV
    LambdaRole -.->|Must have| ModifyLT
    
    style DRSService fill:#527FFF
    style LambdaRole fill:#DD344C
    
    note1[CRITICAL INSIGHT:<br/>DRS uses calling role's<br/>IAM permissions, NOT<br/>service-linked role]
    note1 -.-> DRSService
```

**Key Insight**: When Lambda calls `drs:StartRecovery`, DRS performs EC2 operations using the **Lambda role's IAM permissions**, not the DRS service-linked role. This is why OrchestrationRole needs comprehensive EC2 permissions.

---

## Step Functions Orchestration

### State Machine Flow

```mermaid
stateDiagram-v2
    [*] --> InitializeExecution
    
    InitializeExecution --> ValidatePlan: Load plan details
    ValidatePlan --> ExecuteWave1: Plan valid
    ValidatePlan --> Failed: Invalid plan
    
    ExecuteWave1 --> WaitWave1: DRS job started
    WaitWave1 --> PollWave1Status: Wait 30s
    
    PollWave1Status --> CheckWave1Complete: Check job status
    CheckWave1Complete --> ExecuteWave2: All servers LAUNCHED
    CheckWave1Complete --> WaitWave1: Still PENDING
    CheckWave1Complete --> Failed: Timeout or error
    
    ExecuteWave2 --> WaitWave2: DRS job started
    WaitWave2 --> PollWave2Status: Wait 30s
    
    PollWave2Status --> CheckWave2Complete: Check job status
    CheckWave2Complete --> ExecuteWaveN: All servers LAUNCHED
    CheckWave2Complete --> WaitWave2: Still PENDING
    CheckWave2Complete --> Failed: Timeout or error
    
    ExecuteWaveN --> FinalizeExecution: All waves complete
    FinalizeExecution --> [*]: Success
    
    Failed --> [*]: Execution failed
    
    note right of ExecuteWave1
        For each wave:
        1. Get protection groups
        2. Collect server IDs
        3. Call start_recovery()
        4. Store job ID
    end note
    
    note right of PollWave1Status
        Poll DRS job status:
        - describe_jobs(job_id)
        - Check participatingServers
        - launchStatus: LAUNCHED
    end note
```

### Wave Execution Pattern

```mermaid
graph TB
    subgraph "Wave 1: Database Tier"
        W1PG1[Protection Group: DB-Primary]
        W1PG2[Protection Group: DB-Secondary]
        W1Job[DRS Job ID: job-abc123]
        W1Server1[Server: s-111]
        W1Server2[Server: s-222]
        W1Server3[Server: s-333]
    end
    
    subgraph "Wave 2: Application Tier"
        W2PG1[Protection Group: App-Servers]
        W2Job[DRS Job ID: job-def456]
        W2Server1[Server: s-444]
        W2Server2[Server: s-555]
    end
    
    subgraph "Wave 3: Web Tier"
        W3PG1[Protection Group: Web-Servers]
        W3Job[DRS Job ID: job-ghi789]
        W3Server1[Server: s-666]
    end
    
    W1PG1 --> W1Server1
    W1PG1 --> W1Server2
    W1PG2 --> W1Server3
    
    W1Server1 --> W1Job
    W1Server2 --> W1Job
    W1Server3 --> W1Job
    
    W1Job -->|Wait for LAUNCHED| W2PG1
    
    W2PG1 --> W2Server1
    W2PG1 --> W2Server2
    
    W2Server1 --> W2Job
    W2Server2 --> W2Job
    
    W2Job -->|Wait for LAUNCHED| W3PG1
    
    W3PG1 --> W3Server1
    W3Server1 --> W3Job
    
    style W1Job fill:#E7157B
    style W2Job fill:#E7157B
    style W3Job fill:#E7157B
```

**Wave Execution Rules:**
1. **One DRS job per wave** - All servers in a wave launched with single `start_recovery()` call
2. **Sequential execution** - Wave N+1 starts only after Wave N completes
3. **LAUNCHED status** - Trust DRS job status without requiring `recoveryInstanceID`
4. **Dependency validation** - Circular dependencies detected at plan creation

---

## Deployment Architecture

### CloudFormation Nested Stacks

```mermaid
graph TB
    Master[master-template.yaml]
    
    Database[database-stack.yaml]
    Lambda[lambda-stack.yaml]
    API[api-stack.yaml]
    Frontend[frontend-stack.yaml]
    Security[security-stack.yaml]
    StepFn[step-functions-stack.yaml]
    
    Master --> Database
    Master --> Lambda
    Master --> API
    Master --> Frontend
    Master --> Security
    Master --> StepFn
    
    subgraph "Database Stack"
        DDB1[(protection-groups)]
        DDB2[(recovery-plans)]
        DDB3[(execution-history)]
        GSI[StatusIndex GSI]
    end
    
    subgraph "Lambda Stack"
        L1[api-handler]
        L2[orchestration-stepfunctions]
        L3[orchestration]
        L4[execution-finder]
        L5[execution-poller]
        L6[frontend-builder]
        R1[ApiHandlerRole]
        R2[OrchestrationRole]
        R3[ExecutionFinderRole]
        R4[ExecutionPollerRole]
        R5[CustomResourceRole]
    end
    
    subgraph "API Stack"
        APIGW[API Gateway]
        Cognito[Cognito User Pool]
        CognitoClient[App Client]
        Authorizer[Cognito Authorizer]
    end
    
    subgraph "Frontend Stack"
        S3[S3 Bucket]
        CF[CloudFront Distribution]
        OAI[Origin Access Identity]
    end
    
    subgraph "Step Functions Stack"
        SM[State Machine]
        SMRole[State Machine Role]
    end
    
    Database --> DDB1
    Database --> DDB2
    Database --> DDB3
    DDB3 --> GSI
    
    Lambda --> L1
    Lambda --> L2
    Lambda --> L3
    Lambda --> L4
    Lambda --> L5
    Lambda --> L6
    L1 --> R1
    L2 --> R2
    L3 --> R2
    L4 --> R3
    L5 --> R4
    L6 --> R5
    
    API --> APIGW
    API --> Cognito
    Cognito --> CognitoClient
    APIGW --> Authorizer
    
    Frontend --> S3
    Frontend --> CF
    CF --> OAI
    
    StepFn --> SM
    SM --> SMRole
    
    style Master fill:#232F3E
    style Database fill:#3B48CC
    style Lambda fill:#FF9900
    style API fill:#FF4F8B
    style Frontend fill:#569A31
    style StepFn fill:#E7157B
```

### S3 Deployment Bucket Structure

```
s3://aws-drs-orchestration/
├── cfn/
│   ├── master-template.yaml
│   ├── database-stack.yaml
│   ├── lambda-stack.yaml
│   ├── api-stack.yaml
│   ├── frontend-stack.yaml
│   ├── security-stack.yaml
│   └── step-functions-stack.yaml
├── lambda/
│   ├── api-handler.zip                    # index.py
│   ├── orchestration-stepfunctions.zip    # orchestration_stepfunctions.py
│   ├── orchestration.zip                  # drs_orchestrator.py
│   ├── execution-finder.zip               # execution_finder.py
│   ├── execution-poller.zip               # execution_poller.py
│   └── frontend-builder.zip               # build_and_deploy.py
└── frontend/
    ├── index.html
    ├── assets/
    │   ├── index-[hash].js
    │   └── index-[hash].css
    └── aws-config.js
```

### Technology Stack Versions

| Component | Technology | Version |
|-----------|------------|---------|
| **Frontend** | React | 19.1.1 |
| | TypeScript | 5.9.3 |
| | Vite | 7.1.7 |
| | CloudScape Design System | 3.0.1148 |
| | AWS Amplify | 6.15.8 |
| | React Router | 7.9.5 |
| | Axios | 1.13.2 |
| **Backend** | Python | 3.12 |
| | boto3 | (Lambda runtime) |
| | crhelper | 2.0.11 |
| **Infrastructure** | CloudFormation | 2010-09-09 |
| | DynamoDB | On-demand |
| | API Gateway | REST |
| | Step Functions | Standard |

---

## Component Interaction Matrix

| Component | Interacts With | Purpose |
|-----------|----------------|---------|
| **api-handler** | DynamoDB (all 3 tables) | CRUD operations |
| | AWS DRS | Server discovery |
| | Step Functions | Start executions |
| | Lambda (self) | Async invocation |
| **orchestration-stepfunctions** | DynamoDB (all 3 tables) | Read plans, update execution |
| | AWS DRS | start_recovery, describe_jobs |
| | EC2 | Launch template operations |
| **execution-finder** | DynamoDB (execution-history) | Query StatusIndex GSI |
| | Lambda (execution-poller) | Invoke for each execution |
| **execution-poller** | DynamoDB (execution-history) | Update execution status |
| | AWS DRS | describe_jobs |
| | CloudWatch | Put metrics |
| **frontend-builder** | S3 | Upload frontend artifacts |
| | CloudFront | Create invalidation |

---

## Summary

This architecture provides:

- **6 Lambda functions** for API, orchestration, and monitoring
- **3 DynamoDB tables** for data persistence with GSI for efficient queries
- **1 Step Functions state machine** for wave-based orchestration
- **1 EventBridge rule** for scheduled execution monitoring
- **Modular CloudFormation** with 6 nested stacks for maintainability
- **Serverless design** with pay-per-use pricing (~$12-40/month)
- **Enterprise-grade** with encryption, authentication, and audit trails

**Critical Architectural Decisions:**
1. **DRS uses calling role permissions** - OrchestrationRole needs EC2 permissions
2. **One DRS job per wave** - All servers launched together for efficiency
3. **LAUNCHED status is reliable** - No need to wait for recoveryInstanceID
4. **EventBridge polling** - 1-minute schedule for execution monitoring
5. **Step Functions orchestration** - Replaces legacy Lambda-based orchestrator
