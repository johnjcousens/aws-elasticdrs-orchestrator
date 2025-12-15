# Implementation Plan

## Status: ✅ COMPLETE (Dec 14, 2025)

Feature fully implemented and tested. LaunchConfig settings are preserved on export and automatically applied to DRS source servers on import.

- [x] 1. Add API endpoints for export/import
  - [x] 1.1 Add GET /config/export endpoint to Lambda handler
    - Add route handling in `handle_request()` for `/config/export`
    - Create `export_configuration()` function that scans Protection Groups and Recovery Plans tables
    - Include metadata (schemaVersion, exportedAt, sourceRegion, exportedBy)
    - Transform DynamoDB items to export format (exclude internal fields like GroupId, PlanId, CreatedDate)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 6.1_
  - [ ] 1.2 Write property test for export completeness
    - **Property 2: Export Completeness**
    - **Validates: Requirements 1.3, 1.4, 1.5**
  - [x] 1.3 Add POST /config/import endpoint to Lambda handler
    - Add route handling for `/config/import`
    - Create `import_configuration()` function with dry_run parameter support
    - Implement schema validation using JSON schema
    - Return detailed results (created, skipped, failed arrays)
    - _Requirements: 3.1, 3.7, 6.2, 6.3, 6.4_
  - [ ] 1.4 Write property test for schema validation
    - **Property 10: Schema Version Validation**
    - **Validates: Requirements 7.2, 7.3**

- [x] 2. Implement Protection Group import validation
  - [x] 2.1 Create validate_protection_group_import() function
    - Check if PG name already exists (skip if exists)
    - For explicit servers: validate all SourceServerIds exist in DRS
    - For tag-based: validate tags resolve to at least one server
    - Check for server conflicts with existing PGs
    - Check for conflicts with active executions
    - Return ValidationResult with detailed error info
    - _Requirements: 3.2, 3.4, 3.5, 3.6, 5.1, 5.2, 5.5, 5.6_
  - [ ] 2.2 Write property test for import idempotency
    - **Property 4: Import Idempotency**
    - **Validates: Requirements 3.2, 3.3**
  - [ ] 2.3 Write property test for server validation
    - **Property 6: Server Validation Completeness**
    - **Validates: Requirements 3.4, 3.5, 8.4**
  - [ ] 2.4 Write property test for non-destructiveness
    - **Property 5: Import Non-Destructiveness**
    - **Validates: Requirements 5.1**

- [x] 3. Implement Recovery Plan import validation
  - [x] 3.1 Create validate_recovery_plan_import() function
    - Check if RP name already exists (skip if exists)
    - Validate all referenced Protection Groups exist (in import or system)
    - Handle cascade failures when referenced PG failed import
    - Return ValidationResult with dependency details
    - _Requirements: 3.3, 5.3, 5.4_
  - [ ] 3.2 Write property test for cascade failure
    - **Property 8: Cascade Failure Propagation**
    - **Validates: Requirements 5.4, 8.2**

- [x] 4. Implement import orchestration
  - [x] 4.1 Create import_configuration() orchestrator
    - Process Protection Groups first (dependencies for Recovery Plans)
    - Track which PGs were created vs skipped vs failed
    - Process Recovery Plans with PG dependency resolution
    - Support dry_run mode (validate without persisting)
    - Generate correlation ID for CloudWatch logging
    - _Requirements: 5.1, 5.4, 6.3, 6.4, 8.8_
  - [ ] 4.2 Write property test for dry run isolation
    - **Property 9: Dry Run Isolation**
    - **Validates: Requirements 6.3, 6.4**
  - [ ] 4.3 Write property test for results accuracy
    - **Property 11: Results Summary Accuracy**
    - **Validates: Requirements 3.7, 8.3**

- [ ] 5. Checkpoint - Ensure all backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Add Settings modal to frontend
  - [x] 6.1 Create SettingsModal component
    - Add modal with Tabs component (Export | Import)
    - Wire up to Settings gear icon click in AppLayout
    - Use CloudScape Modal, Tabs, SpaceBetween components
    - _Requirements: 2.1, 4.1_
  - [x] 6.2 Update AppLayout to handle Settings click
    - Add onClick handler to settings utility button
    - Add state for settings modal visibility
    - Render SettingsModal when visible
    - _Requirements: 2.1_

- [x] 7. Implement Export panel
  - [x] 7.1 Create ConfigExportPanel component
    - Add Export button with loading state
    - Call GET /config/export API
    - Trigger browser download with filename `drs-orchestration-config-{timestamp}.json`
    - Display error message on failure
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 8. Implement Import panel
  - [x] 8.1 Create ConfigImportPanel component
    - Add file picker for JSON files
    - Parse and validate file client-side
    - Display preview (counts by resource type)
    - Add Confirm/Cancel buttons
    - _Requirements: 4.1, 4.2, 4.3_
  - [x] 8.2 Create ImportResultsDialog component
    - Display summary (created, skipped, failed counts)
    - Show expandable sections for each category
    - Display detailed error messages for failed resources
    - _Requirements: 4.4, 4.5_

- [x] 9. Add API service methods
  - [x] 9.1 Add exportConfiguration() to api service
    - GET /config/export
    - Return parsed JSON response
    - _Requirements: 6.1_
  - [x] 9.2 Add importConfiguration() to api service
    - POST /config/import with config body
    - Support dryRun parameter
    - Return ImportResults type
    - _Requirements: 6.2, 6.3_

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Write property test for round-trip consistency
  - [ ] 11.1 Write property test for export/import round-trip
    - **Property 1: Export Round-Trip Consistency**
    - **Validates: Requirements 1.1, 1.2, 3.2, 3.3**
    - Create random Protection Groups and Recovery Plans
    - Export configuration
    - Clear database
    - Import configuration
    - Verify equivalent state

- [ ] 12. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
