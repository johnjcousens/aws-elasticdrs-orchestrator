# 3-1-Decision-Marketplace-Procurement-Implementation-Strategy

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4994957319/3-1-Decision-Marketplace-Procurement-Implementation-Strategy

**Created by:** Lei Shi on August 07, 2025  
**Last modified by:** Lei Shi on August 07, 2025 at 10:23 PM

---

Decision Record ID: [AWSM-504](https://healthedge.atlassian.net/browse/AWSM-504)
--------------------------------------------------------------------------------

**Date: August 7, 2025**

Context
-------

HealthEdge needs to implement a governance structure for AWS Marketplace subscriptions and procurement across multiple organizational units (OUs), each with distinct requirements and compliance needs.

Problem Statement
-----------------

The organization requires:

1. Controlled software procurement process
2. Different marketplace experiences per OU
3. Compliance with corporate procurement policies
4. Cost optimization and centralized billing
5. Automated approval workflows

Options Considered
------------------

### Option 1: Decentralized Management

* Pros:

  + Local autonomy
  + Faster procurement
* Cons:

  + Lack of central control
  + Potential compliance risks
  + Cost inefficiencies

### Option 2: Fully Centralized Management

* Pros:

  + Maximum control
  + Unified compliance
* Cons:

  + Slower procurement process
  + Less flexibility for OU-specific needs

### Option 3: AWS Private Marketplace with OU-Specific Experiences (Selected)

* Pros:

  + Balanced control and flexibility
  + OU-specific customization
  + Centralized governance
  + Automated workflows
  + Enhanced compliance controls
* Cons:

  + Initial setup complexity
  + Resource investment in configuration

Decision
--------

Implement AWS Private Marketplace with customized experiences per OU

Rationale
---------

1. Provides required governance controls
2. Enables OU-specific customization
3. Maintains centralized oversight
4. Supports compliance requirements
5. Allows for automated workflows
6. Scalable solution for future growth

Implementation Scope
--------------------

### Phase 1: Foundation (Q3 2025)

* AWS Organizations structure setup
* Marketplace Delegated Administrator account setup
* Base Private Marketplace implementation

### Phase 2: Sandbox OU as pilot scope (Q3 2025)

1. Initial set of products to be decide and approved for Sandbox accounts
2. Sandbox OU specific Private Marketplace Experience setup
3. New product approval request process setup
4. Validation of the implementations

### Phase 3: Whole organization Implementation (future)

* Repeat process and lesson learned from Phase 2 for other BUs and/or entire organization
* Monitoring setup
* Reporting frameworks
* Automated controls

Success Criteria
----------------

1. All OUs have functioning Private Marketplace experiences
2. 100% compliance with procurement policies
3. Reduced procurement cycle time by x% (to-be-discussed)

### Resource Requirements

1. AWS Organizations Management account and Delegated Administrator account access
2. Procurement team involvement
3. Security team review
4. OU stakeholder participation

### Risks and Mitigation

| Risk | Mitigation |
| --- | --- |
| User adoption resistance | Comprehensive training program |
| Initial setup complexity | Phased implementation approach |
|  |  |
|  |  |

### Dependencies

1. AWS Organizations setup
2. IAM framework
3. Procurement process redesign
4. Stakeholder approval
5. Security review completion

### Review Schedule

* Weekly progress reviews during implementation
* Monthly governance reviews post-implementation
* Quarterly effectiveness assessments

### Next Steps

1. Form implementation team
2. Finalize technical design
3. Begin Phase 1 implementation
4. Schedule training sessions

This decision is subject to review in 12 months or upon significant organizational changes.