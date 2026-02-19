# Staging Accounts UI Mockup

## Target Account Settings Modal

### Modal Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ Edit Target Account                                          [X] │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Account Information                                               │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ Account ID:        160885257264                           │   │
│ │ Account Name:      DEMO_TARGET                            │   │
│ │ Role ARN:          arn:aws:iam::160885257264:role/...     │   │
│ │ External ID:       drs-orchestration-test-160885257264    │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ Staging Accounts                                                  │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ Staging accounts provide additional replication capacity  │   │
│ │ for extended source servers. Each staging account can     │   │
│ │ replicate up to 300 servers.                              │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ 📊 STAGING_01 (664418995426)                              │   │
│ │    Role: DRSOrchestrationRole-test                        │   │
│ │    Status: ✅ Connected • 150 servers replicating         │   │
│ │    [Test Connection] [Remove]                             │   │
│ ├───────────────────────────────────────────────────────────┤   │
│ │ 📊 STAGING_02 (777777777777)                              │   │
│ │    Role: DRSOrchestrationRole-test                        │   │
│ │    Status: ✅ Connected • 75 servers replicating          │   │
│ │    [Test Connection] [Remove]                             │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ [+ Add Staging Account]                                           │
│                                                                   │
│                                    [Cancel]  [Save Changes]       │
└─────────────────────────────────────────────────────────────────┘
```

## Add Staging Account Modal

Clicking **[+ Add Staging Account]** opens a nested modal:

```
┌─────────────────────────────────────────────────────────────────┐
│ Add Staging Account                                          [X] │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Staging Account Details                                          │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ Account ID *                                              │   │
│ │ ┌─────────────────────────────────────────────────────┐   │   │
│ │ │ 888888888888                                        │   │   │
│ │ └─────────────────────────────────────────────────────┘   │   │
│ │                                                           │   │
│ │ Account Name *                                            │   │
│ │ ┌─────────────────────────────────────────────────────┐   │   │
│ │ │ STAGING_03                                          │   │   │
│ │ └─────────────────────────────────────────────────────┘   │   │
│ │                                                           │   │
│ │ Role ARN *                                                │   │
│ │ ┌─────────────────────────────────────────────────────┐   │   │
│ │ │ arn:aws:iam::888888888888:role/DRSOrchestration... │   │   │
│ │ └─────────────────────────────────────────────────────┘   │   │
│ │                                                           │   │
│ │ External ID *                                             │   │
│ │ ┌─────────────────────────────────────────────────────┐   │   │
│ │ │ drs-orchestration-test-888888888888                 │   │   │
│ │ └─────────────────────────────────────────────────────┘   │   │
│ │                                                           │   │
│ │ Region *                                                  │   │
│ │ ┌─────────────────────────────────────────────────────┐   │   │
│ │ │ us-west-2                                    [▼]    │   │   │
│ │ └─────────────────────────────────────────────────────┘   │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ [Validate Access]                                                 │
│                                                                   │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ ✅ Validation Results                                     │   │
│ │                                                           │   │
│ │ • Role accessible: ✅ Success                            │   │
│ │ • DRS initialized: ✅ Yes                                │   │
│ │ • Current servers: 42 total, 42 replicating             │   │
│ │ • Capacity impact: 267/300 total (225 + 42)             │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│                                    [Cancel]  [Add Account]        │
└─────────────────────────────────────────────────────────────────┘
```

## Main Dashboard View (Combined Capacity - Primary Display)

Dashboard prominently shows **combined aggregate capacity** as the main metric:

```
┌─────────────────────────────────────────────────────────────────┐
│ DRS Capacity - DEMO_TARGET (160885257264)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ ✅ COMBINED CAPACITY OK                                          │
│                                                                   │
│ Replicating Servers (Combined)                                   │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ Operational: 267 / 1,000 servers (27%)                    │   │
│ │ █████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     │   │
│ │ Hard Limit:  267 / 1,200 servers (22%)                    │   │
│ │                                                           │   │
│ │ ✅ OK: 733 available operational slots                    │   │
│ │ 4 accounts × 250 operational limit (300 hard limit)       │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ Recovery Capacity                                                 │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ 267 / 4,000 instances (7%)                                │   │
│ │ ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     │   │
│ │                                                           │   │
│ │ ✅ OK: 3,733 recovery slots available                     │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ Top Contributing Accounts                                         │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ 1. ⚠️ STAGING_01 (664418995426)     150 servers          │   │
│ │    Top Region: us-west-2 (150 servers)                   │   │
│ │    Individual: 150/250 (60%) ✅ OK                        │   │
│ │                                                           │   │
│ │ 2. ✅ STAGING_02 (777777777777)      75 servers          │   │
│ │    Top Region: us-east-1 (50 servers)                    │   │
│ │    Individual: 75/250 (30%) ✅ OK                         │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ All Accounts (4 total)                                            │
│ • ✅ STAGING_01 (664418995426): 150/250 (60%) - OK               │
│ • ✅ STAGING_02 (777777777777): 75/250 (30%) - OK                │
│ • ✅ STAGING_03 (888888888888): 36/250 (14%) - OK                │
│ • ✅ Target (160885257264): 6/250 (2%) - OK                      │
│                                                                   │
│ Active Operations                                                 │
│ • Concurrent Jobs: 0/20 (0%) ✅                                  │
│ • Servers in Jobs: 0/500 (0%) ✅                                 │
│                                                                   │
│ ✅ No Warnings                                                    │
│                                                                   │
│ [View Account Details]  [Configure Staging Accounts]              │
└─────────────────────────────────────────────────────────────────┘
```

### Example: Account at CRITICAL Threshold (250 servers)

```
┌─────────────────────────────────────────────────────────────────┐
│ DRS Capacity - DEMO_TARGET (160885257264)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ 🔴 COMBINED CAPACITY CRITICAL                                    │
│                                                                   │
│ Replicating Servers (Combined)                                   │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ Operational: 506 / 500 servers (101%)                     │   │
│ │ ██████████████████████████████████████████████████████    │   │
│ │ Hard Limit:  506 / 600 servers (84%)                      │   │
│ │                                                           │   │
│ │ 🔴 CRITICAL: Exceeding operational capacity               │   │
│ │ -6 operational slots (over limit by 6 servers)            │   │
│ │ 2 accounts × 250 operational limit (300 hard limit)       │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ Recovery Capacity                                                 │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ 506 / 4,000 instances (13%)                               │   │
│ │ ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     │   │
│ │                                                           │   │
│ │ ✅ OK: 3,494 recovery slots available                     │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ Top Contributing Accounts                                         │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ 1. 🚫 STAGING_01 (664418995426)     280 servers          │   │
│ │    Top Region: us-west-2 (280 servers)                   │   │
│ │    Individual: 280/250 (112%) 🚫 HYPER-CRITICAL          │   │
│ │    ⚠️ EXCEEDING SAFE CAPACITY - IMMEDIATE ACTION!        │   │
│ │                                                           │   │
│ │ 2. 🔴 Target (160885257264)         226 servers          │   │
│ │    Top Region: us-west-2 (226 servers)                   │   │
│ │    Individual: 226/250 (90%) 🟠 WARNING                  │   │
│ │    ⚠️ Approaching operational limit                       │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ All Accounts (2 total)                                            │
│ • 🚫 STAGING_01 (664418995426): 280/250 (112%) - HYPER-CRITICAL │
│ • 🟠 Target (160885257264): 226/250 (90%) - WARNING              │
│                                                                   │
│ Active Operations                                                 │
│ • Concurrent Jobs: 0/20 (0%) ✅                                  │
│ • Servers in Jobs: 0/500 (0%) ✅                                 │
│                                                                   │
│ 🚫 CRITICAL WARNINGS (2)                                          │
│ • STAGING_01 at 280/250 (112%) - EXCEEDING SAFE CAPACITY!        │
│   ACTION: Add staging account immediately or remove servers       │
│ • Target at 226/250 (90%) - approaching operational limit         │
│   ACTION: Plan to add staging account                             │
│                                                                   │
│ [View Account Details]  [Configure Staging Accounts]              │
└─────────────────────────────────────────────────────────────────┘
```

### Example: Account at 250 Servers (Operational Limit)

```
┌─────────────────────────────────────────────────────────────────┐
│ DRS Capacity - DEMO_TARGET (160885257264)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ 🔴 COMBINED CAPACITY CRITICAL                                    │
│                                                                   │
│ Replicating Servers (Combined)                                   │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ Operational: 250 / 250 servers (100%)                     │   │
│ │ ██████████████████████████████████████████████████████    │   │
│ │ Hard Limit:  250 / 300 servers (83%)                      │   │
│ │                                                           │   │
│ │ 🔴 CRITICAL: At operational capacity limit                │   │
│ │ 0 operational slots remaining (50 hard limit buffer)      │   │
│ │ 1 account × 250 operational limit (300 hard limit)        │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ Recovery Capacity                                                 │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ 250 / 4,000 instances (6%)                                │   │
│ │ ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     │   │
│ │                                                           │   │
│ │ ✅ OK: 3,750 recovery slots available                     │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ Top Contributing Accounts                                         │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ 1. 🔴 Target (160885257264)         250 servers          │   │
│ │    Top Region: us-west-2 (250 servers)                   │   │
│ │    Individual: 250/250 (100%) 🔴 CRITICAL                │   │
│ │    ⚠️ AT OPERATIONAL LIMIT - ADD STAGING ACCOUNT NOW!    │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ All Accounts (1 total)                                            │
│ • 🔴 Target (160885257264): 250/250 (100%) - CRITICAL            │
│                                                                   │
│ Active Operations                                                 │
│ • Concurrent Jobs: 0/20 (0%) ✅                                  │
│ • Servers in Jobs: 0/500 (0%) ✅                                 │
│                                                                   │
│ 🔴 CRITICAL WARNINGS (1)                                          │
│ • Target at 250/250 (100%) - AT OPERATIONAL LIMIT                │
│   ACTION: Add staging account NOW to continue replication         │
│   50-server safety buffer remaining before hard limit             │
│                                                                   │
│ [View Account Details]  [Configure Staging Accounts]              │
└─────────────────────────────────────────────────────────────────┘
```

### Example with 2 Accounts (Target + 1 Staging)

```
┌─────────────────────────────────────────────────────────────────┐
│ DRS Capacity - DEMO_TARGET (160885257264)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ ✅ COMBINED CAPACITY OK                                          │
│                                                                   │
│ Replicating Servers (Combined)                                   │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ 156 / 600 servers (26%)                                   │   │
│ │ █████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     │   │
│ │                                                           │   │
│ │ ✅ OK: 444 available replication slots                    │   │
│ │ 2 accounts × 300 servers each                             │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ Recovery Capacity                                                 │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ 156 / 4,000 instances (4%)                                │   │
│ │ ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     │   │
│ │                                                           │   │
│ │ ✅ OK: 3,844 recovery slots available                     │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ Top Contributing Accounts                                         │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ 1. 🔴 STAGING_01 (664418995426)     150 servers          │   │
│ │    Top Region: us-west-2 (150 servers)                   │   │
│ │    Individual: 150/300 (50%) ⚠️ WARNING                  │   │
│ │                                                           │   │
│ │ 2. ✅ Target (160885257264)           6 servers          │   │
│ │    Top Region: us-west-2 (6 servers)                     │   │
│ │    Individual: 6/300 (2%) OK                              │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ All Accounts (2 total)                                            │
│ • 🔴 STAGING_01 (664418995426): 150/300 (50%) - WARNING          │
│ • ✅ Target (160885257264): 6/300 (2%) - OK                      │
│                                                                   │
│ Active Operations                                                 │
│ • Concurrent Jobs: 0/20 (0%) ✅                                  │
│ • Servers in Jobs: 0/500 (0%) ✅                                 │
│                                                                   │
│ ⚠️ Active Warnings (1)                                            │
│ • STAGING_01 at 50% - consider adding another staging account    │
│                                                                   │
│ [View Account Details]  [Configure Staging Accounts]              │
└─────────────────────────────────────────────────────────────────┘
```

### Example with High Combined Capacity

```
┌─────────────────────────────────────────────────────────────────┐
│ DRS Capacity - DEMO_TARGET (160885257264)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ 🔴 COMBINED CAPACITY WARNING                                     │
│                                                                   │
│ Replicating Servers (Combined)                                   │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ 1,120 / 1,200 servers (93%)                               │   │
│ │ ███████████████████████████████████████████████████░░░    │   │
│ │                                                           │   │
│ │ 🔴 WARNING: Approaching combined capacity limit           │   │
│ │ 80 available replication slots                            │   │
│ │ 4 accounts × 300 servers each                             │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ Recovery Capacity                                                 │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ 1,120 / 4,000 instances (28%)                             │   │
│ │ ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     │   │
│ │                                                           │   │
│ │ ✅ OK: 2,880 recovery slots available                     │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ Top Contributing Accounts                                         │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ 1. 🚫 STAGING_01 (664418995426)     300 servers          │   │
│ │    Top Region: us-west-2 (300 servers)                   │   │
│ │    Individual: 300/300 (100%) 🚫 CRITICAL                │   │
│ │                                                           │   │
│ │ 2. 🔴 STAGING_02 (777777777777)     290 servers          │   │
│ │    Top Region: us-east-1 (200 servers)                   │   │
│ │    Individual: 290/300 (97%) 🔴 WARNING                  │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ All Accounts (4 total)                                            │
│ • 🚫 STAGING_01 (664418995426): 300/300 (100%) - CRITICAL        │
│ • 🔴 STAGING_02 (777777777777): 290/300 (97%) - WARNING          │
│ • 🔴 STAGING_03 (888888888888): 280/300 (93%) - WARNING          │
│ • 🔴 Target (160885257264): 250/300 (83%) - INFO                 │
│                                                                   │
│ Active Operations                                                 │
│ • Concurrent Jobs: 0/20 (0%) ✅                                  │
│ • Servers in Jobs: 0/500 (0%) ✅                                 │
│                                                                   │
│ 🚫 Active Warnings (4)                                            │
│ • STAGING_01 at 100% - AT HARD LIMIT, cannot add more servers    │
│ • STAGING_02 at 97% - approaching limit                           │
│ • STAGING_03 at 93% - approaching limit                           │
│ • Combined capacity at 93% - add more staging accounts            │
│                                                                   │
│ [View Account Details]  [Configure Staging Accounts]              │
└─────────────────────────────────────────────────────────────────┘
```

### Capacity Status Indicators

**Per-Account Status** (each staging account tracked individually):
- ✅ **OK** (0-200 servers, 0-67%): Normal operation
- ⚠️ **INFO** (200-225 servers, 67-75%): Monitor capacity
- 🟠 **WARNING** (225-250 servers, 75-83%): Plan to add staging account
- 🔴 **CRITICAL** (250-280 servers, 83-93%): At operational limit - add staging account NOW
- 🚫 **HYPER-CRITICAL** (280-300 servers, 93-100%): Exceeding safe capacity - IMMEDIATE ACTION REQUIRED

**Operational Limit**: 250 servers per account (leaves 50-server safety buffer)
**Hard Limit**: 300 servers per account (AWS enforced)

**Combined Status** (aggregate across all accounts):
- Calculated as: `(total_servers / (num_accounts × 250))` for operational capacity
- Shows warning when any individual account exceeds 250 servers
- Tracks total against hard limit: `(total_servers / (num_accounts × 300))`

**Recovery Capacity**:
- Target account can recover up to 4,000 instances
- Shows recovery capacity against target account's 4,000-server limit

### Detailed Capacity View Modal

Clicking **[View Details]** opens expanded view:

```
┌─────────────────────────────────────────────────────────────────┐
│ DRS Capacity Details - DEMO_TARGET (160885257264)            [X] │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Combined Capacity Summary                                         │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ Total Replicating Servers:  267 / 300  (89%)             │   │
│ │ Recovery Capacity:          267 / 4000 (7%)              │   │
│ │ Available Replication Slots: 33 servers                   │   │
│ │ Available Recovery Slots:    3733 servers                 │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ Per-Account Breakdown                                             │
│                                                                   │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ Direct (160885257264) - Target Account                   │   │
│ │ Status: ✅ OK                                             │   │
│ │                                                           │   │
│ │ Replicating: 6/300 (2%)                                   │   │
│ │ ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░     │   │
│ │                                                           │   │
│ │ Regional Breakdown:                                       │   │
│ │ • us-west-2: 6 servers (6 replicating)                   │   │
│ │                                                           │   │
│ │ Available Slots: 294 servers                              │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ STAGING_01 (664418995426) - Staging Account              │   │
│ │ Status: 🔴 WARNING - Approaching limit                   │   │
│ │                                                           │   │
│ │ Replicating: 150/300 (50%)                                │   │
│ │ ██████████████████████████████████████████████████        │   │
│ │                                                           │   │
│ │ Regional Breakdown:                                       │   │
│ │ • us-west-2: 150 servers (150 replicating)               │   │
│ │                                                           │   │
│ │ Available Slots: 150 servers                              │   │
│ │                                                           │   │
│ │ ⚠️ Recommendation: Consider adding another staging        │   │
│ │    account to distribute replication load                 │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ STAGING_02 (777777777777) - Staging Account              │   │
│ │ Status: ⚠️ INFO - Monitor capacity                        │   │
│ │                                                           │   │
│ │ Replicating: 75/300 (25%)                                 │   │
│ │ █████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░        │   │
│ │                                                           │   │
│ │ Regional Breakdown:                                       │   │
│ │ • us-east-1: 50 servers (50 replicating)                 │   │
│ │ • us-west-2: 25 servers (25 replicating)                 │   │
│ │                                                           │   │
│ │ Available Slots: 225 servers                              │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ STAGING_03 (888888888888) - Staging Account              │   │
│ │ Status: ✅ OK                                             │   │
│ │                                                           │   │
│ │ Replicating: 36/300 (12%)                                 │   │
│ │ ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░        │   │
│ │                                                           │   │
│ │ Regional Breakdown:                                       │   │
│ │ • us-west-2: 36 servers (36 replicating)                 │   │
│ │                                                           │   │
│ │ Available Slots: 264 servers                              │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ Capacity Planning                                                 │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ Current Configuration:                                    │   │
│ │ • 1 target account (160885257264)                        │   │
│ │ • 3 staging accounts                                      │   │
│ │ • Maximum replication capacity: 1,200 servers            │   │
│ │   (4 accounts × 300 servers each)                        │   │
│ │                                                           │   │
│ │ Current Usage:                                            │   │
│ │ • 267 servers replicating (22% of max capacity)          │   │
│ │ • 933 available replication slots                         │   │
│ │                                                           │   │
│ │ Recovery Capacity:                                        │   │
│ │ • Target account can recover up to 4,000 instances       │   │
│ │ • Currently protecting 267 servers (7% of recovery cap)  │   │
│ │ • 3,733 available recovery slots                          │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│                                                        [Close]     │
└─────────────────────────────────────────────────────────────────┘
```

## Component Structure (React/TypeScript)

### TargetAccountSettingsModal.tsx
```typescript
interface StagingAccount {
  accountId: string;
  accountName: string;
  roleArn: string;
  externalId: string;
  status?: 'connected' | 'error' | 'validating';
  serverCount?: number;
  replicatingCount?: number;
}

