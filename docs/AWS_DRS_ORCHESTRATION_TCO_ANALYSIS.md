# AWS DRS Orchestration vs VMware SRM - Total Cost of Ownership Analysis

**Analysis Date**: November 2025  
**Comparison Period**: 3-Year Total Cost of Ownership  
**Environment Size**: 1,000 Virtual Machines  
**Purpose**: Comprehensive cost comparison for enterprise disaster recovery solutions

---

## Executive Summary

### Bottom Line

| Solution | 3-Year TCO | Annual Avg Cost | Staffing Required | Cost per VM/Year |
|----------|-----------|-----------------|-------------------|------------------|
| **VMware SRM On-Premises** | **$10.2M** | **$3.4M** | **4 FTEs** | **$3,400** |
| **AWS DRS + Orchestration** | **$2.09M** | **$697K** | **1 FTE** | **$697** |
| **Savings** | **$8.11M (79%)** | **$2.7M/year** | **3 FTEs** | **$2,703 (79%)** |

### Key Findings

**Capital Expenditure Elimination**:
- VMware solution requires $3.5M upfront (Year 0) for hardware and software
- AWS solution has zero CapEx - all OpEx model
- **CapEx Avoidance**: $3.5M

**Annual Operating Cost Reduction**:
- VMware: $3.3M - $3.4M per year (data center, staff, maintenance)
- AWS: $697K per year (service costs, support, 1 FTE)
- **Annual OpEx Savings**: $2.7M (79% reduction)

**Staffing Efficiency**:
- VMware: 4 dedicated FTEs for infrastructure and DR operations
- AWS: 1 FTE for DR coordination and solution management
- **Labor Savings**: 3 FTEs ($450K/year)

**Data Center Cost Elimination**:
- No power consumption ($420K/year saved)
- No cooling infrastructure ($630K/year saved)
- No rack space rental ($960K/year saved)
- **Facilities Savings**: $2.01M/year

---

## VMware SRM On-Premises - Complete Cost Breakdown

### Assumptions

- **Deployment Model**: Active-Active (Primary + DR sites)
- **VM Count**: 1,000 VMs total
- **VM Density**: 25 VMs per ESXi host
- **Storage per VM**: 75GB average
- **Total Storage**: 75TB per site (150TB with overhead)
- **Host Count**: 40 hosts per site × 2 sites = 80 total hosts
- **Time Period**: 3-year TCO analysis

---

## Year 0 - Capital Expenditure (CapEx)

### 1. Compute Infrastructure

**ESXi Host Specifications** (80 hosts total):
- Dual Intel Xeon Scalable processors (32 cores/socket)
- 512GB RAM per host
- Dual 10GbE network adapters
- Redundant power supplies
- Rack mounting hardware

**Cost Breakdown**:
- Hardware cost per host: $15,000
- 80 hosts × $15,000 = **$1,200,000**

### 2. Storage Infrastructure

**NetApp FAS Arrays**:

**Primary Site**:
- NetApp FAS8300 HA pair
- 150TB usable capacity (with RAID overhead)
- All-flash configuration
- Redundant controllers
- **Cost**: $400,000

**DR Site**:
- NetApp FAS8300 HA pair (matching config)
- 150TB usable capacity
- All-flash configuration
- **Cost**: $400,000

**NetApp Software Licenses**:
- SnapMirror replication (both sites): $50,000
- Data protection suite: $30,000
- Management tools: $20,000
- **Total NetApp Software**: $100,000

**Storage Networking**:
- Fiber Channel switches (8 total): $80,000
- Fiber Channel cables and SFPs: $20,000
- **Total Storage Network**: $100,000

**Total Storage Infrastructure**: **$1,000,000**

### 3. Network Infrastructure

**Core Network Equipment**:
- Core switches (4 total): $120,000
- Routers (4 total): $80,000
- Network security appliances: $50,000
- Cabling and installation: $30,000
- **Total Network**: $280,000

**WAN Infrastructure**:
- WAN acceleration appliances (2): $60,000
- Installation and configuration: $10,000
- **Total WAN**: $70,000

**Total Network Infrastructure**: **$350,000**

### 4. VMware Software Licenses

**vSphere Enterprise Plus**:
- 160 CPU licenses (80 hosts × 2 sockets)
- Cost per CPU: $4,500
- **Subtotal**: $720,000

**vCenter Server Standard**:
- 2 instances (primary + DR)
- Cost per instance: $6,000
- **Subtotal**: $12,000

**VMware Site Recovery Manager (SRM) Enterprise**:
- 1,000 VM licenses
- Cost per VM: $200
- **Subtotal**: $200,000

