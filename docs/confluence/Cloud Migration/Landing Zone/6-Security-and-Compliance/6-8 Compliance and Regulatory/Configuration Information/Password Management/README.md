# Password Management

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4993286435/Password%20Management

**Created by:** Shreya Singh on August 07, 2025  
**Last modified by:** Shreya Singh on August 08, 2025 at 09:50 PM

---

**HITRUST Requirement: Password Policy documentation and enforcement**  
Control ID: 01.d User Password Management  
Control Type: Technical  
Control Level: Implementation  
HIPAA Mapping: 45 CFR §164.308(a)(5)(ii)(D) – Log-in Monitoring

**Control Objective:**  
Ensure secure authentication by documenting and enforcing password requirements through technical mechanisms that prevent weak or unauthorized credentials.

**Technical & Operational Implementation:**

**Password Policy Configuration**

* Use AWS IAM password policy to define and enforce password complexity, rotation frequency, minimum length, reuse prevention, and MFA requirements.

  + **Minimum password length:** ≥ 8 characters (HITRUST often recommends ≥ 12 for higher maturity levels).
  + **Require uppercase letters:** Enabled.
  + **Require lowercase letters:** Enabled.
  + **Require numbers:** Enabled.
  + **Require non-alphanumeric characters:** Enabled.
  + **Prevent password reuse:** At least last 4 passwords remembered.
  + **Password expiration:** Max 90 days (HITRUST explicit; HIPAA requires “when appropriate” but align to HITRUST).
  + **Allow users to change own password:** Enabled.
  + **Force reset on first login:** Enabled for new accounts.
  + **Track failed logins :** Enabled
* Enforce IAM best practices, including enabling IAM Identity Center for centralized user authentication and policy enforcement across AWS accounts.

**Technical Enforcement Controls**

* Enable IAM Identity Center or integrate with external identity providers like Okta or Azure AD via SAML to enforce enterprise-grade password policies and single sign-on.
* Leverage AWS Config to continuously audit password policy compliance. Eg: following AWS Managed Config rules can be enabled:

  + `iam-password-policy`
  + `root-account-mfa-enabled`
  + `mfa-enabled-for-iam-console-access`
  + `iam-user-no-policies-check`
  + `iam-user-unused-credentials-check`
  + `access-keys-rotated`
  + `iam-user-mfa-enabled`
* Use AWS Organizations Service Control Policies (SCPs) to restrict IAM password policy overrides or misconfigurations.  
  Enable IAM Access Analyzer to monitor for unintended access paths and credential exposures.

**Monitoring and Logging**

* Track all IAM authentication and password policy events using AWS CloudTrail and analyze them in CloudWatch Logs or AWS Security Hub.

  + Retain CloudTrail logs for ≥ 6 years if aligning with HITRUST evidence requirement
  + Store logs in S3 with encryption (SSE-S3 or SSE-KMS) and enable Object Lock for immutability
  + **CloudTrail logging enabled** for all regions to track:

    - Password changes
    - Login failures
    - MFA changes
  + **CloudWatch alarms** for:

    - Excessive failed login attempts (≥ 5)
    - Root account usage
    - Password policy changes
* Configure Amazon GuardDuty to detect brute-force login attempts or unusual IAM activity.

**Potential Evidence to Collect:**

* IAM password policy configuration screenshot or Terraform code
* CloudTrail logs showing password policy enforcement or MFA usage
* GuardDuty alerts for login anomalies
* Config rule evaluation history for password policy compliance
* Identity Center configuration details showing enforced password requirements and integrations

---

**HITRUST Requirement: Change default passwords of all new devices before deployment**  
**Control ID:** 01.d User Password Management  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.308(a)(5)(ii)(C) – Password Management

**Control Objective:**  
Prevent unauthorized access by ensuring all default credentials on systems and devices are replaced with secure administrative credentials prior to deployment in a networked environment.

**Technical & Operational Implementation:**

#### Credential Rotation and Hardening:

* Use AWS Secrets Manager to store and automatically rotate default credentials for applications and databases deployed in AWS.
* Leverage AWS Systems Manager Parameter Store for secure storage of non-rotating credentials with strict access controls.
* Configure IAM to disallow use of default credentials by implementing custom policies and enforcing MFA for privileged users.

#### Baseline Configurations:

