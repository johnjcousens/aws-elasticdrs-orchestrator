# AWS DRS Orchestration vs VMware SRM - Total Cost of Ownership Analysis

**Analysis Date**: November 2025  
**Comparison Period**: 3-Year Total Cost of Ownership  
**Environment Size**: 1,000 Virtual Machines  

---

## Executive Summary

### Bottom Line - 3-Year TCO (1,000 VMs)

<div class="compact-table">

| Solution | 3-Year TCO | Annual Avg | Staffing | Cost/VM/Year |
|----------|-----------|------------|----------|--------------|
| **VMware SRM** | **$10.2M** | **$3.4M** | **4 FTEs** | **$3,400** |
| **AWS DRS + Orch** | **$2.09M** | **$697K** | **1 FTE** | **$697** |
| **Savings** | **$8.11M (79%)** | **$2.7M** | **3 FTEs** | **$2,703** |

</div>

---

## Key Findings

**Capital Expenditure Elimination**:
- VMware: $3.5M upfront (Year 0)
- AWS: $0 CapEx (100% OpEx)
- **Savings**: $3.5M

**Annual Operating Cost Reduction**:
- VMware: $3.3M - $3.4M/year
- AWS: $697K/year
- **Savings**: $2.7M/year (79%)

---

## Key Findings (continued)

**Staffing Efficiency**:
- VMware: 4 FTEs ($620K/year)
- AWS: 1 FTE ($150K/year)
- **Savings**: 3 FTEs ($470K/year)

**Data Center Cost Elimination**:
- Power/cooling: $1.05M/year saved
- Rack space: $960K/year saved
- **Total**: $2.01M/year saved

---

## Year 0 - Capital Expenditure

### VMware SRM Initial Investment

<div class="compact-table">

| Component | Cost |
|-----------|------|
| **Compute** (80 ESXi hosts) | $1,200,000 |
| **Storage** (NetApp × 2 sites) | $1,000,000 |
| **Network** (switches, WAN) | $350,000 |
| **VMware Software** | $1,165,000 |
| **Total CapEx** | **$3,715,000** |

</div>

**AWS DRS**: $0 CapEx

---

## VMware SRM - Annual Operating Costs

<div class="small-table">

| Category | Annual Cost | % |
|----------|-------------|---|
| Data Center (power, cooling, space) | $2,111,200 | 62% |
| Staffing (4 FTEs) | $620,000 | 18% |
| Hardware Maintenance | $238,000 | 7% |
| Software Maintenance | $233,000 | 7% |
| Network/WAN | $168,000 | 5% |
| **Total Annual OpEx** | **$3,545,200** | **100%** |

</div>

---

## AWS DRS - Annual Operating Costs

<div class="small-table">

| Category | Annual Cost | % |
|----------|-------------|---|
| AWS DRS Service | $476,000 | 67% |
| Staffing (1 FTE) | $150,000 | 21% |
| AWS Enterprise Support | $48,000 | 7% |
| DR Testing | $15,000 | 2% |
| Compliance & Auditing | $10,000 | 1% |
| Monitoring Tools | $7,000 | 1% |
| Training & Certification | $6,000 | 1% |
| Orchestration Platform | $3,360 | <1% |
| **Total Annual OpEx** | **$715,360** | **100%** |

</div>

---

## 3-Year Cost Comparison

<div class="compact-table">

| Year | VMware SRM | AWS DRS | Savings | % |
|------|-----------|---------|---------|---|
| **Year 0** | $7,027,200 | $715,360 | $6,311,840 | 90% |
| **Year 1** | $3,312,200 | $715,360 | $2,596,840 | 78% |
| **Year 2** | $3,545,200 | $715,360 | $2,829,840 | 80% |
| **Year 3** | $3,545,200 | $715,360 | $2,829,840 | 80% |
| **Total** | **$17.4M** | **$2.9M** | **$14.6M** | **84%** |

</div>

*3-year period (Years 1-3): $10.2M vs $2.1M = 79% savings*

---

## Data Center Cost Breakdown

### VMware SRM Annual Facility Costs

<div class="compact-table">

| Category | Annual Cost |
|----------|-------------|
| Power Consumption (350,400 kWh) | $420,480 |
| Cooling/HVAC (1.5× power) | $630,720 |
| Rack Space Rental (80 racks) | $960,000 |
| Security & Monitoring | $50,000 |
| Physical Maintenance | $50,000 |
| **Total** | **$2,111,200** |

</div>

**AWS Solution**: $0 facility costs

---

## Staffing Comparison

### VMware SRM (4 FTEs = $620K/year)

<div class="compact-table">

| Role | Count | Annual Cost |
|------|-------|-------------|
| Sr Infrastructure Architect | 1 | $180,000 |
| VMware Systems Engineers | 2 | $300,000 |
| Storage Administrator | 1 | $140,000 |
| **Total** | **4** | **$620,000** |

</div>

### AWS DRS (1 FTE = $150K/year)

<div class="compact-table">

| Role | Count | Annual Cost |
|------|-------|-------------|
| DR Operations Engineer | 1 | $150,000 |
| **Total** | **1** | **$150,000** |

</div>

**Savings**: 75% reduction (3 FTEs, $470K/year)

---

## Storage Cost Analysis

### 3-Year Storage Comparison (75TB)

<div class="compact-table">

| Solution | 3-Year Total | Cost/TB | Cost/GB |
|----------|--------------|---------|---------|
| **NetApp FAS** | $1,405,000 | $18,733 | $18.27 |
| **AWS EBS** | $270,000 | $3,600 | $3.60 |
| **Savings** | **$1,135,000** | **81%** | **80%** |

