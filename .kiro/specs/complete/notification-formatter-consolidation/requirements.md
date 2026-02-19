# Requirements Document

## Introduction

The notification-formatter Lambda (`lambda/notification-formatter/index.py`) contains pure HTML email formatting functions that are never invoked in the current execution flow. As a result, SNS email subscribers receive raw JSON instead of formatted HTML. This feature consolidates the HTML formatting functions into `lambda/shared/notifications.py`, wires `publish_recovery_plan_notification` to produce HTML before publishing to SNS, archives the standalone Lambda, and removes it from the CloudFormation stack and deploy pipeline.

## Glossary

- **Formatter_Functions**: The set of pure Python functions that produce HTML email content: `format_start_notification`, `format_complete_notification`, `format_failure_notification`, `format_pause_notification`, `format_notification_message`, and helpers `_get_base_email_styles`, `_build_info_box`, `_build_console_link`, `_wrap_html_email`.
- **Shared_Notifications_Module**: The file `lambda/shared/notifications.py` containing `publish_recovery_plan_notification` and the `send_execution_*` / `send_execution_paused` convenience functions.
- **Publish_Function**: The `publish_recovery_plan_notification` function in the Shared_Notifications_Module.
- **Notification_Formatter_Lambda**: The standalone AWS Lambda defined in `cfn/lambda-stack.yaml` as `NotificationFormatterFunction`, sourced from `lambda/notification-formatter/`.
- **Deploy_Script**: The `scripts/deploy.sh` shell script that packages, syncs, and deploys Lambda functions.
- **Package_Script**: The `package_lambda.py` script that zips Lambda directories for deployment.
- **Archive_Directory**: The `archive/code/` directory where retired code is preserved.

## Requirements

### Requirement 1: Move Formatter Functions to Shared Module

**User Story:** As a developer, I want the HTML email formatting functions consolidated into the shared notifications module, so that all notification logic lives in one place and the formatter Lambda can be retired.

#### Acceptance Criteria

1. THE Shared_Notifications_Module SHALL contain all Formatter_Functions with identical signatures and behavior as the originals in `lambda/notification-formatter/index.py`.
2. WHEN the Formatter_Functions are moved, THE Shared_Notifications_Module SHALL preserve the original function docstrings, type hints, and return types.
3. WHEN the Formatter_Functions are moved, THE Shared_Notifications_Module SHALL not introduce any new external dependencies beyond the Python standard library.

### Requirement 2: Publish HTML-Formatted Notifications via SNS

**User Story:** As an operations engineer, I want SNS email notifications to arrive as formatted HTML instead of raw JSON, so that I can quickly read and act on DR execution events.

#### Acceptance Criteria

1. WHEN `publish_recovery_plan_notification` is called with a valid `event_type` ("start", "complete", "fail", "pause"), THE Publish_Function SHALL call `format_notification_message` to produce an HTML email body and a plain-text default message.
2. WHEN `publish_recovery_plan_notification` publishes to SNS, THE Publish_Function SHALL use the SNS `MessageStructure` parameter set to `"json"` with protocol-specific messages: an `"email"` key containing the HTML body and a `"default"` key containing the plain-text fallback.
3. WHEN `publish_recovery_plan_notification` is called with an unrecognized `event_type`, THE Publish_Function SHALL fall back to a plain-text message containing the event type and JSON-serialized details.
4. WHEN `format_notification_message` raises an exception, THE Publish_Function SHALL log the error and fall back to publishing the raw JSON details so that notifications are never silently lost.

### Requirement 3: Archive the Standalone Notification Formatter Lambda

**User Story:** As a developer, I want the retired notification-formatter Lambda code archived rather than deleted, so that the code history is preserved for reference.

#### Acceptance Criteria

1. WHEN the consolidation is complete, THE Archive_Directory SHALL contain a copy of the `lambda/notification-formatter/` directory at `archive/code/notification-formatter/`.
2. WHEN the code is archived, THE original `lambda/notification-formatter/` directory SHALL be removed from the active codebase.

### Requirement 4: Remove Notification Formatter Lambda from Infrastructure

**User Story:** As a DevOps engineer, I want the retired Lambda removed from CloudFormation and the deploy pipeline, so that we do not maintain unused infrastructure.

#### Acceptance Criteria

1. WHEN the consolidation is deployed, THE `cfn/lambda-stack.yaml` template SHALL not contain the `NotificationFormatterFunction` resource, its associated outputs (`NotificationFormatterFunctionArn`, `NotificationFormatterFunctionName`), or any references to the notification-formatter S3 key.
2. WHEN the consolidation is deployed, THE `cfn/notification-stack.yaml` template SHALL not contain the `NotificationFormatterRole` resource or its associated output (`NotificationFormatterRoleArn`).
3. WHEN the consolidation is deployed, THE Deploy_Script SHALL not include `"notification-formatter"` in any Lambda function update list.
4. WHEN the consolidation is deployed, THE Package_Script SHALL not include `("notification-formatter", False)` in the lambdas list.

### Requirement 5: Update Tests

**User Story:** As a developer, I want the existing formatter tests to pass against the new module location, so that I have confidence the move did not break formatting behavior.

#### Acceptance Criteria

1. WHEN the Formatter_Functions are moved, THE existing test file `tests/unit/test_notification_formatter_html.py` SHALL import the Formatter_Functions from `lambda.shared.notifications` instead of `notification-formatter.index`.
2. WHEN all tests are run, THE test suite SHALL pass with zero failures related to notification formatting or publishing.
3. WHEN `publish_recovery_plan_notification` is updated, THE test suite SHALL include tests verifying that SNS receives HTML-formatted messages with `MessageStructure` set to `"json"`.
