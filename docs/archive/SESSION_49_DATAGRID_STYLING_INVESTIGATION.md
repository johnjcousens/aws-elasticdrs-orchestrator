# Session 49: DataGrid Header Styling Investigation

**Date**: November 22, 2024, 8:00 PM - 8:30 PM EST  
**Status**: ❌ **UNRESOLVED** - Requires deeper investigation  
**Commit**: `0b7ef5d` - Styling attempts committed but issue persists

## Problem Summary

**Issue**: Material-UI DataGrid column headers render with white-on-white text in production, making them invisible/unreadable.

**Affected Component**: `frontend/src/components/DataGridWrapper.tsx`

**User Impact**: Cannot read column headers on Recovery Plans, Executions, and Protection Groups pages.

## Investigation Timeline

### Attempt 1: Theme References (FAILED)
- Changed `backgroundColor: theme.palette.secondary.main` to use AWS Squid Ink color
- Changed `color: theme.palette.primary.contrastText` to white
- **Result**: Still white-on-white after deployment

### Attempt 2: Hardcoded Hex Colors (FAILED)
- Replaced theme references with hardcoded values:
  - `backgroundColor: '#232F3E'` (AWS Squid Ink)
  - `color: '#FFFFFF'` (White)
- **Result**: Still white-on-white after deployment and cache clear

### Attempt 3: !important Flags (FAILED)
- Added CSS `!important` flags to force override:
  - `backgroundColor: '#232F3E !important'`
  - `color: '#FFFFFF !important'`
- **Result**: Still white-on-white after deployment

### Attempt 4: slotProps API (FAILED)
- Used Material-UI DataGrid's official `slotProps` API:
```typescript
slotProps={{
  columnHeaders: {
    style: {
      backgroundColor: '#232F3E',
      color: '#FFFFFF',
    },
  },
}}
```
- **Result**: Still white-on-white after deployment

### Attempt 5: Combined Approach (FAILED)
- Used both `slotProps` AND `sx` with `!important` flags
- **Result**: Still white-on-white after deployment

## Key Findings

1. **Multiple styling approaches ALL fail** - Suggests root cause is NOT simple CSS specificity
2. **User confirmed white-on-white in incognito** - Rules out browser cache issues
3. **Global CSS has light mode styles** - `frontend/src/index.css` sets white background for light color scheme
4. **No obvious CSS conflicts** - Only one `MuiDataGrid-columnHeaders` style in codebase
5. **Browser DevTools needed** - Cannot determine actual applied CSS without inspecting in browser

## Current Code State

**File**: `frontend/src/components/DataGridWrapper.tsx`

**Current Styling** (Lines ~115-130):
```typescript
<DataGrid
  rows={rows}
  columns={responsiveColumns}
  // ... other props
  slotProps={{
    columnHeaders: {
      style: {
        backgroundColor: '#232F3E',
        color: '#FFFFFF',
      },
    },
  }}
  sx={{
    '& .MuiDataGrid-columnHeaders': {
      backgroundColor: '#232F3E !important',
      color: '#FFFFFF !important',
      fontWeight: 600,
      fontSize: isMobile ? '0.75rem' : '0.875rem',
    },
    // ... other sx styles
  }}
/>
```

## Hypothesis for Root Cause

Based on all attempts failing, likely causes:

### 1. **Material-UI Theme Provider Override** (MOST LIKELY)
- The theme provider in `App.tsx` or `main.tsx` may be setting global overrides
- Need to inspect actual theme configuration
- Check if theme has DataGrid-specific overrides

### 2. **DataGrid Version Compatibility**
- Check `package.json` for `@mui/x-data-grid` version
- Verify compatibility with current Material-UI core version
- API changes between versions might affect styling

### 3. **Global Theme Mode**
- `frontend/src/index.css` has `color-scheme: light dark`
- May be forcing light mode which overrides our styles
- Need to check if Material-UI respects or ignores this

### 4. **CSS-in-JS Rendering Order**
- Material-UI uses Emotion for CSS-in-JS
- Style insertion order might cause our styles to be overridden
- May need to use `StyledEngineProvider` with `injectFirst`

