# Business Continuity & Disaster Recovery

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4930863374/Business%20Continuity%20%26%20Disaster%20Recovery

**Created by:** Shreya Singh on July 14, 2025  
**Last modified by:** Shreya Singh on July 15, 2025 at 12:46 AM

---

**HITRUST Requirement – Capacity Allocation and Network Impact Mitigation**  
Control ID: 09.h Capacity Management  
Control Type: Technical  
Control Level: System Control  
HIPAA Mapping: 45 CFR §164.308(a)(1)(ii)(A), §164.310(c), §164.312(b)

**Control Objective:**

The organization must ensure that sufficient storage capacity is provisioned and monitored to reduce the risk of resource exhaustion and to minimize adverse impacts on network performance (e.g., latency, bandwidth saturation). This includes proactive allocation, trend analysis, and automated scaling or archiving to maintain performance and availability.

🔧 **Technical Implementation:**

**Capacity Monitoring & Alerting:**

* Use Amazon CloudWatch to monitor storage utilization (e.g., EBS, EFS, S3) with configured alarms when usage exceeds thresholds (e.g., 80%).
* Create CloudWatch Dashboards to visualize trends in storage growth across environments.

**Proactive Allocation & Optimization:**

* Enable AWS Trusted Advisor to track underutilized/overutilized storage and provide cost/performance optimization recommendations.
* Implement AWS Budgets and Cost Explorer to identify storage hotspots early.

**Dynamic Scaling:**

* Use Amazon EFS, which auto-scales based on usage, for applications requiring flexible storage.
* For EC2 workloads, use EBS Elastic Volumes and auto-scaling policies to adjust disk sizes on demand.

**Storage Tiering & Archival:**

* Configure Amazon S3 Intelligent-Tiering or Lifecycle Policies to archive infrequently accessed data, preserving bandwidth and reducing hot storage usage.

**Backup Considerations:**

* Ensure backup frequency and retention policies align with allocated capacity to prevent bloat (via AWS Backup and vault limits).

**Tagging & Compliance Enforcement:**

* Enforce tagging on storage resources using AWS Config rules (e.g., `required-tags` on EBS/S3).
* Detect non-compliant storage configurations (e.g., unattached volumes consuming capacity).

**Logging & Governance:**

* Store logs centrally in S3 with defined retention policies to avoid overconsumption.
* Apply lifecycle expiration rules on log buckets.

📋 **Possible Evidence to Collect:**

* CloudWatch Alarm and Dashboard Configurations for Storage Thresholds
* Trusted Advisor Report on Storage Optimization
* S3 Lifecycle Policy JSON Export
* EBS Volume Auto Scaling Policy or Snapshot Management
* AWS Config Rule Snapshot (`required-tags`, `ec2-volume-inuse-check`)
* Cost Explorer Trend Reports for Storage Services
* AWS Budget Alerts for Storage Spikes
* Documentation on EFS or S3 Intelligent-Tiering Enablement
* Internal SOP for Storage Capacity Planning and Monitoring
* Evidence of Volume Adjustments or Auto Scaling Events

---

**HITRUST Requirement – Backup and Restoration Controls**  
Control ID: 09.l Back-up  
Control Type: Technical + Operational  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(7)(ii)(A), §164.308(a)(7)(ii)(B), §164.310(d)(1), §164.312(c)(1)

**Control Objective:**  
To ensure the confidentiality, integrity, and availability of information through regularly scheduled and policy-driven backups of data and software. The organization must:

* Perform regular backups at intervals aligned with business and compliance needs
* Ensure backups are created when equipment is relocated or reconfigured
* Periodically test both backup data and restoration procedures to validate recoverability
* Maintain comprehensive documentation of backup schedules, scope, and test results
* Ensure restoration capabilities meet recovery time and recovery point objectives (RTO/RPO)

**Technical Implementation:**

1. **Automated Backup Management**  
   Use AWS Backup for centralized orchestration across services like EBS, EC2, RDS, DynamoDB, and S3  
   Define backup plans with frequency (e.g., daily, weekly), retention policies, and vault destinations  
   Enable cross-region copies for geo-redundancy
2. **Event-Driven Backups for Equipment Relocation**  
   Trigger on-demand backups using AWS Lambda or Amazon EventBridge when:

* EC2/EBS volumes are stopped, detached, or moved
* EC2 instances are tagged with a relocation flag (e.g., Relocation=True)

3. **Backup Testing and Validation**  
   Use AWS Elastic Disaster Recovery (DRS) or staging environments to test restore scenarios  
   Leverage AWS Systems Manager Automation Documents to execute scripted recovery validations (e.g., EC2 restore from snapshot)
4. **Backup Policy Enforcement and Monitoring**  
   Enable AWS Backup Audit Manager to assess compliance with backup frequency and scope  
   Apply AWS Config rules (e.g., backup-plan-enabled, rds-instance-backup-enabled) to detect non-compliant resources
5. **Secure Backup Storage**  
   Store backups in AWS Backup Vaults or Amazon S3 with versioning enabled  
   Use S3 Lifecycle Policies to archive older backups to Glacier or Deep Archive  
   Protect data with KMS encryption at rest and IAM policies controlling vault access
6. **Logging and Audit Trail**  
   Enable AWS CloudTrail and Backup Audit Manager for full traceability of backup and restoration operations  
   Store logs in centralized S3 buckets with proper retention policies  
   Use Amazon Macie to identify and protect sensitive data in backup storage

**Possible Evidence to Collect:**

* AWS Backup Plan Configuration Exports
* AWS Backup Job History and Success/Failure Reports
* AWS Backup Vault Retention Policies
* Audit Manager Reports Showing Backup Policy Compliance
* Lambda/EventBridge Trigger Logs for Relocation-Based Backups
* Systems Manager Automation Logs of Restoration Tests
* AWS Config Rule Evaluation Snapshots (backup-plan-enabled, rds-instance-backup-enabled)
* S3 Versioning and Lifecycle Policy JSON
* Documentation of RTO/RPO Definitions
* Backup and Restoration Test Reports or Evidence of Periodic Drills

---

**HITRUST Requirement – System-Specific Backup Definition and Restoration Procedures**  
Control ID: 09.l Back-up  
Control Type: Technical + Operational  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(7)(ii)(A), §164.308(a)(7)(ii)(B), §164.312(c)(1)

**Control Objective:**  
To ensure that every system has a defined, risk-aligned backup and restoration strategy that meets organizational, regulatory, and contractual obligations. The organization must:

* Define and document the scope of data to be backed up for each system
* Set appropriate imaging frequency based on system criticality
* Specify retention duration based on legal, regulatory, or business requirements
* Formally document how each system can be completely restored from backup
* Ensure the entire process is consistent, testable, and auditable

**Technical Implementation:**

1. **System-Specific Backup Configuration**

Maintain a centralized Backup and Restore Register that defines:

* Backup scope (e.g., databases, configuration, logs)
* Backup frequency (e.g., hourly, daily, weekly)
* Retention requirements based on applicable compliance, legal, and business contracts  
  Use AWS resource tags like `BackupTier`, `RetentionDays`, or `ComplianceGroup` to link policies to workloads

2. **AWS Backup Plans per Classification**

Use AWS Backup to create plans tailored to backup levels (e.g., Critical, Standard, Archive):

* Assign backup rules by tag
* Set retention periods aligned with contracts and regulatory expectations
* Use vaults with access control for different data classifications

3. **Documentation of Full System Restoration**

Document complete system restore procedures in:

* AWS Systems Manager Documents (SSM Documents) for EC2/volume-level recovery
* AWS Elastic Disaster Recovery (DRS) configurations for server replication and recovery
* Step-by-step runbooks showing how to restore all components (e.g., app server + DB + DNS)

4. **Backup Immutability and Lifecycle**

Use Backup Vault Lock and Amazon S3 Object Lock to ensure immutability  
Configure S3 Lifecycle Policies to move older backups to Glacier or Deep Archive

5. **Enforcement and Monitoring**

Use AWS Config rules to ensure that:

* Required tags exist (`backup-plan-enabled`, `required-tags`)
* Backup plans are assigned
* Retention rules are enforced  
  Review AWS Backup Audit Manager reports to validate ongoing compliance

**Possible Evidence to Collect:**

* System Backup & Restore Register or CMDB Export
* AWS Backup Plan JSON Exports for Each Tier
* Backup Vault Retention and Lock Settings
* Systems Manager Document or Runbook for Restoration Procedures
* AWS Backup Audit Manager Compliance Reports
* S3 Lifecycle Policy Configuration
* AWS Config Evaluation for Backup Tagging and Policy Compliance
* Output from `aws backup list-recovery-points-by-resource`
* RPO/RTO Matrix Documentation
* Logs Showing Restoration Success from CloudTrail or Automation Runs

---

**HITRUST Requirement – Offline Backups of Data**  
Control ID: 09.l Back-up  
Control Type: Technical + Operational  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(7)(ii)(A), §164.312(c)(1)

**Control Objective:**  
To ensure data can be recovered even in the event of a cyberattack, ransomware incident, or cloud provider compromise, the organization must maintain offline (disconnected or immutable) backups. These backups should be protected from unauthorized modification and deletion, and must be available for emergency restoration scenarios.

**Technical Implementation:**

1. **Immutable and Offline Backup Options in AWS**  
   Use one or more of the following AWS-native features to implement offline or logically air-gapped backups:

* AWS Backup Vault Lock: Prevents deletion or modification of backup data by enforcing immutability for a specified retention period (WORM – Write Once, Read Many)
* Amazon S3 Object Lock: Enables WORM protection on S3 objects used for backup storage (e.g., third-party backup exports or CloudTrail logs)
* S3 Glacier Deep Archive: Acts as a cold, long-term offline-like backup store. Not actively connected to live systems and requires time to retrieve data (minimizing accidental overwrite)

2. **Cross-Account or Cross-Region Backup Copies**  
   Create automated cross-region or cross-account backups using AWS Backup policies to isolate from primary production accounts  
   Optionally restrict access with Service Control Policies (SCPs) to create an effective air gap between environments
