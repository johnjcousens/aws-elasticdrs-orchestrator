ba# HRP Disaster Recovery Technical Architecture

**Document Version:** 1.0  
**Last Updated:** January 20, 2026  
**Source:** HRP Confluence DR Documentation Analysis

## Executive Summary

This document provides comprehensive technical architecture details for HRP (HealthEdge Reimbursement Platform) disaster recovery implementation on AWS. HRP operates as a multi-tenant SaaS platform serving 20+ healthcare customers with 1,000+ servers requiring sub-4-hour RTO and 15-minute RPO.

**Key Architecture Characteristics:**
- Multi-region deployment across 4 AWS regions (us-east-1, us-west-2, us-east-2, us-west-1)
- Hybrid cloud architecture with customer on-premises AD integration via Site-to-Site VPN
- AWS Elastic Disaster Recovery Service (EDRS/DRS) as primary DR strategy
- Multi-tenant isolation with customer-specific VPCs and /24 subnet allocation
- Active Directory multi-region replication with 3 DCs per primary region
- Transit Gateway full-mesh connectivity across all regions

## 1. Network Architecture

### 1.1 Multi-Region Network Topology

**Primary Regions:** us-east-1 AND us-west-2 (both are PRIMARY, not primary/secondary)  
**DR Regions:** us-east-2, us-west-1

**Network Account:** 639966646465

#### Transit Gateway Architecture

| Region | Transit Gateway ID | Status | Peering |
|--------|-------------------|--------|---------|
| us-east-1 | tgw-015161a2212309004 | ✅ Deployed | Full mesh (3 peerings) |
| us-west-2 | tgw-06d6189d0728dd473 | ✅ Deployed | Full mesh (3 peerings) |
| us-east-2 | tgw-05a059452f80f47df | ✅ Deployed | Full mesh (3 peerings) |
| us-west-1 | tgw-00393e08109429992 | ✅ Deployed | Full mesh (3 peerings) |

**Transit Gateway Features:**
- Full-mesh peering across all 4 regions
- Customer isolation enforced via route tables
- Centralized routing for inter-region traffic
- Supports customer VPN connectivity

### 1.2 Customer Network Isolation

**Architecture Pattern:**
- Each customer has dedicated VPC in customer production account
- Customer-specific /24 subnet allocation
- Network isolation enforced via Transit Gateway route tables
- No cross-customer communication allowed

**VPC Design:**
- Application subnets across 3 Availability Zones
- Private subnets for database and backend services
- No public-facing resources (all customer access via VPN)

### 1.3 VPN Connectivity

**VPN Concentrators (us-east-1):**
- PaloAltoFirewall1UsEast1: i-0d29bd1e48bae39f6 (us-east-1a)
- PaloAltoFirewall2UsEast1: i-0ca3b5865cba59e2a (us-east-1b)

**VPN Architecture:**
- Site-to-Site VPN per customer
- Terminates on Palo Alto firewall VPN concentrators
- Customer-specific VPN tunnels with dedicated CIDRs
- Firewall rules enforce customer isolation

**Dual Firewall Purpose:**
1. AWS Network Firewall: Traffic inspection within AWS
2. Palo Alto Firewalls: VPN concentration and NAT for customer VPNs only

### 1.4 DNS Architecture

**Route53 Resolver Endpoints:**

| Region | Inbound Endpoint | Outbound Endpoint | Status |
|--------|-----------------|-------------------|--------|
| us-east-1 | rslvr-in-493b9cdb79544ad6a | rslvr-out-15dd1c166e0744f9b | ✅ Operational |
| us-west-2 | rslvr-in-b009fe8f8bea494da | rslvr-out-b74939a8fe264ff09 | ✅ Operational |
| us-east-2 | Deployed | Deployed | ✅ Operational |
| us-west-1 | Deployed | Deployed | ✅ Operational |

