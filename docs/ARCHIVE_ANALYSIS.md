# ARCHIVE Reference Architecture Analysis

## Executive Summary

The ARCHIVE folder contains **two complementary AWS reference architectures** that can be combined to build your main Step Function orchestration solution:

1. **DR Orchestrator** (`dr-orchestration-artifacts/`) - Multi-region DR lifecycle orchestration with modular service support
2. **DRS Plan Automation** (`drs-tools/drs-plan-automation/`) - Wave-based DRS recovery with PreWave/PostWave SSM automation

Both use **Step Functions calling other Step Functions** - exactly your planned architecture.

---

## Architecture Comparison

| Feature | DR Orchestrator | DRS Plan Automation |
|---------|-----------------|---------------------|
| **Primary Focus** | Full DR lifecycle (Instantiate→Activate→Cleanup→Replicate) | DRS-specific wave-based recovery |
| **Step Function Hierarchy** | 3 levels (DR-Orchestrator → Lifecycle → ModuleFactory) | 2 levels (StateMachine → Lambda) |
| **Multi-Account** | Yes (cross-account role assumption) | Yes (DRS account roles) |
| **Service Modules** | DRS, RDS, ECS, Lambda, R53, EventBridge, ElastiCache, etc. | DRS + SSM Automation runbooks |
| **UI** | CloudWatch Dashboard | React UI with Cognito auth |
| **Approval Workflow** | SNS email approval | None (API-triggered) |
| **Configuration** | JSON manifests in S3 | DynamoDB (Applications, Plans, Waves) |

---

## Recommended Hybrid Architecture

Combine both approaches for your 1000-server scale:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MAIN DR ORCHESTRATOR (Step Function)                      │
│  - Manual approval via SNS                                                   │
│  - Reads master manifest from S3                                             │
│  - Coordinates 4 lifecycle phases                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│ STAGING ACCOUNT 1 │   │ STAGING ACCOUNT 2 │   │ STAGING ACCOUNT 3 │
│ Step Function     │   │ Step Function     │   │ Step Function     │
│ (300 servers max) │   │ (300 servers max) │   │ (300 servers max) │
└───────────────────┘   └───────────────────┘   └───────────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                    DRS PLAN AUTOMATION (per staging account)               │
│  - Wave-based recovery (DBServers → AppServers → WebServers)              │
│  - PreWave Actions: Stop source instances, RDS failover, etc.             │
│  - PostWave Actions: Health checks, DNS updates, notifications            │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Key Components to Reuse

### 1. DR Orchestrator Step Functions (3-tier hierarchy)

**Main Orchestrator** (`DR-Orchestrator.yaml`):
```
Request Approval → Get Manifest from S3 → Call Lifecycle Step Function
```

**Lifecycle Orchestrator** (`Lifecycle-Orchestrator.yaml`):
```
For each Layer (sequential):
    For each Resource in Layer (parallel):
        Call ModuleFactory Step Function
```

**ModuleFactory** (`ModuleFactory.yaml`):
```
Execute lifecycle action → Poll status → Send success token
```

### 2. Module Factory Pattern (Extensible)

The `modulefactory/modules/` folder contains reusable modules:

| Module | Lifecycle Actions | Use Case |
|--------|-------------------|----------|
| `drs.py` | activate, replicate, cleanup | DRS failover/failback |
| `mysql.py` | activate, replicate, cleanup | Aurora MySQL failover |
| `sqlserver.py` | activate, replicate, cleanup | RDS SQL Server failover |
| `r53record.py` | activate | DNS failover |
| `ecsservice.py` | instantiate, activate, cleanup | ECS service scaling |
| `lambdafunction.py` | activate | Lambda alias switching |
| `elasticache.py` | activate | ElastiCache failover |
| `autoscaling.py` | instantiate, cleanup | ASG scaling |
| `eventbridge.py` | activate, cleanup | EventBridge rule management |

### 3. DRS Plan Automation Features

**Wave-Based Recovery**:
- Organize servers by tags (Role: DBServer, AppServer, WebServer)
- Sequential wave execution with configurable wait times
- PreWave/PostWave SSM Automation runbooks

**Data Model** (DynamoDB):
```json
{
  "AppId": "uuid",
  "AppName": "Sample Application",
  "AccountId": "012345678912",
  "Region": "us-west-2",
  "Plans": [{
    "PlanId": "uuid",
    "Waves": [{
      "Name": "Database Wave",
      "KeyName": "Role",
      "KeyValue": "DBServer",
      "MaxWaitTime": 900,
      "PreWaveActions": [{ "SSM Automation" }],
      "PostWaveActions": [{ "SSM Automation" }]
    }]
  }]
}
```

### 4. DRS Configuration Synchronizer

**Critical for multi-account**:
- Synchronizes launch templates, replication settings across accounts
- Tag-based overrides for specific servers
- Automatic subnet assignment based on IP ranges
- Scheduled via EventBridge (hourly)

---

## Manifest-Based Configuration

### DR Orchestrator Manifest Format

```json
[
  {
    "layer": 1,
    "resources": [
      {
        "action": "DRS",
        "resourceName": "WebServers",
        "parameters": {
          "AccountId": "111111111111",
          "HostNames": ["web-01", "web-02"],
          "Tags": {"Wave": "1"}
        }
      }
    ]
  },
  {
    "layer": 2,
    "resources": [
      {
        "action": "R53Record",
        "resourceName": "DNS-Failover",
        "parameters": {
          "HostedZoneId": "Z1234567890",
          "RecordName": "app.example.com",
          "TargetValue": "dr-alb.us-west-2.elb.amazonaws.com"
        }
      }
    ]
  }
]
```

