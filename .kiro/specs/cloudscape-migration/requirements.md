# CloudScape Migration Specification

## Overview
Migrate the AWS DRS Orchestration frontend from Material-UI to AWS CloudScape Design System while maintaining the current look, feel, and functionality.

## Goals
1. Replace all Material-UI components with CloudScape equivalents
2. Maintain existing functionality and user workflows
3. Preserve AWS-branded theme and visual consistency
4. Improve alignment with AWS console design patterns
5. Ensure accessibility (WCAG 2.1 AA) is maintained

## Scope

### Components to Migrate (23 total)

#### Pages (5)
1. LoginPage.tsx - Cognito authentication
2. Dashboard.tsx - Overview metrics
3. ProtectionGroupsPage.tsx - Protection Groups CRUD
4. RecoveryPlansPage.tsx - Recovery Plans CRUD
5. ExecutionsPage.tsx - Execution monitoring

#### Shared Components (18)
1. ProtectionGroupDialog.tsx - Create/Edit Protection Groups
2. RecoveryPlanDialog.tsx - Create/Edit Recovery Plans
3. ServerSelector.tsx - Visual server selection
4. RegionSelector.tsx - AWS region dropdown
5. StatusBadge.tsx - Status indicators
6. WaveProgress.tsx - Wave execution timeline
7. DateTimeDisplay.tsx - Timestamp formatting
8. ConfirmDialog.tsx - Confirmation dialogs
9. TagFilterEditor.tsx - Tag-based filtering
10. ErrorBoundary.tsx - Error handling
11. LoadingSpinner.tsx - Loading states
12. EmptyState.tsx - Empty data states
13. SearchBar.tsx - Search functionality
14. Pagination.tsx - Table pagination
15. SortableTable.tsx - Sortable tables
16. ActionButton.tsx - Action buttons
17. InfoPanel.tsx - Information panels
18. NavigationBar.tsx - Top navigation

### Dependencies to Update

#### Remove
- @mui/material (6.1.3)
- @mui/icons-material
- @emotion/react
- @emotion/styled

#### Add
- @cloudscape-design/components (latest)
- @cloudscape-design/global-styles (latest)
- @cloudscape-design/design-tokens (latest)
- @cloudscape-design/collection-hooks (for tables)

## Component Mapping

### Material-UI → CloudScape

| Material-UI | CloudScape | Notes |
|-------------|------------|-------|
| Button | Button | Similar API |
| TextField | Input, FormField | Wrapped in FormField |
| Select | Select | Similar API |
| Dialog | Modal | Different prop names |
| DataGrid | Table | Significant API differences |
| Stepper | ProgressIndicator | Different structure |
| Chip | Badge | Similar concept |
| Alert | Alert, Flashbar | Flashbar for notifications |
| Card | Container | Different styling |
| AppBar | TopNavigation | AWS console pattern |
| Drawer | SideNavigation | AWS console pattern |
| Tabs | Tabs | Similar API |
| Checkbox | Checkbox | Similar API |
| Radio | RadioGroup | Similar API |
| Switch | Toggle | Different name |
| Tooltip | Popover | More flexible |
| CircularProgress | Spinner | Different API |
| LinearProgress | ProgressBar | Similar concept |

## Migration Strategy

### Phase 1: Setup & Infrastructure
1. Install CloudScape dependencies
2. Remove Material-UI dependencies
3. Update theme configuration
4. Create CloudScape theme wrapper
5. Update global styles

### Phase 2: Core Components
1. Migrate shared utility components (StatusBadge, DateTimeDisplay)
2. Migrate form components (dialogs, selectors)
3. Migrate layout components (navigation, panels)

### Phase 3: Page Components
1. Migrate LoginPage
2. Migrate ProtectionGroupsPage
3. Migrate RecoveryPlansPage
4. Migrate ExecutionsPage
5. Migrate Dashboard

### Phase 4: Testing & Refinement
1. Visual regression testing
2. Functionality testing
3. Accessibility testing
4. Performance testing
5. Cross-browser testing

## Design Considerations

### Visual Consistency
- Use CloudScape's AWS-branded theme
- Maintain current color scheme where possible
- Preserve spacing and layout patterns
- Keep existing iconography (AWS icons)

### Functionality Preservation
- All CRUD operations work identically
- Server discovery flow unchanged
- Execution monitoring unchanged
- Search and filtering unchanged
- Pagination unchanged

### Accessibility
- Maintain WCAG 2.1 AA compliance
- Keyboard navigation working
- Screen reader support
- Focus management
- Color contrast ratios

## Key Differences to Handle

### 1. Table Component
Material-UI DataGrid is feature-rich. CloudScape Table requires:
- Manual sorting implementation
- Manual filtering implementation
- Manual pagination implementation
- Collection hooks for state management

### 2. Modal/Dialog
CloudScape Modal has different:
- Prop names (visible vs open)
- Footer structure (explicit footer prop)
- Size options (small, medium, large, max)

### 3. Form Fields
CloudScape requires:
- FormField wrapper for labels and errors
- Explicit error state management
- Different validation patterns

### 4. Navigation
CloudScape uses AWS console patterns:
- TopNavigation for header
- SideNavigation for sidebar
- BreadcrumbGroup for breadcrumbs

### 5. Notifications
CloudScape uses Flashbar for notifications:
- Stack of flash messages
- Different dismiss patterns
- Type-based styling (success, error, warning, info)

## Acceptance Criteria

### Functional Requirements
- [ ] All pages render without errors
- [ ] All CRUD operations work
- [ ] Server discovery works
- [ ] Execution monitoring works
- [ ] Search and filtering work
- [ ] Pagination works
- [ ] Sorting works
- [ ] Authentication flow works

### Visual Requirements
- [ ] AWS-branded theme applied
- [ ] Consistent spacing and layout
- [ ] Proper color contrast
- [ ] Icons display correctly
- [ ] Responsive design works
- [ ] Loading states display
- [ ] Error states display
- [ ] Empty states display

### Technical Requirements
- [ ] No Material-UI dependencies remain
- [ ] CloudScape dependencies installed
- [ ] Build succeeds without warnings
- [ ] Bundle size acceptable (<3MB)
- [ ] No console errors
- [ ] TypeScript types correct

### Testing Requirements
- [ ] All existing tests pass
- [ ] Visual regression tests pass
- [ ] Accessibility tests pass
- [ ] Cross-browser tests pass
- [ ] Performance benchmarks met

## Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation:** Migrate incrementally, test each component

### Risk 2: Visual Inconsistencies
**Mitigation:** Create design system documentation, use CloudScape tokens

### Risk 3: Functionality Loss
**Mitigation:** Comprehensive testing, feature parity checklist

### Risk 4: Performance Degradation
**Mitigation:** Performance benchmarks, bundle size monitoring

## Timeline Estimate

- **Phase 1 (Setup):** 2-4 hours
- **Phase 2 (Core Components):** 8-12 hours
- **Phase 3 (Pages):** 8-12 hours
- **Phase 4 (Testing):** 4-6 hours

**Total:** 22-34 hours

## Success Metrics

- Zero Material-UI dependencies
- All functionality preserved
- WCAG 2.1 AA compliance maintained
- Bundle size <3MB
- No visual regressions
- User workflows unchanged
