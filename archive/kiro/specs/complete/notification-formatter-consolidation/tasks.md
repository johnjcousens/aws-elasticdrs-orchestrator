# Implementation Plan: Notification Formatter Consolidation

## Overview

Consolidate HTML email formatting functions from the standalone `notification-formatter` Lambda into `lambda/shared/notifications.py`, wire `publish_recovery_plan_notification` to produce HTML before publishing to SNS, archive the old Lambda code, and remove it from CloudFormation and the deploy pipeline.

## Tasks

- [x] 1. Move formatter functions into shared notifications module
  - [x] 1.1 Add the HTML formatting functions to `lambda/shared/notifications.py`. Copy these functions from `lambda/notification-formatter/index.py` into `lambda/shared/notifications.py`: `_get_base_email_styles`, `_build_info_box`, `_build_console_link`, `_wrap_html_email`, `format_start_notification`, `format_complete_notification`, `format_failure_notification`, `format_pause_notification`, `format_notification_message`. Add module-level variables `PROJECT_NAME`, `ENVIRONMENT`, and `AWS_REGION` from env vars if not already present. Preserve all docstrings, type hints, and return types exactly. _Requirements: 1.1, 1.2, 1.3_
  - [x] 1.2 Update `publish_recovery_plan_notification` to format HTML before publishing. Call `format_notification_message(event_type, details)` to get HTML and plain-text messages. Use `MessageStructure="json"` with protocol-specific message body: `{"default": ..., "email": ...}`. Wrap the formatting call in try/except so that if formatting fails, fall back to `json.dumps(details)` as plain message. _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [x] 1.3 Write property test: **Property 1: Formatter output contains required fields** — *For any* valid details dictionary containing `planName` and `executionId`, and *for any* event type in `{"start", "complete", "fail", "pause"}`, `format_notification_message` returns a dict with `"default"` containing the plan name and `"email"` containing `<!DOCTYPE html>`, the plan name, and the execution ID. Use `hypothesis` with `@settings(max_examples=100)`. **Validates: Requirements 1.1**
  - [x] 1.4 Write property test: **Property 2: SNS publish uses structured HTML messages** — *For any* valid event type in `{"start", "complete", "fail", "pause"}` and *for any* valid details dictionary, `publish_recovery_plan_notification` calls SNS publish with `MessageStructure="json"` and a JSON message body containing `"default"` and `"email"` keys. Mock `sns.publish`. Use `hypothesis` with `@settings(max_examples=100)`. **Validates: Requirements 2.1, 2.2**

- [x] 2. Update existing tests to use new import path
  - [x] 2.1 Update `tests/unit/test_notification_formatter_html.py` imports. Replace `import_module("notification-formatter.index")` with direct imports from `lambda.shared.notifications`. Update all function references to import from the new location. All existing test assertions remain unchanged. _Requirements: 5.1, 5.2_
  - [x] 2.2 Write unit tests for updated `publish_recovery_plan_notification`. Test that SNS publish is called with `MessageStructure="json"` for valid event types. Test formatter exception fallback publishes raw JSON without `MessageStructure`. Test unrecognized event type produces plain-text fallback message. Mock SNS client for all tests. _Requirements: 2.1, 2.2, 2.3, 2.4, 5.3_

- [x] 3. Checkpoint: All tests pass
  - [x] 3.1 Run all backend unit and property tests (`tests/unit/`). Ensure all tests pass. Ask the user if questions arise.

- [x] 4. Archive old Lambda and remove from infrastructure
  - [x] 4.1 Archive `lambda/notification-formatter/` to `archive/code/notification-formatter/`. Copy the entire `lambda/notification-formatter/` directory to `archive/code/notification-formatter/`. Remove the original `lambda/notification-formatter/` directory. _Requirements: 3.1, 3.2_
  - [x] 4.2 Remove `NotificationFormatterFunction` from `cfn/lambda-stack.yaml`. Remove the `NotificationFormatterFunction` resource definition. Remove the `NotificationFormatterFunctionArn` and `NotificationFormatterFunctionName` outputs and exports. _Requirements: 4.1_
  - [x] 4.3 Remove `NotificationFormatterRole` from `cfn/notification-stack.yaml`. Remove the `NotificationFormatterRole` resource definition. Remove the `NotificationFormatterRoleArn` output and export. _Requirements: 4.2_
  - [x] 4.4 Remove `notification-formatter` from deploy pipeline. Remove `"notification-formatter"` from both `LAMBDA_FUNCTIONS` arrays in `scripts/deploy.sh` (lambda-only and full deploy sections). Remove `("notification-formatter", False)` from the `lambdas` list in `package_lambda.py`. _Requirements: 4.3, 4.4_

- [ ] 5. Final validation and deployment
  - [x] 5.1 Run all backend and frontend tests. Run `cfn-lint` on all CloudFormation templates. Ensure everything passes. Ask the user if questions arise.
  - [ ] 5.2 Commit all changes with a descriptive conventional commit message. Push to remote.
  - [ ] 5.3 Deploy using `./scripts/deploy.sh test`. Verify deployment succeeds.
  - [ ] 5.4 Run a live drill test to verify HTML-formatted email notifications are received.

## Notes

- The formatter functions are pure Python with no external dependencies — the move is a straight copy
- The Lambda handler functions (`lambda_handler`, `handle_execution_notification`, etc.) and plain-text formatters (`format_execution_message`, etc.) are NOT moved — they were Lambda-specific entry points
- Deploy via `./scripts/deploy.sh test` after all changes are complete
- All backend code follows PEP 8 standards (79 char lines, 4 spaces, double quotes, type hints)
do a v