3. **Access Control and Audibility**  
   Restrict deletion and write access using strict IAM roles and AWS Organizations SCPs  
   Enable CloudTrail and AWS Backup Audit Manager to track all access or attempted deletions of backup data
4. **Offline Exports (Optional)**  
   For ultra-critical environments, consider exporting encrypted backups to physical media or isolated accounts not connected to primary infrastructure  
   This may involve secure export workflows managed through AWS Snowball or 3rd-party BaaS vendors

**Possible Evidence to Collect:**

* AWS Backup Vault Lock Configuration Screenshot
* Amazon S3 Bucket Policy Showing Object Lock Configuration
* Evidence of S3 Glacier Deep Archive Usage
* Cross-Region Backup Copy Configuration
* IAM Role Permissions Showing Deletion Restrictions
* SCP Policies Restricting Backup Access
* AWS Backup Audit Manager Reports Showing Retention Enforcement
* CloudTrail Logs Showing Attempted or Successful Restore/Delete Events
* Offline Export Workflow Documentation (if applicable)
* Backup Policy Referencing Offline or Immutable Backup Requirements

---

**HITRUST Requirement – Automated Backup Tracking**  
Control ID: 09.l Back-up  
Control Type: Technical  
Control Level: System Control  
HIPAA Mapping: 45 CFR §164.308(a)(7)(ii)(A), §164.312(b), §164.312(c)(1)

**Control Objective:**  
To ensure the organization can consistently monitor, verify, and audit backup operations, automated tools must be used to track all backup activity across systems. This promotes recoverability, accountability, and timely detection of failed or missing backups.

**Technical Implementation:**

1. **Centralized Backup Visibility**  
   Use AWS Backup as the central service for managing and tracking backups across AWS services such as EC2, EBS, RDS, DynamoDB, and S3.

* All backup jobs, retention policies, and recovery points are visible in a unified console
* Tag-based grouping enables environment-level visibility (e.g., Production, Dev)

2. **Automated Compliance Reporting**  
   Enable AWS Backup Audit Manager to:

* Automatically track compliance against defined backup policies
* Generate daily, weekly, or monthly reports showing backup success/failure, job coverage, and exceptions
* Report on whether all tagged resources are covered by a backup plan

3. **Real-Time Monitoring and Alerts**

* Set up Amazon CloudWatch Alarms for failed backup jobs or incomplete recovery points
* Use AWS EventBridge rules to trigger notifications (SNS, Lambda) on backup state changes

4. **Integration with Security and SIEM Tools**

* Export AWS Backup and CloudTrail logs to Amazon Security Lake or third-party SIEMs (e.g., Splunk)
* Enables correlation with other infrastructure events for incident response

5. **Resource Configuration Monitoring**

Use AWS Config to detect:

* Resources that are not associated with a backup plan
* Drifts from expected backup tagging or lifecycle configurations

**Possible Evidence to Collect:**

* Screenshot of AWS Backup Dashboard with Active Job History
* AWS Backup Audit Manager Report Samples
* EventBridge Rule Definitions and Notification Setup
* CloudWatch Alarm Configuration for Backup Failures
* Config Rule Evaluation Results for `backup-plan-enabled`
* Security Lake/SIEM Integration Logs
* Backup Plan Summary Exports
* Tagging Coverage Report by Backup Tier or Environment
* Incident Log Showing Alert Triggered for Missed Backup
* Audit Policy or SOP Requiring Use of Automated Tracking Tools

---

**HITRUST Requirement – Backup Integrity, Security, and Disaster Accessibility**  
Control ID: 09.l Back-up  
Control Type: Technical + Operational  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.308(a)(7)(ii)(A), §164.308(a)(7)(ii)(B), §164.312(c)(1), §164.310(a)(1)

**Control Objective:**  
To ensure that backup copies remain both secure and recoverable in accordance with backup policy, and that the organization can access and restore data even during area-wide disasters. The control emphasizes the need to:

* Preserve the integrity and availability of backup data
* Protect backup copies from unauthorized changes or deletion
* Identify and mitigate disaster-related risks that could affect backup accessibility

**Technical Implementation:**

1. **Backup Integrity and Availability Controls**

* Use AWS Backup Vault Lock to enforce immutability of backup data (WORM model)
* Enable Amazon S3 Object Lock for object-level write-once-read-many (WORM) protection
* Encrypt all backups at rest with AWS KMS and enforce access controls with IAM and SCPs
* Apply Amazon S3 Versioning to prevent data loss due to accidental overwrites or deletions

2. **Redundant and Disaster-Resilient Backup Architecture**

* Configure cross-region backup copies using AWS Backup to store backups in a geographically distant AWS region
* Use Amazon S3 Glacier Deep Archive for long-term availability with physical separation
* Ensure replication occurs automatically via Backup Plans and is logged via CloudTrail

3. **Backup Accessibility Testing and Validation**

* Periodically test backup restoration via AWS Elastic Disaster Recovery (DRS) or isolated restore environments
* Define and document Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO) for all critical systems
* Use AWS Systems Manager Automation Documents to run scripted backup integrity checks and mock restores

4. **Monitoring and Alerting**

* Monitor backup health with AWS Backup Audit Manager
* Create CloudWatch Alarms to notify on failed backups or missing recovery points
* Use EventBridge to trigger workflows if backups fail or recovery SLA breaches occur

5. **Disaster Preparedness**

* Define regional disaster recovery zones in HealthEdge’s BC/DR plan
* Use AWS Organizations to manage isolated, secure recovery accounts that store backups with limited access
* Consider air-gapped accounts with minimal inbound access for true regional isolation

**Possible Evidence to Collect:**

* AWS Backup Vault Lock and S3 Object Lock Configuration Screenshots
* KMS Encryption Policy and Access Logs
* Cross-Region Backup Plan Configurations
* AWS Backup Audit Manager Integrity and Policy Compliance Reports
* DRS Restore Test Reports or Runbooks
* CloudTrail Logs for Backup Activity
* CloudWatch Alarm and EventBridge Rule Definitions
* S3 Glacier/Deep Archive Configuration for Long-Term Retention
* DR Plan Referencing Cross-Region Accessibility and Mitigation Steps
* RTO/RPO Documentation with Restore Timeline Evidence

---

**HITRUST Requirement – Backup Inventory Management**  
Control ID: 09.l Back-up  
Control Type: Operational  
Control Level: Organizational Control  
HIPAA Mapping: 45 CFR §164.310(d)(1), §164.308(a)(1)(ii)(D), §164.312(c)(1)

**Control Objective:**  
To support recoverability, audibility, and operational oversight, the organization must maintain an accurate inventory of all backup copies. This includes:

* Descriptions of the contents of each backup (e.g., type of data, systems covered)
* Metadata such as backup timestamp, size, and classification
* The current physical or logical location (e.g., region, vault, account) of each backup copy

**Technical Implementation:**

1. **Centralized Backup Inventory via AWS Backup**  
   Use the AWS Backup console and API to track all backup jobs, associated resources, and recovery points

* Export inventory using `list-backup-vaults`, `list-recovery-points-by-resource`, and `list-backup-jobs`
* Enable tagging for `System`, `Environment`, `BackupType`, and `DataSensitivity` to describe contents

2. **Maintain Inventory of Backup Content and Context**  
   Create an automated inventory report that includes:

* Resource ARN (e.g., EC2, RDS)
* Backup job ID
* Data classification (e.g., PHI, PCI, Internal)
* Snapshot timestamp and size
* Encryption and KMS key ID
* Source region and destination region (if cross-region)

3. **Backup Location and Retention Tracking**  
   For each backup, track where the data is stored:

* Vault Name and Vault Region
* Storage class (e.g., Standard, Glacier Deep Archive)
* Retention period and lifecycle policy
* Vault Lock or Object Lock status for immutability

4. **Tooling and Automation**

* Use AWS Systems Manager Inventory to enrich backup records with workload metadata
* Automate inventory exports using Lambda and EventBridge triggered on `BackupJobCompleted`
* Store inventories in versioned S3 buckets or a centralized CMDB tool
* Monitor with AWS Config to ensure all backup resources are tracked

**Possible Evidence to Collect:**

* Export of `list-recovery-points-by-resource` output (CSV or JSON)
* Sample backup inventory report showing content, metadata, and region
* Screenshot of tagged backup vaults with region and classification labels
* AWS Backup Plan and Vault Summary
* Sample backup job records from CloudTrail logs
* Lifecycle policy configuration and vault lock status
* S3 bucket logs or Athena queries showing inventory exports
* AWS Config rule results for untagged or unmanaged backups
* Backup register or CMDB record including content and location metadata

---

**HITRUST Requirement – Encryption of Backed-Up Confidential Information**  
Control ID: 09.l Back-up  
Control Type: Technical  
Control Level: System Control  
HIPAA Mapping: 45 CFR §164.312(a)(2)(iv), §164.312(c)(1)

**Control Objective:**  
To ensure the confidentiality of covered and sensitive information, the organization must enforce encryption of backup data—both in transit and at rest—using strong, standards-based cryptographic controls.

**Technical Implementation:**

1. **Encryption of Backup Data at Rest**  
   All AWS-managed backups (via AWS Backup) are encrypted at rest using AWS Key Management Service (KMS) keys.

* Use customer-managed KMS keys (`CMKs`) for greater control, auditing, and rotation
* Ensure backup vaults (for EC2, RDS, DynamoDB, EFS) are explicitly assigned a KMS key
* For backups stored in Amazon S3 (including Glacier), enforce bucket-level encryption with `AES-256` or `aws:kms`

2. **Encryption of Backup Data in Transit**

* Data transferred to backup services is encrypted in transit via TLS 1.2 or higher
* For manual backups or third-party exports (e.g., database dumps), enforce encryption using OpenSSL, GPG, or client-side encryption libraries

3. **Access and Key Control**

* Use strict IAM policies and KMS key policies to restrict access to decryption operations
* Enable KMS key rotation and CloudTrail logging for all `Decrypt`, `Encrypt`, and `GenerateDataKey` operations
* Apply Service Control Policies (SCPs) to restrict use of default KMS keys for highly sensitive data

