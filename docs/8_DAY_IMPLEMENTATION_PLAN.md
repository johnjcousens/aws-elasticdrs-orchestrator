# 8-Day Implementation Plan - AWS DRS Orchestration Demo
**Created**: November 12, 2025 10:09 AM EST
**Demo Date**: Wednesday, November 20, 2025
**Status**: 🟢 ON TRACK - Day 1 of 8

---

## 🎯 Project Goal
Deliver working 2-tier disaster recovery demo showing:
- 6 Windows servers in us-east-1
- Wave 1: Database tier (2 servers, sequential)
- Wave 2: Web tier (4 servers, parallel, depends on Wave 1)
- Total recovery time: ~25 minutes
- Full UI → Lambda → Step Functions → DRS orchestration

---

## 📊 Current Infrastructure Status (As of Nov 12, 2025)

### ✅ CloudFormation Stacks (5 deployed)
```
drs-orchestration-test-FrontendStack    CREATE_COMPLETE
drs-orchestration-test-ApiStack         UPDATE_COMPLETE (updated Nov 11)
drs-orchestration-test-LambdaStack      UPDATE_COMPLETE (updated Nov 11)
drs-orchestration-test-DatabaseStack    CREATE_COMPLETE
drs-orchestration-test (master)         UPDATE_COMPLETE
```

### ✅ S3 Buckets (2)
```
aws-drs-orchestration                   Lambda deployment artifacts
drs-orchestration-fe-438465159935-test  Frontend hosting
```

### ✅ Lambda Functions (3)
```
drs-orchestration-api-handler-test      Python 3.12  9KB   (Updated TODAY 2:31 AM!)
drs-orchestration-orchestration-test    Python 3.12  5KB   Step Functions handler
drs-orchestration-frontend-builder-test Python 3.12  396KB Build/deploy frontend
```

### ✅ DynamoDB Tables (3)
```
drs-orchestration-protection-groups-test
drs-orchestration-recovery-plans-test
drs-orchestration-execution-history-test
```

### ✅ DRS Source Servers (6 Windows servers - ALL READY!)
```
Server ID                  Hostname            Replication Status
s-3c1730a9e0771ea14       EC2AMAZ-4IMB9PN     CONTINUOUS ✓
s-3d75cdc0d9a28a725       EC2AMAZ-RLP9U5V     CONTINUOUS ✓
s-3afa164776f93ce4f       EC2AMAZ-H0JBE4J     CONTINUOUS ✓
s-3c63bb8be30d7d071       EC2AMAZ-8B7IRHJ     CONTINUOUS ✓
s-3578f52ef3bdd58b4       EC2AMAZ-FQTJG64     CONTINUOUS ✓
s-3b9401c1cd270a7a8       EC2AMAZ-3B0B3UD     CONTINUOUS ✓
```

**Infrastructure Health**: 🟢 EXCELLENT - All systems operational, servers fully replicated

---

## 🚨 Critical Bugs Blocking Demo (4 Total)

### BUG #1: API Endpoint Mismatch ⚠️ SHOWSTOPPER
**Severity**: CRITICAL - Breaks execute button
**File**: `frontend/src/services/api.ts` (line 209)
**Issue**: Frontend sends POST to `/recovery-plans/{id}/execute` but backend expects POST to `/executions`
**Impact**: 404 error when clicking "Execute Recovery Plan"
**Fix Time**: 30 minutes
**Status**: 🔴 NOT STARTED

### BUG #2: Data Model Mismatch ⚠️ CRITICAL
**Severity**: CRITICAL - Breaks create plan
**File**: `frontend/src/components/RecoveryPlanDialog.tsx` (line 109)
**Issue**: Frontend sends `{name, description, protectionGroupId, waves}` but backend requires `{PlanName, Description, AccountId, Region, Owner, RPO, RTO, Waves}`
**Impact**: 400 error "Missing required field" when creating Recovery Plan
**Fix Time**: 45 minutes
**Status**: 🔴 NOT STARTED

### BUG #3: Wave Structure Mismatch ⚠️ CRITICAL
**Severity**: CRITICAL - Breaks wave validation
**File**: New file needed `frontend/src/services/waveTransform.ts`
**Issue**: Frontend Wave format doesn't match backend validation expectations
**Impact**: Wave validation rejects frontend data
**Fix Time**: 45 minutes
**Status**: 🔴 NOT STARTED

