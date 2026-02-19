# Requirements Document

## Introduction

This document defines the requirements for enhancing the AWS DRS Orchestration UI by adopting additional CloudScape Design System components. The goal is to replace custom component implementations with native CloudScape components to improve consistency, accessibility, maintainability, and alignment with AWS Console design standards. This spec is based on the analysis in `.kiro/specs/cloudscape-component-recommendations.md`.

**Note**: This spec focuses on adopting new CloudScape components. CSS refactoring (design tokens, inline styles, CSS modules) is covered separately in `.kiro/specs/css-refactoring/`.

## Glossary

- **CloudScape**: AWS's open-source design system providing React components and design tokens
- **Wizard**: CloudScape component for multi-step workflows with clear step progression and navigation
- **AttributeEditor**: CloudScape component for editing key-value pairs with add/remove functionality
- **KeyValuePairs**: CloudScape component for displaying read-only key-value information
- **Cards**: CloudScape component for displaying items in a card-based grid layout
- **TokenGroup**: CloudScape component for displaying selected items as dismissible tokens
- **Popover**: CloudScape component for displaying contextual information without modal interruption
- **CodeEditor**: CloudScape component for editing code with syntax highlighting
- **Protection_Group**: A logical grouping of DRS source servers for coordinated recovery
- **Recovery_Plan**: A plan defining waves of servers to recover in sequence
- **Wave**: A group of servers within a recovery plan that are recovered together
- **DRS**: AWS Elastic Disaster Recovery Service

## Requirements

### Requirement 1: Wizard Component for Protection Group Dialog

**User Story:** As a user, I want a clear step-by-step workflow when creating or editing protection groups, so that I can easily navigate between server selection, launch settings, and server configurations.

#### Acceptance Criteria

1. WHEN a user opens the Protection Group dialog, THE Wizard_Component SHALL display three distinct steps: "Server Selection", "Launch Settings", and "Server Configurations"
2. WHEN a user completes a step, THE Wizard_Component SHALL enable navigation to the next step
3. WHEN a user is on any step, THE Wizard_Component SHALL allow navigation back to previous steps
4. WHEN a user is on the final step, THE Wizard_Component SHALL display a "Create Group" or "Update Group" action button
5. WHEN validation errors exist on a step, THE Wizard_Component SHALL prevent navigation to subsequent steps and display error indicators
6. WHEN a user cancels the wizard, THE Wizard_Component SHALL close without saving changes

### Requirement 2: Wizard Component for Recovery Plan Dialog

**User Story:** As a user, I want a guided workflow when creating or editing recovery plans, so that I can configure basic information and wave settings in a logical sequence.

#### Acceptance Criteria

1. WHEN a user opens the Recovery Plan dialog, THE Wizard_Component SHALL display two distinct steps: "Basic Information" and "Wave Configuration"
2. WHEN a user completes the basic information step, THE Wizard_Component SHALL enable navigation to wave configuration
3. WHEN a user is on the wave configuration step, THE Wizard_Component SHALL allow navigation back to basic information
4. WHEN validation errors exist, THE Wizard_Component SHALL display error indicators on the affected step
5. WHEN a user submits the wizard, THE Wizard_Component SHALL validate all steps before saving

### Requirement 3: AttributeEditor for Tag Management

**User Story:** As a user, I want a standardized interface for managing server selection tags, so that I can easily add, edit, and remove tag key-value pairs.

#### Acceptance Criteria

1. WHEN a user views the tag editor in Protection Group dialog, THE AttributeEditor_Component SHALL display existing tags as editable key-value rows
2. WHEN a user clicks "Add tag", THE AttributeEditor_Component SHALL add a new empty key-value row
3. WHEN a user clicks remove on a tag row, THE AttributeEditor_Component SHALL remove that tag from the list
4. WHEN a user edits a tag key or value, THE AttributeEditor_Component SHALL update the tag in real-time
5. WHEN the tag list is empty, THE AttributeEditor_Component SHALL display an empty state with guidance
6. IF a user enters duplicate tag keys, THEN THE AttributeEditor_Component SHALL display a validation error

### Requirement 4: KeyValuePairs for Capacity Metrics Display

**User Story:** As a user, I want capacity metrics displayed in a consistent format, so that I can quickly scan and understand system capacity information.

#### Acceptance Criteria

1. WHEN displaying capacity metrics on the Dashboard, THE KeyValuePairs_Component SHALL render metrics with consistent label and value styling
2. WHEN displaying capacity metrics in CapacityDashboard, THE KeyValuePairs_Component SHALL support multiple columns layout
3. THE KeyValuePairs_Component SHALL display labels using CloudScape design tokens for text-label color
4. THE KeyValuePairs_Component SHALL display values using CloudScape design tokens for text-body-default color
5. WHEN a metric value is unavailable, THE KeyValuePairs_Component SHALL display a placeholder dash

### Requirement 5: KeyValuePairs for Execution Details

**User Story:** As a user, I want execution metadata displayed in a scannable format, so that I can quickly review execution details like start time, duration, and execution ID.