interface TargetAccountForm {
  accountId: string;
  accountName: string;
  roleArn: string;
  externalId: string;
  stagingAccounts: StagingAccount[];
}

export const TargetAccountSettingsModal = ({ account, onSave, onClose }) => {
  const [formData, setFormData] = useState<TargetAccountForm>(account);
  const [showAddStaging, setShowAddStaging] = useState(false);

  const handleAddStagingAccount = (stagingAccount: StagingAccount) => {
    setFormData({
      ...formData,
      stagingAccounts: [...formData.stagingAccounts, stagingAccount]
    });
    setShowAddStaging(false);
  };

  const handleRemoveStagingAccount = (accountId: string) => {
    setFormData({
      ...formData,
      stagingAccounts: formData.stagingAccounts.filter(
        sa => sa.accountId !== accountId
      )
    });
  };

  return (
    <Modal visible={true} onDismiss={onClose} header="Edit Target Account">
      <SpaceBetween size="l">
        {/* Account Information Section */}
        <Container header={<Header>Account Information</Header>}>
          <FormField label="Account ID">
            <Input value={formData.accountId} disabled />
          </FormField>
          <FormField label="Account Name">
            <Input 
              value={formData.accountName}
              onChange={({ detail }) => setFormData({...formData, accountName: detail.value})}
            />
          </FormField>
          {/* ... other fields ... */}
        </Container>

        {/* Staging Accounts Section */}
        <Container 
          header={<Header>Staging Accounts</Header>}
          footer={
            <Button onClick={() => setShowAddStaging(true)}>
              + Add Staging Account
            </Button>
          }
        >
          <Alert type="info">
            Staging accounts provide additional replication capacity for extended 
            source servers. Each staging account can replicate up to 300 servers.
          </Alert>

          <SpaceBetween size="m">
            {formData.stagingAccounts.map(staging => (
              <StagingAccountCard
                key={staging.accountId}
                account={staging}
                onRemove={() => handleRemoveStagingAccount(staging.accountId)}
              />
            ))}
          </SpaceBetween>
        </Container>
      </SpaceBetween>

      {/* Add Staging Account Modal */}
      {showAddStaging && (
        <AddStagingAccountModal
          onAdd={handleAddStagingAccount}
          onClose={() => setShowAddStaging(false)}
        />
      )}
    </Modal>
  );
};
```

### AddStagingAccountModal.tsx
```typescript
export const AddStagingAccountModal = ({ onAdd, onClose }) => {
  const [formData, setFormData] = useState<StagingAccount>({
    accountId: '',
    accountName: '',
    roleArn: '',
    externalId: '',
  });
  const [validationResult, setValidationResult] = useState(null);
  const [validating, setValidating] = useState(false);

  const handleValidate = async () => {
    setValidating(true);
    try {
      const result = await api.validateStagingAccount(formData);
      setValidationResult(result);
    } catch (error) {
      setValidationResult({ error: error.message });
    } finally {
      setValidating(false);
    }
  };

  const handleAdd = () => {
    onAdd({
      ...formData,
      status: 'connected',
      serverCount: validationResult?.currentServers,
      replicatingCount: validationResult?.replicatingServers,
    });
  };

  return (
    <Modal visible={true} onDismiss={onClose} header="Add Staging Account">
      <SpaceBetween size="l">
        <FormField label="Account ID" errorText={errors.accountId}>
          <Input
            value={formData.accountId}
            onChange={({ detail }) => setFormData({...formData, accountId: detail.value})}
            placeholder="888888888888"
          />
        </FormField>

        <FormField label="Account Name">
          <Input
            value={formData.accountName}
            onChange={({ detail }) => setFormData({...formData, accountName: detail.value})}
            placeholder="STAGING_03"
          />
        </FormField>

        <FormField label="Role ARN">
          <Input
            value={formData.roleArn}
            onChange={({ detail }) => setFormData({...formData, roleArn: detail.value})}
            placeholder="arn:aws:iam::888888888888:role/DRSOrchestrationRole-test"
          />
        </FormField>

        <FormField label="External ID">
          <Input
            value={formData.externalId}
            onChange={({ detail }) => setFormData({...formData, externalId: detail.value})}
            placeholder="drs-orchestration-test-888888888888"
          />
        </FormField>

        <Button onClick={handleValidate} loading={validating}>
          Validate Access
        </Button>

        {validationResult && (
          <Alert type={validationResult.valid ? "success" : "error"}>
            <SpaceBetween size="xs">
              <div>✅ Role accessible: {validationResult.roleAccessible ? 'Success' : 'Failed'}</div>
              <div>✅ DRS initialized: {validationResult.drsInitialized ? 'Yes' : 'No'}</div>
              <div>📊 Current servers: {validationResult.currentServers} total, {validationResult.replicatingServers} replicating</div>
              <div>⚠️ Capacity impact: {validationResult.totalAfter}/300 total</div>
            </SpaceBetween>
          </Alert>
        )}
      </SpaceBetween>

      <Box float="right">
        <SpaceBetween direction="horizontal" size="xs">
          <Button onClick={onClose}>Cancel</Button>
          <Button 
            variant="primary" 
            onClick={handleAdd}
            disabled={!validationResult?.valid}
          >
            Add Account
          </Button>
        </SpaceBetween>
      </Box>
    </Modal>
  );
};
```

## User Flow

1. **User clicks "Edit" on target account** → Opens TargetAccountSettingsModal
2. **Sees existing staging accounts** → List with status and server counts
3. **Clicks "+ Add Staging Account"** → Opens AddStagingAccountModal
4. **Fills in staging account details** → Account ID, name, role ARN, External ID
5. **Clicks "Validate Access"** → Backend tests role assumption and queries DRS
6. **Sees validation results** → Shows current servers and capacity impact
7. **Clicks "Add Account"** → Adds to staging accounts list
8. **Clicks "Save Changes"** → Updates DynamoDB Target Accounts table
9. **Capacity display updates** → Shows new breakdown with all staging accounts

## API Endpoints Needed

```typescript
// Validate staging account access
POST /api/accounts/staging-accounts/validate
{
  "accountId": "888888888888",
  "roleArn": "arn:aws:iam::888888888888:role/...",
  "externalId": "drs-orchestration-test-888888888888",
  "region": "us-west-2"
}

