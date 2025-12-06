# Phase 4E: Manual UI Test Guide

**Date**: December 6, 2024  
**Status**: Ready to Execute  
**Goal**: Validate end-to-end workflow through CloudFront frontend

---

## Prerequisites

✅ **Phase 4D Complete**: First successful DRS drill execution validated via API  
✅ **Frontend Deployed**: CloudFront distribution operational  
✅ **Test Data Available**: 3 Protection Groups, 1 Recovery Plan with 6 servers  
✅ **Test Credentials**: testuser@example.com / IiG2b1o+D$

---

## Test Environment

**Frontend URL**: https://d1wfyuosowt0hl.cloudfront.net  
**API Endpoint**: https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test  
**Region**: us-east-1  
**Account**: 777788889999  
**Environment**: test

---

## Test Objectives

1. ✅ Validate user authentication through Cognito
2. ✅ Verify Protection Groups page displays correctly
3. ✅ Verify Recovery Plans page displays correctly
4. ✅ Test drill execution through UI
5. ✅ Verify real-time execution monitoring
6. ✅ Validate execution history display
7. ✅ Test CloudScape UI components

---

## Test Procedure

### Step 1: Login and Authentication

**Action**:
1. Open browser to https://d1wfyuosowt0hl.cloudfront.net
2. Enter credentials:
   - Username: `testuser@example.com`
   - Password: `IiG2b1o+D$`
3. Click "Sign In"

**Expected Result**:
- ✅ Login successful
- ✅ Redirected to Dashboard or Protection Groups page
- ✅ Navigation menu visible
- ✅ User email displayed in header

**Validation Points**:
- [ ] Login form displays correctly
- [ ] Credentials accepted
- [ ] JWT token obtained (check browser DevTools Network tab)
- [ ] Navigation menu shows all pages
- [ ] No console errors

---

### Step 2: Protection Groups Page

**Action**:
1. Navigate to "Protection Groups" page
2. Verify existing Protection Groups display
3. Check server details and status

**Expected Result**:
- ✅ 3 Protection Groups displayed:
  - WebServers (2 servers)
  - AppServers (2 servers)
  - DatabaseServers (2 servers)
- ✅ Server details visible (hostname, Server ID, replication status)
- ✅ All servers show "CONTINUOUS" replication
- ✅ CloudScape Table component renders correctly

**Validation Points**:
- [ ] Table displays 3 Protection Groups
- [ ] Server count accurate (2 servers each)
- [ ] Server details expandable/visible
- [ ] Replication status shows "CONTINUOUS"
- [ ] Edit/Delete buttons visible
- [ ] No loading errors
- [ ] No console errors

**Screenshot**: Capture Protection Groups page

---

### Step 3: Recovery Plans Page

**Action**:
1. Navigate to "Recovery Plans" page
2. Verify existing Recovery Plan displays
3. Check wave configuration

**Expected Result**:
- ✅ 1 Recovery Plan displayed: "TEST"
- ✅ 3 waves visible:
  - Wave 1: WebTier (2 servers)
  - Wave 2: AppTier (2 servers)
  - Wave 3: DatabaseTier (2 servers)
- ✅ Wave dependencies shown correctly
- ✅ CloudScape Table and expandable rows work

**Validation Points**:
- [ ] Table displays 1 Recovery Plan
- [ ] Plan name: "TEST"
- [ ] Wave count: 3
- [ ] Wave details expandable
- [ ] Server assignments visible
- [ ] Execute button visible
- [ ] No loading errors
- [ ] No console errors

**Screenshot**: Capture Recovery Plans page with expanded waves

---

### Step 4: Execute Drill from UI

**Action**:
1. On Recovery Plans page, locate "TEST" plan
2. Click "Execute" or "Execute Drill" button
3. Confirm execution in dialog (if prompted)
4. Observe execution start

**Expected Result**:
- ✅ Execution confirmation dialog appears
- ✅ Execution starts successfully
- ✅ Redirected to Execution Details page or Executions page
- ✅ Execution ID displayed
- ✅ Initial status: "PENDING" or "POLLING"

**Validation Points**:
- [ ] Execute button clickable
- [ ] Confirmation dialog displays (if implemented)
- [ ] Execution triggers successfully
- [ ] Execution ID generated
- [ ] Status updates visible
- [ ] No errors in UI
- [ ] No console errors

**Screenshot**: Capture execution confirmation and initial status

---

### Step 5: Monitor Execution Progress

**Action**:
1. Stay on Execution Details page
2. Observe real-time status updates
3. Watch wave progress
4. Monitor for completion

**Expected Result**:
- ✅ Status updates automatically (polling every 5-10 seconds)
- ✅ Wave progress visible:
  - Wave 1: PENDING → POLLING → LAUNCHING → COMPLETED
  - Wave 2: PENDING → POLLING → LAUNCHING → COMPLETED
  - Wave 3: PENDING → POLLING → LAUNCHING → COMPLETED
- ✅ Overall status: PENDING → POLLING → COMPLETED
- ✅ Execution completes in ~15-20 minutes
- ✅ CloudScape StatusIndicator components show correct states