#### Acceptance Criteria

1. WHEN viewing execution details, THE KeyValuePairs_Component SHALL display metadata in a structured key-value format
2. THE KeyValuePairs_Component SHALL support inline layout for compact display
3. THE KeyValuePairs_Component SHALL support stacked layout for detailed views
4. WHEN displaying timestamps, THE KeyValuePairs_Component SHALL format them consistently

### Requirement 6: TokenGroup for Selected Servers Display

**User Story:** As a user, I want to see my selected servers displayed as dismissible tokens, so that I can easily review and modify my selection.

#### Acceptance Criteria

1. WHEN servers are selected in ServerSelector, THE TokenGroup_Component SHALL display each selected server as a token
2. WHEN a user clicks dismiss on a token, THE TokenGroup_Component SHALL remove that server from the selection
3. THE TokenGroup_Component SHALL display server hostname or ID as the token label
4. WHEN many servers are selected, THE TokenGroup_Component SHALL wrap tokens to multiple lines
5. WHEN no servers are selected, THE TokenGroup_Component SHALL display an empty state

### Requirement 7: TokenGroup for Selected Protection Groups

**User Story:** As a user, I want to see selected protection groups displayed as tokens in wave configuration, so that I can easily review and modify my selection.

#### Acceptance Criteria

1. WHEN protection groups are selected in WaveConfigEditor, THE TokenGroup_Component SHALL display each selected group as a token
2. WHEN a user clicks dismiss on a token, THE TokenGroup_Component SHALL remove that protection group from the wave
3. THE TokenGroup_Component SHALL display protection group name as the token label
4. THE TokenGroup_Component SHALL display server count as token description

### Requirement 8: Popover for Contextual Information

**User Story:** As a user, I want contextual help and status details displayed inline without modal interruption, so that I can get information quickly while maintaining my workflow context.

#### Acceptance Criteria

1. WHEN a user hovers over a capacity warning indicator, THE Popover_Component SHALL display detailed capacity information
2. WHEN a user hovers over a server status indicator, THE Popover_Component SHALL display server status details
3. WHEN a user clicks a help icon, THE Popover_Component SHALL display contextual help text
4. THE Popover_Component SHALL position itself automatically to avoid viewport overflow
5. THE Popover_Component SHALL close when the user clicks outside or presses Escape

### Requirement 9: Cards Component for Dashboard Metrics

**User Story:** As a user, I want dashboard metrics displayed as cards, so that I have a consistent visual presentation aligned with AWS Console patterns.

#### Acceptance Criteria

1. WHEN displaying execution metrics on Dashboard, THE Cards_Component SHALL render each metric category as a card
2. THE Cards_Component SHALL support header with metric title
3. THE Cards_Component SHALL support body with metric value and status indicator
4. THE Cards_Component SHALL maintain consistent spacing using CloudScape design tokens

### Requirement 10: Cards Component for Protection Groups Gallery View

**User Story:** As a user, I want an optional card-based gallery view for protection groups, so that I can visually browse and select protection groups.

#### Acceptance Criteria

1. WHEN viewing the Protection Groups page, THE Cards_Component SHALL offer an alternative gallery view
2. THE Cards_Component SHALL display protection group name as card header
3. THE Cards_Component SHALL display server count, region, and status in card sections
4. WHEN a user selects a card, THE Cards_Component SHALL highlight the selected card
5. THE Cards_Component SHALL support responsive grid layout

### Requirement 11: CodeEditor for JSON Configuration

**User Story:** As a user, I want to view and edit JSON configuration with syntax highlighting, so that I can work with launch templates and configuration exports effectively.

#### Acceptance Criteria

1. WHEN viewing launch template JSON, THE CodeEditor_Component SHALL display JSON with syntax highlighting
2. WHEN editing configuration, THE CodeEditor_Component SHALL provide line numbers
3. THE CodeEditor_Component SHALL support copy-to-clipboard functionality
4. IF JSON syntax is invalid, THEN THE CodeEditor_Component SHALL display validation errors
5. THE CodeEditor_Component SHALL support both light and dark themes

### Requirement 12: Maintain Existing Functionality

**User Story:** As a user, I want all existing functionality preserved when CloudScape components are adopted, so that my workflows are not disrupted.

#### Acceptance Criteria

1. WHEN CloudScape components replace custom implementations, THE System SHALL preserve all existing form validation logic
2. WHEN CloudScape components replace custom implementations, THE System SHALL preserve all existing API contracts
3. WHEN CloudScape components replace custom implementations, THE System SHALL preserve all existing keyboard navigation
4. WHEN CloudScape components replace custom implementations, THE System SHALL preserve all existing accessibility features

### Requirement 13: Theme Support

**User Story:** As a user, I want the UI to properly support light and dark themes, so that I can use my preferred visual mode.

#### Acceptance Criteria

1. WHEN CloudScape components are adopted, THE System SHALL automatically support light mode
2. WHEN CloudScape components are adopted, THE System SHALL automatically support dark mode
3. THE System SHALL use CloudScape design tokens for all custom styling to ensure theme compatibility
