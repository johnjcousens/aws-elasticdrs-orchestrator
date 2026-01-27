# Audit Logging and Monitoring

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4972085345/Audit%20Logging%20and%20Monitoring

**Created by:** Shreya Singh on July 30, 2025  
**Last modified by:** Shreya Singh on August 05, 2025 at 03:55 AM

---

**HITRUST Requirement – Employee Monitoring Notification and Consent**  
**Control ID:** 06.e Prevention of Misuse of Information Assets  
**Control Type:** Administrative  
**Control Level:** Policy and Procedural  
**HIPAA Mapping:** 45 CFR §164.308(a)(5)(ii)(A) – Awareness and Training

**Control Objective:**  
Ensure that employees are informed about and acknowledge the monitoring of their activities within organizational systems, including AWS-hosted environments.

**Technical & Operational Implementation:**

**Monitoring Notification to Employees:**

* Include clear login banner messages (via EC2 user-data scripts or OS-level configurations) stating that all activity may be monitored and logged for security and compliance purposes.
* Provide notification via the organization's Acceptable Use Policy (AUP) or Information Security Policy, distributed through onboarding and annual training.
* Document acceptance via e-signature (e.g., in HRIS or GRC system).

**Consent Collection:**

* Obtain employee consent to monitoring via:

  + Signed policy acknowledgments (stored in HR systems)
  + Consent checkboxes embedded in login portals (e.g., AWS SSO login page customizations if SAML/Okta is used)
* Maintain audit records of acknowledgment through internal ticketing systems (e.g., JIRA) or compliance platforms.

**Cloud-Based Activity Monitoring:**

* Use AWS CloudTrail, AWS Config, and AWS CloudWatch Logs to monitor user activity across services.
* Store logs in an encrypted S3 bucket with object lock and lifecycle policies for retention and immutability.
* Integrate logs with SIEM platforms (e.g., CrowdStrike) for behavior analytics and audit reviews.

**Possible Evidence to Collect:**

* Screenshot or text of login banner displayed during AWS EC2/SAML login
* Signed employee policy acknowledgments (exported PDF or HRIS screenshot)
* Audit logs showing user activity monitoring (CloudTrail event examples)
* SIEM report samples showing alerting on suspicious employee actions
* Policy documents referencing employee monitoring and consent
* Record of policy delivery and acknowledgment (via HR system or LMS)

---

**HITRUST Requirement – Audit Logging of Critical Events**  
**Control ID:** 06.i Information Systems Audit Controls  
**Control Type:** Technical  
**Control Level:** Configurable  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that critical security-relevant events across AWS-hosted systems are continuously audited, logged, and retained to support accountability, forensic investigations, and compliance with regulatory requirements.

**Technical & Operational Implementation:**

**AWS Services and Configuration:**

* Enable AWS CloudTrail across all AWS accounts and regions to capture all management events (e.g., user logins, API calls).
* Enable AWS Config to track configuration changes and maintain historical resource states.
* Configure Amazon CloudWatch to collect application logs, custom error messages, and metrics from EC2, Lambda, and other services.
* Capture specific auditable events such as:

  1. User log-on and log-off (tracked via CloudTrail login events)
  2. Configuration changes (monitored via AWS Config rules)
  3. Application alerts and errors (collected via CloudWatch Logs/Alarms)
  4. System administration activities (captured by enabling CloudTrail Data Events or SSM Session Manager logs)
  5. Modification of privileges/access (detected using AWS IAM Access Analyzer or AWS CloudTrail)
  6. Account creation/modification/deletion (IAM user and role activity via CloudTrail)
  7. Concurrent logins (analyzed via SIEM correlation of CloudTrail login events)
  8. Override or disablement of access controls (logged via IAM policy changes in CloudTrail)

**Storage & Retention:**

* Logs stored in Amazon S3 with bucket encryption, access logging, and S3 Object Lock for immutability.
* S3 Lifecycle Policies used to enforce log retention for 6+ years or per organizational policy.

**Security & Monitoring:**

* Amazon GuardDuty enabled to detect anomalous access behaviors and configuration tampering.
* Logs integrated into SIEM platforms (e.g., Splunk, CrowdStrike Falcon LogScale, Elastic) for advanced analytics and continuous compliance monitoring.

**Possible Evidence to Collect:**

* CloudTrail configuration screenshots or export of enabled trails
* IAM policy or Config rule ensuring logging for privileged activity
* S3 bucket configuration showing log destination, encryption, and object lock settings
* Example CloudTrail event for login or role modification
* SIEM alert reports triggered from audit log data
* Retention policy documentation or lifecycle policy configuration for logs

---

**HITRUST Requirement – Protection of Audit Tool Access**  
**Control ID:** 06.j Protection of Information Systems Audit Tools  
**Control Type:** Technical  
**Control Level:** Configurable  
**HIPAA Mapping:** 45 CFR §164.312(c)(1) – Integrity

**Control Objective:**  
Ensure that access to audit tools used to monitor, log, or analyze AWS infrastructure and systems is restricted and protected to prevent unauthorized use, tampering, or compromise.

**Technical & Operational Implementation:**

**Access Control & Identity Management:**

* Restrict access to AWS audit tools (e.g., AWS CloudTrail, CloudWatch, Config, GuardDuty, Security Hub) using AWS IAM least privilege policies.
* Create dedicated IAM roles or groups for audit and compliance teams with read-only access to audit tools.
* Use AWS Organizations SCPs to deny high-risk actions (e.g., stopping CloudTrail, deleting logs) outside of approved roles/accounts.
* Enable MFA on accounts with elevated audit permissions to prevent credential misuse.

**Logging Integrity and Protection:**

* Store audit logs (e.g., from CloudTrail or GuardDuty) in **S3 buckets with server-side encryption (SSE-KMS)** and **Object Lock** enabled.
* Restrict delete/overwrite access with **bucket policies** and **IAM conditions** (`s3:DeleteObject`, `s3:PutObject`).
* Monitor access to audit logs using **AWS CloudTrail data events** and **Amazon CloudWatch metrics**.

**Audit Tool Hardening:**

* Prevent modification of audit configurations (e.g., turning off CloudTrail or GuardDuty) using **Config Rules**, **Security Hub Controls**, or **CloudFormation StackSets with drift detection**.
* Regularly review IAM permissions and perform **access reviews** using **AWS IAM Access Analyzer**.

**Possible Evidence to Collect:**

* IAM policy JSON restricting access to CloudTrail, Config, or GuardDuty
* Screenshot of CloudTrail logs stored in an S3 bucket with encryption and Object Lock enabled
* SCP or Config rule documentation preventing audit log deletion
* GuardDuty or CloudTrail logs showing access attempts to audit services
* Report from IAM Access Analyzer showing users with access to audit tools

---

**HITRUST Requirement – Audit Record Content and Integrity**  
**Control ID:** 09.aa Audit Logging  
**Control Type:** Technical  
**Control Level:** Configurable  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that audit records contain sufficient detail—such as user identifiers, action performed, and timestamp—to support accountability, traceability, and compliance verification in AWS environments.

**Technical & Operational Implementation:**

**Log Content Standards:**

* Use **AWS CloudTrail** to log AWS API activity across accounts, capturing:

  + `userIdentity.arn` → Unique user ID
  + `eventName` → Function performed
  + `eventTime` → Date/time of the action
  + `requestParameters` / `resources` → Data subject/resource identifiers (if applicable)
