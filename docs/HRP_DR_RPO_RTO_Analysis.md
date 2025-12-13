# HRP Disaster Recovery: Worst-Case RPO/RTO Analysis

**Document Version:** 4.0  
**Created:** December 12, 2025  
**Last Updated:** December 12, 2025  
**Purpose:** Brutally honest assessment of AWS DR gaps vs current on-prem capability

---

## Technology Inventory: DRS vs Non-DRS Components

### Components Using AWS DRS (Block-Level Replication)

| Component | Server Type | DR Method | RPO | RTO | Notes |
|-----------|-------------|-----------|-----|-----|-------|
| Oracle Database | EC2 | **AWS DRS** | 15 min | 5-10 min (per server) | Multi-volume config, crash recovery needed |
| WebLogic Admin | EC2 | **AWS DRS** | 15 min | 5-10 min (per server) | Must start before Managed servers |
| WebLogic Managed | EC2 | **AWS DRS** | 15 min | 5-10 min (per server) | Depends on Admin server |
| Connector Servers | EC2 | **AWS DRS** | 15 min | 5-10 min (per server) | Customer integration points |
| SQL Server | EC2 | **AWS DRS** | 15 min | 5-10 min (per server) | Full recovery model required |
| Ansible/Jump | EC2 | **AWS DRS** | 15 min | 5-10 min (per server) | Management infrastructure |
| Delphix | EC2 | **AWS DRS** | 15 min | 5-10 min (per server) | Data masking/virtualization |

### Components NOT Using DRS (Native/Other DR Methods)

| Component | DR Method | RPO | RTO | Notes |
|-----------|-----------|-----|-----|-------|
| **Active Directory (HRP)** | Native AD Replication | Near real-time | **0 min** (all 4 regions) | DCs in us-east-1, us-west-2, us-east-2, us-west-1 - NO FAILOVER NEEDED |
| **RedHat IDM** | Native IDM Replication | Near real-time | **0 min** (all 4 regions) | IDM servers in all 4 regions - NO FAILOVER NEEDED |
| **Customer AD DCs** | Native AD Replication | Near real-time | Varies | AWS DCs in all regions + on-prem DCs via VPN |
| **SFTP (Future)** | AWS Transfer Family + S3 CRR | Near real-time | 5-10 min (DNS failover) | Currently EC2 with DRS, planned migration |
| **FSx ONTAP** | SnapMirror Replication | 30 min | 30-60 min | **NOT in HRP** - GuidingCare only |
| **EKS (WebUI)** | Multi-region clusters | N/A | 5-10 min (scale up pods) | Pods pre-exist in DR, scaled to 0 |
| **S3 Storage** | Cross-Region Replication | Near real-time | Automatic | Database backups, artifacts |
| **Route 53** | Global service | N/A | Automatic | DNS failover built-in |
| **Palo Alto Firewalls** | Pre-deployed in DR | N/A | N/A | HE manages; customer switches their VPN tunnel |
| **Customer VPN Tunnels** | Customer-managed | N/A | **Variable (customer-dependent)** | Customer must reconfigure VPN to DR endpoint |

### Key Insight: What Actually Needs DRS Failover

**DRS Required (Manual Failover):**
- Oracle databases (~8 per 1000 servers)
- WebLogic servers (~80 per 1000 servers)
- Connector servers (~40 per 1000 servers)
- SQL Server (~20 per 1000 servers)
- Ansible/Jump/Delphix (~50 per 1000 servers)
- **Total DRS servers: ~800 of 1000** (80%)

**Already Multi-Region (No Failover):**
- HRP AD Domain Controllers (3 per region x 4 regions = 12 servers)
- RedHat IDM servers (3 per region x 4 regions = 12 servers)
- Customer AD DCs (3 per customer per region)
- EKS clusters (pre-deployed)
- Network infrastructure (TGW, firewalls)
- **Total non-DRS: ~200 of 1000** (20%)

**Customer-Dependent (Adds Delay):**
- Customer VPN tunnel reconfiguration to DR endpoint
- Customer validation and testing
- **This is outside HE control and adds significant time**

---

## The Hard Truth: Current vs AWS Comparison

### What They Have Today (On-Prem)
| Capability | Current State |
|------------|---------------|
| **Full DR Test Cycle** | **4 hours total** (failover + run + failback) |
| **Failover Time** | 5 minutes (clean shutdown) |
| **Technology** | VMware SRM + Pure Storage SAN replication |
| **IP Addresses** | **No change** (stretched VLANs) |
| **Replication Level** | Entire customer volume (single unit) |
| **Failback** | Delta sync from Pure, fast |
| **Automation** | **VMware SRM orchestrates everything** |
| **Servers** | All servers fail over as coordinated unit |

### What AWS DRS Actually Is
| Capability | AWS Reality | Gap |
|------------|-------------|-----|
| **Automation** | **NONE** - Console clicks or API calls | 🔴 **CRITICAL** |
| **Orchestration** | **NONE** - You build it yourself | 🔴 **CRITICAL** |
| **Full DR Test Cycle** | **Days** (manual at scale) | 🔴 **Unusable** |
| **Failover Time** | **Days** for 1000 servers manually | 🔴 **Unusable** |
| **IP Addresses** | **ALL CHANGE** (different region CIDR) | 🔴 **Major** |
| **Replication Level** | Per-instance (not unified) | 🔴 **Coordination nightmare** |
| **Failback** | Manual reverse setup | 🔴 **Not designed** |
| **Cross-account** | Separate console per account | 🔴 **Multiplies effort** |
| **Server Limit** | **300 servers per staging account** | 🔴 **Multiple staging accounts needed** |

