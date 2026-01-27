# HRP Confluence Documentation Reference

**Date**: 2026-01-20  
**Purpose**: Comprehensive reference to all HRP-related Confluence documentation in the Cloud Migration workspace

---

## Overview

This document provides a complete index of HealthEdge Revenue Platform (HRP) documentation from the Confluence Cloud Migration space, organized by DR lifecycle phase and topic area.

**📋 For detailed technical architecture analysis, see:** [HRP DR Technical Architecture](HRP_DR_TECHNICAL_ARCHITECTURE.md)

The technical architecture document extracts and organizes all key technical details from the Confluence documentation including:
- Multi-region network architecture (Transit Gateway, VPC, VPN)
- Active Directory multi-region deployment (3 DCs per region)
- RedHat IDM architecture and replication
- Application components (WebLogic, EKS, SFTP, Answers)
- Database architecture (Oracle, SQL Server, FSx)
- AWS Elastic Disaster Recovery (EDRS/DRS) implementation
- DNS and Route53 architecture with identified gaps
- RTO/RPO targets and success metrics
- Implementation roadmap and validation procedures

---

## 1. Disaster Recovery Scoping

### HRP Disaster Recovery Scoping Overview
**Path**: `docs/confluence/Cloud Migration/Disaster Recovery/1-Scope/HRP Disaster Recovery Scoping Overview/`  
**Confluence**: https://healthedge.atlassian.net/wiki/spaces/CP1/pages/[page-id]

**Content**: Initial scoping and requirements gathering for HRP DR strategy

---

## 2. DR Discovery and Analysis

### HRP - DR Discovery Sessions
**Path**: `docs/confluence/Cloud Migration/Disaster Recovery/2-DR Discovery and Analysis/HRP - DR Discovery Sessions/`  
**Confluence**: https://healthedge.atlassian.net/wiki/spaces/CP1/pages/[page-id]

**Content**: 
- Current DR testing procedures
- Infrastructure analysis
- Application dependencies
- Customer environment requirements
- Testing frequency and requirements

**Key Findings**:
- Current DR requires failing over entire customer environment as single unit
- Component-level failovers not applicable for HRP applications
- If one component fails (Oracle database), either recover in place or fail over entire environment

---

## 3. DR Assessment Report

### HRP - Assessment Report
**Path**: `docs/confluence/Cloud Migration/Disaster Recovery/3-DR Assessment Report/HRP -Assessment Report/`  
**Confluence**: https://healthedge.atlassian.net/wiki/spaces/CP1/pages/[page-id]

**Content**:
- Current state assessment
- Gap analysis
- Risk assessment
- Compliance requirements
- RTO/RPO analysis

---

## 4. DR Recommendations

### HRP - DR Recommendations (Primary)
**Path**: `docs/confluence/Cloud Migration/Disaster Recovery/4-DR Recommendations/HRP - DR Recommendations/`  
**Confluence**: https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5112397888

**Created**: September 21, 2025 by Venkata Kommuri

**Content**:
- Comprehensive DR strategy using lift-and-shift approach
- AWS regional strategy architecture
- Component-level recovery options
- RTO/RPO targets
- DNS and Route 53 failover strategy
- Active Directory integration
- Certificate management

**Key Architecture Components**:
- AWS Elastic Disaster Recovery (DRS)
- Multi-region deployment (US-East-1/US-East-2, US-West-1/US-West-2)
- Route 53 health checks and failover
- Application Load Balancer (ALB) configuration
- Customer-specific DNS records (e.g., `customer-a.hrp.healthedge.com`)

**Business Drivers**:
- Business continuity for critical HRP services
- Risk mitigation for downtime and data loss
- Regulatory compliance for healthcare industry
- Customer SLA requirements

### HRP - DR Recommendations Re Architecture (Future State)
**Path**: `docs/confluence/Cloud Migration/Disaster Recovery/4-DR Recommendations/Future/HRP - DR Recommendations Re Architecture/`  
**Confluence**: https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5081628954

**Created**: September 09, 2025 by Venkata Kommuri

**Content**:
- Cloud-native disaster recovery strategy
- Complete re-architecture to AWS cloud-native services
- Transformation from monolithic to microservices-based system
- Serverless computing and managed databases
- Event-driven architecture

**Strategic Vision**:
- Transform from infrastructure-dependent to cloud-native platform
- Inherently resilient, scalable, and cost-effective
- Advanced analytics capabilities
- AI/ML integration opportunities
- Unlimited scalability

**Key Advantages**:
- Automatic failover and self-healing
- Distributed architecture eliminating single points of failure
- Reduced operational overhead
- Competitive advantage in healthcare market