**DNS Domains:**
- `healthedge.biz` - HRP Windows Active Directory domain
- `idm.healthedge.biz` - HRP RedHat Identity Management domain
- `customer-a.hrp.healthedge.com` - Customer-specific DNS patterns
- `*.local` - Customer Active Directory domains (e.g., alh.local, axm.local)

**DNS Resolution Flow:**
1. AWS workload queries customer AD domain
2. Route53 Resolver Outbound Endpoint forwards query
3. Forwarding rule targets customer DCs (AWS or on-premises)
4. Response returns via same path

**Critical DNS Gap Identified:**
- us-west-2 `healthedge.biz` forwarding rule targets us-east-1 DCs instead of local us-west-2 DCs
- Impact: If us-east-1 fails, us-west-2 workloads lose DNS resolution despite local DCs existing
- Recommendation: Update us-west-2 forwarding rules to target local DCs (10.222.50.100, 10.222.53.225, 10.222.58.173)

## 2. Active Directory Architecture

### 2.1 HRP Windows Active Directory

**Domain:** healthedge.biz  
**Account:** 211234826829 (HRP-SharedServices)

#### Domain Controller Deployment

**Primary East Coast (us-east-1) - ✅ DEPLOYED:**

| DC Name | Instance ID | IP Address | AZ | Status |
|---------|-------------|------------|-----|--------|
| he3-mgtdc-1 | i-087375866dd0bd64c | 10.196.210.95 | us-east-1d | ✅ Running |
| he3-mgtdc-2 | i-01506f4f9a828e547 | 10.196.214.166 | us-east-1a | ✅ Running |
| he3-mgtdc-3 | i-0c254921c194fa949 | 10.196.218.73 | us-east-1b | ✅ Running |

**Primary West Coast (us-west-2) - ✅ DEPLOYED:**

| DC Name | Instance ID | IP Address | AZ | Status |
|---------|-------------|------------|-----|--------|
| he3-mgtdc-03 | i-04e193093bf2e7b6c | 10.222.50.100 | us-west-2b | ✅ Running |
| he3-mgtdc-04 | i-00e77b62d7ee58202 | 10.222.53.225 | us-west-2a | ✅ Running |
| he3-mgtdc-05 | i-0466e4d35b8675803 | 10.222.58.173 | us-west-2c | ✅ Running |

**DR Regions (us-east-2, us-west-1) - ✅ DEPLOYED:**
- 3 DCs in us-east-2 (deployed and promoted)
- 2 DCs in us-west-1 (deployed and promoted)

### 2.2 Active Directory DR Strategy

**Multi-Region by Design:**
- Domain controllers deployed in both PRIMARY regions (us-east-1 + us-west-2)
- Native AD replication between regions
- **No failover orchestration required** - authentication services remain available during regional failure
- AZ distribution within each region for local high availability

**AD Sites & Services:**
- Separate AD site per AWS region
- Site links configured for inter-region replication
- FSMO roles distributed across regions

**Replication Monitoring:**
- Command: `repadmin /replsummary`
- Frequency: Weekly
- CloudWatch metrics for DC health

### 2.3 Customer Active Directory Integration

**Architecture Pattern:**
- Each customer has separate AD forest (e.g., alh.local, axm.local, citi.local)
- Customer AD DCs deployed in customer production accounts (NOT shared services)
- Hybrid connectivity: AWS DCs + on-premises DCs via Site-to-Site VPN
- AD replication between AWS and on-premises over VPN

**Customer AD Deployment (Per Customer):**
- 3 DCs in primary region across 3 AZs
- 1 DC in DR region (non-partner deployments)
- On-premises DCs maintained by customer

**Customer AD Examples:**

| Customer | AD Domain | AWS DCs (Target) | NAT'd On-Prem IPs | Status |
|----------|-----------|------------------|-------------------|--------|
| ALH | alh.local | 10.229.0.81, .213, .148 | 172.29.38.11, .12 | ⚠️ Verify |
| AXM | axm.local | TBD | 172.29.25.11, .12 | ⚠️ Verify |
| CITI | citi.local | TBD | 172.29.45.11, .12 | ⚠️ Verify |