4. **Compliance Monitoring and Enforcement**

* Use AWS Config rules such as `s3-bucket-server-side-encryption-enabled`, `rds-storage-encrypted`, `ebs-encrypted-volumes` to detect non-encrypted backups
* Integrate with AWS Backup Audit Manager to confirm encryption is active and compliant with policy

**Possible Evidence to Collect:**

* KMS Key Policy and Alias for Backup Vault Encryption
* AWS Backup Plan Showing KMS Key Assignment
* S3 Bucket Encryption Settings (Console or JSON export)
* RDS/EBS/DynamoDB Volume Encryption Flags
* CloudTrail Logs Showing Encryption Operations via KMS
* AWS Config Rule Evaluation Results for Backup Encryption
* AWS Backup Audit Manager Report with Encryption Compliance Status
* Sample Command-Line Backup Workflow Using Client-Side Encryption
* SCP Definition Restricting Use of Default AWS-Managed KMS Keys
* Key Rotation Policy and Audit Log Reports

---

**HITRUST Requirement – Third-Party Backup SLA Requirements**  
**Control ID:** 09.l Back-up  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(b)(1), §164.308(a)(8), §164.314(a)(1), §164.312(c)(1)

**Control Objective:**  
To ensure that when backups are handled by a third-party vendor, the confidentiality, integrity, and availability (CIA) of backup data are preserved. The service level agreement (SLA) or business associate agreement (BAA) must explicitly define:

* Encryption and access control requirements
* Retention, deletion, and availability commitments
* Roles and responsibilities for backup and restoration
* Audit rights and incident notification procedures

**Technical Implementation:**

1. **Vendor Contract and SLA Management**

* Include backup-specific clauses in the SLA/BAA that cover:

  + Encryption standards (e.g., AES-256, TLS 1.2+)
  + Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO)
  + Backup retention and deletion timelines
  + Notification requirements for access failures, data breaches, or integrity issues

2. **Vendor Assessment and Documentation**

* Conduct third-party risk assessments using internal or external vendor security questionnaires
* Ensure the vendor complies with frameworks such as SOC 2 Type II, ISO 27001, or FedRAMP
* Maintain due diligence records and re-evaluate the vendor on a recurring basis (e.g., annually)

3. **Cloud Service Provider Controls (e.g., AWS Backup)**  
   If using AWS-managed backup services:

* Review and rely on AWS’s shared responsibility model
* Ensure AWS Backup adheres to built-in controls for encryption, availability, and audit logging
* Obtain and store AWS compliance documentation via AWS Artifact

4. **Audit and Monitoring Controls**

* Ensure the vendor allows access to backup job history, audit trails, and access logs
* Periodically review those records against SLA commitments
* Include right-to-audit clauses for backup operations

5. **Backup Ownership and Exit Clauses**

* Ensure the agreement defines:

  + Who owns the backup data
  + How data will be returned or deleted on contract termination
  + Continuity of service requirements during transition

**Possible Evidence to Collect:**

* Executed SLA or BAA with Backup-Related Security Clauses
* Third-Party Security Review and Risk Assessment Results
* Vendor Compliance Certifications (e.g., SOC 2 Report, ISO 27001 Certificate)
* Screenshots or Exports from Vendor Portal Showing Backup Compliance
* AWS Artifact Download (if AWS is the provider)
* RTO/RPO Clauses from SLA
* Audit Rights and Notification Terms
* Incident Response Clauses for Backup Service Provider
* Record of Vendor Performance Review or SLA Compliance Logs
* Documentation of Termination and Data Disposal Clauses

---

**HITRUST Requirement – Full and Incremental/Differential Backup Scheduling**  
Control ID: 09.l Back-up  
Control Type: Technical  
Control Level: System Control  
HIPAA Mapping: 45 CFR §164.308(a)(7)(ii)(A), §164.312(c)(1)

**Control Objective:**  
To ensure consistent and restorable backup data, the organization must implement a structured backup schedule that includes:

* Weekly full backups to ensure complete copies of data are preserved
* Daily incremental or differential backups to capture changes and reduce restore time
* Use of separate logical or physical media to mitigate single point of failure risks

**Technical Implementation:**

1. **AWS Backup Plan Configuration**  
   Use AWS Backup to define scheduled backup rules that align with this requirement:

* **Full Backups Weekly:**

  + Use backup rule with `cron` expression targeting a full backup every 7 days
  + Target separate backup vaults or tagged vault tiers (e.g., `WeeklyFullVault`)
* **Incremental Backups Daily:**

  + AWS Backup automatically performs incremental backups after the initial full backup
  + Schedule using daily `cron` expressions
  + Store in separate vault (e.g., `DailyIncrVault`) to align with “separate media” expectation

2. **Media Separation in AWS Terms**

* Use separate backup vaults with independent access policies
* Optionally store full vs. incremental backups in different AWS accounts or regions
* Leverage Amazon S3 + S3 Glacier for long-term full backup storage and AWS Backup Vault for recent incremental copies

3. **Backup Verification and Logging**

* Enable AWS Backup Audit Manager to track backup frequency and completion
* Use CloudTrail and CloudWatch to verify backups were initiated and completed as scheduled

4. **Tagging and Lifecycle Management**

* Tag backup jobs and resources with labels like `BackupType=Full` or `BackupType=Incremental`
* Apply lifecycle policies to manage retention duration separately for full and incremental backups

5. **Restoration Strategy**

* Document restore procedures that reflect the sequence of applying full + incremental backups
* Use AWS DRS or SSM Automation for full system restoration testing

**Possible Evidence to Collect:**

* AWS Backup Plan JSON with Daily and Weekly Rules
* Backup Vault Configurations and Policy Separation
* Audit Manager Reports Showing Daily and Weekly Backup Completion
* CloudTrail Events for Backup Jobs with BackupType Tagging
* Lifecycle Policy Configuration Differentiating Backup Types
* Evidence of Separate Vaults or Storage Classes Used
* Weekly Full Backup Job Logs from CloudWatch
* Backup Register Showing Recovery Point Frequency and Media Location
* SOP or Playbook Detailing Full + Incremental Restore Sequence
* Config Rule Output Validating Scheduled Backup Compliance

---

**HITRUST Requirement – Backup Generations and Activity Logging**  
**Domain:** 12 – Data Protection and Privacy  
**Control ID:** 10.l  
**Control Type:** Technical + Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(D), §164.308(a)(7)(ii)(A), §164.310(d)(1), §164.312(c)(1)

**Control Objective:**  
To ensure effective disaster recovery and forensic traceability, the organization must:

* Maintain at least three generations of backup data (e.g., full + related incremental/differential)
* Store these generations off-site to support geographic separation and durability
* Log each backup operation (onsite and offsite) with critical metadata: name, date, time, and action

**Technical Implementation:**

1. **Multi-Generation Backup Storage**

* Use AWS Backup to create and manage retention policies that store:

  + Daily incremental backups
  + Weekly full backups
  + Retain previous generations for 3+ cycles using Vault lifecycle policies
* Store backups in AWS Backup Vaults and configure cross-region copies for off-site durability

2. **Backup Logging and Metadata Tracking**

* Use **CloudTrail** to log all AWS Backup activities with metadata such as:

  + Username or IAM role (`name`)
  + `eventTime`, `eventName`, and `resourceArn` (date, time, and action)
* Supplement with **AWS Backup Audit Manager** reports for structured tracking of job success/failure and policy compliance
* Enable **CloudWatch Logs** and **EventBridge** for real-time event streaming to SIEM

3. **Exportable Backup Inventory**

* Generate an inventory using `list-backup-jobs` or `list-recovery-points-by-resource` to show:

  + Backup type (full/incremental)
  + Date/time
  + Source resource and storage location
* Export to **Amazon S3** or integrate into a **CMDB**

4. **Long-Term Storage Strategy**

* Use **Amazon S3 Glacier Deep Archive** or **Vault Lock** for previous full backup generations
* Segment vaults by backup generation or use tagging (`Generation=Gen1/Gen2/Gen3`) for clarity

**Possible Evidence to Collect:**

* AWS Backup Plan JSON with Generation-Based Retention Periods
* Backup Vault Lifecycle Policy with Multi-Generation Support
* CloudTrail Logs Showing Backup Actions with Name, Time, Action
* Sample Backup Audit Manager Compliance Reports
* EventBridge Rule Logs for Backup Completion Events
* Inventory Export of Backup Recovery Points with Generation Tags
* Backup Activity Log Extract (CSV or JSON) Showing Metadata
* Documentation of Retention and Off-Site Storage Strategy
* Evidence of S3 Glacier or Cross-Region Vault Use
* CMDB Snapshot Showing Backup History per System

---

**HITRUST Requirement – Backup Before Server Movement**  
**Domain:** 12 – Data Protection and Privacy  
**Control ID:** 10.m  
**Control Type:** Operational + Technical  
**Control Level:** System Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A), §164.312(c)(1), §164.310(d)(1)

**Control Objective:**  
To prevent data loss during infrastructure changes, the organization must ensure a **current and restorable backup** of covered information exists before **relocating, decommissioning, or physically moving servers or instances**.

**Technical Implementation:**

1. **Pre-Movement Backup Automation**

* Use **AWS Backup** or **AWS Lambda** to trigger on-demand backups when servers (EC2 instances or on-prem systems via AWS Backup Gateway) are:

  + Tagged for decommissioning or migration (`PlannedMove=True`)
  + Scheduled to be stopped or terminated
* Use **Amazon EventBridge** to monitor instance state changes and invoke backup workflows

2. **Manual/Approval-Based Backups for High-Risk Systems**

* Require manual confirmation of a recent backup before approving infrastructure change tickets (via JIRA, ServiceNow, etc.)
* Generate **backup job logs** from AWS Backup or **SSM Automation** that confirms job success

3. **Snapshot and Recovery Point Tracking**

