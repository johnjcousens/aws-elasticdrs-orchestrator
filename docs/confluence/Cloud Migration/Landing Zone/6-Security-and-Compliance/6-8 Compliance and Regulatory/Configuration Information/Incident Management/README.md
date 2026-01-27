# Incident Management

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4986306603/Incident%20Management

**Created by:** Shreya Singh on August 05, 2025  
**Last modified by:** Shreya Singh on August 12, 2025 at 05:23 PM

---

**HITRUST Requirement – HR Point of Contact & Sanction Notification**  
**Control ID:** 02.f Disciplinary Process  
**Control Type:** Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(C) – Sanction Policy

**Control Objective:**  
Ensure that the organization formally assigns responsibility for handling employee-related incidents and promptly communicates sanctions involving security policy violations to appropriate security leadership in AWS-hosted environments.

**Technical & Operational Implementation:**

**Human Resources & Security Incident Coordination:**

* Designate an HR representative as the primary point of contact for coordinating all personnel-related security incidents (e.g., inappropriate access, misuse of credentials).
* Define this role within the organization’s incident response plan and ensure awareness during onboarding and annual training.

**Sanctions Process and Escalation:**

* Establish a documented formal employee sanctions policy aligned with AWS Acceptable Use Policies and internal security policies.
* Integrate workflows in a ticketing or HR system (e.g Jira) that require escalation of employee-related infractions to the CISO or designated representative.
* Ensure the workflow includes identification of the individual involved, description of the violation, investigation steps, and resulting action.

**Monitoring & Audit Trail:**

* Use AWS CloudTrail to monitor employee actions (especially privileged access or resource modifications).
* Connect findings from CloudTrail, GuardDuty, and IAM Access Analyzer to centralized SIEMs or ticketing systems for investigation and HR coordination.
* Ensure the incident is logged with timestamp, account ID, and IAM role used.

**Possible Evidence to Collect:**

* HR policy documentation showing point of contact assignment.
* Incident response plan and organizational chart showing HR and CISO roles.
* Sample sanction reports redacted to show communication to security leadership.
* Audit logs from CloudTrail showing incident investigation trail.
* Screenshots from ServiceNow/Jira workflows demonstrating escalation and resolution steps.

---

**HITRUST Requirement – Disciplinary Process for Security Violations**  
**Control ID:** 02.f Disciplinary Process  
**Control Type:** Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(C) – Sanction Policy

**Control Objective:**  
Establish and enforce a fair, documented, and graduated disciplinary process to respond to verified security breaches, while maintaining accountability in AWS-hosted environments.

**Technical & Operational Implementation:**

**Verification of Breach Prior to Sanction:**

* Use AWS-native tools such as AWS CloudTrail, AWS Config, and Amazon GuardDuty to confirm any suspected policy violation.
* Ensure only verified findings are escalated for disciplinary action through incident response workflows.

**Fair and Graduated Disciplinary Process:**

* Define a formal policy in the HR handbook that outlines fair treatment for employees suspected of breaches.
* Implement a tiered disciplinary response model based on:

  + Severity of incident (e.g., unintentional vs. malicious).
  + Number of prior offenses.
  + Level of training received.
  + Contractual obligations or regulatory impacts.

**Documentation of Disciplinary Events:**

* Use Jira or HRIS platforms to record:

  1. The personnel involved in the investigation and decision-making.
  2. All investigative steps and evidence reviewed.
  3. Timeline of key events (e.g., detection, response, resolution).
  4. Notification records to HR, Legal, CISO, and the employee.
  5. Clear rationale for the final disciplinary decision.
  6. Indication if it was tied to a compliance failure (e.g., HIPAA, HITRUST).
  7. Final resolution and follow-up actions (e.g., training, revocation of access).

**Link to Compliance & Risk Programs:**

* Tie disciplinary findings into the AWS Audit Manager or GRC platforms to track risk themes and identify systemic issues.

**Possible Evidence to Collect:**

* HR disciplinary policy document.
* Redacted samples of disciplinary investigation records.
* Screenshots from Jira or ServiceNow tracking the disciplinary process.
* Logs from AWS CloudTrail supporting breach verification.
* Email notifications or HR communications showing CISO awareness.
* Evidence of policy updates based on recurring incident themes.

---

**HITRUST Requirement – Documentation of Security Incident Investigations**

**Control ID:** 02.f Disciplinary Process  
**Control Type:** Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**

Ensure accountability and transparency by recording personnel involved in AWS-related security incidents and documenting the outcomes for compliance and root cause analysis.

**Technical & Operational Implementation:**

**Employee Involvement Tracking:**

* Use incident response platforms (e.g., AWS Security Hub, Jira) to log:

  + Names and roles of all personnel involved in triage, analysis, remediation, and resolution.
  + Roles can be tracked using IAM role associations in CloudTrail logs or through manual tagging in ticketing systems.

**Outcome Documentation:**

* Document resolution steps, mitigations applied, lessons learned, and follow-up actions.
* Capture these details in:

  + Incident response runbooks (via AWS Systems Manager Documents or Playbooks).
  + Jira tickets linked to AWS Security Hub findings or GuardDuty alerts.
  + AWS Audit Manager evidence collections (for compliance tracking).

**Integration & Automation:**

* Use AWS Config + CloudTrail to correlate IAM actions with user roles during incidents.
* Automate incident tracking workflows using EventBridge + Lambda to tag and track incident participants.
* Store final investigation reports securely in S3 with access logging and encryption (e.g., for review by compliance or legal).

**Possible Evidence to Collect:**

* Jira/ServiceNow incident tickets showing employee assignments and comments.
* AWS IAM user and role mappings from CloudTrail logs.
* Final PDF or markdown reports summarizing each incident and its resolution.
* Screenshots of incident dashboards in AWS Security Hub.
* Evidence of access-controlled S3 bucket storing outcome documentation.

---

**HITRUST Requirement – Management Authorization & Disciplinary Escalation**

**Control ID:** 06.e Prevention of Misuse of Information Assets  
**Control Type:** Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(C) – Sanction Policy, 45 CFR §164.308(a)(6) – Security Incident Procedures

**Control Objective:**

Ensure that information asset usage is explicitly authorized by management and that any unauthorized access or misuse identified in AWS environments is promptly escalated for review and potential disciplinary or legal action.

**Technical & Operational Implementation:**

**Management Approval of Information Assets:**

* All AWS account provisioning (via AWS Control Tower or Service Catalog) requires documented approval from appropriate stakeholders.
* Use tagging strategies (`Owner`, `DataClass`, `ApprovedBy`) to indicate managerial authorization on AWS resources (S3 buckets, RDS, EC2 instances).
* Approval workflows can be automated using AWS Service Catalog or AWS Service Management Connector with platforms like ServiceNow or Jira.

**Detection of Unauthorized Activity:**

* Use AWS CloudTrail, AWS Config, and AWS GuardDuty to detect:

  + Access to unauthorized resources
  + IAM policy violations
  + Data exfiltration attempts
* Raise alerts through Amazon Security Hub or Amazon CloudWatch Alarms, integrating with Slack, Jira, or email for notification to relevant management.

**Escalation for Disciplinary Review:**

* Integrate AWS detection mechanisms with ServiceNow or Jira ticketing systems to automatically assign alerts to designated managers or compliance officers.
* Maintain an incident response escalation matrix mapping alert types to responsible business managers.

**Possible Evidence to Collect:**

* IAM and SCP policy artifacts showing access limitations and ownership tags.
* Security Hub and GuardDuty findings escalated to tickets with assigned managers.
* ServiceNow approval workflow logs for AWS resource provisioning.
* Screenshots or logs showing alert routing and manager acknowledgement.
* Incident documentation showing resolution steps and manager involvement.

