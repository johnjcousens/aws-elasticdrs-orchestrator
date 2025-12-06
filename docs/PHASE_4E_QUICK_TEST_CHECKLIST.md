# Phase 4E: Quick Test Checklist

**Frontend**: https://d1wfyuosowt0hl.cloudfront.net  
**Credentials**: ***REMOVED*** / IiG2b1o+D$

---

## Quick Checklist

### 1. Login ✅
- [ ] Open frontend URL
- [ ] Enter credentials
- [ ] Login successful
- [ ] Dashboard/Protection Groups page loads

### 2. Protection Groups ✅
- [ ] Navigate to Protection Groups
- [ ] See 3 groups (WebServers, AppServers, DatabaseServers)
- [ ] Each group shows 2 servers
- [ ] All servers show CONTINUOUS replication
- [ ] No errors

### 3. Recovery Plans ✅
- [ ] Navigate to Recovery Plans
- [ ] See 1 plan (TEST)
- [ ] Plan shows 3 waves
- [ ] Wave details expandable
- [ ] Execute button visible
- [ ] No errors

### 4. Execute Drill ✅
- [ ] Click Execute on TEST plan
- [ ] Confirm execution (if prompted)
- [ ] Execution starts
- [ ] Execution ID displayed
- [ ] Status: PENDING or POLLING
- [ ] No errors

### 5. Monitor Execution (~15-20 min) ✅
- [ ] Status updates automatically
- [ ] Wave 1 completes
- [ ] Wave 2 completes
- [ ] Wave 3 completes
- [ ] Overall status: COMPLETED
- [ ] No errors

### 6. Verify Completion ✅
- [ ] Final status: COMPLETED
- [ ] All waves: COMPLETED
- [ ] All servers: LAUNCHED
- [ ] Duration: ~15-20 minutes
- [ ] Success indicator shown

### 7. Execution History ✅
- [ ] Navigate to Executions page
- [ ] See execution in history
- [ ] Details accurate
- [ ] Can view execution details

### 8. Browser DevTools ✅
- [ ] Console: No errors
- [ ] Network: API calls successful (200)
- [ ] Network: JWT token in headers
- [ ] Network: Polling requests visible

---

## Expected Results

**Protection Groups**: 3 groups, 6 servers total  
**Recovery Plan**: 1 plan, 3 waves  
**Execution Duration**: ~15-20 minutes  
**Success Rate**: 100% (all servers launched)  
**Errors**: 0

---

## Test Data IDs

**Recovery Plan**: 1d86a60c-028e-4b67-893e-11775dc0525e  
**WebServers PG**: d25cb93b-0537-4979-8937-03c711d3116a  
**AppServers PG**: ba395002-ea25-44a6-a468-0bd6fb7b6565  
**DatabaseServers PG**: 0c00fff2-1066-4aef-886a-16d2151791a4

---

## Screenshots to Capture

1. Login page
2. Protection Groups page
3. Recovery Plans page (with expanded waves)
4. Execution start confirmation
5. Execution monitoring (POLLING status)
6. Wave 1 completed
7. Wave 2 completed
8. Final COMPLETED status
9. Execution history page
10. Browser DevTools console (no errors)

---

## If Something Fails

**Login fails**: Check credentials, clear browser cache  
**Data doesn't load**: Check Network tab, verify JWT token  
**Execution doesn't start**: Check Lambda logs, verify DRS servers  
**Status doesn't update**: Check ExecutionPoller Lambda, EventBridge rule

---

**Estimated Time**: 30-45 minutes  
**Critical**: Take screenshots at each step!