* Ensure a **point-in-time recovery snapshot** is captured via:

  + EBS Snapshots for EC2 volumes
  + RDS Snapshots for database instances
  + AWS Backup for file systems and block storage
* Store backups in a designated **vault** with retention policy to preserve the snapshot during the migration window

4. **Data Availability Testing**

* Confirm that recovery points are **restorable** by testing them in an isolated environment using **AWS Elastic Disaster Recovery (DRS)** or **manual restore** procedures
* Log outcomes and attach to change management record

5. **Policy and Change Control Integration**

* Embed backup verification as a mandatory step in your **change control policy** or infrastructure migration checklist
* Maintain audit logs and evidence of backup availability tied to server move events

**Possible Evidence to Collect:**

* AWS Backup Job Report or CloudTrail Event Showing Pre-Move Backup
* Lambda/EventBridge Rule Configuration for Backup on EC2 State Change
* SSM Automation Document Execution Logs for Backup Task
* EBS/RDS Snapshot ID and Metadata Confirming Timestamp
* Approval Ticket with Attached Backup Log or Screenshot
* DRS Restore Test Output from Staging Region
* Backup Vault Configuration Showing Retention Enforcement
* Change Management SOP Requiring Pre-Move Backup
* Config Rule Output Validating Snapshot Before Termination
* Evidence of Tagging and Backup Triggering (`PlannedMove=True`)

---

**HITRUST Requirement – Backup Testing and Verification**  
**Domain:** 12 – Data Protection and Privacy  
**Control ID:** 10.n  
**Control Type:** Technical + Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A), §164.312(c)(1)

**Control Objective:**  
To ensure the reliability and usability of backup data, the organization must:

* Test backup media and recovery points following backup creation to confirm data integrity
* Conduct **periodic restoration testing**, including at least **once annually** per system
* Identify and resolve issues related to backup corruption, compatibility, or format

**Technical Implementation:**

1. **Post-Backup Integrity Verification**

* Use **AWS Backup Vault Checksum Verification** and **CloudTrail logs** to confirm successful backup creation and storage
* Automate verification workflows using **AWS Lambda** or **SSM Automation** to:

  + Validate recovery point presence
  + Generate hash or checksum comparisons (if using custom backup tools)

2. **Scheduled Annual Restore Tests**

* Perform **annual restore tests** for all critical systems using:

  + **AWS Elastic Disaster Recovery (DRS)** to spin up test environments
  + **AWS Systems Manager Automation** to restore EC2 instances or file systems in a staging VPC
  + Manually restore **RDS snapshots**, **EBS volumes**, or **DynamoDB tables** for validation

3. **Logging and Documentation of Test Results**

* Document every backup test with metadata including:

  + Date/time, system tested, restore method, success/failure status, and responsible personnel
* Store logs centrally in **Amazon S3** and/or your **GRC or CMDB** tool
* Tag test artifacts with `BackupTest=True` for traceability

4. **Testing Policy Enforcement**

* Embed testing requirements into your **backup and disaster recovery policy**
* Use **AWS Config** to ensure backup policies are enforced on all tagged critical assets

5. **Metrics and Compliance Monitoring**

* Monitor restore success rates and testing frequency with:

  + **AWS Backup Audit Manager** reports
  + **Security Hub findings** if integrated with compliance tools
  + External SIEM dashboards if exporting CloudTrail logs

**Possible Evidence to Collect:**

* Restore Test Logs with Timestamp, Resource ID, and Outcome
* AWS Backup Audit Manager Reports Confirming Restore Testing
* Output from SSM Automation Executions (e.g., restore-from-snapshot workflows)
* Elastic Disaster Recovery (DRS) Job Summary Reports
* Internal Annual Restore Test Schedule or Calendar
* Backup Policy Document Requiring Post-Backup Verification
* CloudTrail Logs or EventBridge Events Showing Backup/Test Activity
* RDS Snapshot Restore Success Logs
* EBS Volume or EC2 Instance Restore Report
* Security Hub Compliance Status for Backup Integrity Controls

---

**HITRUST Requirement – Business Continuity Planning and Asset Protection**  
**Domain:** 01 – Information Protection Program  
**Control ID:** 09.a  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A), §164.308(a)(1)(ii)(A), §164.310(a)(1), §164.310(c)

**Control Objective:**  
To maintain organizational resilience and information security during disruptions, the organization must:

* Identify all assets supporting critical business processes
* Evaluate and procure appropriate business continuity insurance
* Safeguard personnel, facilities, and information assets
* Develop and document business continuity plans (BCPs) that incorporate security requirements

**Technical Implementation:**

1. **Critical Asset Identification**

* Maintain an **asset inventory** in a CMDB or asset management system (e.g., AWS Systems Manager Inventory, ServiceNow)
* Tag AWS resources supporting critical services with labels such as `CriticalAsset=True` or `BCP_Asset=True`
* Map these assets to specific **business processes** and **continuity tiers** (e.g., Tier 1, Tier 2)

2. **Business Continuity Insurance and Risk Integration**

* Include **cyber and business interruption insurance** in the overall risk strategy
* Maintain documentation of insurance coverage, renewal terms, and responsible parties
* Link policy coverage to **RTO/RPO metrics** and continuity tiers in risk management register

3. **Protection of Personnel and Information Assets**

* Enforce physical access controls via **badge systems** or **AWS Ground Station policies** (for on-prem/hybrid)
* Ensure security groups, IAM controls, and monitoring (e.g., GuardDuty, AWS Config) are aligned with protecting critical cloud-based information assets
* Implement **disaster recovery roles and assignments** to ensure personnel continuity

4. **Documented BCP with Security Requirements**

* Maintain a **Business Continuity Plan** that includes:

  + Critical systems and their recovery procedures
  + Information security controls that must persist during disruption (e.g., MFA, encryption, backup access)
  + Communication and coordination protocols for personnel
* Store the BCP securely (e.g., encrypted S3 bucket) and test it annually
* Align with broader enterprise strategies like ISO 22301 or NIST SP 800-34

**Possible Evidence to Collect:**

* Asset Inventory with BCP Classification (CSV/CMDB Export)
* AWS Tagging Schema Document for Critical Business Systems
* Copy of Business Continuity or Cyber Insurance Certificate
* DR/BCP Policy Referencing Security Requirements and Personnel Roles
* Access Control Logs (Physical or AWS IAM) for Protected Systems
* Business Continuity Plan Document with BCP Scope, Assets, and Controls
* Recovery Tier Matrix Mapping Assets to RTO/RPO
* AWS Config Compliance Snapshot for BCP Assets
* Quarterly Risk Register Review Notes
* DR Simulation/BCP Test Report with Lessons Learned

---

**HITRUST Requirement – Identification of Critical Business Processes for Business Continuity**  
**Domain:** 01 – Information Protection Program  
**Control ID:** 09.b  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A), §164.308(a)(1)(ii)(A)

**Control Objective:**  
To support the development of effective business continuity plans, the organization must identify and document **critical business processes** whose interruption would significantly impact operations, compliance, or patient care (in healthcare environments).

**Technical Implementation:**

1. **Business Impact Analysis (BIA)**

* Conduct a formal **Business Impact Analysis** (BIA) involving departmental leadership and risk management
* Document the following for each process:

  + Process name and owner
  + RTO (Recovery Time Objective) and RPO (Recovery Point Objective)
  + Regulatory, financial, or operational impact if disrupted
  + Dependency mapping (apps, services, infrastructure)

2. **Mapping to Systems and Cloud Resources**

* Map critical processes to specific AWS workloads or services using **tags** like `BusinessProcess=ClaimsProcessing`, `Criticality=Tier1`
* Maintain a relationship matrix between business functions and system-level assets in a **CMDB** or asset register

3. **Integration into Business Continuity Planning**

* Use identified processes to prioritize recovery efforts in the **BCP**
* Document mitigation strategies for each critical process (e.g., cloud failover, cross-region replication)

4. **Review and Governance**

* Review and update the list of critical business processes at least annually
* Involve **risk owners**, department heads, and IT in the classification process
* Include review results in the organization's **risk register**

**Possible Evidence to Collect:**

* Business Impact Analysis Report with Process Inventory
* BCP Document Referencing Critical Process Priorities
* System-to-Process Mapping Spreadsheet or CMDB Export
* AWS Tagging Policy and Sample Tagged Resources
* RTO/RPO Matrix by Business Process
* Governance Committee Meeting Notes or Risk Review Logs
* Organizational Chart Showing Process Ownership
* Change Log for Business Process Classification Reviews
* DR Playbooks Aligned to Critical Processes
* Evidence of Annual BIA or BCP Review Cycle

---

**HITRUST Requirement – Integrated Business Continuity and Information Security Planning**  
**Domain:** 01 – Information Protection Program  
**Control ID:** 09.c  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A), §164.308(a)(1)(ii)(A)

**Control Objective:**  
To ensure comprehensive business resilience, the organization must:

* Identify all **critical business processes**
* Integrate **information security management requirements** with broader business continuity needs such as staffing, operations, logistics, and facilities
* Coordinate planning across security, IT, HR, and facilities to reduce risk and improve recovery effectiveness

**Technical Implementation:**

1. **Identification of Critical Processes**

* Conduct and document a **Business Impact Analysis (BIA)** to identify critical business processes
* Classify each process based on impact, RTO, and RPO
* Use tags and relational mapping to link these processes to specific AWS workloads and cloud resources

2. **Integration of Security with Broader Continuity Planning**

* Ensure that the **Business Continuity Plan (BCP)** includes:

  + Security requirements (e.g., access control, encryption, backup, logging)
  + Dependencies on staffing (e.g., key personnel roles)
  + Operations continuity (e.g., alternate workflows, cloud-based failovers)
  + Material and transport dependencies (e.g., alternate logistics or vendors)
  + Facilities (e.g., remote access or alternate site preparedness)

3. **Cross-Functional Coordination**

* Collaborate with:

  + **IT and Security**: to identify and secure critical systems
  + **HR and Admin**: to define remote work policies and emergency staffing
  + **Facilities**: to define alternate locations or workspace recovery
  + **Supply Chain**: to account for key material or transportation continuity