**Year 1 Support & Maintenance** (25% of license cost):
- Support cost: $233,000
- **Subtotal**: $233,000

**Total VMware Software (Year 1)**: **$1,165,000**

### Year 0 Total Capital Expenditure: **$3,715,000**

---

## Annual Operating Expenditure (OpEx)

### 1. Data Center Costs

**Power Consumption**:
- 80 hosts × 500W average load = 40kW
- Annual consumption: 40kW × 8,760 hours = 350,400 kWh
- Cost at $0.12/kWh: **$420,480/year**

**Cooling (HVAC)**:
- Cooling requirement: 1.5× power consumption
- Additional power for cooling: 60kW × 8,760 hours
- Cost at $0.12/kWh: **$630,720/year**

**Rack Space Rental**:
- 80 full racks required (hosts, storage, network)
- Cost per rack: $1,000/month
- Annual cost: 80 × $12,000 = **$960,000/year**

**Facilities Overhead**:
- Physical security systems
- Environmental monitoring
- Fire suppression systems
- Building maintenance allocation
- **Estimated**: $100,000/year

**Total Data Center Costs**: **$2,111,200/year**

### 2. Network & Bandwidth Costs

**WAN Circuit (Primary to DR)**:
- Dedicated 10Gbps circuit
- Monthly cost: $10,000
- **Annual cost**: $120,000/year

**Internet Connectivity**:
- Primary site: $2,000/month
- DR site: $2,000/month
- **Annual cost**: $48,000/year

**Total Network Costs**: **$168,000/year**

### 3. Staffing Costs

**Required Personnel** (4 FTEs):

1. **Senior Infrastructure Architect** (1 FTE)
   - VMware infrastructure design
   - DR architecture and planning
   - Capacity planning
   - Salary + benefits: $180,000/year

2. **VMware Systems Engineers** (2 FTEs)
   - ESXi host management
   - vCenter administration
   - SRM configuration and testing
   - Patch management
   - Salary + benefits: $150,000/year each = $300,000/year

3. **Storage Administrator** (1 FTE)
   - NetApp array management
   - SnapMirror replication
   - Performance tuning
   - Backup coordination
   - Salary + benefits: $140,000/year

**Total Staffing Costs**: **$620,000/year**

### 4. Hardware Maintenance & Support

**Server Hardware Maintenance**:
- 5% of hardware cost annually
- $1,200,000 × 5% = **$60,000/year**

**Storage Hardware Maintenance**:
- NetApp support (15% annually)
- $1,000,000 × 15% = **$150,000/year**

**Network Equipment Maintenance**:
- 8% of network hardware annually
- $350,000 × 8% = **$28,000/year**

**Total Hardware Maintenance**: **$238,000/year**

### 5. VMware Software Maintenance

**Annual Support & Subscription** (Years 2-3):
- 25% of license costs annually
- $932,000 × 25% = **$233,000/year**

*Note: Year 1 support included in CapEx*

### 6. DR Testing & Validation Costs

**Quarterly DR Drills**:
- Staff time (4 FTEs × 16 hours × 4 drills)
- External consultants for validation
- Report generation and documentation
- **Estimated**: $40,000/year

**Annual Comprehensive Testing**:
- Full failover test
- Application validation
- Performance benchmarking
- **Estimated**: $20,000/year

**Total DR Testing**: **$60,000/year**

### 7. Training & Professional Development

**VMware Certification**:
- VCP certifications (2 engineers): $8,000/year
- VCAP advanced training (1 engineer): $6,000/year

**NetApp Training**:
- Storage administration courses: $4,000/year

**SRM Specialized Training**:
- Annual updates and best practices: $7,000/year

**Total Training**: **$25,000/year**

### 8. Operational Overhead

**Backup Software & Management**:
- Backup software for 80 hosts
- **Estimated**: $30,000/year

**Monitoring & Management Tools**:
- vRealize Operations Suite
- Log aggregation tools
- Performance monitoring
- **Estimated**: $40,000/year

**Compliance & Auditing**:
- Annual compliance reviews
- Security assessments
- Documentation maintenance
- **Estimated**: $20,000/year

**Total Operational Overhead**: **$90,000/year**

---

## VMware SRM 3-Year Total Cost

| Year | CapEx | OpEx | Annual Total |
|------|-------|------|--------------|
| **Year 0** | $3,715,000 | $3,312,200 | **$7,027,200** |
| **Year 1** | $0 | $3,312,200 | **$3,312,200** |
| **Year 2** | $0 | $3,545,200* | **$3,545,200** |
| **Year 3** | $0 | $3,545,200* | **$3,545,200** |
| **3-Year Total** | **$3,715,000** | **$6,502,400** | **$10,217,400** |

