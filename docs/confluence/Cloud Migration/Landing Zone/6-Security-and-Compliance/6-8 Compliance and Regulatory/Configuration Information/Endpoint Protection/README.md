# Endpoint Protection

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4989616724/Endpoint%20Protection

**Created by:** Shreya Singh on August 06, 2025  
**Last modified by:** Shreya Singh on August 06, 2025 at 10:54 PM

---

**HITRUST Requirement** – User Awareness of Equipment and Session Security  
Control ID: 01.g Unattended User Equipment  
Control Type: Administrative  
Control Level: Implementation  
HIPAA Mapping: 45 CFR §164.310(b) – Workstation Use; 45 CFR §164.310(c) – Workstation Security

**Control Objective**:  
Ensure all users are aware of their responsibilities for protecting unattended equipment, securing sessions, and preventing unauthorized access to information systems and physical devices.

**Technical & Operational Implementation:**

* Users accessing AWS resources (via AWS Management Console, CLI, or SDKs) should receive regular security awareness training that emphasizes secure workstation behavior and session management.
* Use AWS IAM Identity Center (formerly AWS SSO) session timeouts and idle session management to ensure that inactive sessions are automatically logged out after a defined period.
* Educate users to log off from AWS Console or use secure mechanisms like MFA-protected screen savers when temporarily leaving a device.
* AWS Systems Manager Session Manager logs all session activity for administrators accessing EC2 instances and ensures those sessions are properly terminated when no longer needed.
* Leverage AWS Config and AWS Security Hub to detect and alert on non-compliant configurations, such as disabled screen locks or improperly secured endpoints connected via VPN or AWS Workspaces.
* For physical devices, organizations using AWS WorkSpaces or AppStream should enforce group policies to require auto-lock after inactivity and enforce password authentication to resume activity.

**Potential Evidence to Collect**:

* Security awareness training materials covering workstation and session protection
* IAM Identity Center session timeout configurations
* Screenshots or configuration files showing auto-lock settings in AppStream or WorkSpaces
* Systems Manager Session Manager audit logs
* AWS Config rules enforcing session inactivity policies
* Internal policies on user responsibilities for equipment and terminal security

---

**HITRUST Requirement – Anti-Malware Controls and BYOD Management**  
**Control ID**: 09.j Controls Against Malicious Code  
**Control Type**: Technical  
**Control Level**: Implementation  
**HIPAA Mapping**: 45 CFR §164.308(a)(5)(ii)(B) – Protection from Malicious Software

**Control Objective**:  
Deploy, maintain, and manage anti-malware protections across user endpoints, servers, BYOD environments, and networks. Ensure timely updates, automated scanning, and appropriate defenses for environments where traditional antivirus is not feasible.

**Technical & Operational Implementation**:

* Anti-malware installation and updates:  
  Use Amazon Inspector and AWS Systems Manager Patch Manager to automate installation and updating of anti-malware tools on EC2 instances. Systems Manager State Manager can enforce the presence of endpoint protection software and check for version compliance.
* Regular scans and software reviews:  
  Use Amazon Inspector for continuous scanning of workloads for vulnerabilities and malware. Implement AWS Config rules to ensure unauthorized software is detected and removed where possible.
* Centralized anti-malware infrastructure:  
  Use AWS Systems Manager with a centralized patch and configuration management policy. Organizations may also integrate endpoint protection platforms like CrowdStrike, SentinelOne, or Trend Micro via AWS Marketplace with centralized update capabilities.
* Signature update verification:  
  Use AWS Systems Manager Compliance reports to validate that each managed instance has received and applied the latest updates, including anti-malware signature updates.
* Scanning files/media/email/web/removable devices:  
  In VDI or WorkSpaces environments, install third-party endpoint protection to scan email attachments, USB access, or file downloads. Use Amazon WorkMail and integrated malware scanning or partner solutions like Proofpoint or Mimecast for email malware filtering. Web traffic can be protected via AWS Network Firewall or AWS WAF integrated with reputation-based threat feeds.
* Multi-layered malware scanning :  
  Implement defense-in-depth using layered security:

  + At email gateway (e.g., Amazon WorkMail + email security tools)
  + At endpoint (e.g., AWS WorkSpaces + endpoint AV)
  + At the network level (e.g., AWS Network Firewall or Transit Gateway appliances)
