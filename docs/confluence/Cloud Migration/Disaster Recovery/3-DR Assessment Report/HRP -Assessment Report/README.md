# HRP -Assessment Report

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5081661569/HRP%20-Assessment%20Report

**Created by:** Venkata Kommuri on September 09, 2025  
**Last modified by:** Venkata Kommuri on September 09, 2025 at 07:26 PM

---

**HRP Disaster Recovery Assessment Report**

**Executive Summary**

This assessment report provides a comprehensive analysis of the current Health Rules Payor (HRP) disaster recovery capabilities and requirements for AWS cloud migration. The assessment was conducted through multiple technical sessions with key stakeholders to understand the existing on-premises DR strategy and identify requirements for implementing DR in AWS.

**Current State Overview**

Health Edge currently operates HRP in an single active data center configuration with storage-level replication providing disaster recovery capabilities. The existing solution supports multiple customers with dedicated infrastructure per customer and contractual DR testing requirements.

**Current Architecture Analysis**

**Application Infrastructure**

* **Technology Stack:** Java applications running on Oracle WebLogic
* **Database Platform:** Oracle OLTP and SQL Server Data Warehouse
* **Customer Model:** Dedicated infrastructure per customer (no shared resources)
* **Scaling:** 1-15 WebLogic servers per customer environment

**Current DR Implementation**

* **Strategy:** Storage-level volume replication
* **Architecture:** Active-standby data centers (Ohio and Massachusetts)
* **Network:** Stretched networks maintaining consistent IP addressing
* **Failover:** "All or nothing" approach - entire customer environment fails over together
* **Testing:** Annual live production DR tests (contractually required)

**Database Replication**

* **Current Technologies:**

  + Golden Gate (legacy customers)
  + Click replication (new standard since January 2024)
  + Real-time OLTP to Data Warehouse replication
* **Migration Status:** Transitioning from Golden Gate to Click (both must be supported)

**Key Findings**

**Strengths of Current DR Solution**

1. **Proven Reliability:** 4-8 hour failover capability for clean shutdowns
2. **Network Consistency:** Stretched networks eliminate IP/hostname changes
3. **Comprehensive Coverage:** Entire customer environment replicates as single unit
4. **Contractual Compliance:** Meets customer SLA requirements for DR testing

**Challenges for AWS Migration**

1. **Technology Dependencies:** Dual replication technology support required
2. **Network Complexity:** Stretched network model not directly applicable to AWS
3. **Integration Points:** Multiple external vendor integrations requiring secure connectivity
4. **Customer Isolation:** Dedicated infrastructure model increases AWS resource requirements
5. **Authentication Dependencies:** External Okta and Active Directory integrations

**Critical Dependencies Identified**

**External Integrations**

**Authentication Systems:**

* Okta SSO (Health Edge and customer instances)
* Customer Active Directory/LDAP (RSO)

**Third-Party Services:**

* Third-party claim editing software (CES, CXT, EZ Grouper, Source)
* Melissa Data microservices (Kubernetes required)

**Network Requirements**

* Site-to-site VPN connectivity to vendors
* Customer VPN tunnels for DR scenarios
* Secure connectivity for all external services

**Database Requirements**

* Oracle and SQL Server support
* Golden Gate and Click replication capabilities
* Custom database support for specific customers

**Risk Assessment**

**High Risk Areas**

1. **Replication Technology Migration:** Supporting both Golden Gate and Click during transition
2. **Network Connectivity:** Ensuring secure, reliable connections to external services
3. **Customer Isolation:** Maintaining security boundaries in shared cloud infrastructure
4. **DR Testing:** Meeting contractual obligations for live production testing

**Medium Risk Areas**

1. **Authentication Integration:** Okta and Active Directory connectivity from AWS
2. **Third-Party Vendor Connectivity:** Site-to-site VPN establishment and maintenance
3. **Performance:** Ensuring application performance meets current standards
4. **Compliance:** Meeting customer-specific regulatory requirements

**Low Risk Areas**

1. **Application Platform:** Java/WebLogic well-supported in AWS
2. **Database Platform:** Oracle and SQL Server available as managed services
3. **Monitoring:** AWS native monitoring capabilities

**Customer Impact Analysis**

**Per-Customer Infrastructure Requirements**

**Minimum Configuration**

* 3 database instances (OLTP, Data Warehouse, Replication)
* 1-15 WebLogic application servers
* 1 replication server (Golden Gate or Click)
* Dedicated network segment (/25 for production)

**Maximum Configuration (with custom database)**

* 4 database instances
* Additional custom application components
* Enhanced security requirements

**Shared Services Impact**

* **File Transfer Services:** SFTP and Move-IT (logically separated by customer)
* **External Integrations:** Vendor-hosted services requiring VPN connectivity

**Recommendations Summary**

**Immediate Actions Required**

1. **Technology Assessment:** Evaluate AWS-native alternatives for Golden Gate and Click
2. **Network Design:** Design AWS networking architecture supporting customer isolation
3. **Integration Planning:** Map all external integration points and connectivity requirements
4. **Compliance Review:** Validate AWS services meet customer regulatory requirements

**Migration Strategy Considerations**

1. **Phased Approach:** Migrate customers in phases to minimize risk
2. **Pilot Program:** Select low-complexity customers for initial migration
3. **Parallel Operations:** Maintain on-premises DR during migration period
4. **Testing Strategy:** Develop comprehensive DR testing procedures for AWS

**Next Steps**

**Action Items**

1. **Detailed Technical Design:** Develop AWS-specific architecture designs
2. **Vendor Engagement:** Engage with replication technology vendors for AWS support
3. **Customer Communication:** Develop customer communication plan for migration
4. **Pilot Selection:** Identify and prepare pilot customers for migration
5. **Timeline Development:** Create detailed migration timeline with milestones