# Bug 12 Fix - Remove Invalid recoverySnapshotID Parameter

## [Overview]
Remove invalid `recoverySnapshotID` parameter from DRS API call that's causing all recovery operations to fail with ParamValidationError.

This fix addresses Bug 12 where the `start_drs_recovery_for_wave()` function in `lambda/index.py` incorrectly adds a `recoverySnapshotID` parameter to each sourceServer in the array. According to AWS DRS API documentation, `start_recovery()` only accepts `sourceServerID` at the server level - DRS automatically uses the latest recovery snapshot without requiring explicit specification. The current implementation (lines 1083-1117) fetches snapshots and adds them to the API call, which violates the API contract and causes immediate validation failure. This bug was introduced in Bug 8's enhancement attempt and has broken all DRS job creation (both drill and recovery operations). The fix removes the entire snapshot fetching logic and simplifies the sourceServers array to contain only the required `sourceServerID` field, restoring DRS functionality while maintaining the valid tags parameter for job tracking.

## [Types]
No type system changes required - this is a pure code removal fix.

The function signature remains unchanged:
```python
def start_drs_recovery_for_wave(
    region: str,
    server_ids: List[str],
    execution_id: str,
    execution_type: str,
    is_drill: bool
) -> Dict[str, Any]
```

Return type structure remains the same:
```python
{
    'JobId': str,        # DRS job ID for wave-level tracking
    'Servers': List[Dict]  # Per-server results with shared job ID
}
```

## [Files]
Remove invalid snapshot fetching logic from Lambda function and ensure deployment across all environments.

**Modified Files:**
- `lambda/index.py` (lines 1083-1117)
  - Remove entire STEP 2 section (snapshot fetching and recoverySnapshotID logic)
  - Simplify sourceServers array construction
  - Keep STEP 1 (launch configs) and STEP 3 (tags) unchanged
  - Preserve all error handling and logging patterns

**Deployment Files (no changes, used for deployment):**
- `lambda/deploy_lambda.py` - Deployment script for Lambda updates
- `scripts/sync-to-deployment-bucket.sh` - S3 repository sync
- `cfn/lambda-stack.yaml` - CloudFormation Lambda configuration

**Documentation Files (updated):**
- `docs/BUG_12_RESOLUTION.md` - Bug fix documentation
- `docs/PROJECT_STATUS.md` - Session tracking

## [Functions]
Simplify `start_drs_recovery_for_wave()` by removing invalid API parameter construction.

**Modified Function:**
- Function: `start_drs_recovery_for_wave()`
- File: `lambda/index.py`
- Lines: 1070-1200 (approximate range)
- Changes:
  1. **Remove lines 1083-1117** - Entire STEP 2 (snapshot fetching logic)
  2. **Replace with simplified array construction**:
     ```python
     # STEP 2: Build sourceServers array (simplified - no snapshot IDs needed)
     source_servers = [{'sourceServerID': sid} for sid in server_ids]
     print(f"[DRS API] Built sourceServers array for {len(server_ids)} servers")
     ```
  3. **Keep STEP 1 unchanged** - Launch configuration fetching (lines 1079-1080)
  4. **Keep STEP 3 unchanged** - Tags construction (lines 1118-1125)
  5. **Keep STEP 4 unchanged** - API call and response handling (lines 1126-1200)

**Unmodified Functions:**
- `get_server_launch_configurations()` (lines 970-1030) - Still fetches configs, but they're not used yet (future enhancement)
- All other functions in `lambda/index.py` remain unchanged

## [Classes]
No class modifications required - this fix operates at the function level only.

## [Dependencies]
No dependency changes required.

Current dependencies remain:
- `boto3` - AWS SDK for Python (DRS, DynamoDB, S3 clients)
- `python3.12` - Lambda runtime
- All existing Lambda IAM permissions in `cfn/lambda-stack.yaml` (DRS, DynamoDB, EC2 access)

## [Testing]
Verify fix through direct execution test and deployment validation.

**Test Strategy:**
1. **Syntax Validation**
   - Python syntax check: `python3 -m py_compile lambda/index.py`
   - Ensure no import errors or syntax issues

2. **Deployment Verification**
   - Deploy Lambda via `deploy_lambda.py --direct`
   - Confirm function update succeeds
   - Check CloudWatch logs for deployment confirmation

3. **Functional Testing**
   - Trigger test recovery execution via UI
   - Monitor CloudWatch logs for DRS API call
   - Verify:
     - No ParamValidationError
     - JobId returned (not null)
     - DynamoDB status: Wave = LAUNCHING, Server = LAUNCHING
     - Job appears in DRS console