---

**HITRUST Requirement – Security Incident Reporting Contacts**

**Control ID:** 11.a Reporting Information Security Events  
**Control Type:** Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**

Ensure that clearly defined and widely communicated points of contact are available for reporting information security incidents, and that both internal and external security contacts are documented and maintained.

**Technical & Operational Implementation:**

**Security Incident Point of Contact:**

* Designate a formal security incident contact (e.g., CISO or SecOps lead) within AWS documentation and communication workflows.
* Include this contact in security policy documents published on Confluence, internal wikis, or AWS SSO welcome banners.

**Communication and Availability:**

* Establish an always-monitored email alias (e.g., `security@company.com`) or PagerDuty escalation path that includes the designated POC and backup personnel.
* Use AWS Chatbot or Amazon SNS with email/SMS triggers to notify the security POC in real-time of incidents detected via CloudTrail, GuardDuty, or Security Hub.

**Third-Party Contact Maintenance:**

* Maintain an up-to-date contact list of CSPs, critical SaaS vendors, and managed service providers in an internal IR playbook (e.g., stored in AWS SSM Parameter Store or encrypted S3 bucket).
* Integrate contacts into ticketing systems like Jira or ServiceNow to ensure rapid outreach in case of third-party breaches.

**Possible Evidence to Collect:**

* Documentation or screenshots showing security incident contact email/Slack/PagerDuty routing configuration.
* Internal policy files or communication plans referencing incident response points of contact.
* GuardDuty/CloudWatch alert notification rule configurations with targeted security escalation.
* Sample contact list of external security partners/vendors with roles and communication details.
* Audit logs showing security alerts being routed to and acknowledged by the designated contact.

---

**HITRUST Requirement – Anonymous Reporting of Security Issues**

**Control ID:** 11.a Reporting Information Security Events  
**Control Type:** Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

### **Control Objective:**

Ensure that individuals can report suspected or actual information security concerns without fear of retaliation, including through anonymous means.

**Technical & Operational Implementation:**

Anonymous Reporting Channels:

* Establish an anonymous security incident reporting form using AWS services such as:

  + AWS Amplify + Lambda + DynamoDB: For hosting and processing anonymous web forms securely.
  + Amazon API Gateway with IAM-controlled Lambda: To ingest and store anonymous submissions with auditability.
  + Encrypt submissions with AWS KMS and store in Amazon S3 or DynamoDB with restricted access.

3rd-Party Integration (Optional):

* Integrate with third-party whistleblower platforms (e.g., OneTrust) that offer secure and anonymous reporting portals.
* Configure those platforms to forward anonymized alerts via Amazon SNS or AWS Security Hub custom findings for triage.

Privacy & Access Controls:

* Implement strict access control on stored reports using IAM, S3 bucket policies, or parameter store policies to ensure anonymity.
* Enable CloudTrail and AWS Config to track access to anonymous submissions without compromising the identity of reporters.

**Possible Evidence to Collect:**

* Screenshots or URLs of hosted anonymous reporting portals (internal or external).
* IAM role and policy JSON files showing restricted access to anonymous report submissions.
* CloudTrail logs showing access controls around submission storage locations.
* Documentation or SOP outlining how anonymous reports are processed and escalated securely.
* Sample incident reports (redacted) submitted via anonymous channels.

---

**HITRUST Requirement – Comprehensive Incident Management Program**

**Control ID:** 11.a Reporting Information Security Events  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6) – Security Incident Procedures

**Control Objective:**

Establish a robust, scalable incident management program for AWS-hosted environments to ensure timely detection, handling, documentation, and communication of security incidents — including roles, workflows, forensics, and sanctions.

**Technical & Operational Implementation:**

**Incident Policies & Procedures**

* Maintain documented Incident Response Plan (IRP) in a version-controlled repo (e.g., AWS CodeCommit or S3 with versioning).
* Include procedures for:

  + Triage & classification of security events via AWS Security Hub custom insights.
  + Root cause analysis via AWS CloudTrail, GuardDuty findings, and Detective.
  + Forensic investigation references, integrating with services like AWS Partner forensic tools or AWS Marketplace IR tools.

**Roles & Responsibilities**

* Define incident response roles using AWS IAM roles, Okta groups, or AWS SSO assignments.
* Assign security team members as Incident Response Coordinators in AWS Systems Manager OpsCenter or Jira/AWS integrated platforms.

**Incident Detection & Reporting**

* Enable AWS GuardDuty, CloudTrail, AWS Config, and Security Hub for continuous monitoring.
* Integrate findings into Amazon EventBridge for alerting and AWS Lambda for auto-response.
* Use AWS SNS or ServiceNow/AWS Chatbot for incident notification workflows.

**Communication Processes**

* Develop automated incident communication templates via AWS SES, SNS, or third-party tools (e.g., PagerDuty).
* Store notification logs in S3, with encryption and access logging enabled.
* Ensure plain language breach notification is templated and managed by compliance/legal teams.

**Assignment of Responsibilities**

* Document decision-making roles and responsibilities in Runbooks using AWS Systems Manager Documents (SSM Documents).
* Assign tagged owners to all critical resources using AWS Tags and track via AWS Resource Groups.

**Incident Program Components:**

* Feedback to reporters : Use AWS Service Catalog AppRegistry + custom feedback Lambda + SES/SNS
* Tools for reporting: AWS Security Hub insights, OpsCenter, Jira integration
* References to sanctions: Documented in your org’s incident policy, reviewed via AWS Audit Manager.
* Plain language communication: Templates in SES, WorkMail, or third-party integrations.
* Automated workflows: Use AWS Step Functions, Lambda, EventBridge and SSM Automation documents.

**Possible Evidence to Collect:**

* Incident Response Policy and classification matrix (PDF/Markdown)
* CloudTrail & GuardDuty finding logs showing detection of incidents
* IAM role assignments for IR coordinators
* SSM Automation workflows for incident handling
* SNS/SES messages for incident notifications
* Screenshots of OpsCenter entries or JIRA tickets with timestamps

---

**HITRUST Requirement – Breach Notification & Reporting Protocol**

**Control ID:** 11.a Reporting Information Security Events  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.404 – Notification to Individuals; 45 CFR §164.406 – Notification to Media

**Control Objective:**

Ensure timely and complete breach reporting and communication in compliance with regulatory timelines and organizational policies using AWS services and integrations.

**Technical & Operational Implementation:**

#### Timely Notification:

* Automation of Timelines:  
  Use AWS Step Functions and Amazon EventBridge rules to track incident detection timestamps and trigger workflows to ensure breach notification occurs within regulatory windows (e.g., 60 days or 30 days for law enforcement delays).
* Timestamp Logging:  
  Capture event discovery timestamps using AWS CloudTrail and GuardDuty, storing them in an auditable Amazon DynamoDB or Amazon RDS table.

#### Incident Report Contents:

* Description of the event - Collected from CloudTrail, GuardDuty, and AWS Config logs.
* Date of the breach - Timestamp from initial GuardDuty/CloudTrail findings
* Date of discovery - Logged automatically in SIEM (e.g., OpenSearch, Splunk) and OpsCenter
* Types of information involved - Assessed with Amazon Macie (for PHI/PII detection in S3)
* Recommended steps for affected entities - Stored in pre-defined IRP templates in S3, triggered via Step Functions
* Remediation steps taken - Tracked via AWS Systems Manager Automation documents or manual notes in OpsCenter
* Point of contact information - Maintained in incident response playbooks stored in S3 or AWS Service Catalog AppRegistry metadata.

