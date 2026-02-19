# Implementation Plan: Account Context Improvements and Notification System Activation

## Overview

This plan implements three critical features: Account Context Management (direct `accountId` on Protection Groups and Recovery Plans), Notification System Activation (SNS integration for execution events), and Interactive Pause/Resume (Step Functions task token callback pattern). Implementation follows a phased approach: infrastructure/IAM first, then backend shared utilities, Lambda handlers, Step Functions integration, frontend updates, data backfill, and finally end-to-end wiring.

## Tasks

- [x] 1. CloudFormation infrastructure updates
  - [x] 1.1 Update IAM permissions for SNS subscription management in `cfn/master-template.yaml`. Add `sns:Subscribe`, `sns:Unsubscribe`, `sns:ListSubscriptionsByTopic`, `sns:GetSubscriptionAttributes`, `sns:SetSubscriptionAttributes`, `sns:GetTopicAttributes`, `sns:ListTopics` to `UnifiedOrchestrationRole` SNS policy. Add `states:SendTaskSuccess`, `states:SendTaskFailure`, `states:SendTaskHeartbeat` permissions for task token callbacks. Scope all SNS permissions to `${ProjectName}-*` resources. _Requirements: 5.2, 5.12, 6.6, 6.7, 6.15_
  - [x] 1.2 Add environment variables to existing Lambda functions in `cfn/master-template.yaml`. Add `EXECUTION_NOTIFICATIONS_TOPIC_ARN` from NotificationStack outputs to execution-handler, data-management-handler, and dr-orchestration-stepfunction Lambdas. Add `API_GATEWAY_URL` environment variable for callback URL construction. _Requirements: 5.8, 5.9, 6.4_
  - [x] 1.3 Verify notification stack outputs in `cfn/notification-stack.yaml`. Ensure `ExecutionNotificationsTopicArn` and `DRSOperationalAlertsTopicArn` are exported. Add exports if missing. _Requirements: 5.8_
  - [x] 1.4 Add execution callback API Gateway endpoint in `cfn/api-gateway-deployment-stack.yaml`. Create `/execution-callback` resource with GET method. Set `AuthorizationType: NONE` (task token is the credential). Add `action` and `taskToken` query string parameters. Integrate with existing execution-handler Lambda via AWS_PROXY. Add method responses for 200, 400, 500 with `text/html` content type. _Requirements: 6.4, 6.13_

- [x] 2. Checkpoint: Validate CloudFormation templates
  - [x] 2.1 Run `cfn-lint` on all modified templates (`cfn/master-template.yaml`, `cfn/notification-stack.yaml`, `cfn/api-gateway-deployment-stack.yaml`). Ensure all templates pass validation. Ask the user if questions arise.

- [x] 3. Backend shared utilities: Account context
  - [x] 3.1 Add invocation source detection to `lambda/shared/account_utils.py`. Implement `detect_invocation_source(event)` returning `"api_gateway"` or `"direct"` based on `requestContext` presence. Implement `get_invocation_metadata(event)` for logging/audit. Implement `extract_account_from_cognito(event)` to get account ID from Cognito identity. _Requirements: 1.10, 1.11_
  - [x] 3.2 Add account context validation to `lambda/shared/account_utils.py`. Implement `validate_account_context_for_invocation(event, body)` that enforces `accountId` required for direct invocation and optional for API Gateway. Reuse existing `validate_account_id()` for 12-digit format validation. Return dict with `accountId`, `assumeRoleName`, `externalId`. Raise `InputValidationError` with clear message when `accountId` missing in direct mode. _Requirements: 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.13_
  - [x] 3.3 Write property tests for account context validation. **Property 2: Account ID Format Validation** — *For any* string, `validate_account_id` returns True if and only if the string is exactly 12 digits. **Property 3: Invocation Source Detection** — *For any* Lambda event, events with `requestContext` are detected as `api_gateway`, events without are detected as `direct`. **Property 4: Direct Invocation Requires Account ID** — *For any* direct Lambda event without `accountId` in body, `validate_account_context_for_invocation` raises `InputValidationError`. **Validates: Requirements 1.6, 1.7, 1.9, 1.10**

