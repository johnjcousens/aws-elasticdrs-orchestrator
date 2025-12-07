# AWS DRS Orchestration Solution

A serverless disaster recovery orchestration platform providing VMware SRM-like capabilities for AWS Elastic Disaster Recovery (DRS).

---

## ✅ SESSION 70 - IAM FIX & STEP FUNCTIONS ORCHESTRATION

**Issue**: DRS drills failed with `ec2:StartInstances` permission denied  
**Root Cause**: IAM conditions incompatible with DRS tagging behavior  
**Status**: ✅ IAM FIX DEPLOYED - DRS drills working, Step Functions orchestration in progress

### 📋 Session Links

- **[Session 70 Root Cause](docs/SESSION_70_FINAL_ROOT_CAUSE.md)** - Why IAM conditions blocked DRS operations
- **[Session 70 Final Analysis](docs/SESSION_70_FINAL_ANALYSIS.md)** - Complete analysis
- **[Deploy Guide](DEPLOY_DELETEVOLUME_FIX.md)** - Deployment instructions (COMPLETED)

### 🎯 Validation Results

**IAM Fix Validated** (Job: drsjob-3949c80becf56a075):

- ✅ EC2AMAZ-4IMB9PN (s-3c1730a9e0771ea14) → i-097556fe6481c1d3a LAUNCHED
- ✅ EC2AMAZ-RLP9U5V (s-3d75cdc0d9a28a725) → i-06ea360aab5e258fd LAUNCHED
- ✅ Status: COMPLETED - Both servers launched successfully

**IAM Policy Verified**:

```yaml
ec2:StartInstances - NO condition ✅
ec2:DeleteVolume - NO condition ✅
ec2:DetachVolume - NO condition ✅
```

**Step Functions Bug Fixed**: The orchestration Lambda was incorrectly requiring `recoveryInstanceID` from the job response. DRS doesn't always populate this field in the job response - it populates it on the source server instead. Fixed to trust LAUNCHED status.

---

## ⚠️ CRITICAL DEBUGGING RULE

**DO NOT investigate DRS configuration, launch settings, or launch templates.**

The CLI works - drills execute successfully via AWS CLI. If a drill fails through Lambda/Step Functions, **the problem is ALWAYS in the code**, not DRS configuration.

```bash
# Proven working CLI command:
aws drs start-recovery --source-servers sourceServerID=s-3578f52ef3bdd58b4 --is-drill --region us-east-1
```

When debugging: Check Lambda code → IAM permissions → Step Functions logic. **NEVER** investigate DRS launch templates or replication settings.

---

## 🔍 DRS API & Step Functions Coordination

### Core Pattern: Lambda Polling with Step Functions Wait States

AWS DRS does NOT provide event-driven notifications. The proven pattern uses **polling**:

```python
# 1. Start recovery for ALL servers in wave (ONE API call)
response = drs_client.start_recovery(
    sourceServers=[{'sourceServerID': sid} for sid in server_ids],
    isDrill=True
    # NO tags parameter - causes conversion phase to be skipped!
)
job_id = response['job']['jobID']  # ONE job ID for entire wave

# 2. Poll job status (Step Functions Wait state)
job_status = drs_client.describe_jobs(filters={'jobIDs': [job_id]})

# 3. CRITICAL: Poll per-server launch status (WE NEED TO ADD THIS)
log_items = drs_client.describe_job_log_items(jobID=job_id)
```

### DRS Job Status Progression

**Job-Level**: `PENDING → STARTED → COMPLETED`  
**Per-Server**: `PENDING → IN_PROGRESS → LAUNCHED` (or `FAILED`)

### Our Implementation Status

| Feature | Status | Location |
|---------|--------|----------|
| ONE API call per wave | ✅ Correct | `orchestration_stepfunctions.py` |
| No tags parameter | ✅ Correct | `start_recovery()` call |
| Wave-level job tracking | ✅ Correct | `execution_poller.py` |
| `describe_job_log_items` polling | ❌ Missing | Need to add |
| Per-server launch status extraction | ❌ Missing | Need to add |
| EC2 instance ID tracking | ⚠️ Partial | Uses `recoveryInstanceID` from `participatingServers` |

### Next Step: Add to ExecutionPoller Lambda

The current `poll_wave_status()` in `lambda/poller/execution_poller.py` uses `describe_jobs()` but should also call `describe_job_log_items()`:

```python
def poll_wave_status(wave: Dict[str, Any], execution_type: str) -> Dict[str, Any]:
    job_id = wave.get('JobId')
    
    # EXISTING: Query job status
    job_status = query_drs_job_status(job_id)
    
    # ADD THIS: Query per-server launch events
    log_items = query_drs_job_log_items(job_id)
    
    # Extract EC2 instance IDs from LAUNCH_FINISHED events
    for item in log_items:
        if item['event'] == 'LAUNCH_FINISHED':
            server_id = item['eventData']['sourceServerID']
            instance_id = item['eventData'].get('ec2InstanceID')
            # Update server record with instance_id

def query_drs_job_log_items(job_id: str) -> List[Dict]:
    """Query per-server launch status from DRS."""
    log_items = []
    paginator = drs.get_paginator('describe_job_log_items')
    for page in paginator.paginate(jobID=job_id):
        log_items += page['items']
    return log_items
```

