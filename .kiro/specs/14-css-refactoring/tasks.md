# Implementation Plan: CSS Refactoring

## Overview

This implementation plan breaks down the CSS refactoring feature into discrete, incremental tasks. Each task builds on previous steps and includes validation through testing. The plan follows a phased approach: Foundation → Pages → Shared Components → Specialized Components → Validation & Cleanup.

## Tasks

- [ ] 1. Create Z-Index Scale
  - [ ] 1.1 Create `frontend/src/styles/z-index.css` file
  - [ ] 1.2 Define z-index custom properties (base: 0, dropdown: 1000, modal-overlay: 1999, modal: 2000, tooltip: 3000, notification: 4000)
  - [ ] 1.3 Add documentation comments explaining each layer
  - [ ] 1.4 Import z-index.css in main.tsx
  - [ ] 1.5 Test that z-index file is loaded correctly

- [ ] 2. Create Utilities CSS
  - [ ] 2.1 Create `frontend/src/styles/utilities.css` file
  - [ ] 2.2 Add flexbox utilities (flexRow, flexColumn, flexBetween)
  - [ ] 2.3 Add spacing utilities (gapXs, gapS, gapM)
  - [ ] 2.4 Add text utilities (textSecondary, textMuted, textMonospace)
  - [ ] 2.5 Import utilities.css in main.tsx
  - [ ] 2.6 Test that utility classes work correctly

- [ ] 3. Create Design Token Reference Documentation
  - [ ] 3.1 Create `frontend/src/styles/design-tokens.md` file
  - [ ] 3.2 Document color tokens with examples and use cases
  - [ ] 3.3 Document spacing scale with pixel equivalents
  - [ ] 3.4 Document typography tokens with usage guidelines
  - [ ] 3.5 Add links to official CloudScape documentation
  - [ ] 3.6 Include token mapping table (hardcoded values → CloudScape tokens)