*Includes software maintenance starting Year 2

### Annual OpEx Breakdown Summary

| Category | Annual Cost | % of Total |
|----------|-------------|------------|
| Data Center (power, cooling, space) | $2,111,200 | 62% |
| Staffing (4 FTEs) | $620,000 | 18% |
| Hardware Maintenance | $238,000 | 7% |
| Software Maintenance | $233,000 | 7% |
| Network/WAN | $168,000 | 5% |
| Operational Overhead | $90,000 | 3% |
| DR Testing | $60,000 | 2% |
| Training | $25,000 | 1% |
| **Total Annual OpEx** | **$3,545,200** | **100%** |

---

## AWS DRS + Orchestration - Complete Cost Breakdown

### Assumptions

- **Deployment Model**: AWS DRS with Serverless Orchestration
- **VM Count**: 1,000 source servers
- **Storage per VM**: 75GB average
- **Total Replication Storage**: 75TB
- **AWS Region**: us-east-1 (Primary) to us-west-2 (DR)
- **Time Period**: 3-year TCO analysis

---

## Annual Operating Costs

### 1. AWS DRS Service Costs

**Replication Servers**:
- 1,000 replication servers
- Average cost: $30/month per server
- **Annual cost**: $360,000/year

**EBS Staging Storage**:
- 1,000 servers × 75GB = 75TB
- EBS gp3 storage: $0.08/GB-month
- Monthly: 75,000GB × $0.08 = $6,000
- **Annual cost**: $72,000/year

**Data Transfer (Cross-Region)**:
- Continuous replication bandwidth
- Estimated: $2,000/month
- **Annual cost**: $24,000/year

**Point-in-Time Snapshots**:
- EBS snapshots for recovery points
- Incremental snapshot storage: $0.05/GB-month
- Estimated average: 30TB snapshots
- Monthly: 30,000GB × $0.05 = $1,500
- **Annual cost**: $18,000/year

**Recovery Instance Costs** (Drill testing):
- Monthly drill: 1,000 instances × 4 hours
- Average instance: t3.medium ($0.0416/hour)
- Monthly: 1,000 × 4 × $0.0416 = $166
- **Annual cost**: $2,000/year

**AWS DRS Total**: **$476,000/year**

### 2. Orchestration Platform Costs

**Lambda (Recovery Execution)**:
- 100 invocations/month (testing + production)
- Average duration: 2 minutes per invocation
- Cost: $0.20/million requests + compute time
- **Annual cost**: $1,200/year

**DynamoDB (3 Tables)**:
- On-demand pricing
- Recovery plans, protection groups, execution history
- Average: $50/month
- **Annual cost**: $600/year

**API Gateway (REST API)**:
- 10,000 API calls/month
- $3.50 per million calls
- **Annual cost**: $600/year

**CloudFront (CDN)**:
- Frontend distribution
- 100GB data transfer/month
- **Annual cost**: $240/year

**S3 (Frontend Hosting)**:
- Static website hosting
- 10GB storage + requests
- **Annual cost**: $120/year

**Cognito (Authentication)**:
- User pool for 50 users
- $20/month
- **Annual cost**: $240/year

**CloudWatch (Logging)**:
- Log ingestion and retention
- 10GB logs/month
- **Annual cost**: $240/year

**CloudTrail (Audit)**:
- Event logging and retention
- Management events only
- **Annual cost**: $120/year

**Orchestration Total**: **$3,360/year**

### 3. AWS Enterprise Support

**Enterprise Support Tier**:
- 10% of AWS monthly spend
- Based on DRS + Orchestration costs
- Average monthly: $40,000
- **Annual cost**: $48,000/year

**Included Services**:
- 24/7 technical support
- <15 minute response for critical issues
- Technical Account Manager (TAM)
- Infrastructure Event Management
- Well-Architected reviews
- Operational reviews

### 4. Staffing Costs

**DR Operations Engineer** (1 FTE):
- Solution administration and monitoring
- DR drill coordination and execution
- Runbook maintenance and updates
- CloudWatch alert response
- Recovery plan optimization
- Executive reporting
- **Salary + benefits**: $150,000/year

**Responsibilities**:
- Manage AWS DRS replication
- Maintain orchestration platform
- Execute monthly DR drills
- Coordinate with application teams
- Update recovery procedures
- Handle escalations

**Efficiency Gain**:
- 75% reduction vs VMware (1 FTE vs 4 FTEs)
- No hardware infrastructure to manage
- No patching/upgrade cycles
- Automated failover testing
- Serverless auto-scaling