* Create AMIs (Amazon Machine Images) for EC2 instances with default accounts removed or replaced with secure administrator credentials.
* Use AWS OpsWorks or EC2 User Data scripts to remove or update default system credentials during instance initialization.
* Deploy AWS Network Firewall and VPC configurations with no embedded default credentials.

**Compliance & Monitoring:**

* Use AWS Config to audit for usage of default or weak credentials via custom rules.
* Detect insecure login behavior and brute-force attempts using Amazon GuardDuty and integrate alerts with AWS Security Hub.
* Scan infrastructure using Amazon Inspector to identify software components with known default credentials or insecure settings.

#### Device & Access Point Management:

* For AWS-compatible edge devices (e.g., AWS Snowball, AWS IoT Greengrass), reset factory credentials using AWS IoT policies and certificates.
* Ensure that all network devices integrated with AWS services are configured using secure credential management protocols and APIs.

**Potential Evidence to Collect:**

* Secrets Manager configuration with rotation policies
* CloudTrail logs showing password update events
* EC2 launch templates or AMI definitions with default password removal
* IAM policies prohibiting default or shared credentials
* Inspector reports showing absence of default credentials
* GuardDuty alerts for login attempts using known defaults
* Config rule evaluations related to credential strength

---

**HITRUST Requirement:** Secure Transmission of Authentication Credentials  
**Control ID:** 01.d User Password Management  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.312(e)(1) – Transmission Security

**Control Objective:**  
Ensure that authentication credentials are transmitted securely over communication channels to prevent interception, replay attacks, or unauthorized access during transmission.

**Technical & Operational Implementation:**

Secure Transmission Methods for Authentication

* Use AWS Identity and Access Management (IAM) to enforce encrypted access via HTTPS (TLS 1.2 or higher) for all interactions with the AWS Management Console, AWS CLI, SDKs, and APIs. This prevents credentials (usernames, passwords, access keys, session tokens) from being exposed in transit.
* Enable multifactor authentication (MFA) using secure cryptographic protocols such as TOTP or FIDO2 for IAM users and federated identities. Ensure secure provisioning and validation of MFA tokens using encrypted channels.
* Leverage AWS Secrets Manager and AWS Systems Manager Parameter Store for secure storage and retrieval of credentials. Access to these services is performed via secure API calls over TLS, and responses are encrypted in transit.
* For federated authentication (e.g., with Okta or Azure AD), configure SAML 2.0 or OIDC identity federation with encrypted assertions and signed tokens. Use HTTPS endpoints for all identity provider (IdP) communications.
* Ensure all EC2 instances, containers, and serverless functions (e.g., AWS Lambda) that access AWS resources retrieve temporary credentials using the AWS Secure Token Service (STS) via encrypted channels.
* Enforce client-side encryption using tools like AWS Encryption SDK or AWS Certificate Manager (ACM) when transmitting sensitive data between internal systems or third-party applications.

Audit and Monitoring

* Monitor credential access and API usage via AWS CloudTrail. CloudTrail logs capture all authentication attempts, including MFA use, credential lifecycle events, and access key activity.
* Use Amazon GuardDuty to detect anomalous or suspicious use of credentials in near real-time, including attempts to bypass secure channels or use credentials from unexpected geographies.
* Enable AWS Config rules to monitor whether secure transmission is enforced, such as disallowing use of non-HTTPS endpoints or unencrypted API access.

**Evidence to Collect:**

* IAM policies enforcing use of TLS-secured APIs
* MFA configuration reports from IAM or AWS IAM Identity Center
* CloudTrail logs showing use of encrypted channels during authentication
* Configuration of Secrets Manager or Parameter Store with encrypted retrieval
* GuardDuty alerts indicating credential misuse
* Screenshots or Terraform templates demonstrating secure identity federation setup
* AWS Config rule compliance showing enforcement of secure transmission protocols

---

**HITRUST Requirement:** Identity Verification for Account Recovery  
**Control ID:** 01.d User Password Management  
**Control Type:** Technical  
**Control Level**: Implementation  
**HIPAA Mapping:** 45 CFR §164.312(a)(2)(i) – Unique User Identification

**Control Objective:**  
Ensure user identity is properly verified before allowing password resets or account recovery to prevent unauthorized access to sensitive systems and data.

**Technical & Operational Implementation:**

#### Identity Verification Prior to Password Reset