### 🔴 CRITICAL: DRS 300-Server Limit

**AWS DRS can only replicate 300 source servers per staging account.**

| Scale | DRS Servers | Staging Accounts Needed | Complexity |
|-------|-------------|------------------------|------------|
| Current (101 servers) | ~76 | 1 | Manageable |
| 500 servers | ~400 | 2 | Moderate |
| 1000 servers | ~800 | **3** | High |
| 1500 servers | ~1200 | **4** | Very High |

**Impact at 1000-Server Scale:**
- Need **3 separate DRS staging accounts** in DR region
- Each staging account = separate DRS console
- Failover coordination across 3 staging accounts + multiple source accounts
- Automation must orchestrate across all staging accounts
- Cost: Additional staging infrastructure in 3 accounts

---

## Scale Reality Check (Verified December 12, 2025)

### HRP Server Inventory (ACTUAL - AWS API Verified)

| Account | Purpose | us-east-1 | us-west-2 | Total |
|---------|---------|-----------|-----------|-------|
| 769064993134 | HRP Customer Production | 60 | 0 | 60 |
| 538127172524 | HRP Customer AD DCs | 25 | 0 | 25 |
| 211234826829 | HRP Shared Services (Mgt DCs, IDM) | 7 | 5 | 12 |
| 639966646465 | Network (Palo Alto) | 2 | 2 | 4 |
| **TOTAL HRP** | | **94** | **7** | **~101 servers** |

### HRP Customer Breakdown (769064993134)
| Customer | Oracle | WebLogic | Connector | Ansible | LB | Other | Total |
|----------|--------|----------|-----------|---------|-----|-------|-------|
| AXM | 1 | 2 | 2 | 2 | 0 | 2 | 9 |
| ALH | 3 | 4 | 2 | 2 | 2 | 0 | 13 |
| CITI | 2 | 2 | 1 | 1 | 1 | 0 | 7 |
| FRSO | 1 | 2 | 1 | 1 | 1 | 0 | 6 |
| + DRS Replication Servers | | | | | | | ~12 |
| + Delphix, Jump, Test | | | | | | | ~13 |
| **Subtotal** | | | | | | | **~60** |

### HRP Customer AD DCs (538127172524)
| Customer | DCs in us-east-1 |
|----------|------------------|
| AXM | 3 |
| ALH | 3 |
| CITI | 3 |
| FRSO | 3 |
| UST | 3 |
| ATR | 3 |
| WIP | 3 |
| EDIF | 3 |
| **Total** | **24 + 1 test** |

### HRP Shared Services (211234826829)
| Server | Type | Region |
|--------|------|--------|
| he3-mgtdc-1, 2, 3 | Management DCs | us-east-1 |
| he3-idm-01, 02, 03 | IDM Servers | us-east-1 |
| he3-mgtdc-03, 04, 05 | Management DCs | us-west-2 |
| he3-idm-04, 05, 06 | IDM Servers | us-west-2 |

### Key Finding: HRP is NOT at Scale Yet
- **Current HRP total: ~101 servers** (not 1000)
- **us-west-2 has minimal HRP presence** (only Shared Services DCs/IDM)
- **No FSx ONTAP in HRP accounts** (FSx is in GuidingCare account 096212910625)
- **HRP customers are in us-east-1 only currently**

### AWS Account Structure
- 769064993134: HRP Customer Production (Oracle, WebLogic, Connectors)
- 538127172524: HRP Customer AD Domain Controllers
- 211234826829: HRP Shared Services (Management DCs, IDM)
- 639966646465: Network (Palo Alto firewalls for VPN)
- **4 accounts = 4 separate DRS console sessions**

### Scaling to 1000 Servers (40 Customers)

**Projected Server Distribution at 1000 Servers:**

| Component | Per Customer | 40 Customers | DR Method |
|-----------|--------------|--------------|-----------|
| Oracle DB | 2 | 80 | DRS |
| WebLogic Admin | 1 | 40 | DRS |
| WebLogic Managed | 4 | 160 | DRS |
| Connectors | 2 | 80 | DRS |
| SQL Server | 1 | 40 | DRS |
| Customer AD DCs | 3 | 120 | Native AD Replication |
| Ansible/Jump | 2 | 80 | DRS |
| Load Balancers | 2 | 80 | DRS |
| SFTP | 1 | 40 | DRS (or Transfer Family) |
| Other (Delphix, Test) | 3 | 120 | DRS |
| **Subtotal Customer** | **21** | **840** | |
| HRP Shared Services DCs | - | 12 | Native AD Replication |
| HRP IDM Servers | - | 12 | Native IDM Replication |
| Network (Palo Alto) | - | 8 | Pre-deployed |
| EKS (WebUI pods) | - | N/A | Multi-region |
| **Total** | | **~872 DRS + ~152 Non-DRS** | |

**Key Insight:** At 1000-server scale:
- **~800 servers require DRS failover** (manual console clicks)
- **~200 servers use native replication** (no failover needed)
- **Customer AD DCs (120) do NOT need DRS** - native AD replication handles DR