### 5. DR Testing & Validation Costs

**Monthly DR Drills**:
- 1,000 test instances × 4 hours
- Instance costs (included in DRS costs above)
- Staff validation time (included in 1 FTE above)
- **Additional cost**: $0 (included above)

**Annual Comprehensive Testing**:
- Full application validation
- Performance benchmarking
- External audit support
- **Estimated**: $10,000/year

**Test Automation**:
- SSM document development
- CloudWatch synthetic monitoring
- Lambda test orchestration
- **Estimated**: $5,000/year

**Total DR Testing**: **$15,000/year**

### 6. Training & Certification

**AWS Certification**:
- AWS Certified Solutions Architect: $300
- AWS Certified DevOps Engineer: $300
- **Annual recertification**: $600/year

**AWS Training**:
- AWS DR best practices courses: $2,000/year
- DRS deep-dive workshops: $1,500/year
- **Total training**: $3,500/year

**Conference Attendance**:
- AWS re:Invent or Summit: $2,500/year

**Total Training & Certification**: **$6,000/year**

### 7. Monitoring & Management Tools

**Enhanced Monitoring**:
- CloudWatch Container Insights: $1,200/year
- CloudWatch Contributor Insights: $800/year
- **CloudWatch Enhanced**: $2,000/year

**Third-Party Monitoring** (Optional):
- Datadog or New Relic integration
- Application performance monitoring
- **Estimated**: $5,000/year

**Total Monitoring**: **$7,000/year**

### 8. Compliance & Auditing

**Compliance Tools**:
- AWS Config rules: $1,200/year
- Security Hub assessments: $800/year
- **Compliance subtotal**: $2,000/year

**External Audits**:
- Annual DR capability review
- SOC2/ISO compliance validation
- **Estimated**: $8,000/year

**Total Compliance**: **$10,000/year**

---

## AWS DRS + Orchestration 3-Year Total Cost

| Year | CapEx | OpEx | Annual Total |
|------|-------|------|--------------|
| **Year 1** | $0 | $715,360 | **$715,360** |
| **Year 2** | $0 | $715,360 | **$715,360** |
| **Year 3** | $0 | $715,360 | **$715,360** |
| **3-Year Total** | **$0** | **$2,146,080** | **$2,146,080** |

### Annual OpEx Breakdown Summary

| Category | Annual Cost | % of Total |
|----------|-------------|------------|
| AWS DRS Service | $476,000 | 67% |
| Staffing (1 FTE) | $150,000 | 21% |
| AWS Enterprise Support | $48,000 | 7% |
| DR Testing | $15,000 | 2% |
| Compliance & Auditing | $10,000 | 1% |
| Monitoring Tools | $7,000 | 1% |
| Training & Certification | $6,000 | 1% |
| Orchestration Platform | $3,360 | <1% |
| **Total Annual OpEx** | **$715,360** | **100%** |

---

## Side-by-Side Comparison

### 3-Year Total Cost of Ownership

| Solution | Year 0 | Year 1 | Year 2 | Year 3 | **3-Year Total** |
|----------|--------|--------|--------|--------|------------------|
| **VMware SRM** | $7,027,200 | $3,312,200 | $3,545,200 | $3,545,200 | **$10,217,400** |
| **AWS DRS + Orch** | $715,360 | $715,360 | $715,360 | $715,360 | **$2,146,080** |
| **Savings** | $6,311,840 | $2,596,840 | $2,829,840 | $2,829,840 | **$8,071,320** |
| **% Savings** | 90% | 78% | 80% | 80% | **79%** |

### Capital vs Operating Expenditure

| Solution | Total CapEx | Total OpEx | CapEx % | OpEx % |
|----------|-------------|------------|---------|--------|
| **VMware SRM** | $3,715,000 | $6,502,400 | 36% | 64% |
| **AWS DRS + Orch** | $0 | $2,146,080 | 0% | 100% |

**Key Insight**: AWS solution eliminates all capital expenditure, converting to predictable OpEx model.

### Annual Cost Comparison by Category

| Cost Category | VMware Annual | AWS Annual | Savings | % Savings |
|---------------|---------------|------------|---------|-----------|
| **Infrastructure** | $2,349,200 | $0 | $2,349,200 | 100% |
| **Service Costs** | $0 | $479,360 | -$479,360 | N/A |
| **Staffing** | $620,000 | $150,000 | $470,000 | 76% |
| **Support/Maint** | $471,000 | $48,000 | $423,000 | 90% |
| **DR Testing** | $60,000 | $15,000 | $45,000 | 75% |
| **Training** | $25,000 | $6,000 | $19,000 | 76% |
| **Other** | $20,000 | $17,000 | $3,000 | 15% |
| **Total Annual** | **$3,545,200** | **$715,360** | **$2,829,840** | **80%** |