- [ ] 4. Refactor Global Styles (index.css)
  - [ ] 4.1 Replace background color (#f2f3f3) with `var(--awsui-color-background-layout-main)`
  - [ ] 4.2 Replace text color (#16191f) with `var(--awsui-color-text-body-default)`
  - [ ] 4.3 Verify font-family uses CloudScape font stack
  - [ ] 4.4 Test in light mode
  - [ ] 4.5 Test in dark mode
  - [ ] 4.6 Verify visual appearance unchanged

- [ ] 5. Refactor App-Level Styles (App.css)
  - [ ] 5.1 Replace scrollbar track color (#f2f3f3) with CloudScape token
  - [ ] 5.2 Replace scrollbar thumb colors (#879596, #5f6b7a) with CloudScape tokens
  - [ ] 5.3 Test scrollbar appearance in light mode
  - [ ] 5.4 Test scrollbar appearance in dark mode
  - [ ] 5.5 Verify visual appearance unchanged

- [ ] 6. CHECKPOINT: Capture Baseline (BEFORE Any Component Refactoring)
  - [ ] 6.1 Retrieve Cognito credentials from AWS Secrets Manager
  - [ ] 6.2 Navigate to CloudFront URL: https://d1kqe40a9vwn47.cloudfront.net
  - [ ] 6.3 Login with Cognito credentials
  - [ ] 6.4 Capture screenshot of Dashboard page (desktop 1920x1080)
  - [ ] 6.5 Capture screenshot of ExecutionsPage (desktop 1920x1080)
  - [ ] 6.6 Capture screenshot of ExecutionDetailsPage (desktop 1920x1080)
  - [ ] 6.7 Capture screenshot of RecoveryPlansPage (desktop 1920x1080)
  - [ ] 6.8 Capture screenshot of ProtectionGroupsPage (desktop 1920x1080)
  - [ ] 6.9 Capture screenshot of LoginPage (desktop 1920x1080)
  - [ ] 6.10 Capture screenshot of Dashboard (tablet 768x1024)
  - [ ] 6.11 Capture screenshot of Dashboard (mobile 375x667)
  - [ ] 6.12 Test navigation between all pages
  - [ ] 6.13 Test table filtering and sorting on ExecutionsPage
  - [ ] 6.14 Test modal opening/closing on ProtectionGroupsPage
  - [ ] 6.15 Test form interactions on RecoveryPlansPage
  - [ ] 6.16 Document all interactive elements and their behavior
  - [ ] 6.17 Save baseline screenshots to `.kiro/specs/css-refactoring/screenshots/baseline/`
  - [ ] 6.18 Create baseline functionality checklist
  - [ ] 6.19 Measure baseline page load times for all pages

- [ ] 7. Refactor ExecutionDetailsPage
  - [ ] 7.1 Create `frontend/src/pages/ExecutionDetailsPage.module.css`
  - [ ] 7.2 Extract all inline styles to CSS module classes
  - [ ] 7.3 Replace hardcoded colors with CloudScape tokens
  - [ ] 7.4 Replace hardcoded spacing with CloudScape tokens
  - [ ] 7.5 Replace hardcoded font sizes with CloudScape tokens
  - [ ] 7.6 Update component to import and use CSS module
  - [ ] 7.7 Test visual appearance (before/after comparison)
  - [ ] 7.8 Test theme switching (light/dark)
  - [ ] 7.9 Verify zero inline styles remain

- [ ] 8. Refactor ExecutionsPage
  - [ ] 8.1 Create `frontend/src/pages/ExecutionsPage.module.css`
  - [ ] 8.2 Extract inline styles for table cells (whiteSpace: nowrap)
  - [ ] 8.3 Replace any hardcoded colors with CloudScape tokens
  - [ ] 8.4 Update component to import and use CSS module
  - [ ] 8.5 Test visual appearance
  - [ ] 8.6 Test table functionality
  - [ ] 8.7 Verify zero inline styles remain

- [ ] 9. Refactor LoginPage
  - [ ] 9.1 Create `frontend/src/pages/LoginPage.module.css`
  - [ ] 9.2 Extract all inline styles to CSS module
  - [ ] 9.3 Replace hardcoded colors with CloudScape tokens
  - [ ] 9.4 Replace hardcoded spacing with CloudScape tokens
  - [ ] 9.5 Replace box-shadow with CloudScape shadow tokens
  - [ ] 9.6 Update component to import and use CSS module
  - [ ] 9.7 Test visual appearance
  - [ ] 9.8 Test login functionality
  - [ ] 9.9 Verify zero inline styles remain

- [ ] 10. Refactor Dashboard
  - [ ] 10.1 Create `frontend/src/pages/Dashboard.module.css`
  - [ ] 10.2 Extract all inline styles to CSS module
  - [ ] 10.3 Replace hardcoded values with CloudScape tokens
  - [ ] 10.4 Update component to import and use CSS module
  - [ ] 10.5 Test visual appearance
  - [ ] 10.6 Test dashboard functionality
  - [ ] 10.7 Verify zero inline styles remain

- [ ] 11. Refactor RecoveryPlansPage
  - [ ] 11.1 Create `frontend/src/pages/RecoveryPlansPage.module.css`
  - [ ] 11.2 Extract all inline styles to CSS module
  - [ ] 11.3 Replace hardcoded values with CloudScape tokens
  - [ ] 11.4 Update component to import and use CSS module
  - [ ] 11.5 Test visual appearance
  - [ ] 11.6 Test recovery plans functionality
  - [ ] 11.7 Verify zero inline styles remain

- [ ] 12. Refactor ProtectionGroupsPage
  - [ ] 12.1 Create `frontend/src/pages/ProtectionGroupsPage.module.css`
  - [ ] 12.2 Extract all inline styles to CSS module
  - [ ] 12.3 Replace hardcoded values with CloudScape tokens
  - [ ] 12.4 Update component to import and use CSS module
  - [ ] 12.5 Test visual appearance
  - [ ] 12.6 Test protection groups functionality
  - [ ] 12.7 Verify zero inline styles remain

- [ ] 13. Refactor LoadingState Component
  - [ ] 13.1 Create `frontend/src/components/LoadingState.module.css`
  - [ ] 13.2 Extract all inline styles to CSS module
  - [ ] 13.3 Replace hardcoded colors (#5f6b7a) with CloudScape tokens
  - [ ] 13.4 Replace hardcoded spacing with CloudScape tokens
  - [ ] 13.5 Update component to import and use CSS module
  - [ ] 13.6 Test all loading state variants (inline, centered, fullscreen)
  - [ ] 13.7 Verify zero inline styles remain

- [ ] 14. Refactor PasswordChangeForm Component
  - [ ] 14.1 Create `frontend/src/components/PasswordChangeForm.module.css`
  - [ ] 14.2 Extract all inline styles to CSS module
  - [ ] 14.3 Replace hardcoded colors with CloudScape tokens
  - [ ] 14.4 Replace hardcoded spacing with CloudScape tokens
  - [ ] 14.5 Replace box-shadow with CloudScape shadow tokens
  - [ ] 14.6 Update component to import and use CSS module
  - [ ] 14.7 Test visual appearance
  - [ ] 14.8 Test password change functionality
  - [ ] 14.9 Verify zero inline styles remain

- [ ] 15. Refactor ServerSelector Component
  - [ ] 15.1 Create `frontend/src/components/ServerSelector.module.css`
  - [ ] 15.2 Extract all inline styles to CSS module
  - [ ] 15.3 Replace hardcoded colors with CloudScape tokens
  - [ ] 15.4 Replace hardcoded spacing with CloudScape tokens
  - [ ] 15.5 Update component to import and use CSS module
  - [ ] 15.6 Test server selection functionality
  - [ ] 15.7 Test search and filtering
  - [ ] 15.8 Verify zero inline styles remain

- [ ] 16. Refactor InvocationSourceBadge Component
  - [ ] 16.1 Create `frontend/src/components/InvocationSourceBadge.module.css`
  - [ ] 16.2 Extract inline styles (display, alignItems, gap, whiteSpace)
  - [ ] 16.3 Replace hardcoded spacing with CloudScape tokens
  - [ ] 16.4 Update component to import and use CSS module
  - [ ] 16.5 Test badge display for all invocation sources
  - [ ] 16.6 Verify zero inline styles remain

- [ ] 17. Refactor DataTableSkeleton Component
  - [ ] 17.1 Create `frontend/src/components/DataTableSkeleton.module.css`
  - [ ] 17.2 Extract all inline styles to CSS module
  - [ ] 17.3 Replace hardcoded colors with CloudScape tokens
  - [ ] 17.4 Replace hardcoded spacing with CloudScape tokens
  - [ ] 17.5 Update component to import and use CSS module
  - [ ] 17.6 Test skeleton loading state
  - [ ] 17.7 Verify zero inline styles remain

- [ ] 18. Refactor ProtectionGroupDialog Component
  - [ ] 18.1 Create `frontend/src/components/ProtectionGroupDialog.module.css`
  - [ ] 18.2 Extract inline styles (maxHeight, overflow, border)
  - [ ] 18.3 Replace hardcoded values with CloudScape tokens
  - [ ] 18.4 Update component to import and use CSS module
  - [ ] 18.5 Test dialog functionality
  - [ ] 18.6 Test server preview scrolling
  - [ ] 18.7 Verify zero inline styles remain

- [ ] 19. Refactor ImportResultsDialog Component
  - [ ] 19.1 Create `frontend/src/components/ImportResultsDialog.module.css`
  - [ ] 19.2 Extract inline styles (color, fontSize)
  - [ ] 19.3 Replace hardcoded values with CloudScape tokens
  - [ ] 19.4 Update component to import and use CSS module
  - [ ] 19.5 Test dialog display
  - [ ] 19.6 Verify zero inline styles remain

- [ ] 20. Refactor WaveConfigEditor Component
  - [ ] 20.1 Create `frontend/src/components/WaveConfigEditor.module.css`
  - [ ] 20.2 Extract inline styles (display, alignItems, gap, fontWeight)
  - [ ] 20.3 Replace hardcoded spacing with CloudScape tokens
  - [ ] 20.4 Update component to import and use CSS module
  - [ ] 20.5 Test wave configuration editing
  - [ ] 20.6 Test expand/collapse functionality
  - [ ] 20.7 Verify zero inline styles remain

- [ ] 21. Refactor AccountSelector Component
  - [ ] 21.1 Create `frontend/src/components/AccountSelector.module.css`
  - [ ] 21.2 Extract inline styles (minWidth)
  - [ ] 21.3 Replace hardcoded spacing with CloudScape tokens
  - [ ] 21.4 Update component to import and use CSS module
  - [ ] 21.5 Test account selection
  - [ ] 21.6 Verify zero inline styles remain

- [ ] 22. Refactor ErrorFallback Component
  - [ ] 22.1 Create `frontend/src/components/ErrorFallback.module.css`
  - [ ] 22.2 Extract all inline styles to CSS module
  - [ ] 22.3 Replace hardcoded colors with CloudScape status tokens
  - [ ] 22.4 Replace hardcoded spacing with CloudScape tokens
  - [ ] 22.5 Update component to import and use CSS module
  - [ ] 22.6 Test error display
  - [ ] 22.7 Test error details expansion
  - [ ] 22.8 Verify zero inline styles remain

- [ ] 23. Audit Remaining Components
  - [ ] 23.1 Run grep search for `style={{` in all component files
  - [ ] 23.2 Create list of remaining components needing refactoring
  - [ ] 23.3 Prioritize components by inline style count
  - [ ] 23.4 Document any justified inline styles with comments

- [ ] 24. Refactor Remaining Components (Batch 1)
  - [ ] 24.1 Create CSS modules for identified components
  - [ ] 24.2 Extract inline styles to CSS modules
  - [ ] 24.3 Replace hardcoded values with CloudScape tokens
  - [ ] 24.4 Update components to use CSS modules
  - [ ] 24.5 Test all refactored components
  - [ ] 24.6 Verify zero inline styles remain

- [ ] 25. Refactor Remaining Components (Batch 2)
  - [ ] 25.1 Create CSS modules for identified components
  - [ ] 25.2 Extract inline styles to CSS modules
  - [ ] 25.3 Replace hardcoded values with CloudScape tokens
  - [ ] 25.4 Update components to use CSS modules
  - [ ] 25.5 Test all refactored components
  - [ ] 25.6 Verify zero inline styles remain

- [ ] 26. Configure ESLint Rules for Inline Styles
  - [ ] 26.1 Add `react/forbid-dom-props` rule to .eslintrc
  - [ ] 26.2 Configure rule to error on `style` prop
  - [ ] 26.3 Add `react/forbid-component-props` rule as warning
  - [ ] 26.4 Test ESLint configuration
  - [ ] 26.5 Run ESLint on entire codebase
  - [ ] 26.6 Fix any ESLint errors

- [ ] 27. Configure Stylelint Rules
  - [ ] 27.1 Install stylelint and required plugins
  - [ ] 27.2 Create .stylelintrc.json configuration
  - [ ] 27.3 Add `color-no-hex` rule
  - [ ] 27.4 Add rule to disallow hardcoded spacing values
  - [ ] 27.5 Add `custom-property-pattern` rule for camelCase
  - [ ] 27.6 Add `selector-class-pattern` rule for camelCase
  - [ ] 27.7 Test Stylelint configuration
  - [ ] 27.8 Run Stylelint on all CSS files
  - [ ] 27.9 Fix any Stylelint errors

- [ ] 28. Integrate CSS Linting into CI/CD
  - [ ] 28.1 Add ESLint step to deploy.sh script
  - [ ] 28.2 Add Stylelint step to deploy.sh script
  - [ ] 28.3 Configure linting to run before deployment
  - [ ] 28.4 Test CI/CD pipeline with linting
  - [ ] 28.5 Document linting in deployment guide

- [ ] 29. Visual Regression Testing (AFTER Refactoring)
  - [ ] 28.1 Retrieve Cognito credentials from AWS Secrets Manager
  - [ ] 28.2 Navigate to CloudFront URL: https://d1kqe40a9vwn47.cloudfront.net
  - [ ] 28.3 Login with Cognito credentials
  - [ ] 28.4 Capture screenshot of Dashboard page (desktop 1920x1080)
  - [ ] 28.5 Capture screenshot of ExecutionsPage (desktop 1920x1080)
  - [ ] 28.6 Capture screenshot of ExecutionDetailsPage (desktop 1920x1080)
  - [ ] 28.7 Capture screenshot of RecoveryPlansPage (desktop 1920x1080)
  - [ ] 28.8 Capture screenshot of ProtectionGroupsPage (desktop 1920x1080)
  - [ ] 28.9 Capture screenshot of Dashboard (tablet 768x1024)
  - [ ] 28.10 Capture screenshot of Dashboard (mobile 375x667)
  - [ ] 28.11 Test navigation between all pages
  - [ ] 28.12 Test table filtering and sorting on ExecutionsPage
  - [ ] 28.13 Test modal opening/closing on ProtectionGroupsPage
  - [ ] 28.14 Test form interactions on RecoveryPlansPage
  - [ ] 28.15 Document all interactive elements and their behavior
  - [ ] 28.16 Save baseline screenshots to `.kiro/specs/css-refactoring/baseline/`
  - [ ] 28.17 Create baseline functionality checklist

- [ ] 29. Visual Regression Testing (AFTER Refactoring)
  - [ ] 29.1 Navigate to CloudFront URL: https://d1kqe40a9vwn47.cloudfront.net
  - [ ] 29.2 Login with Cognito credentials
  - [ ] 29.3 Capture screenshot of Dashboard page (desktop 1920x1080)
  - [ ] 29.4 Capture screenshot of ExecutionsPage (desktop 1920x1080)
  - [ ] 29.5 Capture screenshot of ExecutionDetailsPage (desktop 1920x1080)
  - [ ] 29.6 Capture screenshot of RecoveryPlansPage (desktop 1920x1080)
  - [ ] 29.7 Capture screenshot of ProtectionGroupsPage (desktop 1920x1080)
  - [ ] 29.8 Capture screenshot of Dashboard (tablet 768x1024)
  - [ ] 29.9 Capture screenshot of Dashboard (mobile 375x667)
  - [ ] 29.10 Compare all screenshots with baseline (pixel-perfect comparison)
  - [ ] 29.11 Review and document any visual differences
  - [ ] 29.12 Verify all differences are intentional improvements
  - [ ] 29.13 Test in Chrome (latest)
  - [ ] 29.14 Test in Firefox (latest)
  - [ ] 29.15 Test in Safari (latest)
  - [ ] 29.16 Save comparison report to `.kiro/specs/css-refactoring/screenshots/comparison/`

- [ ] 30. Functional Regression Testing (AFTER Refactoring)
  - [ ] 30.1 Navigate to CloudFront URL and login
  - [ ] 30.2 Test Dashboard: Verify all widgets load correctly
  - [ ] 30.3 Test Dashboard: Verify statistics display correctly
  - [ ] 30.4 Test Dashboard: Verify navigation links work
  - [ ] 30.5 Test ExecutionsPage: Verify table loads with data
  - [ ] 30.6 Test ExecutionsPage: Verify filtering works
  - [ ] 30.7 Test ExecutionsPage: Verify sorting works
  - [ ] 30.8 Test ExecutionsPage: Verify pagination works
  - [ ] 30.9 Test ExecutionsPage: Click execution to view details
  - [ ] 30.10 Test ExecutionDetailsPage: Verify all execution details display
  - [ ] 30.11 Test ExecutionDetailsPage: Verify wave information displays
  - [ ] 30.12 Test ExecutionDetailsPage: Verify progress bars render
  - [ ] 30.13 Test RecoveryPlansPage: Verify table loads
  - [ ] 30.14 Test RecoveryPlansPage: Open create recovery plan modal
  - [ ] 30.15 Test RecoveryPlansPage: Verify form fields work
  - [ ] 30.16 Test RecoveryPlansPage: Close modal without saving
  - [ ] 30.17 Test ProtectionGroupsPage: Verify table loads
  - [ ] 30.18 Test ProtectionGroupsPage: Open protection group dialog
  - [ ] 30.19 Test ProtectionGroupsPage: Verify server selector works
  - [ ] 30.20 Test ProtectionGroupsPage: Close dialog
  - [ ] 30.21 Test all navigation: Side navigation works
  - [ ] 30.22 Test all navigation: Breadcrumbs work
  - [ ] 30.23 Test all navigation: Back button works
  - [ ] 30.24 Test error handling: Verify error messages display correctly
  - [ ] 30.25 Test loading states: Verify spinners display correctly
  - [ ] 30.26 Compare functionality with baseline checklist
  - [ ] 30.27 Document any functional differences
  - [ ] 30.28 Verify all differences are intentional improvements

- [ ] 31. Theme Switching Testing (AFTER Refactoring)
  - [ ] 31.1 Navigate to CloudFront URL and login
  - [ ] 31.2 Test Dashboard in light mode: Capture screenshot
  - [ ] 31.3 Switch to dark mode: Verify theme changes without reload
  - [ ] 31.4 Test Dashboard in dark mode: Capture screenshot
  - [ ] 31.5 Verify all CloudScape tokens adapted correctly
  - [ ] 31.6 Test ExecutionsPage in light mode: Capture screenshot
  - [ ] 31.7 Switch to dark mode: Verify theme changes
  - [ ] 31.8 Test ExecutionsPage in dark mode: Capture screenshot
  - [ ] 31.9 Test ExecutionDetailsPage in light mode: Capture screenshot
  - [ ] 31.10 Switch to dark mode: Verify theme changes
  - [ ] 31.11 Test ExecutionDetailsPage in dark mode: Capture screenshot
  - [ ] 31.12 Test RecoveryPlansPage in light mode: Capture screenshot
  - [ ] 31.13 Switch to dark mode: Verify theme changes
  - [ ] 31.14 Test RecoveryPlansPage in dark mode: Capture screenshot
  - [ ] 31.15 Test ProtectionGroupsPage in light mode: Capture screenshot
  - [ ] 31.16 Switch to dark mode: Verify theme changes
  - [ ] 31.17 Test ProtectionGroupsPage in dark mode: Capture screenshot
  - [ ] 31.18 Test LoginPage in light mode: Capture screenshot
  - [ ] 31.19 Switch to dark mode: Verify theme changes
  - [ ] 31.20 Test LoginPage in dark mode: Capture screenshot
  - [ ] 31.21 Verify custom components adapt to theme
  - [ ] 31.22 Verify no hardcoded colors remain visible
  - [ ] 31.23 Save theme comparison screenshots to `.kiro/specs/css-refactoring/screenshots/themes/`
  - [ ] 31.24 Document any theme-specific issues

- [ ] 32. Accessibility Testing (AFTER Refactoring)
  - [ ] 32.1 Navigate to CloudFront URL and login
  - [ ] 32.2 Run accessibility audit on Dashboard
  - [ ] 32.3 Run accessibility audit on ExecutionsPage
  - [ ] 32.4 Run accessibility audit on ExecutionDetailsPage
  - [ ] 32.5 Run accessibility audit on RecoveryPlansPage
  - [ ] 32.6 Run accessibility audit on ProtectionGroupsPage
  - [ ] 32.7 Verify color contrast ratios meet WCAG AA standards
  - [ ] 32.8 Verify focus indicators are visible
  - [ ] 32.9 Verify keyboard navigation works
  - [ ] 32.10 Verify screen reader compatibility
  - [ ] 32.11 Document any accessibility improvements
  - [ ] 32.12 Document any accessibility regressions (should be none)

- [ ] 33. Performance Testing (AFTER Refactoring)
  - [ ] 33.1 Navigate to CloudFront URL and login
  - [ ] 33.2 Measure Dashboard page load time
  - [ ] 33.3 Measure ExecutionsPage page load time
  - [ ] 33.4 Measure ExecutionDetailsPage page load time
  - [ ] 33.5 Measure RecoveryPlansPage page load time
  - [ ] 33.6 Measure ProtectionGroupsPage page load time
  - [ ] 33.7 Compare with baseline performance metrics
  - [ ] 33.8 Verify CSS bundle size (should be smaller or same)
  - [ ] 33.9 Verify no performance regressions
  - [ ] 33.10 Document any performance improvements

- [ ] 34. Update Developer Documentation
  - [ ] 34.1 Create example component demonstrating CSS module usage
  - [ ] 34.2 Create example component demonstrating CloudScape token usage
  - [ ] 34.3 Document common styling patterns for cards
  - [ ] 34.4 Document common styling patterns for lists
  - [ ] 34.5 Document common styling patterns for forms
  - [ ] 34.6 Document common styling patterns for modals
  - [ ] 34.7 Provide before/after examples of refactored components
  - [ ] 34.8 Update DEVELOPER_GUIDE.md with CSS guidelines
  - [ ] 34.9 Create quick reference guide for CloudScape tokens
  - [ ] 34.10 Document Playwright testing procedures
  - [ ] 34.11 Document baseline capture process
  - [ ] 34.12 Document visual regression testing process

- [ ] 35. Final Audit and Cleanup
  - [ ] 35.1 Run automated search for inline styles
  - [ ] 35.2 Run automated search for hardcoded colors
  - [ ] 35.3 Run automated search for hardcoded spacing
  - [ ] 35.4 Run automated search for hardcoded z-index
  - [ ] 35.5 Review and document any remaining exceptions
  - [ ] 35.6 Update migration checklist
  - [ ] 35.7 Run all ESLint checks
  - [ ] 35.8 Run all Stylelint checks
  - [ ] 35.9 Run final visual regression tests
  - [ ] 35.10 Run final functional regression tests
  - [ ] 35.11 Run final theme switching tests
  - [ ] 35.12 Run final accessibility tests
  - [ ] 35.13 Run final performance tests
  - [ ] 35.14 Create final refactoring report with all test results
  - [ ] 35.15 Document all improvements and changes
  - [ ] 35.16 Get stakeholder approval for deployment

## Notes

- All tasks are required for complete implementation
- All tests are required (no optional tests)
- Each task includes validation through testing
- Checkpoints ensure incremental validation
- Visual regression testing ensures no unintended changes
- Theme switching testing ensures CloudScape token compliance
- Browser compatibility testing ensures cross-browser support
- Documentation updates ensure clarity for developers

## Implementation Order Rationale

1. **Foundation first** - Z-index scale, utilities, documentation
2. **Global styles next** - index.css, App.css
3. **Pages** - High-impact, user-facing components
4. **Shared components** - Reusable components used across pages
5. **Specialized components** - Remaining components
6. **Validation & cleanup** - Linting, testing, documentation

This order ensures foundational infrastructure is in place before refactoring components, and validation happens throughout the process.

## Success Metrics

- 0 inline styles (except justified with comments)
- 100% CloudScape token usage for colors, spacing, typography
- 0 visual regressions
- Theme switching works correctly on all pages
- All linting rules pass
- Documentation complete
- All tests pass


## Summary

**Total Tasks:** 35
**Total Subtasks:** 267

**Phase Breakdown:**
- Phase 1 (Foundation): Tasks 1-6 (44 subtasks) - Includes baseline capture
- Phase 2 (Pages): Tasks 7-12 (42 subtasks)
- Phase 3 (Shared Components): Tasks 13-22 (63 subtasks)
- Phase 4 (Specialized Components): Tasks 23-25 (18 subtasks)
- Phase 5 (Validation & Cleanup): Tasks 26-35 (100 subtasks)

**Estimated Timeline:**
- Phase 1: 2-3 days (includes comprehensive baseline capture)
- Phase 2: 3-4 days
- Phase 3: 4-5 days
- Phase 4: 2-3 days
- Phase 5: 4-5 days (includes extensive Playwright testing)
- **Total: 15-20 days**

**Testing Requirements:**
- Baseline capture using Playwright MCP (BEFORE refactoring)
- Visual regression testing using Playwright MCP (AFTER refactoring)
- Functional regression testing using Playwright MCP (AFTER refactoring)
- Theme switching testing using Playwright MCP
- Accessibility testing
- Performance testing
- Browser compatibility testing (Chrome, Firefox, Safari)
- Viewport testing (mobile, tablet, desktop)
- All tests use Cognito credentials from AWS Secrets Manager
- All tests run against CloudFront URL: https://d1kqe40a9vwn47.cloudfront.net

**Playwright MCP Integration:**
- Task 6: Baseline capture (BEFORE any refactoring) → `.kiro/specs/css-refactoring/screenshots/baseline/`
- Task 29: Visual regression testing (AFTER refactoring) → `.kiro/specs/css-refactoring/screenshots/comparison/`
- Task 30: Functional regression testing (AFTER refactoring)
- Task 31: Theme switching testing (AFTER refactoring) → `.kiro/specs/css-refactoring/screenshots/themes/`
- Task 32: Accessibility testing (AFTER refactoring)
- Task 33: Performance testing (AFTER refactoring)

**Success Metrics:**
- 0 inline styles (except justified)
- 100% CloudScape token usage
- 0 visual regressions (pixel-perfect comparison)
- 0 functional regressions
- Theme switching works correctly
- All linting rules pass
- Documentation complete
- All Playwright tests pass
- Stakeholder approval obtained