### BUG #4: ServerSelector Mock Data ⚠️ BLOCKER
**Severity**: HIGH - Prevents real server selection
**File**: `frontend/src/components/ServerSelector.tsx` (line 41)
**Issue**: Hardcoded mock servers instead of calling DRS API
**Impact**: Can't assign real DRS servers to waves
**Fix Time**: 30 minutes
**Status**: 🔴 NOT STARTED

**Total Bug Fix Time Estimate**: 2.5 hours

---

## 📅 8-Day Implementation Schedule

### **Days 1-2: Tuesday-Wednesday Nov 12-13** 🔴 CRITICAL PATH
**Focus**: Fix all 4 bugs, achieve end-to-end working demo

#### Tuesday Nov 12 (TODAY) - Morning Session (4 hours)
- [x] ✅ AWS infrastructure analysis complete (10:09 AM)
- [ ] 🟡 IN PROGRESS: Create implementation tracking document
- [ ] Fix BUG #1: API endpoint alignment (30 min)
  - Modify `frontend/src/services/api.ts`
  - Update executeRecoveryPlan method
  - Add unit test
- [ ] Fix BUG #2: Data model transformation (45 min)
  - Modify `frontend/src/components/RecoveryPlanDialog.tsx`
  - Add required fields: AccountId, Region, Owner, RPO, RTO
  - Update CreateRecoveryPlanRequest interface
- [ ] Test: Create Protection Group with real DRS servers (30 min)

**Deliverable**: Protection Groups working with real servers

#### Tuesday Nov 12 - Afternoon Session (4 hours)
- [ ] Fix BUG #3: Wave structure transformation (45 min)
  - Create `frontend/src/services/waveTransform.ts`
  - Implement transformWaveToBackend()
  - Update wave creation logic
- [ ] Fix BUG #4: ServerSelector API integration (30 min)
  - Replace mock data with apiClient.listDRSSourceServers()
  - Update error handling
  - Test with all 6 real servers
- [ ] Test: Create Recovery Plan with 2 waves (30 min)
- [ ] Git commit: "fix: Align frontend↔backend API contracts"
- [ ] Push to origin main

**Deliverable**: Recovery Plans created with real server assignments

#### Wednesday Nov 13 (4 hours)
- [ ] Test complete flow: Create PG → Create Plan → Execute → Monitor
- [ ] Fix any execution errors discovered
- [ ] Verify DynamoDB records are correct
- [ ] Test wave dependency logic (Wave 2 waits for Wave 1)
- [ ] Git commit: "feat: End-to-end recovery execution working"
- [ ] Push to origin main

**Deliverable**: Working demo from UI → Lambda → Step Functions → DRS

---

### **Days 3-4: Thursday-Friday Nov 14-15** 🟡 DEMO CONTENT
**Focus**: Build production-ready 2-tier recovery plan

#### Thursday Nov 14 (4 hours)
- [ ] Create Protection Group: "Production-Application"
  - Server assignment:
    * DB Tier: EC2AMAZ-4IMB9PN, EC2AMAZ-RLP9U5V
    * Web Tier: EC2AMAZ-H0JBE4J, EC2AMAZ-8B7IRHJ, EC2AMAZ-FQTJG64, EC2AMAZ-3B0B3UD
- [ ] Build Recovery Plan: "Production-2Tier-DR"
  - Wave 1: Database (2 servers, sequential execution)
  - Wave 2: Web (4 servers, parallel execution, depends on Wave 1)
- [ ] Configure wave settings:
  - Health checks enabled
  - Rollback on failure
  - Timeout: 30 minutes per wave
- [ ] Test wave dependency chain
- [ ] Git commit: "feat: 2-tier production recovery plan"
- [ ] Push to origin main

**Deliverable**: Complete 2-tier recovery plan configured

#### Friday Nov 15 (4 hours)
- [ ] Execute 3 test recovery drills
  - Drill 1: Full execution, monitor timing
  - Drill 2: Verify parallel wave execution
  - Drill 3: Test failure recovery (optional)
- [ ] Document execution times:
  - Wave 1 (DB) completion time
  - Wave 2 (Web) completion time
  - Total recovery time
- [ ] Capture screenshots:
  - Protection Group page
  - Recovery Plan configuration
  - Execution in progress
  - Completed execution
- [ ] Git commit: "test: Validated 2-tier recovery timing"
- [ ] Push to origin main

**Deliverable**: Proven 25-minute recovery plan with documented timings

---

### **Days 5-6: Monday-Tuesday Nov 18-19** 🟢 POLISH & AUTOMATION
**Focus**: Automated cleanup and error handling