**Customer AD DR Considerations:**

| Failure Scenario | Impact | Mitigation |
|-----------------|--------|------------|
| AWS Region Failure | ⚠️ AWS workloads lose local DC | Failover to on-prem DCs via VPN |
| VPN Tunnel Failure | ⚠️ Replication paused | AWS DCs continue serving AWS workloads |
| On-Prem DC Failure | ⚠️ On-prem auth affected | AWS DCs unaffected |
| Both AWS + On-Prem Fail | ❌ CRITICAL | Complete customer AD outage |

## 3. RedHat Identity Management (IDM)

### 3.1 IDM Architecture

**Domain:** idm.healthedge.biz  
**Purpose:** Linux authentication services (complements Windows AD)  
**Account:** 211234826829 (HRP-SharedServices)

#### IDM Server Deployment

**Primary East Coast (us-east-1) - ✅ DEPLOYED:**

| Server Name | Instance ID | IP Address | AZ | Status |
|-------------|-------------|------------|-----|--------|
| he3-idm-01 | TBD | 10.196.208.129 | us-east-1d | ✅ Running |
| he3-idm-02 | TBD | 10.196.214.248 | us-east-1a | ✅ Running |
| he3-idm-03 | TBD | 10.196.219.233 | us-east-1b | ✅ Running |

**Primary West Coast (us-west-2) - ✅ DEPLOYED:**

| Server Name | Instance ID | IP Address | AZ | Status |
|-------------|-------------|------------|-----|--------|
| he3-idm-04 | TBD | 10.222.49.221 | us-west-2b | ✅ Running |
| he3-idm-05 | TBD | 10.222.59.162 | us-west-2c | ✅ Running |
| he3-idm-06 | TBD | 10.222.54.170 | us-west-2a | ✅ Running |

**DR Regions - ✅ DEPLOYED:**
- 3 servers in us-east-2 (he3-idm-07, 08, 09) - deployed and configured
- 3 servers in us-west-1 (he3-idm-10, 11, 12) - deployed and configured

### 3.2 IDM DR Strategy

**Multi-Region Deployment Complete:**
- IDM deployed and configured in all 4 regions with multi-master replication
- **No failover orchestration required**
- CA Renewal Master: he2-idm-01.idm.healthedge.biz (us-west-2) - survives us-east-1 failure
- Full mesh replication topology across all regions

**IDM Features:**
- Centralized sudo management (no hardcoded sudoers files)
- Account propagation: ~20 seconds (vs 12+ hours legacy)
- SSSD server affinity for local IDM server preference
- Kerberos authentication with NTP time sync requirement

**Critical IDM DNS Gap:**
- us-west-2 IDM servers (10.222.49.221, 10.222.59.162, 10.222.54.170) NOT in any forwarding rules
- Recommendation: Add us-west-2 IDM IPs to forwarding rules for AWS-side redundancy

## 4. Application Architecture

### 4.1 Application Components

**WebLogic Application Servers:**
- Oracle WebLogic on EC2 instances
- Admin Server: Domain management (critical priority)
- Managed Servers: Application hosting
- Node Manager: Server lifecycle management
- Domain configuration replication required

**EKS Microservices:**
- Web UI components on Amazon EKS
- Melissa Data microservices
- Container-based workloads

**SFTP Services:**
- AWS Transfer Family for SFTP
- Move-IT with Amazon EFS backend
- File transfer integration with customers

**Answers System:**
- Windows-based reporting system
- SQL Server backend
- Customer reporting capabilities

### 4.2 Database Architecture

**Oracle Databases:**
- Oracle on EC2 instances
- Protected by AWS Elastic Disaster Recovery (EDRS)
- Continuous block-level replication
- Sub-second RPO capability

**SQL Server Databases:**
- SQL Server on EC2 instances
- Protected by EDRS
- Availability Group failover for clustered instances
- Sync validation before failover