// Add staging account to target account
POST /api/accounts/{targetAccountId}/staging-accounts
{
  "accountId": "888888888888",
  "accountName": "STAGING_03",
  "roleArn": "arn:aws:iam::888888888888:role/...",
  "externalId": "drs-orchestration-test-888888888888"
}

// Remove staging account from target account
DELETE /api/accounts/{targetAccountId}/staging-accounts/{stagingAccountId}

// Test staging account connection
POST /api/accounts/{targetAccountId}/staging-accounts/{stagingAccountId}/test
```

## CLI Management (Direct Lambda Invocation)

### Add Staging Account via Lambda

```bash
#!/bin/bash
# add-staging-account.sh

TARGET_ACCOUNT_ID="160885257264"
STAGING_ACCOUNT_ID="664418995426"
STAGING_ACCOUNT_NAME="STAGING_01"
STAGING_ROLE_ARN="arn:aws:iam::664418995426:role/DRSOrchestrationRole-test"
STAGING_EXTERNAL_ID="drs-orchestration-test-664418995426"

aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-dev \
  --payload "{
    \"operation\": \"add_staging_account\",
    \"targetAccountId\": \"${TARGET_ACCOUNT_ID}\",
    \"stagingAccount\": {
      \"accountId\": \"${STAGING_ACCOUNT_ID}\",
      \"accountName\": \"${STAGING_ACCOUNT_NAME}\",
      \"roleArn\": \"${STAGING_ROLE_ARN}\",
      \"externalId\": \"${STAGING_EXTERNAL_ID}\"
    }
  }" \
  response.json