### Per-VM Economics

| Metric | VMware SRM | AWS DRS + Orch | Savings |
|--------|-----------|----------------|---------|
| **Annual Cost/VM** | $3,545 | $715 | $2,830 (80%) |
| **3-Year Cost/VM** | $10,217 | $2,146 | $8,071 (79%) |
| **Monthly Cost/VM** | $295 | $60 | $236 (80%) |

---

## Storage Cost Analysis: NetApp vs AWS EBS

### NetApp FAS On-Premises Storage

**Hardware Costs**:
- Primary site FAS8300: $400,000
- DR site FAS8300: $400,000
- **Total Hardware**: $800,000

**Software Costs**:
- SnapMirror license: $50,000
- Data protection suite: $30,000
- Management tools: $20,000
- **Total Software**: $100,000

**Annual Maintenance**:
- 15% of hardware + software annually
- ($900,000 × 15%) = $135,000/year

**Storage Networking**:
- Fiber Channel switches: $80,000
- Cables and SFPs: $20,000
- **Total Storage Network**: $100,000

**NetApp 3-Year Total**:
- Year 0: $1,000,000 (CapEx)
- Years 1-3: $135,000/year (OpEx) = $405,000
- **3-Year Total**: $1,405,000
- **Cost per TB**: $18,733/TB (75TB usable)
- **Cost per GB (3-year)**: $18.27/GB

### AWS EBS Replication Storage

**Staging Storage** (75TB):
- EBS gp3 storage: $0.08/GB-month
- Monthly: 75,000GB × $0.08 = $6,000
- Annual: $72,000
- **3-Year Total**: $216,000

**Snapshot Storage** (30TB average):
- EBS snapshots: $0.05/GB-month
- Monthly: 30,000GB × $0.05 = $1,500
- Annual: $18,000
- **3-Year Total**: $54,000

**AWS EBS 3-Year Total**: $270,000
- **Cost per TB**: $3,600/TB (75TB staging)
- **Cost per GB (3-year)**: $3.60/GB

### Storage Cost Comparison

| Metric | NetApp FAS | AWS EBS | Savings |
|--------|-----------|----------|---------|
| **3-Year Total** | $1,405,000 | $270,000 | $1,135,000 (81%) |
| **Cost per TB** | $18,733/TB | $3,600/TB | $15,133 (81%) |
| **Cost per GB** | $18.27/GB | $3.60/GB | $14.67 (80%) |
| **Annual Cost** | $541,667 | $90,000 | $451,667 (83%) |

**Key Advantages - AWS EBS**:
- ✅ No upfront hardware costs
- ✅ No maintenance contracts
- ✅ Automatic scaling
- ✅ Pay-as-you-go pricing
- ✅ Built-in replication
- ✅ No storage networking required

**NetApp Advantages**:
- ⚠️ Requires upfront capital
- ⚠️ Fixed capacity (overprovisioning)
- ⚠️ Maintenance and upgrade cycles
- ⚠️ Physical infrastructure management
- ⚠️ Storage networking complexity

---

## Data Center Cost Elimination

### VMware SRM Data Center Requirements

**Physical Footprint**:
- 80 full racks (40 per site)
- 2 data center facilities
- Redundant power and cooling

**Annual Facility Costs**:
| Category | Annual Cost |
|----------|-------------|
| Power consumption | $420,480 |
| Cooling (HVAC) | $630,720 |
| Rack space rental | $960,000 |
| Security & monitoring | $50,000 |
| Physical maintenance | $50,000 |
| **Total Facility** | **$2,111,200/year** |

**3-Year Facility Costs**: $6,333,600

### AWS Solution - Zero Facility Costs

**What's Eliminated**:
- ✅ No power consumption
- ✅ No cooling infrastructure
- ✅ No rack space requirements
- ✅ No physical security
- ✅ No facility maintenance
- ✅ No real estate footprint

**3-Year Facility Savings**: **$6,333,600**

---

## Staffing & Operations Comparison

### VMware SRM Staffing (4 FTEs)

| Role | Count | Salary | Responsibilities |
|------|-------|--------|-----------------|
| **Sr Infrastructure Architect** | 1 | $180K | Architecture, capacity planning, DR design |
| **VMware Systems Engineers** | 2 | $300K | ESXi, vCenter, SRM, patching |
| **Storage Administrator** | 1 | $140K | NetApp, SnapMirror, performance |
| **Total** | **4** | **$620K/year** | Full infrastructure management |

