# Architecture Diagrams

## Overview

This document provides Mermaid diagrams illustrating the refactored handler architecture, dual invocation modes, and data flow patterns in the DR Orchestration Platform.

## Handler Responsibility Architecture

```mermaid
flowchart TB
    subgraph "Frontend"
        UI[CloudFront + React]
    end
    
    subgraph "API Gateway"
        APIGW[API Gateway<br/>Cognito JWT Auth]
    end
    
    subgraph "Lambda Handlers"
        QH[query-handler<br/>READ-ONLY<br/>+ Audit Logging]
        DMH[data-management-handler<br/>CRUD + Data Sync]
        EH[execution-handler<br/>Recovery Actions<br/>+ Wave Updates]
    end
    
    subgraph "EventBridge"
        EB1[Inventory Sync<br/>Every 5 min]
        EB2[Staging Sync<br/>Every 15 min]
        EB3[Recovery Instance Sync<br/>Every 10 min]
    end
    
    subgraph "Step Functions"
        SF[DR Orchestration<br/>State Machine]
    end
    
    subgraph "DynamoDB Tables"
        PG[(Protection Groups)]
        RP[(Recovery Plans)]
        EH_TABLE[(Execution History)]
        INV[(Inventory)]
        AUDIT[(Audit Logs)]
    end
    
    subgraph "AWS Services"
        DRS[AWS DRS API]
        EC2[AWS EC2 API]
    end
    
    UI --> APIGW
    APIGW --> QH
    APIGW --> DMH
    APIGW --> EH
    
    EB1 --> DMH
    EB2 --> DMH
    EB3 --> DMH
    
    SF --> QH
    SF --> EH
    
    QH -.Read.-> PG
    QH -.Read.-> RP
    QH -.Read.-> EH_TABLE
    QH -.Read.-> INV
    QH -->|WRITE| AUDIT
    
    DMH -->|Write| PG
    DMH -->|Write| RP
    DMH -->|Write| INV
    
    EH -->|Write| EH_TABLE
    
    DMH --> DRS
    DMH --> EC2
    EH --> DRS
    EH --> EC2
    QH -.Query.-> DRS
    QH -.Query.-> EC2
    
    style QH fill:#90EE90
    style DMH fill:#87CEEB
    style EH fill:#FFB6C1
    style AUDIT fill:#FFD700
```

## Dual Invocation Mode Architecture

```mermaid
flowchart TB
    subgraph "API Gateway Invocation"
        USER[User]
        CF[CloudFront]
        APIGW[API Gateway]
        COGNITO[Cognito JWT<br/>Validation]
    end
    
    subgraph "Direct Lambda Invocation"
        SF[Step Functions]
        EB[EventBridge]
    end
    
    subgraph "query-handler Lambda"
        DETECT{Invocation<br/>Mode?}
        API_MODE[API Gateway Mode<br/>Extract Cognito User]
        DIRECT_MODE[Direct Lambda Mode<br/>Extract IAM Principal]
        RBAC[RBAC Check<br/>Cognito Groups]
        IAM_EXTRACT[IAM Principal<br/>Extraction]
        AUDIT[Audit Logging]
        PROCESS[Process Query]
    end
    
    subgraph "Audit Log Fields"
        API_FIELDS[principal_type: CognitoUser<br/>principal_arn: cognito:user:email<br/>user_groups: Admin, Operator<br/>source_ip, user_agent]
        DIRECT_FIELDS[principal_type: AssumedRole/User/Service<br/>principal_arn: IAM ARN<br/>session_name: session-123]
    end
    
    USER --> CF
    CF --> APIGW
    APIGW --> COGNITO
    COGNITO --> DETECT
    
    SF --> DETECT
    EB --> DETECT
    
    DETECT -->|requestContext<br/>exists| API_MODE
    DETECT -->|No requestContext| DIRECT_MODE
    
    API_MODE --> RBAC
    RBAC --> AUDIT
    
    DIRECT_MODE --> IAM_EXTRACT
    IAM_EXTRACT --> AUDIT
    
    AUDIT --> PROCESS
    
    API_MODE -.Logs.-> API_FIELDS
    DIRECT_MODE -.Logs.-> DIRECT_FIELDS
    
    style DETECT fill:#FFD700
    style API_MODE fill:#90EE90
    style DIRECT_MODE fill:#87CEEB
    style AUDIT fill:#FFB6C1
```

## Wave Polling Flow (Refactored)