4. **Policy and Governance Inclusion**

* Define a **BC/DR governance framework** that mandates integration of information security with business operations
* Assign **BCP owners** per department with coordination oversight from Risk/Compliance

**Possible Evidence to Collect:**

* Business Impact Analysis Report Identifying Critical Processes
* Integrated Business Continuity Plan Referencing Security, Staffing, and Operational Aspects
* System-to-Process Dependency Matrix or Mapping Document
* Organizational Chart of BCP Stakeholders Across Functions
* Meeting Minutes from Cross-Functional Continuity Planning Sessions
* RTO/RPO Matrix Incorporating Security and Operational Recovery Targets
* Policy Document Defining Roles, Responsibilities, and Integration Expectations
* DR Playbooks Referencing Both Security Controls and Non-IT Recovery Needs
* Documentation of Alternate Facilities and Remote Work Preparedness
* Audit or Risk Register Entries Covering Security-Continuity Integration Gaps

---

**HITRUST Requirement – Business Impact Analysis for Disasters, Security Failures, and Service Disruptions**  
**Domain:** 01 – Information Protection Program  
**Control ID:** 09.d  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A), §164.308(a)(1)(ii)(A), §164.312(a)(1), §164.312(c)(1)

**Control Objective:**  
To ensure effective business continuity and disaster recovery planning, the organization must conduct a **Business Impact Analysis (BIA)** that:

* Assesses the operational and security consequences of disasters (natural or manmade)
* Evaluates the risks and impact of **security control failures**
* Identifies the potential consequences of **service outages and system unavailability** on operations, patients, customers, or compliance

**Technical Implementation:**

1. **Conducting the Business Impact Analysis (BIA)**

* Use a standardized BIA methodology to identify:

  + Critical systems and processes
  + Dependencies (infrastructure, applications, personnel)
  + Potential disruptions (disasters, cyberattacks, third-party outages)
  + RTO and RPO metrics for each system/process
* Evaluate scenarios including:

  + Natural disasters (e.g., earthquake, fire, flood)
  + Logical failures (e.g., security breach, ransomware, misconfiguration)
  + Availability loss (e.g., system crash, DDoS, AWS region outage)

2. **Mapping Consequences to Business Functions and Cloud Workloads**

* Link each critical business process to corresponding **AWS resources or services**
* Use tagging (e.g., `Criticality=High`, `RecoveryTier=1`) and AWS Config to track these mappings

3. **Documenting and Prioritizing Risks**

* Capture the impact level (high/medium/low) across dimensions:

  + Operational disruption
  + Financial and legal consequences
  + Data loss and breach implications
* Incorporate these assessments into the **organization’s risk register** and business continuity plan

4. **Integration with DR and Security Planning**

* Use BIA findings to prioritize:

  + Backup schedules and retention
  + Cross-region deployment and failover design (e.g., Route 53, Global Accelerator)
  + Incident response and security control tuning

5. **Review and Update Cycle**

* Reassess BIA results annually or after major changes (e.g., new system, acquisition, regulatory change)
* Involve IT, security, compliance, and business unit leaders in each review

**Possible Evidence to Collect:**

* Business Impact Analysis Report Documenting Disruption Scenarios and Impacts
* RTO/RPO Matrix Aligned with BIA Findings
* Risk Register Entries Tied to BIA Scenarios
* Dependency Maps or CMDB Exports Linking Processes to Systems
* Meeting Notes from BIA Workshops or DR Planning Sessions
* DR Playbooks Referencing BIA-Informed Recovery Strategies
* AWS Tagging Schema Showing Criticality and Tiering
* Audit Logs or Approval Records from Annual BIA Reviews
* BCP or DR Plan with BIA Cross-Reference Sections
* Scenario-Based Risk Assessments for Cyber, Natural, and Technical Failures

---

**HITRUST Requirement – Business Continuity Risk Assessment (BCRA)**  
**Domain:** 01 – Information Protection Program  
**Control ID:** 09.e  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(A), §164.308(a)(7)(ii)(A), §164.308(a)(8)

**Control Objective:**  
To ensure that the organization’s business continuity program is based on a thorough understanding of organizational risk, the organization must:

* Assess risks across **all business processes**, not just IT systems
* Include information security risks in the broader continuity context
* Perform **annual risk assessments** involving business unit leaders
* **Quantify and prioritize** risks according to impact on business objectives
* Address risks to critical resources, allowable outage times, and recovery priorities

**Technical Implementation:**

1. **Enterprise Business Continuity Risk Assessment (BCRA)**

* Conduct a formal **BCRA** annually using standardized methodology (e.g., ISO 22301, NIST SP 800-30)
* Cover full business landscape: IT, HR, operations, vendors, facilities, etc.
* Document results in a structured format that ties to the **risk register** and **BCP**

2. **Cross-Functional Collaboration**

* Involve:

  + Business unit leaders to assess operational impact
  + Security teams to assess control failure impacts
  + Legal/compliance to assess regulatory implications
  + Facilities and IT for physical and cloud infrastructure dependencies

3. **Risk Quantification and Prioritization**

* Score risks based on:

  + **Likelihood** (e.g., DDoS, ransomware, data center outage)
  + **Impact** (on customer, compliance, finance, operations)
  + **Recovery Time Objective (RTO)** and **Recovery Point Objective (RPO)**
* Prioritize based on effect on **key business objectives** and continuity strategy

4. **Inclusion of Key Elements**

* Risk to **critical resources** (apps, staff, physical sites, cloud infra)
* **Disruption impacts**, e.g., data unavailability, legal penalties, loss of life
* **Allowable downtime** per system and process
* **Recovery prioritization**: which systems or processes must be restored first

5. **Documentation and Review Cycle**

* Store assessments in a centralized GRC tool or secure document repository
* Link risk assessment output to:

  + **BCP**
  + **Disaster recovery playbooks**
  + **Backup and incident response plans**

**Possible Evidence to Collect:**

* Most recent Business Continuity Risk Assessment Report
* Risk Register Entries with RTO/RPO and Prioritization Columns
* Stakeholder Involvement Matrix or Meeting Notes
* Risk Quantification Scoring Tables
* Prioritization Worksheet for Recovery Order
* Impact vs. Likelihood Matrix
* Annual Review Schedule and Version History
* Mapping Document Linking Risks to Business Processes
* Risk Communication Plan or Approval Memo
* Excerpt from BCP Referencing BCRA Outputs

---

**HITRUST Requirement – Integration of Information Security into Business Continuity Strategy**  
**Domain:** 01 – Information Protection Program  
**Control ID:** 09.f  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(A), §164.308(a)(7)(ii)(A)

**Control Objective:**  
To ensure that information security is effectively integrated into the organization’s business continuity strategy, the organization must:

* Identify events that could disrupt **critical business processes**, including both natural and human-made threats
* Conduct **risk assessments** to evaluate likelihood, scale, and recovery time from such disruptions
* Develop a **business continuity strategy** based on risk results that defines how continuity will be achieved
* Obtain **management approval** and implement a formal **business continuity plan (BCP)** based on this strategy

**Technical Implementation:**

1. **Threat and Interruption Scenario Identification**

* Document potential threats that could affect business continuity, such as:

  + Equipment failure, fire, flood, data corruption, ransomware, DDoS attacks
  + Cloud region failure or unauthorized access
* Use **threat modeling** workshops or templates that include cloud-specific vectors (e.g., IAM misconfigurations, service outages)

2. **Risk Assessment and Impact Evaluation**

* Conduct **risk assessments** using methodologies such as NIST SP 800-30 or ISO 22301
* Evaluate:

  + **Probability** and **impact** of events
  + **Recovery Time Objective (RTO)** and **Recovery Point Objective (RPO)**
  + Operational, legal, and financial damage

3. **Business Continuity Strategy Development**

* Define the **strategy** to maintain or resume operations, including:

  + Cloud service replication (e.g., **AWS cross-region backups**, **active-active setups**)
  + Remote access policies, security controls continuity, and recovery orchestration
* Incorporate **security requirements** like encryption, logging, access controls into the continuity plan

4. **Plan Endorsement and Execution**

* Present strategy to **senior management** for approval
* Formally document and endorse the BCP
* Include executive sign-off, version control, and distribution list
* Store the plan in a **secure, accessible location** (e.g., encrypted S3 bucket)

**Possible Evidence to Collect:**

* Threat Matrix or Disruption Scenario List
* Business Continuity Risk Assessment Report with Security Risk Integration
* RTO/RPO Table Based on Security Events and Operational Disruptions
* Business Continuity Strategy Document (pre-plan)
* Management Approval Memo or Signature Page of BCP
* Final Endorsed Business Continuity Plan with Change Log
* BCP Testing Reports Referencing Information Security Events
* Communication Plan or Training Log for Continuity Plan Awareness
* DR Architecture Diagram Showing Security Continuity Measures
* SOPs for Emergency Recovery that Include Security Safeguards

---

**HITRUST Requirement – Business Continuity Planning Structure**  
**Domain:** 01 – Information Protection Program  
**Control ID:** 09.g  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A)

**Control Objective:**  
To ensure the organization is prepared to sustain critical operations during contingency situations, the business continuity plan must address processing capacity, essential functions, recovery objectives, roles, and contact information.

**Technical Implementation:**

1. **Capacity Identification for Contingency Operations**

* Define:

  + Minimum compute/storage needs (e.g., AWS EC2 instance types, RDS capacity, load balancer specs)
  + Required network and bandwidth specs for DR
  + Environmental dependencies (power, HVAC, DNS services, etc.)

2. **Mission-Critical Functions and Dependencies**

* Maintain an inventory of essential services (e.g., patient data services, billing systems)
* Define associated contingency requirements for each critical function (e.g., RPO/RTO values)
* Use AWS Application Discovery Service or Config data to map service dependencies

3. **Recovery Objectives, Priorities, and Metrics**

* Document:

  + RTO (e.g., < 1 hour for EHR access)
  + RPO (e.g., < 15 min for patient encounter logs)
  + Metrics: % of system restoration within target, availability KPIs
