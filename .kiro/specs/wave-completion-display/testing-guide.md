# Testing Guide - Wave Completion Display

## Prerequisites

### Required Access
- AWS Console access to account 891376951562
- CloudFront URL: https://d1kqe40a9vwn47.cloudfront.net
- AWS CLI configured with appropriate credentials
- Browser with developer tools (Chrome/Firefox recommended)

### Required DRS Setup
- At least one DRS source server configured
- Recovery plan created with one or more waves
- Servers in "Ready for recovery" state

---

## Test Execution Instructions

### Step 1: Verify Deployment Status

**Check Frontend Deployment**:
```bash
# Check CloudFront distribution
aws cloudfront get-distribution --id E3VQCJEXAMPLE --query 'Distribution.Status'

# Check S3 frontend bucket timestamp
aws s3 ls s3://hrp-drs-tech-adapter-fe-891376951562-dev/ --recursive | grep index.html
```

**Check Backend Deployment**:
```bash
# Check Lambda function last modified
aws lambda get-function \
  --function-name hrp-drs-tech-adapter-execution-handler-dev \
  --query 'Configuration.LastModified'

# Check Lambda environment variables
aws lambda get-function-configuration \
  --function-name hrp-drs-tech-adapter-execution-handler-dev \
  --query 'Environment.Variables'
```

---

### Step 2: Start Single-Wave Recovery Test

**Navigate to Application**:
1. Open browser: https://d1kqe40a9vwn47.cloudfront.net
2. Open Developer Tools (F12)
3. Go to Console tab
4. Clear console logs

**Start Recovery**:
1. Navigate to Recovery Plans page
2. Select a recovery plan with ONE wave
3. Click "Start Recovery"
4. Confirm recovery start
5. Navigate to execution details page

**Monitor Execution**:
1. Watch wave status indicator
2. Watch server status updates
3. Monitor browser console for logs
4. Take screenshots at key stages:
   - Recovery started (wave in progress)
   - Servers launching
   - Wave completed (green checkmark)
   - EC2 data displayed

**Expected Console Logs**:
```javascript
[WaveProgress] Wave 1 EC2 data availability:
  - Total servers: 2
  - Servers with EC2 data: 2/2
  - Servers missing data: 0
  - Missing fields: []

[WaveProgress] Wave status transition:
  - Wave 1: started → completed
  - Reason: endTime set and all servers launched
  - endTime: 1707667200000
  - All servers launched: true
```

**Verification Checklist**:
- [ ] Wave status shows 🔄 while in progress
- [ ] Wave status changes to ✅ when complete
- [ ] Wave status badge shows "Completed"
- [ ] Overall progress shows 100%
- [ ] Instance ID column shows actual EC2 instance IDs
- [ ] Instance ID is clickable link to AWS Console
- [ ] Type column shows EC2 instance type (e.g., t3.medium)
- [ ] Private IP column shows IP address
- [ ] Launch Time column shows timestamp
- [ ] Column header says "Server Name" (not "Server ID")
- [ ] Console logs show EC2 data availability
- [ ] Console logs show wave status transition
- [ ] No errors in console

---

### Step 3: Check Lambda CloudWatch Logs

**Find Log Stream**:
```bash
# Get recent log streams
aws logs describe-log-streams \
  --log-group-name /aws/lambda/hrp-drs-tech-adapter-execution-handler-dev \
  --order-by LastEventTime \
  --descending \
  --max-items 5

# Get log events from most recent stream
aws logs get-log-events \
  --log-group-name /aws/lambda/hrp-drs-tech-adapter-execution-handler-dev \
  --log-stream-name '<STREAM_NAME_FROM_ABOVE>' \
  --limit 100
```

**Search for Timing Logs**:
```bash
# Search for EC2 enrichment timing
aws logs filter-log-events \
  --log-group-name /aws/lambda/hrp-drs-tech-adapter-execution-handler-dev \
  --filter-pattern "[TIMING]" \
  --start-time $(date -u -d '10 minutes ago' +%s)000 \
  --limit 50
```