* BYOD protection:  
  Enforce conditional access via AWS IAM Identity Center (formerly AWS SSO) integrated with device posture checks. Require MDM-enrolled and AV-protected BYOD devices before granting access to AWS-hosted resources via Amazon WorkSpaces Web or AppStream 2.0.
* Anti-malware for headless servers :  
  Where EC2 or container-based servers cannot run AV agents, deploy network-based malware detection via:

  + AWS Network Firewall with Suricata rule sets
  + Amazon VPC Traffic Mirroring with IDS/IPS appliances
  + Use Amazon GuardDuty with malware detection for runtime EC2 and container workloads

**Potential Evidence to Collect**:

* AWS Systems Manager compliance reports showing anti-malware versioning
* Inspector scan summaries
* Config rules enforcing installation of security agents
* Screenshots from endpoint protection platforms or MDM solutions
* Logs showing web/email/malware scans across layers
* BYOD access policy and technical enforcement mechanisms
* Documentation of compensating controls for headless server environments (e.g., VPC Traffic Mirroring or IDS tools)

---

**HITRUST Requirement – Augmented Endpoint Protection**  
**Control ID**: 09.j Controls Against Malicious Code  
**Control Type**: Technical  
**Control Level**: Implementation  
**HIPAA Mapping**: 45 CFR §164.308(a)(5)(ii)(B) – Protection from Malicious Software

**Control Objective**:  
Enhance traditional antivirus defenses by leveraging operating system–level protections and additional security solutions to mitigate exploitation of unknown vulnerabilities, particularly in commonly targeted applications.

**Technical & Operational Implementation**:

* OS-Level Protections:  
  For Amazon EC2 Windows/Linux instances or AWS WorkSpaces, enable built-in protections:

  + Windows Defender Exploit Guard or Windows Security for behavioral analysis and attack surface reduction.
  + SELinux or AppArmor on Linux for mandatory access controls.
* Amazon Inspector Runtime:  
  For container workloads (Amazon ECS, EKS, or Fargate), Inspector now offers runtime behavior analysis to detect software vulnerabilities and anomalous behaviors that traditional AV might miss.
* Amazon WorkSpaces/Web Access Protections:  
  Use WorkSpaces application restrictions to limit execution of Java applets, browser plug-ins, and legacy macros. Pair with endpoint protection tools that support behavior-based detection (e.g., CrowdStrike Falcon, Trend Micro Apex One).
* Hardening and Least Privilege:  
  Implement hardening baselines via AWS Systems Manager State Manager or AWS OpsWorks, using CIS Benchmarks or OS-native policies to restrict unnecessary features in commonly exploited applications (e.g., macros in MS Office).
* Browser and Plugin Protection:  
  Use cloud-based endpoint protection tools deployed via Systems Manager to monitor browser sessions and detect exploit chains. Limit use of vulnerable plugins via configuration management and enforce browser version patching.

**Potential** **Evidence to Collect**:

* Screenshots or logs showing OS-based security features enabled (e.g., Defender Exploit Guard, SELinux).
* Policies pushed via Systems Manager enforcing plugin or macro restrictions.
* Inspector runtime findings and remediation reports.
* Endpoint protection console logs demonstrating behavioral-based detections.
* BYOD/WorkSpaces configurations with restricted application usage and plugin controls.

---

**HITRUST Requirement – Centrally Managed Spam and Malware Protection**  
**Control ID**: 09.j Controls Against Malicious Code  
**Control Type**: Technical  
**Control Level**: Implementation  
**HIPAA Mapping**: 45 CFR §164.308(a)(5)(ii)(B) – Protection from Malicious Software

**Control Objective**:  
Ensure that anti-malware and spam protection systems are deployed at key network layers and across all endpoint types. Implement centralized management and configuration updates to mitigate risks from unsolicited messages and malware propagation.

**Technical & Operational Implementation**:

* Network Entry/Exit Points: Use AWS Network Firewall, Amazon Route 53 Resolver DNS Firewall, and email gateway integrations (e.g., SES + Proofpoint/Mimecast) to detect and block spam or phishing campaigns entering via public networks or inbound email.
* Endpoint & Server Protections: Deploy Amazon Inspector, AWS Systems Manager Patch Manager, and supported endpoint protection tools (e.g., CrowdStrike, Sophos, Trend Micro) to workstations, EC2 instances, and mobile workforce systems via SSM.
* Mobile Device Coverage: Enforce MDM solutions (e.g., Intune or MobileIron) integrated with AWS WorkSpaces or VPN solutions to extend protections to BYOD and mobile endpoints accessing the AWS environment.
* Spam Filtering Coverage:  
  Apply spam/malware filters at:

  + Email: via Amazon WorkMail, Amazon SES integrations, or third-party MX filtering.
  + Web: integrate secure DNS filtering tools.
  + Cloud-native HTTP/HTTPS filtering through secure proxies or NGFWs.
* Vulnerability-Driven Exploit Mitigation: Use Amazon Inspector, AWS Security Hub, and GuardDuty to detect exploit attempts delivered via malware, phishing links, or malicious file attachments.
* Centralized Management: Use AWS Systems Manager to push security configurations and coordinate update schedules. Integrate with vendor dashboards (e.g., Falcon Console, Defender ATP) for centralized threat and spam policy management.
* Automated Signature Updates: Validate and automate spam/malware detection signatures and engine updates using vendor APIs or SSM automation documents triggered by release notifications or regular patching cadences.

**Evidence to Collect**:

* Screenshots or reports from spam filtering tools configured on mail gateways or SES.
* Endpoint protection update logs and dashboard status across EC2 or WorkSpaces.
* Systems Manager automation documents enforcing spam/malware protection policies.
* Inspector and GuardDuty findings showing detection of malicious attachments or exploits.

---

**HITRUST Requirement – Critical System File Scanning Frequency**  
**Control ID**: 09.j Controls Against Malicious Code  
**Control Type**: Technical  
**Control Level**: Implementation  
**HIPAA Mapping**: 45 CFR §164.308(a)(1)(ii)(A) – Risk Analysis (in context of malware detection and system integrity)

**Control Objective**:  
Ensure that critical system files are regularly scanned for integrity and potential compromise, especially at boot time and at a defined recurring interval (e.g., every 12 hours) to detect and respond to unauthorized changes or malicious modifications.

**Technical & Operational Implementation**:

* **Boot-Time File Scans**:  
  Use Amazon Inspector for EC2 instances with agent-based scanning to detect critical file changes and known vulnerabilities, especially post-boot or instance start.
* Automated Periodic Scanning (Every 12 Hours):

  + Schedule AWS Systems Manager Automation Documents or SSM Run Command to trigger antivirus/malware scan tools on EC2 instances every 12 hours.
  + For Linux systems, use ClamAV or OSSEC/Wazuh agents scheduled via cron for `/etc`, `/bin`, and other critical system directories.
  + For Windows-based EC2 instances, use Defender Antivirus configured through Group Policy via Systems Manager State Manager, with scan schedules pushed every 12 hours.
* **File Integrity Monitoring (FIM)**:  
  Deploy file integrity monitoring tools such as AWS CloudWatch Agent with custom metrics or third-party tools (e.g., Tripwire, Wazuh) to validate system file integrity regularly.
* **Security Validation**:

  + Validate that signature databases (e.g., ClamAV `.cvd` files or Defender updates) are refreshed before each scheduled scan.
  + Use AWS Security Hub to aggregate findings from multiple sources (Inspector, GuardDuty, etc.) and alert on suspicious file modifications.

**Potential Evidence to Collect**:

* Screenshot or command logs showing scheduled tasks for 12-hour scan cycles.
* Inspector scan reports or antivirus logs with timestamps at boot and interval triggers.
* Systems Manager documents showing execution history for scan enforcement.
* Security Hub or SIEM alerts showing findings tied to scan intervals.

---

**HITRUST Requirement – Memory Protection Against Unauthorized Code Execution**  
**Control ID:** 09.j Controls Against Malicious Code  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(5)(ii)(B) – Protection from Malicious Software

**Control Objective:**  
Ensure that information systems implement security measures to prevent unauthorized code execution in system memory, reducing exposure to exploitation, malware injection, and other runtime attacks.

**Technical & Operational Implementation:**

