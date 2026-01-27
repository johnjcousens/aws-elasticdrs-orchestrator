# Configuration Management

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4939415853/Configuration%20Management

**Created by:** Shreya Singh on July 17, 2025  
**Last modified by:** Shreya Singh on July 17, 2025 at 10:26 PM

---

**HITRUST Requirement – Compliance Assessments and Corrective Action Management**  
Control ID: 06.g Compliance with Security Policies and Standards  
Control Type: Procedural  
Control Level: Organizational Control  
HIPAA Mapping**:** 45 CFR §164.308(a)(1)(ii)(D) – Information System Activity Review

**Control Objective:**  
Ensure that regular compliance assessments are performed and that findings of non-compliance are addressed through root cause analysis, corrective actions, and follow-up validation to improve the security and privacy posture.

**Technical & Operational Implementation:**

1. **Annual Compliance Assessments**

   * Conduct formal compliance assessments at least annually to evaluate adherence to security, privacy, and regulatory requirements.
   * Assessments should include scope, schedule, responsible personnel, and documented procedures.
2. **Compliance Review Execution**

   * Reviews must be conducted by individuals with roles in security, privacy, internal audit, or external compliance functions.
   * Review processes should reference documented policies, technical configurations, logs, and other evidence of control effectiveness.
3. **Non-Compliance Identification and Response**

   * If any deficiencies are identified, management must:

     + Conduct a root cause analysis to determine the origin of non-compliance.
     + Assess whether systemic controls or user behaviors need correction.
     + Define corrective actions, assign owners, and document implementation.
     + Track corrective actions in a centralized issue tracking system or GRC platform.
     + Validate and review the effectiveness of actions taken.

**Possible Evidence to Collect:**

* Annual compliance assessment report with completion date and responsible parties
* Audit logs or evidence review checklists
* Meeting minutes showing discussion of non-compliance and root cause analysis
* Remediation plans with deadlines and assigned owners
* Tickets or GRC entries confirming implementation and validation of corrective actions
* Follow-up review reports verifying non-recurrence of the original issue

---

**HITRUST Requirement – Use of Automated Compliance Tools and Scanning**  
Control ID: 06.g Compliance with Security Policies and Standards  
Control Type: Technical  
Control Level: System-level Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(D) – Information System Activity Review

**Control Objective:**  
Enhance compliance monitoring efficiency and effectiveness by leveraging automation for assessments, scans, and evidence collection where feasible.

**Technical & Operational Implementation:**

1. **Automated Tool Utilization**

   * Deploy automated tools or platforms to perform compliance-related scans and checks (e.g., policy adherence, system misconfigurations, vulnerability scans, or access control audits).
   * Examples include AWS Config, Cloud Security Posture Management (CSPM) tools and compliance automation platforms like Vanta or Wiz.
2. **Integration with Compliance Frameworks**

   * Map tool capabilities to organizational compliance requirements (e.g., HITRUST, HIPAA, NIST, ISO 27001, SOC-2).
   * Configure automated checks to validate control coverage, alert on deviations, and log results.
3. **Monitoring and Reporting**

   * Ensure reports from compliance tools are retained in audit-ready formats.
   * Integrate tool output into dashboards for continuous compliance visibility.
   * Assign ownership to review and act on findings from automated scans.

**Possible Evidence to Collect:**

* Screenshots or configurations from compliance scanning tools
* Tool output logs showing recent automated scans and results
* Reports demonstrating mapping of automated controls to regulatory requirements
* Workflow or ticketing system logs showing actions taken based on scan results
* Policies or procedures documenting the requirement to use automation where applicable

---

**HITRUST Requirement – Continuous Monitoring Program Implementation**  
Control ID: 06.g Compliance with Security Policies and Standards  
Control Type: Operational  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(D) – Information System Activity Review

**Control Objective:**  
Establish a structured and responsive continuous monitoring program that ensures timely detection of security issues and ongoing assessment of compliance posture.

**Technical & Operational Implementation:**

1. **Defined Metrics and Assessment Cadence**

   * Define and document key performance and risk indicators to be evaluated at least annually.
   * Conduct annual internal compliance reviews across all business units.
2. **Independent Validation**

   * Arrange bi-annual assessments by third-party auditors or external consultants to verify objectivity and coverage.
   * Ensure alignment with regulatory or framework-specific requirements (e.g., HITRUST r2, ISO 27001).
3. **Ongoing Monitoring Strategy**

   * Maintain a formal continuous monitoring plan that includes frequency, scope, responsible parties, and data sources.
   * Monitor logs, alerts, configurations, and asset status using tools such as AWS Security Hub, CloudTrail, or SIEMs.
4. **Analysis and Correlation**

   * Aggregate and correlate data from assessments, monitoring tools, and alerts to identify risks or deviations.
   * Leverage automation where possible to identify trends or anomalies.
5. **Remediation and Reporting**

   * Initiate corrective actions based on analysis results with appropriate prioritization.
   * Report the security status monthly to executive leadership and regulatory authorities when applicable.

---

**Possible Evidence to Collect:**

* Continuous monitoring strategy document or policy
* List of defined security metrics and thresholds
* Internal and external assessment schedules and results
* Logs or dashboards showing ongoing monitoring activity
* Monthly security posture reports submitted to leadership
* Tickets or workflows demonstrating response actions
* Agreements with third-party assessors

---

**HITRUST Requirement – Independent Continuous Monitoring Assessors**  
Control ID: 06.g Compliance with Security Policies and Standards  
Control Type: Operational  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(D) – Information System Activity Review

**Control Objective:**  
Ensure the integrity and effectiveness of the continuous monitoring program by assigning qualified and appropriately independent assessment personnel.

**Technical & Operational Implementation:**

1. **Assignment of Monitoring Roles**

   * Designate internal assessors or engage assessment teams to monitor implemented security controls across systems, applications, and infrastructure.
   * Ensure assessors are familiar with the organization's technical environment and regulatory obligations.
2. **Assessor Independence Requirements**

   * Establish a minimum independence requirement for assessors aligned with the organization’s risk management framework and continuous monitoring strategy.
   * Implement safeguards to prevent conflicts of interest (e.g., separation from system ownership or operational roles).
3. **Ongoing Monitoring and Verification**

   * Incorporate periodic reviews of assessor assignments to validate their objectivity.
   * Ensure assessment results are reviewed by oversight bodies (e.g., security steering committees, compliance leads).

**Possible Evidence to Collect:**

* Continuous monitoring policy identifying use of assessors
* Documentation of assessor roles, responsibilities, and independence criteria
* Org chart or RACI matrix showing segregation of duties
* Signed attestations or conflict-of-interest statements from assessors
* Internal audit reports or summaries showing independent control review
* Evidence of periodic monitoring reviews conducted by designated teams

---

**HITRUST Requirement – Security Compliance Reviews and Metrics Tracking**  
Control ID: 06.g Compliance with Security Policies and Standards  
Control Type: Procedural  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(A) – Risk Analysis

**Control Objective:**  
Ensure that the internal security organization performs regular compliance reviews and maintains actionable security metrics to inform risk assessments and long-term planning.

**Technical & Operational Implementation:**

1. **Periodic Compliance Review Integration**

   * Integrate compliance reviews of information processing activities into the organization’s formal risk assessment schedule.
   * Define review frequency and scope in accordance with organizational risk appetite, compliance obligations, and system criticality.
2. **Security Metrics and Results Tracking**

   * Establish standardized metrics (e.g., number of violations, policy exceptions, patch compliance rate) for measuring compliance results across systems.
   * Maintain a secure repository of compliance records, ensuring traceability and auditability.
   * Leverage trend analysis to detect recurring patterns, prioritize security improvements, and support risk-informed decision making.
3. **Linkage to Risk Management**

   * Correlate compliance results with threat intelligence, incident trends, and vulnerability scan outcomes.
   * Feed this data into the organization’s broader risk management framework to support long-term mitigation strategies and audit readiness.

**Possible Evidence to Collect:**