#### Communication Workflow:

* Stakeholder Notification:  
  Use Amazon SES or SNS for automated email/text notifications to internal and external stakeholders, including law enforcement, customers, or regulators.
* Incident Dashboards & Evidence:  
  Present incident summaries via AWS QuickSight dashboards or Confluence/JIRA integrations, with links to raw findings and mitigation evidence.

**Possible Evidence to Collect:**

* Notification logs from Amazon SNS/SES
* Incident report template filled with real incident data (hosted in S3 or Confluence)
* CloudTrail logs showing timestamps of discovery
* GuardDuty or Macie findings indicating information involved
* Step Functions execution history showing breach response flow
* Email headers confirming breach report was sent within 60 days
* Evidence of communications reviewed by legal/compliance

---

**HITRUST Requirement – Incident Reporting Awareness & Contact Availability**

**Control ID:** 11.a Reporting Information Security Events  
**Control Type:** Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(5)(i) – Security Awareness and Training

**Control Objective:**

Ensure that all employees, contractors, and third-party users are trained to promptly recognize and report security incidents, and that points of contact are clearly documented and accessible.

**Technical & Operational Implementation in AWS:**

Mandatory Incident Response Training:  
AWS customers should integrate IR training into onboarding and recurring security awareness programs. This can be managed via:

* AWS IAM Identity Center (fka AWS SSO) to group users by role (employee, contractor, third-party) and assign training requirements based on group membership.
* Tracking training completion using integrations between AWS SSO and third-party LMS tools (e.g., KnowBe4, Skillsoft, SAP Litmos).
* Training content may include IR workflows involving AWS services like CloudTrail, GuardDuty, and Security Hub, ensuring practical awareness.

Responsibility to Report Security Events:  
Define policies and include training on:

* Recognizing GuardDuty findings.
* Using AWS Systems Manager OpsCenter or AWS Support to initiate incident reports.
* Triggering internal alerting systems integrated with Amazon SNS or Slack/MS Teams for real-time escalation.

Documented Procedures & Points of Contact:

* Maintain a published IR policy in a shared location such as AWS WorkDocs, Confluence, or S3 bucket with access controls.
* Use Amazon Service Catalog AppRegistry or AWS Resource Tags to link systems with responsible IR team contacts.
* Provide clear escalation paths in documentation used during AWS Audit Manager reviews.

Availability of Contact Information:

* Host the security incident response contact details in a central repository accessible to all users (e.g., internal Confluence, S3-hosted HTML page).
* Restrict unauthorized access using S3 Bucket Policies, CloudFront signed URLs, or WorkDocs permissions.
* Include the contacts in AWS Security Hub custom actions (e.g., “Notify IR Team”).

**Possible Evidence to Collect:**

* Training logs showing incident response module completions by employees, contractors, and third-party users.
* Screenshot or access log showing the published IR contact page.
* Copies of IR policy documents with procedures and contact lists.
* IAM policy evidence showing role-based access to IR documentation.

---

**HITRUST Requirement – Formal Information Security Event Reporting**

**Control ID:** 11.a Reporting Information Security Events  
**Control Type:** Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**

Establish clear, timely, and structured procedures for detecting, reporting, escalating, and responding to information security events, including required notifications to stakeholders, while enabling all personnel to report issues without fear of retaliation.

**Technical & Operational Implementation in AWS:**

#### Establishing Procedures & Policy Direction:

* Define a centralized Incident Response Plan (IRP) and host it in a version-controlled repository (e.g., AWS CodeCommit, Confluence).
* Use AWS Organizations Service Control Policies (SCPs) and AWS IAM permissions boundaries to enforce preventative guardrails and responsibilities per role.

#### Incident Reporting Workflow:

* Automate detection of anomalies via:

  + Amazon GuardDuty for threat detection.
  + AWS CloudTrail for audit logging and tracking unauthorized or suspicious API activity.
  + AWS Security Hub for centralized alert aggregation and prioritization.
* Set Amazon EventBridge rules or AWS Lambda triggers to initiate response playbooks (e.g., isolation, notification).

#### Timeliness and Response Coordination:

* Use AWS Systems Manager OpsCenter or AWS Incident Manager (within AWS Systems Manager) to document:

  + Time of report
  + Assigned personnel
  + Escalation steps
* Integrate with AWS ChatOps tools like Slack or Amazon Chime for time-stamped updates during incident response.

#### Notification Mechanisms:

* Define communication protocols using Amazon SNS to notify:

  + Internal stakeholders (security, legal, compliance teams)
  + External stakeholders (vendors, regulators, affected clients)
  + Law enforcement or CERT teams if applicable

#### Reporting Channels & Anonymity:

* Provide a confidential whistleblower channel (e.g., third-party form integrated with AWS API Gateway + Lambda) to allow anonymous reporting.
* Ensure IAM permissions on this channel enforce anonymity and protect whistleblower identity.

#### Policy Communication & Training:

* Include the IRP and breach notification policy in security awareness training.
* Store signed acknowledgement receipts in AWS WorkDocs or HR tools integrated via AWS SSO.
* Conduct regular tabletop exercises using AWS Well-Architected Security Lens or incident simulations.

**Possible Evidence to Collect:**

* IRP document with version history.
* GuardDuty or Security Hub alerts showing event correlation.
* IAM policies showing defined permissions for incident responders and system administrators.
* OpsCenter incident records with response timelines.
* SNS topic subscription and message history for alert notifications.
* Screenshots or logs from the anonymous reporting mechanism.
* Communication templates for regulatory breach notifications.
* Training logs or attestation receipts from AWS-integrated LMS solutions.

---

**HITRUST Requirement – Insider Threat Program**

**Control ID:** 11.a Reporting Information Security Events  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(D) – Information System Activity Review; 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**

Establish a formal insider threat program with multidisciplinary participation to detect, respond to, and mitigate risks posed by internal actors with access to sensitive systems and data in AWS environments.

**Technical & Operational Implementation in AWS:**

#### Cross-Disciplinary Insider Threat Team Formation:

* Assemble a response team comprising security, HR, legal, compliance, and IT leads.
* Define roles and responsibilities in the Incident Response Plan (IRP) stored in version-controlled systems like AWS CodeCommit or integrated platforms like Confluence.

#### Insider Threat Detection:

* Enable AWS CloudTrail to log all management API activity across accounts.
* Use Amazon GuardDuty and AWS Security Hub to detect unusual behavior like privilege escalation, disabled logging, or unusual data access patterns.
* Integrate Amazon Detective for contextual investigation of suspected insider activity.

#### Behavioral Monitoring:

* Configure AWS CloudWatch and AWS Config to alert on policy violations or sudden changes in user behavior (e.g., changes to S3 bucket permissions, unauthorized SSH access).
* Use AWS Identity and Access Management Access Analyzer to audit permissions and identify excessive access rights.

#### Response and Containment:

* Automate incident response with AWS Systems Manager Incident Manager, triggering playbooks to isolate compromised IAM users or roles (e.g., attach deny SCPs or rotate credentials).
* Set up Amazon SNS alerts for high-severity findings to notify the insider threat response team immediately.

#### Collaboration and Evidence Collection:

* Store incident evidence (CloudTrail logs, IAM activity, screenshots) securely in Amazon S3 with Object Lock to prevent tampering.
* Use AWS Audit Manager to continuously assess insider threat control effectiveness and document improvements.

**Possible Evidence to Collect:**

