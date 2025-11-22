# Session 45 Part 2 - Testing Guide

## Deployment Status ✅

**Deployment**: Complete  
**CloudFront Invalidation**: Completed at 2:23 PM EST  
**URL**: https://d1wfyuosowt0hl.cloudfront.net  
**Fix Deployed**: onChange parameter correction (commit 27bcd61)  
**Bundle**: index-Cwvbj2U5.js

---

## Quick Test Steps

### 1. Pre-Test Setup (30 seconds)
```bash
# Clear your browser cache completely
# Chrome/Edge: Cmd+Shift+Delete (Mac) or Ctrl+Shift+Delete (Windows)
# Select "Cached images and files" → Clear data

# Or use Incognito/Private browsing
```

### 2. Load Application (1 minute)
1. Navigate to: **https://d1wfyuosowt0hl.cloudfront.net**
2. **Hard refresh**: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
3. Open Browser Console: `F12` → **Console** tab
4. Verify new bundle loaded:
   - Check Network tab
   - Look for: `index-Cwvbj2U5.js` (new bundle)
   - Old bundle was: `index-B8ZYuCUy.js`

### 3. Authentication (1 minute)
1. Sign in with your credentials
2. Navigate to **Recovery Plans** page

### 4. Critical Test - Protection Group Dropdown (2 minutes)

#### Test Procedure:
1. Click **"Create New Recovery Plan"** button
2. In dialog: Name the plan (e.g., "Test Plan Session 45")
3. **Expand Wave 1** (click accordion)
4. Locate **"Protection Groups"** dropdown
5. Click dropdown to open options
6. **Click on ANY Protection Group option**

#### Expected Results ✅:
```
✅ Console shows: 🔵 onChange fired! { newValue: [ProtectionGroup] }
✅ Blue chip appears in the dropdown
✅ Chip contains the Protection Group name
✅ Server dropdown below populates with servers
✅ Chip persists (doesn't disappear)
✅ Can add multiple Protection Groups (chips stack)
```

#### Failure Signs ❌:
```
❌ No console.log message appears
❌ Chip appears but immediately disappears
❌ Server dropdown stays empty
❌ Clicking option does nothing
❌ Any JavaScript errors in console
```

### 5. Additional Verification (1 minute)

#### Test Server Dropdown:
1. After Protection Group selection works
2. Verify Server dropdown populates
3. Try selecting a server
4. Check if server chip appears

#### Test Multiple Protection Groups:
1. Click Protection Group dropdown again
2. Select a second Protection Group
3. Verify both chips display
4. Check servers from both groups appear

---

## Detailed Testing Scenarios

### Scenario A: First-Time User Flow
```
1. Open app in fresh browser/incognito
2. Sign in
3. Create new recovery plan
4. Expand Wave 1
5. Select Protection Group
6. Expected: Immediate chip display with console log
```

### Scenario B: Existing Plan Modification
```
1. Open existing recovery plan
2. Navigate to Wave configuration
3. Modify Protection Group selections
4. Expected: Changes persist correctly
```

### Scenario C: Multi-Wave Testing
```
1. Create plan with multiple waves
2. Test Protection Group selection in Wave 1
3. Test Protection Group selection in Wave 2
4. Expected: Both waves work independently
```

---

## Console Log Reference

### Success Pattern:
```javascript
🔵 onChange fired! {
  newValue: [
    { id: 'pg-12345', name: 'Production-PG', ... }
  ]
}
```

### What to Look For:
- **Blue circle emoji** (🔵) - Indicates our debug log
- **"onChange fired!"** - Confirms handler executed
- **newValue array** - Contains selected Protection Group(s)
- **No errors** - Clean console

### Common Error Patterns:
```javascript
// If you see these, fix didn't work:
TypeError: Cannot read property 'map' of undefined
Warning: MUI: A component is changing an uncontrolled input
Uncaught Error in onChange handler
```

---

## Network Tab Verification

### Check Loaded Bundle:
1. Open DevTools → **Network** tab
2. Filter: `JS`
3. Look for: `index-Cwvbj2U5.js`
4. Click file → **Preview** tab
5. Search for: `🔵 onChange fired!`
6. Should find the debug log in the code