### DRS Staging Account Requirements (300-Server Limit)

**DRS can only replicate 300 servers per staging account.** At 1000-server scale:

| Scale | DRS Servers | Staging Accounts | Source Accounts | Total Consoles |
|-------|-------------|------------------|-----------------|----------------|
| Current | ~76 | 1 | 4 | 5 |
| 500 servers | ~400 | 2 | ~20 | ~22 |
| 1000 servers | ~800 | **3** | ~40 | **~43** |

**Architecture at 1000 Servers:**
```
Source Accounts (40 customer accounts)
    ↓ DRS Replication
Staging Account 1 (300 servers) ─┐
Staging Account 2 (300 servers) ─┼─→ DR Region
Staging Account 3 (200 servers) ─┘
```

**Implications:**
- 3 separate DRS consoles to manage during failover
- Cross-account IAM roles needed for orchestration
- Automation must coordinate across all 3 staging accounts
- Additional cost for staging infrastructure in 3 accounts

---

## DRS Console Reality: What "Failover" Actually Means

### Per-Server Manual Steps (Console)
For EACH of the ~101 HRP servers:

1. Log into correct AWS account (switch accounts between 4 accounts)
2. Navigate to DRS console
3. Find the source server
4. Select recovery point
5. Click "Initiate recovery"
6. Configure launch settings (instance type, subnet, security group)
7. Wait for launch
8. Verify instance is running
9. Check replication status
10. Repeat for next server

**Time per server: 5-15 minutes** (assuming no issues)

### The Math (Manual Console) - ACTUAL HRP Scale
| Scenario | Servers | Time per Server | Total Time | Staff Needed |
|----------|---------|-----------------|------------|--------------|
| Single HRP customer | 7-13 | 10 min | 1.2-2.2 hours | 1 |
| All HRP customers (769064993134) | 60 | 10 min | **10 hours** | 1 |
| All HRP AD DCs (538127172524) | 25 | 10 min | **4.2 hours** | 1 |
| All HRP (4 accounts, parallel) | 101 | 10 min | **4-5 hours** | 4 people |

**Current HRP scale is manageable - but still requires coordination across 4 accounts**

### Future Scale Consideration
If HRP grows to 40+ customers with ~25 servers each = **1000 servers**:
| Scenario | Servers | Time per Server | Total Time | Staff Needed |
|----------|---------|-----------------|------------|--------------|
| All customers | 1000 | 10 min | **167 hours** | 1 |
| All customers (parallel) | 1000 | 10 min | **17 hours** | 10 people |

**And that's JUST launching instances - no validation, no DNS, no application startup**

---

## Worst-Case Failover Timeline (1000 Servers Scale)

### Assumptions (1000-Server Scale)
- **~800 DRS servers** across multiple customer accounts
- **~200 non-DRS servers** (AD, IDM, network) - already multi-region
- Manual console operations (no automation)
- 10 trained staff available
- No automation exists
- Things go wrong (they will)

### What Doesn't Need Failover (Already Multi-Region)
| Component | Count | Why No Failover Needed |
|-----------|-------|------------------------|
| HRP AD DCs (healthedge.biz) | 6 | Already in us-east-1 + us-west-2, native replication |
| HRP IDM Servers | 6 | Already in us-east-1 + us-west-2, native replication |
| Customer AD DCs | ~120 | AWS DCs + on-prem DCs, native AD replication |
| Palo Alto Firewalls | 8 | Pre-deployed in all regions |
| EKS Clusters | N/A | Pre-exist in DR, just scale up pods |
| **Total Non-DRS** | **~140** | **No manual failover required** |

---

## Worst-Case Failover Timeline (Current 101 HRP Servers, Manual)

### Assumptions (Current State)
- 101 HRP servers across 4 accounts (current state)
- ~76 DRS servers (excludes AD/IDM which are already multi-region)
- Manual console operations
- 4 trained staff available (1 per account)
- No automation exists
- Things go wrong (they will)

### Phase 0: Detection & Mobilization
| Step | Time | Notes |
|------|------|-------|
| Detect outage | 30-60 min | Monitoring alerts |
| Confirm regional failure | 30-60 min | Not transient |
| Assemble 4-person DR team | 1-2 hours | Off-hours, weekends |
| Decision to failover | 30-60 min | Management approval |
| Assign accounts to staff | 15 min | 4 accounts, 4 people |
| **Subtotal** | **2.5-5 hours** | Before any recovery starts |

### Phase 1: DRS Instance Recovery (Manual Console)
| Step | Time | Notes |
|------|------|-------|
| Log into all 4 accounts | 15 min | MFA, account switching |
| Initiate recovery (101 servers) | **2.5-5 hours** | 4 people parallel |
| Wait for instances to launch | 1-2 hours | Staggered completion |
| Verify all instances running | 1-2 hours | Check each one |
| Troubleshoot failures | 1-3 hours | 5-10% will fail |
| **Subtotal** | **6-12 hours** | Just to get instances up |

**🔴 CRITICAL:** DRS has no bulk operations. Each server is individual clicks.

### Phase 2: Post-Launch Configuration (Manual)
| Step | Time | Notes |
|------|------|-------|
| SSM agent reinstall (101 servers) | 1-2 hours | Different region endpoint |
| Verify SSM connectivity | 30-60 min | |
| DNS updates (~101 A records) | 1-2 hours | Every IP changed |
| Verify DNS propagation | 30 min | |
| **Subtotal** | **3-6 hours** | |