* AWS CloudWatch Logs and AWS Config also capture similar details for configuration changes and custom application logging.
* Where PHI or PII is involved, ensure tagging and correlation of actions to specific data subjects using resource tagging or DynamoDB/GW logs that capture request context.

Log Enrichment and Normalization:

* Forward CloudTrail and other AWS logs to a centralized logging account and ingest them into a SIEM platform (e.g., Splunk, CrowdStrike, Datadog) for normalization and analysis.
* Enrich logs with user-friendly context (e.g., username, role, IP address) through custom Lambda functions or log processing pipelines.

**Possible Evidence to Collect:**

* CloudTrail log sample showing `userIdentity.arn`, `eventName`, and `eventTime`
* CloudWatch Logs or Config snapshots capturing resource-level modifications
* SIEM or log aggregation platform reports showing normalized entries with all 4 required fields
* Screenshot of tagged PHI resources and associated activity logs
* Policies or procedures defining required audit log content and review process

---

**HITRUST Requirement – Audit Log Retention Policy**  
**Control ID:** 09.aa Audit Logging  
**Control Type:** Administrative & Technical  
**Control Level:** Configurable  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that audit log retention aligns with organizational policies and compliance requirements by enforcing consistent storage, availability, and deletion timelines across AWS environments.

**Technical & Operational Implementation:**

**Retention Policy Specification:**

* The organization defines log retention periods in its internal Security Logging Policy or Data Retention Policy.
* These requirements are mapped to compliance mandates (e.g., 6 years for HIPAA).

**AWS-Based Retention Enforcement:**

* CloudTrail Logs:

  + Delivered to an Amazon S3 bucket with Object Lock enabled (to support immutability).
  + S3 Lifecycle Policies enforce retention schedules (e.g., transition to Glacier, delete after X years).
* CloudWatch Logs:

  + Configure log group retention settings (1 day to infinite) via the AWS Console, CLI, or IaC (e.g., Terraform).
* AWS Config Logs:

  + Store compliance configuration snapshots and deliver to S3 with similar retention policies applied.
* Use AWS Backup for consistent backup and restoration policies for services such as RDS and EC2 that generate audit-relevant metadata.

**Automation & Monitoring:**

* Set up AWS Config rules or Security Hub controls to detect misconfigured log retention.
* Automate enforcement using AWS Lambda or Systems Manager Automation runbooks.

**Possible Evidence to Collect:**

* Screenshot of S3 bucket lifecycle policy
* CloudTrail configuration showing log delivery to S3
* CloudWatch log group retention setting
* Policy document specifying audit log retention period
* Compliance platform (e.g., Vanta) export showing audit log coverage and enforcement
* AWS Config rule status or Security Hub finding verifying retention settings

---

**HITRUST Requirement – Metadata Logging for Message Transmission**  
**Control ID:** 09.aa Audit Logging  
**Control Type:** Technical  
**Control Level:** Configurable  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that logs of messages sent and received over AWS-hosted systems are maintained to capture metadata (e.g., time, date, origin, destination), while excluding message content, to support auditing, compliance, and forensic readiness.

**Technical & Operational Implementation:**

**Metadata Logging (excluding content):**

* **AWS CloudTrail** captures API calls related to message services (e.g., `SendMessage`, `ReceiveMessage` for SQS; `Publish`, `Subscribe` for SNS), recording:

  + Timestamp, source IP, caller identity, and resource ARN.
  + These logs do not include payload content.
* **Amazon SES (Simple Email Service)**:

  + Use event publishing to Amazon CloudWatch or Amazon S3 to log delivery events.
  + Logs include sender/recipient addresses, timestamps, delivery status, but not message content.
* **Amazon WorkMail or Amazon Pinpoint**:

  + Monitor logs for SMTP transaction metadata via CloudWatch or EventBridge rules.
  + Use Amazon CloudWatch Logs Insights for queries filtering by sender, recipient, and timestamp.
* **AWS Config** and **AWS Lambda**:

  + Can be used to enrich logs with origin/destination tags or validate that message content is excluded.

**Log Storage & Protection:**

* All logs are stored in Amazon S3 with encryption at rest (SSE-S3 or SSE-KMS).
* Use Object Lock and S3 Bucket Policies to enforce access restrictions and retention.

**Compliance Safeguards:**

* GuardDuty and Security Hub can alert on abnormal message patterns or unauthorized transmission behavior.
* IAM Policies and Service Control Policies (SCPs) ensure only authorized systems/users can invoke messaging services.

**Possible Evidence to Collect:**

* CloudTrail logs showing message send/receive API calls
* SES event logs showing metadata (e.g., timestamp, sender, destination)
* CloudWatch log sample with message delivery metadata
* Screenshot or export from SIEM showing message metadata captured
* Policy document restricting message content logging
* S3 object metadata showing encryption and access controls

---

**HITRUST Requirement – Audit Log Retention and Archiving**  
**Control ID:** 09.aa Audit Logging  
**Control Type:** Technical  
**Control Level:** Configurable  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that audit logs are retained for a minimum period (e.g., 90 days) and archived for at least one year to support post-incident investigations and meet regulatory compliance obligations.

**Technical & Operational Implementation:**

**AWS Log Retention (90 Days):**

* **AWS CloudTrail**:

  + Configure event history to retain for 90 days by default.
  + Enable delivery of logs to Amazon S3 for long-term storage.
* **Amazon CloudWatch Logs**:

  + Set retention policies for individual log groups to 90 days using the `PutRetentionPolicy` API or CloudFormation templates.
  + Supports exporting to S3 for archival purposes.

**AWS Log Archival (1 Year or Longer):**

* **Amazon S3 with Object Lock & Lifecycle Policy**:

  + Store archived logs (e.g., CloudTrail, Config, VPC Flow Logs) in an S3 bucket.
  + Apply lifecycle rules to transition logs to S3 Glacier or S3 Glacier Deep Archive after 90 days.
  + Configure Object Lock with compliance mode for immutability during the one-year retention period.
* **AWS Config**:

  + Continuously records resource configuration changes and sends snapshots to S3.
  + S3-based logs can be archived and retained based on lifecycle policies.

**Security & Integrity:**

* Enable S3 Server-Side Encryption (SSE-KMS) for all log buckets.
* Enable AWS CloudTrail log file integrity validation for tamper-evident log storage.

**Possible Evidence to Collect:**

* Screenshot or CLI output of CloudTrail configuration showing delivery to S3
* CloudWatch log group retention policy set to 90 days
* S3 bucket lifecycle policy JSON showing transition to Glacier after 90 days and deletion after 1 year
* S3 Object Lock configuration (Compliance Mode + Retention Date)
* Sample archived log files (or filenames with timestamped paths)
* AWS Config rule snapshots and delivery confirmation to S3

---

**HITRUST Requirement – Secure Audit Logging for Confidential Data Access and Modifications**  
**Control ID:** 09.aa Audit Logging  
**Control Type:** Technical  
**Control Level:** System Enforced  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure secure and immutable audit records are generated each time a user accesses, creates, updates, or deletes covered and/or confidential information to support forensic analysis and compliance.

**Technical & Operational Implementation:**

**Audit Trail Creation:**

