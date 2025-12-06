# CloudScape Migration - Kickoff Guide

## Status: READY TO START

**Created**: December 6, 2025  
**Estimated Duration**: 22-34 hours  
**Current Phase**: Pre-Migration (Specification Complete)

---

## Quick Start

### Prerequisites Checklist

Before starting the migration, ensure:

- [ ] DRS validation is complete (or migration approved to proceed in parallel)
- [ ] All current Material-UI functionality is documented
- [ ] Development environment is set up (Node.js 18+, npm)
- [ ] Git branch created for migration work
- [ ] Team has reviewed migration plan and approved timeline

### Step 1: Read Documentation (30 minutes)

Review these documents in order:

1. **[requirements.md](requirements.md)** - Understand scope and goals
2. **[implementation-plan.md](implementation-plan.md)** - Review detailed phases
3. **[tasks.md](tasks.md)** - See specific task breakdown
4. **[cloudscape-migration.md](../../steering/cloudscape-migration.md)** - Learn migration patterns
5. **[cloudscape-best-practices.md](../../steering/cloudscape-best-practices.md)** - Understand best practices

### Step 2: Set Up Environment (1 hour)

```bash
# 1. Create migration branch
git checkout -b feature/cloudscape-migration
git push -u origin feature/cloudscape-migration

# 2. Install CloudScape dependencies
cd frontend
npm install @cloudscape-design/components@latest \
  @cloudscape-design/global-styles@latest \
  @cloudscape-design/design-tokens@latest \
  @cloudscape-design/collection-hooks@latest \
  @cloudscape-design/board-components@latest

# 3. Verify installation
npm list @cloudscape-design/components

# 4. Commit dependency changes
git add package.json package-lock.json
git commit -m "chore: Install CloudScape dependencies"
git push
```

### Step 3: Remove Material-UI (30 minutes)

```bash
cd frontend

# Remove Material-UI packages
npm uninstall @mui/material @mui/icons-material @mui/x-data-grid \
  @emotion/react @emotion/styled

# Commit changes
git add package.json package-lock.json
git commit -m "chore: Remove Material-UI dependencies"
git push
```

**Note**: Build will fail at this point - this is expected!

### Step 4: Create Theme Configuration (1 hour)

Create `frontend/src/styles/cloudscape-theme.ts`:

```typescript
import { applyMode, Mode } from '@cloudscape-design/global-styles';

export const initializeTheme = () => {
  // Apply AWS branded theme
  applyMode(Mode.Light);
};

export const themeConfig = {
  // Custom theme tokens if needed
};
```

Update `frontend/src/main.tsx`:

```typescript
import '@cloudscape-design/global-styles/index.css';
import { initializeTheme } from './styles/cloudscape-theme';

initializeTheme();

// Remove Material-UI ThemeProvider
// <ThemeProvider theme={theme}>
//   <App />
// </ThemeProvider>

// Replace with:
<App />
```

Commit changes:

```bash
git add frontend/src/styles/cloudscape-theme.ts frontend/src/main.tsx
git commit -m "feat: Add CloudScape theme configuration"
git push
```

### Step 5: Start Component Migration (Ongoing)

Follow the task list in [tasks.md](tasks.md), starting with Phase 2:

1. **StatusBadge.tsx** (30 min)
2. **LoadingSpinner.tsx** (30 min)
3. **ConfirmDialog.tsx** (1 hour)
4. Continue through all components...

For each component:
1. Read original component
2. Apply migration patterns from steering docs
3. Test component in isolation
4. Commit changes
5. Move to next component

---

## Migration Workflow

### Daily Workflow

**Morning** (30 minutes)
1. Review yesterday's progress
2. Check for any issues or blockers
3. Plan today's components to migrate
4. Review relevant migration patterns

**During Migration** (6-8 hours)
1. Pick next component from task list
2. Read component and understand functionality
3. Apply CloudScape migration patterns
4. Test component thoroughly
5. Commit and push changes
6. Update task list with completion status

**End of Day** (15 minutes)
1. Document any issues encountered
2. Update progress tracking
3. Commit all work
4. Plan next day's tasks

### Testing Workflow

After each component migration:

1. **Visual Test**: Does it look correct?
2. **Functional Test**: Do all interactions work?
3. **Console Test**: No errors or warnings?
4. **TypeScript Test**: No type errors?
5. **Accessibility Test**: Keyboard navigation works?

### Git Workflow

```bash
# For each component
git add frontend/src/components/ComponentName.tsx
git commit -m "feat(cloudscape): Migrate ComponentName to CloudScape"
git push

# For each phase completion
git add .
git commit -m "feat(cloudscape): Complete Phase X - [Phase Name]"
git tag -a "cloudscape-phase-X" -m "CloudScape Migration Phase X Complete"
git push --tags
```

---

## Progress Tracking

### Phase 1: Setup & Infrastructure

- [ ] Task 1.1: Install CloudScape dependencies (15 min)
- [ ] Task 1.2: Remove Material-UI dependencies (15 min)
- [ ] Task 1.3: Create CloudScape theme configuration (30 min)
- [ ] Task 1.4: Update main.tsx (30 min)
- [ ] Task 1.5: Create AppLayout wrapper (1 hour)
- [ ] Task 1.6: Create ContentLayout wrapper (30 min)

**Estimated**: 2-4 hours  
**Actual**: ___ hours  
**Status**: Not Started

### Phase 2: Core Shared Components