* Internal compliance review schedules and meeting minutes
* Documented security metrics definitions and thresholds
* Historical compliance reports and dashboards
* Risk assessment reports referencing compliance input
* Logs or records of identified non-compliance and follow-up actions
* Trend analyses or executive summaries showing long-term concerns

---

**HITRUST Requirement – Documentation and Approval of Compliance Review Outcomes**  
Control ID: 06.g Compliance with Security Policies and Standards  
Control Type: Procedural  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(D) – Information System Activity Review

**Control Objective:**  
Ensure that the results and recommendations of compliance reviews are formally recorded and validated through appropriate management oversight.

**Technical & Operational Implementation:**

1. **Compliance Review Documentation**

   * Record all compliance review findings, including identified gaps, associated risks, and recommended remediations.
   * Include scope, methodology, evidence reviewed, and relevant timelines in the documentation.
2. **Management Review and Approval**

   * Submit compliance review reports and recommendations to designated management personnel for validation.
   * Ensure that review approvals are formally recorded (e.g., via signature, email confirmation, or meeting minutes).
   * Use approval as a trigger for initiating remediation actions or adjusting risk posture.

**Possible Evidence to Collect:**

* Compliance review reports with embedded findings and recommendations
* Audit trails or approval logs showing management sign-off
* Meeting notes or attestations confirming management oversight
* Policy or SOP describing the compliance review and approval workflow
* Tracker showing review outcomes and responsible approvers

---

**HITRUST Requirement – Technical Security Configuration Compliance Reviews**  
Control ID: 06.h Technical Compliance Checking  
Control Type: Technical/Procedural  
Control Level: System & Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(A) – Risk Analysis  
  
 **Control Objective:**  
Ensure the security configuration of systems is regularly validated and any configuration drift or non-compliance is detected and remediated in a timely and documented manner.

**Technical & Operational Implementation:**

1. **Annual Configuration Review**

   * Conduct technical configuration reviews of all relevant systems at least annually.
   * Use experienced personnel or automated compliance tools (e.g., SCAP scanners, AWS Config, CIS-CAT, Nessus).
   * Assess configurations against approved baselines such as CIS Benchmarks, DISA STIGs, or organizational hardening guides.
2. **Non-Compliance Handling Process**

   * Investigate and document root causes of any deviation from approved configurations.
   * Analyze whether control gaps could lead to reoccurrence or security incidents.
   * Define and implement corrective actions through formal ticketing or change management processes.
   * Validate remediation effectiveness through follow-up testing or re-scans.

**Possible Evidence to Collect:**

* Configuration scan reports or manual review checklists
* List of configuration baselines and system-specific deviation logs
* Root cause analysis (RCA) documentation for non-compliant systems
* Change tickets or remediation logs tied to the issues found
* Review meeting notes or approvals confirming corrective actions

---

**HITRUST Requirement – Technical Configuration Compliance Reviews**  
Control ID: 06.h Technical Compliance Checking  
Control Type: Technical  
Control Level: System-Level Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(A) – Risk Analysis

### **Control Objective:**

Ensure that technical configurations of systems are regularly reviewed for compliance with security baselines using expert personnel, automated tools, and risk-based criteria to detect and remediate deviations.

**Technical & Operational Implementation:**

**Use of Qualified Technical Personnel**

* Assign experienced technical specialists (e.g., Security Engineers or System Administrators) to perform configuration compliance checks.
* Validate personnel qualifications through job descriptions, training records, or certifications.

**Use of Industry-Standard Automated Tools**

* Implement automated compliance tools such as:

  + AWS Config for continuous resource configuration checks
  + AWS Inspector for vulnerability scanning
  + AWS Security Hub for consolidated security findings

**Automated Report Generation**

* Use tools that generate technical reports detailing compliance status, misconfigurations, and remediation timelines.
* Store reports in a centralized location (e.g., S3, document repository, audit log systems).

**Annual Review Cadence**

* Perform comprehensive configuration reviews at least annually across all in-scope systems.
* Include configuration validation in the organization’s annual governance or audit calendar.

**Risk-Based Frequency Enhancements**

* For high-risk systems or major changes (e.g., OS upgrades, control failures), increase check frequency.
* Tie compliance check triggers to the organization’s formal risk assessment process.

**Possible Evidence to Collect:**

* Job descriptions or org charts showing designated technical compliance personnel
* Tool output logs (e.g., AWS Config rule evaluations, Inspector reports)
* Compliance scan schedules and change management tickets
* Versioned technical configuration reports with interpretation notes
* Risk assessment records indicating when increased frequency was warranted
* Annual audit logs or checklists showing technical control validations

---

**HITRUST Requirement – Technical Compliance Validation for Interoperability**  
Control ID: 06.h – Technical Configuration Standards and Validation  
Control Type: Technical  
Control Level: System-Level Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(A) – Risk Analysis

**Control Objective:**

Demonstrate and validate technical compliance to support secure, standards-based interoperability across systems and platforms.

### **Technical & Operational Implementation:**

**Interoperability-Centric Compliance Framework**

* Implement compliance checks that validate adherence to interoperability standards (e.g., HL7, FHIR, DICOM, IHE profiles).
* Embed these checks into system integration and deployment processes.

**Tooling and Standards Mapping**

* Use automated tools and validation suites that assess conformance to recognized technical standards (e.g., NIST SP 800-53, ONC Interoperability Standards, OWASP guidelines).

**Evidence of Compliance**

* Ensure the compliance validation generates documented evidence demonstrating that system configurations, protocols, and data exchanges conform to interoperability expectations.
* Integrate validation results into CI/CD pipelines or configuration management workflows.

**Ongoing Review and Maintenance**

* Align technical compliance validation with system lifecycle events such as integration milestones, upgrades, or interoperability testing rounds.
* Include interoperability-focused controls in continuous compliance scanning routines (e.g., AWS Config rules for encryption protocols or VPC peering settings).

### **Possible Evidence to Collect:**

* Compliance reports showing adherence to interoperability standards
* Output from interoperability testing tools (e.g., Inferno for FHIR, NIST test suites)
* Documentation showing mapping of system architecture to interoperability controls
* Change tickets or CI/CD pipeline logs showing validation during system updates
* Internal policy referencing interoperability-specific compliance mandates
* System design documents or interface specifications validated by compliance tooling

---

**HITRUST Requirement – Change Control for Information Systems**  
Control ID: 09.b Change Management  
Control Type: Technical / Procedural  
Control Level: System-Level Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(B) – Risk Management

**Control Objective:**

Ensure that all changes to information systems—including applications, infrastructure, configurations, and databases—are properly documented, tested, and approved to minimize disruption and maintain security posture.

**Technical & Operational Implementation:**

**Documented Change Management Process**

* Establish a formal change control process within the organization’s ITSM (e.g., ServiceNow, Jira, Remedy).
* Require that all changes are logged with a detailed description, reason, associated risk, and affected components.

**Testing Before Deployment**

* Validate changes in a development or staging environment before production deployment.
* Use automated testing frameworks (e.g., unit tests, regression tests, infrastructure testing via AWS CloudFormation StackSets or Terraform plans).
* For infrastructure changes, tools like AWS Config and Inspector can ensure changes meet security benchmarks.

**Approval Workflow**

* Implement tiered approval based on change risk (e.g., minor vs. major changes).
* Require sign-offs from security, compliance, and application owners when applicable.
* Use IAM roles and audit logs in tools like AWS Systems Manager and CodePipeline to enforce approval controls.

**Exceptions for Automated Security Patches**

* Define and document exceptions for low-risk changes (e.g., automated OS patches using AWS Systems Manager Patch Manager).
* Even in exceptions, ensure monitoring and rollback mechanisms are in place.

**Possible Evidence to Collect:**

* Change request tickets with timestamps and approver names
* Pre-deployment and post-deployment test logs
* Change management policy or standard operating procedures (SOPs)
* Evidence of approval workflow execution (e.g., ServiceNow approvals)
* Audit logs from source control or CI/CD platforms (e.g., GitHub, CodePipeline)
* Screenshots or export logs from AWS Config showing baseline changes

