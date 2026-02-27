---
inclusion: always
---

# AWS Stack Protection Rules

## ⛔⛔⛔ ABSOLUTE PROHIBITION - READ FIRST ⛔⛔⛔

**STOP. Before executing ANY AWS CLI or CloudFormation command:**

### ALLOWED PATTERNS - TEST AND QA:
```
✅ aws dynamodb * --table-name *-test
✅ aws dynamodb * --table-name *-qa
✅ aws lambda * --function-name *-test
✅ aws lambda * --function-name *-qa
✅ Stack names ending in "-test" or "-qa"
✅ Target account setup stacks: drs-orchestration-target-account-setup (any region)
✅ Staging account setup stacks: drs-orchestration-staging-account-setup (any region)
✅ Region: us-east-2 (orchestration stacks)
✅ Region: us-east-1 (target/staging account setup stacks)
```

---

## CRITICAL: Protected CloudFormation Stacks

### NEVER TOUCH THESE STACKS

The following CloudFormation stacks are **PRODUCTION CRITICAL** and must **NEVER** be modified, updated, or deleted under any circumstances:

- `aws-drs-orchestration-prod` (production master stack)
- `aws-drs-orchestration-prod-*` (all production nested stacks)

### Why These Stacks Are Protected

These stacks contain:
- Production API Gateway endpoints
- Active Lambda functions
- Production databases with live data
- CloudFront distributions serving production traffic
- Cognito user pools with real user accounts

### Consequences of Modification

Modifying these stacks would:
- Cause service outages
- Delete production data
- Disrupt active user sessions
- Require manual recovery procedures

### Correct Development and QA Stacks

For development and testing, use:
- **Test Stack** (old architecture - protected, do not modify):
  - Stack name: `aws-drs-orchestration-test`
  - Environment: `test`
  - Deployment bucket: `aws-drs-orchestration-438465159935-test`
  - Region: `us-east-2`
  
- **QA Stack** (new architecture - for integration testing):
  - Stack name: `aws-drs-orchestration-qa`
  - Environment: `qa`
  - Deployment bucket: `aws-drs-orchestration-438465159935-qa`
  - Region: `us-east-2`

### Verification Before Any Stack Operation

Before ANY CloudFormation operation, verify:
1. Stack name ends with `-test` or `-qa`
2. Environment parameter is `test` or `qa`
3. You are NOT operating on protected production stacks
4. For test stack: Use old deploy.sh (protected, do not modify)
5. For QA stack: Use new deploy-main-stack.sh (integration testing)

### Emergency Procedures

If you accidentally target a protected stack:
1. IMMEDIATELY cancel the operation
2. Do NOT proceed with any changes
3. Notify the team immediately
4. Document the incident

## Always Follow Rules

- **ALWAYS** verify stack name before any CloudFormation operation
- **ALWAYS** use `-test` or `-qa` environment for development work
- **NEVER** assume a stack is safe to modify without verification
- **NEVER** use wildcards or patterns that could match protected production stacks
- **NEVER** modify the test stack (uses old architecture, protected)
- **ALWAYS** use QA stack for new architecture integration testing