**Time Allocation**:
- Infrastructure maintenance: 40%
- Hardware troubleshooting: 20%
- Patching and upgrades: 15%
- DR testing and coordination: 15%
- Capacity planning: 10%

**3-Year Staffing Cost**: $1,860,000

### AWS DRS Staffing (1 FTE)

| Role | Count | Salary | Responsibilities |
|------|-------|--------|-----------------|
| **DR Operations Engineer** | 1 | $150K | DR coordination, testing, monitoring |
| **Total** | **1** | **$150K/year** | Solution management only |

**Time Allocation**:
- DR drill coordination: 30%
- Monitoring and alerts: 25%
- Recovery plan optimization: 20%
- Reporting and documentation: 15%
- Training and process improvement: 10%

**3-Year Staffing Cost**: $450,000

### Staffing Efficiency Gains

| Metric | VMware | AWS | Improvement |
|--------|--------|-----|-------------|
| **FTE Count** | 4 | 1 | 75% reduction |
| **Annual Cost** | $620K | $150K | 76% savings |
| **3-Year Cost** | $1,860K | $450K | $1,410K saved |
| **Infrastructure Focus** | 75% | 0% | No infrastructure mgmt |
| **DR Focus** | 25% | 100% | 4× DR focus |

**Key Efficiency Drivers**:
- ✅ No hardware to manage
- ✅ No patching cycles
- ✅ Automated scaling
- ✅ Self-healing infrastructure
- ✅ Simplified testing

---

## Return on Investment (ROI) Analysis

### Investment Comparison

**VMware SRM**:
- Year 0 investment: $7,027,200
- Annual operating cost: $3,312,200 (Year 1), $3,545,200 (Years 2-3)
- 3-year total: $10,217,400

**AWS DRS + Orchestration**:
- Year 0 investment: $715,360 (no CapEx)
- Annual operating cost: $715,360 (consistent)
- 3-year total: $2,146,080

### Cumulative Cost Comparison

| Year | VMware Cumulative | AWS Cumulative | Cumulative Savings |
|------|-------------------|----------------|-------------------|
| **Year 0** | $7,027,200 | $715,360 | $6,311,840 |
| **Year 1** | $10,339,400 | $1,430,720 | $8,908,680 |
| **Year 2** | $13,884,600 | $2,146,080 | $11,738,520 |
| **Year 3** | $17,429,800 | $2,861,440 | $14,568,360 |

### Break-Even Analysis

**Immediate Return**:
- AWS solution has positive ROI from Month 1
- No capital investment required
- $6.3M CapEx avoidance in Year 0

**Payback Period**: Immediate (no upfront investment)

**5-Year Extended Analysis**:
| Solution | 5-Year Total |
|----------|--------------|
| VMware SRM | $17,888,200 |
| AWS DRS + Orchestration | $3,576,800 |
| **5-Year Savings** | **$14,311,400 (80%)** |

### Financial Impact Summary

| Metric | Value | Notes |
|--------|-------|-------|
| **3-Year Savings** | $8,071,320 | 79% cost reduction |
| **Year 0 CapEx Avoidance** | $3,715,000 | Immediate cash preservation |
| **Annual OpEx Savings** | $2,829,840 | Starting Year 2 |
| **Labor Savings** | $1,410,000 | 3 FTEs over 3 years |
| **Facility Savings** | $6,333,600 | Data center elimination |
| **ROI** | Immediate | No upfront investment |
| **Payback Period** | 0 months | OpEx model |

---

## Risk & Hidden Costs Analysis

### VMware SRM Hidden Costs

**Hardware Refresh (Year 4-5)**:
- Servers reaching end-of-life
- Estimated refresh cost: $1.5M - $2M
- Technology obsolescence risk

**Broadcom Acquisition Impact**:
- VMware licensing uncertainty
- Potential 200-400% price increases
- Bundle requirements (forced purchases)
- Support model changes

**Capacity Overprovisioning**:
- Must size for peak + growth (typically 40% overhead)
- Unused capacity = wasted investment
- Difficult to scale down

**Shadow IT Costs**:
- Undocumented labor hours
- Emergency troubleshooting
- Weekend maintenance windows
- Performance optimization efforts

**Estimated Hidden Costs**: $500K - $1M over 3 years

### AWS DRS Hidden Benefits

**Automatic Scaling**:
- Pay only for what you use
- Scale up/down instantly
- No overprovisioning required

**Managed Services**:
- AWS handles infrastructure
- Automatic patching and updates
- Built-in monitoring
- Security compliance maintained by AWS