cat response.json | jq .
```

### Remove Staging Account via Lambda

```bash
#!/bin/bash
# remove-staging-account.sh

TARGET_ACCOUNT_ID="160885257264"
STAGING_ACCOUNT_ID="664418995426"

aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-dev \
  --payload "{
    \"operation\": \"remove_staging_account\",
    \"targetAccountId\": \"${TARGET_ACCOUNT_ID}\",
    \"stagingAccountId\": \"${STAGING_ACCOUNT_ID}\"
  }" \
  response.json

cat response.json | jq .
```

### List Staging Accounts via Lambda

```bash
#!/bin/bash
# list-staging-accounts.sh

TARGET_ACCOUNT_ID="160885257264"

aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-dev \
  --payload "{
    \"operation\": \"get_target_account\",
    \"targetAccountId\": \"${TARGET_ACCOUNT_ID}\"
  }" \
  response.json

cat response.json | jq '.stagingAccounts'
```

### Validate Staging Account via Lambda

```bash
#!/bin/bash
# validate-staging-account.sh

STAGING_ACCOUNT_ID="664418995426"
STAGING_ROLE_ARN="arn:aws:iam::664418995426:role/DRSOrchestrationRole-test"
STAGING_EXTERNAL_ID="drs-orchestration-test-664418995426"
REGION="us-west-2"

aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-dev \
  --payload "{
    \"operation\": \"validate_staging_account\",
    \"accountId\": \"${STAGING_ACCOUNT_ID}\",
    \"roleArn\": \"${STAGING_ROLE_ARN}\",
    \"externalId\": \"${STAGING_EXTERNAL_ID}\",
    \"region\": \"${REGION}\"
  }" \
  response.json

cat response.json | jq .
```

### Direct DynamoDB Update (Emergency/Scripting)

```bash
#!/bin/bash
# update-staging-accounts-dynamodb.sh

TARGET_ACCOUNT_ID="160885257264"
TABLE_NAME="aws-drs-orchestration-target-accounts-dev"

# Get current item
aws dynamodb get-item \
  --table-name "${TABLE_NAME}" \
  --key "{\"accountId\": {\"S\": \"${TARGET_ACCOUNT_ID}\"}}" \
  --output json > current.json

# Update with new staging accounts
aws dynamodb update-item \
  --table-name "${TABLE_NAME}" \
  --key "{\"accountId\": {\"S\": \"${TARGET_ACCOUNT_ID}\"}}" \
  --update-expression "SET stagingAccounts = :staging" \
  --expression-attribute-values '{
    ":staging": {
      "L": [
        {
          "M": {
            "accountId": {"S": "664418995426"},
            "accountName": {"S": "STAGING_01"},
            "roleArn": {"S": "arn:aws:iam::664418995426:role/DRSOrchestrationRole-test"},
            "externalId": {"S": "drs-orchestration-test-664418995426"}
          }
        },
        {
          "M": {
            "accountId": {"S": "777777777777"},
            "accountName": {"S": "STAGING_02"},
            "roleArn": {"S": "arn:aws:iam::777777777777:role/DRSOrchestrationRole-test"},
            "externalId": {"S": "drs-orchestration-test-777777777777"}
          }
        }
      ]
    }
  }' \
  --return-values ALL_NEW

