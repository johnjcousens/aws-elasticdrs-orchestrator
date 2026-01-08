# CRITICAL FIX: Restore Working Step Functions Pattern

## Problem Identified
The system broke due to **over-engineering** - the Step Functions template became overly complex with additional error handling states that disrupted the core orchestration flow.

## Root Cause Analysis
Comparing current broken system vs working archive (Jan 7, 2026):

### Working Pattern (Archive):
- **Simple Step Functions** with 6 core states
- **Lambda owns ALL state** via `OutputPath: '$.Payload'`
- **Clean state transitions** without complex error handling
- **Proven successful execution**: 04c0b4a4-e3ea-4129-9d2a-282ec9e68744

### Broken Pattern (Current):
- **Complex Step Functions** with 15+ states including error handlers
- **Additional logging configuration** that may cause issues
- **Complex error handling states** that interrupt normal flow
- **Over-engineered resume logic** that adds complexity

## Fix Applied
**Restored the working Step Functions template** from commit `59bed2d` (Jan 7, 2026):

1. **Simplified state machine** - removed complex error handling states
2. **Archive pattern** - Lambda returns complete state via `OutputPath`
3. **Clean transitions** - removed `HandleInitializationError` and similar states
4. **Removed logging configuration** - simplified to core functionality
5. **Standard IAM role** - removed complex logging permissions

## Expected Result
This should restore the **exact working pattern** that successfully executed:
- 3-tier recovery plan (Database → App → Web)
- Wave-based execution with pause/resume
- DRS job polling and status tracking
- Recovery instance creation and monitoring

## Deployment
Following GitHub Actions workflow:
1. Commit this fix
2. Deploy via pipeline (22 minutes estimated)
3. Test with same recovery plan that worked on Jan 7th
4. Monitor execution logs for success

## Verification Steps
1. Create new execution of `3TierRecoveryPlanCreatedInUIBasedOnTags`
2. Verify Step Functions execution starts successfully
3. Monitor wave progression (Database → App → Web)
4. Confirm DRS jobs are created and tracked
5. Validate recovery instances are launched

This fix removes the complexity that was causing failures and restores the proven working architecture.