**Expected Log Sequence**:
```
[TIMING] Starting EC2 enrichment for wave 1
[TIMING] Calling describe_recovery_instances for 2 servers
[TIMING] describe_recovery_instances returned 2 instances
[TIMING] Calling describe_instances for 2 instance IDs
[TIMING] describe_instances returned 2 instances
[TIMING] EC2 enrichment completed in 1.23s
[TIMING] Setting wave status to 'completed'
```

**Verification Checklist**:
- [ ] EC2 enrichment starts before status update
- [ ] `describe_recovery_instances()` called successfully
- [ ] `describe_instances()` called successfully
- [ ] Enrichment completes in <2 seconds
- [ ] Wave status set to 'completed' after enrichment
- [ ] No errors during enrichment
- [ ] All servers have EC2 data populated

---

### Step 4: Verify DynamoDB Data

**Check Execution Record**:
```bash
# Get execution record
aws dynamodb get-item \
  --table-name hrp-drs-tech-adapter-execution-history-dev \
  --key '{"executionId": {"S": "<EXECUTION_ID>"}}' \
  --output json | jq '.Item'
```

**Verify Wave Data**:
```json
{
  "waveExecutions": {
    "L": [
      {
        "M": {
          "waveNumber": {"N": "1"},
          "status": {"S": "completed"},
          "endTime": {"N": "1707667200000"},
          "serverExecutions": {
            "L": [
              {
                "M": {
                  "serverId": {"S": "s-abc123"},
                  "serverName": {"S": "hrp-core-db01-az1"},
                  "launchStatus": {"S": "LAUNCHED"},
                  "recoveredInstanceId": {"S": "i-0abc123def456"},
                  "instanceType": {"S": "t3.medium"},
                  "privateIp": {"S": "10.0.1.45"},
                  "launchTime": {"N": "1707667100000"}
                }
              }
            ]
          }
        }
      }
    ]
  }
}
```

**Verification Checklist**:
- [ ] Wave has `status: "completed"`
- [ ] Wave has `endTime` set
- [ ] All servers have `launchStatus: "LAUNCHED"`
- [ ] All servers have `recoveredInstanceId`
- [ ] All servers have `instanceType`
- [ ] All servers have `privateIp`
- [ ] All servers have `launchTime`

---

### Step 5: Multi-Wave Recovery Test

**Start Multi-Wave Recovery**:
1. Select recovery plan with 2+ waves
2. Start recovery
3. Monitor each wave's progression
4. Verify wave dependencies are respected

**Expected Behavior**:
- Wave 1 starts immediately
- Wave 2 waits for Wave 1 to complete
- Each wave shows correct status
- EC2 data appears for all waves

**Verification Checklist**:
- [ ] Waves execute in sequence
- [ ] Wave 2 doesn't start until Wave 1 completes
- [ ] Each wave shows green ✅ when complete
- [ ] EC2 data appears for all servers in all waves
- [ ] Overall progress updates correctly
- [ ] Console logs show transitions for each wave

---

### Step 6: Edge Case Testing

**Test 1: Server Launch Failure**
1. Start recovery with a server that will fail
2. Verify wave status shows failed ❌
3. Verify failed server shows error indicator
4. Verify successful servers show EC2 data

**Test 2: Partial EC2 Data**
1. Check if any servers have missing EC2 fields
2. Verify missing fields show "—"
3. Check console logs for missing field warnings

**Test 3: Rapid Polling**
1. Start recovery
2. Monitor polling frequency
3. Verify no duplicate API calls
4. Verify no race conditions

---

## Troubleshooting

### Issue: Wave Status Not Updating

**Check**:
1. Browser console for errors
2. Network tab for API responses
3. Lambda logs for status update
4. DynamoDB for wave.endTime field