### Phase 3: FSx ONTAP
**NOTE: HRP does NOT currently use FSx ONTAP** (FSx is in GuidingCare account 096212910625)
| Step | Time | Notes |
|------|------|-------|
| N/A for HRP | 0 | HRP uses local Oracle storage |
| **Subtotal** | **0 hours** | |

### Phase 4: Database Recovery
| Step | Time | Notes |
|------|------|-------|
| Oracle startup (~8 DBs) | 1-2 hours | Sequential dependencies |
| Oracle crash recovery | 1-2 hours | If unclean shutdown |
| Oracle validation | 1-2 hours | |
| **Subtotal** | **3-6 hours** | |

### Phase 5: Application Startup
| Step | Time | Notes |
|------|------|-------|
| WebLogic Admin servers | 30-60 min | Must be first |
| WebLogic Managed servers | 1-2 hours | After Admin |
| Connector services | 1-2 hours | |
| Application validation | 2-4 hours | Per customer |
| **Subtotal** | **5-9 hours** | |

### Phase 6: Customer Access (CUSTOMER-DEPENDENT - Outside HE Control)
| Step | Time | Notes |
|------|------|-------|
| Route 53 DNS failover | 30 min | HE-controlled |
| Notify customers of DR event | 1-2 hours | Contact all 8 customers |
| **Customer VPN tunnel switch** | **2-8 hours** | **CUSTOMER ACTION REQUIRED** - they reconfigure their VPN to DR endpoint |
| Customer validation | **4-16 hours** | Each customer tests their apps |
| **Subtotal** | **8-27 hours** | **Largely outside HE control** |

**⚠️ CRITICAL:** Customers control their own VPN tunnels. HE manages Palo Alto firewalls, but customers must reconfigure their VPN endpoint to point to DR. This is:
- Outside HE control
- Dependent on customer IT availability (weekends, holidays)
- Variable per customer (some fast, some slow)
- A major source of delay during DR events

---

## Total Failover Time (Manual, 101 HRP Servers - Current State)

**Note:** Only ~76 servers need DRS failover. AD/IDM (25 servers) are already multi-region.

| Phase | Best Case | Worst Case |
|-------|-----------|------------|
| Detection & Mobilization | 2.5 hours | 5 hours |
| DRS Instance Recovery | 6 hours | 12 hours |
| Post-Launch Config | 3 hours | 6 hours |
| FSx ONTAP | 0 hours | 0 hours |
| Database Recovery | 3 hours | 6 hours |
| Application Startup | 5 hours | 9 hours |
| Customer Access | 7 hours | 25 hours |
| **TOTAL** | **26.5 hours (~1.1 days)** | **63 hours (~2.6 days)** |

### Compare to Current On-Prem
| Metric | On-Prem | AWS (Manual, 101 servers) | Gap |
|--------|---------|---------------------------|-----|
| Failover | 5 minutes | **1-2.6 days** | 🔴 **300-750x slower** |
| Full test cycle | 4 hours | **3-7 days** | 🔴 **18-42x slower** |

### At Future Scale (1000 servers - ~800 DRS servers)
| Metric | On-Prem | AWS (Manual, 800 DRS servers) | Gap |
|--------|---------|-------------------------------|-----|
| Failover | 5 minutes | **2.5-7 days** | 🔴 **700-2000x slower** |
| Full test cycle | 4 hours | **1.5-4 weeks** | 🔴 **Unusable** |

**Note:** 200 servers (AD, IDM, network) don't need DRS failover - they're already multi-region or pre-deployed.

---

## Failback Timeline (Manual, 101 HRP Servers - Current State)

Failback is WORSE because:
1. Must configure reverse replication for each server
2. Must wait for full sync (not delta like Pure)
3. Same manual steps again

| Phase | Best Case | Worst Case |
|-------|-----------|------------|
| Validate primary region | 1 hour | 4 hours |
| Configure reverse DRS (~76 DRS servers) | **3-6 hours** | Manual per server |
| Wait for replication sync | **12-48 hours** | Full data copy |
| Execute failback (~76 DRS servers) | 5-10 hours | Same as failover |
| All other steps | 10-25 hours | |
| **TOTAL FAILBACK** | **1.5-2 days** | **4-5 days** |

**Note:** AD/IDM servers don't need failback - they're already multi-region.

### Full DR Test Cycle (Failover + Test + Failback)
| Environment | Time (Current ~76 DRS servers) | Time (Future ~800 DRS servers) |
|-------------|--------------------------------|--------------------------------|
| On-Prem (VMware SRM) | **4 hours** | **4 hours** |
| AWS (Manual DRS) | **3-7 days** | **1.5-4 weeks** |

---

## 1000-Server Scale: Detailed Failover Timeline

### Phase 0: Detection & Mobilization (Same as Current)
| Step | Time | Notes |
|------|------|-------|
| Detect outage | 30-60 min | Monitoring alerts |
| Confirm regional failure | 30-60 min | Not transient |
| Assemble 10-person DR team | 1-2 hours | Off-hours, weekends |
| Decision to failover | 30-60 min | Management approval |
| Assign accounts to staff | 30 min | Multiple customer accounts |
| **Subtotal** | **3-5 hours** | Before any recovery starts |