**Validation Points**:
- [ ] Status updates automatically (no manual refresh needed)
- [ ] Wave progress timeline visible (CloudScape Steps component)
- [ ] Current wave highlighted
- [ ] Completed waves show checkmarks
- [ ] Server launch status visible
- [ ] DRS job IDs displayed
- [ ] Timestamps shown
- [ ] No UI freezing
- [ ] No console errors

**Screenshots**: 
- Capture at POLLING status
- Capture at Wave 1 COMPLETED
- Capture at Wave 2 COMPLETED
- Capture at final COMPLETED status

**Note**: This will take ~15-20 minutes. You can:
- Keep browser tab open and monitor
- Open browser DevTools Network tab to see API polling
- Check CloudWatch logs in parallel

---

### Step 6: Verify Execution Completion

**Action**:
1. Wait for execution to complete
2. Verify final status
3. Check all wave statuses
4. Review execution details

**Expected Result**:
- ✅ Overall status: "COMPLETED"
- ✅ All 3 waves: "COMPLETED"
- ✅ All 6 servers: "LAUNCHED"
- ✅ Execution duration: ~15-20 minutes
- ✅ No errors displayed
- ✅ Success message or indicator shown

**Validation Points**:
- [ ] Final status: COMPLETED
- [ ] All waves completed
- [ ] All servers launched
- [ ] Duration displayed
- [ ] Success indicator visible (green checkmark, success badge)
- [ ] No error messages
- [ ] CloudWatch logs link works (if implemented)

**Screenshot**: Capture final completed status

---

### Step 7: Execution History

**Action**:
1. Navigate to "Executions" page (if separate from details)
2. Verify execution appears in history
3. Check execution details

**Expected Result**:
- ✅ Execution appears in history table
- ✅ Execution details accurate:
  - Execution ID
  - Plan name: "TEST"
  - Type: "DRILL"
  - Status: "COMPLETED"
  - Start time
  - End time
  - Duration
  - Initiated by: testuser@example.com
- ✅ CloudScape Table with sorting/filtering works

**Validation Points**:
- [ ] Execution visible in history
- [ ] All details accurate
- [ ] Clickable to view details
- [ ] Table sorting works
- [ ] Table filtering works (if implemented)
- [ ] Pagination works (if multiple executions)

**Screenshot**: Capture execution history page

---

### Step 8: Test Additional UI Features

**Action**:
1. Test navigation between pages
2. Test responsive design (resize browser)
3. Test CloudScape components:
   - Tables (sorting, filtering, pagination)
   - Buttons (hover states, disabled states)
   - Status indicators
   - Expandable rows
   - Modals/dialogs
4. Check accessibility (keyboard navigation)

**Expected Result**:
- ✅ Navigation works smoothly
- ✅ UI responsive on different screen sizes
- ✅ CloudScape components function correctly
- ✅ No visual glitches
- ✅ Keyboard navigation works

**Validation Points**:
- [ ] Navigation menu works
- [ ] Back button works
- [ ] UI scales on mobile/tablet sizes
- [ ] Tables sortable
- [ ] Buttons have hover effects
- [ ] Status indicators color-coded correctly
- [ ] Expandable rows work
- [ ] Tab key navigation works
- [ ] No accessibility warnings in DevTools

---

## Browser DevTools Checks

### Console Tab
**Check for**:
- [ ] No JavaScript errors
- [ ] No React warnings
- [ ] No API errors
- [ ] No authentication errors

### Network Tab
**Check for**:
- [ ] API calls successful (200 responses)
- [ ] JWT token in Authorization headers
- [ ] Polling requests every 5-10 seconds during execution
- [ ] No 401/403 errors
- [ ] No CORS errors

### Application Tab
**Check for**:
- [ ] JWT token stored correctly (localStorage or sessionStorage)
- [ ] User session persists on page refresh
- [ ] No sensitive data in localStorage

---

## Test Data Reference

### Protection Groups
1. **WebServers** (d25cb93b-0537-4979-8937-03c711d3116a)
   - s-3c1730a9e0771ea14 (EC2AMAZ-4IMB9PN)
   - s-3d75cdc0d9a28a725 (EC2AMAZ-RLP9U5V)

2. **AppServers** (ba395002-ea25-44a6-a468-0bd6fb7b6565)
   - s-3afa164776f93ce4f (EC2AMAZ-H0JBE4J)
   - s-3c63bb8be30d7d071 (EC2AMAZ-8B7IRHJ)

3. **DatabaseServers** (0c00fff2-1066-4aef-886a-16d2151791a4)
   - s-3578f52ef3bdd58b4 (EC2AMAZ-FQTJG64)
   - s-3b9401c1cd270a7a8 (EC2AMAZ-3B0B3UD)

### Recovery Plan
- **Name**: TEST
- **ID**: 1d86a60c-028e-4b67-893e-11775dc0525e
- **Waves**: 3 (WebTier → AppTier → DatabaseTier)

### Previous Execution (from Phase 4D)
- **Execution ID**: d44956e0-e776-418a-84c5-24d1e98a4862
- **Status**: COMPLETED
- **Duration**: 16m 57s

