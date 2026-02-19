# DRS Agent Deployer - Quick Start Guide

## For Developers Starting Implementation

### Step 1: Understand the Feature (5 minutes)

**What it does:**
- Automates DRS agent deployment to EC2 instances
- Supports same-account and cross-account replication
- Centralized orchestration from one account

**Key concepts:**
- **Source Account**: Where EC2 instances run and agents are installed
- **Staging Account**: Where DRS staging area is created and data replicates to
- **Orchestration Account**: Central account that manages deployments

### Step 2: Review the Spec (15 minutes)

1. **Read `requirements.md`** - Focus on:
   - US-1 to US-3 (core deployment patterns)
   - US-6 (cross-account role assumption)
   - NFR-1 to NFR-3 (performance, security, reliability)

2. **Skim `design.md`** - Focus on:
   - Architecture Overview section
   - Component Design for Lambda function
   - Data Flow diagrams

3. **Open `tasks.md`** - This is your implementation checklist

### Step 3: Current Status

✅ **Phase 1 Complete**: Core Lambda function implemented
- File: `lambda/drs-agent-deployer/index.py`
- 695 lines of Python code
- Supports both deployment patterns
- Test events created

🚧 **Phase 2 Next**: CloudFormation Integration
- Add Lambda to `cfn/lambda-stack.yaml`
- Deploy to dev environment
- Test end-to-end

### Step 4: Start Implementation (Now!)

Open `tasks.md` and start with **Phase 2: CloudFormation Integration**

```bash
# Open the tasks file
code .kiro/specs/drs-agent-deployer/tasks.md

# Or view in terminal
cat .kiro/specs/drs-agent-deployer/tasks.md
```

**First task**: Add `DRSAgentDeployerFunction` to `cfn/lambda-stack.yaml`

### Step 5: Reference Documentation

When you need details, check `reference/` folder:

| File | Use When |
|------|----------|
| `DRS_AGENT_DEPLOYMENT_GUIDE.md` | Need deployment examples, API usage |
| `DRS_CROSS_ACCOUNT_REPLICATION.md` | Setting up cross-account pattern |
| `DRS_AGENT_DEPLOYMENT_FRONTEND_INTEGRATION.md` | Building UI components |
| `DRS_CROSS_ACCOUNT_REPLICATION_COMPLETE.md` | Implementation summary |

## Quick Commands

### Test Lambda Locally
```bash
# Validate syntax
python3 -m py_compile lambda/drs-agent-deployer/index.py

# Run with test event (after deployment)
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-drs-agent-deployer-dev \
  --payload file://lambda/drs-agent-deployer/test-events/single-account.json \
  response.json
```

### Deploy to Dev
```bash
# Full deployment
./scripts/deploy.sh dev

# Lambda only (faster)
./scripts/deploy.sh dev --lambda-only

# Skip tests (fastest)
./scripts/deploy.sh dev --lambda-only --quick
```

### Check Logs
```bash
# Tail logs
aws logs tail /aws/lambda/hrp-drs-tech-adapter-drs-agent-deployer-dev --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/hrp-drs-tech-adapter-drs-agent-deployer-dev \
  --filter-pattern "ERROR"
```

## Implementation Checklist

Use this as your daily checklist:

### Today (Phase 2)
- [ ] Add Lambda function to `cfn/lambda-stack.yaml`
- [ ] Add CloudWatch Logs group
- [ ] Add outputs (ARN, name)
- [ ] Package Lambda function
- [ ] Deploy to dev
- [ ] Test with single-account event
- [ ] Test with cross-account event

### This Week (Phase 3)
- [ ] Add API Gateway endpoints
- [ ] Test API with cURL
- [ ] Update API documentation

### Next Week (Phase 4)
- [ ] Create TypeScript types
- [ ] Add API service methods
- [ ] Create UI components
- [ ] Integrate into Protection Groups page
- [ ] Test UI workflows

## Common Questions

**Q: Where is the Lambda function code?**
A: `lambda/drs-agent-deployer/index.py` (already complete)

**Q: What CloudFormation file do I edit?**
A: `cfn/lambda-stack.yaml` (add new resources)

**Q: How do I test without deploying?**
A: You can't fully test without deployment, but you can validate syntax locally

**Q: What if I break something?**
A: Use `./scripts/deploy.sh dev --skip-push` to test without pushing to git

**Q: Where do I add API endpoints?**
A: `cfn/api-gateway-operations-methods-stack.yaml`

**Q: Where do I create UI components?**
A: `frontend/src/components/` (create new files)

## Need Help?

1. **Check the design doc**: `design.md` has detailed architecture
2. **Check reference docs**: `reference/` folder has examples
3. **Check existing code**: Look at other Lambda functions in `cfn/lambda-stack.yaml`
4. **Check CloudWatch Logs**: Runtime errors show up there

## Success Criteria

You'll know you're done with Phase 2 when:
- ✅ Lambda function appears in AWS Console
- ✅ CloudWatch Logs group exists
- ✅ Test event returns successful deployment
- ✅ DRS source servers appear in console

## Let's Go! 🚀

Open `tasks.md` and start checking off tasks!

```bash
code .kiro/specs/drs-agent-deployer/tasks.md
```