**Reference**: See `archive/drs-tools/drs-plan-automation/` for complete working implementation.

---

## 🎯 CURRENT STATUS - December 7, 2025

**Latest Work**: DRS IAM Fix + Step Functions Bug Fix (Session 70)  
**Status**: ✅ IAM FIX VALIDATED - Testing multi-wave Step Functions orchestration  
**Next Step**: Complete 3-wave drill test via UI

### Session 70 Summary

**IAM Fix Validated** (Job: drsjob-3949c80becf56a075):

- ✅ EC2AMAZ-4IMB9PN (s-3c1730a9e0771ea14) → LAUNCHED
- ✅ EC2AMAZ-RLP9U5V (s-3d75cdc0d9a28a725) → LAUNCHED

**Step Functions Bug Fixed**:
The orchestration Lambda was checking `recoveryInstanceID` from the job response, but DRS doesn't always populate that field there. Fixed to trust LAUNCHED status without requiring the instance ID from the job response.

**3-Wave Drill Test In Progress** (3TierTest plan):

- Wave 0 (Database): EC2AMAZ-FQTJG64 - ✅ LAUNCHED
- Wave 1 (App): EC2AMAZ-H0JBE4J - depends on wave-0
- Wave 2 (Web): EC2AMAZ-4IMB9PN - depends on wave-1

**See**: [Session 70 Root Cause](docs/SESSION_70_FINAL_ROOT_CAUSE.md) | [Session 70 Final Analysis](docs/SESSION_70_FINAL_ANALYSIS.md)

### Recent Milestones

- ✅ **Step Functions Bug Fixed** - Session 70 (Dec 7, 2025) - Trust LAUNCHED status
- ✅ **IAM Condition Fix Deployed** - Session 70 (Dec 7, 2025) - [Root Cause](docs/SESSION_70_FINAL_ROOT_CAUSE.md)
- ✅ **ec2:DetachVolume Permission Added** - Session 69 (Dec 7, 2025)
- ✅ **Authentication Blocker RESOLVED** - Session 68
- ✅ **CloudScape Migration Complete** - 100% (27/27 tasks)

---

## Quick Start

### Current Deployment (TEST Environment)

| Resource | Value |
|----------|-------|
| Frontend | https://d1wfyuosowt0hl.cloudfront.net |
| API | https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test |
| Region | us-east-1 |
| Account | 777788889999 |
| Test User | testuser@example.com / IiG2b1o+D$ |

### Deploy New Stack

```bash
aws cloudformation deploy \
  --template-url https://aws-drs-orchestration.s3.us-east-1.amazonaws.com/cfn/master-template.yaml \
  --stack-name drs-orchestration \
  --parameter-overrides \
    ProjectName=drs-orchestration \
    Environment=prod \
    SourceBucket=aws-drs-orchestration \
    AdminEmail=your-email@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

**Deployment Time**: ~20-30 minutes

For detailed deployment instructions, see [Deployment Guide](docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md).

---

## Key Features

### Protection Groups
- Automatic DRS server discovery by region
- Visual server selection with assignment tracking
- Single server per group constraint
- Real-time search and 30-second auto-refresh

### Recovery Plans
- Wave-based orchestration with dependencies
- Pre/post-wave SSM automation
- Drill mode for testing without production impact

### Execution Monitoring
- Real-time wave progress with CloudScape Stepper
- Complete execution history and audit trail
- CloudWatch Logs integration

---

## Architecture

### Modular CloudFormation Stacks

| Stack | Purpose |
|-------|---------|
| master-template.yaml | Root orchestrator |
| database-stack.yaml | DynamoDB tables (3) |
| lambda-stack.yaml | Lambda functions (4) + IAM |
| api-stack.yaml | Cognito + API Gateway + Step Functions |
| security-stack.yaml | WAF + CloudTrail (optional) |
| frontend-stack.yaml | S3 + CloudFront |

### Components

- **Frontend**: React 18.3 with AWS CloudScape Design System
- **API**: API Gateway REST API with Cognito auth
- **Backend**: Python 3.12 Lambda functions
- **Orchestration**: Step Functions for wave execution
- **Data**: DynamoDB (Protection Groups, Recovery Plans, Execution History)

---

## Lambda Deployment

```bash
cd lambda

# Direct deployment (fastest - development)
python3 deploy_lambda.py --direct \
  --function-name drs-orchestration-api-handler-test \
  --region us-east-1

# Full deployment (S3 + Direct)
python3 deploy_lambda.py --full \
  --bucket aws-drs-orchestration \
  --function-name drs-orchestration-api-handler-test \
  --region us-east-1