---

## Success Criteria

### Must Pass
- [ ] Login successful
- [ ] Protection Groups display correctly (3 groups)
- [ ] Recovery Plans display correctly (1 plan)
- [ ] Drill execution triggers successfully
- [ ] Real-time status updates work
- [ ] Execution completes successfully
- [ ] All waves complete
- [ ] All servers launch
- [ ] Execution history displays correctly
- [ ] No critical errors in console

### Should Pass
- [ ] UI responsive on mobile/tablet
- [ ] CloudScape components render correctly
- [ ] Navigation smooth and intuitive
- [ ] Loading states display correctly
- [ ] Error handling graceful (if errors occur)
- [ ] Accessibility features work

### Nice to Have
- [ ] Animations smooth
- [ ] Tooltips helpful
- [ ] Help text clear
- [ ] Performance good (no lag)

---

## Troubleshooting

### Issue: Login Fails
**Check**:
- Credentials correct (testuser@example.com / IiG2b1o+D$)
- Cognito User Pool accessible
- Network connectivity
- Browser console for errors

**Fix**:
- Verify credentials in AWS Cognito console
- Check API Gateway CORS configuration
- Clear browser cache/cookies

### Issue: Protection Groups Don't Load
**Check**:
- API endpoint accessible
- JWT token valid
- Network tab for API errors
- CloudWatch logs for Lambda errors

**Fix**:
- Refresh page to get new JWT token
- Check API Gateway authorizer configuration
- Verify DynamoDB table has data

### Issue: Execution Doesn't Start
**Check**:
- Execute button clickable
- API call successful (Network tab)
- Lambda function logs
- DynamoDB execution record created

**Fix**:
- Check Lambda function permissions
- Verify Recovery Plan exists
- Check DRS source servers available

### Issue: Status Doesn't Update
**Check**:
- Polling requests in Network tab
- ExecutionPoller Lambda running
- DynamoDB execution record updating

**Fix**:
- Check EventBridge rule enabled
- Verify ExecutionPoller Lambda permissions
- Check StatusIndex GSI working

---

## Test Report Template

```markdown
# Phase 4E: Manual UI Test Results

**Date**: YYYY-MM-DD  
**Tester**: [Your Name]  
**Browser**: [Chrome/Firefox/Safari] [Version]  
**Environment**: TEST (us-east-1)

## Test Summary
- Total Tests: 8
- Passed: X
- Failed: X
- Warnings: X

## Detailed Results

### Step 1: Login ✅/❌
- Status: PASS/FAIL
- Notes: ...
- Screenshot: [filename]

### Step 2: Protection Groups ✅/❌
- Status: PASS/FAIL
- Groups Displayed: X
- Notes: ...
- Screenshot: [filename]

### Step 3: Recovery Plans ✅/❌
- Status: PASS/FAIL
- Plans Displayed: X
- Notes: ...
- Screenshot: [filename]

### Step 4: Execute Drill ✅/❌
- Status: PASS/FAIL
- Execution ID: ...
- Notes: ...
- Screenshot: [filename]

### Step 5: Monitor Progress ✅/❌
- Status: PASS/FAIL
- Duration: X minutes
- Notes: ...
- Screenshots: [filenames]

### Step 6: Verify Completion ✅/❌
- Status: PASS/FAIL
- Final Status: ...
- Notes: ...
- Screenshot: [filename]

### Step 7: Execution History ✅/❌
- Status: PASS/FAIL
- Notes: ...
- Screenshot: [filename]

### Step 8: Additional Features ✅/❌
- Status: PASS/FAIL
- Notes: ...

## Issues Found
1. [Issue description]
2. [Issue description]

## Browser Console Errors
- [List any errors]

## Recommendations
1. [Recommendation]
2. [Recommendation]

## Overall Assessment
- [ ] Ready for production
- [ ] Needs minor fixes
- [ ] Needs major fixes

## Screenshots
- [List all screenshot files]
```

---

## Next Steps After Testing

### If All Tests Pass ✅
1. Document results in `docs/PHASE_4E_MANUAL_UI_TEST_RESULTS.md`
2. Proceed to Phase 4F: Playwright E2E Tests
3. Update PROJECT_STATUS.md

### If Tests Fail ❌
1. Document failures in detail
2. Create bug tickets for each issue
3. Prioritize fixes
4. Re-test after fixes

---

## Quick Start

```bash
# 1. Open frontend
open https://d1wfyuosowt0hl.cloudfront.net

# 2. Login
# Username: testuser@example.com
# Password: IiG2b1o+D$

# 3. Navigate to Recovery Plans

# 4. Execute "TEST" plan

# 5. Monitor execution (~15-20 minutes)

# 6. Verify completion

# 7. Check execution history
```

---

**Status**: Ready to Execute  
**Estimated Duration**: 30-45 minutes (including 15-20 minute execution)  
**Prerequisites**: All met ✅

---

**Note**: Take screenshots at each step for documentation. Use browser DevTools to monitor API calls and console for errors.