```mermaid
sequenceDiagram
    participant SF as Step Functions
    participant QH as query-handler<br/>(READ-ONLY)
    participant EH as execution-handler<br/>(WRITE)
    participant DRS as AWS DRS API
    participant DDB as DynamoDB<br/>Execution History
    
    SF->>QH: poll_wave_status<br/>(execution_id, job_id, wave_number)
    
    Note over QH: Read-Only Operations
    QH->>DRS: describe_jobs(job_id)
    DRS-->>QH: Job status + server states
    
    QH->>QH: Calculate wave progress<br/>(launched, failed, total)
    QH->>QH: Determine wave completion<br/>(job_status, server_states)
    
    QH-->>SF: Wave status data<br/>(NO DynamoDB writes)
    
    SF->>EH: update_wave_completion_status<br/>(execution_id, wave_data)
    
    Note over EH: Write Operations
    EH->>DDB: update_item<br/>(execution_id, wave_status)
    DDB-->>EH: Update confirmed
    
    EH->>EH: Send notifications<br/>(wave_completed, wave_failed)
    
    EH-->>SF: Update result
    
    SF->>SF: Check wave completion
    
    alt Wave Complete
        SF->>SF: Proceed to next wave
    else Wave In Progress
        SF->>SF: Wait and poll again
    end
```

## EventBridge Sync Operations Flow

```mermaid
flowchart LR
    subgraph "EventBridge Rules"
        EB1[Inventory Sync<br/>rate 5 min]
        EB2[Staging Sync<br/>rate 15 min]
        EB3[Recovery Instance Sync<br/>rate 10 min]
    end
    
    subgraph "data-management-handler"
        INV_SYNC[handle_sync_source_server_inventory]
        STAGE_SYNC[handle_sync_staging_accounts]
        REC_SYNC[handle_sync_recovery_instances]
    end
    
    subgraph "AWS Services"
        DRS[AWS DRS API<br/>describe_source_servers]
        EC2[AWS EC2 API<br/>describe_instances]
    end
    
    subgraph "DynamoDB Tables"
        INV_TABLE[(Source Server<br/>Inventory)]
        STAGE_TABLE[(Staging<br/>Accounts)]
        REC_TABLE[(Recovery<br/>Instances)]
        REGION_TABLE[(Region<br/>Status)]
    end
    
    EB1 -->|Invoke| INV_SYNC
    EB2 -->|Invoke| STAGE_SYNC
    EB3 -->|Invoke| REC_SYNC
    
    INV_SYNC --> DRS
    INV_SYNC --> EC2
    INV_SYNC --> INV_TABLE
    INV_SYNC --> REGION_TABLE
    
    STAGE_SYNC --> DRS
    STAGE_SYNC --> STAGE_TABLE
    
    REC_SYNC --> DRS
    REC_SYNC --> EC2
    REC_SYNC --> REC_TABLE
    
    style INV_SYNC fill:#87CEEB
    style STAGE_SYNC fill:#87CEEB
    style REC_SYNC fill:#87CEEB
```

## Cross-Account Audit Trail

```mermaid
flowchart TB
    subgraph "Hub Account (891376951562)"
        QH[query-handler]
        AUDIT_TABLE[(Centralized<br/>Audit Logs)]
        STS[AWS STS<br/>AssumeRole]
    end
    
    subgraph "Spoke Account 1 (123456789012)"
        ROLE1[DRSRole]
        DRS1[AWS DRS API]
    end
    
    subgraph "Spoke Account 2 (234567890123)"
        ROLE2[DRSRole]
        DRS2[AWS DRS API]
    end
    
    QH -->|1. AssumeRole| STS
    STS -->|2. Temporary Credentials| ROLE1
    ROLE1 -->|3. Query DRS| DRS1
    DRS1 -->|4. Server Data| QH
    
    QH -->|5. Write Audit Log<br/>source_account: 891376951562<br/>target_account: 123456789012<br/>assumed_role_arn<br/>cross_account_session| AUDIT_TABLE
    
    QH -.Cross-Account Query.-> ROLE2
    ROLE2 -.Query DRS.-> DRS2
    
    style QH fill:#90EE90
    style AUDIT_TABLE fill:#FFD700
    style ROLE1 fill:#FFB6C1
    style ROLE2 fill:#FFB6C1
```

## IAM Principal Extraction Flow

```mermaid
flowchart TB
    CONTEXT[Lambda Context<br/>invoked_function_arn]
    
    EXTRACT{Parse ARN<br/>Pattern}
    
    ASSUMED[AssumedRole Pattern<br/>arn:aws:sts::ACCOUNT:assumed-role/ROLE/SESSION]
    USER[IAM User Pattern<br/>arn:aws:iam::ACCOUNT:user/USER]
    SERVICE[AWS Service Pattern<br/>arn:aws:events::ACCOUNT:rule/RULE]
    
    ASSUMED_RESULT[principal_type: AssumedRole<br/>principal_arn: arn:aws:iam::ACCOUNT:role/ROLE<br/>session_name: SESSION<br/>account_id: ACCOUNT]
    
    USER_RESULT[principal_type: User<br/>principal_arn: arn:aws:iam::ACCOUNT:user/USER<br/>session_name: null<br/>account_id: ACCOUNT]
    
    SERVICE_RESULT[principal_type: Service<br/>principal_arn: arn:aws:events::ACCOUNT:rule/RULE<br/>session_name: null<br/>account_id: ACCOUNT]
    
    AUDIT[Write to<br/>Audit Log]
    
    CONTEXT --> EXTRACT
    
    EXTRACT -->|Matches| ASSUMED
    EXTRACT -->|Matches| USER
    EXTRACT -->|Matches| SERVICE
    
    ASSUMED --> ASSUMED_RESULT
    USER --> USER_RESULT
    SERVICE --> SERVICE_RESULT
    
    ASSUMED_RESULT --> AUDIT
    USER_RESULT --> AUDIT
    SERVICE_RESULT --> AUDIT
    
    style EXTRACT fill:#FFD700
    style ASSUMED_RESULT fill:#90EE90
    style USER_RESULT fill:#87CEEB
    style SERVICE_RESULT fill:#FFB6C1
```

