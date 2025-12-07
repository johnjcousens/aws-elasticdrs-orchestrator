# AWS DRS Orchestration Solution

A serverless disaster recovery orchestration platform providing VMware SRM-like capabilities for AWS Elastic Disaster Recovery (DRS).

---

## 🚨 SESSION 70 - CRITICAL FIX READY FOR DEPLOYMENT

**Issue**: Multi-disk server drills fail with `ec2:DeleteVolume` permission denied  
**Root Cause**: IAM condition blocking DRS staging volume cleanup  
**Status**: ✅ FIX READY - CloudFormation updated, awaiting deployment

### 📋 Quick Links
- **[Deploy Fix Now](DEPLOY_DELETEVOLUME_FIX.md)** - 10-minute deployment guide
- **[Root Cause Analysis](docs/DRS_DETACHVOLUME_ROOT_CAUSE_ANALYSIS.md)** - Why Server 2 failed 10 min after Server 1 succeeded
- **[Session 70 Notes](docs/SESSION_70_DELETEVOLUME_FIX.md)** - Complete technical details and lessons learned

### 🎯 What Changed

**Problem**: IAM policy had `ec2:DeleteVolume` permission BUT with condition requiring `AWSElasticDisasterRecoveryManaged: true` tag. DRS staging volumes use `drs.amazonaws.com-*` tags instead.

**Fix**: Removed blocking IAM condition from `cfn/lambda-stack.yaml` (OrchestrationRole + ApiHandlerRole)

**Deploy**:
```bash
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name drs-orchestration-test \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

**Test**: Both servers should now LAUNCH successfully in DRS drills.

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

**Latest Work**: DRS ec2:DeleteVolume IAM Condition Fix (Session 70)  
**Status**: ✅ FIX READY FOR DEPLOYMENT  
**Next Step**: Deploy CloudFormation update, then run clean DRS drill test

### Session 70 Summary

**Problem**: DRS Job had 2 servers - Server 1 LAUNCHED, Server 2 FAILED 10 minutes later with `ec2:DeleteVolume` permission denied.

**Root Cause**: IAM condition required `AWSElasticDisasterRecoveryManaged: true` tag, but DRS staging volumes use `drs.amazonaws.com-*` tags.

**Fix Applied**:
1. ✅ Removed blocking IAM condition from OrchestrationRole in `cfn/lambda-stack.yaml`
2. ✅ Added `ec2:DetachVolume` + `ec2:DeleteVolume` to ApiHandlerRole
3. ✅ Git commit ready to push
4. ⏳ CloudFormation deployment pending

**See**: [Deploy Fix Guide](DEPLOY_DELETEVOLUME_FIX.md) | [Root Cause Analysis](docs/DRS_DETACHVOLUME_ROOT_CAUSE_ANALYSIS.md) | [Session Notes](docs/SESSION_70_DELETEVOLUME_FIX.md)

### Morning Pickup Checklist

```bash
# 1. Deploy CloudFormation fix
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name drs-orchestration-test \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1

# 2. Wait for completion
aws cloudformation wait stack-update-complete \
  --stack-name drs-orchestration-test \
  --region us-east-1

# 3. Verify IAM policy (should show DeleteVolume with NO Condition)
aws iam get-role-policy \
  --role-name drs-orchestration-test-LambdaStac-OrchestrationRole-LuY7ANIrFtME \
  --policy-name EC2Access \
  --region us-east-1 | grep -A 5 "DeleteVolume"

# 4. Run DRS drill test
# Go to https://d1wfyuosowt0hl.cloudfront.net
# Login: testuser@example.com / IiG2b1o+D$
# Execute a Recovery Plan - BOTH servers should now LAUNCH successfully
```

### Recent Milestones

- ✅ **ec2:DeleteVolume IAM Condition Fix** - Session 70 (Dec 7, 2025) - [Deploy Guide](DEPLOY_DELETEVOLUME_FIX.md)
- ✅ **ec2:DetachVolume Permission Added** - Session 69 (Dec 7, 2025)
- ✅ **Authentication Blocker RESOLVED** - Session 68
- ✅ **CloudScape Migration Complete** - 100% (27/27 tasks)
- ✅ **GitLab CI/CD Pipeline Created**

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
- [ ] Validate DRS drill with both servers launching
- [ ] Add `describe_job_log_items` to ExecutionPoller

### After DRS Validation
- [ ] Fix 5 UI display bugs (non-critical)
- [ ] Step Functions orchestration migration
- [ ] SNS notifications
- [ ] CloudWatch dashboard

---

## Version History

**v1.0.4** - December 7, 2025 (Session 70)
- 🔧 **CRITICAL FIX**: Removed IAM condition blocking `ec2:DeleteVolume` on DRS staging volumes
- Root cause: Condition required wrong tag (`AWSElasticDisasterRecoveryManaged` vs `drs.amazonaws.com-*`)
- Fixes multi-disk server drill failures during cleanup phase
- See: [Deploy Guide](DEPLOY_DELETEVOLUME_FIX.md) | [Root Cause](docs/DRS_DETACHVOLUME_ROOT_CAUSE_ANALYSIS.md)

**v1.0.3** - December 7, 2025 (Session 69)
- ec2:DetachVolume permission fix
- CloudScape migration complete (100%)
- GitLab CI/CD pipeline

**Best-Known-Config** (Tag: bfa1e9b)
- Validated CloudFormation lifecycle
- Rollback: `git checkout Best-Known-Config && git push origin main --force`

---

**Last Updated**: December 7, 2025  
**Git Repository**: `git@ssh.code.aws.dev:personal_projects/alias_j/jocousen/AWS-DRS-Orchestration.git`