* Use AWS IAM Identity Center (formerly AWS SSO) or integrated Identity Providers (e.g., Okta, Azure AD) to enforce identity verification steps before initiating a password reset. These may include challenge questions, multi-factor authentication (MFA), or administrative approval workflows.
* Require MFA for all IAM users and federated identities, particularly for password recovery actions. AWS enforces MFA input as a prerequisite to self-service password resets when integrated with compatible IdPs.
* For root account or IAM password resets, configure administrative controls to disallow direct self-service reset and instead require AWS Support or internal security admin workflow involving identity validation.
* Implement AWS Helpdesk or ITSM tools (e.g., Jira Service Management) integrated with AWS IAM Identity Center to ensure that any password reset request triggers a mandatory identity verification procedure.
* Log all password reset requests and identity verification outcomes using AWS CloudTrail. These logs provide immutable records to support forensic review or audit investigations.
* Use AWS Config to monitor password policy compliance and ensure only authorized entities are permitted to perform sensitive identity-related actions.

**Evidence to Collect:**

* IAM or SSO password reset policies requiring identity verification
* MFA enforcement reports from IAM Identity Center or IdP
* Screenshots or logs showing identity verification challenge steps
* AWS CloudTrail events showing password reset actions with verified user context
* ITSM workflow documentation detailing password reset identity checks
* Config rule snapshots verifying access control on identity management actions

---

**HITRUST Requirement:** Automated Authentication and Secure Credential Storage  
**Control ID:** 01.d User Password Management  
**Control Type:** Technical  
**Control Level:** Implementation  
**HIPAA Mapping:** 45 CFR §164.312(a)(1) – Access Control

**Control Objective:** Prevent the storage or use of plaintext passwords or other authentication credentials in automated scripts, macros, or login processes that may compromise system security or user identity.

**Technical & Operational Implementation:**

#### Credential Management

* Avoid embedding passwords in infrastructure-as-code, shell scripts, Lambda functions, or automation tools. Enforce this through static code analysis and code review practices in CI/CD pipelines (e.g., AWS CodePipeline, GitHub Actions with secret scanning).
* Use AWS Secrets Manager or AWS Systems Manager Parameter Store with encryption to securely store and manage passwords, database credentials, and API keys. These services integrate with IAM to control access and rotate secrets securely.
* Ensure credentials used in automation (e.g., EC2 bootstrapping, Lambda functions) are retrieved securely at runtime using temporary AWS credentials via IAM roles and instance profiles rather than hardcoded passwords.
* Enforce IAM policies that deny the use of credentials stored in known insecure locations (e.g., user-data scripts, environment variables in plaintext).
* Audit for password leakage or misuse using Amazon Macie, which detects sensitive data such as passwords or secrets embedded in unstructured content across S3.

#### Monitoring and Detection

* Use AWS CloudTrail to track usage of AWS Secrets Manager and IAM role assumption to ensure secure practices are followed.
* Enable AWS Config rules (e.g., `secretsmanager-rotation-enabled`, `iam-password-policy`) to continuously monitor compliance with secure credential storage and handling practices.

#### Evidence to Collect:

* IAM role and instance profile configuration screenshots
* Sample code snippets using AWS Secrets Manager with no hardcoded credentials
* CloudTrail logs showing secure secret access patterns
* Macie alerts for plaintext password presence in S3
* Config rule compliance reports validating secure storage of credentials
* CI/CD pipeline secret scanning configuration and results

---

**HITRUST Requirement:** Password Acknowledgement and Acceptance  
**Control ID**: 01.d User Password Management  
**Control Type**: Administrative  
**Control Level**: Implementation  
**HIPAA Mapping**: 45 CFR §164.308(a)(5)(ii)(D) – Procedures for Monitoring Login Attempts and Reporting Discrepancies

**Control Objective**:  
Ensure that users are aware of and accountable for the issuance of authentication credentials by requiring formal acknowledgement upon password issuance.

**Technical & Operational Implementation**:

Password Acknowledgement Mechanism

* When provisioning IAM users or federated identities via AWS IAM Identity Center, implement workflows that require user acknowledgment of password receipt and responsibility through external systems such as Jira, or ITSM tools integrated with AWS provisioning workflows.
* Use AWS Lambda functions or Step Functions to trigger acknowledgment notifications via email or ticketing systems upon initial password issuance.

Credential Issuance Tracking