```

See [Lambda Deployment Guide](docs/LAMBDA_DEPLOYMENT_GUIDE.md) for all options.

---

## S3 Repository Sync

Auto-sync enabled by default on every `git push`.

```bash
make sync-s3           # Manual sync
make sync-s3-build     # Build frontend and sync
make sync-s3-dry-run   # Preview changes
```

See [S3 Sync Automation](docs/S3_SYNC_AUTOMATION.md) for details.

---

## API Endpoints

### Protection Groups
- `GET /protection-groups` - List all
- `POST /protection-groups` - Create
- `PUT /protection-groups/{id}` - Update
- `DELETE /protection-groups/{id}` - Delete

### DRS Server Discovery
- `GET /drs/source-servers?region={region}` - Discover servers with assignment status

### Recovery Plans
- `GET /recovery-plans` - List all
- `POST /recovery-plans` - Create
- `PUT /recovery-plans/{id}` - Update
- `DELETE /recovery-plans/{id}` - Delete

### Executions
- `GET /executions` - List history
- `POST /executions` - Start execution
- `GET /executions/{id}` - Get details

---

## Documentation

### Core Docs
- [Deployment Guide](docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md) - Complete deployment instructions
- [Lambda Deployment Guide](docs/LAMBDA_DEPLOYMENT_GUIDE.md) - Lambda deployment automation
- [S3 Sync Automation](docs/S3_SYNC_AUTOMATION.md) - Repository sync workflow
- [Project Status](docs/PROJECT_STATUS.md) - Session history and tracking

### Architecture & Design
- [Architectural Design Document](docs/architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md)
- [Product Requirements](docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md)
- [DRS Integration Rules](docs/DRS_INTEGRATION_RULES.md) - 25 prescriptive rules

### DRS Integration
- [DRS + Step Functions Analysis](docs/DRS_STEP_FUNCTIONS_COORDINATION_ANALYSIS.md)
- [Gap Analysis](docs/DRS_PLAN_AUTOMATION_GAP_ANALYSIS.md) - 5 missing features
- [Integration Guide](docs/DRS_TOOLS_COMPLETE_INTEGRATION_GUIDE.md)
- [DR Orchestration Artifacts Analysis](docs/DR_ORCHESTRATION_ARTIFACTS_ANALYSIS.md) - Enterprise features evaluation

### Security
- [Code Review Findings](docs/CODE_REVIEW_FINDINGS.md) - 15+ findings with fixes

---

## Troubleshooting

### Common Issues

**API Gateway 401 Unauthorized**
- Verify Cognito token is valid and not expired
- Check API Gateway authorizer configuration

**DRS Recovery Fails**
- Check Lambda IAM permissions (OrchestrationRole)
- Review CloudTrail for exact API errors
- **Never** investigate DRS launch templates

**Frontend Build Fails**
- Verify Node.js 18+ available
- Check frontend-builder Lambda logs

### Debug Commands

```bash
# Check Lambda errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/drs-orchestration-api-handler-test \
  --filter-pattern "ERROR" \
  --region us-east-1

# Check execution status
aws dynamodb get-item \
  --table-name execution-history-test \
  --key '{"ExecutionId":{"S":"xxx"},"PlanId":{"S":"yyy"}}' \
  --region us-east-1
```

---

## Roadmap

### Immediate Priority

- [x] Validate DRS drill with both servers launching - ✅ COMPLETE (Session 70)
- [x] Fix Step Functions LAUNCHED status detection - ✅ COMPLETE (Session 70)
- [ ] Complete 3-wave drill test via UI (in progress)
- [ ] Add `describe_job_log_items` to ExecutionPoller Lambda
- [ ] Implement CloudWatch dashboard for failures (2 days)
- [ ] Add structured logging (3 days)

### Enterprise Features (Phase 2)
- [ ] Approval workflow (SNS + callback) (5 days)
- [ ] Parameter resolution (SSM/CloudFormation) (3 days)
- [ ] Modular resource architecture (10 days)
- [ ] Fix 5 UI display bugs (non-critical)
- [ ] SNS notifications

---

## Version History

**v1.0.4** - December 7, 2025 (Session 70)

- ✅ **IAM FIX VALIDATED**: Both servers launched successfully (Job: drsjob-3949c80becf56a075)
- 🔧 **Step Functions Bug Fixed**: Trust LAUNCHED status without requiring recoveryInstanceID
- Fixed `ec2:StartInstances` permission by removing IAM conditions
- Root cause: IAM conditions incompatible with DRS tagging behavior
- See: [Root Cause Analysis](docs/SESSION_70_FINAL_ROOT_CAUSE.md) | [Deploy Guide](DEPLOY_DELETEVOLUME_FIX.md)

**v1.0.3** - December 7, 2025 (Session 69)

- ec2:DetachVolume permission fix
- CloudScape migration complete (100%)
- GitLab CI/CD pipeline

**Best-Known-Config** (Tag: bfa1e9b)

- Validated CloudFormation lifecycle
- Rollback: `git checkout Best-Known-Config && git push origin main --force`

---

**Last Updated**: December 7, 2025 (Session 70)  
**Git Repository**: `git@ssh.code.aws.dev:personal_projects/alias_j/jocousen/AWS-DRS-Orchestration.git`