* **AWS CloudTrail**:

  + Enables logging of all management and data events (e.g., `GetObject`, `PutObject`, `DeleteObject`) in services like Amazon S3, DynamoDB, and RDS.
  + Activate Data Event Loggin**g** specifically for S3 buckets and Lambda functions that process sensitive data.
* **Amazon S3 Server Access Logs** *(Optional Complement)*:

  + Capture object-level access (GET, PUT, DELETE) for buckets storing covered data.
* **AWS Config**:

  + Records configuration changes across AWS services, tracking resource updates including IAM policies and encryption status.
* **CloudWatch Logs + Insights**:

  + Aggregate and analyze access patterns and modification events in near real-time.

**Security & Integrity of Logs:**

* Store logs in an S3 bucket with:

  + SSE-KMS encryption,
  + Object Lock in Compliance Mode, and
  + Access controls restricting log modification to specific IAM roles only.
* Enable CloudTrail Integrity Validation to detect tampering.

**Possible Evidence to Collect:**

* CloudTrail log sample showing `GetObject`, `PutObject`, `DeleteObject` for confidential data
* Data event configuration screenshot for CloudTrail and target S3 bucket(s)
* S3 bucket policy demonstrating restricted access and encryption
* AWS Config history showing resource modifications (e.g., updates to security groups or roles)
* Evidence of immutable storage (S3 Object Lock configuration)
* CloudWatch Insights query showing event history for sensitive operations

---

**HITRUST Requirement – Justification and Periodic Review of Auditable Events**  
**Control ID:** 09.aa Audit Logging  
**Control Type:** Administrative / Technical  
**Control Level:** Policy-Governed and System Enforced  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure the organization documents the rationale for auditable events selected for continuous monitoring and reviews the listing annually to support effective incident investigations and risk-based oversight.

**Technical & Operational Implementation:**

**Documented Rationale for Audit Scope:**

* Maintain a formal policy or decision register outlining:

  + Why certain AWS events (e.g., `ConsoleLogin`, `DeleteObject`, `PutObjectAcl`, etc.) are tracked continuously.
  + The relationship between audit events and risk scenarios (e.g., unauthorized access, privilege escalation, resource exfiltration).
* Include references to industry best practices for justification.

**Continuous Monitoring Configurations:**

* AWS CloudTrail is configured to:

  + Track all management and data plane events across AWS accounts.
  + Send events to centralized log buckets and optionally to CloudWatch Logs for immediate alerting.
* AWS Config rules monitor configuration drift and changes.
* Use Security Hub or SIEM integrations to continuously analyze and correlate audit data.

**Annual Review Process:**

* Assign responsibility to the compliance or security operations team to:

  + Review the CloudTrail event selectors, AWS Config rules, and GuardDuty findings.
  + Conduct this review at least every 12 months (using internal policy or ticketing system, e.g., Jira).
  + Document evidence of review, findings, and any updates to the audit scope.

**Possible Evidence to Collect:**

* Audit policy document with rationale for event selection
* List of AWS CloudTrail event selectors with justification mapping
* Screenshot or export of AWS Config rule set related to auditing
* Review logs or tickets showing the annual assessment of audit configurations
* Audit review meeting notes or compliance report with a “Reviewed on” timestamp

---

**HITRUST Requirement – Logging Privileged User Activities**  
**Control ID:** 09.aa Audit Logging  
**Control Type:** Technical  
**Control Level:** System Enforced  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(D) – Information System Activity Review

**Control Objective:**  
Ensure that all privileged user activities are captured with sufficient detail to detect inappropriate actions and support forensic investigations in AWS-hosted environments.

**Technical & Operational Implementation:**

**Logging and Monitoring Activities of Privileged Users:**

* **AWS CloudTrail** is configured to capture:

  + Event success/failure (e.g., `errorCode` or `responseElements`)
  + Timestamp (`eventTime`)
  + Action details (`eventName`, `requestParameters`, `responseElements`)
  + Identity of the calling entity (`userIdentity`, `arn`)
  + Affected resources and processes (`resourceName`, `eventSource`)
* **AWS CloudTrail Lake** or **Athena** queries can be used to isolate:

  + Events initiated by users with elevated IAM roles or group memberships (e.g., `AdministratorAccess`, `PowerUserAccess`)
  + Sensitive operations like `DeleteTrail`, `PutBucketAcl`, `TerminateInstances`, etc.
* **Amazon CloudWatch Logs Insights** is used to filter for anomalous behavior or error patterns for privileged roles.
* **GuardDuty** and **Security Hub** detect suspicious use of root accounts, privilege escalation attempts, and unusual API usage.

**Correlating Events with System-Level Context:**

* Use AWS Systems Manager Session Manager to log interactive sessions from privileged users on EC2 instances.
* Log SSM session activities to CloudWatch Logs with session transcripts and command history.
* Maintain identity attribution via federated login from AWS IAM Identity Center (formerly AWS SSO) or Okta, linking back to human identity.

**Possible Evidence to Collect:**

* CloudTrail log entries showing admin activity with fields: `eventName`, `eventTime`, `userIdentity`, `responseElements`
* IAM role policy documentation showing scope of privileges
* Screenshots of SSM session logs in CloudWatch
* GuardDuty findings for privileged user anomalies
* Compliance ticket or report demonstrating review of privileged user activity

---

**HITRUST Requirement – Audit Log Review Procedures**  
**Control ID:** 09.ab Monitoring System Use  
**Control Type:** Administrative and Technical  
**Control Level:** Policy and System Enforced  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(D) – Information System Activity Review

**Control Objective:**  
Establish and enforce structured procedures for the periodic review of audit logs in AWS environments, including defined frequency, documentation, personnel roles, and qualifications.

**Technical & Operational Implementation:**

**Audit Log Review Frequency:**

* Define log review cadence in the organization’s Information Security Policy or System Monitoring SOP.
* Examples:

  + Daily: critical AWS services (e.g., IAM, CloudTrail, GuardDuty alerts)
  + Weekly/Bi-weekly: infrastructure configuration changes (Config, CloudFormation)
  + Monthly: EC2, S3 access logs and billing anomalies

**Documentation of Log Reviews:**

* Use internal ticketing or compliance platforms (e.g., JIRA) to record:

  + Reviewer name and role
  + Timeframe of logs reviewed
  + Summary of findings or anomalies
  + Actions taken (if applicable)
* Use AWS Security Hub or Audit Manager to generate periodic reports and export evidence.

**Defined Roles and Responsibilities:**

* Roles involved: Cloud Security Engineers, Compliance Analysts, DevSecOps
* Each assigned role has a documented responsibility matrix (RACI model) aligned with system categories (e.g., networking, IAM, compute).

**Qualifications and Certifications:**

* Personnel responsible for log review must have one or more of the following:

  + Certified Cloud Security Professional (CCSP)
  + AWS Certified Security – Specialty
  + Certified Information Systems Auditor (CISA)
  + Experience with log analysis tools (e.g., Splunk, CloudWatch, GuardDuty)

**Possible Evidence to Collect:**

* Policy or SOP showing log review frequency and documentation expectations
* Audit logs showing review records in ticketing systems
* Reviewer training logs or certification transcripts
* Screenshots of CloudTrail or Security Hub reports with timestamps
* Role assignment matrix detailing responsibilities of reviewers

---