* Store issuance logs in Amazon DynamoDB or AWS Secrets Manager with metadata (e.g., timestamp, recipient identity) to record credential delivery events.
* Use AWS CloudTrail to track IAM user creation and credential issuance events.
* Apply tagging and resource-level access tracking to identify credentials issued for specific systems or workloads.

Policy Enforcement

* Include password acknowledgment requirements in onboarding SOPs and employee handbooks, stored and versioned in Amazon S3 and linked through AWS WorkDocs or company intranet.
* Enforce policy acknowledgments through Amazon WorkSpaces or AppStream 2.0 when delivering virtual desktops, requiring password receipt confirmations as part of onboarding login scripts.

Audit and Review

* Periodically audit CloudTrail logs and identity provisioning workflows to ensure password acknowledgments are being issued and recorded appropriately.
* Use AWS Config to ensure all credential issuance actions are followed by a tagging or logging step indicating acknowledgment capture.

**Potential Evidence to Collect**:

* Sample of ticket/email confirmations from the onboarding system
* AWS CloudTrail logs showing IAM user creation and password issuance events
* DynamoDB or S3 records containing acknowledgment metadata
* Screenshot of onboarding procedure referencing password receipt acknowledgment
* Output from AWS Config showing conformance to credential issuance and tracking policies

---

**HITRUST Requirement:** Password Management and Security Enforcement  
**Control ID**: 01.d User Password Management  
**Control Type**: Technical  
**Control Level**: Implementation  
**HIPAA Mapping**: 45 CFR §164.308(a)(5)(ii)(C) – Procedures for Creating, Changing, and Safeguarding Passwords

**Control Objective**:  
Ensure strong password management by enforcing the timely update, replacement, and configuration of secure passwords across all systems, particularly in response to compromise or account lifecycle events.

**Technical & Operational Implementation**:

Password Change Upon Indication of Compromise

* Enable AWS CloudTrail and Amazon GuardDuty to detect signs of account compromise such as unauthorized logins or unusual activity.
* Configure AWS Security Hub to generate findings that can trigger AWS Systems Manager Automation to disable credentials or rotate IAM user passwords via Lambda functions or Secrets Manager.

Default Password Alteration

* Avoid use of default vendor credentials by integrating AWS Systems Manager State Manager or AWS Config to detect and remediate default usernames and passwords.
* Leverage AWS Secrets Manager to generate unique, random secrets for application or database credentials at deployment, replacing vendor-provided defaults.

Temporary Password Change on First Logon

* For IAM users, enforce mandatory password reset on first sign-in by setting the `PasswordResetRequired` flag via the AWS CLI or IAM console during user creation.
* Monitor compliance through AWS Config rules for IAM password policy settings.

Password Reset After Account Recovery

* Use AWS IAM Identity Center or custom identity workflows via AWS Cognito to enforce immediate password reset following account recovery scenarios.
* Implement MFA for account recovery procedures and trigger automated password rotation using AWS Lambda functions integrated with Secrets Manager and CloudWatch Events.

**Evidence to Collect**:

* IAM user creation logs showing `PasswordResetRequired` set to true
* CloudTrail logs and GuardDuty findings showing detection and response to suspected compromise
* AWS Config compliance reports for password policy enforcement
* Screenshots or exported logs from AWS Secrets Manager showing automated credential rotation
* Audit logs or workflow records showing user password reset after account recovery events
* Terraform or CloudFormation templates enforcing secure credential deployment policies

---

**HITRUST Requirement:**Password Encryption During Transmission and Storage  
**Control ID**: 01.d User Password Management  
**Control Type**: Technical  
**Control Level**: Implementation  
**HIPAA Mapping**: 45 CFR §164.312(a)(2)(iv) – Encryption and Decryption; 45 CFR §164.312(e)(2)(ii) – Integrity Controls

**Control Objective**:  
Ensure all passwords are protected using strong encryption mechanisms both during transmission over networks and while at rest to safeguard against unauthorized access or tampering.

**AWS Technical & Operational Implementation**:

Encryption During Transmission

* Enforce TLS 1.2 or higher across all AWS services using IAM policies, service control policies (SCPs), and AWS CloudFront security policies.
* Use AWS Certificate Manager (ACM) to provision and manage SSL/TLS certificates for secure access to web applications and APIs.
* For applications hosted on AWS (e.g., EC2, ALB, API Gateway), configure HTTPS listeners and ensure all password exchanges occur over secure channels.

