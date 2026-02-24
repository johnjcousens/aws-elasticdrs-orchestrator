---
inclusion: always
---

# AWS Stack Protection Rules

## ⛔⛔⛔ ABSOLUTE PROHIBITION - READ FIRST ⛔⛔⛔

**STOP. Before executing ANY AWS CLI or CloudFormation command:**

### ALLOWED PATTERNS - QA ONLY:
```
✅ aws dynamodb * --table-name *-qa
✅ aws lambda * --function-name *-qa  
✅ Stack names ending in "-qa"
✅ Region: us-east-1
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

### Correct Development Stack

For development and testing, use:
- Stack name: `aws-drs-orchestration-qa`
- Environment: `qa`
- Deployment bucket: `aws-drs-orchestration-qa`
- Region: `us-east-1`
- Stack ARN: `arn:aws:cloudformation:us-east-1:438465159935:stack/aws-drs-orchestration-qa/ae2732a0-0da7-11f1-81ab-0ebf70dc8dab`

### Verification Before Any Stack Operation

Before ANY CloudFormation operation, verify:
1. Stack name ends with `-qa` (not `-test`)
2. Environment parameter is `qa` (not `test`)
3. You are NOT operating on protected stacks

### Emergency Procedures

If you accidentally target a protected stack:
1. IMMEDIATELY cancel the operation
2. Do NOT proceed with any changes
3. Notify the team immediately
4. Document the incident

## Always Follow Rules

- **ALWAYS** verify stack name before any CloudFormation operation
- **ALWAYS** use `-qa` environment for development work
- **NEVER** assume a stack is safe to modify without verification
- **NEVER** use wildcards or patterns that could match protected stacks