### Phase 1: DRS Instance Recovery (~800 DRS Servers)
| Step | Time | Notes |
|------|------|-------|
| Log into all customer accounts | 1 hour | Many accounts, MFA |
| Initiate recovery (800 servers) | **13-27 hours** | 10 people parallel, 10 min/server |
| Wait for instances to launch | 2-4 hours | Staggered completion |
| Verify all instances running | 2-4 hours | Check each one |
| Troubleshoot failures | 4-8 hours | 5-10% will fail |
| **Subtotal** | **22-44 hours** | Just to get instances up |

### Phase 2: Post-Launch Configuration (~800 Servers)
| Step | Time | Notes |
|------|------|-------|
| SSM agent reinstall (800 servers) | 4-8 hours | Different region endpoint |
| Verify SSM connectivity | 2-4 hours | |
| DNS updates (~800 A records) | 4-8 hours | Every IP changed |
| Verify DNS propagation | 1-2 hours | |
| **Subtotal** | **11-22 hours** | |

### Phase 3: Database Recovery (~80 Oracle + ~40 SQL)
| Step | Time | Notes |
|------|------|-------|
| Oracle startup (~80 DBs) | 4-8 hours | Sequential dependencies |
| Oracle crash recovery | 4-8 hours | If unclean shutdown |
| Oracle validation | 4-8 hours | |
| SQL Server startup (~40 DBs) | 2-4 hours | |
| SQL Server validation | 2-4 hours | |
| **Subtotal** | **16-32 hours** | |

### Phase 4: Application Startup (~200 WebLogic + ~80 Connectors)
| Step | Time | Notes |
|------|------|-------|
| WebLogic Admin servers (~40) | 2-4 hours | Must be first |
| WebLogic Managed servers (~160) | 4-8 hours | After Admin |
| Connector services (~80) | 4-8 hours | |
| Application validation | 8-16 hours | Per customer |
| **Subtotal** | **18-36 hours** | |

### Phase 5: EKS WebUI (Already Multi-Region)
| Step | Time | Notes |
|------|------|-------|
| Scale up DR pods | 30-60 min | Pods pre-exist at 0 replicas |
| Update DNS to DR LB | 30 min | |
| Validate WebUI | 1-2 hours | |
| **Subtotal** | **2-4 hours** | |

### Phase 6: Customer Access (~40 Customers - CUSTOMER-DEPENDENT)
| Step | Time | Notes |
|------|------|-------|
| Route 53 DNS failover | 30 min | HE-controlled |
| Notify customers of DR event | 2-4 hours | Contact all 40 customers |
| **Customer VPN tunnel switch** | **12-36 hours** | **CUSTOMER ACTION REQUIRED** - 40 customers reconfigure VPN |
| Customer validation | **16-48 hours** | Each customer tests their apps |
| **Subtotal** | **31-89 hours** | **Largely outside HE control** |

**⚠️ CRITICAL at Scale:** With 40 customers, VPN tunnel switching becomes a major bottleneck:
- Each customer must reconfigure their VPN to DR endpoint
- Customer IT teams have varying response times
- Weekend/holiday DR events = longer delays
- Some customers may take 24+ hours to switch
- Failback requires ANOTHER VPN switch (doubles the delay)

### Total Failover Time (Manual, 1000 Servers - ~800 DRS)

| Phase | Best Case | Worst Case |
|-------|-----------|------------|
| Detection & Mobilization | 3 hours | 5 hours |
| DRS Instance Recovery | 22 hours | 44 hours |
| Post-Launch Config | 11 hours | 22 hours |
| Database Recovery | 16 hours | 32 hours |
| Application Startup | 18 hours | 36 hours |
| EKS WebUI | 2 hours | 4 hours |
| Customer Access (VPN switch) | 31 hours | 89 hours |
| **TOTAL** | **103 hours (~4.3 days)** | **232 hours (~9.7 days)** |

**Note:** Customer VPN tunnel switching is the longest phase and is outside HE control.

### Failback at 1000-Server Scale

| Phase | Best Case | Worst Case |
|-------|-----------|------------|
| Validate primary region | 2 hours | 8 hours |
| Configure reverse DRS (~800 servers) | **16-32 hours** | Manual per server |
| Wait for replication sync | **24-72 hours** | Full data copy |
| Execute failback (~800 servers) | 22-44 hours | Same as failover |
| Post-failback config | 11-22 hours | DNS, SSM, etc. |
| **Customer VPN switch AGAIN** | **12-36 hours** | Back to primary endpoint |
| Customer validation | 16-48 hours | |
| **TOTAL FAILBACK** | **4-7 days** | **11-16 days** |

**⚠️ Failback VPN Impact:** Customers must switch their VPN tunnels TWICE:
1. Failover: Primary → DR endpoint
2. Failback: DR → Primary endpoint

This doubles the customer-dependent delay and is a major difference from on-prem where VPN endpoints don't change.

### Full DR Test Cycle at 1000-Server Scale
| Environment | Failover | Test | Failback | **Total** |
|-------------|----------|------|----------|-----------|
| On-Prem (VMware SRM) | 5 min | 2 hours | 2 hours | **4 hours** |
| AWS (Manual DRS) | 4-10 days | 1-2 days | 4-16 days | **9-28 days** |