echo "✅ Staging accounts updated"
```

### Helper Script: Bulk Add Staging Accounts

```bash
#!/bin/bash
# bulk-add-staging-accounts.sh
# Add multiple staging accounts to a target account

TARGET_ACCOUNT_ID="160885257264"
ENVIRONMENT="test"

# Array of staging accounts
declare -a STAGING_ACCOUNTS=(
  "664418995426:STAGING_01"
  "777777777777:STAGING_02"
  "888888888888:STAGING_03"
)

for staging in "${STAGING_ACCOUNTS[@]}"; do
  IFS=':' read -r ACCOUNT_ID ACCOUNT_NAME <<< "$staging"
  
  ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/DRSOrchestrationRole-${ENVIRONMENT}"
  EXTERNAL_ID="drs-orchestration-${ENVIRONMENT}-${ACCOUNT_ID}"
  
  echo "Adding staging account: ${ACCOUNT_NAME} (${ACCOUNT_ID})"
  
  aws lambda invoke \
    --function-name "aws-drs-orchestration-data-management-handler-${ENVIRONMENT}" \
    --payload "{
      \"operation\": \"add_staging_account\",
      \"targetAccountId\": \"${TARGET_ACCOUNT_ID}\",
      \"stagingAccount\": {
        \"accountId\": \"${ACCOUNT_ID}\",
        \"accountName\": \"${ACCOUNT_NAME}\",
        \"roleArn\": \"${ROLE_ARN}\",
        \"externalId\": \"${EXTERNAL_ID}\"
      }
    }" \
    response.json
  
  if jq -e '.errorMessage' response.json > /dev/null 2>&1; then
    echo "❌ Failed to add ${ACCOUNT_NAME}"
    cat response.json | jq .
  else
    echo "✅ Added ${ACCOUNT_NAME}"
  fi
  
  rm response.json
done

echo ""
echo "Staging accounts configuration complete!"
```

### Verify Capacity After Adding Staging Accounts

```bash
#!/bin/bash
# verify-capacity.sh

TARGET_ACCOUNT_ID="160885257264"

aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-dev \
  --payload "{
    \"operation\": \"get_drs_account_capacity_all_regions\",
    \"queryParams\": {
      \"account_context\": {
        \"accountId\": \"${TARGET_ACCOUNT_ID}\"
      }
    }
  }" \
  response.json

