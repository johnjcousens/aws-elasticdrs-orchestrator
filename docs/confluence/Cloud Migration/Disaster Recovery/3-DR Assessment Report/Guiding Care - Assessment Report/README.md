# Guiding Care - Assessment Report

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4990370153/Guiding%20Care%20-%20Assessment%20Report

**Created by:** Venkata Kommuri on August 06, 2025  
**Last modified by:** Venkata Kommuri on August 06, 2025 at 09:15 PM

---

Guiding Care Disaster Recovery Assessment Report
================================================

1. Project Overview
-------------------

This document outlines the requirements for designing a comprehensive disaster recovery (DR) strategy for the Guiding Care environment that will be migrated from on-premises to AWS. The project consists of two phases:

1. **Phase 1:** Migrate on-premises resources to AWS using a lift-and-shift approach ( Not part of DR Assessment Work)
2. **Phase 2:** Design and implement disaster recovery solutions for the AWS environment

The DR design must cover recommendations across applications, data storage, infrastructure, operations, network, and security components to meet business uptime objectives.

2. Current Environment Assessment
---------------------------------

### 2.1 Data Center Architecture

**Primary Data Centers:**

* **IAD3 (Reston, Virginia)** - Primary for East Coast customers (~75% of customer base)
* **LX3 (Los Angeles)** - Primary for West Coast customers (~25% of customer base)

**Current DR Limitations:**

* Insufficient hardware for failover
* No VM replication between sites
* Manual rebuild requirement
* 4-hour RTO not currently achievable

### 2.2 Application Architecture

**Presentation Layer:**

* Main Guiding Care Portal (.NET-based)
* Authorization Portal (.NET-based)
* Member Portal (.NET-based)

**Load Balancing:**

* HA Proxy with custom ACLs and rules
* Single instance per environment (not deployed in high-availability configuration)

**API Layer:**

* 40-50 different APIs (primarily .NET Framework and .NET 8 based)
* WSO2 API Gateway for external API access

**Rules Engine:**

* FICO (being replaced with custom Java-based rules engine)

**Database Layer:**

* SQL Server with Always-On Availability Groups
* Redis for application caching (36 hosts across data centers)
* MongoDB for ETL processes (no replication currently)
* Tableau Database for reporting

### 2.3 Network Components

**Firewall Infrastructure:**

* 4 ASA firewalls per data center (handle site-to-site VPNs)
* 2 Palo Alto firewalls per data center (primarily for web applications)

**Connectivity Types:**

* **Web Application Access:** HTTPS (Port 443)
* **Database Connectivity:** Site-to-site VPNs through ASA firewalls
* **Cloud Connectivity:** VPN tunnel to Azure East and West (for DocIO service)

### 2.4 Backup and Recovery Infrastructure

**SQL Server Backup Strategy:**

* **Full backups:** Weekly
* **Differential backups:** Nightly
* **Transaction logs:** Hourly
* **Retention:** 60 days
* **Primary storage:** Pure Storage appliance
* **Cross-data center replication:** via MPLS
* **No direct storage replication**

3. Business Objectives
----------------------

* Ensure business continuity in the event of infrastructure failures, regional outages, or other disruptive events
* Meet or exceed the organization's Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO)
* Provide cost-effective DR solutions that align with business criticality of different applications
* Remediate current issues identified in the existing environment
* Establish operational procedures for DR testing, failover, and recovery

4. Technical Requirements
-------------------------

### 4.1 Migration Requirements (Phase 1)

Perform lift-and-shift migration of servers to appropriate AWS resources:

* Replace HA Proxy with AWS Elastic Load Balancers
* Migrate SQL Server to EC2 or consider Amazon RDS for SQL Server
* Replace SIFS with Amazon FSx or S3 for document storage
* Consider AWS API Gateway to replace WSO2
* Maintain application functionality and performance during and after migration
* Establish appropriate networking in AWS to support existing connectivity models

### 4.2 Disaster Recovery Requirements (Phase 2)

* Design DR solutions for all critical AWS infrastructure components
* Provide DR recommendations for:

  + Application tier (.NET applications, APIs)
  + Database tier (SQL Server, Redis, MongoDB)
  + Document storage
  + Integration components (batch and real-time processing)
  + Network components
  + Security components
* Align DR strategies with application criticality and business requirements
* Consider AWS-native DR capabilities and multi-region architectures
* Ensure data consistency and integrity across primary and DR environments
* Address the current DR limitations including:

  + Automating recovery processes
  + Implementing VM/instance replication
  + Meeting or exceeding 4-hour RTO targets

5. Component-Specific Requirements
----------------------------------

### 5.1 Web Application Tier

* Implement high availability and DR capabilities for all web applications
* Address single point of failure in current HA Proxy implementation
* Translate existing ACLs and custom rules to AWS equivalents

### 5.2 Database Tier

* Maintain or improve upon current SQL Server Always-On Availability Groups architecture
* Implement proper replication and DR for Redis caching infrastructure
* Establish DR capabilities for MongoDB (currently lacking replication)

### 5.3 API and Integration Layer

* Ensure WSO2 API Gateway functionality is preserved or improved in AWS
* Maintain integration with third-party systems
* Implement appropriate DR for batch processing components (Apache Airflow)
* Consider replacing Azure Service Bus with AWS-native services for outbound data processing

### 5.4 Document Storage

* Migrate from on-premises SIFS/VNX and Azure Blob Storage to appropriate AWS storage services
* Maintain document metadata and security controls during migration
* Implement appropriate backup and DR strategies for document storage

### 5.5 Networking and Security

* Replace or migrate current firewall configurations to AWS security groups and NACLs
* Maintain VLAN segmentation through appropriate AWS constructs
* Ensure customer VPN connections are properly migrated and have DR capabilities
* Consider implementing AWS WAF to replace Cloudflare WAF

6. Key Dependencies and Constraints
-----------------------------------

* Existing architecture and customer-specific configurations must be maintained during migration
* Application and database interdependencies must be considered in DR design
* Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO) requirements must be defined per component
* Budget constraints for DR implementation (to be specified)
* Customer connectivity requirements must be maintained

7. Success Criteria
-------------------

* Documented DR design that addresses all critical components
* DR solution meets or exceeds RTO/RPO requirements for all application tiers
* Clear operational procedures for DR testing, failover, and recovery
* Cost-effective implementation aligned with business priorities
* Successful validation of DR capabilities through testing

8. Outstanding Questions
------------------------

* Are there any regulatory or compliance requirements that must be addressed?
* What is the criticality classification of different applications and components?
* Are there any specific security requirements for the DR environment?
* What operational team structure will manage DR operations?

**Note:** This document will be updated as additional information becomes available through further discussions.