* AWS Systems Manager & Inspector: Use AWS Systems Manager to enforce patching baselines that address known vulnerabilities enabling unauthorized code execution. AWS Inspector scans for Common Vulnerabilities and Exposures (CVEs) related to memory exploits.
* Amazon EC2 + EC2 Image Builder: Harden AMIs with settings that enable modern OS-level protections like DEP (Data Execution Prevention), ASLR (Address Space Layout Randomization), and Kernel-mode code integrity.
* AWS Nitro Enclaves: For high-assurance workloads, isolate sensitive memory using Nitro Enclaves, which provide isolated compute environments without external networking.
* AWS WAF & Shield: Reduce the surface area of external threats capable of injecting malicious code by filtering requests and mitigating attacks targeting memory vulnerabilities.
* Amazon GuardDuty: Detect behavior patterns that may indicate attempts at memory exploitation, such as privilege escalation or suspicious process launches.
* AWS Lambda: As a managed compute service, AWS Lambda automatically runs within a secure sandboxed environment with memory isolation and execution control.

**Potential Evidence to Collect:**

* Systems Manager patch compliance reports
* Inspector vulnerability reports targeting memory risks
* Configurations of EC2 hardening scripts
* Lambda function runtime settings and security context logs
* GuardDuty findings related to unauthorized code execution attempts

---

**HITRUST Requirement – Malicious Code Blocking, Quarantine, and Alerting**  
**Control ID:** 09.j Controls Against Malicious Code  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(5)(ii)(B) – Protection from Malicious Software

**Control Objective:**  
Ensure automated mechanisms are in place to detect, block, and isolate malicious code, while notifying administrators in real time to enable timely incident response and containment.

**Technical & Operational Implementation:**

* **Amazon GuardDuty:** Continuously monitors AWS accounts and workloads for indicators of compromise (IoCs). When malicious behavior is detected, GuardDuty can trigger alerts via Amazon CloudWatch and send notifications to administrators through Amazon SNS or third-party integrations (e.g., PagerDuty, Splunk).
* **AWS Security Hub:** Aggregates findings from multiple services like GuardDuty, Inspector, and third-party anti-malware tools. Security Hub can be configured with automation rules to notify teams or trigger remediation workflows.
* **AWS Network Firewall / AWS WAF:** Blocks known malicious IPs, payloads, or malware propagation through custom rule sets and managed threat signatures.
* **Amazon Inspector:** Detects vulnerabilities and malware in EC2 instances and container images. Infected instances can be flagged for quarantine actions via automated scripts or Lambda functions.
* **Systems Manager Automation & Lambda:** When malicious code is detected, automation documents or Lambda functions can isolate affected instances, move them to a quarantine VPC/subnet, and revoke IAM roles or access.
* **AWS CloudTrail + CloudWatch Logs Insights:** Tracks execution of scripts or commands that match known malware behavior and triggers automated alerts.

**Evidence to Collect:**

* GuardDuty findings with malware classification
* SNS alert delivery logs and incident notification records
* Security Hub compliance status reports
* Automation execution logs for quarantine actions
* Firewall/WAF rule logs showing blocking behavior

---

**HITRUST Requirement – Centrally Managed Malware Protection**  
**Control ID:** 09.j Controls Against Malicious Code  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(5)(ii)(B) – Protection from Malicious Software

**Control Objective:**  
Ensure that anti-malware mechanisms are centrally managed and enforced across all systems, preventing users from bypassing, disabling, or misconfiguring protections.

**Technical & Operational Implementation:**

* AWS Systems Manager (SSM): Enables centralized management of EC2 instances. Through State Manager and Automation documents, organizations can enforce the installation and configuration of antivirus/anti-malware software, ensuring compliance across all instances.
* AWS Config: Can be used to track compliance of EC2 instances with required antivirus configurations. Non-compliant resources (e.g., malware protection disabled) can trigger auto-remediation via Lambda.
* AWS Organizations + SCPs: Service Control Policies (SCPs) restrict users (even administrators) from disabling security tooling or altering critical configuration management services (e.g., SSM, Config, or CloudWatch).
* Amazon Inspector + GuardDuty + Security Hub: These tools operate centrally and cannot be disabled by individual users. Their findings are routed to centralized dashboards and alerting pipelines (e.g., AWS SNS, Splunk, PagerDuty).
* AWS IAM Permissions Boundary: Prevents users from modifying malware protection agents or terminating scanning tools by tightly scoping user permissions.

**Evidence to Collect:**