#### Monday Nov 18 (4 hours)
- [ ] Create cleanup Lambda function:
  ```python
  def terminate_drill_instances(event):
      # Terminate all recovered instances
      # Tag source servers as "available"
      # Update DynamoDB execution status
      # Send SNS notification
      # Log cleanup metrics to CloudWatch
  ```
- [ ] Add CloudWatch Event rule:
  - Trigger: ExecutionStateChange → COMPLETED
  - Action: Invoke cleanup Lambda after 2 hours
- [ ] Update CloudFormation template
- [ ] Deploy stack updates
- [ ] Test cleanup on 2 drill executions
- [ ] Git commit: "feat: Automated drill instance cleanup"
- [ ] Push to origin main

**Deliverable**: Self-cleaning drill executions

#### Tuesday Nov 19 (4 hours)
- [ ] Test failure scenarios:
  - Server launch failure (simulate 1 server timeout)
  - Health check timeout (simulate unhealthy instance)
  - Wave dependency failure (simulate Wave 1 failure)
- [ ] Verify error messages are clear in UI
- [ ] Add retry logic for transient failures
- [ ] Update error handling in Lambda
- [ ] Test rollback functionality
- [ ] Git commit: "fix: Enhanced error handling and retries"
- [ ] Push to origin main

**Deliverable**: Reliable error handling and user feedback

---

### **Days 7-8: Wednesday Nov 20** 🎬 DEMO DAY
**Focus**: Perfect execution + backup plans

#### Morning (2 hours) - Dress Rehearsal
- [ ] Run final dress rehearsal drill
- [ ] Time each step precisely
- [ ] Verify all UI elements load correctly
- [ ] Pre-create Protection Group & Recovery Plan
- [ ] Prepare 3 demo scenarios:
  1. Happy path (normal execution)
  2. Failure + recovery (show error handling)
  3. Execution monitoring (live status updates)

#### Demo Script (15 minutes)

**1. Introduction (2 min)**
- "AWS DRS Orchestration automates VMware SRM-like disaster recovery"
- Show 6 source servers in DRS console
- Explain 2-tier architecture (Database → Web)

**2. Protection Group Demo (3 min)**
- Navigate to Protection Groups page
- Show automatic server discovery
- Create PG "Demo-Production-App" with 6 servers
- Explain assignment tracking (prevents conflicts)

**3. Recovery Plan Demo (5 min)**
- Navigate to Recovery Plans page
- Click "Create Recovery Plan"
- Configure Wave 1: Database tier
  - 2 servers (EC2AMAZ-4IMB9PN, EC2AMAZ-RLP9U5V)
  - Sequential execution
  - Priority: Critical
- Configure Wave 2: Web tier
  - 4 servers (remaining)
  - Parallel execution
  - Depends on Wave 1 completion
- Show wave dependency graph
- Save plan

