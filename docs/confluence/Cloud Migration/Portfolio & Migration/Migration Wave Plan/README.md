# Migration Wave Plan

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5030740009/Migration%20Wave%20Plan

**Created by:** Michael Pabon on August 20, 2025  
**Last modified by:** Kaitlin Wieand on October 07, 2025 at 07:06 PM

---

* This document outlines the strategy for wave planning for HealthEdge. In the Mobilize phase of this engagement, the team utilized the existing data from BU teams and ModelizeIT Discovery data to evaluate and formulate a high-level migration disposition, plan and timeline. Leveraging data from the discovery tool and on-going application assessments, this document with delineate the comprehensive migration strategy for all applications within the scope, representing the migration phase of this journey.

The primary migration strategy for this phase will involve re-hosting the workloads by replicating servers on AWS, utilizing the Cloud Migration Factory (CMF) in conjunction with AWS MGN (Application Migration service). Additionally, the strategy includes limited database re-platform for Delphix and clustered use cases.

**Wave Plan Principles**

These principles will be evaluated and applied to the continuous application analysis and planning work-streams as well as the business case validation

| **ID** | **Title** | **Description** |
| --- | --- | --- |
| COM-001 | Application Servers | All will be included in wave plan |
| COM-002 | Database Servers | All database servers will be included in Wave plan  **Re-platform:**   1. Delphix 2. Cluster Databases |
| COM-003 | Prioritization Criteria | The following prioritization criteria will be used in the current iteration of the wave plan  **HRP:**   1. Customer sentiments 2. Classification (Internal/Partner/Customer) 3. Tier (Blue Cross/North Winds/UST/Group 1,2,3) 4. Size (Small/Medium/Large) 5. Upgrade Windows schedule 6. Complexity (Low/Medium/High)   **GC:**   1. Customer Sentiments 2. Classification (Internal/Customer) 3. Tier (Platinum/Diamond/Gold/Silver/Bronze) 4. Module Complexity (Low/Medium/High) |
| COM-004 | Open Enrollment Schedule for HRP & GC  Christmas and Newyear’s eve | Freeze from mid Oct 2026 to mid Jan 2027  December 22, 2025 to January 02, 2026  December 21, 2026 to January 01, 2027 |
| COM-005 | Wave Phases | Each individual wave will have 4 phases: Migration Planning, Build, Infrastructure Testing, and Cutover  Please see Wave Planning Phases Section to see high level details of each phase. We will have a separate run-book with details of each phase to be linked shortly. |
| COM-006 | Testing timeline | 6 weeks of Non-prod environments testing (Internal & Customer)  1 week of Pre-prod environment testing (Internal & Customer)  1 week of Prod environment testing (Internal & Customer) |
| COM-007 | Migration Start date | **HRP:**  Internal - September 29, 2025  Customer Non-prod - December 22, 2025  Customer Prod - February 02, 2026  **GC:**  Internal - October 13, 2025  Customer Non-prod - December 22, 2025  Customer Prod - February 02, 2026  **Source, PDM, MRF:**  Internal - Q2, 2026  Customer Non-prod - Q3,2026  Customer Prod - Q4, 2026  **Wellframe:**  Internal - Q3, 2026  Customer Non-prod - Q4,2026  Customer Prod - Q1, 2027 |

**Migration Wave Plan Phases:**

**For example:** Wave 3 migration is structured into three sub-waves (3a, 3b, and 3c) to efficiently manage the transition of non-production and production environments. This approach ensures systematic migration of approximately 6-7 non-production environments, pre-production, and production environments.

| **Week** | **1** | **2** | **3** | **4** | **5** | **6** | **7** | **8** | **9** | **10** | **11** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Wave 3a** | **P** | **B** | **IT** | **NP - T1** | **NP - T2** | **NP - T3** |  |  |  |  |  |
| **Wave 3b** |  |  |  | **P** | **B** | **IT** | **NP - T1** | **NP - T2** | **NP - T3** |  |  |
| **Wave 3c** |  |  |  |  |  |  | **P** | **B** | **IT** | **PP - T1** | **P - T2** |