* Systems Manager compliance reports showing antivirus agent installation and operational status
* AWS Config rules and remediation execution logs
* SCP policy documents showing user-level enforcement
* GuardDuty or Security Hub centralization logs
* IAM policies and permission boundaries

---

**HITRUST Requirement – Separation of User and System Management Functionalities**  
**Control ID:** 09.j Controls Against Malicious Code  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.312(a)(1) – Access Control

**Control Objective:**  
Ensure a clear separation between user-facing services (e.g., web applications) and backend system administration (e.g., database or infrastructure management) to reduce risk of privilege misuse, unauthorized access, or inadvertent system modification.

**Technical & Operational Implementation:**

* VPC Subnet Isolation: Deploy user interface services (e.g., front-end applications, load balancers) in separate public or application subnets, while system management components (e.g., RDS, backend admin services) are isolated within private subnets, enforcing strong network boundaries.
* Security Groups and NACLs: Define granular security group rules to restrict communication between tiers (UI vs. backend). Only allow tightly scoped access from specific ports/IPs for management operations.
* IAM Roles and Permission Boundaries: Assign distinct IAM roles for user-facing Lambda/API Gateway/Web UI components and backend system admins. Prevent privilege escalation or crossover via scoped permissions.
* AWS Systems Manager Session Manager: Admin access to backend systems is handled via Systems Manager, removing the need for direct access from user-exposed environments.
* AWS Control Tower Guardrails or SCPs: Enforce preventive guardrails to disallow cross-functional access between user-facing services and infrastructure control functions.
* RDS Proxy or API Gateway Isolation: Interfaces like Amazon RDS Proxy and Amazon API Gateway are used to decouple user transactions from direct database access, enhancing logical separation.

**Evidence to Collect:**

* VPC architecture diagrams showing subnet segregation
* Security Group configuration screenshots
* IAM role definitions and policies showing separation of privileges
* Systems Manager session activity logs
* AWS Config rules validating tiered access architecture

---

**HITRUST Requirement: Audit logs for all malware checks**  
**Control ID:** 09.j Controls Against Malicious Code  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.312(b) – Audit Controls

**Control Objective:**  
Ensure that anti-virus or anti-spyware software generates audit logs for all malware checks to support accountability, incident detection, and forensic investigation.

**Technical & Operational Implementation:**

* **Amazon GuardDuty**: Continuously monitors for malicious activity and generates findings, which serve as audit logs, stored in AWS CloudWatch and Security Hub.
* **Amazon Inspector**: Performs malware and vulnerability scans and logs results for each assessment, which can be exported and reviewed.
* **AWS Systems Manager (SSM) Run Command / Patch Manager**: When used with managed EC2 instances and third-party anti-malware agents (e.g., Trend Micro, Sophos, CrowdStrike), these tools can log scan results and actions. Logs can be forwarded to S3, CloudWatch, or an external SIEM.
* **CloudWatch Logs**: Can aggregate audit logs from EC2 antivirus agents via custom logging scripts or CloudWatch agents.
* **AWS Security Hub**: Consolidates audit results and security findings from GuardDuty, Inspector, and partner solutions, supporting centralized compliance reporting.

**Evidence to Collect:**

* GuardDuty findings stored in CloudWatch Logs
* Inspector scan result reports
* CloudWatch Logs or S3 logs showing anti-malware scan results from EC2 agents
* Security Hub dashboards and exportable findings
* Configuration details of third-party AV tools integrated via Systems Manager or CloudTrail

---

**HITRUST Requirement: False-positive evaluation**   
**Control ID:** 09.j Controls Against Malicious Code  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(A) – Risk Analysis

**Control Objective:**  
Ensure the organization properly addresses false positives generated during malicious code detection and eradication, and evaluates the potential impact of such detections on system availability.

**Technical & Operational Implementation:**

* **Amazon GuardDuty**: Provides severity ratings for findings and includes metadata to help distinguish between true threats and false positives. Security teams can mark findings as benign and use suppression rules for repetitive false positives.
* **AWS Security Hub**: Allows customization of finding severity and filtering. False positives can be suppressed, and exceptions documented. Integrates with ticketing systems like Jira or ServiceNow for tracking reviews.
* **Amazon Inspector**: Assessment reports indicate which findings may be false positives. Findings are linked to CVEs or threat intelligence sources for validation.
* **CloudWatch Alarms and Logs**: Alerting and logging can be tuned to reduce false positives by refining log metrics and thresholds.
* **AWS Systems Manager Incident Manager**: Helps orchestrate incident response and includes workflows for reviewing, confirming, and escalating or suppressing suspected false positives.

