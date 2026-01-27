# Decision & Outcomes

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4891902034/Decision%20%26%20Outcomes

**Created by:** Alexandria Burke on June 25, 2025  
**Last modified by:** Shreya Singh on November 03, 2025 at 10:23 PM

---

This page contains the approved validations, confirming completion of the Landing Zone Assurance (LZA) review. The document package includes:

* Documented results from 'point-in-time' control testing/ activities.
* Recommendation on appropriate evidences in AWS for all applicable controls mapped to the LZA
* Confirmation of audit readiness for assessment purposes
* Validation of the as-built landing zone environment against the approved controls package

### **1. Document Results from Control Testing Activities**

**Goal:** Verify that each control in scope operates as intended.  
**Steps:**

1. Identify applicable controls from your control framework (e.g., HITRUST, NIST 800-53) mapped to LZA components.
2. Test procedures undertaken — e.g., inspect configurations, review logs, execute CLI queries, or use AWS Config rules / Security Hub findings.
3. Perform testing (skipped):

   * Use AWS CLI / Config to confirm control enforcement (e.g., encryption at rest, least privilege, SCPs).
   * Take screenshots, export CLI command outputs, or reference CloudFormation / Terraform states.
4. Record results: For each control, document test date, tester, method, outcome (pass/fail), and remediation if applicable.

### **2. Collect Evidence for All Applicable Controls Mapped to the LZA**

**Goal:** Gather artifacts demonstrating control implementation.

**Steps:**

1. Link the appropriate evidences in AWS for all applicable controls mapped to the LZA

### **3. Confirm Audit Readiness for Assessment Purposes**

**Goal:** Ensure all documentation and artifacts meet auditor expectations.  
**Steps:**

1. Review control testing documentation for completeness and consistency.
2. Confirm all gaps or findings have documented remediation plans.

### **4. Validate the As-Built Landing Zone Against the Approved Controls Package**

**Goal:** Confirm deployed configurations match approved control design.  
**Steps:**

1. Compare as-built architecture (AWS Org OUs, accounts, guardrails) to the approved controls matrix.
2. Verify key security baselines:

   * SCPs enforced on all OUs
   * CloudTrail centralized and immutable
   * Logging and encryption enabled
   * Cross-account roles and tags correctly applied
3. Document variances and either remediate or record them as accepted risk.
4. Obtain final compliance sign-off from Security and Compliance leads.

Together, these materials demonstrate that the LZA implementation meets defined compliance, security, and operational control objectives.

---

[draft for internal review] Milestone 10: Compliance Validation of LZA workload



## Jira Issues Table

**Query:** `(text ~ "Compliance Validation - Migration*" or summary ~ "Compliance Validation - Migration*") and project in (AWSM) ORDER BY created DESC`

**View in Jira:** [https://healthedge.atlassian.net/issues/?jql=(text%20~%20%22Compliance%20Validation%20-%20Migration*%22%20or%20summary%20~%20%22Compliance%20Validation%20-%20Migration*%22)%20and%20project%20in%20(AWSM)%20ORDER%20BY%20created%20DESC](https://healthedge.atlassian.net/issues/?jql=(text%20~%20%22Compliance%20Validation%20-%20Migration*%22%20or%20summary%20~%20%22Compliance%20Validation%20-%20Migration*%22)%20and%20project%20in%20(AWSM)%20ORDER%20BY%20created%20DESC)


| Type | Key | Summary | Assignee | Priority | Status | Updated |
|---|---|---|---|---|---|---|
| Story | AWSM-1194 | GC: Design and Configure Delphix Infrastructure Setup in AWS (wave 2b, us-west-2) | Senthil Ramasamy | Medium | Done | December 15, 2025 |
| Story | AWSM-1193 | HRP: Design and Configure Delphix Infrastructure Setup in AWS (wave 2b) | Senthil Ramasamy | Medium | Done | December 17, 2025 |
| Story | AWSM-1172 | Leverage LZA-Deployed KMS CMKs for Encryption | Alex Dixon | Medium | In Review | January 07, 2026 |
| Story | AWSM-1162 | Implement Audit Logging |  | Medium | To Do | December 09, 2025 |
| Story | AWSM-1153 | Generate Bubble Test Report with AD Isolation Validation |  | Medium | To Do | December 09, 2025 |
| Story | AWSM-1100 | Implement Tag Validation with SCPs and Tag Policies | John Cousens | Medium | In Review | January 07, 2026 |
| Task | AWSM-1051 | Configure Cluster Management Access in LZA Permission Sets | David Garibaldi | Medium | Done | December 19, 2025 |
| Story | AWSM-904 | LZA Compliance Validation Package | Shreya Singh | Medium | Done | December 12, 2025 |
| Task | AWSM-861 | Compliance Team Network Access | Jarrod Hermance | Medium | Done | December 09, 2025 |
| Story | AWSM-683 | Compliance Review - GC, HRP DR recommendations | Janmejay Singh | Medium | Done | October 07, 2025 |
| Task | AWSM-602 | Compliance Validation - Golden Image compliance baseline | Alexandria Burke | Medium | Done | October 07, 2025 |
| Task | AWSM-601 | Compliance Validation - Tag Management | Shreya Singh | Medium | Done | September 30, 2025 |
| Subtask | AWSM-596 | Compliance Validation - AWS DNS Design | Shreya Singh | Medium | Done | October 06, 2025 |
| Subtask | AWSM-540 | Compliance Validation - AWS VPC Endpoint Design | Shreya Singh | Medium | Done | October 06, 2025 |
| Subtask | AWSM-539 | Compliance Validation - Transit Gateway Design | Shreya Singh | Medium | Done | October 06, 2025 |
| Subtask | AWSM-538 | Compliance Validation - Direct Connect Design | Shreya Singh | Medium | Done | October 06, 2025 |
| Subtask | AWSM-537 | Compliance Validation - VPN Design | Shreya Singh | Medium | Done | October 06, 2025 |
| Subtask | AWSM-536 | Compliance Validation - Data Flows | Shreya Singh | Medium | Done | October 06, 2025 |
| Subtask | AWSM-535 | Compliance Validation - VPC Design  | Shreya Singh | Medium | Done | October 06, 2025 |


*Snapshot taken: January 12, 2026 02:52:48 UTC*