Encryption During Storage

* Store passwords using AWS Secrets Manager or AWS Systems Manager Parameter Store (SecureString type) with AWS KMS encryption enabled.
* For databases (e.g., RDS, DynamoDB, Redshift), ensure encryption at rest is enabled and keys are managed via AWS Key Management Service (KMS).
* Enable server-side encryption for S3 buckets storing any files or configuration data containing credentials or hashed passwords.

Compliance Monitoring

* Use AWS Config rules to ensure encryption in transit and at rest settings are enforced across services.
* Integrate AWS Security Hub to aggregate and flag findings related to unencrypted traffic or resources.
* Audit CloudTrail logs to verify password handling actions use encrypted endpoints and encrypted resources.

**Potential Evidence to Collect**:

* TLS policy configurations from CloudFront, API Gateway, or ELB
* Screenshots or Terraform code showing Secrets Manager and Parameter Store using KMS encryption
* Config rule compliance reports for encryption settings in S3, RDS, and EC2
* ACM certificate issuance logs and SSL listener configurations
* IAM policies or SCPs enforcing encryption usage
* CloudTrail logs showing password operations executed over HTTPS endpoints
* Key usage logs from AWS KMS showing access to encrypted password stores

---

**HITRUST Requirement:** User Responsibility for Password Confidentiality  
**Control ID**: 01.d User Password Management  
**Control Type**: Administrative  
**Control Level**: Policy  
**HIPAA Mapping**: 45 CFR §164.308(a)(3)(ii)(A) – Workforce Security; 45 CFR §164.308(a)(5)(i) – Security Awareness and Training

**Control Objective**:  
Ensure users acknowledge their responsibility to maintain the confidentiality of passwords and restrict the sharing of group credentials to authorized personnel only.

**Technical & Operational Implementation**:

Password Confidentiality Acknowledgement

* Use AWS IAM Identity Center (formerly AWS SSO) integrated with corporate HR or onboarding platforms (e.g., Workday, BambooHR) to require users to sign or digitally acknowledge Acceptable Use Policies (AUPs) that include password confidentiality.
* Incorporate the policy acknowledgment into onboarding workflows using tools like AWS Lambda and Step Functions to automate tracking and enforcement.
* Store signed acknowledgment forms securely using Amazon S3 with encryption enabled (SSE-KMS) and access limited via IAM policies.

Enforcement of Password Confidentiality

* Use IAM policies and roles to enforce individual account credentials. Shared credentials should be replaced by role assumption with proper access auditing via CloudTrail.
* Employ AWS Secrets Manager or AWS Systems Manager Parameter Store for secure, role-based access to shared credentials if absolutely necessary, while auditing access logs for misuse.
* Implement security awareness training via AWS Learning Management System (LMS) integrations or third-party platforms that include password confidentiality modules.

Monitoring and Alerts

* Enable AWS Config and AWS Security Hub to track and report non-compliant IAM policies that allow use of shared access or wildcards.
* Use AWS CloudTrail and Amazon CloudWatch Logs Insights to monitor anomalous authentication patterns that may indicate shared credentials.

**Potential Evidence to Collect**:

* Signed user acknowledgment forms or onboarding workflow records
* IAM policies enforcing individual access with no shared users
* Training completion records for password handling and AUP
* S3 bucket storing signed forms with audit logs
* CloudTrail logs showing access by individual user identities
* Secrets Manager access logs indicating use of controlled credentials
* AWS Config compliance reports on IAM user uniqueness and key rotation

---

**HITRUST Requirement:** Temporary Password Strength and Individualization  
**Control ID**: 01.d User Password Management  
**Control Type**: Technical  
**Control Level**: Implementation  
**HIPAA Mapping**: 45 CFR §164.308(a)(5)(ii)(D) – Log-in Monitoring

**Control Objective**:  
Ensure that temporary passwords issued to users are unique to each individual and are sufficiently complex to prevent guessing or brute-force attacks.

**Technical & Operational Implementation**:

Unique Temporary Passwords

* When creating IAM users manually or programmatically via AWS CLI, API, or CloudFormation, enable "Require password reset" and assign unique temporary passwords to each user.
* Integrate AWS IAM with identity providers through AWS IAM Identity Center (SSO) or AWS Directory Service to assign per-user credentials.
* Use AWS Lambda and AWS Secrets Manager to dynamically generate and assign one-time, user-specific temporary credentials for service access or onboarding automation.