---

**HITRUST Requirement – Strict & Controlled Change Management**  
Control ID: 09.b Change Management  
Control Type: Technical + Operational  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(B) – Risk Management; §164.308(a)(1)(ii)(D) – Information System Activity Review

**Control Objective:**  
Ensure all changes to equipment, software, configurations, and operating procedures are consistently managed, recorded, assessed for business and security impact, formally approved, and communicated to affected stakeholders before implementation.

**Technical & Operational Implementation:**

1. **Central Change Control Governance**

Establish an enterprise change management process (ITSM) that classifies and routes changes (standard, normal, emergency). Integrate with ServiceNow, Jira Service Management, or AWS Systems Manager Change Manager to enforce workflow consistency.

2. **Identification & Recording of Significant Changes**

Require every non-trivial change (infrastructure, code, configuration, network, database) to generate a change record with requester, scope, affected assets, risk rating, planned window, and rollback plan. Auto-ingest AWS CloudTrail and AWS Config change data to enrich records.

3. **Planning & Testing of Changes**

Mandate pre-prod testing in segregated environments. Use infrastructure-as-code preview capabilities (AWS CloudFormation Change Sets, Terraform plan) and blue/green or canary deployments (AWS CodeDeploy, Elastic Beanstalk, ECS/EC2 rolling updates) to validate functionality and rollback paths.

4. **Impact & Security Assessment**

Evaluate operational, compliance, and security impacts for each significant change. Use automated policy checks (AWS Config conformance packs, cfn-guard, OpenSCAP) and vulnerability/permission analysis (AWS Inspector, Access Analyzer) to detect risk before approval.

5. **Formal Approval Workflow**

Route change tickets through required approvers: system owner, security, operations, and CAB (Change Advisory Board) depending on risk tier. Enforce approval gates in AWS Systems Manager Change Manager or CI/CD pipelines (CodePipeline manual approval steps).

6. **Stakeholder Communication & Scheduling**

Notify relevant personnel (Ops, Security, Help Desk, Business Owner) ahead of change windows via integrated notifications (SNS, Slack/Teams webhooks). Publish change calendars; include outage expectations and rollback criteria. Post-implementation, distribute completion status and any deviations.

**Possible Evidence to Collect:**

* Change management policy and workflow diagrams
* Sample change tickets showing description, testing evidence, impact analysis, and approvals
* AWS Systems Manager Change Manager or ServiceNow export of approved changes
* CloudFormation Change Set and deployment logs demonstrating pre-change review
* AWS Config history showing tracked configuration deltas tied to change IDs
* CAB meeting minutes or approval records
* Stakeholder notification logs (SNS, email) for high-impact changes
* Post-change review / rollback documentation and metrics on change success rate

---

**HITRUST Requirement – Defined and Implemented Fallback Procedures**  
Control ID: 09.b Change Management  
Control Type: Operational  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(7)(ii)(B) – Disaster Recovery Plan (DRP)

**Control Objective:**  
Ensure the organization is prepared to recover from unsuccessful changes and unexpected disruptions by establishing clearly defined and implemented fallback procedures, including assigned roles and responsibilities.

**Technical & Operational Implementation:**

1. **Fallback Planning and Documentation**  
   Develop fallback procedures as part of change management, DRP, and BCP processes. These procedures should define the steps to abort and reverse changes if they result in system instability, data corruption, or service disruption.
2. **Implementation of Fallback Plans**  
   Integrate fallback plans into operational runbooks or playbooks for infrastructure, applications, and configurations. Use version-controlled documentation to ensure procedures are current and repeatable.
3. **Automation and Tooling**  
   Use AWS services such as:

* AWS CloudFormation Rollback Triggers to automatically revert failed deployments,
* AWS CodeDeploy Blue/Green Deployment with automatic rollback on failure,
* AWS Backup and EBS Snapshots for rapid restoration of data and systems prior to change events.

4. **Role Assignments and Responsibilities :** Clearly define responsibility for initiating fallback, including escalation paths. Assign fallback responsibilities to relevant roles (e.g., DevOps Engineer, Incident Commander, or Change Manager). Include them in the RACI matrix.
5. **Testing and Validation**  
   Periodically test fallback procedures during tabletop exercises or scheduled change windows to ensure operational effectiveness. Incorporate learnings from incident mortems.

**Possible Evidence to Collect:**

* Documented fallback procedures with step-by-step rollback instructions
* AWS deployment logs showing automated rollback events
* RACI chart or role documentation defining fallback responsibilities
* Change records including rollback plan fields
* Evidence of periodic fallback testing (e.g., test results, meeting minutes)
* Post-incident reports describing invocation of fallback procedures and outcome

---

**HITRUST Requirement – Control and Archival of Information Asset Changes**  
Control ID: 09.b Change Management  
Control Type: Technical  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that all changes to information systems, networks, and services are systematically managed and archived to support traceability, accountability, and post-incident analysis.

**Technical & Operational Implementation:**

1. **Change Control Enforcement**  
   Establish a formal change management process to control updates to systems, networks, and services. All proposed changes should be logged, reviewed, approved, and implemented through structured workflows. Use services such as:

* AWS Systems Manager Change Manager for centralized change control
* AWS Config to track and audit changes to infrastructure resources
* AWS CloudTrail for monitoring and recording API activity and user actions

2. **Archival and Audit Logging**  
   Implement automated archival mechanisms to store change histories, including timestamps, actors, affected resources, and change descriptions. Services that support this include:

* Amazon S3 with versioning and object lock for secure change archiving
* CloudTrail logs stored in S3, with AWS Backup for retention management
* AWS Config snapshots to preserve configurations pre/post change

3. **Retention and Access Controls :** Define retention periods and ensure archival data is protected against unauthorized alteration or deletion. Use IAM, S3 bucket policies, and AWS KMS for secure and auditable storage.

**Possible Evidence to Collect:**

* Change request logs showing tracking and approvals
* AWS Config and CloudTrail configuration evidence
* Screenshots or reports showing archived system/network changes
* Change control policy referencing archival requirements
* Access logs or encryption policies applied to archived data
* Sample of version-controlled infrastructure-as-code repositories (e.g., Terraform)

---

**HITRUST Requirement – Separation of Production and Non-Production Environments**  
Control ID: 09.d Separation of Development, Test, and Operational Environments  
Control Type: Technical  
Control Level: Organizational Control  
HIPAA Mapping**:** 45 CFR §164.308(a)(1)(ii)(B) – Information Access Management

**Control Objective:**  
Prevent unintended impacts to operational systems by ensuring that development, test, and quality assurance environments are logically or physically separated from production systems.

**Technical & Operational Implementation:**

**Environment Segregation**

* Enforce network segmentation using VPCs, subnets, or firewall rules to isolate production from dev/test/staging environments.
* Apply separate IAM roles and permissions per environment to enforce least privilege access and prevent unauthorized changes.

**Access Control and Resource Tagging**

* Use IAM policies with environment-specific tags and ABAC (Attribute-Based Access Control) to restrict access based on environment.
* Implement resource-level tagging (e.g., `Environment=Prod` or `Environment=Dev`) across services like EC2, RDS, and S3.

**Deployment and Pipeline Governance**

* Use AWS CodePipeline or CodeDeploy with gated approvals between stages.
* Ensure that automated tests and approvals occur before promoting artifacts from dev/test to production stages.

**Monitoring and Enforcement**

* Monitor changes using AWS Config rules to detect unauthorized resource creation or modification across environments.
* Enforce compliance using Service Control Policies (SCPs) and Config Conformance Packs within AWS Organizations.

**Possible Evidence to Collect:**

* Architecture diagrams showing environment separation
* IAM policy samples restricting cross-environment access
* Network security group/firewall rules illustrating isolation
* Dev/prod tagging and ABAC policy configurations
* Deployment pipeline configurations with approval gates
* AWS Config rule compliance reports showing enforcement

---

**HITRUST Requirement – Secure Configuration and Maintenance of Operational Systems**  
Control ID: 10.h Control of Operational Software  
Control Type: Technical  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(B) – Information System Security Configuration