* Insider Threat Response Policy and team charter.
* CloudTrail and GuardDuty logs showing detection and investigation of insider activity.
* IAM policy reviews and Access Analyzer reports with mitigation steps.
* Incident playbooks executed in AWS Systems Manager.
* Audit Manager reports showing continuous control assessments.
* Communications logs via SNS showing alerting of insider response team.
* Documentation of HR/legal/compliance collaboration in previous incidents.

---

**HITRUST Requirement – Cooperation with Legal Investigations**

**Control ID:** 11.a Reporting Information Security Events  
**Control Type:** Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(C) – Sanction Policy

**Control Objective:**

Ensure workforce accountability by enforcing disciplinary measures when employees or contractors fail to cooperate with federal or state investigations, especially regarding information security events within AWS-hosted systems.

**Technical & Operational Implementation in AWS:**

#### **Policy Enforcement:**

* Maintain an Acceptable Use and Sanctions Policy documented in your corporate GRC platform (e.g., Drata, Confluence).
* Policy includes a clause requiring full cooperation with legal investigations, referencing disciplinary actions for non-compliance.

#### **Security Logging & Cooperation Mechanism:**

* Enable AWS CloudTrail and AWS Config to log and track all relevant user activities across AWS accounts.
* Ensure CloudTrail logs are immutable via S3 Object Lock to serve as legal evidence.
* Store access records in a centralized logging service (e.g., CloudWatch Logs, third-party SIEM) for legal review.

#### **Incident Documentation:**

* For non-cooperation cases, document audit trails and management reviews using AWS Systems Manager OpsCenter or case tracking systems like Jira integrated with AWS.

#### **HR & Compliance Integration:**

* Integrate disciplinary workflows with identity providers (e.g., Okta, Azure AD) to suspend access of non-cooperative personnel.
* Involve HR and legal teams through shared evidence repositories, formalizing disciplinary action trails and timestamped decisions.

#### **Collaboration with Legal Authorities:**

* Ensure your AWS Acceptable Use Policy and Incident Response Playbooks reflect readiness to respond to law enforcement data requests under subpoenas or investigations.

**Possible Evidence to Collect:**

* Copy of Acceptable Use & Sanction Policy.
* Logs from CloudTrail or Config showing user activity (and tampering or non-cooperation indicators).
* Case notes or disciplinary documentation from HR systems or AWS OpsCenter.
* Audit Manager assessments demonstrating policy enforcement.
* Incident response records highlighting interaction with federal/state bodies and follow-up actions.

---

**HITRUST Requirement – IDS/IPS Event Reporting**

**Control ID:** 11.a Reporting Information Security Events  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(D) – Information System Activity Review; 45 CFR §164.312(b) – Audit Controls

**Control Objective:**

Ensure that intrusion detection and prevention alerts are actively leveraged to identify, report, and respond to potential information security events within AWS-hosted infrastructure.

**Technical & Operational Implementation in AWS:**

#### **Detection Tools:**

* Amazon GuardDuty acts as a managed IDS/IPS service by continuously monitoring for malicious activity and unauthorized behavior using AWS CloudTrail, VPC Flow Logs, and DNS logs.
* Integrate AWS Network Firewall and Amazon Inspector with Amazon CloudWatch to monitor for known attack patterns, network anomalies, or vulnerable resources.

#### **Alertin**g and Reporting:

* Configure GuardDuty to send real-time alerts to Amazon SNS, which can notify the security team or trigger automated workflows.
* Utilize AWS Security Hub to aggregate, normalize, and prioritize findings from GuardDuty, Inspector, and other sources.

#### Integration with SIEM:

* Route IDS/IPS logs and alerts to third-party SIEM platforms (e.g., Splunk, Sumo Logic) using Kinesis Firehose or CloudWatch Logs for correlation and incident reporting.
* Apply tagging or metadata classification on findings for context-aware incident triage.

#### Response Automation:

* Use AWS Lambda or AWS Systems Manager Automation to initiate response actions based on GuardDuty findings (e.g., isolate EC2 instances, revoke IAM roles).
* Maintain incident tracking and resolution history via AWS Security Hub Insights or integrated case management systems.

**Possible Evidence to Collect:**

* GuardDuty and Inspector configuration screenshots.
* Sample CloudWatch alarms or SNS notification trails for IDS/IPS alerts.
* SIEM logs showing security event reports triggered by AWS IDS/IPS services.
* Security Hub finding summaries and response documentation.
* Lambda or Systems Manager runbooks triggered by security alerts.

---

**HITRUST Requirement – Duress Alarm & High-Risk Alert Response**

**Control ID:** 11.a Reporting Information Security Events  
**Control Type:** Technical / Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(i) – Security Incident Procedures

**Control Objective:**

Establish mechanisms to immediately signal critical, high-risk security or personal safety incidents (analogous to duress alarms) and ensure rapid, context-aware response actions are taken in AWS environments.

**Technical & Operational Implementation in AWS:**

#### **Duress-like Signaling Mechanisms:**

* **Custom Alarms or Emergency Flags**: Configure AWS applications (e.g., web portals, admin dashboards) with a mechanism (e.g., panic button, help flag) to simulate a duress signal — such as triggering a silent notification or hidden API call.
* **AWS CloudWatch Alarms**: Set high-sensitivity thresholds for detecting unusual access patterns or forced access attempts (e.g., IAM role misuse, data exfiltration, failed login bursts).

#### **High-Risk Response Procedures:**

* Automation via AWS Lambda or Step Functions: On receiving a signal or alarm, automatically isolate affected resources (e.g., EC2 quarantine), revoke access tokens, or alert responders.
* Integration with Amazon SNS / EventBridge: Immediately notify designated response teams (SOC, management) through email, SMS, or ticketing systems like Jira or PagerDuty.

#### Security Escalation & Forensics:

* Enable AWS Config and AWS CloudTrail to track changes and collect evidence during incident response.
* Use AWS Security Hub Insights to prioritize duress-related security findings for fast triage.
* Implement a “break-glass” IAM policy reviewed regularly, with logging enabled, for emergency administrative access.

**Possible Evidence to Collect:**

* Alarm definitions in CloudWatch for high-risk indicators or manual trigger interfaces.
* SNS topic configurations and notifications tied to incident response.
* Lambda/Step Functions execution logs showing automated response to flagged events.
* Security Incident response policy referencing emergency procedures and duress scenarios.
* IAM policy versions or “break-glass” access logs reviewed and signed off by security officers.

---

**HITRUST Requirement – Incident-Based Information Security Assessment**

**Control ID:** 11.a Reporting Information Security Events  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**

Ensure incidents are reviewed through security assessments (fully or by sampling) to validate the effectiveness of implemented controls and to assess whether prior risk assessments remain accurate and relevant.

**Technical & Operational Implementation in AWS:**

#### Post-Incident Review Framework:

* Establish an Incident Review SOP that mandates either full or sampled post-incident assessments based on impact, frequency, or classification of the event.
* Use AWS Security Hub or third-party GRC platforms to track and assess control effectiveness linked to the incident (e.g., firewall policies, IAM role misconfiguration, logging gaps).

#### Assessment Mechanisms:

* CloudTrail & AWS Config Logs: Review for unauthorized actions or failures in enforcement of guardrails (e.g., SCPs, IAM Conditions).
* AWS Audit Manager: Automate evidence collection for mapped HITRUST controls to analyze gaps post-incident.
* Perform risk re-evaluation using findings from the incident, updating threat models or control configurations as needed (e.g., changing EC2 security group rules based on port scanning incident).

#### Sample-Based Assessment Triggers:

* Define criteria for sample review (e.g., 10% of all logged low-severity incidents per quarter).
* Use Amazon Athena queries or AWS QuickSight dashboards over centralized log repositories (S3, OpenSearch) to identify relevant incidents for sampling.