- [x] 4. Backend shared utilities: Notification management
  - [x] 4.1 Add SNS subscription management to `lambda/shared/notifications.py`. Implement `manage_recovery_plan_subscription(plan_id, email, action)` supporting create/update/delete. On create: call `sns.subscribe()` with email protocol and `FilterPolicy` scoped to `recoveryPlanId`. On delete: call `sns.unsubscribe()` using stored subscription ARN. On update: delete old subscription then create new one. Implement `get_subscription_arn_for_plan(plan_id)` to retrieve ARN from DynamoDB. Reuse existing `validate_email()` from `security_utils.py`. _Requirements: 5.2, 5.5, 5.7, 5.11, 5.12_
  - [x] 4.2 Add Recovery Plan notification publishing to `lambda/shared/notifications.py`. Implement `publish_recovery_plan_notification(plan_id, event_type, details)` that publishes to SNS with `recoveryPlanId` and `eventType` message attributes. Update existing `send_execution_started()`, `send_execution_completed()`, `send_execution_failed()`, `send_execution_paused()` to include message attributes for filter policy matching. Handle SNS publish failures gracefully (log but don't block execution). _Requirements: 5.3, 5.4, 5.8, 5.9, 5.11_
  - [x] 4.3 Write property tests for notification utilities. **Property 5: Email Format Validation** — *For any* string, `validate_email` returns True only if the string contains `@` followed by a domain with at least one `.`. **Property 7: Notification Delivery for All Event Types** — *For any* event type in `["start", "complete", "fail", "pause"]`, `publish_recovery_plan_notification` calls SNS publish with correct `recoveryPlanId` and `eventType` message attributes. **Validates: Requirements 5.3, 5.6**

- [x] 5. Checkpoint: Shared utilities tests pass
  - [x] 5.1 Run all unit and property tests for shared utilities (`tests/unit/test_account_utils*.py`, `tests/unit/test_notifications*.py`). Ensure all tests pass. Ask the user if questions arise.

- [x] 6. Lambda handler updates: Data management
  - [x] 6.1 Update Protection Group creation in `lambda/data-management-handler/index.py`. Use `validate_account_context_for_invocation()` for account validation. Make `accountId` required (currently optional with empty default). Sanitize user inputs with `sanitize_string()`. Return proper error responses for validation failures. _Requirements: 1.1, 1.6, 1.7, 1.12, 1.13_
  - [x] 6.2 Update Recovery Plan creation in `lambda/data-management-handler/index.py`. Add `accountId`, `assumeRoleName`, `notificationEmail`, `snsSubscriptionArn` fields to DynamoDB item. Use `validate_account_context_for_invocation()` for account validation. Validate `notificationEmail` format using `validate_email()` if provided. Validate all waves reference Protection Groups from the same account. Create SNS subscription via `manage_recovery_plan_subscription()` when email provided. Update item with `snsSubscriptionArn` after subscription creation. Handle subscription creation failure gracefully (don't fail plan creation). _Requirements: 1.2, 1.3, 1.4, 1.5, 1.8, 1.9, 2.1, 2.2, 4.1, 4.2, 4.3, 5.1, 5.2, 5.6_
  - [x] 6.3 Update Recovery Plan update handler in `lambda/data-management-handler/index.py`. Handle `notificationEmail` changes: delete old subscription, create new one. Handle email removal: delete subscription, clear `snsSubscriptionArn`. Validate new email format before processing. _Requirements: 5.5, 5.12_
  - [x] 6.4 Update Recovery Plan delete handler in `lambda/data-management-handler/index.py`. Delete SNS subscription before deleting Recovery Plan from DynamoDB. Handle subscription cleanup errors gracefully (continue with deletion). _Requirements: 5.12_
  - [x] 6.5 Write unit tests for data management handler changes. Test Protection Group creation with valid/invalid account context for both invocation modes. Test Recovery Plan creation with notification email and SNS subscription. Test Recovery Plan update with email change (old subscription deleted, new created). Test Recovery Plan deletion with subscription cleanup. Test account consistency validation across waves. _Requirements: 1.1, 1.2, 2.1, 2.2, 4.1, 5.1, 5.2, 5.5, 5.12_
  - [x] 6.6 Write property test for account consistency validation. **Property 1: Account ID Consistency** — *For any* set of Protection Groups with mixed account IDs, creating a Recovery Plan referencing them raises a validation error. **Validates: Requirements 2.2, 4.1, 4.2**

- [x] 7. Lambda handler updates: Execution and orchestration (PARTIALLY REVERTED — 7.1, 7.2 need rework)
  - [x] 7.1 Add notification publishing to `lambda/dr-orchestration-stepfunction/index.py`. **REVERTED** — must be re-applied. Add `publish_recovery_plan_notification()` calls in execution start, complete, and failure paths. **CRITICAL**: Do NOT modify the `begin_wave_plan()` return structure or any existing state machine interaction logic. Only ADD notification calls after existing logic succeeds. Include `"pauseBeforeExecution": false` in the `begin_wave_plan()` return dict to support the Step Functions pause check. _Requirements: 5.3, 5.4, 5.8, 5.9, 5.10_
  - [x] 7.2 Implement pause handler with task token in `lambda/dr-orchestration-stepfunction/index.py`. **REVERTED** — must be re-applied. Add `handle_execution_pause(event, context)` that receives `taskToken` from Step Functions `waitForTaskToken`. **CRITICAL**: This handler is only called when the Step Functions state machine routes to `PauseForApproval`. It must NOT affect the normal (non-pause) execution flow. _Requirements: 6.1, 6.2, 6.3_
  - [x] 7.3 Add callback handler to `lambda/execution-handler/index.py`. Implement `handle_execution_callback(event)` that processes GET requests with `action` and `taskToken` query parameters. Implement `_validate_task_token(task_token)` for format validation. Implement `_resume_via_task_token(task_token)` calling `stepfunctions.send_task_success()`. Implement `_cancel_via_task_token(task_token)` calling `stepfunctions.send_task_failure()`. Implement `_log_callback_action()` for audit trail. Return HTML success/error pages for browser display. Add routing in `lambda_handler` to detect callback requests (unauthenticated path). _Requirements: 6.4, 6.5, 6.6, 6.7, 6.8, 6.10, 6.11, 6.12, 6.14_
  - [x] 7.4 Write unit tests for execution and orchestration handler changes. Test notification publishing on execution start, complete, failure. Test pause handler with valid task token. Test callback handler resume and cancel actions. Test invalid/expired task token rejection. Test HTML response generation for success and error pages. _Requirements: 5.3, 6.5, 6.6, 6.7, 6.10_
  - [x] 7.5 Write property tests for callback handler. **Property 10: Invalid Task Token Rejection** — *For any* string that is not a valid task token format (length < 100), both resume and cancel operations reject it with a ValueError. **Validates: Requirements 6.5, 6.10**

- [x] 8. Checkpoint: All backend tests pass
  - [x] 8.1 Run all backend unit and property tests (`tests/unit/`). Ensure all tests pass. Ask the user if questions arise.

- [x] 9. Notification formatter updates
  - [x] 9.1 Update notification formatter Lambda in `lambda/notification-formatter/index.py`. Add `format_pause_notification(details)` that generates HTML email with Resume/Cancel action buttons. Add `format_start_notification(details)`, `format_complete_notification(details)`, `format_failure_notification(details)` for informational emails. Update `format_notification_message(event_type, details)` to route to appropriate formatter. Include Recovery Plan name, execution ID, timestamp, console link in all email templates. Ensure mobile-friendly HTML layout. _Requirements: 5.4, 5.10, 6.2, 6.3, 6.13_
  - [x] 9.2 Write unit tests for notification formatter. Test each email template contains required fields (plan name, event type, timestamp, execution details). Test pause notification contains resume and cancel action URLs. Test HTML output is well-formed. _Requirements: 5.4, 5.10, 6.2, 6.3_

- [x] 10. Step Functions state machine updates (REVERTED — needs safe rework)
  - [x] 10.1 Update Step Functions state machine in `cfn/step-functions-stack.yaml`. **CRITICAL SAFETY**: The `CheckPauseRequired` Choice state MUST handle the case where `$.pauseBeforeExecution` does not exist in the state output from `InitiateWavePlan`. Use `IsPresent` check before `BooleanEquals` to prevent `Invalid path` crashes. The orchestration Lambda's `begin_wave_plan()` return value must include `"pauseBeforeExecution": false` by default. Add `PauseForApproval` Task state using `arn:aws:states:::lambda:invoke.waitForTaskToken`. Pass `taskToken` via `$$.Task.Token` (double `$$` for context object). Set `TimeoutSeconds: 86400`. Add `HandleTimeout` and `HandleCancellation` Fail states. **Validation**: Run a single-wave drill WITHOUT pause enabled and verify it completes successfully BEFORE testing pause. _Requirements: 6.1, 6.8, 6.9_

- [x] 11. Frontend updates
  - [x] 11.1 Enhance Account Context provider in `frontend/src/contexts/AccountContext.tsx`. Add `getAccountContext()` method returning `{ accountId, assumeRoleName, externalId }`. Expose via context so all components can access current account context. _Requirements: 1.12_
  - [x] 11.2 Update Protection Group creation form. Auto-populate `accountId` from current account context (read-only display). Include `accountId` and `assumeRoleName` in create request payload. Validate 12-digit account ID format on frontend. _Requirements: 1.1, 1.6, 1.12_
  - [x] 11.3 Update Recovery Plan creation form. Auto-populate `accountId` from current account context (read-only display). Add optional `notificationEmail` field with email format validation. Validate all selected Protection Groups belong to the same account as current context. Show warning if Protection Groups from different accounts are selected. Include `accountId`, `assumeRoleName`, `notificationEmail` in create request payload. _Requirements: 1.2, 1.3, 1.4, 1.8, 1.12, 2.2, 4.1, 4.2, 5.1_
  - [x] 11.4 Update Recovery Plan edit form. Allow updating `notificationEmail` field. Show current subscription status (pending confirmation, active, none). _Requirements: 5.5, 5.7_
  - [x] 11.5 Update export/import functionality. Include `accountId` and `assumeRoleName` in exported Protection Groups. Include `accountId`, `assumeRoleName` in exported Recovery Plans. Validate account context on import with clear error messages. Maintain backward compatibility with existing export format. _Requirements: 3.1, 3.2, 3.3, 3.4_
  - [x] 11.6 Write frontend unit tests. Test AccountContext provider `getAccountContext()` method. Test Protection Group form auto-populates account context. Test Recovery Plan form validates Protection Group account consistency. Test notification email validation. Test export includes account context fields. _Requirements: 1.1, 1.2, 1.12, 2.2, 3.1, 3.2, 5.1_

- [x] 12. Checkpoint: Frontend and backend integration
  - [x] 12.1 Run all frontend and backend tests. Ensure all tests pass. Ask the user if questions arise.

- [x] 13. Data backfill scripts
  - [x] 13.1 Create Protection Group backfill script `scripts/backfill-protection-groups.py`. Scan all Protection Groups missing `accountId`. Derive `accountId` from `assumeRoleName` ARN or DRS source server ARNs. Support `--dry-run` (default) and `--apply` modes. Print summary of updated, skipped, and errored items. Handle pagination for large tables. _Requirements: 2.4_
  - [x] 13.2 Create Recovery Plan backfill script `scripts/backfill-recovery-plans.py`. Scan all Recovery Plans missing `accountId`. Derive `accountId` from first Protection Group in plan's waves. Add empty defaults for `assumeRoleName`, `notificationEmail`, `snsSubscriptionArn`. Support `--dry-run` (default) and `--apply` modes. Handle edge cases (no waves, missing Protection Groups, mixed accounts). _Requirements: 2.4_
  - [x] 13.3 Write unit tests for backfill scripts. Test dry run mode produces correct output without modifying DynamoDB. Test apply mode updates items correctly. Test edge cases (missing Protection Groups, empty waves, mixed accounts). _Requirements: 2.4_

- [x] 14. Final checkpoint: Full integration validation
  - [x] 14.1 Run all unit tests, property tests, and cfn-lint validation. Ensure everything passes. Ask the user if questions arise.

- [ ] 15. Regression testing and safe deployment
  - [x] 15.1 Run all existing backend unit tests (`tests/unit/`) to verify no regressions. Fix any test failures caused by missing functions or changed imports. Do NOT modify existing test assertions — only fix imports and mocks that reference reverted code.
  - [x] 15.2 Run all frontend tests (`npx vitest run` in `frontend/`). Fix any TypeScript compilation errors. Verify the frontend builds cleanly with `npm run build`.
  - [x] 15.3 Run `cfn-lint` on all CloudFormation templates. Verify `cfn/step-functions-stack.yaml` passes validation.
  - [x] 15.4 Commit ALL working changes (including completed 7.1, 7.2, and pending 10.1 once done) with a descriptive conventional commit message. Push to remote. This creates a safe rollback point before deploying.
  - [x] 15.5 Deploy using `./scripts/deploy.sh test`. Verify deployment succeeds and all Lambda functions are updated.
  - [x] 15.6 Run a live drill test against the `TargetAcountOnly` plan (plan ID `c5621161-98af-41ed-8e06-652cd3f88152`) to verify execution flow works end-to-end: Step Functions starts, wave initiates, DRS job starts, poller tracks progress, execution completes.

## Notes

- **LESSON LEARNED**: All changes MUST be committed before deploying. The previous implementation deployed uncommitted changes that broke the Step Functions state machine and left executions stuck in PARTIAL status.
- **REVERTED FILES**: `cfn/step-functions-stack.yaml` was reverted to the last committed (working) version. `lambda/dr-orchestration-stepfunction/index.py` has been re-implemented (tasks 7.1, 7.2 complete). Task 10.1 must still be re-implemented with the safety constraints noted above.
- **STILL INTACT**: All changes (account context, notifications, export/import, frontend, deploy script, tests, orchestration handler) are in the working tree.
- **DEPLOYMENT ORDER**: Tests pass → Commit → Deploy → Live drill. Never deploy uncommitted code.
- **REGRESSION TESTING**: Always run full test suite AND a live drill before deploying changes that touch execution-handler, dr-orchestration-stepfunction, or step-functions-stack.yaml.
- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document (Section 7)
- Unit tests validate specific examples and edge cases
- All backend code follows PEP 8 standards (79 char lines, 4 spaces, double quotes, type hints)
- All frontend code uses TypeScript strict mode with CloudScape components
- Deploy using `./scripts/deploy.sh test`  — never use direct AWS CLI deployment commands
- Backfill scripts should be run after backend deployment but before frontend deployment