**FSx for Large Databases:**
- Amazon FSx for NetApp ONTAP
- Cross-region replication
- Used for databases requiring high-performance file storage

### 4.3 Authentication Integration

**Okta SSO:**
- Primary authentication for HRP users
- SAML-based single sign-on
- Integration with customer identity providers

**LDAP/RSO:**
- Customer AD integration via LDAP
- Remote Sign-On (RSO) for customer users
- Trust relationships with customer AD forests

## 5. AWS Elastic Disaster Recovery (EDRS/DRS)

### 5.1 DRS Architecture

**Primary DR Strategy:** AWS Elastic Disaster Recovery Service (powered by CloudEndure)

**DRS Components:**

| Component | Description | Location |
|-----------|-------------|----------|
| DRS Agent | Lightweight replication agent | Source servers |
| Staging Area | Low-cost EC2 instances | Target AWS region |
| Recovery Instances | Full-scale EC2 instances | Target AWS region (launched during recovery) |
| Replication Servers | Managed EC2 instances | Target AWS region |

**DRS Capabilities:**
- Continuous block-level replication
- Sub-second RPO (15-minute target for HRP)
- Minutes RTO (target: <10 minutes for critical workloads)
- Non-disruptive to source servers
- Automated recovery orchestration

### 5.2 DRS Configuration

**Replication Configuration:**
- Data plane routing: PRIVATE_IP
- EBS encryption: ENCRYPTED (alias/aws/ebs)
- Staging disk type: GP3
- Replication server instance type: m5.large (admin/db), m5.medium (managed servers)
- Bandwidth throttling: 0 (unlimited)

**Launch Templates:**
- Copy tags: Enabled
- Launch disposition: STARTED
- Post-launch actions: SSM documents for WebLogic startup
- CloudWatch log groups: /aws/drs/weblogic-*
- S3 log bucket: weblogic-drs-logs

**Server Priority:**
- Critical: Admin Server, Database servers (dedicated replication servers)
- High: Managed servers (shared replication servers)

### 5.3 DRS Testing Strategy

**Monthly DR Testing Schedule:**
- Week 1: EDRS database recovery (Oracle, SQL Server)
- Week 2: EDRS application recovery (WebLogic)
- Week 3: Network failover (Route 53, VPN, ALB)
- Week 4: End-to-end DR scenario with Answers system

**Quarterly Comprehensive Testing:**
- Full environment failover
- Cross-region recovery validation
- Vendor integration testing
- Performance benchmarking
- Business continuity validation

## 6. Recovery Time and Point Objectives

### 6.1 Current vs Target Metrics

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Overall RTO | 15-20 minutes | <10 minutes | 33-50% |
| Critical Workloads RTO | 15 minutes | <5 minutes | 67% |
| RPO | 15 minutes | 15 minutes | Maintained |
| Availability | 99.9% | 99.9% | Maintained |

### 6.2 RTO/RPO by Component

| Component | RTO Target | RPO Target | DR Strategy |
|-----------|-----------|-----------|-------------|
| WebLogic Servers | 10 minutes | 15 minutes | EDRS continuous replication |
| Oracle Databases | 10 minutes | 15 minutes | EDRS continuous replication |
| SQL Server | 10 minutes | 15 minutes | EDRS + AG failover |
| EKS Workloads | 5 minutes | N/A | DNS failover + health checks |
| SFTP Services | 15 minutes | 15 minutes | AWS Transfer Family + EFS |
| Active Directory | 0 minutes | N/A | Multi-region (no failover needed) |
| RedHat IDM | 0 minutes | N/A | Multi-region (no failover needed) |

## 7. DR Testing and Validation

### 7.1 Validation Status (December 12, 2025)

**Automated Validation Results (AWSM-1144):**
- Pass Rate: 100% (39/39 checks passed)
- Network infrastructure: Fully deployed in all 4 regions
- AD/IDM servers: Fully functional in us-east-1 only

**Acceptance Criteria:**