### DRS Plan Automation Wave Format

```json
{
  "Waves": [
    {
      "Name": "Database Wave",
      "KeyName": "Role",
      "KeyValue": "DBServer",
      "MaxWaitTime": 900,
      "PreWaveActions": [{
        "Name": "Stop Source RDS",
        "StartAutomationExecution": {
          "DocumentName": "AWS-StopRdsInstance",
          "Parameters": {"InstanceId": ["db-instance-id"]}
        }
      }],
      "PostWaveActions": [{
        "Name": "Verify DB Connectivity",
        "StartAutomationExecution": {
          "DocumentName": "Custom-VerifyDBConnection",
          "Parameters": {"Endpoint": ["dr-db.cluster.us-west-2.rds.amazonaws.com"]}
        }
      }]
    }
  ]
}
```

---

## Multi-Account Cross-Account Role Pattern

### Target Account Role (`TargetAccountsAssumeRole.yaml`)

Deploy this role in each source account (40+ accounts):

```yaml
AssumeRolePolicyDocument:
  Statement:
    - Effect: Allow
      Principal:
        AWS: !Sub "arn:aws:iam::${OrchestratorAccountId}:root"
      Action: sts:AssumeRole
      Condition:
        StringEquals:
          aws:PrincipalOrgID: !Ref OrganizationId
```

### DRS Account Role (`drs-plan-automation-account-role.yaml`)

Deploy in each DRS staging account:
- DRS full access
- SSM Automation execution
- EC2 describe/tag operations
- CloudWatch logging

---

## Scripts Reference

### Useful Scripts in ARCHIVE/scripts/

| Script | Purpose |
|--------|---------|
| `updateDRSLaunchsettings.sh` | Bulk update DRS launch configurations |
| `isolateEC2InstancesForDRSByTag.sh` | Isolate instances for DR testing |
| `createEC2BackupImageAndLaunchTemplate.sh` | Create AMI backups with launch templates |
| `exportEC2SecurityGroups.sh` | Export SG rules for DR region |
| `importEC2SecurityGroups.sh` | Import SG rules to DR region |

### SSM Documents in ARCHIVE/drs-tools/

| Document | Purpose |
|----------|---------|
| `createopsitem.yaml` | Create OpsItem for tracking |
| `manualapproval.yml` | Manual approval gate |

---

## Recommended Implementation Phases

### Phase 1: Foundation (Weeks 1-4)
1. Deploy DR Orchestrator baseline in central account
2. Deploy cross-account roles to all 40+ source accounts
3. Deploy DRS Configuration Synchronizer
4. Create initial manifests for 1 application

### Phase 2: DRS Integration (Weeks 5-8)
1. Integrate DRS module with multi-staging-account support
2. Implement wave-based recovery for first application
3. Add PreWave/PostWave SSM automation
4. Test drill workflow end-to-end

### Phase 3: Scale (Weeks 9-12)
1. Add remaining applications to manifests
2. Implement parallel execution across staging accounts
3. Add CloudWatch dashboards for monitoring
4. Implement SNS notifications for each phase

### Phase 4: Non-DRS Services (Weeks 13-16)
1. Add RDS/Aurora failover modules
2. Add Route 53 DNS failover
3. Add customer VPN notification workflow
4. Full DR test with all 1000 servers

---

## Cost Estimate Update

Based on reference architecture complexity:

| Component | Effort | Cost Range |
|-----------|--------|------------|
| Main Orchestrator Step Function | 2-3 weeks | $40-60K |
| Multi-Staging Account DRS Module | 3-4 weeks | $60-80K |
| Wave-Based Recovery Integration | 2-3 weeks | $40-60K |
| Cross-Account Role Deployment | 1-2 weeks | $20-40K |
| SSM Automation Runbooks (20+) | 3-4 weeks | $60-80K |
| CloudWatch Dashboards | 1 week | $15-25K |
| Testing & Validation | 4-6 weeks | $80-120K |
| **Total** | **16-23 weeks** | **$315-465K** |

This is lower than previous estimates because the reference architecture provides 60-70% of the code.

---

## Key Files to Study

### Must Read
1. `dr-orchestration-artifacts/README.md` - Overall architecture
2. `drs-tools/drs-plan-automation/README.MD` - Wave-based recovery
3. `dr-orchestration-artifacts/src/modulefactory/modules/drs.py` - DRS integration
4. `drs-tools/drs-configuration-synchronizer/README.md` - Multi-account config sync

### Step Function Definitions
1. `dr-orchestration-artifacts/src/dr-orchestrator/DR-Orchestrator.yaml`
2. `dr-orchestration-artifacts/src/dr-orchestrator/Lifecycle-Orchestrator.yaml`
3. `dr-orchestration-artifacts/src/dr-orchestrator/ModuleFactory.yaml`
4. `drs-tools/drs-plan-automation/cfn/lambda/drs-plan-automation/template.yaml`

### Module Examples
1. `dr-orchestration-artifacts/src/modulefactory/modules/drs.py`
2. `dr-orchestration-artifacts/src/modulefactory/modules/mysql.py`
3. `dr-orchestration-artifacts/src/modulefactory/modules/r53record.py`