**HITRUST Requirement – Continuous System Monitoring for Anomalies and Optimal State**  
**Control ID:** 09.ab Monitoring System Use  
**Control Type:** Technical  
**Control Level:** System Enforced  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that AWS-based systems are continuously monitored to detect anomalies or signs of system malfunction or compromise, and to validate optimal, resilient, and secure operations.

**Technical & Operational Implementation:**

**Monitoring and Anomaly Detection:**

* **Amazon CloudWatch** is configured to monitor key performance indicators (CPU, memory, network I/O, etc.) for EC2, RDS, Lambda, and other AWS services.
* **AWS CloudTrail** is enabled across all regions to log API activity for security event auditing and anomaly correlation.
* **AWS GuardDuty** is deployed for intelligent threat detection using machine learning to identify:

  + Unusual API calls (e.g., unauthorized access attempts)
  + Suspicious network traffic (e.g., port scanning or known malware)
  + EC2 instance compromise or IAM credential exfiltration

**Resilience and Availability Monitoring:**

* Use AWS Health Dashboard and AWS Trusted Advisor for proactive alerts on system health and resilience risks (e.g., service limits, open ports).
* Leverage Auto Scaling Groups and Elastic Load Balancing to maintain optimal availability and system resilience.
* Configure AWS Config and Security Hub for compliance drift detection and correlation with security baselines.

**Operational Response and Validation:**

* Set CloudWatch Alarms with SNS notifications to automatically alert incident response teams.
* Use AWS Systems Manager OpsCenter to track and remediate operational anomalies.
* Integrate all security findings with a SIEM (e.g., Splunk or CrowdStrike) to enable centralized alert correlation and behavioral baselining.

**Possible Evidence to Collect:**

* CloudWatch dashboard screenshots showing monitored metrics
* GuardDuty findings with timestamps and descriptions
* CloudTrail logs showing user and service actions
* SNS alert logs demonstrating notification configuration
* OpsCenter incident records for anomalies
* Policy documents defining monitoring scope and thresholds

---

**HITRUST Requirement – Comprehensive Monitoring of Privileged Operations and Access Events**  
**Control ID:** 09.ab Monitoring System Use  
**Control Type:** Technical  
**Control Level:** System Enforced  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that AWS systems log and monitor privileged operations, authorized/unauthorized access attempts, and system alerts to detect misuse, enhance accountability, and support incident response.

**Technical & Operational Implementation:**

**Monitoring of Privileged Operations:**

* Use AWS IAM Access Analyzer, CloudTrail, and AWS Config to track use of privileged accounts, such as `AdministratorAccess` or roles with sensitive permissions.
* AWS CloudTrail logs:

  + API calls related to EC2 instance start/stop (`StartInstances`, `StopInstances`)
  + Attachments/detachments of EBS volumes or ENIs (I/O devices)
* Amazon GuardDuty flags unusual use of root or IAM permissions as potential privilege escalation.

**Monitoring of Authorized Access:**

* CloudTrail captures:

  + User identity (ARN), source IP, user agent
  + Timestamps, event name/type
  + Accessed S3 buckets, RDS instances, EC2 resources
* Amazon S3 server access logs or CloudWatch Logs for detailed access patterns to data and tools.

**Monitoring of Unauthorized Access Attempts:**

* GuardDuty detects:

  + Login attempts to deactivated or non-existent IAM users
  + IAM policy violations (e.g., denied actions)
  + Access attempts from anomalous locations or unauthorized regions
* AWS WAF, Network Firewall, and VPC Flow Logs monitor:

  + Unusual access patterns or blocked traffic
  + IDS/IPS integration with third-party tools like Palo Alto, CrowdStrike(via Gateway Load Balancer or partner appliances)

**Monitoring of System Alerts or Failures:**

* CloudWatch configured with:

  + Metrics for `StatusCheckFailed`, `SystemReboot`, and `DiskReadOps`
  + Custom logs from console errors, Lambda exceptions, ECS task failures
* Amazon EventBridge and SNS for triggering alarms on failures, security group changes, or misconfigured security settings
* AWS Security Hub aggregates and correlates alerts from all integrated services, including third-party intrusion detection systems.

**Possible Evidence to Collect:**

* CloudTrail logs showing privileged role actions and access attempts
* GuardDuty reports detailing privilege escalation or anomaly detection
* IAM role usage patterns and changes captured by AWS Config
* CloudWatch alert rules and SNS notification evidence
* Logs of blocked/denied network access (VPC Flow Logs, AWS WAF logs)
* Screenshots of Security Hub findings or third-party SIEM integrations
* Policy/procedure documents outlining roles and monitoring responsibilities

---

**HITRUST Requirement – Compliance with Legal Requirements for Access Monitoring**  
**Control ID:** 09.ab Monitoring System Use  
**Control Type:** Administrative  
**Control Level:** Policy and Procedural  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(D) – Information System Activity Review

**Control Objective:**  
Ensure that the organization's monitoring of authorized and unauthorized access complies with all applicable legal and regulatory requirements, including data privacy and security laws.

**Technical & Operational Implementation:**

**Compliance Alignment:**

* AWS customers must ensure that their use of services (e.g., monitoring user actions in CloudTrail or GuardDuty) adheres to jurisdiction-specific privacy laws (e.g. HIPAA, CCPA).
* Legal counsel is consulted to interpret laws governing the collection, analysis, and retention of access logs, especially when logs contain personal identifiers.

**Monitoring Configuration:**

* Use AWS CloudTrail and Amazon CloudWatch to monitor all access and administrative events.
* Enable AWS Config for configuration change tracking and compliance audits.
* Leverage AWS Security Hub and Amazon GuardDuty for automated threat detection and alerting on unauthorized access attempts.

**Regional Compliance:**

* Implement data residency controls (e.g., using AWS Regions and Availability Zones strategically) to ensure log data is retained and processed within legally acceptable jurisdictions.
* Enable AWS Organizations service control policies (SCPs) to restrict unauthorized logging or monitoring across accounts.

**Documentation and Retention:**

* Maintain detailed records of access logs and audit events in Amazon S3 with bucket policies enforcing encryption and retention using Object Lock and lifecycle policies.
* Archive logs in AWS Glacier or AWS Backup for long-term retention as required by law.

**Possible Evidence to Collect:**

* Log retention policy referencing legal compliance
* Screenshots of CloudTrail, GuardDuty, and Config settings
* Audit logs demonstrating access attempts and detection of unauthorized activity
* Documentation of legal counsel engagement or internal policy alignment with regional laws
* SCP policy documents restricting unauthorized changes to monitoring configurations

---

**HITRUST Requirement – Monitoring of Confidential Information Systems and Physical Access**  
**Control ID:** 09.ab Monitoring System Use  
**Control Type:** Technical and Administrative  
**Control Level:** Implementation and Monitoring  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls; §164.310(a)(2)(ii) – Facility Security Plan

**Control Objective:**  
Ensure confidential information systems are monitored using automated tools and strategic logging capabilities, including physical and network-level detection mechanisms, to identify unauthorized access, data modification, or anomalies.

**Technical & Operational Implementation:**

**Automated Monitoring and Log Analysis:**