**Rapid Innovation**:
- New features released regularly
- No upgrade cycles required
- Instant access to improvements

---

## Scalability Analysis

### VMware SRM Scaling Costs

**Adding 500 More VMs** (Total: 1,500 VMs):

**Additional Infrastructure**:
- 20 more ESXi hosts: $300,000
- Storage expansion (37.5TB): $250,000
- Network upgrades: $50,000
- **Additional CapEx**: $600,000

**Additional OpEx**:
- Power & cooling: +$210K/year
- Rack space: +$240K/year
- Maintenance: +$90K/year
- **Additional OpEx**: +$540K/year

**Total Marginal Cost** (3-year):
- CapEx: $600,000
- OpEx: $1,620,000
- **Total**: $2,220,000
- **Cost per additional VM**: $4,440

### AWS DRS Scaling Costs

**Adding 500 More VMs** (Total: 1,500 VMs):

**Additional AWS DRS**:
- 500 replication servers × $30/month = +$180K/year
- Storage (37.5TB) = +$36K/year
- Data transfer = +$12K/year
- **Additional Annual Cost**: +$228K/year

**Staffing**:
- Same 1 FTE can manage 1,500 VMs
- No additional headcount required

**Total Marginal Cost** (3-year):
- **Total**: $684,000
- **Cost per additional VM**: $1,368

**Scaling Efficiency**: AWS is 69% cheaper per additional VM

---

## Decision Matrix

### When to Choose VMware SRM

**Consider VMware SRM if**:
- ✅ Already heavily invested in VMware infrastructure
- ✅ On-premises requirement due to compliance/regulations
- ✅ Dedicated data center with excess capacity
- ✅ Existing VMware expertise and staff
- ❌ But be prepared for Broadcom licensing changes

### When to Choose AWS DRS + Orchestration

**Choose AWS DRS + Orchestration if**:
- ✅ Want to eliminate capital expenditure
- ✅ Need predictable OpEx model
- ✅ Want to reduce staffing requirements (75% reduction)
- ✅ Desire faster deployment (days vs months)
- ✅ Need elastic scaling capabilities
- ✅ Want to avoid data center costs
- ✅ Prefer managed services over infrastructure
- ✅ Seeking 79% cost reduction over 3 years

---

## Summary & Recommendations

### Key Takeaways

**Financial Impact**:
| Metric | 3-Year Value |
|--------|--------------|
| Total Cost Savings | $8,071,320 (79%) |
| CapEx Elimination | $3,715,000 |
| Annual OpEx Reduction | $2,829,840 |
| Labor Cost Savings | $1,410,000 |
| Data Center Savings | $6,333,600 |

**Operational Benefits**:
- **75% staffing reduction** (4 FTEs → 1 FTE)
- **Zero capital investment** (100% OpEx model)
- **100% facility cost elimination**
- **Immediate deployment** (days vs months)
- **Elastic scalability** (no overprovisioning)
- **Managed infrastructure** (no patching, no hardware)

**Strategic Value**:
- Escape VMware/Broadcom licensing uncertainty
- Future-proof architecture with cloud-native design
- Competitive advantage through cost leadership
- Faster disaster recovery capabilities
- Simplified compliance and auditing

### Our Recommendation

**For enterprises with 1,000+ VMs: AWS DRS + Orchestration is the clear choice.**

**Rationale**:
1. **Financial**: 79% cost reduction ($8M+ savings over 3 years)
2. **Operational**: 75% reduction in required staff
3. **Strategic**: Elimination of vendor lock-in and capital risk
4. **Technical**: Cloud-native architecture with modern capabilities
5. **Scalability**: Linear cost model vs exponential on-premises costs

### Implementation Approach

**Phase 1: Pilot (Month 1-2)**
- Start with 50-100 non-critical VMs
- Validate replication and recovery
- Train 1 DR operations engineer
- Conduct initial drill testing

**Phase 2: Migration (Month 3-6)**
- Migrate 250-300 VMs per month
- Parallel run with existing VMware SRM
- Continuous drill testing
- Refine runbooks and procedures

**Phase 3: Full Production (Month 7-9)**
- Complete migration to AWS DRS
- Decommission VMware SRM infrastructure
- Realize full cost savings
- Establish quarterly DR drill cadence

**Phase 4: Optimization (Month 10-12)**
- Fine-tune recovery plans
- Implement automation enhancements
- Review and optimize costs
- Document lessons learned

---

## Appendix A: Cost Calculation Methodology

### VMware SRM Costs