**Possible Evidence to Collect:**

* Post-incident reports showing control testing and effectiveness evaluations.
* Risk assessment update logs indicating changes based on incident learnings.
* Screenshots or logs from AWS Config or CloudTrail audits for affected resources.
* Audit Manager assessment results and change management records.
* GRC tool entries showing incident-linked HITRUST control reassessment.

---

**HITRUST Requirement – Reporting Mechanisms for Workforce Security Violations**

**Control ID:** 11.b Reporting Security Weaknesses  
**Control Type:** Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**

Ensure a user-friendly, accessible reporting mechanism is in place for all workforce members—including employees, contractors, and third-party users—to report incidents, security events, or policy violations in a timely manner.

**Technical & Operational Implementation in AWS:**

#### Incident and Violation Reporting Channels:

* Implement a dedicated AWS-hosted reporting portal or ticketing system (e.g., Jira, ServiceNow) with SSO integration via AWS IAM Identity Center (SSO) or external IdPs like Okta.
* Enable anonymous feedback or violation reporting forms using Amazon WorkDocs or Amazon Connect with privacy-focused configurations.

#### Policy Enforcement and Awareness:

* Distribute Acceptable Use Policies (AUP) and workforce rules via Amazon WorkDocs or your organization's internal portal.
* Include reporting procedures in mandatory AWS security awareness training modules via platforms like AWS Skill Builder or integrated LMS.

#### Automated Alerts and Routing:

* Configure AWS Lambda + SES/SNS to automatically route submitted reports to designated incident response teams.
* Use Amazon Connect or Chatbots for live or asynchronous reporting experiences.

#### Availability and Accessibility:

* Ensure high availability by hosting the reporting mechanism across multi-AZ architecture or via AWS Global Accelerator.
* Provide mobile and multilingual access using AWS Amplify and Amazon Translate.

**Possible Evidence to Collect:**

* Screenshots or URLs of reporting forms/portals available to workforce.
* Incident ticket logs showing time of report, type of violation, and response time.
* Training records with AUP acknowledgment and reporting awareness.
* Email or Slack notification examples showing incident report routing.
* Policies and communications demonstrating accessibility of reporting channels.

---

**HITRUST Requirement – Incident Handling Capability**  
**Control ID:** 11.c Responsibilities and Procedures  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(i) – Security Incident Procedures

**Control Objective:**  
Establish, document, and implement a structured incident response capability that ensures timely detection, containment, eradication, and recovery from security incidents in cloud environments, while aligning with corporate policies and vulnerability management activities.

**AWS Technical & Operational Implementation:**

Detection and Analysis:  
Use AWS GuardDuty, AWS Security Hub, and Amazon Detective to detect anomalies, suspicious activities, or known threats. Integrate findings with AWS Lambda or third-party SOAR tools for automated enrichment and triage.

Containment:  
Set up automated incident response playbooks using AWS Systems Manager Automation or EventBridge rules that isolate compromised resources (e.g., auto-remove EC2 instance from ELB, revoke session tokens via AWS IAM).

Eradication:  
Implement remediation actions through AWS Systems Manager Run Command, Patch Manager, and Lambda to remove malware, revoke compromised keys, or uninstall malicious software from EC2 instances or containers.

Recovery (Including PR and Reputation Management):  
Utilize AWS Backup to restore known-good configurations. Maintain predefined RTO/RPO. Use Amazon CloudFront or Route 53 with failover routing to minimize downtime. Communications may leverage Amazon Chime or integrations with PR management tools to coordinate public messaging.

Policy and Corporate Direction:  
Define an incident response policy document stored in AWS WorkDocs or Confluence and reference it across training and SOPs.

Roles and Responsibilities:  
Map responsibilities using AWS IAM roles and assign incident response tasks in ticketing tools (e.g., Jira) with role-based access control integrated with IAM Identity Center.

Business and Technical Procedures:  
Document runbooks and response playbooks (stored in S3 or version-controlled in AWS CodeCommit). Use AWS Systems Manager Documents (SSM Documents) for automation steps.

Communication:  
Use Amazon SNS or AWS Chatbot to notify stakeholders (e.g., security team Slack channel, email, or SMS). Route findings using EventBridge.

Reporting and Retention:  
Log incidents in AWS Security Hub Insights or third-party GRC tools. Retain all logs using AWS CloudTrail (set retention per compliance) and export long-term records to Amazon S3 with lifecycle policies.

Vulnerability Management Integration:  
Tie incident handling into AWS Inspector for continuous vulnerability assessment and GuardDuty for IDS. Link alerts to internal IDS/IPS tools or SIEMs via Kinesis Data Firehose.

**Possible Evidence to Collect:**  
– Sample GuardDuty/Inspector findings  
– Incident response runbooks  
– Screenshots of AWS Systems Manager Automation execution  
– IAM role and responsibility matrix  
– Communication logs from SNS or Slack integrations  
– Evidence of backup restoration and event correlation from AWS tools

---

**HITRUST Requirement: Regular incident response capability tests and/or exercises**

**Control ID:** 11.c Responsibilities and Procedures  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**  
Ensure the incident response (IR) plan is validated through regular testing or exercises to verify readiness and improve effectiveness in a cloud-native environment.

**AWS Technical & Operational Implementation:**

* **IR Simulation and Tabletop Exercises:**  
  Conduct regular incident response tabletop exercises involving AWS stakeholders, simulating scenarios like data exfiltration, credential leakage, or GuardDuty alerts. Use AWS Well-Architected Security Pillar IR scenarios as baselines.
* **Automated Runbook Testing:**  
  Use AWS Systems Manager Automation documents to simulate incident response workflows and validate response logic and actions (e.g., isolate an EC2 instance, rotate IAM keys).
* **GuardDuty and Security Hub Integration:**  
  Trigger mock alerts in AWS GuardDuty or ingest simulated findings via AWS Security Hub custom actions to test alert routing and remediation automation (e.g., via EventBridge and Lambda).
* **Incident Response Plan Reviews:**  
  Store IR plans in AWS WorkDocs or Confluence and review them periodically for cloud-specific threats. Maintain version control using AWS CodeCommit or GitHub.
* **SIEM/Alerting Pipeline Test:**  
  Validate that alerts generated by GuardDuty, Inspector, CloudTrail, and Config are flowing into a centralized SIEM (e.g., Splunk, Elastic, or OpenSearch) and that on-call teams are receiving notifications via Amazon SNS, PagerDuty, or AWS Chatbot.

**Evidence to Collect:**

* Meeting minutes or screenshots of completed IR tabletop exercises
* AWS Systems Manager Automation execution logs
* Sample simulated GuardDuty/Inspector findings
* Change history or commit log of updated IR plans
* Output from Amazon CloudWatch or Security Hub showing mock alert ingestion
* Documentation of lessons learned and plan updates following tests

---

**HITRUST Requirement: The incident management plan is reviewed and updated annually**

**Control ID:** 11.c Responsibilities and Procedures  
**Control Type:** Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**  
Ensure the organization maintains an up-to-date incident response (IR) plan that reflects changes in the AWS environment, services, threat landscape, and organizational processes.

**AWS Technical & Operational Implementation:**

* **Annual Review Cadence:**  
  Establish a defined process to review the AWS-specific incident management plan at least annually. Ensure updates account for changes in AWS services (e.g., introduction of new security services like Amazon Detective or changes in IAM).
* **Version Control & Change Tracking:**  
  Store the IR plan in a version-controlled repository (e.g., AWS CodeCommit, GitHub, or Confluence with audit logging) to track updates and ensure accountability for changes.