| Criteria | Status | Evidence |
|----------|--------|----------|
| AD DCs verified in all regions | 🟡 Pending 3 regions | 3 DCs in us-east-1 |
| IDM servers verified in all regions | 🟡 Pending 3 regions | 3 IDM in us-east-1 |
| Route 53 forwarders confirmed | 🟡 Pass but needs updates | Forwarding rules exist |
| AD replication tracked | ✅ PASS | Multi-region enables native replication |
| No failover orchestration required | ✅ PASS | AD/IDM already multi-region |

### 7.2 Testing Approach

**Bubble Test Isolation (OPTIONAL):**
- Purpose: Validate AD recovery without production risk
- Method: NACL-based network isolation
- Process: Shutdown DR DCs, create AMI backups, apply isolation NACLs
- Key Principle: Explicit DENY rules block ALL production traffic

**Open Question:** Would bubble testing use NEW isolated VPC or modify NACLs on existing DR VPCs?

## 8. Implementation Roadmap

### 8.1 Implementation Phases

**Phase 1: DR Infrastructure and Services (2-3 weeks)**
- Deploy EC2 instances for DCs in DR regions
- Update LZA network-config.yaml (IPSets, firewall rules, Route53)
- Join to domain and DCPROMO
- Configure AD Sites & Services for new regions
- Update Route53 forwarding rules

**Phase 2: RedHat IDM Deployment (2-3 weeks)**
- Deploy IDM servers in DR regions
- Configure multi-master replication
- Update Route53 forwarding rules
- Validate replication health

**Phase 3: Route53 Updates (1 week)**
- Update forwarding rules to target new DCs
- Fix us-west-2 DNS gaps
- Add us-west-2 IDM IPs to forwarding rules

**Phase 4: Security Groups (1 week - parallel with Phase 1)**
- Configure security groups for AD/IDM traffic
- Update firewall rules

**Phase 5: Validation (2 weeks)**
- AD replication validation (`repadmin /replsummary`)
- IDM replication validation (`ipa topologysegment-find`)
- DNS resolution testing
- Authentication testing from DR workloads

**Total Estimated Duration:** 8-10 weeks

### 8.2 Success Criteria

**Performance Metrics:**
- RTO Achievement: Consistently achieve 1-15 minutes recovery times
- RPO Achievement: Data loss limited to 15 minutes or less
- Availability Target: 99.9% uptime (8.77 hours downtime/year)
- Failover Success Rate: 95% successful automated failovers
- Test Success Rate: 100% successful monthly DR tests

**Operational Metrics:**
- Mean Time to Recovery (MTTR): Achieve current minutes MTTR
- Test Frequency: Increase from annual to monthly DR testing
- Alert Response Time: Automated alerts within 1 minute
- Documentation Coverage: 100% of DR procedures documented and tested

**Cost Metrics:**
- DR Cost Reduction: 20-30% reduction in DR infrastructure costs
- Operational Savings: 40% reduction in DR testing effort
- Efficiency Gains: 50% reduction in DR-related incidents
- Resource Utilization: Improved through Auto Scaling

## 9. Monitoring and Operations

### 9.1 Monitoring Strategy

**Current Monitoring (Ongoing):**

| Check | Tool | Frequency |
|-------|------|-----------|
| DC health | CloudWatch metrics | Daily |
| AD replication | `repadmin /replsummary` | Weekly |
| IDM replication | `ipa topologysegment-find` | Weekly |
| Network connectivity | Ping/traceroute between regions | Weekly |
| DRS replication status | DRS Console | Continuous |

### 9.2 Operational Procedures

**DRS Agent Management:**
- Agent installation during maintenance windows
- Agent version updates quarterly
- Replication health monitoring continuous
- Staging area cost optimization

**AD/IDM Operations:**
- FSMO role management and documentation
- Replication monitoring and alerting
- DNS forwarding rule updates
- Security group maintenance

## 10. Key Findings and Recommendations