Password Complexity

* Enforce password complexity requirements (minimum length, uppercase, lowercase, numbers, symbols) through IAM password policies defined in AWS IAM.
* Monitor policy enforcement using AWS Config rules like `iam-password-policy-check` to ensure minimum length and complexity are maintained.
* Use AWS Systems Manager Session Manager to eliminate the need for persistent passwords by enabling temporary access via short-lived secure sessions.

Rotation and Expiry

* Set temporary passwords to expire automatically after first use using IAM’s `PasswordResetRequired` flag or by integrating with custom onboarding automation using Step Functions and DynamoDB.
* Leverage AWS Control Tower or Service Catalog to standardize account provisioning with secure password handling practices.

**Potential Evidence to Collect**:

* IAM password policy configuration showing complexity enforcement
* CloudTrail logs showing unique IAM user creation with password reset flag
* Secrets Manager or Parameter Store records of unique temporary credential generation
* Config rule compliance status for `iam-password-policy-check`
* Evidence of Lambda or automation functions generating per-user passwords
* User onboarding or directory synchronization logs confirming individual credential assignments

---

**HITRUST Requirement:** Password Masking and Display Protection  
**Control ID**: 01.d User Password Management  
**Control Type**: Technical  
**Control Level**: Implementation  
**HIPAA Mapping**: 45 CFR §164.312(a)(2)(iv) – Encryption and Decryption

**Control Objective**:  
Prevent unauthorized viewing or disclosure of passwords by ensuring that password fields and secrets are not displayed in plain or clear text during input, retrieval, or storage processes.

**Technical & Operational Implementation**:

Masked Password Inputs

* AWS Management Console login and IAM user password prompts use masked input fields by default, ensuring password characters are not visible on screen.
* When using AWS WorkSpaces, AppStream 2.0, or Amazon Connect agent desktops, ensure password inputs in third-party or custom apps follow UI/UX standards for password masking.

Avoiding Clear Text Passwords in Storage and Retrieval

* Use AWS Secrets Manager and AWS Systems Manager Parameter Store to securely store credentials and ensure values are retrieved only via IAM-authorized API access. These services encrypt secrets at rest and do not expose them in plaintext by default.
* Enable audit logging through AWS CloudTrail to monitor any calls to `GetSecretValue` or `GetParameter` with `WithDecryption=true`, and review access controls.

Preventing Plaintext in Logs

* Configure logging systems like CloudWatch Logs and Lambda logs to redact or avoid logging sensitive input fields such as passwords using filters or log scrubbing mechanisms.
* Use AWS WAF’s logging and redaction capabilities to automatically redact sensitive form fields in HTTP logs, including password fields.

IAM and API Protections

* Implement least privilege IAM policies that restrict who can call actions like `iam:CreateLoginProfile`, `iam:UpdateLoginProfile`, and `iam:ChangePassword`.
* Leverage Amazon Inspector and AWS Config to scan for misconfigurations that may lead to exposure of sensitive credentials in plaintext.

**Potential Evidence to Collect**:

* Screenshots or user interface evidence of password masking in web forms and CLI tools
* Secrets Manager/Parameter Store configuration showing no plaintext display
* CloudTrail logs indicating limited access to secret retrieval APIs
* IAM policies restricting access to password-modifying APIs
* Log redaction/filtering configuration for CloudWatch and WAF logs
* Reports from Amazon Inspector or AWS Config on plaintext exposure risks

---

**HITRUST Requirements:** Password and Passphrase Complexity and Management  
**Control ID**: 01.d User Password Management  
**Control Type**: Technical  
**Control Level**: Implementation  
**HIPAA Mapping**: 45 CFR §164.308(a)(5)(ii)(D) – Log-in Monitoring

**Control Objective**:  
Ensure strong, non-compromised, and user-friendly password creation by enforcing password complexity requirements, detecting weak or reused passwords, and using automated mechanisms to guide secure password selection.

**Technical & Operational Implementation**:

Password Blacklist Maintenance and Verification

* Integrate AWS Cognito user pools with AWS Lambda triggers (PreSignUp or PreAuthentication) to enforce password policies and check user-chosen passwords against a dynamic list of commonly used or compromised passwords (e.g., integrating with HaveIBeenPwned or internal breach databases).
* Use Cognito Advanced Security features to evaluate the security risk of user sign-in attempts, flagging poor password practices and known compromised credentials.
* Maintain and review a regularly updated dictionary of forbidden passwords and apply it during password creation through custom validation logic.