* Prioritize recovery for life-critical, regulatory, and customer-facing systems

4. **Contingency Roles and Assignment**

* List individuals with assigned roles:

  + Incident Commander
  + Technical Recovery Lead
  + Communications Liaison
* Include:

  + Clear role definitions (who triggers the DR plan, who validates the environment)
  + Contact information (phone, email, alternate contact)

5. **Backup DR Plan & Training**

* Store plan in offline-accessible locations (e.g., printed binder + S3 bucket with MFA delete)
* Schedule quarterly tabletop exercises or DR drills
* Automate notifications using AWS SNS and Lambda triggers for DR activation

**Possible Evidence to Collect:**

* Business Continuity Plan (with capacity estimates, mission mappings, recovery metrics)
* Critical Workload Dependency Matrix or Application Tier Classification
* RTO/RPO Definition Worksheet
* Recovery Priority Chart with Categories and Justification
* Staff Assignment Sheet with Contact Information
* DR Test Reports and Tabletop Exercise Logs
* AWS Compute and Storage Utilization Snapshots
* Example Recovery Metric Dashboard (CloudWatch, QuickSight)
* Role-based Access List for BCP-related AWS accounts
* Training Records and Plan Distribution Acknowledgments

---

**HITRUST Requirement – Alternate Site Accessibility and Mitigation**  
**Domain:** 12 – Data Protection and Privacy  
**Control ID:** 10.l  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(B)

**Control Objective:**  
Ensure continuity of critical information systems by identifying risks to alternate processing/storage site accessibility and preparing targeted mitigation strategies.

**Technical Implementation:**

1. **Identification of Alternate Site Accessibility Risks**

* Conduct risk analysis on:

  + Cloud region unavailability (e.g., AWS region failure or latency)
  + Internet service provider or network transit outages
  + Localized power grid failure affecting data center or hybrid cloud
* Use AWS Route 53 Health Checks or Amazon CloudWatch to monitor service reachability.

2. **Mitigation Actions**

* Define explicit steps such as:

  + Auto-failover setup between AWS Regions (e.g., US-West → US-East) using Route 53 with latency or failover routing.
  + Cross-region replication for Amazon S3, RDS, DynamoDB, and EBS snapshots.
  + Use of AWS Elastic Disaster Recovery (DRS) to spin up cold/warm standby environments on-demand.
  + Alternate VPN tunnels or Direct Connect redundancy with failover.
  + Storing a secondary copy of backup data in S3 Glacier in a separate region with access logging.

3. **Documentation and Testing**

* Include site accessibility evaluation in the Business Continuity Plan or Risk Register.
* Test mitigation strategy at least annually or after major infrastructure changes.
* Validate that failover and mitigation plans meet RTO/RPO thresholds.

**Possible Evidence to Collect:**

* Risk Assessment Report identifying region-specific or provider-specific risks
* Business Continuity Plan section on alternate site and failover configuration
* AWS Route 53 Failover Configuration or Health Check logs
* Architecture diagram showing multi-region setup and replication
* AWS DRS or replication settings exports
* S3 Cross-Region Replication policy JSON
* Tabletop exercise results simulating alternate site failure and response
* CloudTrail or GuardDuty logs proving health check or failover triggering

---

**HITRUST Requirement – Main Site Resilience: Power and Communications**  
**Domain:** 12 – Data Protection and Privacy  
**Control ID:** 10.m  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(B), §164.310(b)

---

**Control Objective:**  
Ensure continuous operation of critical systems at the main site during unexpected outages by maintaining emergency power and backup communications.

---

**Technical Implementation:**

1. **Emergency Power Availability**

* Implement uninterruptible power supply (UPS) systems for critical servers, network gear, and data storage.
* Configure automatic failover to generators in on-prem data centers.
* In AWS, ensure that critical workloads run in multi-AZ environments, benefiting from AWS-managed power and redundancy.
* For hybrid environments, monitor UPS battery health and fuel supply for generators.

2. **Backup Telecommunications**

* Establish redundant internet and telecom connectivity through multiple ISPs.
* For AWS Direct Connect customers, use redundant connections or a combination of Direct Connect and Site-to-Site VPN.
* Implement auto-failover DNS routing using AWS Route 53 for primary and backup endpoints.
* Ensure backup communications cover both data and voice capabilities.

3. **Monitoring and Testing**

* Conduct annual failover testing of power and telecom systems.
* Use CloudWatch or a facilities BMS (Building Management System) to monitor power supply status and network reachability.
* Document outage response procedures in the Business Continuity or DR plan.

---

**Possible Evidence to Collect:**

* Power and telecom redundancy architecture diagrams
* UPS/generator maintenance logs and vendor service reports
* ISP or telecom contract documents with redundancy clauses
* CloudWatch dashboards showing uptime of critical services
* Route 53 failover routing policy configuration
* Business Continuity Plan outlining emergency power and telecom provisions
* Tabletop or DR test results verifying main site failover readiness
* Physical or virtual network topology diagrams showing alternate communications paths

---

**HITRUST Requirement – Business Continuity Planning Responsibilities and Thresholds**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.a  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(i), §164.308(a)(7)(ii)(A), §164.308(a)(7)(ii)(B)

**Control Objective:**  
Ensure all stakeholders clearly understand, document, and agree upon their business continuity responsibilities, and define thresholds for acceptable data and service loss.

**Technical & Operational Implementation:**

1. **Identification of Responsibilities and Procedures**

* Assign specific continuity and recovery responsibilities to key roles across departments.
* Define procedures for IT recovery, data restoration, communications, and decision-making.
* Store these procedures in a centralized, version-controlled repository (e.g., Confluence, AWS Backup Plan docs).

2. **Agreement on Responsibilities and Procedures**

* Conduct stakeholder reviews and tabletop exercises to validate BCP ownership and clarity.
* Require documented sign-off on continuity roles, communication chains, and failover procedures.
* Use tools like DocuSign or compliance platforms (e.g., Vanta, Drata) to capture approvals.

3. **Identification of Acceptable Loss (RTO/RPO)**

* Define acceptable data loss (Recovery Point Objective - RPO) and time to recover (Recovery Time Objective - RTO) by system or data classification level.
* Document business impacts if RPO/RTO targets are missed.
* Implement monitoring with AWS Backup Audit Manager or AWS DRS to track if targets are at risk.

**Possible Evidence to Collect:**

* Business Continuity Plan (BCP) with named roles and responsibilities
* Documented sign-offs or acknowledgments of responsibilities (PDFs, emails, e-signatures)
* Tabletop exercise summary reports validating procedure alignment
* List of defined RTO/RPO by system, signed by department heads
* Risk assessments that map criticality to continuity thresholds
* Audit logs of change approvals to BCP procedures or assignments
* Backup plan metadata showing configured RTO/RPO targets

---

**HITRUST Requirement – Offsite Storage of Business Continuity Plans**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.a  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(B)

**Control Objective:**  
Ensure that business continuity plans remain accessible and protected during disasters that impact the primary site.

**Technical & Operational Implementation:**

1. **Remote Storage of Business Continuity Plans**

* Store BCP documentation in a geographically separate location from the primary data center or HQ.
* Use secure, cloud-based document management platforms such as AWS S3 (with cross-region replication), Google Workspace, or Microsoft SharePoint Online.
* Ensure these systems are accessible from authorized endpoints in case of a disaster (multi-factor access, IP allow-listing if applicable).

2. **Distance-Based Risk Mitigation**

* Validate that the remote storage region is not subject to the same disaster risks (e.g., separate seismic or flood zones).
* For cloud storage: enable multi-region or cross-region backup (e.g., AWS S3 Cross-Region Replication, Glacier Vault Lock for BCP data).
* For physical media: use a third-party provider with a documented policy for offsite tape/media vaulting.

**Possible Evidence to Collect:**

* Screenshot or configuration of BCP document repository showing remote/cloud location
* Network architecture diagrams showing geographic separation between primary site and BCP storage
* Evidence of BCP access test from alternate location (e.g., test login log, screenshot)
* Configuration of AWS S3 bucket with cross-region replication enabled
* Physical storage contract or chain-of-custody logs for offsite BCP media
* Audit logs or policy documents demonstrating geographic risk mitigation

---

**HITRUST Requirement – Business Continuity Planning Process**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.b  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(B)

### **Control Objective:**

Ensure that business continuity plans are comprehensive, actionable, and capable of supporting recovery operations, restoring services, and maintaining security controls following disruptions.

### **Technical & Operational Implementation:**

1. **Recovery and Restoration Procedures**

* Define RTOs and RPOs for each critical business function.
* Document step-by-step recovery procedures for resuming operations within the established timeframes.
* Use orchestration tools (e.g., AWS Systems Manager Automation, runbooks in ServiceNow) to guide and test recovery actions.

2. **Dependency & Contract Assessments**

* Maintain an updated inventory of business dependencies (internal and third-party).
* Review contracts to ensure they contain continuity clauses, including minimum response/restoration times and fallback responsibilities.

3. **Documentation and Updates**

* Maintain and regularly update agreed-upon BCP procedures.
* Use version-controlled systems (e.g., Git, Confluence, SharePoint) to track changes.
* Ensure all staff have access to the most current documentation during drills or actual events.

4. **Periodic Testing**

* Test at least one component or scenario of the BCP annually.
* Use a combination of tabletop exercises, simulation testing, and failover drills to validate operational readiness.
* Document lessons learned and corrective actions post-test.

5. **Alignment with Business Objectives**

* Identify recovery priorities based on business impact analysis (BIA).
* Ensure communication services and customer-facing operations are prioritized in accordance with service-level expectations.

6. **Emergency Access to Confidential Information**

* Define and document secure procedures for accessing electronic PHI or confidential data during emergencies.
* Implement pre-approved emergency access controls using break-glass accounts or privileged access solutions (e.g., CyberArk, AWS IAM Emergency Access).

7. **Resource Identification & Fallback Arrangements**

* Identify all required resources: personnel, equipment, facilities.
* Establish reciprocal agreements or subscribe to commercial DR/BCP services.
* Define staffing roles and responsibilities in the BCP.