### 10.1 Architecture Strengths

1. **Multi-Region by Design:** AD and IDM already deployed in both primary regions, providing inherent high availability
2. **No Failover Orchestration Required:** Authentication services remain available during regional failure without explicit failover
3. **Transit Gateway Full Mesh:** All 4 regions interconnected for flexible failover paths
4. **EDRS Continuous Replication:** Sub-second RPO capability for application and database servers
5. **Customer Isolation:** Strong multi-tenant isolation via VPCs and Transit Gateway routing

### 10.2 Critical Gaps Identified

1. **DNS Forwarding Rules:**
   - us-west-2 `healthedge.biz` targets us-east-1 DCs instead of local DCs
   - us-west-2 IDM servers not in any forwarding rules
   - Impact: Loss of DNS resolution if us-east-1 fails

2. **DC Deployment Status:**
   - us-west-2 DCs exist but not promoted (DCPROMO pending)
   - us-east-2 and us-west-1 DCs not yet deployed
   - Impact: Limited DR coverage to single primary region

3. **IDM Configuration:**
   - us-west-2 IDM servers deployed but not configured
   - DR regions IDM servers not deployed
   - Impact: Linux authentication limited to us-east-1

### 10.3 Recommendations

**Immediate Actions (Priority 1):**
1. Update us-west-2 Route53 forwarding rules to target local DCs
2. Add us-west-2 IDM IPs to forwarding rules
3. Complete DCPROMO for us-west-2 DCs
4. Configure us-west-2 IDM servers

**Short-Term Actions (Priority 2 - 8-10 weeks):**
1. Deploy AD DCs in DR regions (us-east-2, us-west-1)
2. Deploy IDM servers in DR regions
3. Configure AD Sites & Services for all regions
4. Update all Route53 forwarding rules

**Ongoing Actions:**
1. Monthly DR testing per defined schedule
2. Weekly replication health monitoring
3. Quarterly comprehensive DR validation
4. Annual DR audit and technology refresh

## 11. Reference Documentation

### 11.1 Confluence Pages

- **HRP - DR Recommendations:** Primary architecture and strategy document
- **HRP Active Directory, RedHat IDM, and DNS DR Design:** Identity and DNS architecture
- **HRP EC2 Weblogic DR Detailed Design:** WebLogic EDRS implementation
- **HRP New Customer LZA Runbook:** DC deployment procedures
- **5-7-Decision-DNS-Design:** Route53 Resolver configuration

### 11.2 AWS Console Links

| Resource | Account | Region |
|----------|---------|--------|
| HRP Domain Controllers | 211234826829 | us-east-1 |
| HRP IDM Servers | 211234826829 | us-east-1, us-west-2 |
| Palo Alto Firewalls | 639966646465 | us-east-1 |
| Route53 Resolver | 639966646465 | All regions |
| Transit Gateways | 639966646465 | All regions |

### 11.3 Validation Scripts

- `scripts/ad_dns_dr_validation.py` - Automated AD/DNS/Route53 validation
- `weblogic-drs-assessment.sh` - Pre-implementation assessment for WebLogic
- `install-drs-agent.sh` - DRS agent installation
- `monitor-initial-replication.sh` - DRS replication monitoring

## 12. Glossary

| Term | Definition |
|------|------------|
| EDRS | AWS Elastic Disaster Recovery Service (formerly CloudEndure) |
| DRS | Disaster Recovery Service (AWS service name) |
| IDM | RedHat Identity Management (FreeIPA) |
| FSMO | Flexible Single Master Operations (AD roles) |
| DCPROMO | Domain Controller Promotion (AD installation) |
| TGW | Transit Gateway |
| SSSD | System Security Services Daemon (Linux authentication) |
| RSO | Remote Sign-On |
| LZA | Landing Zone Accelerator |

---

**Document Status:** Initial version based on Confluence documentation analysis  
**Next Review:** After Phase 1 implementation completion  
**Owner:** HRP DR Implementation Team