**Hardware Sizing**:
- VM density: 25 VMs per ESXi host (industry standard)
- Storage per VM: 75GB average
- Host specifications: Dual-socket, 512GB RAM
- Redundant infrastructure at both sites

**Data Center Costs**:
- Power: $0.12/kWh (US average)
- Server power draw: 500W average load
- Cooling multiplier: 1.5× (industry standard)
- Rack rental: $1,000/month (enterprise colocation)

**Staffing**:
- Fully loaded cost: Salary + 40% (benefits, taxes, overhead)
- Based on market rates for VMware/storage engineers
- 4 FTEs required for 24/7 infrastructure support

**Maintenance**:
- Hardware: 5-8% annually (manufacturer contracts)
- Software: 25% annually (VMware standard)
- NetApp storage: 15% annually (includes support)

### AWS DRS Costs

**Service Pricing**:
- Based on AWS public pricing (us-east-1, November 2025)
- DRS replication: $30/server/month
- EBS storage: $0.08/GB-month (gp3)
- EBS snapshots: $0.05/GB-month (incremental)
- Data transfer: Cross-region pricing

**Staffing**:
- 1 FTE DR operations engineer
- Focus on DR coordination, not infrastructure
- Fully loaded cost: $150K (salary + benefits)

**Support**:
- AWS Enterprise Support: 10% of monthly spend
- Includes TAM, 24/7 support, <15min response

### Industry Sources

- VMware/Broadcom pricing: Public rate cards + enterprise discounts
- NetApp pricing: Industry benchmarks and analyst reports
- Data center costs: Uptime Institute, IDC research
- AWS pricing: Public AWS pricing calculator
- Staffing costs: Glassdoor, Salary.com, market research

---

## Appendix B: Glossary

**CapEx** (Capital Expenditure): Upfront costs for physical assets (servers, storage, network equipment)

**OpEx** (Operating Expenditure): Ongoing operational costs (power, staff, maintenance, subscriptions)

**TCO** (Total Cost of Ownership): Complete cost over specified period including CapEx, OpEx, and hidden costs

**FTE** (Full-Time Equivalent): One full-time employee (40 hours/week, 52 weeks/year)

**RTO** (Recovery Time Objective): Maximum acceptable time to restore service after disaster

**RPO** (Recovery Point Objective): Maximum acceptable data loss measured in time

**DR** (Disaster Recovery): Processes and infrastructure for recovering IT systems after failure

**DRS** (Disaster Recovery Service): AWS Elastic Disaster Recovery service

**SRM** (Site Recovery Manager): VMware's disaster recovery orchestration solution

**SnapMirror**: NetApp's block-level replication technology

**ESXi**: VMware's bare-metal hypervisor

**vCenter**: VMware's centralized management platform

---

## Appendix C: Assumptions & Constraints

### Key Assumptions

**Environment**:
- 1,000 VMs to be protected
- 75GB average storage per VM
- Active-Active deployment (Primary + DR sites)
- Cross-region replication (us-east-1 ↔ us-west-2)

**Timeline**:
- 3-year TCO analysis
- Year 0 includes initial CapEx
- Years 1-3 include operational costs

**Scaling**:
- 25 VMs per ESXi host (VMware)
- No overprovisioning in AWS (pay for actual usage)

**Financial**:
- Conservative cost estimates
- Market-rate salaries for staff
- Enterprise pricing for software/hardware
- No special discounts applied

### Constraints & Limitations

**VMware SRM**:
- Assumes owned/leased data center space
- Does not include disaster recovery site construction
- Assumes enterprise software agreements
- Hardware refresh not included (Year 4+)

**AWS DRS**:
- Does not include source server costs (AWS EC2 or on-premises)
- Assumes standard AWS pricing (no private pricing)
- Enterprise support included for fair comparison
- Cross-account recovery not included

**Excluded Costs**:
- Application licensing
- WAN circuits to AWS Direct Connect
- Disaster recovery testing tools
- Change management overhead
- Training for application teams

---

## Document Control

**Version**: 1.0  
**Date**: November 23, 2025  
**Author**: AWS DRS Orchestration Team  
**Status**: Final  

**Review History**:
- v1.0 (Nov 23, 2025): Initial comprehensive TCO analysis

**Related Documents**:
- AWS DRS Orchestration Architecture Design
- Disaster Recovery Solutions Sales Battlecard
- Yearly Review Presentation
- Implementation and Deployment Guide

---

*This TCO analysis provides a comprehensive financial comparison between traditional on-premises VMware SRM and cloud-native AWS DRS with orchestration for enterprise disaster recovery at scale. All costs are based on industry-standard pricing and conservative estimates to ensure accurate financial planning.*