* **Service Inventory Alignment:**  
  Ensure the plan references current AWS services in use (e.g., EC2, RDS, S3, Lambda) and logging configurations (e.g., CloudTrail, VPC Flow Logs, Config).
* **Stakeholder Review:**  
  Involve Security, DevOps, Compliance, and Incident Response teams in the annual review cycle to confirm relevance across all environments (dev, staging, prod).
* **AWS Artifact Usage:**  
  Use AWS Artifact to download current AWS SOC/ISO certifications and ensure third-party expectations (e.g., for shared responsibility) are reflected in the IR plan.

**Evidence to Collect:**

* Record of annual review (meeting invite, notes, sign-off log)
* Latest version of the incident management plan with revision date
* Version history from Confluence, Git, or SharePoint
* Acknowledgment from stakeholders involved in the review
* Comparison summary of changes (e.g., services added, procedures modified)

---

**HITRUST Requirement: Audit trails and evidence collection post incident**   
**Control ID:** 11.c Responsibilities and Procedures

**Control Objective:**  
Ensure forensic readiness, secure evidence handling, incident response, and timely recovery actions are performed during and after a security event in the AWS environment.

**AWS Technical & Operational Implementation:**

1. Forensic Readiness & Evidence Collection

   * Utilize AWS CloudTrail, AWS Config, and Amazon GuardDuty to collect logs and forensic evidence.
   * Store logs in immutable storage (e.g., S3 with Object Lock) for regulatory/legal investigations.
   * Use AWS Security Hub to consolidate findings and escalate incidents.
2. Controlled Recovery Actions

   * Implement AWS Systems Manager automation documents to execute controlled recovery playbooks.
   * Require approval workflows using AWS Systems Manager Change Manager before initiating recovery scripts.
3. Access Control to Live Systems

   * Enforce strict IAM roles and attribute-based access control (ABAC) to ensure only authorized personnel can access live incident response environments.
4. Documentation of Emergency Actions

   * Use AWS Systems Manager OpsCenter or ticketing integration (e.g., with Jira or ServiceNow) to log and track each emergency action.
5. Containment and Restoration

   * Use Amazon Inspector for vulnerability detection and AWS WAF/Shield for real-time containment of external threats.
   * Trigger automated rollback or snapshot restore using Amazon EC2 AMIs, EBS snapshots, or RDS point-in-time recovery.
6. Incident Reporting & Management Review

   * Establish an AWS SNS notification pipeline that alerts management teams on incident triggers.
   * Integrate AWS ChatOps (e.g., with Slack) or AWS Security Hub findings into ticketing tools with management oversight.
7. Verification of Integrity

   * Validate system integrity using AWS Config rules, CloudTrail event monitoring, and runtime monitoring from tools like Amazon Detective or third-party agents (e.g., Wiz, CrowdStrike).
8. Stakeholder Notification

   * Use AWS Simple Email Service (SES) or SNS topics to notify internal/external stakeholders when incidents are resolved and environments are confirmed secure.

**Evidence to Collect:**

* CloudTrail & GuardDuty logs showing event traces
* Evidence of S3 Object Lock usage for forensic data
* Systems Manager OpsItem or ticketing record with documented emergency actions
* IAM audit showing least privilege access to IR environments
* Notifications or alerts sent to stakeholders via SNS or email logs
* Screenshot or record of post-incident review or management sign-off

---

**HITRUST Requirement: Incident logs are maintained and reported to appropriate authorities**   
**Control ID:** 11.c Responsibilities and Procedures

**Control Objective:**  
Ensure all security incidents are logged, retained, and reported to regulatory authorities in compliance with legal or contractual obligations.

**Technical & Operational Implementation:**

1. Incident Logging and Maintenance

   * Enable AWS CloudTrail across all AWS accounts to log API activity for incident detection and investigation.
   * Use AWS Security Hub, Amazon GuardDuty, and Amazon Detective to identify, analyze, and record security-related findings.
   * Store logs in Amazon S3 with Object Lock to meet retention requirements and prevent tampering.
   * Use AWS Config to maintain a history of configuration changes and compliance drifts tied to security events.
2. Annual Reporting to Authorities

   * Maintain incident reports in a central repository (e.g., Amazon S3, AWS Backup Vaults) tagged with metadata for filtering and export.
   * Generate annual reports from logs and incident management tools using Amazon Athena or AWS Glue for querying logs and building datasets.
   * Share reports securely with regulatory bodies using AWS Transfer Family (for SFTP) or pre-signed S3 URLs with time-limited access.

**Evidence to Collect:**

* CloudTrail logs of incident events (e.g., `DeleteBucket`, `AuthorizeSecurityGroupIngress`)
* Security Hub or GuardDuty findings export logs
* Incident tracking or ticketing records from AWS Systems Manager OpsCenter
* Annual incident report files (PDF or CSV) stored in S3 with access logs showing export or sharing
* IAM roles and access logs verifying only authorized personnel accessed incident logs
* Record of submission (e.g., email confirmation or signed acknowledgment from regulator)

---

**HITRUST Requirement: IRP is org wide accessible and reviewed regularly by responsible parties**  
**Control ID:** 11.c Responsibilities and Procedures

**Control Objective:**  
Ensure that incident response policies are effectively communicated to relevant stakeholders and regularly reviewed to maintain effectiveness.

**Technical & Operational Implementation:**

1. Policy Dissemination

   * AWS Organizations: Use Service Control Policies (SCPs) to enforce baseline security behavior across accounts, aligned with incident response expectations.
   * AWS IAM: Attach IAM policies and permission boundaries that reflect incident response responsibilities and ensure role-based access control for incident-related tools.
   * Disseminate incident response policies and runbooks via internal portals (e.g., Confluence, SharePoint, or AWS WorkDocs) and link them within AWS Systems Manager Runbooks, Documents (SSM Docs), and Incident Manager Response Plans.
2. Policy Review and Maintenance

   * Use AWS Systems Manager Automation Documents or AWS Config Rules to remind stakeholders to review and update incident response documentation periodically (e.g., annually or biannually).
   * Maintain version-controlled policies in repositories like AWS CodeCommit or GitHub to track changes, reviews, and approvals.
   * Leverage AWS Artifact or third-party GRC tools to collect, store, and track policy acknowledgment and updates as part of compliance evidence.

**Evidence to Collect:**

* Most recent version of the incident response policy, with dissemination method and acknowledgment tracking (e.g., signed PDF or LMS confirmation).
* Change history or git logs showing version updates and reviewer comments.
* Config rule or automation logs that document policy review schedule and task completion.
* Proof of stakeholder communication, such as email distribution, Slack notifications, or SSM Automation execution logs.

---

**HITRUST Requirement – Annual Testing and Cross-Functional Review of Incident Response Capability**

**Control ID:** 11.c Responsibilities and Procedures  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**

Ensure that the organization regularly tests and evaluates its incident response capabilities—including cross-functional coordination, simulations, and continuous improvement efforts—to validate effectiveness and enhance preparedness against security threats.

**Technical & Operational Implementation:**

* Scheduled IR Testing & Simulation  
  Organizations can leverage AWS Systems Manager Incident Manager and AWS Fault Injection Simulator (FIS) to simulate real-world incident scenarios at least annually. Testing scripts and SSM automation documents can be executed to validate preparedness across systems.
* After-Action Reporting  
  Results from incident exercises are documented in tools like AWS WorkDocs, AWS S3, or integrated GRC platforms. Reports include response gaps, timelines, affected components, and recommendations. These documents feed continuous improvement loops.
