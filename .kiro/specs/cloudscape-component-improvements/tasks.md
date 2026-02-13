# Implementation Plan: CloudScape Component Improvements

## Overview

This implementation plan adopts additional CloudScape Design System components to improve UI consistency and reduce custom code. The approach prioritizes Dashboard changes first (display-only, no functional impact) before moving to more complex component migrations.

## Tasks

- [ ] 1. Phase 1: Dashboard Improvements (Lowest Risk)
  - [ ] 1.1 Replace Dashboard execution metrics with KeyValuePairs
    - Update `frontend/src/pages/Dashboard.tsx`
    - Replace `Box variant="awsui-key-label"` with `KeyValuePairs` component
    - Configure 4-column layout for Active Executions, Completed, Failed, Success Rate
    - _Requirements: 4.1, 4.2_
  
  - [ ] 1.2 Replace CapacityDashboard metrics with KeyValuePairs
    - Update `frontend/src/components/CapacityDashboard.tsx`
    - Replace `ColumnLayout` with `Box variant="awsui-key-label"` pattern with `KeyValuePairs`
    - Apply to Combined Replication Capacity section (Total Replicating, Percentage Used, Available Slots, Status)
    - Apply to Recovery Capacity section
    - _Requirements: 4.1, 4.2, 4.5_
  
  - [ ] 1.3 Write unit tests for KeyValuePairs integration
    - Test that metrics render correctly with KeyValuePairs
    - Test missing value handling (placeholder dash)
    - _Requirements: 4.5_
  
  - [ ] 1.4 Add Popover for capacity warning details
    - Update `frontend/src/components/CapacityDashboard.tsx`
    - Wrap StatusIndicator with Popover for capacity warnings
    - Display detailed capacity information on hover
    - _Requirements: 8.1, 8.3_

- [ ] 2. Checkpoint - Phase 1 Complete
  - Ensure all tests pass, ask the user if questions arise.
  - Verify Dashboard displays correctly with new components
  - Test in both light and dark themes

- [ ] 3. Phase 2: Display Components (Low Risk)
  - [ ] 3.1 Replace ExecutionDetails metadata with KeyValuePairs
    - Update `frontend/src/components/ExecutionDetails.tsx`
    - Replace `ColumnLayout` with manual styling with `KeyValuePairs`
    - Display Started, Ended, Duration, Execution ID as key-value pairs
    - _Requirements: 5.1, 5.2, 5.4_
  
  - [ ] 3.2 Write unit tests for ExecutionDetails KeyValuePairs
    - Test timestamp formatting consistency
    - Test layout variants (inline vs stacked)
    - _Requirements: 5.4_
  
  - [ ] 3.3 Add TokenGroup for selected servers in ServerSelector
    - Update `frontend/src/components/ServerSelector.tsx`
    - Add TokenGroup to display selected servers as dismissible tokens
    - Implement dismiss handler to remove servers from selection
    - Display hostname or ID as token label
    - _Requirements: 6.1, 6.2, 6.3, 6.5_
  
  - [ ] 3.4 Write property test for TokenGroup server selection
    - **Property 6: TokenGroup Display and Dismissal**
    - **Validates: Requirements 6.1, 6.2, 6.3**
  
  - [ ] 3.5 Add TokenGroup for selected protection groups in WaveConfigEditor
    - Update `frontend/src/components/WaveConfigEditor.tsx`
    - Add TokenGroup to display selected PGs as dismissible tokens
    - Implement dismiss handler to remove PGs from wave
    - Display PG name as label, server count as description
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [ ] 3.6 Write property test for TokenGroup PG selection
    - **Property 6: TokenGroup Display and Dismissal**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [ ] 4. Checkpoint - Phase 2 Complete
  - Ensure all tests pass, ask the user if questions arise.
  - Verify TokenGroup displays and dismisses correctly
  - Test keyboard navigation for TokenGroup

- [ ] 5. Phase 3: Form Enhancements (Medium Risk)
  - [ ] 5.1 Replace tag editor with AttributeEditor in ProtectionGroupDialog
    - Update `frontend/src/components/ProtectionGroupDialog.tsx`
    - Replace custom ColumnLayout tag editor with AttributeEditor
    - Configure definition array for Key and Value columns
    - Implement add/remove handlers
    - Add duplicate key validation
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  
  - [ ] 5.2 Write property test for AttributeEditor operations
    - **Property 3: AttributeEditor Item Operations**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
  
  - [ ] 5.3 Write property test for AttributeEditor duplicate validation
    - **Property 4: AttributeEditor Duplicate Key Validation**
    - **Validates: Requirements 3.6**

