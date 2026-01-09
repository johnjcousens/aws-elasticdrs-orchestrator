# Fresh Deployment Focus

## CRITICAL: Fresh Start with Working Code
**Current State**: Restored to commit `59bed2d` (January 7, 2026) with working DRS endpoints and RBAC

## Current Mission
Deploy fresh stack with December 31st working code + modern CI/CD pipeline, then update for new stack configuration.

## Next Steps
1. **Deploy Fresh Stack**: Use GitHub Actions to deploy working code with proper naming (`ProjectName=aws-drs-orchestrator-qa`, `Environment=dev`)
2. **Update CI/CD Configuration**: Update GitHub Actions workflow for new stack
3. **Test End-to-End**: Verify all functionality works with fresh deployment
4. **Update Documentation**: Update all references to new stack configuration

## Key Features Restored (Commit 59bed2d)
- ✅ **Complete DRS endpoint coverage** (all 4 core DRS endpoints + recovery instances)  
- ✅ **Full RBAC implementation** (47+ endpoints with proper permissions)  
- ✅ **Working application functionality** (from the January 7th timeframe)  
- ✅ **Comprehensive DRS integration** (quotas, accounts, source servers, tag sync)
- ✅ **Modern CI/CD Pipeline** (cherry-picked from recent commits)
- ✅ **Workflow conflict prevention** (safe-push.sh, check-workflow.sh scripts)

## DRS Endpoints Available
1. **`GET /drs/source-servers`** - View DRS source servers
2. **`GET /drs/quotas`** - View DRS service quotas and limits  
3. **`GET /drs/accounts`** - View DRS account information
4. **`POST /drs/tag-sync`** - Manual tag synchronization
5. **`GET /executions/{executionId}/recovery-instances`** - View recovery instances

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