* Team Involvement and Training  
  Personnel designated in the AWS IAM Identity Center (or Okta integration) are mapped to incident response roles and included in periodic simulation exercises. Responsibilities and threat awareness are tracked through acknowledgment workflows and AWS CloudTrail logs.
* Cross-Functional Coordination  
  Integrate AWS Chatbot, SNS, and CloudWatch Alarms with collaboration platforms like Slack or Teams to conduct live coordination during tests. Involvement from PR, Legal, and Business Continuity teams is tracked through meeting logs, SIEM alerts, or ServiceNow tickets.

**Evidence to Collect:**

* IR simulation runbooks and logs from AWS Systems Manager / FIS
* After-action reports showing review and remediation plans
* IAM role and identity assignments to incident response personnel
* Meeting invites, task completion records, or SIEM logs demonstrating cross-departmental participation

---

**HITRUST Requirement – Formal Incident Response Program**

**Control ID:** 11.c Responsibilities and Procedures  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**

Establish and maintain a structured incident response program with defined phases and preparation for various incident types, ensuring root cause analysis, containment, and corrective action to prevent recurrence.

**Technical & Operational Implementation:**

* Defined Phases and Preparation  
  AWS recommends adopting the NIST-based incident lifecycle: Preparation, Detection & Analysis, Containment, Eradication, Recovery, and Post-Incident Activities. These phases are embedded in workflows using AWS Systems Manager Incident Manager.
* Incident Type Coverage  
  AWS services such as GuardDuty, AWS Shield, Macie, and AWS WAF help detect and mitigate various threats, including denial-of-service attacks, data exposure, identity misuse, and system abuse. Logs from CloudTrail, Config, and VPC Flow Logs help with analysis.
* Root Cause Analysis and Containment  
  Use AWS Detective for investigating incidents, identifying root cause, and mapping user/resource activity over time. Containment strategies may involve security group quarantine, IAM role revocation, or auto-remediation with Lambda.
* Increased Monitoring  
  Enhance monitoring using Amazon CloudWatch, Security Hub, and SNS to escalate anomalies. Set up custom metrics for unusual system behavior and apply real-time alerts to the response team.
* Corrective Actions and Prevention  
  Apply post-incident automation to enforce preventive controls using AWS Config Rules, Service Control Policies (SCPs), or Infrastructure as Code (IaC) updates through AWS CodePipeline. Use after-action reports and continuous tuning of GuardDuty/Macie findings for resilience.

**Evidence to Collect:**

* Incident runbooks and postmortem reports from Incident Manager
* IAM or network policy changes following incidents
* Automated workflow logs (SSM, Lambda)
* Config rule evaluations showing enforcement of corrective controls
* CloudTrail evidence of containment, recovery, and follow-up actions

---

**HITRUST Requirement – Formal Management of Incident Responses**

**Control ID:** 11.c Responsibilities and Procedures  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**

Ensure all incident responses are formally managed, evidence is collected promptly, escalation and forensic activities are carried out as needed, and all actions are logged, communicated, and closed in a structured and traceable manner.

**Technical & Operational Implementation:**

* Formal Incident Handling  
  Use AWS Systems Manager Incident Manager to initiate and track incidents with predefined runbooks, escalation paths, and timelines. Each incident is treated as a formal event with status updates and closure.
* Evidence Collection  
  Enable AWS CloudTrail, AWS Config, and VPC Flow Logs for automatic log generation across all services. These serve as evidence trails immediately available post-incident.
* Forensic Analysis  
  Use Amazon Detective for forensic-style timeline analysis of user and resource activity. Findings from GuardDuty and Security Hub support deeper investigations.
* Escalation Procedures  
  Configure Incident Manager escalation plans to alert specific teams via email, SMS, or chat integrations (e.g., Slack) based on incident severity and SLA rules.
* Logging Response Activities  
  All actions within the AWS environment are logged through CloudTrail, Config, and AWS Systems Manager Automation. Responses can be logged as part of runbook steps or integrated via custom Lambda functions.
* Communication of Incident Details  
  Use SNS Topics or Chime/Slack integrations with Incident Manager to notify internal/external stakeholders. Custom Lambda functions can redact and forward sanitized summaries when needed.
* Addressing Contributing Security Weaknesses  
  Identified root causes can trigger remediation actions via AWS Config Rules, Security Hub automation, or Lambda scripts to correct misconfigurations or enforce best practices.
* Formal Closure and Documentation  
  AWS Incident Manager allows for documentation of resolution steps, lessons learned, and root cause summaries. Use AWS CloudWatch dashboards or QuickSight to visualize incident metrics over time.

**Evidence to Collect:**

* Incident timelines and logs from AWS Incident Manager
* Detective reports showing event chain and analysis
* CloudTrail logs, Config snapshots, and VPC flow logs
* Evidence of alerts/escalation via SNS or ticketing integrations
* Closure notes and corrective action records from Incident Manager or Confluence/Jira integrations

---

**HITRUST Requirement – Designated Point of Contact for Incident Response**  
Control ID: 11.c Responsibilities and Procedures  
Control Type: Administrative  
Control Level: Implementation  
HIPAA Mapping: 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**  
Ensure that a clearly assigned and authorized point of contact is responsible for managing and coordinating all aspects of the incident response process, including information sharing and execution of response actions.

**Technical & Operational Implementation:**  
In AWS environments, the single point of contact (POC) for incident response is often established through organizational policies and integrated into automated workflows. AWS Systems Manager Incident Manager supports defining an incident response plan with designated contacts assigned roles and escalation responsibilities. The incident commander (assigned role) can be granted IAM permissions to coordinate across services, invoke automation documents (runbooks), and manage communication channels.

Integration with Amazon SNS or third-party tools like PagerDuty ensures that the POC receives immediate alerts. The POC can also use AWS Chatbot or AWS Console to direct actions in real time. Access and authority are enforced through scoped IAM roles and resource policies, ensuring that the POC has sufficient access for full incident lifecycle coordination.

**Evidence to Collect**:

* Incident Manager contact roster showing assigned POC
* IAM role and policy granting authority to execute remediation actions
* Incident timelines showing decisions/actions by designated POC
* Communication records from SNS or external integrations (Slack, email, etc.)
* Policy documents defining POC responsibilities and authority scope

---

**HITRUST Requirement – Automated Incident Response Information Support**  
**Control ID:** 11.c Responsibilities and Procedures  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**  
Leverage automation to enhance the availability, accessibility, and reliability of incident response-related information and resources across the organization.

**Technical & Operational Implementation:**  
AWS provides multiple automated mechanisms to support real-time access to incident response data and coordination tools:

* **AWS Systems Manager Incident Manager** automates incident tracking, resolution workflows, and contact notifications. Playbooks and runbooks are stored centrally and triggered automatically during incident events.
* **AWS Security Hub** consolidates and aggregates findings across AWS services and third-party tools to ensure security incidents and response data are continuously available.
* **Amazon CloudWatch Dashboards** provide real-time operational visibility into security incidents and system health metrics through automated metric collection and visualization.
* **AWS Chatbot** enables automated alerts and interaction with AWS services directly in communication tools like Slack or Microsoft Teams, improving availability of information to responders.
* **EventBridge rules** can be configured to detect specific security findings or operational events and initiate pre-defined automated actions (e.g., triggering Lambda functions or invoking SSM Automation documents).
* **AWS Config + Config Rules** continuously assess AWS resource configurations and alert teams when changes may affect security posture, providing timely data for incident handling.

**Evidence to Collect:**