* Use AWS CloudTrail for API activity logging across AWS accounts and services.
* Use Amazon CloudWatch Logs Insights for log analysis, including filtering access to sensitive resources.
* Enable Amazon GuardDuty for threat detection and correlation of events indicating unauthorized access or attacks on sensitive systems.
* Use AWS Security Hub for centralized visibility of findings related to sensitive system access and anomalies.

**Monitoring Device Deployment:**

* Deploy AWS Config Rules and AWS Inspector in strategically selected AWS accounts (e.g., environments processing PHI/PII).
* Set up Amazon VPC Traffic Mirroring for ad hoc packet-level monitoring of EC2 instances.

**Physical Access Review:**

* For hybrid environments, ensure physical facility access logs (via integrated third-party DCIM or security systems) are reviewed weekly and after security incidents.
* In AWS, leverage AWS Artifact for reviewing physical security compliance of AWS data centers and SOC 2 Type II reports.

**Network Flow Analysis (DMZ-style):**

* Use Amazon VPC Flow Logs to monitor network flows at the subnet, ENI, and VPC levels.
* Stream flow logs to Amazon S3 and analyze using Amazon Athena or integrate with Amazon Kinesis Firehose to forward to a SIEM.
* Use Amazon GuardDuty and VPC Reachability Analyzer to detect anomalous DMZ-style activity across public/private subnets and edge routing.

**Possible Evidence to Collect:**

* GuardDuty or CloudTrail logs showing access to confidential records
* VPC Flow Log exports with evidence of NetFlow-style collection
* Weekly physical access log review entries (from corporate security or building badge systems)
* Screenshots of AWS Config Rules triggering on strategic or ad hoc events
* Centralized dashboards (e.g., QuickSight or SIEM tools) showing anomalous flow analytics
* AWS Artifact SOC 2 Type II or ISO 27001 reports referencing physical access reviews

---

**HITRUST Requirement – Audit Reduction and Report Generation Support**  
**Control ID:** 09.ab Monitoring System Use  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that auditing and monitoring tools used in AWS environments facilitate audit data reduction and support generation of reports to assist with security review, compliance tracking, and incident response.

**Technical & Operational Implementation:**

**Audit Reduction:**

* Use Amazon CloudWatch Logs Insights to query and filter high-volume logs (e.g., API events, VPC flow logs), reducing noise and isolating relevant entries.
* Use AWS CloudTrail Lake for advanced queries on event history with filtering and time-bounded logic.
* Implement AWS Lambda functions to preprocess CloudTrail/GuardDuty logs and extract meaningful patterns or policy violations before sending to SIEMs.
* Apply Athena queries on S3-stored logs (CloudTrail, VPC Flow Logs) to reduce the scope of full log datasets.

**Report Generation:**

* Leverage Amazon QuickSight for visual report generation from CloudTrail Lake, Athena, or Redshift data sources.
* Generate regular compliance and security reports using AWS Security Hub insights and AWS Config conformance packs.
* Forward logs to third-party tools like Splunk or Elastic Stack for customizable audit reporting.
* Use AWS Trusted Advisor and Inspector to support automated summary reports on configuration and vulnerability posture.

**Possible Evidence to Collect:**

* Sample CloudWatch Logs Insights queries showing filtered event patterns.
* Screenshots or exports of audit summary reports (e.g., IAM changes, EC2 access attempts).
* Report schedules or dashboards from QuickSight or Security Hub.
* Lambda code snippets showing audit reduction scripts.
* Athena query logs showing optimization of event data extraction.

---

**HITRUST Requirement – Physical Security Incident Response and Coordination**  
**Control ID:** 09.ab Monitoring System Use  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**  
Ensure timely response to physical security incidents and effective coordination with incident response teams to address root causes, prevent recurrence, and support compliance efforts.

**Technical & Operational Implementation:**

**Physical Security Incident Response:**

* AWS Data Center Controls: AWS operates highly secure facilities with strict physical access controls, surveillance, and security staffing. These controls are validated through third-party audits (SOC 2, ISO 27001, etc.).
* Customer-Side Controls: For hybrid or customer-managed AWS Outposts or Direct Connect, organizations should:

  + Establish physical access logs (badge access, camera footage) via on-prem systems.
  + Investigate tampering or unauthorized access attempts and correlate with AWS service logs if hybrid assets are affected.
* Maintain a Physical Security Response Plan within the broader IR plan to triage facility-related events (e.g., theft, break-ins, badge misuse).

**Coordination with Incident Response Capabilities:**

* Centralize incident tracking using tools like AWS Security Hub, Amazon GuardDuty, and AWS Config, alongside internal ticketing systems (e.g., Jira, ServiceNow).
* Feed outcomes of physical incident investigations into the broader IR workflow using an integrated SIEM (e.g., CrowdStrike, Splunk).
* Update the Incident Response Playbook to include scenarios where physical events (e.g., rack tampering, facility breach) coincide with unauthorized AWS activity (e.g., console logins, network changes).
* Conduct periodic tabletop exercises involving both physical security teams and AWS security operations staff (especially for organizations with AWS Outposts, Local Zones, or Direct Connect).

**Possible Evidence to Collect:**

* Physical security incident reports and IR follow-up logs (e.g., Confluence pages, Jira tickets).
* AWS Config or CloudTrail entries correlated with physical alerts.
* Security playbook excerpts referencing physical-to-digital incident correlation.
* AWS SOC 2 report excerpts for data center physical controls.
* Meeting notes or reports showing coordination between facility security and cloud security teams.

---

**HITRUST Requirement – Protection of Audit Trails and Logs**  
**Control ID:** 09 ac Protection of Log Information  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that access to audit logs and system-generated audit trails is controlled, monitored, and protected from unauthorized access or tampering.

**Technical & Operational Implementation:**

**AWS Log Storage Security:**

* Amazon CloudTrail logs, AWS Config snapshots, and CloudWatch Logs are directed to a secure, centralized Amazon S3 bucket.
* The bucket enforces:

  + IAM-based access control using least privilege.
  + Bucket policies that deny access unless specific service conditions or encryption states are met.
  + S3 Object Lock (governance or compliance mode) for immutability.
  + S3 server-side encryption (SSE-S3, SSE-KMS) to ensure logs are encrypted at rest.

**IAM Role and User Restrictions:**

* Separate IAM roles for logging services (write-only) and for audit reviewers (read-only, no delete).
* Use service control policies (SCPs) in AWS Organizations to block deletion or modification of logs across accounts.

**Additional Protections:**

* Enable AWS CloudTrail Log Integrity Validation to detect changes to logs.
* Log access attempts and API calls using CloudTrail itself, and route logs to Amazon CloudWatch and a centralized SIEM (e.g., Splunk, CrowdStrike).
* Use AWS Security Hub and Amazon GuardDuty to alert on unauthorized access attempts or misconfigured logging resources.

**Possible Evidence to Collect:**

* Screenshot of S3 bucket policies restricting access to logs.
* IAM policy or SCP examples showing log protection.
* Sample CloudTrail log entries showing access attempts to log storage.
* CloudWatch alert configuration for log access violations.
* Proof of Object Lock configuration for log buckets.

---

**HITRUST Requirement – Logging and Review of Administrator Activities**  
**Control ID:** 09 ad Administrator and Operator Logs  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that logging is enabled to capture activities of system administrators and operators, and that these logs are reviewed regularly for potential unauthorized or anomalous activity.

**Technical & Operational Implementation:**