4. **S3 Sync Validation**
   - Run `scripts/sync-to-deployment-bucket.sh`
   - Verify `s3://aws-drs-orchestration/lambda/index.py` updated
   - Confirm metadata tags (git-commit, sync-time)

**Expected Results:**
- ✅ DRS job creation succeeds
- ✅ JobId != null in DynamoDB
- ✅ Wave status = LAUNCHING → IN_PROGRESS → COMPLETED
- ✅ No API parameter validation errors
- ✅ Lambda code synced to S3 for CloudFormation deployments

**Test Files:**
- Use existing UI at https://drs-orchestration-test.example.com
- Monitor via AWS Console → DRS → Recovery instances
- Check CloudWatch Logs: `/aws/lambda/drs-orchestration-api-handler-test`

## [Implementation Order]
Execute changes in specific sequence to minimize risk and enable rapid rollback if needed.

**Step 1: Code Modification (5 minutes)**
1. Open `lambda/index.py` in editor
2. Locate lines 1083-1117 (STEP 2: Build sourceServers array WITH recovery snapshots)
3. Delete entire section (35 lines)
4. Replace with simplified 2-line implementation:
   ```python
   # STEP 2: Build sourceServers array (simplified - DRS uses latest snapshot automatically)
   source_servers = [{'sourceServerID': sid} for sid in server_ids]
   print(f"[DRS API] Built sourceServers array for {len(server_ids)} servers")
   ```
5. Verify STEP 3 (tags) and STEP 4 (API call) remain unchanged
6. Save file

**Step 2: Syntax Validation (2 minutes)**
1. Run: `cd /path/to/project && python3 -m py_compile lambda/index.py`
2. Verify no syntax errors
3. Check for proper indentation (Python requirement)

**Step 3: Local Lambda Deployment (5 minutes)**
1. Navigate to lambda directory
2. Run: `python3 deploy_lambda.py --direct --function-name drs-orchestration-api-handler-test --region us-east-1`
3. Wait for "✅ DEPLOYMENT SUCCESSFUL" message
4. Note deployment timestamp and version

**Step 4: Functional Testing (10 minutes)**
1. Open DRS Orchestration UI
2. Navigate to Recovery Plans
3. Select test plan with 1-2 servers
4. Click "Start Recovery (Drill)"
5. Monitor execution page for JobId appearance
6. Check DRS console for active job
7. Verify no errors in CloudWatch Logs

**Step 5: S3 Repository Sync (3 minutes)**
1. Run: `./scripts/sync-to-deployment-bucket.sh --region us-east-1`
2. Verify sync completes successfully
3. Check S3 bucket: `aws s3 ls s3://aws-drs-orchestration/lambda/ --region us-east-1`
4. Confirm `index.py` has recent timestamp
5. Verify metadata: `aws s3api head-object --bucket aws-drs-orchestration --key lambda/index.py --region us-east-1`

**Step 6: CloudFormation Readiness Check (2 minutes)**
1. Verify `cfn/lambda-stack.yaml` unchanged (no modification needed)
2. Confirm S3 paths in CloudFormation template still valid:
   - `S3Key: 'lambda/api-handler.zip'` (correct)
3. Document that next CFN stack update will use synced code

**Step 7: Documentation Updates (5 minutes)**
1. Update `docs/BUG_12_RESOLUTION.md` with:
   - Deployment timestamp
   - Test results summary
   - Commit hash
2. Update `docs/PROJECT_STATUS.md` Session 57 entry:
   - Mark Bug 12 as "RESOLVED"
   - Add deployment details
3. Commit changes: `git add . && git commit -m "fix: remove invalid recoverySnapshotID parameter (Bug 12)"`

**Step 8: Git Commit and Documentation (3 minutes)**
1. Stage all changes: `git add lambda/index.py docs/`
2. Commit: `git commit -m "fix(drs): remove invalid recoverySnapshotID parameter - Bug 12 resolution"`
3. Push: `git push origin main`
4. Verify remote repository updated

**Total Estimated Time: 35 minutes**

**Rollback Plan (if needed):**
1. `git revert HEAD` (reverts commit)
2. Redeploy previous version: `python3 deploy_lambda.py --direct`
3. Investigate errors and retry with corrections

**Success Criteria:**
- ✅ Code deployed successfully to Lambda
- ✅ Test execution creates DRS job (JobId != null)
- ✅ No ParamValidationError in logs
- ✅ Code synced to S3 repository
- ✅ CloudFormation deployment-ready
- ✅ Documentation updated
- ✅ Git commit pushed to remote