* Configuration of Incident Manager response plans and automation documents
* Security Hub findings dashboard and EventBridge forwarding logic
* CloudWatch dashboards configured for incident-related metrics
* Records of automated Chatbot alerts and communication logs
* Config rule triggers and remediation workflows

---

**HITRUST Requirement – External Reporting and Communication During Incidents**  
**Control ID:** 11.c Responsibilities and Procedures  
**Control Type:** Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**  
Ensure timely and compliant communication of incident details to designated authorities and external stakeholders, in accordance with legal, regulatory, and contractual obligations.

**Technical & Operational Implementation:**

* **AWS Systems Manager Incident Manager** enables automated workflows for incident escalation, documentation, and communication. Contact plans can include external stakeholders if required by contract or law.
* **AWS Audit Manager** supports documentation of compliance with external reporting requirements, ensuring incident response aligns with specific standards (e.g., HIPAA, FedRAMP, NIST 800-53).
* **Amazon CloudWatch Events & EventBridge** can be configured to trigger alerts or notifications to compliance teams when specific security events occur that may require external reporting.
* **AWS CloudTrail** maintains logs of all API activity across AWS services to support forensic analysis and reporting.
* Organizations can integrate AWS with third-party SIEM tools (e.g., Splunk, IBM QRadar) or national threat-sharing platforms (e.g., US-CERT, CISA AIS) for external reporting and coordination.
* **AWS Artifact** provides access to compliance documentation and attestation letters that can support external communications, such as inquiries from auditors or regulators.

**Evidence to Collect:**

* Incident response policies referencing external communication channels and timelines
* Configured contact plans and escalation chains in AWS Incident Manager
* CloudTrail logs demonstrating incident traceability
* Notification and reporting evidence via EventBridge rules and email/Slack integration
* Integration records with third-party tools or platforms like CISA AIS or FedRAMP

---

**HITRUST Requirement – Continuous Improvement Through Incident Evaluation**  
**Control ID:** 11.d Learning from Information Security Incidents  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**  
Leverage insights gained from security incident evaluations to identify trends, assess recurring threats, and enhance the organization’s incident response and recovery processes.

**Technical & Operational Implementation:**

* AWS Security Hub aggregates and prioritizes findings across accounts and services. Insights can highlight recurring findings across time, enabling identification of repeated or high-impact incidents.
* Amazon Detective helps analyze historical security event patterns, supporting root cause identification and recurrence analysis.
* AWS Systems Manager Incident Manager allows teams to log incident retrospectives and attach corrective actions for future preparedness.
* AWS CloudWatch Logs Insights enables queries across incident logs to detect repeat events or correlated patterns.
* AWS Config continuously evaluates resource configurations and changes, helping to determine root causes or identify insecure trends.
* Organizations can automate updates to incident playbooks in AWS Systems Manager Documents (SSM Documents) based on lessons learned.

**Evidence to Collect:**

* Incident postmortem or after-action reports in AWS Incident Manager
* Security Hub insight trends and suppressed findings analysis
* Amazon Detective investigations showing repeated IOCs or root causes
* Updated incident response playbooks or response automation scripts
* Logs of improvement actions taken post-evaluation

---

**HITRUST Requirement – Continuous Improvement Through Lessons Learned**  
**Control ID:** 11.d Learning from Information Security Incidents  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(6)(ii) – Response and Reporting

**Control Objective:**  
Ensure the organization integrates lessons learned from incident response activities and industry developments into procedures, training, and simulations to continuously strengthen its security posture.

**Technical & Operational Implementation:**

* AWS Systems Manager Incident Manager supports post-incident analysis via post-incident reports, allowing documentation of findings and recommendations for improvement.
* AWS Security Hub tracks recurring misconfigurations or threats and provides actionable insights that can drive updates to training and procedures.
* Amazon Detective helps reconstruct events for comprehensive analysis, aiding in identifying systemic weaknesses or procedural gaps.
* Use AWS CloudFormation or SSM Documents to version-control incident response workflows. Updates based on lessons learned can be deployed rapidly across environments.
* Training simulations can be improved using AWS IAM Access Analyzer and GuardDuty findings, helping build realistic test scenarios.
* Integration with AWS Lambda or CodePipeline enables automated updates to training environments or procedural documentation.

**Evidence to Collect:**

* Copies of completed after-action or post-incident review reports
* Documentation showing updates to incident response plans or SSM Documents
* Records of revised tabletop or hands-on training sessions reflecting updates
* Logs from AWS Systems Manager Automation or runbooks reflecting new procedures
* Evidence of updated Security Hub Insights or detection logic based on trends

---

**HITRUST Requirement – Coordination of Incident Handling with Contingency Planning**  
**Control ID:** 11.d Learning from Information Security Incidents  
**Control Type:** Administrative  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(7)(ii)(A) – Contingency Plan

**Control Objective:**  
Ensure incident handling processes are integrated with business continuity and disaster recovery planning to facilitate effective response, recovery, and system resilience.

**Technical & Operational Implementation:**

* Use AWS Resilience Hub to validate and continuously test recovery objectives (RTO/RPO), ensuring alignment between contingency plans and incident handling activities.
* Integrate AWS Systems Manager Incident Manager with AWS Backup, CloudEndure Disaster Recovery, and Elastic Disaster Recovery to automate recovery steps in response to incidents.
* Define escalation paths and contingency triggers in AWS Incident Manager Response Plans, ensuring they account for broader business continuity scenarios.
* Conduct joint tabletop exercises that simulate AWS-based incident scenarios alongside DR playbooks, validating both detection and recovery processes.
* Utilize AWS Organizations SCPs and AWS Config rules to enforce contingency-linked incident response control states, such as backup frequency or resource isolation.

**Evidence to Collect:**

* Response plans from AWS Systems Manager Incident Manager referencing disaster recovery tools or objectives
* Documentation of joint incident response and contingency testing exercises
* RTO/RPO mappings aligned with response plans in AWS Resilience Hub
* CloudWatch metrics and alarms used as triggers for failover or recovery mechanisms
* Records of cross-functional planning between incident response and DR stakeholders

---

**HITRUST Requirement – Legal Evidence Handling for Security Incidents**  
**Control ID:** 11.e Collection of Evidence  
**Control Type:** Administrative / Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(C) – Sanction Policy (indirectly supports investigation-related controls)

**Control Objective:**  
Ensure that evidence related to information security incidents is collected, preserved, and presented in a manner that supports potential legal proceedings and complies with applicable jurisdictional laws.

**Technical & Operational Implementation:**

* Evidence Collection:

  + Leverage AWS CloudTrail, AWS Config, and VPC Flow Logs to continuously record and retain user activity and network events that may serve as forensic evidence.
  + Enable AWS Security Hub and Amazon Detective for deep investigation and linkage of activity across AWS accounts and services.
* Evidence Retention:

  + Store logs and forensic data in Amazon S3 with Object Lock enabled in compliance mode to meet legal hold and retention requirements.
  + Apply AWS Backup and AWS KMS to ensure encrypted, centralized backup of evidence-related data for future legal reference.
* Evidence Presentation:

  + Use Amazon Athena or OpenSearch for querying logs and building timelines to support internal investigations and regulatory inquiries.
  + Export relevant logs or findings via secure mechanisms (e.g., AWS Snowball, AWS Transfer Family, or encrypted S3 sharing) to authorized legal or regulatory entities.

**Evidence to Collect:**

* CloudTrail logs with relevant activity trails
* Object Lock configuration showing immutable storage of evidence
* IAM roles/policies restricting access to evidence
* Chain-of-custody documentation from AWS Systems Manager or manual logs
* Athena queries and analysis reports supporting legal interpretation
* Retention schedules aligned with organizational legal requirements