**Why AWS is so much slower:**
- 800 DRS servers require individual failover clicks
- Customer VPN tunnel switch required (outside HE control)
- Failback requires ANOTHER VPN switch
- No delta sync for failback (full replication)

---

## Why This Is Fundamentally Broken

### Problem 1: DRS Has No Orchestration
- VMware SRM: Click "Failover", everything happens
- AWS DRS: Click 1000 times, hope you don't miss one

### Problem 2: No Bulk Operations
- Cannot select "all servers in this account" and failover
- Cannot create recovery plans that execute automatically
- Cannot define server startup sequences

### Problem 3: Cross-Account Complexity
- Each customer account = separate DRS console
- Must log into each account separately
- No unified view across accounts

### Problem 4: No Dependency Management
- DRS doesn't know Oracle must start before WebLogic
- DRS doesn't know DNS must update after IP assignment
- You must manually sequence everything

### Problem 5: IP Address Changes
- On-prem: Stretched VLANs, IPs don't change
- AWS: Different region = different CIDR = every IP changes
- 1000 DNS updates required

### Problem 6: FSx Is Not Integrated (GuidingCare Issue, Not HRP)
- **HRP does NOT use FSx ONTAP** - uses local Oracle storage
- FSx ONTAP is in GuidingCare account (096212910625)
- HRP storage is simpler but still requires DRS coordination

---

## What Would Be Required to Match On-Prem (HRP-Specific)

### Option A: Build Custom Orchestration for HRP

**Reference Architectures Available:**
- `drs-tools` - AWS DRS automation tools and utilities
- `dr-orchestration-artifacts` - Step Functions workflows, Lambda functions, cross-account patterns

These reference architectures provide a starting point and can significantly reduce development time.

**Scope (Simpler than GuidingCare - no FSx):**
- Step Functions workflow for entire failover
- Lambda functions for each operation
- Cross-account IAM roles (multiple customer + staging accounts)
- DNS automation
- Monitoring and alerting
- Rollback capability
- Testing framework

**Estimated Effort (Current 101 servers, 4 accounts):**
| Component | Effort | Cost |
|-----------|--------|------|
| Architecture & Design | 2-3 weeks | $40-60K |
| DRS Orchestration | 4-6 weeks | $80-120K |
| DNS Automation | 1-2 weeks | $20-30K |
| Cross-Account Framework | 2-3 weeks | $40-60K |
| Testing & Validation | 3-4 weeks | $60-80K |
| Documentation & Training | 1-2 weeks | $20-30K |
| **TOTAL** | **13-20 weeks** | **$260-380K** |

**Estimated Effort (1000 servers, 40+ customer accounts, 3 staging accounts):**
| Component | Effort | Cost |
|-----------|--------|------|
| Architecture & Design | 4-6 weeks | $80-120K |
| DRS Orchestration (3 staging accounts) | 10-14 weeks | $200-280K |
| DNS Automation | 2-3 weeks | $40-60K |
| Cross-Account Framework (40+ source + 3 staging) | 5-7 weeks | $100-140K |
| Customer Onboarding Automation | 3-4 weeks | $60-80K |
| Testing & Validation | 6-8 weeks | $120-160K |
| Documentation & Training | 2-3 weeks | $40-60K |
| **TOTAL** | **32-45 weeks** | **$640-900K** |

**Note:** 300-server DRS limit requires 3 staging accounts at 1000-server scale, adding complexity to orchestration and cross-account framework.

**Timeline:** 
- Current scale (101 servers): 4-6 months to production-ready
- Future scale (1000 servers): 8-12 months to production-ready

**Result:** Achieve 4-8 hour RTO (still not 5 minutes)

### Option B: Third-Party DR Tool
Consider tools that provide orchestration:
- **Zerto** - Has AWS support, orchestration built-in
- **Commvault** - DR orchestration
- **Veeam** - Backup and DR

**Cost:** $100-200K licensing + implementation (smaller scale)
**Timeline:** 2-4 months

### Option C: Accept the Limitation
- Document realistic RTO: 1-2.6 days (current 101 servers)
- Communicate to customers
- Adjust contracts
- Focus on prevention over recovery

---

## Realistic Achievable Targets

### Current Scale (101 Servers - ~76 DRS)

#### With No Additional Investment
| Metric | Target | Reality |
|--------|--------|---------|
| RPO | 15 min | **15 min** (DRS continuous replication) |
| RTO | 4 hours | **1-2.6 days** |
| Full Test Cycle | 4 hours | **3-7 days** |

#### With $260-380K Automation Investment (4-6 months)
| Metric | Target | Achievable |
|--------|--------|------------|
| RPO | 15 min | **15 min** |
| RTO | 4 hours | **4-8 hours** |
| Full Test Cycle | 4 hours | **12-24 hours** |

### Future Scale (1000 Servers - ~800 DRS)

#### With No Additional Investment
| Metric | Target | Reality |
|--------|--------|---------|
| RPO | 15 min | **15 min** (DRS continuous replication) |
| RTO | 4 hours | **4-9 days** |
| Full Test Cycle | 4 hours | **9-25 days** |

#### With $580-840K Automation Investment (8-12 months)
| Metric | Target | Achievable |
|--------|--------|------------|
| RPO | 15 min | **15 min** |
| RTO | 4 hours | **4-8 hours** |
| Full Test Cycle | 4 hours | **12-24 hours** |