### 5. **Browser-Specific Issue**
- Could be browser rendering the DataGrid differently
- Would need to test in multiple browsers
- DevTools inspection required to see actual computed styles

## Recommended Next Steps

### Phase 1: Investigate Theme Provider (HIGH PRIORITY)

1. **Check theme configuration**:
   ```bash
   # Inspect these files:
   frontend/src/theme/index.ts
   frontend/src/App.tsx
   frontend/src/main.tsx
   ```

2. **Look for DataGrid overrides** in theme:
   ```typescript
   components: {
     MuiDataGrid: {
       styleOverrides: {
         columnHeaders: { ... }
       }
     }
   }
   ```

3. **Check theme mode** (light/dark):
   ```typescript
   const theme = createTheme({
     palette: {
       mode: 'light', // or 'dark'
     }
   });
   ```

### Phase 2: Browser DevTools Inspection (CRITICAL)

**User needs to provide**:
1. Right-click column header → Inspect Element
2. Find `<div class="MuiDataGrid-columnHeaders">` in HTML tree
3. Check Styles tab for:
   - What `background-color` is actually applied?
   - What `color` is actually applied?
   - Which CSS rules are being used?
   - Are our rules present but crossed out (overridden)?

### Phase 3: Alternative Solutions

If theme investigation doesn't resolve:

**Option A: Custom StyledDataGrid Component**
```typescript
import { styled } from '@mui/material/styles';
import { DataGrid } from '@mui/x-data-grid';

const StyledDataGrid = styled(DataGrid)(({ theme }) => ({
  '& .MuiDataGrid-columnHeaders': {
    backgroundColor: '#232F3E !important',
    color: '#FFFFFF !important',
  },
}));
```

**Option B: Global CSS Override**
```css
/* In a global CSS file */
.MuiDataGrid-columnHeaders {
  background-color: #232F3E !important;
  color: #FFFFFF !important;
}
```

**Option C: Custom Theme Component Override**
```typescript
const theme = createTheme({
  components: {
    MuiDataGrid: {
      styleOverrides: {
        columnHeaders: {
          backgroundColor: '#232F3E',
          color: '#FFFFFF',
        },
      },
    },
  },
});
```

**Option D: Replace DataGrid with Custom Table**
- Use Material-UI Table components instead
- Full control over styling
- More work but guaranteed to work

## Files Modified This Session

1. ✅ `frontend/src/components/DataGridWrapper.tsx` - Multiple styling attempts
2. ✅ `frontend/src/pages/RecoveryPlansPage.tsx` - Status column text shortened
3. ✅ Deployed to production (still fails)
4. ✅ Git commit `0b7ef5d` with investigation notes

## Testing Checklist for Next Session

- [ ] Inspect theme provider configuration
- [ ] Check theme.components.MuiDataGrid overrides
- [ ] Get browser DevTools CSS inspection from user
- [ ] Test with StyledDataGrid component approach
- [ ] Test with global CSS override
- [ ] Test with custom theme component override
- [ ] Check Material-UI and DataGrid versions
- [ ] Test in different browsers (Chrome, Firefox, Safari)
- [ ] Consider replacing with custom Table component if all else fails

## Related Documentation

- Material-UI DataGrid Styling: https://mui.com/x/react-data-grid/style/
- Material-UI Theme: https://mui.com/material-ui/customization/theming/
- Theme Component Overrides: https://mui.com/material-ui/customization/theme-components/
- Session 48 Investigation: `docs/SESSION_48_UI_DISPLAY_BUGS.md`

## Session Outcome

❌ **Issue NOT resolved** - All styling approaches failed to change column header appearance.

✅ **Changes committed** - Code is in git with detailed notes for next investigation.

🔍 **Next session priority** - Theme provider investigation + browser DevTools inspection required.

---

**Next Session Recommendation**: Start by inspecting theme configuration in `frontend/src/theme/` directory and getting actual CSS from browser DevTools.
