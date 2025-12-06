---
inclusion: manual
---

# CloudScape Migration Steering Guide

## Purpose
Guide the migration of AWS DRS Orchestration frontend from Material-UI to CloudScape Design System while maintaining functionality and AWS-branded look/feel.

## Core Principles

### 1. Incremental Migration
- Migrate one component at a time
- Test each component before moving to next
- Keep application functional throughout migration
- Use feature flags if needed for gradual rollout

### 2. Functionality Preservation
- All CRUD operations must work identically
- Server discovery flow unchanged
- Execution monitoring unchanged
- Search, filtering, sorting unchanged
- Authentication flow unchanged

### 3. Visual Consistency
- Use CloudScape's AWS-branded theme
- Maintain current spacing and layout patterns
- Preserve color scheme where possible
- Keep existing iconography (AWS icons)

### 4. Accessibility First
- Maintain WCAG 2.1 AA compliance
- Test keyboard navigation after each component
- Verify screen reader compatibility
- Ensure proper focus management

## Component Migration Patterns

### Pattern 1: Dialog → Modal
**Always use this pattern for dialogs:**

```typescript
// Material-UI (OLD)
<Dialog open={open} onClose={onClose}>
  <DialogTitle>Title</DialogTitle>
  <DialogContent>Content</DialogContent>
  <DialogActions>
    <Button onClick={onClose}>Cancel</Button>
    <Button onClick={onSave}>Save</Button>
  </DialogActions>
</Dialog>

// CloudScape (NEW)
<Modal
  visible={visible}
  onDismiss={onDismiss}
  header="Title"
  footer={
    <Box float="right">
      <SpaceBetween direction="horizontal" size="xs">
        <Button onClick={onDismiss}>Cancel</Button>
        <Button variant="primary" onClick={onSave}>Save</Button>
      </SpaceBetween>
    </Box>
  }
>
  Content
</Modal>
```

**Key Changes:**
- `open` → `visible`
- `onClose` → `onDismiss`
- Explicit `header` and `footer` props
- Footer requires manual layout with SpaceBetween

### Pattern 2: TextField → FormField + Input
**Always wrap inputs in FormField:**

```typescript
// Material-UI (OLD)
<TextField
  label="Name"
  value={value}
  onChange={(e) => setValue(e.target.value)}
  error={Boolean(error)}
  helperText={error || "Helper text"}
  fullWidth
/>

// CloudScape (NEW)
<FormField
  label="Name"
  description="Helper text"
  errorText={error}
>
  <Input
    value={value}
    onChange={({ detail }) => setValue(detail.value)}
  />
</FormField>
```

**Key Changes:**
- Separate FormField wrapper for label/error
- `onChange` event has `detail` property
- No `fullWidth` prop (default behavior)
- `helperText` → `description`
- `errorText` for errors

### Pattern 3: DataGrid → Table + Collection Hooks
**Use collection hooks for table state:**

```typescript
// Material-UI (OLD)
<DataGrid
  rows={rows}
  columns={columns}
  loading={loading}
  pageSize={25}
  sortModel={sortModel}
  onSortModelChange={setSortModel}
/>

// CloudScape (NEW)
import { useCollection } from '@cloudscape-design/collection-hooks';

const { items, collectionProps, filterProps, paginationProps } = useCollection(
  allItems,
  {
    filtering: {
      empty: <EmptyState />,
      noMatch: <NoMatchState />,
    },
    pagination: { pageSize: 25 },
    sorting: {},
  }
);

<Table
  {...collectionProps}
  columnDefinitions={columnDefinitions}
  items={items}
  loading={loading}
  loadingText="Loading..."
  filter={<TextFilter {...filterProps} />}
  pagination={<Pagination {...paginationProps} />}
/>
```

**Key Changes:**
- Manual sorting/filtering implementation
- Use `@cloudscape-design/collection-hooks`
- Separate filter and pagination components
- `columnDefinitions` instead of `columns`