**Control Objective:**  
Ensure that operational systems and vendor-supplied software are maintained securely by using supported versions, applying secure baseline configurations, and preventing system misuse.

**Technical Implementation:**

**Vendor-Supported Software Maintenance**

* Maintain software at a version actively supported by the vendor to ensure availability of patches and technical support.
* Monitor vendor end-of-support dates using a configuration management database (CMDB) or lifecycle tracking tools.

**Web Browser Security**

* Use latest supported browser versions on all operational systems to leverage up-to-date security features.
* Configure browsers with hardened security settings (e.g., disable legacy plugins, enable site isolation).

**Baseline Configuration Management**

* Establish and maintain a secure baseline configuration using AWS Systems Manager State Manager, OpsWorks, or EC2 Image Builder.
* Enforce compliance with baseline configurations using AWS Config rules and AWS Security Hub.

**Security Parameter Configuration**

* Set and enforce system-level security parameters such as password policies, logging settings, and access control defaults.
* Use automation tools (e.g., AWS SSM Run Command) to verify and enforce configuration settings at scale.

**Possible Evidence to Collect:**

* Inventory of vendor software with support status and patch levels
* Browser version control policy and audit logs
* Baseline configuration templates (e.g., AMIs, EC2 Launch Templates)
* AWS Config rule compliance snapshots
* SSM or GPO logs showing parameter enforcement
* Screenshots or policy documentation on security configuration standards

---

**HITRUST Requirement – Software Authorization and Inventory Control**  
Control ID: 10.h Control of Operational Software  
Control Type: Technical  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.310(d)(1) – Device and Media Controls

**Control Objective:**  
Ensure that only authorized software is installed and used on business systems by maintaining a current inventory to support operational integrity and prevent unauthorized software risks.

**Technical Implementation:**

**Authorized Software Inventory**

* Maintain a centrally managed and regularly updated list of approved software applications required for business purposes.
* Categorize software by purpose, owner, licensing status, and associated risk (e.g., productivity, security, development).

**Inventory Enforcement Tools**

* Use AWS services such as AWS Systems Manager Inventory, AWS Config, or Amazon Inspector to automatically track installed software on EC2 instances and other managed nodes.
* Establish guardrails using AWS Service Catalog or Control Tower Account Factory to restrict provisioning of non-authorized software.

**Review and Update Process**

* Review the authorized software list quarterly or during major IT lifecycle updates.
* Include review checkpoints as part of procurement and software onboarding workflows.

**Possible Evidence to Collect:**

* Master list of authorized software (CSV, CMDB exports, or policy documents)
* Output of AWS Systems Manager Inventory reports
* Screenshots of AWS Config compliance reports
* Version-controlled documentation of software review and approval workflows
* Security policy sections on approved software usage

---

**HITRUST Requirement – Application Allow Listing Enforcement**  
Control ID: 10.h Control of Operational Software  
Control Type: Technical  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.312(c)(1) – Integrity Controls

**Control Objective:**  
Ensure only authorized applications are permitted to execute on systems by implementing application allow listing technology, thereby reducing the risk of unauthorized or malicious software execution.

**Technical & Operational Implementation:**

**Allow Listing Implementation**

* Deploy allow listing technology (e.g., AWS Systems Manager Application Manager, third-party endpoint protection platforms, or host-based firewalls) that enforces execution of only authorized software.
* Configure systems to deny execution of all software not explicitly allow-listed.
* Apply policies across all endpoints and servers through centralized configuration management.

**Rules and Governance**

* Define rules for authorized software execution based on job role, business function, or operational need.
* Ensure the allow list includes software terms of use and licensing conditions as applicable.
* Update allow lists in response to new deployments, deprecations, or software risk assessments.

**Enforcement Scope and Exceptions**

* Apply allow listing across production, development, and administrative environments.
* Document and approve any exceptions through a formal change control process.

**Possible Evidence to Collect:**

* Screenshot or config output from allow listing solution (e.g., AWS Systems Manager, Carbon Black, CrowdStrike)
* Policy documents describing allow listing rules and software approval workflows
* Audit logs showing enforcement or blocks of unauthorized executables
* System baseline reports reflecting approved application signatures
* Exception documentation with business justification and approval

---

**HITRUST Requirement – Pre-Implementation Testing of Applications and Operating Systems**  
Control ID: 10.h Control of Operational Software  
Control Type: Technical  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(A) – Risk Analysis

**Control Objective:**  
Ensure new or updated applications and operating systems are tested for functionality, security, and potential impacts before being implemented in production environments.

**Technical & Operational Implementation:**

**Testing Requirement Before Deployment**

* Enforce that all applications and OS updates are subject to formal testing prior to implementation in production.
* Define testing phases in system development and patch management procedures.

**Testing Scope**

* Conduct usability testing to confirm functionality aligns with user requirements.
* Perform security testing including vulnerability scans and penetration tests to identify risks.
* Assess the impact of changes on integrated or dependent systems.
* Require all testing be performed in separate, isolated environments (e.g., AWS staging accounts, test VPCs).

**Tooling and Documentation**

* Use CI/CD pipelines integrated with security and unit test automation (e.g., AWS CodePipeline, CodeBuild with test runners).
* Maintain test plans, results, and approval workflows in systems like AWS CodeCommit, Jira, or ServiceNow.

**Possible Evidence to Collect:**

* Test cases and results from QA systems or CI pipelines
* Change control records showing test completion before deployment
* Screenshots or audit logs from test environments
* Documentation of separate non-production environments (e.g., dev/test/staging)
* Security assessment reports tied to new releases

---

**HITRUST Requirement – Enforcement of Software Execution Rules**  
Control ID: 10.h Control of Operational Software  
Control Type: Technical  
Control Level: System-Level Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(B) – Security Management Process (Risk Management)

**Control Objective:**  
Prevent execution of unauthorized software by maintaining a disallow list and enforcing rules around software usage.

**Technical & Operational Implementation:**

**Disallow List Implementation**

* Configure systems to block execution of software that appears on an enterprise-defined unauthorized list.
* Implement endpoint protection tools (e.g., AWS Systems Manager, GuardDuty, or third-party EDR like CrowdStrike) to monitor and enforce the disallow list.

**Software Usage Policy Enforcement**

* Develop policy-based rules to allow software execution only under specific conditions, such as license validation, business justification, or IT approval.
* Use configuration management tools (e.g., AWS Config, OpsWorks, or Chef/Puppet integrated with AWS) to enforce rules on system startup and during runtime.

**Monitoring and Response**

* Continuously monitor endpoint activity for attempts to execute disallowed programs.
* Trigger CloudWatch or GuardDuty alerts on unauthorized execution attempts.

**Possible Evidence to Collect:**

* List of disallowed software maintained in CMDB or policy documents
* Screenshots or logs showing software blocks by endpoint protection tools
* Configuration scripts or automation (e.g., Systems Manager State Manager documents) implementing execution restrictions
* Policies defining terms and conditions for allowed software usage
* Audit trail of blocked execution attempts with timestamp and response actions

---

**HITRUST Requirement – Management of Unauthorized Software (Disallow Listing)**  
**Control ID:** 10.h Control of Operational Software  
**Control Type:** Technical  
**Control Level:** System-Level Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(B) – Security Management Process (Risk Management)

**Control Objective:**  
Prevent the execution of unauthorized or unapproved software by maintaining and regularly updating a disallow list and enforcing policies across all device types.

**Technical & Operational Implementation:**

**Asset-Type Specific Identification**

* Use automated scanning tools (e.g., AWS Systems Manager Inventory, AWS Inspector, or third-party tools like CrowdStrike or Tanium) to detect unauthorized software on: Servers, Workstations and Laptops.

**Policy Enforcement via Deny-by-Exception**

* Implement allow-all, deny-by-exception software control models using endpoint security software or Group Policy Objects (GPOs).
* Integrate AWS Systems Manager State Manager or custom Lambda scripts for policy enforcement.

**Disallow List Management**