8. **Post-Interruption System Restoration**

* Ensure security measures (e.g., encryption, access control, monitoring) are re-established without degradation during restoration.
* Use configuration management tools (e.g., Terraform, AWS CloudFormation) to re-provision systems to a secure baseline.
* Validate restored systems against original CIS/SOC baselines.

### **Possible Evidence to Collect:**

* Approved and current Business Continuity Plan document
* Dependency and third-party risk register
* Screenshots of BCP procedure repository with version history
* Test reports, tabletop exercise results, or failover logs
* Emergency access policy with break-glass account procedures
* DR site architecture diagrams or reciprocal service contracts
* Restoration validation reports showing unchanged security posture (e.g., unchanged firewall rules, IAM policies)

---

**HITRUST Requirement – Distribution of Business Continuity Plans**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.c  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(B)

**Control Objective:**  
Ensure that business continuity plans are accessible to key personnel responsible for system security, continuity coordination, and recovery operations, enabling timely execution during disruptions.

**Technical & Operational Implementation:**

1. Role-Based Distribution of BCP Documents  
   Distribute business continuity plans (BCPs) to the following roles or their functional equivalents:

   * Information System Security Officer
   * System Owner
   * Contingency Plan Coordinator
   * System Administrator
   * Database Administrator
2. Secure and Controlled Access  
   Use a role-based access control system (RBAC) within a secure document management platform (e.g., SharePoint, Confluence, AWS WorkDocs).  
   Ensure only authorized personnel can view or modify the BCP content.  
   Implement logging to track access and modifications.
3. Version Control and Notifications  
   Maintain version history of distributed BCPs.  
   Notify responsible personnel upon updates, testing cycles, or changes in recovery procedures.
4. Verification and Acknowledgement  
   Require periodic verification that each stakeholder has reviewed and acknowledged the current version of the BCP.  
   Maintain signed acknowledgement logs (electronic or physical) as evidence.

**Possible Evidence to Collect:**

* List of roles receiving BCPs (policy or distribution matrix)
* Access control settings from the document management system
* Acknowledgement logs or emails confirming BCP receipt
* Screenshot of BCP location showing permissions per role
* Change history or version control audit logs for the BCP file

---

**HITRUST Requirement – Alternate Telecommunications Capability and Priority-of-Service Agreements**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.e  
**Control Type:** Technical & Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(C)

**Control Objective:**  
Ensure that essential business functions and mission-critical systems can resume operations within a defined time period in the event of a telecommunications disruption at the primary or alternate site.

**Technical & Operational Implementation:**

1. Alternate Telecommunications Availability

   * Establish alternate telecommunications services that support recovery of critical systems at both the primary and alternate processing/storage sites.
   * Implement diverse routing options using separate carriers, links, or physical paths where feasible.
2. Service Agreements with Priority-of-Service Clauses

   * Develop primary and alternate telecommunications contracts that include clearly defined availability expectations and recovery time objectives (RTOs).
   * Include priority-of-service provisions to ensure restoration precedence during regional outages.
3. Telecommunications Service Priority (TSP) Request

   * Request TSP codes for all lines supporting national security or emergency preparedness functions.
   * Register with the appropriate government telecom service (e.g., DHS Office of Emergency Communications in the U.S.).
4. Testing and Failover Readiness

   * Periodically test failover from primary to alternate telecommunications services.
   * Validate connectivity at both primary and alternate sites and document testing outcomes.

**Possible Evidence to Collect:**

* Copies of telecom service agreements with priority clauses and RTOs
* Confirmation letter or registration screenshot showing active TSP enrollment
* Network diagrams highlighting primary and alternate telecommunication paths
* Results from telecom failover or continuity testing exercises
* Business continuity policy referencing alternate telecommunications arrangements

---

**HITRUST Requirement – Recovery and Reconstitution of Information Systems**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.i  
**Control Type:** Technical & Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(B)

**Control Objective:**  
Ensure that information systems can be restored to a known, secure, and trusted state following a failure or contingency, including verification of patching, configurations, and system functionality.

**Technical & Operational Implementation:**

1. Reset System Parameters

   * Define procedures to restore all system parameters to either default or organization-approved baseline configurations.
   * Store validated parameter baselines in version-controlled configuration management repositories (e.g., AWS Systems Manager Parameter Store or Git).
2. Reinstall Patches

   * Maintain patch baselines for operating systems and applications.
   * Integrate automated patch installation into recovery workflows (e.g., via Ansible, WSUS, or AWS Systems Manager Patch Manager).
3. Reestablish Configuration Settings

   * Document and restore validated system configuration settings, including firewall rules, logging paths, and access policies.
   * Leverage infrastructure-as-code tools (e.g., Terraform, CloudFormation) to redeploy hardened configurations.
4. Reinstall Application and System Software

   * Maintain a gold image or containerized version of essential software packages.
   * Use secure deployment pipelines to reinstall and verify application integrity.
5. Functional Testing

   * Conduct full post-recovery validation testing to ensure system integrity, patch levels, and configuration compliance.
   * Document all recovery activities and test results in accordance with incident response or DR runbooks.

**Possible Evidence to Collect:**

* Recovery runbooks or documented SOPs showing reconstitution steps
* Backup image definitions or container registry snapshots
* Patch and configuration logs confirming restoration actions
* System testing logs or results following recovery simulations
* Evidence of system parameters baseline and restore scripts

---

**HITRUST Requirement – Alternate Processing Site Readiness**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.j  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(C)

**Control Objective:**  
Ensure that alternate processing locations are identified, provisioned, and protected to support the timely resumption of critical business operations in the event the primary site becomes unavailable.

**Technical & Operational Implementation:**

1. Identification of Alternate Processing Sites

   * Define and document alternate temporary locations for critical processing in the organization's disaster recovery and business continuity plans.
   * Sites may include co-location facilities, cloud failover regions, or third-party DR providers.
2. Third-Party Service Agreements

   * Establish contractual agreements that enable transfer and rapid resumption of operations within Recovery Time Objectives (RTOs).
   * Include priority-of-service clauses, such as fast-track provisioning or resource reservation.
3. Geographical Risk Separation

   * Ensure alternate locations are situated at a safe distance from the primary site to avoid shared risks (e.g., different flood, seismic, or wildfire zones).
   * For cloud: choose regions in different availability zones or continents.
4. Prioritized Availability Commitments

   * Alternate processing site agreements must define service recovery expectations based on criticality of operations.
   * Include detailed SLAs for uptime, incident response, and recovery point objectives (RPOs/RTOs).
5. Equivalent Security Safeguards

   * Apply security controls (e.g., access control, encryption, logging, and monitoring) at the alternate site consistent with the primary production environment.
   * Document the equivalency through security assessments or SOC 2/ISO 27001 reports from third-party providers.

**Possible Evidence to Collect:**

* Alternate site planning documents and location maps
* Signed third-party service agreements with priority-of-service clauses
* Risk assessment indicating sufficient geographic separation
* Security assessment reports or certifications for alternate processing sites
* Configuration and security policy documentation showing equivalence to primary site

---

**HITRUST Requirement – Integration of Contingency Plans**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.k  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A)

**Control Objective:**  
Ensure that contingency plans are developed in alignment with, and support, the requirements and dependencies of related plans (e.g., incident response, disaster recovery, and crisis communication plans).

**Technical & Operational Implementation:**

1. Plan Alignment and Coordination

   * Review related organizational plans (incident response, crisis management, emergency response) to identify overlapping responsibilities and shared resources.
   * Ensure contingency plan requirements (e.g., communication paths, response triggers) are synchronized with other plans to avoid conflict or duplication.
2. Cross-Functional Collaboration

   * Engage stakeholders from IT, legal, compliance, facilities, and business units to confirm integration of contingency planning activities.
   * Use tabletop exercises or plan walkthroughs to validate alignment and identify gaps.
3. Documentation and Version Control

   * Maintain version-controlled documentation demonstrating integration points (e.g., references to incident response procedures in the contingency plan).
   * Include references or links to related plans in contingency plan documentation.
4. Governance and Oversight

   * Establish a change management process to ensure updates to one plan are evaluated for their impact on others.
   * Assign responsibility to a governance body (e.g., BCDR Steering Committee) to oversee plan integration.

**Possible Evidence to Collect:**

* Documented contingency plan referencing related plans (incident response, DR, emergency ops)
* Meeting minutes or approvals showing coordinated plan development
* Change logs indicating cross-plan updates
* Results from integrated tabletop or functional exercises
* Organizational policy requiring plan integration across functional areas

---

**HITRUST Requirement – Business Continuity Plan Creation, Ownership, and Execution**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.b  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A)

**Control Objective:**  
Ensure the organization has at least one documented business continuity plan (BCP) with defined ownership, scope, escalation protocols, and clearly assigned responsibilities for execution.

**Technical & Operational Implementation:**

1. Minimum Plan Development

   * Develop and maintain at least one comprehensive business continuity plan applicable to the organization’s critical business functions and IT assets.
2. Plan Ownership

   * Assign a designated owner for each BCP. The owner is responsible for updates, approvals, testing coordination, and ensuring the plan aligns with business and regulatory requirements.
3. Continuity Strategy Documentation

   * Clearly describe the plan’s approach to continuity, including procedures to ensure the availability and security of information and information assets during disruptive events.
   * Include references to infrastructure redundancies, backup procedures, recovery strategies, and RTO/RPO objectives.
4. Escalation Plan Inclusion

   * Define a formal escalation plan outlining notification flows, chain of command, and criteria for escalating incidents to higher authority or external stakeholders.
5. Escalation Triggers

   * Document conditions that activate the escalation plan (e.g., failure of recovery operations, cross-site impacts, regulatory reporting triggers).
6. Role Assignment

   * Specify the individuals or roles responsible for each major component of the BCP (e.g., communications, technical recovery, vendor coordination, logistics).
   * Include contact information and succession planning to address availability risks.

**Possible Evidence to Collect:**