## RBAC Permission Enforcement

```mermaid
flowchart TB
    REQUEST[API Gateway<br/>Request]
    
    JWT[Extract Cognito JWT<br/>Claims]
    
    GROUPS[User Groups<br/>Admin, Operator, Viewer,<br/>Auditor, Planner]
    
    OPERATION[Operation<br/>create_protection_group,<br/>start_recovery,<br/>view_audit_logs, etc.]
    
    CHECK{check_permission<br/>user_groups, operation}
    
    ADMIN{Admin<br/>Group?}
    OPERATOR{Operator<br/>Operations?}
    VIEWER{Viewer<br/>Operations?}
    AUDITOR{Auditor<br/>Operations?}
    PLANNER{Planner<br/>Operations?}
    
    ALLOW[✓ Allow<br/>Process Request]
    DENY[✗ Deny<br/>403 Forbidden]
    
    REQUEST --> JWT
    JWT --> GROUPS
    JWT --> OPERATION
    
    GROUPS --> CHECK
    OPERATION --> CHECK
    
    CHECK --> ADMIN
    ADMIN -->|Yes| ALLOW
    ADMIN -->|No| OPERATOR
    
    OPERATOR -->|Match| ALLOW
    OPERATOR -->|No Match| VIEWER
    
    VIEWER -->|Match| ALLOW
    VIEWER -->|No Match| AUDITOR
    
    AUDITOR -->|Match| ALLOW
    AUDITOR -->|No Match| PLANNER
    
    PLANNER -->|Match| ALLOW
    PLANNER -->|No Match| DENY
    
    style ALLOW fill:#90EE90
    style DENY fill:#FF6B6B
    style CHECK fill:#FFD700
```

## Parameter Masking Flow

```mermaid
flowchart LR
    INPUT[Request Parameters<br/>username: admin<br/>password: secret123<br/>api_key: sk-abc<br/>region: us-east-2]
    
    MASK[mask_sensitive_parameters]
    
    PATTERNS[Sensitive Patterns<br/>password, api_key,<br/>secret, token,<br/>credential, private_key]
    
    CHECK{Match<br/>Pattern?}
    
    MASKED[Masked Value<br/>***MASKED***]
    
    KEEP[Keep Original<br/>Value]
    
    OUTPUT[Masked Parameters<br/>username: admin<br/>password: ***MASKED***<br/>api_key: ***MASKED***<br/>region: us-east-2]
    
    AUDIT[Write to<br/>Audit Log]
    
    INPUT --> MASK
    MASK --> PATTERNS
    PATTERNS --> CHECK
    
    CHECK -->|Yes| MASKED
    CHECK -->|No| KEEP
    
    MASKED --> OUTPUT
    KEEP --> OUTPUT
    
    OUTPUT --> AUDIT
    
    style MASK fill:#FFD700
    style MASKED fill:#FF6B6B
    style KEEP fill:#90EE90
```

## Audit Error Handling Flow

```mermaid
flowchart TB
    AUDIT[Audit Log<br/>Write Attempt]
    
    DYNAMODB[DynamoDB<br/>put_item]
    
    SUCCESS{Write<br/>Success?}
    
    RETRY{Retry<br/>Count < 3?}
    
    BACKOFF[Exponential Backoff<br/>100ms, 200ms, 400ms]
    
    FALLBACK[CloudWatch Logs<br/>Fallback]
    
    COMPLETE[Audit Log<br/>Persisted]
    
    AUDIT --> DYNAMODB
    DYNAMODB --> SUCCESS
    
    SUCCESS -->|Yes| COMPLETE
    SUCCESS -->|No| RETRY
    
    RETRY -->|Yes| BACKOFF
    RETRY -->|No| FALLBACK
    
    BACKOFF --> DYNAMODB
    
    FALLBACK --> COMPLETE
    
    style SUCCESS fill:#FFD700
    style COMPLETE fill:#90EE90
    style FALLBACK fill:#FFB6C1
```

## Related Documentation

- [Handler Responsibilities](HANDLER_RESPONSIBILITIES.md)
- [Dual Invocation Mode Architecture](DUAL_INVOCATION_MODE.md)
- [IAM Principal Extraction](../security/IAM_PRINCIPAL_EXTRACTION.md)
- [RBAC Permissions](../security/RBAC_PERMISSIONS.md)
- [Audit Log Schema](../security/AUDIT_LOG_SCHEMA.md)
- [Deployment Guide](../guides/DEPLOYMENT_GUIDE.md)