- [ ] Task 2.1: StatusBadge.tsx (30 min)
- [ ] Task 2.2: DateTimeDisplay.tsx - Verify (15 min)
- [ ] Task 2.3: LoadingSpinner.tsx (30 min)
- [ ] Task 2.4: ConfirmDialog.tsx (1 hour)
- [ ] Task 2.5: ProtectionGroupDialog.tsx (2 hours)
- [ ] Task 2.6: RecoveryPlanDialog.tsx (2 hours)
- [ ] Task 2.7: RegionSelector.tsx (1 hour)
- [ ] Task 2.8: ServerSelector.tsx (2 hours)
- [ ] Task 2.9: TagFilterEditor.tsx (1 hour)
- [ ] Task 2.10: WaveProgress.tsx (1.5 hours)
- [ ] Task 2.11: InfoPanel.tsx (30 min)
- [ ] Task 2.12: EmptyState.tsx (30 min)

**Estimated**: 8-12 hours  
**Actual**: ___ hours  
**Status**: Not Started

### Phase 3: Page Components

- [ ] Task 3.1: LoginPage.tsx (1.5 hours)
- [ ] Task 3.2: Dashboard.tsx (1.5 hours)
- [ ] Task 3.3: ProtectionGroupsPage.tsx (3 hours)
- [ ] Task 3.4: RecoveryPlansPage.tsx (3 hours)
- [ ] Task 3.5: ExecutionsPage.tsx (3 hours)

**Estimated**: 8-12 hours  
**Actual**: ___ hours  
**Status**: Not Started

### Phase 4: Testing & Refinement

- [ ] Task 4.1: Visual regression testing (2 hours)
- [ ] Task 4.2: Functionality testing (2 hours)
- [ ] Task 4.3: Accessibility testing (1 hour)
- [ ] Task 4.4: Performance testing (1 hour)

**Estimated**: 4-6 hours  
**Actual**: ___ hours  
**Status**: Not Started

---

## Common Issues & Solutions

### Issue: Build fails after removing Material-UI

**Expected**: This is normal during migration.

**Solution**: Continue with CloudScape component migration. Build will succeed once all Material-UI imports are replaced.

### Issue: Component looks different after migration

**Solution**: 
1. Check CloudScape component documentation
2. Review spacing with SpaceBetween
3. Verify design tokens are applied
4. Compare with AWS console for reference

### Issue: Event handlers not working

**Solution**: CloudScape uses `detail` property in events:

```typescript
// Wrong
onChange={(e) => setValue(e.target.value)}

// Correct
onChange={({ detail }) => setValue(detail.value)}
```

### Issue: Table not sorting/filtering

**Solution**: Use `@cloudscape-design/collection-hooks`:

```typescript
import { useCollection } from '@cloudscape-design/collection-hooks';

const { items, collectionProps } = useCollection(allItems, {
  filtering: {},
  pagination: { pageSize: 25 },
  sorting: {},
});
```

### Issue: Modal not closing

**Solution**: Check `onDismiss` prop updates state:

```typescript
<Modal
  visible={visible}
  onDismiss={() => setVisible(false)}  // Must update state
/>
```

---

## Resources

### Documentation
- CloudScape Components: https://cloudscape.design/components/
- CloudScape Patterns: https://cloudscape.design/patterns/
- Design Tokens: https://cloudscape.design/foundation/visual-foundation/design-tokens/
- Collection Hooks: https://cloudscape.design/get-started/dev-guides/collection-hooks/

### Internal Documentation
- [Implementation Plan](implementation-plan.md)
- [Task Breakdown](tasks.md)
- [Migration Guide](../../steering/cloudscape-migration.md)
- [Best Practices](../../steering/cloudscape-best-practices.md)
- [Component Reference](../../steering/cloudscape-component-reference.md)

### Support
- CloudScape GitHub: https://github.com/cloudscape-design/components
- CloudScape Discussions: https://github.com/cloudscape-design/components/discussions

---

## Success Criteria

Migration is complete when:

- [ ] Zero Material-UI dependencies in package.json
- [ ] All 23 components migrated to CloudScape
- [ ] All functionality preserved (CRUD, search, filter, sort)
- [ ] WCAG 2.1 AA compliance maintained
- [ ] Bundle size <3MB
- [ ] No console errors or warnings
- [ ] All TypeScript types correct
- [ ] Build succeeds without errors
- [ ] All tests pass
- [ ] Visual regression tests pass
- [ ] Accessibility tests pass
- [ ] Performance benchmarks met

---

## Next Steps

1. **Review this kickoff guide** - Understand the process
2. **Complete Prerequisites** - Ensure environment is ready
3. **Start Phase 1** - Install dependencies and set up theme
4. **Begin Component Migration** - Follow task list systematically
5. **Test Continuously** - Validate each component as you go
6. **Document Issues** - Track any problems encountered
7. **Complete Testing** - Comprehensive validation at the end

---

## Timeline

**Week 1** (16 hours)
- Phase 1: Setup & Infrastructure (4 hours)
- Phase 2: Core Components (12 hours)

**Week 2** (16 hours)
- Phase 3: Pages (12 hours)
- Phase 4: Testing & Refinement (4 hours)

**Total**: 22-34 hours over 2 weeks

---

## Contact

For questions or issues during migration:
- Review steering documents first
- Check CloudScape documentation
- Consult with team lead
- Document blockers for resolution

---

**Ready to start? Begin with Step 1: Read Documentation!**
