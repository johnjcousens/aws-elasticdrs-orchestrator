---
inclusion: always
---

# AWS Stack Protection Rules

## ⛔⛔⛔ ABSOLUTE PROHIBITION - READ FIRST ⛔⛔⛔

**STOP. Before executing ANY AWS CLI or CloudFormation command:**

### BANNED PATTERNS - NEVER EXECUTE:
```
❌ ANY command containing "elasticdrs-orchestrator-test"
❌ ANY command containing "-test" stack suffix
❌ aws dynamodb * --table-name *-test
❌ aws lambda * --function-name *-test
❌ aws cloudformation * --stack-name *-test
```

### ALLOWED PATTERNS - DEV ONLY:
```
✅ aws dynamodb * --table-name *-dev
✅ aws lambda * --function-name *-dev  
✅ Stack names ending in "-dev"
```

**If you see "-test" in any resource name, STOP IMMEDIATELY.**

---

## CRITICAL: Protected CloudFormation Stacks

### NEVER TOUCH THESE STACKS

The following CloudFormation stacks are **PRODUCTION CRITICAL** and must **NEVER** be modified, updated, or deleted under any circumstances:

- `hrp-drs-tech-adapter-dev` (master stack)
- `hrp-drs-tech-adapter-dev-*` (all nested stacks)
- `hrp-drs-tech-adapter-github-oidc-dev` (OIDC authentication stack)

### Why These Stacks Are Protected

These stacks contain:
- Production authentication infrastructure (GitHub/GitLab OIDC)
- Live API Gateway endpoints
- Active Lambda functions
- Production databases with live data
- CloudFront distributions serving production traffic
- Cognito user pools with real user accounts

### Consequences of Modification

Modifying these stacks would:
- Break production authentication
- Cause service outages
- Delete production data
- Disrupt active user sessions
- Require manual recovery procedures

### Correct Development Stack

For development and testing, use:
- Stack name: `aws-drs-orch-dev`
- Environment: `dev`
- Deployment bucket: `aws-drs-orch-dev`
- Stack ARN: `arn:aws:cloudformation:us-east-2:891376951562:stack/aws-drs-orch-dev/0f8d1db0-f3d7-11f0-af5c-0eb8e4e8f475`

### Verification Before Any Stack Operation

Before ANY CloudFormation operation, verify:
1. Stack name ends with `-dev` (not `-test`)
2. Environment parameter is `dev` (not `test`)
3. You are NOT operating on protected stacks

### Emergency Procedures

If you accidentally target a protected stack:
1. IMMEDIATELY cancel the operation
2. Do NOT proceed with any changes
3. Notify the team immediately
4. Document the incident

## Always Follow Rules

- **ALWAYS** verify stack name before any CloudFormation operation
- **ALWAYS** use `-dev` environment for development work
- **NEVER** assume a stack is safe to modify without verification
- **NEVER** use wildcards or patterns that could match protected stacks