**Note:** HRP automation is simpler than GuidingCare because:
- No FSx ONTAP to coordinate
- Simpler storage (local Oracle, no shared storage)
- AD/IDM already multi-region (no failover needed)

### What Cannot Be Achieved (Architectural)
| Metric | On-Prem | AWS Limit | Why |
|--------|---------|-----------|-----|
| 5-minute failover | ✅ | ❌ | Instance-level vs volume-level |
| No IP changes | ✅ | ❌ | No stretched VLANs in AWS |
| Delta failback | ✅ | ❌ | DRS doesn't support |
| Single-click failover | ✅ | ❌ | Must build orchestration |

---

## Immediate Actions Required

### Before MVP (2/6/2026) - 8 weeks away
1. **Set realistic expectations with stakeholders**
   - 4-hour RTO is achievable with automation investment (~$260-380K at current scale)
   - Without automation: 1-2.6 days RTO (current 101 servers)
   - At 1000-server scale without automation: 4-9 days RTO

2. **Decide: Build automation or accept limitation**
   - If build: Start immediately, 4-6 months timeline (current scale)
   - If accept: Document and communicate 1-2.6 day RTO

3. **Current HRP scale is manageable**
   - ~76 DRS servers across 4 accounts (AD/IDM already multi-region)
   - 4 trained staff can execute manual failover
   - MVP with 1-2 customers is feasible manually

4. **Fix known gaps (from Confluence docs)**
   - ⚠️ **us-west-2 healthedge.biz forwarding rule** targets us-east-1 DCs (not local)
   - ⚠️ **us-west-2 IDM IPs missing** from forwarding rules
   - Ensure DRS replication is configured for all ~76 DRS servers
   - Document manual runbook for each account

### For Production (3/13/2026)
5. **Have honest conversation with customer**
   - Their 4-hour expectation is based on VMware SRM
   - AWS DRS is fundamentally different
   - Options: invest in automation, accept longer RTO, or reconsider approach

### For 1000-Server Scale (Future)
6. **Automation is MANDATORY at scale**
   - Manual failover of 800 DRS servers = 4-9 days
   - Full test cycle = 9-25 days (unusable)
   - Investment required: $580-840K over 8-12 months

### Key Finding: Build Automation NOW
- **Current: ~76 DRS servers** - manageable with manual process
- **Future: ~800 DRS servers** - automation is mandatory
- **Recommendation:** Build automation now while scale is small
- **Cost savings:** $260-380K now vs $580-840K later

---

## Questions for Leadership

1. **Is automation investment approved for HRP?**
   - Current scale: $260-380K for 4-8 hour RTO
   - Future scale (1000 servers): $580-840K for 4-8 hour RTO
   - Without it: 1-2.6 days (current) or 4-9 days (1000 servers)

2. **Is 4-6 month timeline acceptable?**
   - Automation won't be ready for MVP (2/6/2026)
   - Could be ready for production (3/13/2026) if started now

3. **What is the contractual RTO commitment?**
   - If 4 hours is contractual, automation is required
   - If 24 hours is acceptable, manual process works at current scale
   - At 1000-server scale, even 24-hour RTO requires automation

4. **Has customer been informed of AWS limitations?**
   - They may expect VMware SRM-like experience
   - Current capability: 1-2.6 days (not 4 hours)
   - Future capability at scale: 4-9 days without automation

5. **Should we evaluate third-party DR tools?**
   - May be faster than building custom (2-4 months vs 4-6 months)
   - Cost similar: $100-200K vs $260-380K
   - Consider: Zerto, Commvault, Veeam

6. **What is the growth timeline to 1000 servers?**
   - If 2+ years away: Build automation incrementally
   - If <1 year away: Plan for full-scale automation now

---

## Source Documents

| Document | Link |
|----------|------|
| HRP DR Scoping Overview | https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5269651616 |
| HRP DR Recommendations | https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5112397888 |
| FSx ONTAP DR Assessment | https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5306581074 |
| Oracle DR Runbook | https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5148704910 |
| SQL Server DR Runbook | https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5171216573 |
| WebLogic DR Design | https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5148704821 |
| SFTP DR Design | https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5231640751 |
| AD/DNS DR Document | https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5287313409 |
| Network DR Design | https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5287313416 |

---

## Summary

**The customer expects VMware SRM. AWS DRS is not VMware SRM.**

| What They Expect | What DRS Provides |
|------------------|-------------------|
| Orchestrated failover | Manual clicks |
| 5-minute RTO | 1-2.6 days (current) / 4-9 days (1000 servers) |
| Single recovery plan | Per-server operations |
| Automated failback | Manual reverse setup |
| No IP changes | All IPs change |

### HRP-Specific Assessment (Verified December 12, 2025)

| Metric | Current State | Future (1000 Servers) |
|--------|---------------|----------------------|
| Total HRP Servers | **101** | **~1000** |
| DRS Servers (need failover) | **~76** | **~800** |
| Non-DRS Servers (already multi-region) | **~25** | **~200** |
| AWS Accounts | **4** | **40+** |
| Customers | **8** | **40** |
| FSx ONTAP | **None** | **None** (HRP uses local Oracle) |
| AD/IDM | **Already multi-region** | **Already multi-region** |