**Debug Commands**:
```bash
# Check API response
curl -H "Authorization: Bearer $TOKEN" \
  https://cbpdf7d52d.execute-api.us-east-2.amazonaws.com/dev/executions/<ID>

# Check Lambda logs
aws logs tail /aws/lambda/hrp-drs-tech-adapter-execution-handler-dev --follow
```

---

### Issue: Missing EC2 Data

**Check**:
1. Lambda logs for enrichment timing
2. DynamoDB for populated fields
3. DRS API for instance data
4. IAM permissions for DRS/EC2 APIs

**Debug Commands**:
```bash
# Check DRS recovery instances
aws drs describe-recovery-instances \
  --filters sourceServerIDs=s-abc123

# Check EC2 instances
aws ec2 describe-instances \
  --instance-ids i-0abc123def456
```

---

### Issue: Console Logs Not Appearing

**Check**:
1. Browser console filter settings
2. Log level settings
3. Component mounting
4. React DevTools

**Debug**:
- Clear browser cache
- Hard refresh (Ctrl+Shift+R)
- Check for JavaScript errors
- Verify component is rendering

---

## Performance Benchmarks

### Expected Timings
- **Page Load**: <2 seconds
- **API Response**: <500ms
- **EC2 Enrichment**: <2 seconds
- **Polling Interval**: 5 seconds
- **Status Update Lag**: <5 seconds

### Performance Testing
```bash
# Measure API response time
time curl -H "Authorization: Bearer $TOKEN" \
  https://cbpdf7d52d.execute-api.us-east-2.amazonaws.com/dev/executions/<ID>

# Check Lambda duration
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=hrp-drs-tech-adapter-execution-handler-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

---

## Test Data Collection

### Screenshots to Capture
1. Recovery started (wave in progress)
2. Servers launching
3. Wave completed (green checkmark)
4. EC2 data displayed
5. Browser console logs
6. CloudWatch logs
7. DynamoDB data

### Logs to Export
1. Browser console logs (copy/paste)
2. Lambda CloudWatch logs (export to file)
3. Network tab HAR file
4. DynamoDB query results

### Metrics to Record
- Page load time
- API response time
- EC2 enrichment duration
- Polling frequency
- Status update lag

---

## Success Criteria

### Functional Requirements ✅
- [ ] Wave status shows green ✅ when complete
- [ ] Wave status badge shows "Completed"
- [ ] Overall progress shows 100%
- [ ] Instance ID displays with working link
- [ ] Instance Type displays correctly
- [ ] Private IP displays correctly
- [ ] Launch Time displays correctly
- [ ] Column header says "Server Name"

### Non-Functional Requirements ✅
- [ ] Status updates within 30 seconds
- [ ] EC2 data appears within 1 minute
- [ ] No console errors
- [ ] No unnecessary API calls
- [ ] Graceful handling of missing data

### Performance Requirements ✅
- [ ] EC2 enrichment <2 seconds
- [ ] API response <500ms
- [ ] Page load <2 seconds
- [ ] Polling interval 5 seconds

---

## Reporting

### Test Report Template
```markdown
## Test Execution Summary

**Date**: [DATE]
**Tester**: [NAME]
**Environment**: test
**Status**: [PASS/FAIL]

### Tests Executed
- Single-wave recovery: [PASS/FAIL]
- Multi-wave recovery: [PASS/FAIL]
- Column headers: [PASS/FAIL]
- Console logs: [PASS/FAIL]
- Lambda logs: [PASS/FAIL]

### Issues Found
1. [Issue description]
2. [Issue description]

### Screenshots
[Attach screenshots]

### Logs
[Attach logs]

### Recommendation
[PASS/FAIL with explanation]
```

---

## Next Steps After Testing

1. **If All Tests Pass**:
   - Mark task as complete
   - Update test execution report
   - Close related issues
   - Document lessons learned

2. **If Tests Fail**:
   - Document failures in detail
   - Create follow-up tasks
   - Investigate root causes
   - Plan fixes

3. **If Edge Cases Found**:
   - Document edge cases
   - Create enhancement tasks
   - Update requirements
   - Plan future improvements
