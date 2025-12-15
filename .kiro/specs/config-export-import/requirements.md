# Requirements Document

## Introduction

This feature enables exporting and importing the complete DRS Orchestration configuration (Protection Groups, Recovery Plans, and Launch Settings) to/from a JSON file. This supports disaster recovery of the orchestration platform itself, environment migration, and configuration backup/restore scenarios.

## Glossary

- **Configuration Export**: The process of serializing all Protection Groups, Recovery Plans, and associated settings to a portable JSON format
- **Configuration Import**: The process of deserializing a JSON configuration file and restoring Protection Groups and Recovery Plans
- **Tag-Based Protection Group**: A Protection Group that selects servers dynamically via EC2 tags rather than explicit server IDs
- **Explicit Server Protection Group**: A Protection Group with hardcoded DRS source server IDs
- **Idempotent Import**: Import operation that skips existing resources without error, only creating missing ones

## Requirements

### Requirement 1

**User Story:** As a DR administrator, I want to export all Protection Groups and Recovery Plans to a JSON file, so that I can back up my orchestration configuration or migrate it to another environment.

#### Acceptance Criteria

1. WHEN a user requests a configuration export via API THEN the System SHALL generate a JSON file containing all Protection Groups with their complete configuration
2. WHEN a user requests a configuration export via API THEN the System SHALL include all Recovery Plans with their wave configurations and Protection Group references
3. WHEN exporting a tag-based Protection Group THEN the System SHALL include the ServerSelectionTags object for dynamic server resolution on import
4. WHEN exporting an explicit-server Protection Group THEN the System SHALL include the SourceServerIds array with all server IDs
5. WHEN exporting Protection Groups THEN the System SHALL include LaunchConfig settings (EC2 template, DRS launch settings)
6. WHEN the export completes THEN the System SHALL include metadata (export timestamp, source region, schema version)

### Requirement 2

**User Story:** As a DR administrator, I want to export configuration from the UI, so that I can easily download a backup without using CLI tools.

#### Acceptance Criteria

1. WHEN a user clicks "Export Configuration" in the UI THEN the System SHALL trigger a browser download of the JSON configuration file
2. WHEN generating the export filename THEN the System SHALL use format `drs-orchestration-config-{timestamp}.json`
3. WHEN the export is in progress THEN the System SHALL display a loading indicator
4. IF the export fails THEN the System SHALL display an error message with the failure reason

### Requirement 3

**User Story:** As a DR administrator, I want to import a configuration file via API, so that I can restore or migrate my orchestration setup programmatically.

#### Acceptance Criteria

1. WHEN a user submits a configuration import request THEN the System SHALL validate the JSON schema before processing
2. WHEN importing Protection Groups THEN the System SHALL skip any Protection Group where a group with the same name already exists
3. WHEN importing Recovery Plans THEN the System SHALL skip any Recovery Plan where a plan with the same name already exists
4. WHEN importing an explicit-server Protection Group THEN the System SHALL validate that all SourceServerIds exist in DRS for the target region
5. WHEN a server ID in an explicit-server Protection Group does not exist in DRS THEN the System SHALL report the missing servers and skip that Protection Group
6. WHEN importing a tag-based Protection Group THEN the System SHALL validate that the tags resolve to at least one server
7. WHEN the import completes THEN the System SHALL return a summary of created, skipped, and failed resources

### Requirement 4

**User Story:** As a DR administrator, I want to import configuration from the UI, so that I can restore my setup without using CLI tools.

#### Acceptance Criteria

1. WHEN a user clicks "Import Configuration" in the UI THEN the System SHALL display a file picker for JSON files
2. WHEN a file is selected THEN the System SHALL display a preview of resources to be imported (counts by type)
3. WHEN the user confirms the import THEN the System SHALL process the file and display progress
4. WHEN the import completes THEN the System SHALL display a summary dialog showing created, skipped, and failed resources
5. IF any resources fail validation THEN the System SHALL display specific error messages for each failure

### Requirement 5

**User Story:** As a DR administrator, I want the import to be completely non-destructive and additive-only, so that I never risk corrupting existing configurations or interfering with running executions.

#### Acceptance Criteria

1. WHEN importing configuration THEN the System SHALL never modify or delete any existing Protection Group or Recovery Plan
2. WHEN importing a Protection Group with servers already assigned to another Protection Group THEN the System SHALL skip that Protection Group and report the conflict with full details
3. WHEN importing a Recovery Plan that references a Protection Group not in the import file AND not existing in the system THEN the System SHALL skip that Recovery Plan and report the missing dependency
4. WHEN a Recovery Plan references a Protection Group that was skipped due to errors THEN the System SHALL also skip that Recovery Plan and report the cascade failure
5. WHEN any active execution exists THEN the System SHALL still allow import but SHALL NOT create any Protection Group or Recovery Plan that would conflict with the active execution's servers
6. WHEN a Protection Group cannot be imported due to server conflicts with an active execution THEN the System SHALL report the conflicting execution ID and status

### Requirement 6

**User Story:** As a DR administrator, I want CLI support for export/import, so that I can automate configuration backup and restore in scripts.

#### Acceptance Criteria

1. WHEN a user calls `GET /config/export` THEN the System SHALL return the complete configuration as JSON response body
2. WHEN a user calls `POST /config/import` with JSON body THEN the System SHALL process the import and return results
3. WHEN calling the import API THEN the System SHALL accept an optional `dryRun` parameter that validates without making changes
4. WHEN `dryRun=true` THEN the System SHALL return what would be created, skipped, or failed without persisting changes

### Requirement 7

**User Story:** As a DR administrator, I want the export format to be versioned, so that future schema changes don't break existing exports.

#### Acceptance Criteria

1. WHEN generating an export THEN the System SHALL include a `schemaVersion` field in the metadata
2. WHEN importing a configuration THEN the System SHALL validate the schemaVersion is compatible
3. IF the schemaVersion is unsupported THEN the System SHALL return an error with supported versions

### Requirement 8

**User Story:** As a developer, I want verbose error handling and logging for import operations, so that I can easily troubleshoot why specific resources failed to import.

#### Acceptance Criteria

1. WHEN any Protection Group fails to import THEN the System SHALL log the Protection Group name, failure reason, and all relevant context (server IDs, tags, conflicts)
2. WHEN any Recovery Plan fails to import THEN the System SHALL log the Plan name, failure reason, and which Protection Group dependencies were missing or failed
3. WHEN the import completes THEN the System SHALL return a detailed results object with separate arrays for: created resources, skipped resources (with skip reason), and failed resources (with error details)
4. WHEN a server validation fails THEN the System SHALL include which specific server IDs were not found in DRS
5. WHEN a tag validation fails THEN the System SHALL include which tags were searched and that zero servers matched
6. WHEN a server conflict occurs THEN the System SHALL include the conflicting Protection Group name and ID
7. WHEN an active execution conflict occurs THEN the System SHALL include the execution ID, plan name, and execution status
8. WHEN logging import operations THEN the System SHALL write to CloudWatch Logs with structured JSON including correlation ID for the entire import operation