### Technology DR Method Summary

| Technology | DR Method | Failover Required? |
|------------|-----------|-------------------|
| Oracle, WebLogic, SQL, Connectors | AWS DRS | ✅ Yes (manual) |
| HRP AD (healthedge.biz) | Native AD Replication | ❌ No (multi-region) |
| HRP IDM (idm.healthedge.biz) | Native IDM Replication | ❌ No (multi-region) |
| Customer AD | Native AD Replication | ❌ No (AWS + on-prem) |
| EKS WebUI | Multi-region clusters | ⚠️ Scale up pods only |
| SFTP (current) | AWS DRS | ✅ Yes |
| SFTP (future) | AWS Transfer Family + S3 CRR | ❌ No (DNS failover) |
| Network (Palo Alto) | Pre-deployed | ❌ No |

### Recommendation

**HRP is at a manageable scale for manual DR today, but automation should be built now before scale increases.**

| Option | Cost (Current) | Cost (1000 Servers) | Timeline | RTO Achieved |
|--------|----------------|---------------------|----------|--------------|
| Manual | $0 | $0 | Now | 1-2.6 days / 4-9 days |
| Custom Automation | $260-380K | $640-900K | 4-6 / 8-12 months | 4-8 hours |
| Third-Party Tool | $100-200K | $300-500K | 2-4 months | 4-8 hours |

**Key Insight:** ~20% of servers (AD, IDM, network) don't need DRS failover - they're already multi-region. Focus automation on the ~80% that do (Oracle, WebLogic, SQL, Connectors).

**Without automation investment, the AWS DR solution cannot meet 4-hour RTO expectations at any scale.**

---

## Appendix: Confluence Document Analysis Summary

### Documents Reviewed (December 12, 2025)

| Document | Key Findings |
|----------|--------------|
| **HRP DR Scoping Overview** | Full scope estimate $592K; MVP 2/6/2026, Production 3/13/2026; Step Functions automation planned but NOT in place |
| **Oracle DR Runbook** | Uses AWS DRS; Multi-volume config (data, redo, archive, control); 15 min RPO, 5-10 min RTO per server |
| **SQL Server DR Runbook** | Uses AWS DRS; Full recovery model required; Same RPO/RTO as Oracle |
| **WebLogic DR Design** | Uses AWS DRS; Admin server must start first; Managed servers depend on Admin |
| **SFTP DR Design** | Current: EC2 with DRS; Future: AWS Transfer Family + S3 CRR (near real-time RPO, 5-10 min RTO) |
| **FSx ONTAP DR Assessment** | SnapMirror replication; 30 min RPO, 4 hour RTO; **NOT used by HRP** (GuidingCare only) |
| **AD/DNS DR Document** | AD/IDM already multi-region (us-east-1 + us-west-2); **NO FAILOVER NEEDED**; Gap: us-west-2 forwarding rules target us-east-1 |

### Critical Gaps Identified from Confluence Docs

1. **us-west-2 healthedge.biz Forwarding Rule** - Targets us-east-1 DCs instead of local us-west-2 DCs
2. **us-west-2 IDM IPs Missing** - Not in any forwarding rules (10.222.49.221, 10.222.59.162, 10.222.54.170)
3. **Step Functions Automation** - Planned but NOT implemented yet
4. **DR Region AD/IDM** - Not deployed in us-east-2 or us-west-1 (only network infrastructure ready)

### Assumptions from HRP DR Scoping Overview

Per the November 25, 2025 call:
- Customer production environments: 10-44 servers per customer
- Solution must support 15 min RPO and 4 hour RTO
- DR testing must be identical to actual DR incident (one active environment at a time)
- Must assume possible lack of availability of entire primary region
- AWS DRS for block-level replication; EKS clusters pre-exist in DR with scaled-down pods
- EC2 instances pre-created in target region with pre-allocated IPs
- Each customer has at least one AD server in DR region
- Failover process automated with Step Functions + Lambda (PLANNED, not implemented)

### Technology-Specific DR Methods (Verified)

| Technology | Document | DR Method | Automation Status |
|------------|----------|-----------|-------------------|
| Oracle | Oracle DR Runbook | AWS DRS | Manual (scripts provided) |
| SQL Server | SQL Server DR Runbook | AWS DRS | Manual (scripts provided) |
| WebLogic | WebLogic DR Design | AWS DRS | Manual (scripts provided) |
| SFTP (current) | SFTP DR Design | AWS DRS | Manual |
| SFTP (future) | SFTP DR Design | Transfer Family + S3 CRR | DNS failover (automated) |
| FSx ONTAP | FSx DR Assessment | SnapMirror | Manual CLI commands |
| AD/IDM | AD/DNS DR Document | Native replication | **Already multi-region** |
| EKS | DR Scoping Overview | Multi-region clusters | Scale pods (semi-automated) |

### What the Documents Say vs Reality

| Document Claims | Reality |
|-----------------|---------|
| "15 min RTO" per server | True for single server, but 800 servers = days |
| "Automated failover" | **PLANNED** - Step Functions not implemented |
| "One-click recovery" | Per-server clicks, not bulk operations |
| "Non-disruptive testing" | True, but test cycle takes days at scale |
| "AD already in DR" | True for PRIMARY regions; DR regions (us-east-2, us-west-1) not deployed |