</div>

**NetApp Includes**:
- Hardware: $800K (CapEx)
- Software: $100K (CapEx)
- Maintenance: $405K (3-year OpEx)

**AWS EBS Includes**:
- Staging storage: $216K
- Snapshots: $54K

---

## Scalability Analysis

### Adding 500 More VMs (1,500 Total)

<div class="compact-table">

| Solution | 3-Year Cost | Per VM Cost |
|----------|-------------|-------------|
| **VMware SRM** | $2,220,000 | $4,440 |
| **AWS DRS** | $684,000 | $1,368 |
| **Savings** | **$1,536,000** | **$3,072 (69%)** |

</div>

**VMware Requires**:
- 20 more hosts ($300K)
- Storage expansion ($250K)
- Network upgrades ($50K)
- Additional OpEx ($540K/year)

**AWS Requires**:
- Only incremental service costs
- No infrastructure investment
- Same 1 FTE manages 1,500 VMs

---

## ROI Analysis

### Cumulative Cost Comparison

<div class="compact-table">

| Year | VMware | AWS | Cumulative Savings |
|------|---------|-----|-------------------|
| Year 0 | $7.0M | $0.7M | $6.3M |
| Year 1 | $10.3M | $1.4M | $8.9M |
| Year 2 | $13.9M | $2.1M | $11.7M |
| Year 3 | $17.4M | $2.9M | $14.6M |

</div>

**Payback Period**: Immediate (no CapEx)
**5-Year Savings**: $14.3M (80%)

---

## Financial Impact Summary

<div class="compact-table">

| Metric | 3-Year Value |
|--------|--------------|
| **Total Cost Savings** | $8,071,320 (79%) |
| **CapEx Elimination** | $3,715,000 |
| **Annual OpEx Reduction** | $2,829,840 |
| **Labor Cost Savings** | $1,410,000 |
| **Data Center Savings** | $6,333,600 |

</div>

---

## AWS DRS Service Cost Breakdown

### Annual AWS DRS Costs ($476K/year)

<div class="small-table">

| Component | Monthly | Annual |
|-----------|---------|--------|
| Replication Servers (1,000 × $30) | $30,000 | $360,000 |
| EBS Staging Storage (75TB) | $6,000 | $72,000 |
| Point-in-Time Snapshots (30TB) | $1,500 | $18,000 |
| Data Transfer (Cross-Region) | $2,000 | $24,000 |
| Recovery Instance Testing | $167 | $2,000 |
| **Total AWS DRS** | **$39,667** | **$476,000** |

</div>

---

## Orchestration Platform Costs

### Annual Orchestration Costs ($3,360/year)

<div class="compact-table">

| Service | Annual Cost |
|---------|-------------|
| Lambda (Recovery Execution) | $1,200 |
| DynamoDB (3 Tables) | $600 |
| API Gateway (REST API) | $600 |
| CloudFront (CDN) | $240 |
| Cognito (Authentication) | $240 |
| CloudWatch (Logging) | $240 |
| S3 (Frontend Hosting) | $120 |
| CloudTrail (Audit) | $120 |
| **Total** | **$3,360** |

</div>

**Note**: 99.3% cheaper than VMware SRM license

---

## Decision Matrix

### Choose VMware SRM If:
- ✅ Already invested in VMware infrastructure
- ✅ On-premises compliance requirement
- ✅ Dedicated data center with capacity
- ⚠️ But: Broadcom licensing uncertainty

### Choose AWS DRS + Orchestration If:
- ✅ Want 79% cost reduction ($8M+ savings)
- ✅ Eliminate capital expenditure ($3.7M)
- ✅ Reduce staffing 75% (4 → 1 FTE)
- ✅ Avoid data center costs ($2M/year)
- ✅ Deploy in days vs months
- ✅ Elastic scaling capabilities
- ✅ Prefer managed services

---

## Recommendation

**For enterprises with 1,000+ VMs:**
## AWS DRS + Orchestration is the clear choice

**Why:**
1. **Financial**: 79% cost reduction ($8M+ over 3 years)
2. **Operational**: 75% staff reduction (4 → 1 FTE)
3. **Strategic**: Eliminate vendor lock-in
4. **Technical**: Cloud-native architecture
5. **Scalability**: Linear vs exponential costs

---

## Implementation Roadmap

### Phase 1: Pilot (Months 1-2)
- Migrate 50-100 non-critical VMs
- Train DR operations engineer
- Validate recovery procedures

### Phase 2: Migration (Months 3-6)
- Migrate 250-300 VMs/month
- Parallel run with VMware SRM
- Continuous drill testing

### Phase 3: Production (Months 7-9)
- Complete migration
- Decommission VMware SRM
- Realize full cost savings

---

## Key Takeaways

**Financial**:
- 💰 **$8.1M savings** over 3 years (79%)
- 💵 **$3.7M CapEx** elimination (Year 0)
- 📉 **$2.8M/year OpEx** reduction

**Operational**:
- 👥 **75% staffing** reduction (4 → 1 FTE)
- 🏢 **100% facility** cost elimination
- ⚡ **Zero capital** investment required

**Strategic**:
- 🚀 Deploy in **days vs months**
- 📈 **Elastic scaling** with linear costs
- 🔒 Escape **vendor lock-in**

---

## Questions?

**Complete TCO Analysis Available**
- Detailed cost breakdowns
- Methodology and assumptions
- Industry benchmarks
- 5-year extended analysis

**Contact Information**:
- Technical questions
- Implementation planning
- Cost modeling support

---

# Thank You

**AWS DRS Orchestration**
*Enterprise DR at 79% Lower Cost*

---