### Pattern 4: Select → Select with Options
**Use option objects:**

```typescript
// Material-UI (OLD)
<Select value={value} onChange={onChange}>
  <MenuItem value="us-east-1">US East (N. Virginia)</MenuItem>
  <MenuItem value="us-west-2">US West (Oregon)</MenuItem>
</Select>

// CloudScape (NEW)
<Select
  selectedOption={{ value: value, label: getLabel(value) }}
  onChange={({ detail }) => onChange(detail.selectedOption.value)}
  options={[
    { value: 'us-east-1', label: 'US East (N. Virginia)' },
    { value: 'us-west-2', label: 'US West (Oregon)' }
  ]}
/>
```

**Key Changes:**
- `selectedOption` object with value/label
- `options` array of objects
- `onChange` has `detail.selectedOption`

### Pattern 5: Stepper → ProgressIndicator
**Use steps array:**

```typescript
// Material-UI (OLD)
<Stepper activeStep={activeStep}>
  <Step>
    <StepLabel>Wave 1</StepLabel>
  </Step>
  <Step>
    <StepLabel>Wave 2</StepLabel>
  </Step>
</Stepper>

// CloudScape (NEW)
<ProgressIndicator
  currentStepIndex={currentStepIndex}
  steps={[
    { label: 'Wave 1', description: 'Description' },
    { label: 'Wave 2', description: 'Description' }
  ]}
/>
```

**Key Changes:**
- `activeStep` → `currentStepIndex`
- `steps` array with label/description
- No separate Step components

## Migration Workflow

### For Each Component:

1. **Read Original Component**
   - Understand current functionality
   - Identify Material-UI components used
   - Note any complex logic

2. **Create CloudScape Version**
   - Replace Material-UI imports with CloudScape
   - Apply migration patterns from above
   - Maintain all functionality
   - Keep same prop interface if possible

3. **Test Component**
   - Visual appearance matches
   - All interactions work
   - No console errors
   - TypeScript types correct

4. **Update Imports**
   - Remove Material-UI imports
   - Add CloudScape imports
   - Update any related utilities

5. **Verify Integration**
   - Test in parent components
   - Check data flow
   - Verify event handlers

## Common Pitfalls to Avoid

### ❌ Don't: Mix Material-UI and CloudScape
```typescript
// BAD - mixing libraries
import { Button } from '@mui/material';
import { Modal } from '@cloudscape-design/components';
```

### ✅ Do: Complete component migration
```typescript
// GOOD - all CloudScape
import { Button, Modal } from '@cloudscape-design/components';
```

### ❌ Don't: Forget event.detail
```typescript
// BAD - Material-UI pattern
onChange={(e) => setValue(e.target.value)}
```

### ✅ Do: Use detail property
```typescript
// GOOD - CloudScape pattern
onChange={({ detail }) => setValue(detail.value)}
```

### ❌ Don't: Assume same prop names
```typescript
// BAD - Material-UI props
<Modal open={open} onClose={onClose} />
```

### ✅ Do: Use CloudScape prop names
```typescript
// GOOD - CloudScape props
<Modal visible={visible} onDismiss={onDismiss} />
```

### ❌ Don't: Skip FormField wrapper
```typescript
// BAD - Input without FormField
<Input value={value} onChange={onChange} />
```

### ✅ Do: Always wrap inputs
```typescript
// GOOD - Input with FormField
<FormField label="Name" errorText={error}>
  <Input value={value} onChange={onChange} />
</FormField>
```

## Testing Checklist

After migrating each component, verify:

- [ ] Component renders without errors
- [ ] All props work correctly
- [ ] Event handlers fire properly
- [ ] Validation works (if applicable)
- [ ] Error states display correctly
- [ ] Loading states work
- [ ] Keyboard navigation works
- [ ] Screen reader announces correctly
- [ ] Visual appearance matches design
- [ ] No Material-UI imports remain
- [ ] TypeScript types are correct
- [ ] No console warnings