**Administrator Logging:**

* Enable AWS CloudTrail across all AWS accounts and regions to capture API activity of administrators using root or IAM users/roles.
* Configure CloudTrail Insight Events to detect unusual patterns from administrative accounts (e.g., bursts of activity or first-time service use).
* Use AWS Config to track changes to configuration resources (e.g., IAM, EC2, S3) initiated by admins.

**Separation and Tagging of Admin Activity:**

* Identify administrator actions by tagging IAM users/roles (e.g., "RoleType=Admin") or applying CloudTrail filters for high-privilege operations (e.g., `CreateUser`, `AttachRolePolicy`, `TerminateInstances`).

**Log Review and Monitoring:**

* Forward CloudTrail logs to Amazon CloudWatch Logs for metric filtering and alerting.
* Use AWS Security Hub or a third-party SIEM (e.g CrowdStrike) to automatically review and score risk levels of administrator actions.
* Schedule periodic (e.g., weekly) reviews of key log activity, such as unauthorized access attempts or unusual resource changes.

**Possible Evidence to Collect:**

* CloudTrail configuration screenshots with Insight Events enabled.
* IAM policy or tagging structure used to identify administrator roles.
* Log review SOP or audit trail demonstrating recent review of administrator logs.
* CloudWatch alarm configuration for critical admin actions (e.g., `DeleteTrail`, `DetachPolicy`).
* SIEM dashboard screenshot showing operator activity analysis.

---

**HITRUST Requirement – Logging of System Faults and Errors**  
**Control ID:** 09.ae Fault Logging  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure faults reported by users or system programs are logged, and error logging is enabled where supported, to facilitate troubleshooting, incident analysis, and system reliability in AWS environments.

**Technical & Operational Implementation:**

**Logging of System Faults:**

* Enable AWS CloudWatch Logs on EC2 instances, Lambda functions, ECS containers, and other compute resources to collect application/system logs where user-reported or system faults occur.
* Use CloudWatch Agent or AWS Systems Manager Agent (SSM Agent) to collect OS-level system logs (e.g., `/var/log/syslog`, Windows Event Logs).
* Configure Elastic Load Balancing (ELB) access logs and VPC Flow Logs to detect issues with network communication or service accessibility.

**Error Logging Enablement:**

* Configure applications hosted on AWS (e.g., web apps on EC2, Lambda, or containers) to log errors to CloudWatch or external log destinations (e.g., S3, OpenSearch).
* Use AWS Lambda Destinations and failure handling options to capture invocation and processing errors automatically.
* For RDS/Aurora, enable Enhanced Monitoring and Event Subscriptions to log database errors.

**Alerting & Review:**

* Set up CloudWatch Alarms for error rate thresholds (e.g., `5XX` errors from API Gateway, `Invocation Errors` from Lambda).
* Integrate logs into AWS Security Hub, AWS Config, or a third-party SIEM for analysis and alerting.

**Possible Evidence to Collect:**

* CloudWatch Logs configuration screenshots for EC2, Lambda, or RDS.
* Example log entries showing captured fault or error messages.
* Screenshots of enabled logging for AWS services (e.g., Lambda Console, CloudTrail).
* CloudWatch Alarm definition for error alerts.
* Policy/SOP requiring error logging and automated handling in system designs.

---

**HITRUST Requirement – Time Synchronization for Consistent Log Timestamps**  
**Control ID:** 09.af Clock Synchronization  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that all systems, including servers and network devices in the AWS environment, consistently retrieve time information from at least two synchronized sources to ensure log integrity and reliable forensic analysis.

**Technical & Operational Implementation:**

**AWS Time Synchronization Services:**

* AWS automatically synchronizes all EC2 instances with the Amazon Time Sync Service, which is backed by a fleet of redundant and geographically distributed reference time servers.
* For high-accuracy timekeeping, Chrony or ntpd can be configured on EC2 instances to poll the Amazon Time Sync Service and fallback NTP sources.

**Network Equipment & Hybrid Environments:**