**Wave Stages: (definitions)**

**P** Planning

**B** - Build

**IT** – Infra Testing

**NP Test 1** – Non-prod Test (Week 1)

**NP Test 2** – Non-prod Test (Week 2)

**NP Test 3** – Non-prod Test (Week 3)

**PP Test 1** – Pre-prod Test 1 (Week 1)

**P Test 2** – Prod Test 2 (Week 2)

**Customer Example from Wave 3 (Clover Health):**

|  | **Wave 3** | **Environment** |
| --- | --- | --- |
| Non-prod | Wave 3a | Development |
| Non-prod | Wave 3a | Engineering & PS |
| Non-prod | Wave 3a | Sandbox |
| Non-prod | Wave 3b | Config |
| Non-prod | Wave 3b | Non-prod |
| Non-prod | Wave 3b | TSS |
| Non-prod | Wave 3b | UAT |
| Pre-prod | Wave 3c | Pre-prod |
| Prod | Wave 3c | Prod |

**Customer Wave Assignment Sheet** ([Master-Data-Wave-Grouping-Inventory.xlsx](https://healthedgetrial.sharepoint.com/:x:/s/AWSCloudMigration/EbWsVCIMQ1lElMwnUl10dAYBA_LUa1q8QGPE_eQhZ3k8_Q?e=dd9fTS&nav=MTVfezgxNDY5OTNFLUNGQUMtQzk0Qi05NTgyLTgyODIwNjJBRDU0MH0)): Details of wave numbers mapped to customer names and their respective environments

**Master Wave Planning Sheet** ([Master Data.xlsx](https://healthedgetrial.sharepoint.com/:x:/s/AWSCloudMigration/ERfrOQitmAxAvCbWAl_c13UBC8oj2GTuf4GQQLmlU3darA?e=i2pL13)): Comprehensive wave execution timeline with detailed phase breakdowns from Planning through Production

**Migration Phase Task Details (*****Will be later refined to T-minus plan with detailed tasks for all stakeholders*****)**

The activities captured below are a high level initial scope. As we fine tune migration wave planning, activities and responsibilities of all teams involved will be captured and updated.

| **Phase** | **Scope** | **Week Number** | **AWS Activities** | **HealthEdge Activities** | **Customer Activities** | **Deliverables** | **Outcome** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Planning** | Requirements gathering and preparation | Week 1  Week 4  Week 7 | * Capture all requirements * Validate prerequisites * Ensure readiness for wave execution | * Approve state architecture * Identify constraints |  |  | Documented requirements and approval to proceed |
| **Build (Rehost)** | Migration using AWS MGN | Week 2  Week 5  Week 8 | * MGN agent installation * Source server replication initiation * Security Group configuration * Application Load Balancer setup * Network configuration | * Engage with customer change management |  |  | Replication in progress, infrastructure ready |
| **Build (Replatform)** | New environment setup | Week 2  Week 5  Week 8 | * New server builds in AWS * Security Group configuration * Application Load Balancer setup * Database replatforming * Network configuration |  |  |  | New infrastructure ready for migration |
| **Infrastructure Testing** | Internal validation | Week 3  Week 6  Week 9 | * Comprehensive infrastructure testing * Validation of build phase * Go/No-Go decision point | * Assist in testing and flag issues |  |  | Verified infrastructure readiness |
| **Non-Production Testing** | * Non-production environment migration * Three sequential phases (NP1, NP2, NP3) - 2 weeks of Internal Testing and 1 week of customer testing | Internal Weeks  4, 5, 7, 8  Customer Weeks  6,9 | * Rolling cutover of environments * Immediate testing initiation * Validation and verification (Internal & Customers) |  |  |  | Sign-off for each environment |
| **Final Testing Phase (Pre-Prod/Prod)** | Pre-production validation and Production deployment | Pre-Prod Week 10  Prod Week 11 | * Pre-production environment cutover * Full system integration testing * Performance validation * Production environment cutover * Business validation * Performance monitoring | * Validate migration * Complete testing and provide sign off |  |  | Final production sign-off by wave end date |