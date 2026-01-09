# QA Stack Fix Focus

## CRITICAL: Stay On Target
**Stack ARN**: `arn:aws:cloudformation:us-east-1:438465159935:stack/aws-drs-orchestrator-qa/d38a2b80-ed11-11f0-9317-0affed40063f`

## Current Mission
Fix the broken execution-finder/execution-poller system in QA stack and test everything comprehensively.

## Key Resources
- **API Endpoint**: `https://ibenlje0zj.execute-api.us-east-1.amazonaws.com/dev`
- **Frontend URL**: `https://d3u3jnx97pt51j.cloudfront.net`
- **Test User**: `testuser@example.com` / `TestPassword123!`
- **User Pool**: `us-east-1_FjN6ym9ub`
- **Client ID**: `6flp1qbehh8fdh79hlv4fo077a`

## Problem Identified
- **Execution ID**: `2a0db92f-2cf2-4e6a-a84b-7452fcb0a3f9`
- **Status**: PAUSED (legitimate - has TaskToken for Step Functions waitForTaskToken)
- **DRS Job**: `drsjob-55f05e2afe4582703` - **COMPLETED** with servers **LAUNCHED**
- **Issue**: execution-poller never updated server statuses from "STARTED" to "LAUNCHED"
- **Result**: Resume button broken because servers appear incomplete
- **Lambda Issue**: execution-poller has "Runtime.ImportModuleError: No module named 'index'"

## Architecture Reference (from /archive folder)
- **Orchestration Lambda**: starts DRS job → sets status to "POLLING"
- **Execution-finder**: EventBridge scheduled (1 minute) → finds executions with "POLLING" status
- **Execution-poller**: updates DRS job progress and server statuses in DynamoDB
- **Frontend**: shows real-time progress from DynamoDB (3-second polling for active executions)
- **Step Functions**: waitForTaskToken pattern for pause/resume (supports up to 1 year pauses)
- **Timeout Threshold**: Should be 14,400 seconds (4 hours) for execution-poller, not 1800 seconds (30 minutes)
- **Step Functions**: Supports up to 1 year pauses (waitForTaskToken pattern)

## Authentication & Access
- **Test User**: `testuser@example.com`
- **Password**: `TestPassword123!`
- **User Pool ID**: `us-east-1_FjN6ym9ub`
- **Client ID**: `6flp1qbehh8fdh79hlv4fo077a`

### API Authentication
```bash
# Get JWT token for API access
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id us-east-1_FjN6ym9ub \
  --client-id 6flp1qbehh8fdh79hlv4fo077a \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=testuser@example.com,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Test API endpoints
curl -H "Authorization: Bearer $TOKEN" "https://ibenlje0zj.execute-api.us-east-1.amazonaws.com/dev/executions"
curl -H "Authorization: Bearer $TOKEN" "https://ibenlje0zj.execute-api.us-east-1.amazonaws.com/dev/executions/2a0db92f-2cf2-4e6a-a84b-7452fcb0a3f9"
```

### Frontend Access
- **URL**: `https://d3u3jnx97pt51j.cloudfront.net`
- **Login**: Use same credentials (`testuser@example.com` / `TestPassword123!`)
- **Playwright Testing**: Available if needed for UI automation

## User Instructions
- **Test APIs**: Use curl with JWT token authentication (see commands above)
- **Test Frontend**: Use Playwright if needed for UI testing
- **Create Users**: Can create new Cognito users if needed for testing
- **Use Historian**: Take regular snapshots with mcp_context_historian_mcp_create_checkpoint
- **Reference Archive**: Use `/archive/commit-9546118-uncorrupted/` for working code reference
- **Check Docs**: Use archive `/docs/requirements` and README for architecture understanding

## Requirements Documentation Reference
- **Software Requirements**: `archive/commit-9546118-uncorrupted/docs/requirements/SOFTWARE_REQUIREMENTS_SPECIFICATION.md`
- **UX Page Specs**: `archive/commit-9546118-uncorrupted/docs/requirements/UX_PAGE_SPECIFICATIONS.md`
- **Component Library**: `archive/commit-9546118-uncorrupted/docs/requirements/UX_COMPONENT_LIBRARY.md`
- **Architecture**: execution-finder (EventBridge 1min) → finds POLLING executions → execution-poller updates DRS job status
- **Real-time Updates**: Frontend polls every 3 seconds for active executions
- **Timeout**: Step Functions should support up to 1 year pauses (31,536,000 seconds)

## Current Status
- ✅ API working and authenticated
- ✅ DRS job completed successfully (both servers LAUNCHED)
- ✅ execution-poller Lambda packaging fixed
- ❌ Execution incorrectly marked as TIMEOUT (51 minutes > 30 minute threshold)
- ❌ Server statuses show "UNKNOWN" instead of "LAUNCHED" in DynamoDB
- ❌ Timeout threshold too aggressive (30 minutes vs 1 year requirement)
- ❌ Resume button broken due to incorrect status

## Fix Strategy
1. ✅ Fix execution-poller Lambda packaging issue (COMPLETED)
2. Fix timeout threshold - increase from 30 minutes to 1 year (31,536,000 seconds)
3. Manually trigger execution-poller to update server statuses for stuck execution
4. Test resume functionality via API
5. Verify execution-finder/execution-poller system works automatically
6. Test frontend with Playwright if needed
7. Document progress with historian snapshots

## DO NOT
- Work on main stack
- Work on other stacks  
- Get distracted by pipeline issues
- Focus on anything except QA stack execution fix
- Lose context - use historian MCP regularly