echo "Capacity Breakdown:"
cat response.json | jq '{
  totalServers: .totalSourceServers,
  replicatingServers: .replicatingServers,
  maxReplicating: .maxReplicatingServers,
  status: .status,
  message: .message,
  breakdown: .breakdown
}'
```

## Lambda Handler Updates Required

### data-management-handler/index.py

```python
def handle_add_staging_account(event: Dict) -> Dict:
    """
    Add staging account to target account configuration.
    
    Direct Lambda invocation:
    {
        "operation": "add_staging_account",
        "targetAccountId": "160885257264",
        "stagingAccount": {
            "accountId": "664418995426",
            "accountName": "STAGING_01",
            "roleArn": "arn:aws:iam::664418995426:role/...",
            "externalId": "drs-orchestration-test-664418995426"
        }
    }
    """
    target_account_id = event.get("targetAccountId")
    staging_account = event.get("stagingAccount")
    
    # Validate staging account
    validation = validate_staging_account_access(staging_account)
    if not validation["valid"]:
        return {
            "error": "VALIDATION_FAILED",
            "message": validation["message"]
        }
    
    # Get current target account
    result = target_accounts_table.get_item(
        Key={"accountId": target_account_id}
    )
    
    if "Item" not in result:
        return {
            "error": "TARGET_ACCOUNT_NOT_FOUND",
            "message": f"Target account {target_account_id} not found"
        }
    
    target_account = result["Item"]
    staging_accounts = target_account.get("stagingAccounts", [])
    
    # Check if staging account already exists
    if any(sa["accountId"] == staging_account["accountId"] for sa in staging_accounts):
        return {
            "error": "STAGING_ACCOUNT_EXISTS",
            "message": f"Staging account {staging_account['accountId']} already configured"
        }
    
    # Add staging account
    staging_accounts.append(staging_account)
    
    # Update DynamoDB
    target_accounts_table.update_item(
        Key={"accountId": target_account_id},
        UpdateExpression="SET stagingAccounts = :staging",
        ExpressionAttributeValues={":staging": staging_accounts}
    )
    
    return {
        "success": True,
        "message": f"Added staging account {staging_account['accountName']}",
        "stagingAccounts": staging_accounts
    }


def handle_remove_staging_account(event: Dict) -> Dict:
    """
    Remove staging account from target account configuration.
    
    Direct Lambda invocation:
    {
        "operation": "remove_staging_account",
        "targetAccountId": "160885257264",
        "stagingAccountId": "664418995426"
    }
    """
    target_account_id = event.get("targetAccountId")
    staging_account_id = event.get("stagingAccountId")
    
    # Get current target account
    result = target_accounts_table.get_item(
        Key={"accountId": target_account_id}
    )
    
    if "Item" not in result:
        return {
            "error": "TARGET_ACCOUNT_NOT_FOUND",
            "message": f"Target account {target_account_id} not found"
        }
    
    target_account = result["Item"]
    staging_accounts = target_account.get("stagingAccounts", [])
    
    # Remove staging account
    staging_accounts = [
        sa for sa in staging_accounts 
        if sa["accountId"] != staging_account_id
    ]
    
    # Update DynamoDB
    target_accounts_table.update_item(
        Key={"accountId": target_account_id},
        UpdateExpression="SET stagingAccounts = :staging",
        ExpressionAttributeValues={":staging": staging_accounts}
    )
    
    return {
        "success": True,
        "message": f"Removed staging account {staging_account_id}",
        "stagingAccounts": staging_accounts
    }