## File Organization

### New Files to Create:
```
frontend/src/
├── styles/
│   └── cloudscape-theme.ts          # Theme configuration
├── components/
│   └── cloudscape/
│       ├── AppLayout.tsx             # Main layout wrapper
│       ├── ContentLayout.tsx         # Page content wrapper
│       └── TableWrapper.tsx          # Reusable table component
└── hooks/
    ├── useTableCollection.ts         # Table state management
    └── useFlashbar.ts                # Notification management
```

### Files to Modify:
- All 23 component files (5 pages + 18 shared)
- `src/main.tsx` - Update global styles
- `package.json` - Update dependencies

### Files to Delete:
- `src/theme/` directory (Material-UI theme)
- Any Material-UI specific utilities

## CloudScape Resources

### Official Documentation
- Components: https://cloudscape.design/components/
- Patterns: https://cloudscape.design/patterns/
- Design Tokens: https://cloudscape.design/foundation/visual-foundation/design-tokens/

### Key Packages
- `@cloudscape-design/components` - UI components
- `@cloudscape-design/global-styles` - Global CSS
- `@cloudscape-design/design-tokens` - Theme tokens
- `@cloudscape-design/collection-hooks` - Table state management

### Useful Hooks
- `useCollection` - Table sorting/filtering/pagination
- `useColumnWidths` - Responsive table columns
- `useLocalStorage` - Persist user preferences

## Success Metrics

Track these metrics throughout migration:

- **Components Migrated:** X / 23
- **Material-UI Imports:** 0 (target)
- **Bundle Size:** <3MB (target)
- **Build Warnings:** 0 (target)
- **Console Errors:** 0 (target)
- **TypeScript Errors:** 0 (target)
- **Accessibility Score:** WCAG 2.1 AA (target)

## Phase Completion Criteria

### Phase 1: Setup ✅
- CloudScape dependencies installed
- Material-UI dependencies removed
- Theme configuration created
- Global styles updated
- Layout wrappers created

### Phase 2: Core Components ✅
- All 12 shared components migrated
- No Material-UI imports in shared components
- All components tested individually
- TypeScript types correct

### Phase 3: Pages ✅
- All 5 page components migrated
- No Material-UI imports in pages
- All CRUD operations working
- Search/filter/sort working

### Phase 4: Testing ✅
- Visual regression tests pass
- Functionality tests pass
- Accessibility tests pass
- Performance benchmarks met
- No console errors/warnings

## Troubleshooting

### Issue: Table not sorting
**Solution:** Ensure `useCollection` hook is configured with sorting:
```typescript
const { items, collectionProps } = useCollection(allItems, {
  sorting: {
    defaultState: {
      sortingColumn: columnDefinitions[0],
      isDescending: false,
    },
  },
});
```

### Issue: Modal not closing
**Solution:** Check `onDismiss` prop is connected:
```typescript
<Modal
  visible={visible}
  onDismiss={() => setVisible(false)}  // Must update state
/>
```

### Issue: Input not updating
**Solution:** Use `detail.value` from event:
```typescript
<Input
  value={value}
  onChange={({ detail }) => setValue(detail.value)}  // Not e.target.value
/>
```

### Issue: Form validation not working
**Solution:** Set `errorText` on FormField:
```typescript
<FormField
  label="Name"
  errorText={error}  // Shows error message
>
  <Input value={value} onChange={onChange} />
</FormField>
```

## Next Steps

1. Start with Phase 1: Setup & Infrastructure
2. Install CloudScape dependencies
3. Create theme configuration
4. Update main.tsx
5. Create layout wrappers
6. Begin Phase 2: Core Components migration

## References

- Migration Spec: `.kiro/specs/cloudscape-migration/requirements.md`
- Implementation Plan: `.kiro/specs/cloudscape-migration/implementation-plan.md`
- Task Breakdown: `.kiro/specs/cloudscape-migration/tasks.md`
- CloudScape Docs: https://cloudscape.design/