* For hybrid environments (e.g., using AWS Outposts or on-premises gear connecting via AWS Direct Connect or VPN), organizations should:

  + Configure network appliances to use internal NTP servers that are synchronized with the Amazon Time Sync Service or with other public stratum 1 time sources (e.g., <http://time.cloudflare.com> or NIST).
  + Validate that AWS-managed services (e.g., RDS, EKS, ECS, etc.) inherit AWS Time Sync for consistent time tracking.

**Log Timestamp Consistency:**

* CloudTrail, CloudWatch Logs, VPC Flow Logs, and GuardDuty all use consistent, UTC-based timestamps.
* When logs are collected from EC2 or hybrid systems, ensure the system timezone is UTC and the NTP daemon is operational.

**Redundancy & Validation:**

* Although AWS provides a single IP endpoint, the Amazon Time Sync Service is backed by multiple redundant time sources.
* Organizations may configure a secondary external NTP source as a failover, particularly in hybrid cloud setups.

**Possible Evidence to Collect:**

* Screenshot of `chronyc sources` or `ntpq -p` from EC2 instances showing Amazon Time Sync usage.
* Configuration file samples (e.g., `/etc/chrony.conf`, `/etc/ntp.conf`) specifying multiple time sources.
* AWS documentation reference describing Amazon Time Sync Service use.
* Log samples from CloudTrail or CloudWatch with synchronized timestamps.
* Architecture diagram showing time synchronization design for hybrid infrastructure.

---

**HITRUST Requirement – Segregation of Duties and Audit**  
**Control ID:** 09.c Segregation of Duties  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.312(a)(1) – Access Control; 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that no single individual can access, modify, or use information assets without appropriate authorization and detection mechanisms in AWS-hosted environments.

**Technical & Operational Implementation:**

**Enforcing Least Privilege & Role Segregation:**

* Define fine-grained IAM roles and policies to enforce least privilege. Use IAM Conditions, Resource-level permissions, and Service Control Policies (SCPs) for guardrails.
* Implement segregation of duties by ensuring that users who approve access cannot grant or provision it themselves (e.g., separate roles for approver and executor in Change Manager or IAM Access Analyzer workflows).

**Authorization Mechanisms:**

* Integrate AWS IAM or AWS SSO with identity providers (e.g., Okta) to enforce centralized authentication and MFA.
* Use attribute-based access control (ABAC) with IAM tags to control access based on dynamic user attributes (e.g., department, clearance level).

**Detection Mechanisms:**

* Enable AWS CloudTrail for full API-level auditability across AWS services.
* Stream logs to Amazon CloudWatch Logs, AWS OpenSearch, or a third-party SIEM for behavior analysis and anomaly detection.
* Enable Amazon GuardDuty and AWS Config to detect unexpected access patterns or unauthorized changes to resources.

**Data Access Control:**

* Use S3 Bucket Policies and Access Points to restrict and monitor access to sensitive data.
* Enable Amazon Macie to discover and monitor sensitive information like PII or PHI in S3.

**Privileged Action Monitoring:**

* Set up CloudTrail Insights to detect unusual IAM activity (e.g., privilege escalation, disabling logging).
* Implement AWS Audit Manager or GRC platforms to continuously monitor policy violations and control effectiveness.

**Possible Evidence to Collect:**

* IAM Policy JSON files showing scoped permissions and role boundaries.
* CloudTrail log samples showing privileged actions tied to individual identities.
* SIEM reports showing detection of unauthorized access or modifications.
* S3 bucket policy and Macie findings demonstrating protection of sensitive data.
* Screenshots from GuardDuty or AWS Config highlighting unauthorized change detection.

---

**HITRUST Requirement: Job descriptions contain assigned duties and responsibilities that support SoD**

**Control ID:** 09.c Segregation of Duties  
**Control Type:** Administrative  
**Control Level:** Baseline  
**HIPAA Mapping:** 45 CFR §164.312(a)(1) – Access Control

**AWS Technical & Operational Implementation**

1. **Role Definition and Job Description Accuracy**

* Job roles and responsibilities should be formally defined in HR systems and aligned with least privilege principles for AWS access.
* Within AWS, IAM roles and permissions should be designed to mirror the job functions defined in job descriptions, ensuring tasks are not improperly combined (e.g., deployment and approval cannot be done by the same role).

2. **Enforcement through AWS IAM and AWS Organizations**

* Use IAM roles and policies to strictly enforce separation of duties (e.g., DevOps team can deploy but not approve production changes).
* Service Control Policies (SCPs) in AWS Organizations help enforce guardrails, ensuring job responsibilities don’t drift beyond defined limits.

3. **Audit and Review**

* Conduct periodic access reviews using tools like AWS IAM Access Analyzer and AWS Config Rules to ensure IAM roles align with defined job descriptions.
* Reviews of job roles and access assignments can be documented in AWS Audit Manager or tracked via third-party GRC platforms.

**Possible Evidence to Collect**

* HR job descriptions and associated access role documentation
* IAM policy and role assignments aligned with those descriptions
* Review records from IAM Access Analyzer or AWS Config conformance packs
* Audit logs showing separation of duties enforcement (e.g., CloudTrail logs indicating change request vs. deployment actions by different identities)

---

**HITRUST Requirement: Security audit activities always remain independent**

**Control Objective:**  
Ensure that security audits are conducted with objectivity, free from influence by the systems or personnel being audited.

**Control ID:** 09.c Segregation of Duties  
**Control Type:** Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(8) – Evaluation

**Technical & Operational Implementation**

1. **Independence of Audit Activities**

* AWS provides audit logs (via CloudTrail, Config, CloudWatch, etc.) that can be accessed and analyzed by dedicated audit personnel or external assessors, separate from DevOps or infrastructure management teams.
* Use cross-account logging and centralized security accounts (e.g., AWS Organizations with delegated admin) to ensure logs are reviewed by an independent team.
* AWS Audit Manager enables mapping of controls to assessments and can be used by internal auditors without requiring direct infrastructure access.

2. **Organizational Separation**

* Define roles and responsibilities in policies or AWS IAM groups to clearly separate:

  + Operations teams (e.g., those deploying infrastructure)
  + Security/compliance teams (e.g., those performing the audits)
* Leverage AWS IAM Identity Center to assign access such that auditors cannot modify systems under review.

3. **Use of Third-Party Auditors**

* AWS encourages and supports third-party assessments by providing:

  + AWS Artifact documentation for certifications
  + Tools like Security Hub and Audit Manager to collect evidence without requiring infrastructure privileges

**Possible Evidence to Collect**

* Role-based access configurations for audit team in IAM
* Documentation of segregation of duties in audit policies
* Reports from AWS Audit Manager showing control review activity
* CloudTrail configurations showing logs are directed to a read-only, dedicated audit account

---

**HITRUST Requirement: The initiation of an event is separated from its authorization**

**Control ID:** 09.c Segregation of Duties  
**Control Type:** Administrative  
**Control Level:** Baseline  
**HIPAA Mapping:** 45 CFR §164.308(a)(4)(ii)(C) – Access Establishment and Modification

**Technical & Operational Implementation**

1. **Segregation of Initiation and Approval via IAM Policies**

* Use **A**WS IAM role-based access control (RBAC) to ensure no single user or role can both initiate and approve critical events (e.g., financial transactions, access changes, system modifications).
* Example: An IAM role for initiating an S3 object deletion can be separated from a second role that must approve via AWS Step Functions, AWS Lambda, or a manual workflow.

2. **Approval Workflow Mechanisms**

* Implement **a**pproval workflows using AWS Systems Manager Change Manager, AWS Service Catalog, or third-party tools integrated via API Gateway and Lambda.
* Enforce multi-user approval via tools like AWS CodePipeline for CI/CD and CloudFormation StackSets with approval workflows.

3. **Logging and Oversight**

* Use AWS CloudTrail to audit and track event initiation and approval actions.
* Combine with Amazon CloudWatch and AWS Config Rules to detect policy violations or unauthorized bundling of roles.

**Possible Evidence to Collect**

* IAM policies that demonstrate role separation for initiation and approval actions
* Change Manager approval flows with separation of initiating and approving roles
* CloudTrail logs showing temporal and identity-based separation of execution
* AWS Config conformance packs indicating compliance with SoD enforcement

---

**HITRUST Requirement – Separation of Duties or Compensating Monitoring Controls**

**Control ID:** 09.c Segregation of Duties  
**Control Type:** Administrative  
**Control Level:** Baseline  
**HIPAA Mapping:** 45 CFR §164.308(a)(4)(ii)(C) – Access Establishment and Modification

**Control Objective:**

Limit the risk of unauthorized or unintentional modification of information assets by enforcing separation of duties or, where that is not feasible, implementing compensating controls such as audit trails, management supervision, or dual authorization mechanisms in AWS-hosted environments.

**Technical & Operational Implementation:**

**Enforcing Role Segregation:**

* Define distinct IAM roles for initiators, approvers, and deployers using AWS IAM and IAM Policies.
* Apply AWS Organizations Service Control Policies (SCPs) to enforce functional boundaries between security, development, and operations roles.
* Use IAM role chaining and external ID conditions to prevent role misuse.

**Compensating Monitoring Controls (when SoD is not feasible):**

* Enable AWS CloudTrail across all AWS accounts to capture API activity tied to user identity.
* Use AWS Config to track configuration changes and trigger alerts when critical resources are modified.
* Leverage CloudWatch Alarms, EventBridge Rules, and Security Hub to detect and report suspicious changes in real-time.

**Dual Control and Approvals:**

* Use AWS Systems Manager Change Manager to require approval workflows before infrastructure modifications.
* Configure manual or automated change approval processes using AWS Service Catalog for sensitive operations.

**Logging and Audit Trails:**

* Forward CloudTrail logs to Amazon S3, and integrate with Amazon Athena or third-party SIEMs for forensic investigation.
* Apply granular bucket policies to restrict access to logs, ensuring only authorized personnel can view or modify them.

**Possible Evidence to Collect:**

* IAM role and policy configurations showing functional separation.
* SCP definitions that enforce privilege boundaries across organizational units.
* Change Manager or Service Catalog approval flow records.
* CloudTrail logs showing dual-approval or delegated privilege activity.
* Screenshots or reports from AWS Config and Security Hub highlighting monitoring of unauthorized changes.
* Audit logs stored securely in S3 with access restricted via bucket policy and logged using CloudTrail

---

**HITRUST Requirement – Role-Based Access & Separation of Duties for Administrators**

**Control ID:** 09.c Segregation of Duties  
**Control Type:** Administrative / Technical  
**Control Level:** Baseline  
**HIPAA Mapping:** 45 CFR §164.308(a)(3)(ii)(A) – Workforce Clearance Procedure; 45 CFR §164.308(a)(4)(ii)(C) – Access Establishment and Modification

**Control Objective:**

Ensure that the number of administrators is limited to the minimum necessary based on role and responsibility, and that those administering access controls do not audit their own actions to prevent conflicts of interest and enable accountability in AWS environments.

**Technical & Operational Implementation:**

**Minimal Privilege Assignment:**

* Use AWS IAM to define specific roles for administrators with least privilege required to perform their duties.
* Assign administrative rights only to personnel whose job functions require it.
* Regularly review IAM role assignments using AWS IAM Access Analyzer and AWS Organizations' account access reports.

**Segregation Between Access Administration and Audit:**

* Ensure that users with permission to create or manage IAM policies/roles (e.g., access administrators) do not have access to logs or CloudTrail data.
* Create separate roles for access control administration and for auditing, enforced through IAM policy boundaries.

**Monitoring and Oversight:**

* Use AWS CloudTrail to log all administrative activity and ensure audit records are immutable and accessible only by authorized audit personnel.
* Use AWS Config to monitor changes to IAM configurations and flag any deviations from approved policies.
* Configure AWS Audit Manager or integrate with third-party compliance platforms (e.g., Drata, Vanta) to validate control effectiveness and detect cross-role violations.

**Possible Evidence to Collect:**

* IAM role definitions and policies showing separation between access administrators and audit personnel.
* Access Analyzer reports demonstrating minimal and justified administrator role usage.
* CloudTrail access policies showing log access is restricted from IAM administrators.
* Config rules or Security Hub insights showing role separation compliance.
* Screenshots or documentation from audit toolsets confirming review is performed by independent personnel.

---

**HITRUST Requirement – Separation of Development, QA, and Production Functions**

**Control ID:** 09.c Segregation of Duties  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(D) – Information System Activity Review; 45 CFR §164.312(a)(1) – Access Control

**Control Objective:**

Ensure that development, testing, quality assurance (QA), and production functions are separated across distinct individuals or teams to prevent unauthorized changes, enhance security, and reduce the risk of collusion or error within AWS environments.

**Technical & Operational Implementation:**

**Environment Segregation:**

* Use AWS Organizations to define separate accounts or OUs for development, QA, and production environments.
* Implement Service Control Policies (SCPs) to restrict cross-environment access and enforce environment boundaries.

**Access Control & IAM Role Isolation:**

* Assign environment-specific IAM roles (e.g., `DevRole`, `QAOps`, `ProdOps`) and apply least privilege principles to prevent unauthorized access across environments.
* Enforce session-based access with AWS IAM Identity Center (SSO) and MFA for role assumption into QA and production.

**Deployment Controls:**

* Use AWS CodePipeline or AWS CodeDeploy to enforce automated approvals and segregation of responsibilities.
* Ensure build artifacts from development cannot be directly pushed to production without QA sign-off using CodePipeline manual approval steps or GitOps workflow controls.

**Monitoring and Detection:**

* Enable CloudTrail, AWS Config, and AWS Security Hub in each environment to monitor and alert on policy violations or unauthorized changes.
* Use GuardDuty and Detective to detect and investigate potential insider threats or lateral movement across environments.

**Possible Evidence to Collect:**

* AWS IAM policy JSON files showing restricted cross-environment access.
* SCP definitions limiting access between development, QA, and production.
* CodePipeline/CodeDeploy approval logs or screenshots showing staged deployment workflow.
* CloudTrail logs demonstrating access and deployment segregation.
* Role assignment reports from IAM Identity Center proving functional separation.

---

**HITRUST Requirement – Separation of Development, QA, and Production Duties**

**Control ID:** 09.c Segregation of Duties  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(D) – Information System Activity Review

**Control Objective:**

Ensure the separation of development, testing, quality assurance, and production functions across AWS environments to maintain independence and prevent unauthorized or accidental changes to production systems.

**Technical & Operational Implementation:**

1. **Environment Isolation:**

* Use AWS Organizations to separate environments by account: one for development, one for staging/testing, and one for production.
* Apply AWS Service Control Policies (SCPs) to prevent users or services from accessing multiple environments without approval.

2. **Role Segregation & Least Privilege:**

* Assign distinct IAM roles to development (`DevOpsRole`), QA (`QAEngineerRole`), and production (`ProdOpsRole`) teams.
* Use IAM policy boundaries and conditions to enforce restricted permissions specific to each environment.

3. **Deployment Pipelines with Approvals:**

* Implement AWS CodePipeline with manual approval steps to promote code from development to QA and then production.
* Use cross-account CodeDeploy or CI/CD systems (e.g., GitHub Actions, CircleCI) with restricted credentials and enforced reviewer workflows.

4. **Authentication & Session Control:**

* Use AWS IAM Identity Center (SSO) with role-based access control to ensure only authorized team members can assume environment-specific roles.
* Require MFA and session tagging for traceability.

5. **Monitoring & Change Detection:**

* Enable AWS CloudTrail, Config, and Security Hub to track changes per environment and detect cross-environment access.
* Configure Amazon CloudWatch or third-party tools (e.g., Datadog) to alert on configuration drift or unapproved deployments.

**Possible Evidence to Collect:**

* SCPs and IAM policy documents showing access boundaries.
* CodePipeline screenshots or logs showing gated deployment stages with approval history.
* CloudTrail logs showing IAM role usage by environment.
* AWS Config conformance packs or rules showing compliance with segregation policies.
* Screenshots or exports from IAM Identity Center showing role-user mapping by function.

---

**HITRUST Requirement – Segregation of Mission-Critical and Support Functions**  
**Control ID:** 09.c Segregation of Duties  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.312(a)(1) – Access Control

**Control Objective:**  
Ensure that mission-critical operations and information system support functions are logically and operationally separated in AWS environments to minimize the risk of unauthorized access, conflicts of interest, and operational failures.

**Technical & Operational Implementation:**

**Functional Separation via IAM Roles and Workflows:**

* Define AWS IAM roles and policies that distinctly separate duties between operations teams (e.g., DevOps, infrastructure) and support teams (e.g., helpdesk, admin support).
* Use IAM Conditions and resource-based policies to restrict access to specific services or data depending on the role’s responsibility.
* Implement Change Manager workflows in AWS Systems Manager that enforce approvals for operational functions distinct from those who execute support tasks.

**Environment Segregation:**

* Utilize AWS Organizations and separate accounts/OUs for production vs. support workloads (e.g., “prod-app” vs. “support-services”) with unique access boundaries.
* Apply Service Control Policies (SCPs) to enforce least privilege across account boundaries.

**Activity Logging & Monitoring:**

* Enable AWS CloudTrail and AWS Config to monitor access and changes by mission-critical roles vs. support functions.
* Configure CloudWatch Alarms and Amazon GuardDuty to alert on privilege escalations, anomalous access between separated roles, or misconfigurations.

**Possible Evidence to Collect:**

* IAM role and policy definitions demonstrating functional separation.
* SCPs showing restricted cross-role capabilities.
* CloudTrail and GuardDuty findings showing enforcement of role boundaries.
* Diagrams or documentation of AWS OU/account structure and designated function boundaries.

---