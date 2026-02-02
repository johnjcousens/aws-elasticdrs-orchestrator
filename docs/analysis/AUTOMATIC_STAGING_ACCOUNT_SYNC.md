# Automatic Staging Account Sync

## Problem Statement

When users modify DRS extended source servers (remove old ones, add new ones with different staging accounts), the staging accounts stored in DynamoDB don't automatically update. This causes:

- Dashboard showing stale staging account information
- Settings modal displaying outdated staging accounts
- Capacity calculations using wrong staging account data

The root cause: **Staging accounts are discovered once during target account creation, then remain static in DynamoDB.**

## Solution: Automatic Background Sync

Implemented a scheduled Lambda operation that runs every 5 minutes to automatically discover and sync staging accounts for all target accounts.

### Architecture

```
EventBridge Schedule (rate(5 minutes))
    ↓
Query Handler Lambda (operation: sync_staging_accounts)
    ↓
For each target account:
    ├─→ Discover staging accounts from DRS extended source servers
    ├─→ Compare with current DynamoDB staging accounts
    └─→ Update DynamoDB if changes detected
```

### Implementation Details

**1. EventBridge Schedule Rule**
- Schedule: `rate(5 minutes)`
- Target: Query Handler Lambda
- Payload: `{"operation": "sync_staging_accounts"}`
- Can be disabled via `EnableStagingAccountSync` parameter

**2. Query Handler Operation**
- New operation: `handle_sync_staging_accounts()`
- Scans all target accounts from DynamoDB
- For each account:
  - Calls `discover_staging_accounts_from_drs()` to find current staging accounts
  - Compares discovered IDs with current DynamoDB IDs
  - Calls `update_staging_accounts()` if changes detected
- Returns sync summary with counts and details

**3. Sync Logic**
```python
# Get current staging accounts from DynamoDB
current_ids = {sa.get("accountId") for sa in current_staging}

# Discover from DRS
discovered_ids = {sa.get("accountId") for sa in discovered}

# Update if different
if current_ids != discovered_ids:
    added = discovered_ids - current_ids
    removed = current_ids - discovered_ids
    update_staging_accounts(account_id, discovered)
```

### Sync Results

The sync operation returns detailed results:

```json
{
  "timestamp": "2026-02-02T22:45:00Z",
  "totalAccounts": 5,
  "accountsProcessed": 5,
  "accountsUpdated": 1,
  "accountsSkipped": 4,
  "accountsFailed": 0,
  "details": [
    {
      "accountId": "111122223333",
      "accountName": "DEMO_TARGET",
      "status": "updated",
      "added": ["777788889999"],
      "removed": ["444455556666"],
      "totalStaging": 1
    },
    {
      "accountId": "123456789012",
      "accountName": "Production",
      "status": "unchanged",
      "stagingAccountCount": 2
    }
  ]
}
```

### Skip Conditions

Accounts are skipped (not synced) if:
1. **Current account** - No staging accounts (replicates to itself)
2. **No role ARN** - Can't assume cross-account role to query DRS
3. **No changes** - Discovered staging accounts match current DynamoDB state

### CloudFormation Parameters

**New Parameter:**
```yaml
EnableStagingAccountSync:
  Type: String
  Default: 'true'
  AllowedValues: ['true', 'false']
  Description: Enable automatic staging account discovery and sync
```

**EventBridge Stack Changes:**
- Added `QueryHandlerFunctionArn` parameter
- Added `StagingAccountSyncScheduleRule` resource
- Added `StagingAccountSyncSchedulePermission` for Lambda invocation
- Added condition `EnableStagingAccountSyncCondition`

**Master Template Changes:**
- Pass `QueryHandlerFunctionArn` to EventBridge stack
- Set `EnableStagingAccountSync: 'true'` by default

## Benefits

1. **Zero User Burden** - Completely automatic, no manual refresh needed
2. **Always Up-to-Date** - Staging accounts sync every 5 minutes
3. **Transparent** - Users see current state without knowing sync is happening
4. **Efficient** - Only updates when changes detected
5. **Resilient** - Continues syncing even if individual accounts fail
6. **Observable** - Detailed sync logs for troubleshooting

## Deployment

Deploy using the standard workflow:

```bash
./scripts/deploy.sh test
```

This will:
1. Update query-handler Lambda with sync operation
2. Create EventBridge schedule rule
3. Wire up Lambda permissions
4. Start automatic sync every 5 minutes

## Monitoring

**CloudWatch Logs:**
```bash
# View sync logs
aws logs tail /aws/lambda/aws-drs-orchestration-query-handler-test --follow

# Filter for sync operations
aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-drs-orchestration-query-handler-test \
  --filter-pattern "staging account sync"
```

**EventBridge Rule Status:**
```bash
# Check if rule is enabled
aws events describe-rule \
  --name aws-drs-orchestration-staging-account-sync-test

# View recent invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name Invocations \
  --dimensions Name=RuleName,Value=aws-drs-orchestration-staging-account-sync-test \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 900 \
  --statistics Sum
```

## Disabling Sync

To disable automatic sync:

```bash
# Update stack with sync disabled
aws cloudformation update-stack \
  --stack-name aws-drs-orchestration-test \
  --use-previous-template \
  --parameters ParameterKey=EnableStagingAccountSync,ParameterValue=false \
  --capabilities CAPABILITY_NAMED_IAM
```

Or disable the EventBridge rule directly:

```bash
aws events disable-rule \
  --name aws-drs-orchestration-staging-account-sync-test
```

## Testing

**Manual Trigger:**
```bash
# Invoke sync operation directly
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation": "sync_staging_accounts"}' \
  response.json

cat response.json | jq .
```

**Test Scenario:**
1. Add extended source servers in DRS with new staging account
2. Wait up to 5 minutes for automatic sync
3. Check DynamoDB - new staging account should appear
4. Check dashboard - should show new staging account
5. Check CloudWatch logs - should show sync operation with "updated" status

## Related Files

- `lambda/query-handler/index.py` - Sync operation handler
- `cfn/eventbridge-stack.yaml` - EventBridge schedule rule
- `cfn/master-template.yaml` - Stack wiring
- `lambda/shared/staging_account_discovery.py` - Discovery logic
- `lambda/shared/staging_account_models.py` - DynamoDB update logic

## Related Documentation

- [Staging Account Refresh Fix](STAGING_ACCOUNT_REFRESH_FIX.md) - Frontend refresh implementation
- [DRS Cross Account Setup](../guides/DRS_CROSS_ACCOUNT_SETUP_VERIFICATION.md) - Cross-account configuration