### Verify Asset Loading:
```
✅ index-Cwvbj2U5.js (new bundle)
✅ All assets load from CloudFront
✅ No 404 errors
✅ No 403 forbidden errors
```

---

## Troubleshooting Guide

### Issue: No Debug Logs Appear

**Possible Causes:**
1. Browser cache not cleared
2. Old bundle still loaded
3. Console filters hiding logs

**Solutions:**
```bash
# 1. Force reload
Cmd+Shift+R (Mac) / Ctrl+Shift+R (Windows)

# 2. Clear cache completely
DevTools → Application → Storage → Clear site data

# 3. Check console filters
Console → Show all levels → Clear filters

# 4. Use incognito/private browsing
```

### Issue: Chips Disappear Immediately

**Possible Causes:**
1. State management issue
2. Re-render clearing selection
3. Parent component issue

**Diagnostic Steps:**
```javascript
// Check if onChange fired:
Look for: 🔵 onChange fired!

// If yes but chips disappear:
- Check for additional console errors
- Look for re-render messages
- Verify parent component state
```

### Issue: Server Dropdown Not Populating

**Possible Causes:**
1. Protection Group has no servers
2. API call failing
3. Filtering logic issue

**Diagnostic Steps:**
```javascript
// Check API calls in Network tab:
Filter: XHR/Fetch
Look for: /protection-groups/[id]/servers

// Check console for API errors:
Look for: "Failed to fetch servers"
```

---

## Success Criteria Checklist

### Must Pass (Critical):
- [ ] Protection Group dropdown opens
- [ ] Clicking option produces console log (🔵)
- [ ] Chip appears after selection
- [ ] Chip persists (doesn't disappear)
- [ ] Server dropdown populates
- [ ] No JavaScript errors in console

### Should Pass (Important):
- [ ] Multiple Protection Groups can be selected
- [ ] Chips can be removed (X button works)
- [ ] Server selection works correctly
- [ ] Changes persist on save
- [ ] Dialog can be closed and reopened

### Nice to Have:
- [ ] Visual feedback smooth
- [ ] Dropdown search works
- [ ] Loading states display correctly
- [ ] Error messages clear

---

## Reporting Results

### If Testing Succeeds ✅:
Report back:
```
✅ Protection Group dropdown WORKING
✅ Console logs appearing: [paste log]
✅ Chips displaying correctly
✅ Server dropdown populating
✅ No errors detected

Next Steps: MVP feature complete, all critical bugs resolved
```

### If Testing Fails ❌:
Report back:
```
❌ Issue detected: [describe problem]
❌ Console errors: [paste errors]
❌ Steps to reproduce: [exact steps]
❌ Bundle loaded: [bundle filename from Network tab]

Include:
- Screenshot of issue
- Full console log output
- Network tab showing loaded bundle
```

---

## Automated Test Option

If manual testing is inconvenient, we can run:

```bash
# Run automated Playwright test
cd tests/playwright
npm test test-protection-group-dropdown.spec.ts

# Or run comprehensive test suite
npm test protection-group-selection.spec.ts
```

**Note**: Automated tests provide technical validation but don't replace manual UX verification.

---

## Timeline

- **Deployment**: 2:23 PM EST
- **Invalidation Complete**: 2:24 PM EST
- **Ready for Testing**: 2:25 PM EST (NOW)

**Current Time**: 2:46 PM EST - Deployment has been live for 23 minutes

---

## Contact Information

If you encounter issues:
1. Capture full console log
2. Take screenshot of issue
3. Note exact steps to reproduce
4. Check bundle version in Network tab

We can then:
- Analyze specific errors
- Run additional diagnostics
- Implement additional fixes if needed
- Re-deploy corrected version

---

## Summary

**Deployment Status**: ✅ Complete and Live  
**Testing Window**: Now available  
**Expected Duration**: 5-10 minutes for full validation  
**Critical Test**: Protection Group dropdown onClick behavior  
**Success Indicator**: 🔵 Blue circle logs in console  

**You are now clear to begin testing. Good luck! 🚀**