---

## 5. DR Implementation Roadmap

### HRP - DR Roadmap
**Path**: `docs/confluence/Cloud Migration/Disaster Recovery/5-DR Implementation Roadmap/HRP - DR Roadmap/`  
**Confluence**: https://healthedge.atlassian.net/wiki/spaces/CP1/pages/[page-id]

**Content**:
- Implementation phases and timeline
- Resource requirements
- Dependencies and prerequisites
- Milestone definitions
- Success criteria

---

## 6. Implementation & Runbooks

### HRP DR Implementation
**Path**: `docs/confluence/Cloud Migration/Disaster Recovery/7-Implementation & Runbooks/HRP DR Implementation/`  
**Confluence**: https://healthedge.atlassian.net/wiki/spaces/CP1/pages/[page-id]

**Content**:
- Step-by-step implementation procedures
- Configuration guides
- Deployment scripts
- Validation procedures
- Rollback procedures

### HRP Active Directory, RedHat IDM, and DNS Disaster Recovery
**Path**: `docs/confluence/Cloud Migration/Disaster Recovery/7-Implementation & Runbooks/HRP Active Directory, RedHat IDM, and DNS Disaster/`  
**Confluence**: https://healthedge.atlassian.net/wiki/spaces/CP1/pages/[page-id]

**Content**:
- Active Directory DR strategy
- RedHat IDM integration
- DNS failover configuration
- Multi-region DNS architecture
- Certificate management for DR

**Key Components**:
- Customer Active Directory/LDAP integration
- IP address configuration for customer AD
- DNS resolution for LDAP/LDAPS calls
- Certificate import and validation

---

## 7. Cross-Cutting Documentation

### AWS Disaster Recovery Service Setup for EC2
**Path**: `docs/confluence/Cloud Migration/Disaster Recovery/7-Implementation & Runbooks/AWS Disaster Recovery Service Setup for EC2/`  
**Confluence**: https://healthedge.atlassian.net/wiki/spaces/CP1/pages/[page-id]

**Content**:
- DRS agent installation
- Replication configuration
- Launch settings
- Testing procedures

**Applicable to**: HRP EC2 instances (WebLogic, SFTP, etc.)

### HealthEdge AWS Tagging Strategy for DR
**Path**: `docs/confluence/Cloud Migration/Disaster Recovery/7-Implementation & Runbooks/HealthEdge AWS Tagging Strategy for DR/`  
**Confluence**: https://healthedge.atlassian.net/wiki/spaces/CP1/pages/[page-id]

**Content**:
- DR tag taxonomy
- Tag validation rules
- SCP enforcement
- Tag policies

**HRP-Specific Tags**:
- `dr:enabled=true`
- `dr:priority` (critical/high/medium/low)
- `dr:wave` (1-N)
- `dr:recovery-strategy` (drs/aurora/ecs/lambda/route53)
- `Customer` (customer identifier)
- `Environment` (production/staging/development)

### HealthEdge AWS Tag Validation Implementation
**Path**: `docs/confluence/Cloud Migration/Disaster Recovery/7-Implementation & Runbooks/HealthEdge AWS Tag Validation Implementation/`  
**Confluence**: https://healthedge.atlassian.net/wiki/spaces/CP1/pages/[page-id]

**Content**:
- Tag validation automation
- AWS Config rules
- Compliance reporting
- Remediation procedures

---

## 8. Database-Specific Documentation

### FSx for NetApp ONTAP – Disaster Recovery Assessment
**Path**: `docs/confluence/Cloud Migration/Disaster Recovery/7-Implementation & Runbooks/FSx for NetApp ONTAP – Disaster Recovery Assessmen/`  
**Confluence**: https://healthedge.atlassian.net/wiki/spaces/CP1/pages/[page-id]

**Content**:
- FSx ONTAP DR capabilities
- Replication configuration
- Failover procedures
- Performance considerations

**Applicable to**: HRP large Oracle databases (>16TB)

---

## 9. Security and Compliance

### Encryption in Transit Validation and Verification
**Path**: `docs/confluence/Cloud Migration/Disaster Recovery/4-DR Recommendations/Encryption in Transit Validation and Verification/`  
**Confluence**: https://healthedge.atlassian.net/wiki/spaces/CP1/pages/[page-id]

**Content**:
- TLS/SSL configuration
- Certificate management
- Encryption validation procedures
- Compliance verification

**Applicable to**: All HRP components

---

## 10. Project Management

### Cloud Migration README
**Path**: `docs/confluence/Cloud Migration/README.md`