Password Policy Enforcement

* In IAM and Cognito, define password policies enforcing minimum length, character complexity, and support for passphrases. AWS Cognito allows you to customize these rules to include spaces and printable ASCII characters.
* Enforce password expiration policies and prevent password reuse using IAM’s password policy capabilities and Cognito’s advanced configuration.

User Empowerment and Flexibility

* Configure AWS Cognito to allow users to set longer passphrases, up to 256 characters.
* Use Cognito’s user pool password policy settings to allow special characters, including spaces and all printable characters.
* Educate users via custom UI or onboarding documentation that strong passphrases are acceptable and encouraged.

Automated Tools and Password Strength Support

* Use AWS Amplify or Lambda front-end integrations to suggest strong passphrases and show strength meters during account creation or password change.
* Consider integrating with third-party password strength libraries (e.g., zxcvbn) in the UI to guide users in selecting secure passwords.
* Leverage AWS Secrets Manager to store and rotate strong generated passwords for system accounts and encourage secure practices through automation.

**Evidence to Collect**:

* Cognito password policy configuration showing character complexity, reuse prevention, and length enforcement
* Lambda function code or configuration validating passwords against a blacklist
* Password dictionary or documented procedure for updating it every 180 days and after compromise events
* IAM password policy screenshot and policy JSON
* Audit logs from CloudTrail showing password change attempts and rejected weak passwords
* User interface screenshots or guidance for passphrase creation
* Reports/logs from Cognito Advanced Security on sign-in risk detection and password strength feedback usage

---

**HITRUST Requirements:** Secure Password Distribution Practices  
**Control ID**: 01.d User Password Management  
**Control Type**: Technical  
**Control Level**: Implementation  
**HIPAA Mapping**: 45 CFR §164.312(a)(2)(i) – Unique User Identification  
 **Control Objective**:  
Ensure secure and confidential dissemination of passwords by avoiding third-party intermediaries and unencrypted communication channels.

**Technical & Operational Implementation**:

**Avoiding Use of Third-Parties for Password Distribution**

* Use AWS Identity and Access Management (IAM) for secure account provisioning and password management within AWS services, eliminating the need for third-party password delivery tools.
* For federated identity, leverage AWS SSO or third-party identity providers (IdPs) integrated with SAML or OIDC to delegate authentication without direct password sharing.

**Secure Credential Communication**

* Avoid sending passwords through plaintext email. Enforce use of secure communication protocols like TLS/SSL when transmitting credentials via internal automation workflows.
* Implement AWS Secrets Manager or AWS Systems Manager Parameter Store to securely share credentials and secrets with tightly controlled access policies.
* Automate password rotation and retrieval through IAM roles or AWS Lambda, so no human-readable password is ever manually disseminated.

**Monitoring and Logging**

* Enable AWS CloudTrail to log access to Secrets Manager and IAM CreateUser/ResetLoginProfile actions to monitor how credentials are created or reset.
* Use Amazon CloudWatch and Security Hub to generate alerts for any unauthorized attempts to access password storage services or distribute credentials improperly.

**Evidence to Collect**:

* IAM configuration showing use of login profiles and MFA requirements
* Secrets Manager or SSM Parameter Store policies enforcing encryption and access restrictions
* Email system configuration or documentation showing email transport security settings (e.g., TLS enforcement)
* Logs from CloudTrail showing access and change history of credentials
* Screenshots or infrastructure-as-code for automated secret provisioning workflows
* Security awareness training content documenting prohibition of email-based password sharing

---

**HITRUST Requirements:** User Password Awareness and Safe Practices  
**Control ID**: 01.f Password Use  
**Control Type**: Administrative / Technical  
**Control Level**: Implementation  
**HIPAA Mapping**: 45 CFR §164.308(a)(5)(ii)(D) – Procedures for Monitoring Login Attempts and Reporting Discrepancies

**Control Objective**:  
Promote user responsibility and secure handling of passwords through awareness, policy enforcement, and technical safeguards to prevent unauthorized access and credential compromise.

**Technical & Operational Implementation**:

**Password Policy Awareness and Enforcement**

