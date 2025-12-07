# CRITICAL DEBUGGING RULES

## ⛔ NEVER BLAME DRS CONFIGURATION

**ABSOLUTE RULE**: When DRS drills fail through Lambda/Step Functions, the problem is ALWAYS in our code or IAM permissions - NEVER in DRS configuration.

### Proven Facts
- DRS source servers work perfectly via AWS CLI
- Drills execute successfully when run directly: `aws drs start-recovery --source-servers sourceServerID=s-xxx --is-drill`
- If servers are marked "Ready for Recovery" in DRS console, they WILL launch correctly
- The CLI uses the same DRS APIs as our Lambda code

### What to NEVER Investigate
1. ❌ DRS launch templates
2. ❌ DRS launch settings  
3. ❌ DRS replication settings
4. ❌ DRS service-linked roles (can view but NEVER change)
5. ❌ Source server configuration
6. ❌ Replication state or lag
7. ❌ Conversion server issues

### What to ALWAYS Investigate First
1. ✅ Lambda IAM role permissions (OrchestrationRole)
2. ✅ Cross-account STS assume role configuration
3. ✅ Lambda code differences vs working CLI commands
4. ✅ Step Functions state machine logic
5. ✅ CloudTrail for the EXACT API calls and errors
6. ✅ IAM policy conditions that might block specific resources
7. ✅ Resource-based policies on EC2/EBS resources

### The Logic
If one server succeeds and another fails with the same:
- Same Lambda function
- Same IAM role
- Same DRS job
- Same time window

Then the issue is NOT permissions in general - it's something SPECIFIC about:
- Resource-level IAM conditions
- Cross-account trust policies
- Resource tags affecting IAM evaluation
- Timing/race conditions in our code

### Cross-Account Considerations
The IAM role has STSAccess policy for cross-account operations. Check:
1. Is the role trying to assume a cross-account role unnecessarily?
2. Are there conditions on the EC2 permissions that vary by resource?
3. Is there a resource policy on the target resources?

### Remember
**"It's never a DRS config issue. It's always our code."**