* Maintain a centralized disallow list repository (e.g., via AWS Config or CMDB systems).
* Review and update this list at least annually, using software inventory results and risk assessments.

**Possible Evidence to Collect:**

* Inventory scans or dashboards showing detected unauthorized software by asset type
* Disallow list documentation and update logs
* Policy documents describing deny-by-exception controls
* System Manager or EDR configuration enforcing execution blocks
* Internal audit reports or screenshots confirming periodic reviews of the disallow list
* Meeting minutes or tickets showing annual review cycles for software authorization

---

**HITRUST Requirement – Configuration Control & Archival of Software Versions**  
Control ID: 10.h Control of Operational Software  
Control Type: Technical & Operational  
Control Level: System-Level Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(C) – Sanction Policy / 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure implemented software and associated artifacts are tracked, archived, and retained appropriately for contingency, restoration, and compliance with data retention policies.

**Technical & Operational Implementation:**

**Software Configuration Tracking**

* Implement a configuration control system (e.g., AWS Config, AWS Systems Manager, Git repositories) to track software and associated documentation across all environments.
* Maintain version control for application software through CI/CD pipelines (e.g., AWS CodeCommit, CodePipeline, or GitHub/GitLab).

**Archiving and Contingency Measures**

* Archive all old and replaced software versions in a secure storage location (e.g., Amazon S3 with appropriate lifecycle policies).
* Ensure that all archived artifacts include:

  + Required configuration parameters
  + Deployment procedures
  + Supporting files and installation metadata

**Retention & Restoration Preparedness**

* Align retention with organizational data retention policies (e.g., AWS Backup or custom policies using S3 object lifecycle).
* Tag archived items with version metadata and timestamps for traceability and rollback preparedness.

**Possible Evidence to Collect:**

* Configuration control system audit logs or exports
* Archived version list with metadata (e.g., S3 bucket versioning logs, Git tags/releases)
* CI/CD or change control tickets referencing archived software and rollback capabilities
* Documented procedures for archival and retrieval
* Retention policy documents
* Screenshots or logs showing backup of older configurations in line with retention settings

---

**HITRUST Requirement – Change Rollback Strategy & Audit Logging**  
Control ID: 10.h Control of Operational Software  
Control Type: Technical & Operational  
Control Level: System-Level Control  
HIPAA Mapping: 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure changes to operational software are controlled and auditable, and that rollback mechanisms are in place to maintain system stability and recoverability.

**Technical & Operational Implementation:**

**Rollback Strategy**

* Document rollback procedures for all significant system changes, including infrastructure-as-code and application deployments.
* Require rollback testing or staging validation before production deployments.
* Use AWS services such as AWS CodeDeploy with automatic rollback or AWS CloudFormation with rollback-on-failure options.

**Audit Logging**

* Maintain audit logs for all changes to operational software, libraries, and scripts.
* Leverage tools like AWS CloudTrail, AWS Config, and centralized logging (e.g., Amazon CloudWatch Logs or OpenSearch) to record:

  + Change initiators
  + Timestamps
  + Affected components
* Store audit logs in immutable, tamper-evident storage (e.g., S3 with Object Lock and versioning).

**Possible Evidence to Collect:**

* Change control procedures including rollback planning
* Deployment scripts with integrated rollback paths
* Audit trail logs of software/library changes (e.g., Git history, AWS CloudTrail events)
* Evidence of tested rollback scenarios (e.g., from CI/CD pipelines)
* Audit log retention configuration (e.g., S3 bucket lifecycle settings)
* Change control tickets referencing rollback and validation steps

---

**HITRUST Requirement – Supplier Access Controls**  
Control ID: 10.h Control of Operational Software  
Control Type: Technical & Operational  
Control Level: System-Level Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(D) – Information System Activity Review

**Control Objective:**  
Restrict and monitor supplier access to organizational systems to prevent unauthorized use, ensure accountability, and maintain system security during support activities.

**Technical & Operational Implementation:**

**Access Authorization**

* Grant suppliers physical or logical access only when essential for support activities.
* Require written management approval before provisioning any access.
* Ensure time-bound, role-based access is used where possible.
* Implement JIT (Just-In-Time) access provisioning using tools like AWS IAM Identity Center or AWS SSM Session Manager for cloud environments.

**Monitoring and Oversight**

* Monitor supplier sessions using audit tools (e.g., AWS CloudTrail, GuardDuty, or SIEM platforms).
* Log all access requests, approvals, and activities performed by suppliers.
* Use screen/session recording where feasible for high-privilege access (e.g., AWS Systems Manager Session Manager with logging to S3/CloudWatch).

**Possible Evidence to Collect:**

* Third-party access policy or supplier access procedure
* Access approval records and logs
* AWS IAM role usage logs (with `AssumeRole` events for vendors)
* SSM Session Manager logs and session transcripts
* Monitoring dashboard screenshots or logs showing supplier activity
* Audit trail for supplier access sessions with timestamps and approver info
* Risk assessment or review reports for supplier access events

---

**HITRUST Requirement – Secure Update and Release Management**  
**Control ID:** 10.h Control of Operational Software  
**Control Type:** Technical & Operational  
**Control Level:** System-Level Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(B) – Risk Management

**Control Objective:**  
Ensure that only authorized personnel perform updates to operational systems and that updates are assessed for business, security, and privacy impacts prior to deployment.

**Technical & Operational Implementation:**

**Authorized Update Execution**

* Updates to operational software, applications, and program libraries are strictly performed by authorized administrators.
* Use of IAM roles or AD group-based privilege escalation with logging (e.g., AWS IAM with scoped permissions or SSM Change Manager).
* Enforce separation of duties through automation pipelines and approval workflows (e.g., CodePipeline + manual approval step).

**Code Execution and Environment Hardening**

* Restrict operational systems to run only signed or approved executables; no compiler or dev tools should exist in production.
* Use allowlisting technologies or container security policies (e.g., AWS Inspector, GuardDuty, or KSPM tools).

**Upgrade Risk Evaluation**

* Prior to release upgrades, assess:

  + Business justification (e.g., documented in RFCs or CRs)
  + Security impact analysis (vulnerability exposure, patch impact)
  + Privacy risks (data exposure, logging behavior)
* Use integrated tools (e.g., Jira, ServiceNow) to document and track risk assessment and approvals.

**Possible Evidence to Collect:**

* Change control policy and SOPs showing authorized update process
* IAM policy assignments or admin role access logs
* ServiceNow or Jira records showing business justification and approval
* Documentation of security/privacy impact assessments for recent releases
* Screenshots or logs showing software allowlisting or signed binary enforcement
* Output from tools like AWS Inspector or SSM Patch Manager with validation checks

---

**HITRUST Requirement – Migration Planning for Unsupported Systems**  
Control ID: 10.h Control of Operational Software  
Control Type: Operational  
Control Level: System-Level Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(B) – Risk Management

**Control Objective:**  
Ensure unsupported system components are identified and formally addressed through management-approved migration or replacement strategies to reduce operational and security risks.

**Technical & Operational Implementation:**

**Inventory and Support Status Monitoring**

* Maintain a system inventory with metadata for vendor support lifecycle (e.g., AWS Systems Manager Inventory or CMDB integration).
* Automate EOL/EOS detection using tools like AWS Config custom rules, Nessus, or Qualys asset lifecycle tracking.

**Formal Migration Planning**

* When unsupported components are detected:

  + Document a formal migration/replacement plan
  + Obtain management approval
  + Include risk, resource, timeline, and rollback sections
* Plans must align with enterprise architecture and security strategy.

**AWS-Specific Examples**

* Replace EC2 instances running unsupported OS versions (e.g., Windows Server 2012) with current AMIs.
* Leverage AWS Systems Manager Patch Manager for identifying and auto-remediating outdated OS/software.

**Possible Evidence to Collect:**

* Approved migration/replacement plans (e.g., PDFs, Confluence, ServiceNow records)
* CMDB entries indicating unsupported components
* Management signoff emails or tickets
* Asset inventory report with support status metadata
* Project plans showing budget/resource allocation for replacement
* Meeting notes discussing EOL systems and mitigation strategies

