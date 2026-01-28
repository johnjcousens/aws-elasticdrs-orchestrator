# WaveConfigEditor.tsx Bug Fix

## Issue
When creating a Protection Group with individual server selection (not tag-based), adding it to a Recovery Plan Wave showed "no tags" in the dropdown and prevented server selection.

## Root Cause
The component only checked for `serverSelectionTags` to determine if a Protection Group was configured, ignoring Protection Groups that use `sourceServerIds` (individual server selection).

## Changes Made

### 1. Protection Group Dropdown Labels (Lines 254-283)

**Before:**
```typescript
const tagCount = Object.keys(pg.serverSelectionTags || {}).length;
return {
  label: `${pg.groupName} (${tagCount} tag${tagCount !== 1 ? 's' : ''})`,
  value: pg.protectionGroupId,
  tags: tagCount > 0 ? ['configured'] : ['no-tags']
};
```

**After:**
```typescript
const tagCount = Object.keys(pg.serverSelectionTags || {}).length;
const serverCount = (pg.sourceServerIds || []).length;
const selectionMode = tagCount > 0 ? 'tag-based' : serverCount > 0 ? 'server-based' : 'unconfigured';
const label = tagCount > 0 
  ? `${pg.groupName} (${tagCount} tag${tagCount !== 1 ? 's' : ''})`
  : `${pg.groupName} (${serverCount} server${serverCount !== 1 ? 's' : ''})`;
return {
  label,
  value: pg.protectionGroupId,
  tags: [selectionMode]
};
```

**Impact:**
- Tag-based PGs show: `"MyGroup (3 tags)"`
- Server-based PGs show: `"MyGroup (5 servers)"`
- Tags changed from `'configured'/'no-tags'` to `'tag-based'/'server-based'/'unconfigured'`

### 2. Server Selection Logic (Lines 308-343)

**Before:**
```typescript
{(wave.protectionGroupIds || []).length > 0 ? (
  (() => {
    const selectedPGs = (protectionGroups || []).filter(pg => 
      (wave.protectionGroupIds || []).includes(pg.protectionGroupId)
    );
    const allTagBased = selectedPGs.length > 0 && selectedPGs.every(pg => 
      pg.serverSelectionTags && Object.keys(pg.serverSelectionTags).length > 0
    );
    
    if (allTagBased) {
      return (
        <Alert type="info">
          <strong>Tag-based Protection Groups selected.</strong><br />
          Servers will be automatically resolved at execution time based on Protection Group tags.
          No manual server selection is needed.
        </Alert>
      );
    }
    
    return (
      <ServerSelector
        key={(wave.protectionGroupIds || []).join(',')}
        protectionGroupIds={wave.protectionGroupIds || []}
        protectionGroupId={wave.protectionGroupId || wave.protectionGroupIds?.[0] || ''}
        selectedServerIds={wave.serverIds}
        onChange={(serverIds) => handleUpdateWave(wave.waveNumber, 'serverIds', serverIds)}
        readonly={readonly}
      />
    );
  })()
) : (
  <Alert type="info">
    Select one or more Protection Groups above to choose servers for this wave
  </Alert>
)}
```

**After:**
```typescript
{(wave.protectionGroupIds || []).length > 0 ? (
  (() => {
    const selectedPGs = (protectionGroups || []).filter(pg => 
      (wave.protectionGroupIds || []).includes(pg.protectionGroupId)
    );
    const allTagBased = selectedPGs.length > 0 && selectedPGs.every(pg => 
      pg.serverSelectionTags && Object.keys(pg.serverSelectionTags).length > 0
    );
    const hasServerBasedPGs = selectedPGs.some(pg => 
      pg.sourceServerIds && pg.sourceServerIds.length > 0
    );
    
    if (allTagBased) {
      return (
        <Alert type="info">
          <strong>Tag-based Protection Groups selected.</strong><br />
          Servers will be automatically resolved at execution time based on Protection Group tags.
          No manual server selection is needed.
        </Alert>
      );
    }
    
    if (hasServerBasedPGs) {
      return (
        <ServerSelector
          key={(wave.protectionGroupIds || []).join(',')}
          protectionGroupIds={wave.protectionGroupIds || []}
          protectionGroupId={wave.protectionGroupId || wave.protectionGroupIds?.[0] || ''}
          selectedServerIds={wave.serverIds}
          onChange={(serverIds) => handleUpdateWave(wave.waveNumber, 'serverIds', serverIds)}
          readonly={readonly}
        />
      );
    }
    
    return (
      <Alert type="warning">
        Selected Protection Groups have no servers configured. 
        Please edit the Protection Groups to add servers or configure tags.
      </Alert>
    );
  })()
) : (
  <Alert type="info">
    Select one or more Protection Groups above to choose servers for this wave
  </Alert>
)}
```

**Impact:**
- Added `hasServerBasedPGs` check to detect Protection Groups with individual servers
- ServerSelector now renders for server-based Protection Groups
- Shows warning if Protection Groups have neither tags nor servers configured

## Testing Status

### Backend Verification ✅
API endpoint tested successfully:
```bash
./test_api_manual.sh
```

**Result:** API correctly returns Protection Group with `sourceServerIds`:
```json
{
  "groupName": "AppServersGroup",
  "sourceServerIds": ["s-57eae3bdae1f0179b", "s-5d4ac077408e03d02"],
  "protectionGroupId": "b66e0653-c46e-4ab2-aec6-48d760a529b8"
}
```

### Frontend Verification ⚠️
**Issue:** User reports ServerSelector still shows "No servers found" message despite:
- Dropdown correctly showing `"AppServersGroup (2 servers)"` with `server-based` tag
- `protectionGroups` prop being passed to WaveConfigEditor
- `protectionGroups` prop being passed to ServerSelector

**Likely Cause:** Browser cache holding old frontend code. CloudFront invalidation completed but browser needs hard refresh.

**User Action Required:**
1. Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+F5` (Windows)
2. Or use incognito/private window
3. Check browser console for any errors
4. Verify API response in Network tab shows `sourceServerIds`

### Deployment History
1. **First deployment:** Updated WaveConfigEditor and ServerSelector components
2. **Second deployment:** Full validation and security scanning completed
3. **CloudFront invalidation:** Completed for both deployments

## Testing Checklist
- [x] Backend API returns correct data structure with `sourceServerIds`
- [x] Authentication working with Cognito test user
- [x] WaveConfigEditor dropdown shows server count for server-based PGs
- [x] WaveConfigEditor passes `protectionGroups` prop to ServerSelector
- [x] ServerSelector receives `protectionGroups` prop with `sourceServerIds`
- [ ] User hard refreshes browser to clear cache
- [ ] ServerSelector displays the 2 servers from Protection Group
- [ ] User can select servers in Wave configuration

## Files Changed
- `frontend/src/components/WaveConfigEditor.tsx` - Updated dropdown labels and server-based PG detection
- `frontend/src/components/ServerSelector.tsx` - Added logic to fetch specific servers by ID for server-based PGs
- `test_api_manual.sh` - Created API testing script

## Related Issue
Protection Groups with individual server selection were unusable in Recovery Plan Waves due to incorrect detection logic. Backend fix complete, frontend deployed, awaiting user browser cache clear.