**Evidence to Collect:**

* GuardDuty suppression rule configurations
* Security Hub finding disposition logs or exception documentation
* Incident Manager runbooks or ticketing system logs that show evaluation steps for findings
* Logs from CloudWatch or third-party AV agents indicating suppressed or cleared findings
* Screenshots or exports showing tagging or classification of false positives in GuardDuty or Inspector

---

**HITRUST Requirement: Regular assessment of exempted systems**  
**Control ID:** 09.j Controls Against Malicious Code  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(1)(ii)(A) – Risk Analysis

**Control Objective:**  
Ensure systems exempted from standard anti-virus requirements are periodically assessed to verify that such exemptions remain valid in light of evolving malware threats.

**Technical & Operational Implementation:**

* **Amazon Inspector**: Continuously scans supported EC2 instances, Lambda functions, and container images for vulnerabilities and unintended software changes. Can validate risk posture of systems that don’t run traditional AV agents.
* **AWS Systems Manager Patch Manager & Inventory**: Collects metadata on systems, including software installed, and provides insight into whether the host may be vulnerable to malware or has been exempted incorrectly.
* **AWS Security Hub**: Consolidates findings from Inspector, GuardDuty, and third-party tools to highlight exposure or drift from security baselines — allowing periodic reevaluation of systems previously considered low-risk.
* **Custom Lambda or Systems Manager Automation**: Can schedule reviews or runbook-based scripts to validate exemption decisions periodically (e.g., every 90 days).
* **Amazon GuardDuty**: Detects malicious behavior even on non-traditional or agentless workloads through VPC flow logs, DNS logs, and CloudTrail — helping validate whether an exempt system begins exhibiting suspicious activity.

**Evidence to Collect:**

* Documentation of malware exemption policies and criteria
* Inspector and Security Hub reports showing reviewed low-risk system posture
* Systems Manager inventory reports confirming software stack and exposure
* GuardDuty findings logs indicating no malicious activity on exempted systems
* Change management tickets or review logs showing periodic reassessment actions

---

**HITRUST Requirement: Multi-layered strategy to mitigate risk of malicious code**  
**Control ID:** 09.j Controls Against Malicious Code  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(5)(ii)(B) – Protection from Malicious Software

**Control Objective:**  
Implement a multi-layered strategy combining software, user awareness, access management, and change control to mitigate the risk of malicious code.

**Technical & Operational Implementation:**

1. Malicious Code Detection and Repair Software

   * Amazon GuardDuty: Detects malware activity across AWS environments using threat intelligence and machine learning.
   * Amazon Inspector: Automatically identifies software vulnerabilities and unwanted software on EC2 and container workloads.
   * Amazon Macie: Adds data sensitivity context to malicious activity in S3, supporting threat response.
2. Security Awareness

   * Integrate AWS IAM Access Analyzer, CloudTrail, and Security Hub alerts into security training by highlighting real findings.
   * Awareness training artifacts stored in S3, with tracking via AWS WorkDocs or third-party LMS systems.
   * Use AWS Budgets + Alerts to notify of anomalous cost behaviors potentially linked to malicious activity.
3. Appropriate System Access

   * Enforced via AWS IAM roles and policies, service control policies (SCPs), and ABAC.
   * AWS Identity Center (SSO) integrated with MFA and directory services to restrict access to systems based on role and attribute.
   * CloudTrail and Access Analyzer used to detect and correct excessive or misconfigured permissions.
4. Change Management Controls

   * Implemented using AWS Systems Manager Change Manager, AWS CodePipeline, and CloudFormation drift detection.
   * Versioning and audit trails maintained in AWS Config, CloudTrail, and CodeCommit.
   * Changes to security-sensitive infrastructure gated via approval workflows and validated against security baselines in AWS Config Rules.

**Evidence to Collect:**

* Inspector and GuardDuty findings reports
* Training logs and awareness materials
* IAM policy and role configuration documents
* SCP configurations
* Change Manager records, CloudTrail logs of deployments
* Config compliance snapshots showing change tracking

---