**HRP Team Members**:
- **HRP Technical Lead**: Todd Matton, Joseph Branciforte, Brijesh Singh
- **HRP DevOps**: Riyazuddin Shaik, Vikas Kumar Agrawal

**HRP Migration Status** (as of May 27, 2025):
- **Status**: Done
- **Owner**: Todd Matton
- **Target Completion**: May 30, 2025
- **Current State**: Deployed in test environment
- **Next Steps**: Discuss rollout plan with change management

---

## HRP Architecture Components

### Application Tier
- **WebLogic Application Servers**: DRS-based recovery
- **Web UI**: EKS with DNS failover
- **SFTP Services**: DRS-based recovery

### Database Tier
- **Oracle OLTP Database**: 
  - Small/Medium: DRS
  - Large (>16TB): FSx for NetApp ONTAP
- **SQL Server Data Warehouse**: Always On Distributed Availability Groups

### Shared Services
- **Active Directory**: Multi-region replication
- **DNS**: Route 53 with health checks
- **Network**: VPN, Direct Connect, Transit Gateway

### Recovery Technologies
- **AWS DRS**: EC2 instance recovery
- **FSx ONTAP**: Large database recovery
- **Route 53**: DNS failover
- **EKS**: Container orchestration with DNS failover

---

## DNS Architecture

### Customer-Specific DNS Records

**Pattern**: `{service}.{customer}.hrp.healthedge.com`

**Examples**:
- Primary: `webui.customer-a.hrp.healthedge.com` → ALB in US-East-1
- DR: `webui-dr.customer-a.hrp.healthedge.com` → ALB in US-East-2

**Failover Configuration**:
- Health Check: Application-level health checks
- Failover Time: 60-180 seconds
- TTL: Configurable based on RTO requirements

---

## RTO/RPO Targets

### Current State (Pre-AWS)
- **RTO**: 24+ hours
- **RPO**: 24 hours
- **Testing**: Annual full environment failover

### Target State (AWS Lift-and-Shift)
- **RTO**: 4 hours (83% improvement)
- **RPO**: 30 minutes (DRS continuous replication)
- **Testing**: Quarterly component-level testing

### Future State (Cloud-Native)
- **RTO**: <1 hour (automated failover)
- **RPO**: Near-zero (multi-region active-active)
- **Testing**: Continuous chaos engineering

---

## Related Documentation

### Internal Design Documents
- [BRD - Enterprise DR Orchestration Platform](../HRP/DESIGN-DOCS/00-BRD-Enterprise-DR-Orchestration-Platform.md)
- [PRD - Enterprise DR Orchestration Platform](../HRP/DESIGN-DOCS/01-PRD-Enterprise-DR-Orchestration-Platform.md)
- [SRS - Enterprise DR Orchestration Platform](../HRP/DESIGN-DOCS/02-SRS-Enterprise-DR-Orchestration-Platform.md)
- [TRS - Enterprise DR Orchestration Platform](../HRP/DESIGN-DOCS/03-TRS-Enterprise-DR-Orchestration-Platform.md)

### Reference Architectures
- [Reference Architecture Repositories](../HRP/DESIGN-DOCS/REFERENCE_ARCHITECTURE_REPOSITORIES.md)
- [DR Orchestration Architecture](../../.kiro/steering/dr-orchestration-architecture_HRP_Proposed.md)

### Implementation
- [DRS Orchestration Implementation](../../infra/orchestration/drs-orchestration/)
- [Master Template Analysis](../../infra/orchestration/drs-orchestration/docs/architecture/MASTER_TEMPLATE_ANALYSIS.md)

---

## Key Contacts

### HRP Leadership
- **Technical Leads**: Todd Matton, Joseph Branciforte, Brijesh Singh
- **DevOps**: Riyazuddin Shaik, Vikas Kumar Agrawal

### AWS Professional Services
- **DR Strategy**: Venkata Kommuri
- **Architecture**: Chris Falk
- **Implementation**: John Cousens, Prasad Duvvi

---

## Document Status

**Last Updated**: 2026-01-20  
**Maintained By**: AWS Professional Services  
**Review Frequency**: Monthly during implementation, quarterly post-deployment

---

## Quick Links

| Category | Link |
|----------|------|
| HRP DR Recommendations | https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5112397888 |
| HRP Re-Architecture (Future) | https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5081628954 |
| Cloud Migration Home | https://healthedge.atlassian.net/wiki/spaces/CP1/ |
| DR Implementation Runbooks | `docs/confluence/Cloud Migration/Disaster Recovery/7-Implementation & Runbooks/` |
| HRP Design Documents | `docs/HRP/DESIGN-DOCS/` |