---

**HITRUST Requirement – OS-Level Technical Baseline Controls**  
**Control ID:** 10.h Control of Operational Software  
**Control Type:** Technical  
**Control Level:** System-Level Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(B) – Risk Management  
  
 **Control Objective:**  
Ensure that all operating systems enforce a standardized and secure baseline that includes core security technologies to protect against malicious activity and unauthorized changes.

**Technical & Operational Implementation:**

**Baseline Configuration Standards**

* Establish and enforce OS-specific baseline security standards (e.g., STIG, CIS Benchmarks).
* Document required tools and configurations for antivirus, logging, and host-based protection.

**Technical Control Implementation**

* **Antivirus/EDR:** Deploy endpoint protection tools (e.g., CrowdStrike, Defender for Endpoint, Sophos)

  + Ensure real-time protection and scheduled scans are enabled
* **File Integrity Monitoring (FIM):** Use tools like AWS CloudWatch Agent with custom scripts or Tripwire/Splunk FIM modules
* **Host-Based Firewalls/Filtering:** Configure `iptables`/`firewalld` on Linux or Windows Firewall with Group Policy
* **Logging:** Enable system, security, and application event logging

  + Forward logs to centralized SIEM (e.g., CloudWatch Logs, GuardDuty, Splunk)

**Monitoring and Enforcement**

* Use AWS Config, Systems Manager Compliance, or GuardDuty to detect drift from baseline.
* Periodically validate tools are active and updated across all hosts.

**Possible Evidence to Collect:**

* Baseline configuration documentation or CIS/STIG policy mapping
* Antivirus configuration screenshots or logs
* FIM tool output or configuration files
* Windows Firewall GPO settings or Linux firewall rules
* Logging configuration files and CloudWatch/SIEM ingestion evidence
* AWS Config compliance reports or Systems Manager compliance dashboard screenshots
* Internal audit reports showing compliance with baseline

---

**HITRUST Requirement – Secure Source Code Access Control**  
**Control ID:** 10.j Access Control to Program Source Code  
**Control Type:** Technical  
**Control Level:** System-Level Control  
**HIPAA Mapping:** 45 CFR §164.312(a)(1) – Access Control

**Control Objective:**  
Ensure that access to source code and related development artifacts is tightly controlled to prevent unauthorized or unintended changes and the introduction of unapproved functionality.

**Technical & Operational Implementation:**

**Access Control and Restrictions :**Enforce least privilege for access to code repositories using IAM roles or directory-based permissions (e.g., GitHub Teams, AWS IAM, Azure AD).

* Restrict write/commit/push privileges to authorized developers only; use role-based access control (RBAC) within platforms such as GitHub, GitLab, Bitbucket, or AWS CodeCommit.

**Change Management & Version Control**

* Require code commits to follow an approved change control process with peer reviews.
* Use protected branches and pull request workflows to enforce review before merge.
* Log all repository access and modifications (e.g., Git logs, GitHub/AWS CloudTrail/Audit Logs).

**Artifact Control :**Store associated artifacts (e.g., design docs, validation specs) in secured repositories or document management systems (e.g., Confluence, SharePoint) with appropriate access controls.

**Code Security and Monitoring**

* Implement automated tools for code scanning (e.g., Snyk, SonarQube, GitHub Advanced Security) to detect unauthorized code injections or risky changes.
* Continuously monitor repo access events for anomalous behavior using SIEM or audit tools.

**Possible Evidence to Collect:**

* Access control matrix for developers and reviewers
* IAM policies or GitHub team permissions configuration
* Source control system configuration showing protected branches
* Logs of code reviews and pull request approvals
* Change request records or Jira tickets
* Output of static code analysis or SAST tools
* Audit trail exports from GitHub/GitLab/Bitbucket or AWS CodeCommit
* Repository activity alerts or logging reports (e.g., from AWS CloudTrail, GitHub Audit Log)

---

**HITRUST Requirement – Configuration Management Governance**  
Control ID: 10.k Change Control Procedures  
Control Type: Policy  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(A) – Risk Analysis; 45 CFR §164.308(a)(1)(ii)(B) – Risk Management

**Control Objective:**  
Establish and maintain formal configuration management governance that defines the organizational purpose, scope, and roles necessary to support secure and compliant configuration practices.

**Technical & Operational Implementation:**

**Formal Configuration Management Policy**

* Document a configuration management policy that defines:

  + Purpose – to control and secure system configurations across environments.
  + Scope – covering all assets, platforms, and environments (e.g., cloud, on-prem, hybrid).
  + Roles & Responsibilities – for system owners, configuration managers, approvers, and reviewers.
  + Management Commitment – statement of leadership support and authority delegation.
  + Compliance Requirements – references to standards such as NIST SP 800-128, CIS Benchmarks, HITRUST CSF.

**Organizational Coordination**

* Establish cross-functional coordination processes (e.g., DevOps, security, infrastructure, compliance teams) to:

  + Approve configuration baselines.
  + Coordinate system updates.
  + Respond to configuration-related vulnerabilities or incidents.

**Review and Approval Mechanisms**

* Periodically review the configuration management policy (at least annually).
* Obtain executive or security steering committee approval of major updates.

**Supporting Tools & Automation**

* Use tools like AWS Config, AWS Systems Manager (SSM), Terraform, Ansible, Chef, or Puppet to enforce configuration consistency and governance.

**Possible Evidence to Collect:**

* Configuration management policy document with version history
* Organizational chart with assigned roles and responsibilities
* Meeting minutes or email threads showing coordination across departments
* Evidence of policy review and executive approval
* Change management or configuration tracking tools and logs
* AWS Config rules and compliance reports
* Screenshots or audit trails from SSM, Terraform, or other config-as-code tools

---

**HITRUST Requirement – Security Oversight of Outsourced Development**  
**Control ID:** 10.k Change Control Procedures  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(b)(1) – Business Associate Contracts and Other Arrangements

**Control Objective:**  
Ensure that third-party or outsourced development includes enforceable security controls for change management, flaw tracking, and vulnerability remediation accountability.

**Technical & Operational Implementation:**

**Security Requirements in Contracts**

* Ensure that all contracts for outsourced development include:

  + Clauses requiring change control procedures that specifically address security.
  + Defined security responsibilities for system/component/service developers.

**Flaw Management Expectations for Third-Party Developers**

* Require developers (internal or outsourced) to:

  + Track known vulnerabilities (e.g., using CVE or internal flaw repositories).
  + Resolve flaws in accordance with severity, impact, and organizational policy.
  + Log and report flaw status to designated roles or security personnel.

**Oversight and Enforcement**

* Designate security or compliance roles to review:

  + Flaw remediation reports.
  + Developer tracking logs.
  + SLA adherence for remediation timelines.
* Integrate flaw data into centralized vulnerability management tools if applicable.

**Possible Evidence to Collect:**

* Contract language specifying security-related change control requirements
* SLAs or terms of service covering flaw remediation expectations
* Tickets, logs, or dashboards showing vulnerability tracking and resolution
* Internal procedures requiring third-party reporting to organizational roles
* Emails or meeting records showing security issue escalations from vendors
* Security addenda or amendments to existing service agreements

---

**HITRUST Requirement – Control of Automated Updates on Critical Systems**  
Control ID: 10.k Change Control Procedures  
Control Type: Technical/Operational  
Control Level: Moderate to High  
HIPAA Mapping: 45 CFR §164.308(a)(8) – Evaluation

**Control Objective:**  
Ensure automated updates do not interfere with the stability or functionality of critical systems by restricting their use in high-impact environments.

**Technical & Operational Implementation Guidance:**

**Critical System Update Safeguards**

* Automated updates must be disabled on systems identified as critical to operations, availability, or patient safety (for healthcare entities).
* Manual review and staged testing of updates should be conducted in pre-production environments before applying to critical systems.
* Update processes for critical systems should require:

  + Risk analysis of update impact
  + Change control board (CCB) or management approval
  + Scheduled maintenance windows with rollback plans