- [ ] 6. Checkpoint - Phase 3 Complete
  - Ensure all tests pass, ask the user if questions arise.
  - Verify tag editing works correctly
  - Test form validation with AttributeEditor

- [ ] 7. Phase 4: Workflow Improvements (Higher Risk)
  - [ ] 7.1 Extract step components from ProtectionGroupDialog
    - Create `frontend/src/components/wizard-steps/ServerSelectionStep.tsx`
    - Create `frontend/src/components/wizard-steps/LaunchSettingsStep.tsx`
    - Create `frontend/src/components/wizard-steps/ServerConfigurationsStep.tsx`
    - Move existing tab content to step components
    - _Requirements: 1.1_
  
  - [ ] 7.2 Implement Wizard in ProtectionGroupDialog
    - Update `frontend/src/components/ProtectionGroupDialog.tsx`
    - Replace Modal with nested Tabs with Wizard component
    - Configure 3 steps with extracted step components
    - Implement navigation handlers with validation
    - Configure i18nStrings for button labels
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_
  
  - [ ] 7.3 Write property test for Wizard navigation
    - **Property 1: Wizard Navigation Consistency**
    - **Validates: Requirements 1.2, 1.3**
  
  - [ ] 7.4 Write property test for Wizard validation blocking
    - **Property 2: Wizard Validation Blocking**
    - **Validates: Requirements 1.5**
  
  - [ ] 7.5 Extract step components from RecoveryPlanDialog
    - Create `frontend/src/components/wizard-steps/BasicInformationStep.tsx`
    - Create `frontend/src/components/wizard-steps/WaveConfigurationStep.tsx`
    - Move existing container content to step components
    - _Requirements: 2.1_
  
  - [ ] 7.6 Implement Wizard in RecoveryPlanDialog
    - Update `frontend/src/components/RecoveryPlanDialog.tsx`
    - Replace Modal with Container sections with Wizard component
    - Configure 2 steps with extracted step components
    - Implement navigation handlers with validation
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [ ] 7.7 Write unit tests for RecoveryPlan Wizard
    - Test step rendering
    - Test navigation between steps
    - Test validation on submit
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 8. Checkpoint - Phase 4 Complete
  - Ensure all tests pass, ask the user if questions arise.
  - Verify Protection Group creation/edit workflow
  - Verify Recovery Plan creation/edit workflow
  - Test keyboard navigation through wizard steps

- [ ] 9. Phase 5: Advanced Features (Optional)
  - [ ] 9.1 Add Cards gallery view toggle to ProtectionGroupsPage
    - Update `frontend/src/pages/ProtectionGroupsPage.tsx`
    - Add view toggle button (Table/Cards)
    - Implement Cards component with cardDefinition
    - Configure responsive cardsPerRow
    - _Requirements: 10.1, 10.2, 10.3, 10.5_
  
  - [ ] 9.2 Write property test for Cards content rendering
    - **Property 7: Cards Content Rendering**
    - **Validates: Requirements 10.2, 10.3**
  
  - [ ] 9.3 Create JsonConfigEditor component with CodeEditor
    - Create `frontend/src/components/JsonConfigEditor.tsx`
    - Implement CodeEditor with ace integration
    - Add JSON validation
    - Configure theme support
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [ ] 9.4 Write property test for CodeEditor JSON validation
    - **Property 8: CodeEditor JSON Validation**
    - **Validates: Requirements 11.4**

- [ ] 10. Final Checkpoint
  - Ensure all tests pass, ask the user if questions arise.
  - Run visual regression tests
  - Run accessibility audit
  - Verify all components work in light and dark themes

## Notes

- All tasks are required for comprehensive coverage
- Each phase can be deployed independently
- Phase 1 (Dashboard) has zero functional impact - safe to deploy first
- Phase 4 (Wizard) is the highest risk - consider feature flag for gradual rollout
- Property tests validate universal correctness properties (100 iterations minimum)
- Unit tests validate specific examples and edge cases