**HITRUST Requirement:** The organization implements and regularly updates mobile code protection, including anti-virus and anti-spyware

**Control ID:** 09.k Controls Against Mobile Code  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(5)(ii)(B) – Protection from Malicious Software

**Control Objective:**  
Ensure protection mechanisms are in place to detect, restrict, and update defenses against malicious mobile code.

**Technical & Operational Implementation:**

1. **Mobile Code Protection Implementation**

   * **Amazon Inspector**: Continuously scans for known vulnerabilities and unwanted software, including malware, on EC2 and container workloads.
   * **AWS Systems Manager**: Enables patch compliance enforcement and configuration baselining to prevent unauthorized mobile code deployment.
   * **Amazon GuardDuty**: Detects behavior associated with mobile code execution or propagation, such as suspicious outbound communication or credential exfiltration.
2. **Regular Updates**

   * **Inspector and Systems Manager Patch Manager**: Automatically apply updates and signatures for anti-malware definitions across managed instances.
   * Leverage **AWS Config Rules** and **AWS Security Hub** to continuously assess drift or compliance failures in malware defense configuration.
   * Security tooling (Inspector/GuardDuty) is automatically updated via AWS backend with latest definitions and intelligence feeds.

**Evidence to Collect:**

* Amazon Inspector agent and findings reports
* GuardDuty threat detections related to mobile code
* Patch Manager execution logs and compliance reports
* AWS Config snapshots showing controls related to unauthorized mobile code
* Systems Manager compliance status reports

---

**HITRUST Requirement:** Prevent unauthorized mobile code execution  
**Control ID:** 09.k Controls Against Mobile Code  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(5)(ii)(B) – Protection from Malicious Software

**Control Objective:**  
Prevent unauthorized mobile code execution and ensure controls are in place to manage and isolate mobile code risks.

**Technical & Operational Implementation:**

1. **Blocking Mobile Code Use and Receipt**

   * Use **AWS Network Firewall**, **AWS WAF**, and **Security Groups** to block downloads of known mobile code file types (e.g., `.jar`, `.swf`, `.exe`).
   * Enforce restrictions via **S3 Bucket Policies**, IAM, and **Amazon Macie** to prevent upload or storage of unapproved executable content.
2. **Isolated Execution Environments**

   * Deploy mobile code within AWS Lambda, AWS Fargate, or sandboxed EC2 environments that are isolated using VPC segmentation and security groups.
   * Use Amazon WorkSpaces or AppStream 2.0 with isolated browser streaming for restricted environments.
3. Technical Measures for Managing Mobile Code

   * Leverage Amazon Inspector and AWS Systems Manager to detect and manage execution of unapproved code.
   * Configure GuardDuty Runtime Monitoring and Amazon Detective to monitor behavior and alert on policy violations.
   * Use Systems Manager State Manager to enforce execution policies on managed instances.
4. Controlled Access to Mobile Code

   * Enforce least privilege IAM policies, resource tagging, and ABAC to control which users/systems can access or execute mobile code.
   * Monitor access logs via AWS CloudTrail and AWS CloudWatch Logs Insights for anomalous activity tied to mobile code interactions.

**Evidence to Collect:**

* Firewall/WAF rule sets blocking known executable types
* IAM policies and SCPs restricting code execution
* Inspector or Systems Manager scan results
* CloudTrail logs of denied execution attempts
* VPC configuration screenshots or Terraform output showing network isolation
* Runtime detections from GuardDuty and alerts from Security Hub

---

**HITRUST :** Automated controls to authorize and restrict the use of mobile code (e.g., Java, JavaScript, ActiveX, PDF, postscript, Shockwave movies, and Flash animations).

**Control ID:** 09.k Controls Against Mobile Code  
**Control Type:** Technical  
**Control Level:** 1  
 **Control Objective :**Ensure that mobile code execution is authorized and restricted to reduce risk of malicious activity, particularly in web-facing or user-interactive environments.

**Technical & Operational Implementation**