* Include password usage requirements and user responsibilities in AWS IAM onboarding documentation and employee security training programs.
* Use AWS IAM password policy to enforce complexity, minimum length, and password rotation for console users.
* Apply AWS SSO or identity federation tools (e.g., Okta, Azure AD) with centralized password policy enforcement across business applications.

**Confidentiality and Secure Storage Practices**

* Restrict access to password vaults like AWS Secrets Manager or AWS SSM Parameter Store using strict IAM roles.
* Discourage storing passwords in plaintext or personal devices by reinforcing policy through security awareness training.

**Response to Compromise or Suspicion**

* Automate password rotation using AWS Secrets Manager for service accounts.
* Use GuardDuty or Amazon Detective to monitor for credential misuse, unusual sign-ins, or data exfiltration attempts.
* Integrate CloudTrail with AWS Config rules or Security Hub to alert on suspicious IAM or access key behavior.

**Password Sharing and Social Engineering Risk Mitigation**

* Enforce MFA using IAM or AWS SSO for all users and administrators to protect against shared credentials being used.
* Implement fine-grained access control through IAM roles and least-privilege policies to avoid account or password sharing.
* Incorporate phishing awareness and social engineering modules in employee training.

**Password Reuse Prevention and Quality Selection**

* Encourage use of password managers for generating unique, strong passwords through approved tooling.
* Enforce AWS IAM policies requiring rotation and prohibit reuse of old passwords.

**Evidence to Collect**:

* Screenshots or policy files showing IAM password policy configuration
* IAM or SSO training materials emphasizing secure password practices
* AWS Config or Security Hub findings related to password security violations
* CloudTrail logs of IAM ChangePassword or ResetLoginProfile activity
* Documentation of awareness training sessions and attendance records
* Alerts or detections from GuardDuty indicating compromised credentials
* Password manager usage policy or tooling deployment records

---

**HITRUST Requirements:** Secure Password Management Practices  
**Control ID**: 01.r Password Management System  
**Control Type**: Technical  
**Control Level**: Implementation  
**HIPAA Mapping**: 45 CFR §164.312(a)(2)(i) – Unique User Identification

**Control Objective**:  
Ensure that passwords are securely created, stored, transmitted, and managed throughout their lifecycle to prevent unauthorized access and enforce strong authentication practices.

**Technical & Operational Implementation**:

**Secure Storage of Passwords**

* Use AWS Secrets Manager or AWS Systems Manager Parameter Store to store passwords in encrypted form, protected using AWS KMS (Key Management Service).
* Ensure all stored credentials are encrypted at rest using customer-managed or AWS-managed keys with fine-grained IAM access controls.

**Secure Transmission of Passwords**

* Transmit passwords only over TLS 1.2 or higher when using AWS services (e.g., AWS Management Console, CLI, APIs).
* Enforce HTTPS-only endpoints for applications hosted on services like Amazon API Gateway, ALB, and CloudFront.

**Separation of Password Files from Application Data**

* Store credentials separately from application logic or system data using dedicated AWS services like Secrets Manager, and avoid embedding them in code or AMIs.
* Use AWS CodeBuild, CodePipeline, or Lambda environment variables to reference secrets securely at runtime without hardcoding them.

**Enforcing Quality Passwords**

* Define IAM password policies for AWS console users with minimum length, character requirements, and prohibition of dictionary words.
* If using AWS SSO or identity federation, configure password quality rules via the identity provider (e.g., Okta, Azure AD).

**Password Rotation and Change Enforcement**

* Enforce password expiration intervals and reuse prevention via IAM password policy settings or identity provider controls.
* Use Secrets Manager automatic rotation with Lambda integration to rotate service account credentials securely and on schedule.

**Password History and Reuse Prevention**

* IAM password policies can prevent users from reusing their last N passwords (configurable in AWS Organizations or external IdPs).
* Monitor changes using AWS CloudTrail to log password change attempts and validate adherence to policy.

**Evidence to Collect**:

* IAM password policy configuration files or console screenshots
* Secrets Manager or SSM Parameter Store access and encryption settings
* CloudTrail logs showing password change events
* Evidence of HTTPS enforcement (ALB/CloudFront TLS policies, security headers)
* Documentation or screenshots of password quality settings from IdP (if federated)
* Secrets Manager Lambda rotation function code and success logs
* KMS key policies demonstrating encryption enforcement for stored secrets