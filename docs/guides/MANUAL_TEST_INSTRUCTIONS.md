# Manual Test Instructions for Hardware Display Issue

## Quick Test Steps

1. **Open Browser**: Navigate to http://localhost:3000
2. **Login**: Use `***REMOVED***` / `***REMOVED***`
3. **Navigate**: Go to Protection Groups page
4. **Create**: Click "Create Protection Group" button
5. **Select Region**: Choose "us-west-2" from region dropdown
6. **Wait**: Wait 3-5 seconds for server discovery API call
7. **Check Console**: Open browser DevTools (F12) and check Console tab
8. **Look for**:
   - 🔧 ServerListItem logs showing hardware data
   - 🎨 ServerListItem rendering logs
   - Yellow DEBUG banners in the UI
   - Red-bordered test components

## What to Look For

### In Browser Console:
```
🔧 ServerListItem EC2AMAZ-4IMB9PN: {hasHardware: true, hardware: {...}}
🎨 ServerListItem EC2AMAZ-4IMB9PN rendering: {willShowHardware: true, ...}
```

### In UI:
- **Test Component** (red border): Should show "✅ Hardware condition is TRUE"
- **Original Component**: Should show "CPU: 2 cores | RAM: 7.9 GiB | Disk: 50.0 GiB"
- **DEBUG Banner** (yellow): Should show hardware values

## Expected vs Actual

### Expected:
- Both test and original components show hardware data
- Console logs show hardware object with totalCores, ramGiB, totalDiskGiB
- UI displays: "CPU: 2 cores | RAM: 7.9 GiB | Disk: 50.0 GiB"

### If Issue Persists:
- Test component works but original doesn't → Component logic issue
- Neither works → Data flow issue
- Console shows hardware but UI doesn't → Rendering issue

## Debugging Commands

If you need to check the API directly:
```bash
# Test API endpoint
./test-api-flow.sh

# Test axios flow
node test-axios-flow.js
```

## Current Status

- ✅ API returns correct hardware data (confirmed)
- ✅ Lambda extracts hardware correctly (confirmed)  
- ✅ Frontend API client receives data (confirmed)
- ❓ React component rendering (testing now)

The issue is likely in the React component lifecycle or rendering logic.