* **Amazon WorkSpaces & WorkSpaces Web**: Provision virtual desktops and secure browser environments with tightly managed mobile code execution policies.
* **AWS Systems Manager (SSM)**: Apply configuration baselines across Windows or Linux instances to restrict or disable specific mobile code types (e.g., disabling Flash via Group Policy, restricting Java execution).
* **AWS Config**: Monitor compliance with desired browser and endpoint configurations related to mobile code (e.g., Java enabled = false).
* **Amazon Inspector**: Detect outdated or vulnerable browser plugins or scripting engines.
* **AWS WAF / Network Firewall**: Block delivery of risky mobile code via HTTP/S traffic (e.g., JavaScript injection, ActiveX exploits).
* **IAM & SCPs**: Limit user permissions to install or execute unauthorized mobile code or unsafe extensions.

**Evidence to Collect**

* SSM State Manager compliance reports for browser/mobile code restrictions
* AWS Config rule evaluation results related to mobile code settings
* WAF rule sets and logs showing filtered mobile code
* SCPs and IAM policies enforcing control boundaries
* Screenshot or documentation of WorkSpaces policies restricting plugins/scripting
* Amazon Inspector findings referencing mobile code plugins (e.g., Flash, Java)

---

**HITRUST Requirement:** default-deny traffic policy for all endpoints  
**Control ID:** 09.m Network Controls  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.312(c)(1) – Access Control; 45 CFR §164.308(a)(1)(ii)(A) – Risk Analysis

**Control Objective:**  
Ensure all endpoint systems (e.g., workstations, servers) enforce a default-deny traffic policy through host-based firewalls or port filtering, permitting only explicitly authorized services and ports.

**Technical & Operational Implementation:**

Default-Deny Enforcement on Endpoints

* Use AWS Systems Manager to deploy host-based firewall rules on EC2 instances (Windows Defender Firewall, iptables, etc.), enforcing default-deny policies.
* Leverage EC2 launch templates or SSM State Manager to enforce configuration baselines that apply restrictive host firewall rules.
* Utilize Amazon Inspector to verify whether instances comply with the required host firewall configurations.

Explicitly Allow Required Services and Ports

* Use Security Groups with principle of least privilege to only allow specific inbound and outbound ports.
* Enforce VPC-level restrictions using Network ACLs to provide subnet-level default-deny behavior.
* Use AWS Config rules to continuously evaluate security group settings and report deviations from expected firewall posture.

Supplementary Network Controls

* Deploy AWS Network Firewall at VPC edge to layer network-based filtering on top of host-based protections.
* Use GuardDuty and Amazon Detective to detect suspicious traffic or unauthorized service exposure.

**Evidence to Collect:**

* Systems Manager Association logs showing successful host firewall rule enforcement
* Inspector scan reports confirming host-based firewall configurations
* Security Group configuration snapshots or Terraform manifests
* AWS Config rule evaluation history for SG compliance
* CloudTrail logs showing policy change history for firewall settings
* GuardDuty alerts or Network Firewall logs showing dropped traffic by default-deny rules

---

**HITRUST Requirement:** File sharing is disabled on wireless-enabled devices  
**Control ID:** 09.m Network Controls  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.312(c)(1) – Integrity

**Control Objective:**  
Restrict unauthorized file sharing on wireless-enabled devices to prevent data leakage and ensure the integrity and confidentiality of sensitive information.

**Technical & Operational Implementation:**

Restrict File Sharing on Wireless-Enabled Devices:

* Use AWS WorkSpaces and Amazon WorkSpaces Web to provide secure virtual desktops that do not allow direct file sharing over wireless interfaces unless explicitly configured.
* Disable file sharing protocols (e.g., SMB, AFP, NFS) on EC2 instances with wireless capabilities (if used in hybrid/edge environments) via AWS Systems Manager Run Command or State Manager.
* Configure IAM policies and endpoint protection (e.g., using AWS-provided AMIs integrated with CrowdStrike/SentinelOne via Marketplace) to prevent peer-to-peer sharing over wireless connections.

Enforce Security Baselines:

* Apply AWS Config rules to track configuration drifts such as unexpected sharing service enablement.
* Integrate AWS Control Tower and Service Catalog to enforce wireless device policies and approved gold image deployments.
* Use Amazon Inspector to scan for vulnerable or misconfigured file sharing settings on hybrid fleet systems.

**Evidence to Collect:**

* Systems Manager run logs confirming file sharing disabled
* Inspector assessment reports showing disabled or removed sharing services
* CloudTrail logs showing denied attempts to enable file sharing
* Config rule compliance history for SMB/NFS sharing status
* WorkSpaces Web configuration screenshots showing disabled drive/file access

---