**4. Execution Demo (5 min)**
- Click "Execute Recovery Plan"
- Select "DRILL" mode (safe, doesn't affect source)
- Confirm execution
- Watch live progress:
  * Wave 1: 2 DB servers launching sequentially...
  * Wave 1: Complete ✓ (10 minutes)
  * Wave 2: 4 Web servers launching in parallel...
  * Wave 2: Complete ✓ (15 minutes)
- Show recovered instances in EC2 console
- Show execution history in UI

**5. Q&A (time permitting)**
- Explain automatic cleanup after 2 hours
- Discuss integration with existing workflows
- Show error handling and rollback capabilities

#### Backup Plans
- [ ] Pre-recorded video if live demo fails
- [ ] Screenshots of successful execution
- [ ] Prepared talking points for technical questions
- [ ] Backup AWS account (if primary has issues)

**Deliverable**: Impressive, flawless demo 🎯

---

## 🎯 Success Criteria

### Minimum Viable Demo (Must Have)
- [x] 6 DRS source servers in CONTINUOUS replication
- [ ] Protection Group created with all 6 servers
- [ ] Recovery Plan with 2 waves configured
- [ ] Wave dependency working (Wave 2 waits for Wave 1)
- [ ] Execute button triggers Step Functions
- [ ] UI shows live execution progress
- [ ] Recovered instances visible in EC2

### Enhanced Demo (Nice to Have)
- [ ] Automated cleanup after 2 hours
- [ ] Error handling with clear user messages
- [ ] Rollback on failure
- [ ] Execution history tracking
- [ ] Performance metrics (recovery time)
- [ ] Health checks post-launch

### Excellence Demo (Stretch Goals)
- [ ] Playwright automated E2E tests
- [ ] CloudWatch dashboard showing metrics
- [ ] SNS notifications on completion
- [ ] PDF export of execution report
- [ ] Multi-region failover demo

---

## 📊 Daily Progress Tracking

### Day 1: Tuesday Nov 12, 2025
**Status**: 🟡 IN PROGRESS
**Started**: 10:09 AM EST
**Completed Tasks**:
- [x] AWS infrastructure analysis (CloudFormation, S3, Lambda, DynamoDB, DRS)
- [x] Documented 6 Windows servers (all in CONTINUOUS replication)
- [x] Created 8-day implementation plan

**In Progress**:
- [ ] BUG #1 fix (API endpoint alignment)

**Blockers**: None
**Next Steps**: Complete all 4 bug fixes by end of day

---

## 🔧 Technical Reference

### API Endpoints
```
GET  /protection-groups
POST /protection-groups
GET  /protection-groups/{id}
PUT  /protection-groups/{id}
DELETE /protection-groups/{id}

GET  /recovery-plans
POST /recovery-plans
GET  /recovery-plans/{id}
PUT  /recovery-plans/{id}
DELETE /recovery-plans/{id}

POST /executions                    ← CORRECT endpoint for execute
GET  /executions
GET  /executions/{id}
POST /executions/{id}/cancel

GET  /drs/source-servers?region={region}
```

### DRS Server IDs (for reference)
```
Database Tier:
- s-3c1730a9e0771ea14 (EC2AMAZ-4IMB9PN)
- s-3d75cdc0d9a28a725 (EC2AMAZ-RLP9U5V)

Web Tier:
- s-3afa164776f93ce4f (EC2AMAZ-H0JBE4J)
- s-3c63bb8be30d7d071 (EC2AMAZ-8B7IRHJ)
- s-3578f52ef3bdd58b4 (EC2AMAZ-FQTJG64)
- s-3b9401c1cd270a7a8 (EC2AMAZ-3B0B3UD)
```

### Wave Configuration Template
```typescript
{
  waveNumber: 0,
  name: "Database Tier",
  description: "Critical database servers",
  serverIds: ["s-3c1730a9e0771ea14", "s-3d75cdc0d9a28a725"],
  executionType: "sequential",
  dependsOnWaves: []
}

{
  waveNumber: 1,
  name: "Web Tier",
  description: "Web front-end servers",
  serverIds: ["s-3afa164776f93ce4f", "s-3c63bb8be30d7d071", 
              "s-3578f52ef3bdd58b4", "s-3b9401c1cd270a7a8"],
  executionType: "parallel",
  dependsOnWaves: [0]
}
```

---

## 📝 Commit Message Template
```
<type>: <subject>

<body>

<footer>
```

**Types**: feat, fix, docs, test, refactor, chore
**Example**:
```
fix: Align frontend and backend API contracts

- Updated executeRecoveryPlan endpoint from /recovery-plans/{id}/execute to /executions
- Added required fields to CreateRecoveryPlanRequest (AccountId, Region, Owner, RPO, RTO)
- Implemented waveTransform.ts to convert frontend Wave format to backend format
- Integrated real DRS API in ServerSelector component

Fixes: BUG #1, BUG #2, BUG #3, BUG #4
Testing: Manual test with 6 source servers successful
```

---

## 🎯 Risk Mitigation

### High Risk Areas
1. **Step Functions Execution**: Untested with real DRS servers
   - Mitigation: Test in dev environment first
   - Backup: Manual DRS recovery if automation fails

2. **DRS API Rate Limits**: Launching 6 servers simultaneously
   - Mitigation: Parallel wave limited to 4 servers
   - Backup: Sequential execution fallback

3. **Network Connectivity**: VPC/subnet configuration
   - Mitigation: Pre-verify network settings
   - Backup: Use default VPC settings

4. **Demo Day Issues**: Live demo always risky
   - Mitigation: Pre-recorded video backup
   - Backup: Screenshots of successful test runs

### Rollback Plan
If critical bug cannot be fixed:
1. Use mock data for server selection
2. Skip execution step, show screenshots
3. Focus on UI/UX demonstration only

---

**Last Updated**: November 12, 2025 10:09 AM EST
**Next Update**: After BUG #1 fix completion
**Owner**: jocousen
**Repository**: git@ssh.code.aws.dev:personal_projects/alias_j/jocousen/AWS-DRS-Orchestration.git