**Categorization of Critical Systems**

* Maintain an asset inventory or CMDB identifying systems deemed “critical.”
* Classify applications or platforms where availability and stability are paramount (e.g., EMR, payment gateways, OT devices, etc.).

**System Hardening and Patch Strategy**

* Implement group policies or configuration scripts that block automatic OS or software updates on designated critical systems.
* Use tools like WSUS, SCCM, AWS Systems Manager, or custom patch baselines to enforce staged and controlled update deployment.

**Possible Evidence to Collect:**

* Asset inventory showing critical system categorization
* Screenshots or logs from patch management tools (e.g., Systems Manager Patch Baseline)
* Change control procedures describing exception for critical systems
* Test environment validation records for updates
* Configuration settings or policies disabling auto-updates
* Audit logs confirming no automated updates occurred on production systems

---

**HITRUST Requirement – Configuration Management Plan for Information Systems**  
**Control ID:** 10.k Change Control Procedures  
**Control Type:** Policy / Procedural / Technical  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(D) – Information System Activity Review

**Control Objective:**  
To ensure effective, secure, and accountable management of system configurations throughout the information system lifecycle, enabling traceability, integrity, and authorized access to configuration items.

**Implementation Guidance:**

**Configuration Management Plan Requirements:**  
The organization must **develop, document, and implement** a comprehensive configuration management (CM) plan that:

1. Addresses roles and responsibilities

   * Defines accountable personnel for configuration management
   * Includes segregation of duties in configuration change approvals
2. Defines configuration items (CIs)

   * Identifies system components to be tracked (e.g., hardware, software versions, application settings, infrastructure-as-code)
   * Establishes a baseline for each CI
3. Maps configuration control to SDLC

   * Specifies when CIs enter formal CM during system lifecycle phases (e.g., during design, testing, production)
4. Establishes item tracking and control

   * Ensures version control, CI change tracking, audit logs, and rollback processes
   * Leverages tools (e.g., Git, AWS Config, ServiceNow CMDB) for tracking changes
5. Protects the CM plan

   * Restricts modification access via role-based controls
   * Applies read-only access to most stakeholders; edit access to system owners and CM managers
   * Periodic review to prevent unauthorized disclosure or outdated documentation

**Evidence Examples:**

* Configuration management policy and plan document
* Configuration baseline and inventory (e.g., Git repo, CMDB records)
* Workflow showing when CIs are added to CM during SDLC
* IAM permissions for CM plan access
* Screenshots of AWS Config, version control systems, or change request tracking
* Change history/audit logs

---

**HITRUST Requirement – Mobile Device Change Management**  
Control ID: 10.k Change Control Procedures  
Control Type: Procedural / Technical  
Control Level: L2 (applicable where mobile devices are used for business operations)  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(D); §164.312(c)(1)

**Control Objective:**  
Ensure changes to mobile device configurations, operating systems, patches, and applications are controlled through a formal change management process to mitigate risks to system security and data integrity.

**Implementation Guidance:**

The organization must:

1. **Enforce formal change management** for mobile device environments, covering:

   * Operating system upgrades (e.g., iOS, Android)
   * Patch/application updates (e.g., security or feature updates)
   * Configuration modifications (e.g., MDM profiles, VPN policies)
2. **Utilize Mobile Device Management (MDM)** platforms to centrally apply, audit, and validate changes. E.g., Microsoft Intune, Jamf, VMware Workspace ONE
3. **Require testing and approval** for significant updates prior to deployment on production or high-risk devices
4. **Retain logs and change history** for traceability and audit purposes

   * Document device fleet, applied versions, and exception cases
5. **Enforce rollback/mitigation plans** in case of update failures or incompatibilities

**Supporting Evidence Examples:**

* Mobile change management policy and procedures
* MDM system logs showing deployed OS/patch versions
* Change tickets for mobile application updates
* Risk assessments or test results before major OS rollouts
* Incident log showing failed update and rollback procedure

---

**HITRUST Requirement – Formal Change Control Process**  
Control ID:10.k Change Control Procedures  
Control Type: Procedural  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(D); §164.312(c)(1)

**Control Objective:**  
Ensure all changes to information systems, configurations, and software are formally authorized, controlled, documented, tested, and managed to reduce the risk of system corruption and maintain security and privacy protections.

**Implementation Guidance:**  
The organization must:

1. **Formally control all changes** by:

   * (1) Controlling
   * (2) Documenting, and
   * (3) Enforcing change procedures
2. **Ensure all new systems and major changes** are:

   * (4) Documented
   * (5) Specified (clearly outlined in scope and expectations)
   * (6) Tested (including functionality, security, and compatibility)
   * (7) Quality controlled
   * (8) Implementation is managed by responsible parties
3. **Include the following in change control processes:**

   * (9) Risk assessments for proposed changes
   * (10) Analysis of security and privacy impacts
   * (11) Specification of necessary security controls to address risks or meet compliance requirements

**Evidence Examples:**

* Change request and approval logs (Jira, ServiceNow, etc.)
* Test results and sign-off forms
* Risk assessment templates or reports
* Documentation of rollback plans and security control implementations
* Audit trails and logs demonstrating enforcement of change control policies
* Security/privacy impact assessments (SPIAs or PIA/DPIA) for major changes

---

**HITRUST Requirement – Configuration Validation and Vulnerability Scanning**  
Control Reference: 10.k Change Control Procedures  
Control Type: Technical  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(A), §164.308(a)(1)(ii)(B), §164.312(b)

**Control Objective:**  
Ensure system configurations are validated and continuously assessed for vulnerabilities by comparing against known secure baselines and through routine scanning procedures.

**Implementation Guidance:**  
The organization must:

1. **Use installation checklists** to validate secure configuration for:

   * (1) Servers
   * (2) Devices
   * (3) Appliances
2. **Conduct vulnerability port scanning** on:

   * (4) Servers
   * (5) Desktops
3. **Ensure scanning results:**

   * (6) Are compared to a known effective baseline to validate that configurations meet the organization’s minimum security standards

**Evidence Examples:**

* Completed configuration checklists for new systems
* Vulnerability scan reports from tools like Nessus, OpenVAS, AWS Inspector, etc.
* Baseline configuration documentation (e.g., CIS Benchmarks, AWS Config conformance packs)
* Logs of remediation actions taken based on scan results
* System hardening procedures (e.g., STIGs, group policies)
* Records showing the baseline configurations were reviewed and approved by security

---

**HITRUST Requirement – Security Oversight of Project and Support Environments**  
Control ID: 10.k Change Control Procedures  
Control Type: Operational  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(A) – Risk Analysis; §164.308(a)(1)(ii)(B) – Risk Management  
  
 **Control Objective:**  
Ensure the integrity and security of project, development, and support environments by enforcing change control, oversight of responsibilities, and restricting unauthorized modifications.

**Technical & Operational Implementation:**

**Managerial Oversight Responsibilities**

Managers responsible for application systems must:

1. Ensure the **security of the project and support environments** by applying appropriate safeguards, controls, and monitoring measures.
2. **Review all proposed system changes** to verify they do not compromise the confidentiality, integrity, or availability of the system or operating environment.

**Control of Project and Support Environments**

3. Project and support environments are:

   * **Strictly controlled** through role-based access,
   * Segregated from production when required,
   * Subject to baseline security configurations and monitoring.

**Possible Evidence to Collect:**

* Role descriptions or responsibilities documents showing manager accountability
* Change request reviews or approval workflows documenting security review
* Access control logs for support and staging environments
* Configuration hardening guidelines applied to support/project environments
* Documentation on environment separation (e.g., Dev/Test/Prod)
* Change management policy referencing required security review steps

---

**HITRUST Requirement – Configuration Baseline Management**  
Control ID: 10.k Change Control Procedures  
Control Type: Technical  
Control Level: System-Level Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(A) – Risk Analysis; §164.308(a)(1)(ii)(B) – Risk Management  
  
 **Control Objective:**  