```

### query-handler/index.py

```python
def get_drs_account_capacity_all_regions_enhanced(
    account_context: Optional[Dict] = None
) -> Dict:
    """
    Enhanced capacity calculation including staging accounts.
    
    Returns combined capacity with per-account breakdown and warnings.
    
    Response structure:
    {
        "combined": {
            "totalReplicating": 267,
            "maxReplicating": 300,
            "percentUsed": 89,
            "status": "WARNING",
            "message": "Combined capacity at 89%"
        },
        "accounts": [
            {
                "accountId": "160885257264",
                "accountName": "DEMO_TARGET",
                "accountType": "target",
                "replicatingServers": 6,
                "maxReplicating": 300,
                "percentUsed": 2,
                "status": "OK",
                "regionalBreakdown": [...],
                "warnings": []
            },
            {
                "accountId": "664418995426",
                "accountName": "STAGING_01",
                "accountType": "staging",
                "replicatingServers": 150,
                "maxReplicating": 300,
                "percentUsed": 50,
                "status": "WARNING",
                "regionalBreakdown": [...],
                "warnings": [
                    "Approaching limit - consider adding another staging account"
                ]
            }
        ],
        "recoveryCapacity": {
            "currentServers": 267,
            "maxRecoveryInstances": 4000,
            "percentUsed": 7,
            "availableSlots": 3733
        },
        "warnings": [
            "STAGING_01 at 50% capacity",
            "Combined replication at 89%"
        ]
    }
    """
    target_account_id = account_context.get("accountId") if account_context else None
    
    if not target_account_id:
        target_account_id = get_current_account_id()
    
    # Get target account configuration
    target_account = None
    staging_accounts_config = []
    
    if target_accounts_table:
        result = target_accounts_table.get_item(
            Key={"accountId": target_account_id}
        )
        if "Item" in result:
            target_account = result["Item"]
            staging_accounts_config = target_account.get("stagingAccounts", [])
    
    # Query target account capacity
    target_capacity = query_account_capacity(
        target_account_id,
        target_account.get("roleArn") if target_account else None,
        target_account.get("externalId") if target_account else None,
        account_type="target"
    )
    
    accounts = [target_capacity]
    total_replicating = target_capacity["replicatingServers"]
    all_warnings = []
    
    # Query each staging account capacity
    for staging_config in staging_accounts_config:
        staging_capacity = query_account_capacity(
            staging_config["accountId"],
            staging_config["roleArn"],
            staging_config["externalId"],
            account_type="staging",
            account_name=staging_config.get("accountName", "Unknown")
        )
        
        accounts.append(staging_capacity)
        total_replicating += staging_capacity["replicatingServers"]
        
        # Collect warnings from staging accounts
        if staging_capacity.get("warnings"):
            all_warnings.extend(staging_capacity["warnings"])
    
    # Determine combined status
    percent_used = (total_replicating / DRS_LIMITS["MAX_REPLICATING_SERVERS"]) * 100
    
    if total_replicating >= DRS_LIMITS["MAX_REPLICATING_SERVERS"]:
        combined_status = "CRITICAL"
        combined_message = f"At hard limit: {total_replicating}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} servers"
    elif percent_used >= 93:
        combined_status = "WARNING"
        combined_message = f"Approaching limit: {total_replicating}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} servers ({int(percent_used)}%)"
        all_warnings.append(f"Combined replication at {int(percent_used)}%")
    elif percent_used >= 83:
        combined_status = "INFO"
        combined_message = f"Monitor capacity: {total_replicating}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} servers ({int(percent_used)}%)"
    else:
        combined_status = "OK"
        combined_message = f"Capacity OK: {total_replicating}/{DRS_LIMITS['MAX_REPLICATING_SERVERS']} servers ({int(percent_used)}%)"
    
    return {
        "combined": {
            "totalReplicating": total_replicating,
            "maxReplicating": DRS_LIMITS["MAX_REPLICATING_SERVERS"],
            "percentUsed": int(percent_used),
            "status": combined_status,
            "message": combined_message
        },
        "accounts": accounts,
        "recoveryCapacity": {
            "currentServers": total_replicating,
            "maxRecoveryInstances": DRS_LIMITS["MAX_SOURCE_SERVERS"],
            "percentUsed": int((total_replicating / DRS_LIMITS["MAX_SOURCE_SERVERS"]) * 100),
            "availableSlots": DRS_LIMITS["MAX_SOURCE_SERVERS"] - total_replicating
        },
        "warnings": all_warnings
    }


def query_account_capacity(
    account_id: str,
    role_arn: Optional[str],
    external_id: Optional[str],
    account_type: str = "target",
    account_name: Optional[str] = None
) -> Dict:
    """
    Query DRS capacity for a single account (target or staging).
    
    Returns per-account capacity with status and warnings.
    """
    # Build account context for cross-account access
    account_context = None
    if role_arn and account_id != get_current_account_id():
        account_context = {
            "accountId": account_id,
            "assumeRoleName": role_arn.split("/")[-1],
            "externalId": external_id,
            "isCurrentAccount": False
        }
    
    # Query all regions for this account
    total_servers = 0
    replicating_servers = 0
    regional_breakdown = []
    
    def query_region(region: str) -> Dict:
        try:
            regional_drs = create_drs_client(region, account_context)
            counts = _count_drs_servers(regional_drs)
            return {
                "success": True,
                "region": region,
                "totalServers": counts["totalServers"],
                "replicatingServers": counts["replicatingServers"]
            }
        except Exception as e:
            error_str = str(e)
            if any(x in error_str for x in [
                "UninitializedAccountException",
                "not initialized",
                "UnrecognizedClientException",
                "security token"
            ]):
                return {
                    "success": True,
                    "region": region,
                    "totalServers": 0,
                    "replicatingServers": 0
                }
            return {"success": False, "region": region, "error": str(e)}
    
    # Query regions concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_region = {
            executor.submit(query_region, region): region
            for region in DRS_REGIONS
        }
        
        for future in as_completed(future_to_region):
            result = future.result()
            if result["success"] and result["totalServers"] > 0:
                regional_breakdown.append({
                    "region": result["region"],
                    "totalServers": result["totalServers"],
                    "replicatingServers": result["replicatingServers"]
                })
                total_servers += result["totalServers"]
                replicating_servers += result["replicatingServers"]
    
    # Determine status and warnings for this account
    percent_used = (replicating_servers / DRS_LIMITS["MAX_REPLICATING_SERVERS"]) * 100
    warnings = []
    
    if replicating_servers >= DRS_LIMITS["MAX_REPLICATING_SERVERS"]:
        status = "CRITICAL"
        warnings.append(f"At hard limit: {replicating_servers}/300 servers")
    elif percent_used >= 93:
        status = "WARNING"
        warnings.append(f"Approaching limit: {replicating_servers}/300 servers ({int(percent_used)}%)")
        if account_type == "staging":
            warnings.append("Consider adding another staging account to distribute load")
    elif percent_used >= 83:
        status = "INFO"
        warnings.append(f"Monitor capacity: {replicating_servers}/300 servers ({int(percent_used)}%)")
    else:
        status = "OK"
    
    return {
        "accountId": account_id,
        "accountName": account_name or account_id,
        "accountType": account_type,
        "replicatingServers": replicating_servers,
        "totalServers": total_servers,
        "maxReplicating": DRS_LIMITS["MAX_REPLICATING_SERVERS"],
        "percentUsed": int(percent_used),
        "availableSlots": DRS_LIMITS["MAX_REPLICATING_SERVERS"] - replicating_servers,
        "status": status,
        "regionalBreakdown": regional_breakdown,
        "warnings": warnings
    }
```

This provides a clean, intuitive UI for managing staging accounts with full CLI support!