* BCP document including named owner, escalation procedures, and recovery strategy
* RACI matrix or responsibility table showing roles linked to BCP components
* Incident escalation flowchart or diagram
* Policy requiring BCP ownership and role accountability
* Screenshots of BCP ownership in document management platform
* Logs of annual BCP review and update by assigned owner

---

**HITRUST Requirement – Business Unit-Level Continuity Planning**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.c  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A)

**Control Objective:**  
Ensure each business unit within the organization maintains an individualized business continuity plan that aligns with enterprise resilience requirements.

**Technical & Operational Implementation:**

1. Unit-Specific BCP Mandate

   * Require every distinct business unit (e.g., IT, HR, Finance, Operations, Clinical) to develop and maintain at least one formal business continuity plan.
2. Scope Definition

   * Each unit’s plan must cover its critical functions, data dependencies, communication needs, and unit-specific recovery requirements.
3. Consistency and Governance

   * Provide a standardized BCP template and guidance to ensure consistency across all units.
   * Governance team or risk function should review and approve unit plans for completeness and alignment with enterprise recovery objectives.
4. Periodic Review and Integration

   * Mandate regular reviews and updates of unit-level plans.
   * Integrate individual unit plans into a centralized organizational continuity framework to enable cross-functional coordination during incidents.

**Possible Evidence to Collect:**

* Inventory of all business units with corresponding BCP document links
* Samples of unit-specific BCPs with owner name and last review date
* Internal policy requiring each business unit to maintain a BCP
* Communication or training materials distributed to business units on continuity planning
* Central repository or dashboard showing BCP status by unit (e.g., SharePoint, Confluence, ServiceNow)

---

**HITRUST Requirement – Business Continuity Considerations in Change Management**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.d  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(8)

**Control Objective:**  
Ensure that business continuity implications are considered during system changes to maintain resilience and reduce risk of disruption.

**Technical & Operational Implementation:**

1. Change Impact Assessment

   * Integrate business continuity (BC) impact analysis as a required field in the Change Request (CR) or Change Advisory Board (CAB) process.
   * Require system owners and risk analysts to evaluate potential effects of system changes on continuity and recovery capabilities.
2. Pre-Implementation Controls

   * Prior to implementation, assess whether the proposed change impacts RTO/RPO, BCP documentation, backup procedures, or alternate site dependencies.
   * If impacts exist, require update or testing of affected BCP components.
3. Documentation and Approval

   * Require that change documentation includes signoff from business continuity stakeholders (e.g., continuity manager, DR lead) for high-impact changes.
   * Use change management tools (e.g., ServiceNow, Jira, Remedy) with built-in BC review checkpoints.
4. Emergency Change Process

   * Define a streamlined but documented BC validation process for emergency or fast-tracked changes.

**Possible Evidence to Collect:**

* Change management policy including BC impact assessment requirements
* Completed change requests showing business continuity impact analysis
* Meeting minutes from CAB showing BC considerations
* Audit logs from change management systems (e.g., ServiceNow workflows)
* Training material or process documentation highlighting BC review during change lifecycle

---

**HITRUST Requirement – Emergency Procedures Amendment Based on New Requirements**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.i  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A)

**Control Objective:**  
Ensure that emergency and contingency procedures remain current and effective by incorporating newly identified requirements or changes in risk.

**Technical & Operational Implementation:**

1. Emergency Procedure Review Triggered by Change

   * Define triggers in policy for reviewing emergency procedures (e.g., policy updates, audit findings, new business operations, regulatory changes).
   * Implement a workflow within the Business Continuity Management System (BCMS) or risk management process that flags and routes required updates.
2. Procedure Amendment and Documentation

   * Amend evacuation plans, communication trees, fallback site arrangements, or restoration timelines as applicable.
   * Maintain change history logs in continuity documentation platforms (e.g., SharePoint, Confluence, GRC systems).
3. Stakeholder Notification and Re-distribution

   * Notify impacted personnel and departments when emergency plans are updated.
   * Confirm acknowledgment or conduct refresher training where significant changes are made.

**Possible Evidence to Collect:**

* Updated emergency procedures highlighting recent amendments
* Change log or version history showing updates
* Email or system notifications confirming stakeholder distribution
* Policy requiring periodic review or update based on change
* Meeting minutes or risk assessments that triggered plan amendment

---

**HITRUST Requirement – Assignment of Responsibilities for Emergency and Fallback Procedures**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.j  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A)

**Control Objective:**  
Ensure that ownership of emergency, fallback, and resumption procedures is clearly defined between internal stakeholders and external service providers to support timely and effective recovery.

**Technical & Operational Implementation:**

1. Internal Ownership Definition

   * Assign responsibility for emergency procedures, manual fallback processes, and resumption plans to the respective business resource or process owners.
   * Document ownership in continuity plans, RACI matrices, or process maps.
2. Role-Based Resumption Accountability

   * Include clear escalation and accountability procedures within business continuity playbooks and training materials.
   * Ensure owners are trained and equipped to activate and manage these procedures when necessary.
3. Third-Party Fallback Responsibility

   * Define fallback service responsibilities (e.g., for hosted environments, network continuity) within third-party contracts and SLAs.
   * Validate that vendors acknowledge and test these obligations periodically (e.g., annual DR drills).

**Possible Evidence to Collect:**

* Business continuity plan sections assigning ownership of emergency/fallback/resumption procedures
* RACI charts or documentation assigning responsibilities to internal owners
* Third-party agreements (e.g., MSP or cloud contracts) specifying fallback roles
* Evidence of tabletop exercises or tests validating ownership and vendor responsibilities
* Acknowledgment or training records for responsible individuals

---

**HITRUST Requirement – Comprehensive Business Continuity Planning Framework**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.k  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A), (C), (D)

**Control Objective:**  
Ensure the organization maintains a comprehensive business continuity planning framework that defines activation, emergency response, fallback, and recovery operations, supported by ongoing maintenance, training, and asset identification.

**Technical & Operational Implementation:**

1. Plan Activation Conditions

   * Document the conditions and decision criteria for triggering continuity plans, including roles, responsibilities, and situational assessments.
2. Emergency Procedures

   * Define and document immediate response steps for incidents that disrupt critical business operations (e.g., cyberattacks, natural disasters).
3. Fallback Procedures

   * Detail steps to relocate or restore essential business functions to alternate processing sites or remote work environments.
   * Specify timeframes aligned with Recovery Time Objectives (RTOs).
4. Resumption Procedures

   * Outline the step-by-step return to normal business operations, including system revalidation and data reconciliation.
5. Maintenance & Testing

   * Maintain a documented schedule for testing and updating business continuity plans at least annually or after significant changes.
   * Include corrective actions and lessons learned from exercises.
6. Awareness and Training

   * Deliver recurring training and awareness programs to all stakeholders on BCP activation, emergency roles, and escalation paths.
   * Track attendance and comprehension outcomes.
7. Critical Assets and Resources

   * Maintain an updated inventory of critical IT and non-IT assets (e.g., backup power, DR sites, essential personnel) required for emergency, fallback, and resumption efforts.

**Possible Evidence to Collect:**

* BCP documentation including activation criteria, emergency/fallback/resumption plans
* Records of annual plan testing and updates
* Training logs and awareness material for BCP roles
* Asset inventory list and dependency maps for critical business functions
* Test results or tabletop exercise summaries
* Change control records reflecting BCP updates after major system or business changes

---

**HITRUST Requirement – Security and Role-Based Coverage in Business Continuity Plans**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.l  
**Control Type:** Operational  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(C)

**Control Objective:**  
Ensure the business continuity framework accounts for critical security requirements, temporary operations during system recovery, and clearly assigned roles and responsibilities for plan execution.

**Technical & Operational Implementation:**

1. Security Requirements Alignment

   * Integrate applicable information security controls (e.g., access control, encryption, logging) into all phases of business continuity planning.
   * Ensure confidentiality, integrity, and availability are preserved during emergency or alternate operations.
2. Temporary Operating Procedures

   * Establish documented interim procedures for continuing essential operations pending full recovery or restoration.
   * Include controls for data protection, manual processing, and temporary access authorizations.
3. Roles and Responsibilities

   * Define who is responsible for each component of the continuity plan.
   * Designate alternates to ensure redundancy and continuity of operations during unavailability of primary personnel.
   * Maintain an organizational BCP responsibility matrix (e.g., RACI chart).

**Possible Evidence to Collect:**

* BCP documentation showing mapped security requirements
* Interim operational procedure documents or runbooks
* Role and responsibility listings for BCP execution, including alternates
* Organizational charts with contingency roles
* Tabletop exercise reports demonstrating delegation of responsibility
* Change management logs updating responsibilities as roles change

---

**HITRUST Requirement – Annual Review Responsibility for Business Continuity Plans**  
**Domain:** 19 – Business Continuity and Disaster Recovery  
**Control ID:** 19.m  
**Control Type:** Procedural  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A)

**Control Objective:**  
Ensure business continuity plans remain current, relevant, and effective by assigning responsibility for regular, periodic reviews.

**Technical & Operational Implementation:**

1. Assignment of Review Responsibility

   * Designate a specific individual or role (e.g., BCP Coordinator, Risk Manager, or department lead) to be accountable for periodic reviews of business continuity plans.
   * Include this responsibility in formal job descriptions or role-based access control assignments.
2. Minimum Annual Review Cadence

   * Ensure that at least a portion of the BCP is reviewed annually to validate assumptions, personnel, contact details, recovery strategies, and technological dependencies.
   * Schedule the review as part of the organization’s annual governance calendar.
3. Review Documentation

   * Maintain version control and change logs of the BCP.
   * Use checklists to verify whether all critical sections have been reviewed (e.g., recovery RTO/RPOs, alternate site readiness, escalation paths).

**Possible Evidence to Collect:**

* BCP review schedule showing annual frequency
* Assignment documentation or policies naming responsible personnel
* Job description excerpts referencing BCP oversight
* BCP revision history logs or versioning metadata
* Meeting notes or attestations from BCP review sessions
* Audit logs of BCP edits in document management systems

---