Establish and maintain an up-to-date baseline configuration for information systems to support secure operations, facilitate change tracking, and ensure integrity of systems across updates and upgrades.

**Technical & Operational Implementation:**

Baseline Configuration Development and Maintenance

1. A baseline configuration of each information system must be:

   * Developed, documented, and maintained under configuration control procedures;
   * Managed in accordance with organizational policies and procedures.

Periodic and Trigger-Based Reviews: The baseline configuration must be reviewed and updated: At least once every six months;

2. When critical updates occur, including:

   * Security patches;
   * Emergency changes (e.g., crash recovery, urgent hardware replacements);
   * Major system changes or upgrades.
3. As part of regular component installations or upgrades, ensuring baseline alignment with system updates.
4. Supporting baseline configuration documents must:

   * Reflect active implementation of baseline updates;
   * Be aligned with change control processes;
   * Be updated as per policy or operational necessity.

**Possible Evidence to Collect:**

* Baseline configuration documents and version history
* Configuration management policy outlining update frequency and triggers
* Change records referencing baseline modifications
* Screenshots or exports of configuration management tool outputs (e.g., AWS Config, SCCM)
* Logs or tickets showing patching or emergency change events
* Evidence of policy mandating baseline updates during upgrades

---

**HITRUST Requirement – Mandatory Security Configuration Settings**  
Control ID: 10.k Change Control Procedures  
Control Type: Technical  
Control Level: System-Level Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(B) – Risk Management

**Control Objective:**  
Ensure systems are securely configured by applying and maintaining mandatory configuration settings based on authoritative security baselines, with documented exceptions and monitored configuration changes.

**Technical & Operational Implementation:**

**Baseline Configuration Enforcement**

1. Mandatory configuration settings must be:

   * Established and documented for all information technology products;
   * Aligned with the latest security configuration baselines (e.g., CIS Benchmarks, DISA STIGs);
   * Maintained as authoritative configurations across systems.

**Exception Management**

2. The organization must:

   * Identify, document, and approve exceptions to mandatory configuration settings;
   * Justify exceptions based on explicit operational needs;
   * Track exceptions in a centralized or policy-based manner.

**Monitoring and Control of Configuration Changes**

3. All configuration changes must be:

   * Monitored continuously using automated tools (e.g., AWS Config, Azure Policy, GPO audits);
   * Controlled through change management processes that align with organizational policy;
   * Audited to detect unauthorized or unapproved modifications.

**Possible Evidence to Collect:**

* System hardening standards or secure configuration baselines
* Records of approved configuration exceptions (e.g., tickets, logs, documentation)
* Change control records referencing configuration changes
* Output from configuration monitoring tools (e.g., AWS Config rules, Nessus scans)
* Audit logs showing who made configuration changes and when
* Policies and procedures defining configuration enforcement and exception processes

---

**HITRUST Requirement – Automated Configuration Management Enforcement**  
Control ID: 10.k Change Control Procedures  
Control Type: Technical  
Control Level: System-Level Control  
HIPAA Mapping: 45 CFR §164.312(a)(1) – Access Control; §164.312(b) – Audit Controls  
  
 **Control Objective:**  
Ensure security configuration settings are centrally managed, enforced, and auditable using automated mechanisms to maintain system integrity and detect unauthorized changes.

**Technical & Operational Implementation:**

**Automated Configuration Enforcement Capabilities**

1. Centrally manage, apply, and verify security configuration settings across systems using automated tools (e.g., AWS Config, Puppet, Chef, Ansible, SCCM, Intune).
2. Detect and respond to unauthorized changes to network and system configuration parameters by:

   * Generating real-time alerts for deviations;
   * Automatically reverting unauthorized changes (self-healing mechanisms);
   * Logging incidents for further review.
3. Enforce access restrictions by applying:

   * Role-based access controls (RBAC) or attribute-based access controls (ABAC);
   * Least privilege policies;
   * Network segmentation and firewall rules via automation (e.g., AWS Firewall Manager).
4. Support enforcement actions by:

   * Logging all configuration changes and automated responses;
   * Capturing user identities, timestamps, and system states;
   * Storing audit logs in tamper-evident systems or SIEMs for review (e.g., CloudTrail, Splunk, ELK).

**Possible Evidence to Collect:**

* Configuration management tool output showing baselines and applied settings
* Automated remediation rules and workflows
* Logs of unauthorized change detections and automated responses
* Access control policies and logs showing enforcement activity
* SIEM dashboards or audit trail reports covering configuration events

---

**HITRUST Requirement – Comprehensive Change Control and Baseline Deviation Alerting**  
Control ID: 10.k Change Control Procedures  
Control Type: Operational  
Control Level: System-Level Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(A) – Risk Analysis; 45 CFR §164.308(a)(1)(ii)(B) – Risk Management

**Control Objective:**  
Ensure that changes to information systems are authorized, tested, documented, and controlled to prevent compromise of system security, with automated alerts for any deviation from approved baselines.

**Technical & Operational Implementation:**

**Change Control Governance**

1. Ensure changes do not compromise existing security requirements or controls.
2. Restrict support programmer access strictly to areas required for task execution, following the principle of least privilege.
3. Require formal change approval from authorized personnel before implementation.

**Structured Change Control Activities**

4. Accept change requests only from authorized users.
5. Maintain records of authorization levels associated with change approvals.
6. Evaluate control and integrity mechanisms to ensure changes will not degrade system security.
7. Identify and inventory all software, data, and hardware affected by proposed changes.
8. Require detailed and formally approved proposals prior to change execution.
9. Document unit, system, and user acceptance testing (UAT) procedures; perform testing in segregated environments.
10. Ensure all system components (OS, applications, utilities) undergo formal testing and approval prior to production deployment.
11. Document rollback strategies for failed changes.
12. Require user acceptance signoff following change testing, prior to deployment.
13. Update technical documentation to reflect changes; archive or dispose of outdated documentation securely.
14. Enforce version control over all software modifications and updates.
15. Maintain an auditable trail of all change requests, approvals, and execution records.
16. Test changes for compatibility across mobile devices, OSs, and applications using a documented validation plan.
17. Update operational documentation and user manuals to align with system changes.

**Baseline Integrity Monitoring**

18. Implement automated alerts for any configuration deviation from the approved system baseline; ensure alerts are triaged and reviewed by designated personnel.

**Possible Evidence to Collect:**

* Change management policy and SOPs
* Ticketing system logs (e.g., Jira, ServiceNow) for change approvals and rejections
* Version control repository records (e.g., Git, SVN)
* Test case results and UAT signoffs
* Updated configuration documentation and deprecation logs
* Audit logs showing alert generation for unauthorized baseline deviations
* Evidence of rollback plans and execution during failure scenarios

---

**HITRUST Requirement – Change Monitoring and Integrity Validation for Virtual Machine Images**  
Control ID: 10.k Change Control Procedures  
Control Type: Technical  
Control Level: System-Level Control  
HIPAA Mapping: 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that any changes to virtual machine images are logged, alerted upon, and made visible to stakeholders to maintain operational integrity and traceability.

**Technical & Operational Implementation:**

1. **Change Detection and Logging:** All changes made to virtual machine images must be logged automatically by the virtualization platform or configuration management tools.
2. **Alerting:** Automated alerts must be generated for any modification to a virtual machine image, including rebuilds, reconfigurations, or unauthorized changes.
3. **Integrity Validation and Visibility:** The outcome of any image change or movement—along with results of integrity validation—must be electronically communicated (e.g., via dashboards, customer portals, or alerting systems) to designated business owners and/or customers in a timely manner.

**Possible Evidence to Collect:**

* Audit logs from hypervisor or virtualization tools (e.g., VMware, AWS AMI)
* Configuration or compliance monitoring platform logs (e.g., AWS Config)
* Alert records from SIEM or cloud-native alerting (e.g., CloudWatch)
* Screenshot or export of customer/business owner portals showing visibility of change alerts
* Integrity check reports or hash validation outputs for images before and after changes
* Workflow or automation scripts that notify stakeholders (e.g., Lambda/SNS for AWS)

---