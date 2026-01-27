# Access Controls

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4910448652/Access%20Controls

**Created by:** Alexandria Burke on July 04, 2025  
**Last modified by:** Shreya Singh on July 17, 2025 at 11:46 PM

---

**HITRUST Requirement – Access Control Rules and Rights Based on Business Requirements**

Control ID: 01.a Access Control Policy  
Control Type: Administrative / Technical  
Control Level: All Levels  
HIPAA Mapping**:** 164.308(a)(4)(ii)(C) – Access Establishment and Modification

🎯 **Control Objective**

To ensure that logical and physical access to information systems is granted based on documented business requirements and follows the principles of least privilege, need-to-know, and role-based access.

**Technical Implementation**

The organization has implemented an access control framework aligned with information security principles and tailored to business roles. Key aspects of the implementation include:

1. Role-Based Access Control (RBAC)

   * Access permissions are defined by standard user access profiles based on specific job functions (e.g., HR manager, developer, system admin).
   * These profiles outline system, application, and data-level access needs based on need-to-know, need-to-share, and least privilege principles.
2. Access Classification and Categorization

   * Access rights consider information classification levels (e.g., Public, Internal, Confidential, Restricted) and security levels (e.g., admin, user, read-only).
   * Profiles are reviewed for consistency with business unit policies and compliance obligations (e.g., HIPAA, PCI-DSS).
3. Documented Access Rights and Control Rules

   * All logical and physical access rules are clearly documented in a centralized access control policy.
   * Logical (e.g., file shares, databases, systems) and physical (e.g., badge access to server rooms) access are evaluated jointly for each user group.
4. Access Policy Integration with IAM Systems

   * Access control policies are integrated with IAM tools (e.g., Okta) to enforce predefined roles and control rules.
   * Users are assigned to groups that inherit standardized access rights, minimizing one-off custom access where possible.
5. Alignment with Business Applications

   * Access needs are gathered from application and data owners and are periodically updated to reflect changes in business operations or security posture.
   * Security requirements from each line of business are incorporated into access profiles.

📋 **Possible Evidence to Collect**

* Standard user access profile templates by job role
* Access control policy detailing roles, rights, and rules
* Mapping of access rights to information classification levels
* Examples of documented access rules for business applications
* Screenshots of IAM configuration showing enforcement of RBAC
* Audit trail of periodic reviews or updates to access profiles

---

**HITRUST Requirement – Default and Unnecessary Accounts**

Control ID: 01.b User Registration  
Control Type: Technical + Operational  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(3)(ii)(B) , 164.308(a)(4)(ii)(B) , 164.308(a)(1)(ii)(D) , 164.312(a)(1) , 164.312(d)

**Control Objective:**

Ensure that default, inactive, and unnecessary accounts are removed, disabled, or otherwise protected to prevent unauthorized access.

🔧 **Technical Implementation**

**IAM & Root Account Handling**

* The AWS root account:

  + Is secured with MFA, and not used for daily tasks.
  + All access events are logged via CloudTrail and monitored by Security Hub (or Wiz).
  + Access key usage for root is disabled; alerts trigger if created.

**Removal or Disabling of Unnecessary Accounts**

* IAM users are minimized or deprecated; organizations use IAM Identity Center (SSO) or federated access via SAML/OIDC (e.g., Okta).
* Orphaned IAM users, access keys, or console passwords are:

  + Automatically detected via IAM Credential Report, Config Rules, or GuardDuty findings
  + Disabled or deleted if inactive for 90 days (or shorter, per org policy)

**Access Key Governance**

* IAM Access Analyzer ensures no unused or excessive keys are present.
* AWS Config Rules like `iam-user-no-policies-check`, `access-keys-rotated`, and `inactive-credentials-check` are enabled.

**Account Hygiene Automation**

* Lambda or SSM Automation scripts enforce:

  + Disabling unused accounts
  + Enforcing expiration policies
  + Sending Slack/email alerts when default credentials or test accounts are found

**Prevention of Default Credentials in Services**

* EC2, RDS, and container services:

  + Use secure Secrets Manager, not embedded defaults
  + Hardened AMIs remove default OS users (e.g., `ec2-user`, `admin`) via user-data scripts
* CI/CD pipelines enforce secrets linting and default credential scanning using tools like:

  + `git-secrets`, `TruffleHog`, or AWS CodeGuru

📋 **Possible Evidence to Collect**

* IAM Credential Report showing user/account activity and key usage
* Config Rule Findings (e.g., `iam-user-unused-credentials-check`)
* Screenshot of root account MFA settings
* Alert history/logs showing removal/disablement of unused IAM users
* Access Analyzer Reports on unused accounts
* Federation and Identity Center configuration screenshots
* Lambda/SSM remediation scripts and logs
* GitHub Actions or CodePipeline scan logs for default credential detection
* EC2 launch templates showing no default users
* Documentation of Account Management SOP or Policy

---

**HITRUST Requirement – No Use of Group, Shared, or Generic Accounts**

Control ID: 01.b User Registration  
Control Type: Technical + Operational  
Control Level: Organizational Control  
HIPAA Mapping: 164.312(d), 164.312(a)(1), 164.308(a)(4)(ii)(B), 164.308(a)(5)(ii)(D), 164.308(a)(1)(ii)(D)

**Control Objective:**

Prevent the use of group, shared, or generic accounts and passwords to ensure accountability, traceability, and proper access control enforcement.

🔧 **Technical Implementation**

**Individualized Identity & Authentication**

* IAM Identity Center (SSO) or SAML Federation (e.g., Okta) ensures named user access:

  + Each user signs in with their own corporate identity.
  + All actions are traceable to a specific individual via CloudTrail.

**Disallowing Shared IAM Users or Credentials**

* IAM Users are discouraged. If still used:

  + IAM Credential Reports are monitored for shared-use indicators.
  + Inline policies and usage patterns are reviewed regularly.
  + Any account with console + access key access is flagged.
* Shared or generic account creation (e.g., `admin`, `devops`, `developer1`) is:

  + Blocked at provisioning level using naming conventions in IaC pipelines (e.g., Terraform, CloudFormation)
  + Audited by Config Rules and Access Analyzer

**No Shared Credentials Across Services**

* All service-to-service communication uses:

  + IAM Roles with STS AssumeRole, scoped per service identity
  + Instance profiles or Lambda execution roles
  + AWS Secrets Manager for unique credential generation per environment

**Accountability & Traceability**

* All actions are logged using:

  + CloudTrail (across all regions + org-level aggregation)
  + AWS CloudWatch Logs and Security Lake for analysis
  + Optional: Amazon Detective to trace suspicious behavior
* Custom Lambda/Config Rules alert on:

  + Accounts not tied to users
  + Reused passwords or duplicate access key pairs

📋 **Possible Evidence to Collect**

* Identity Center or SAML Identity Provider configuration screenshot
* List of active IAM users showing unique, named identifiers
* IAM Credential Report (filtered to show no shared/generic users)
* CloudTrail logs showing identity attribution (e.g., `userName = john.doe`)
* Security Hub or Config Rule findings for shared credentials
* Secrets Manager access logs showing unique usage per service/app
* DevSecOps policy preventing `admin` or `shared` IAM user creation
* Incident Response documentation showing traceability to individual accounts
* SOP or policy document forbidding group/shared/generic accounts
* GitHub/GitLab pipeline configuration enforcing account naming standards

---

**HITRUST Requirement – Account Type Identification and Credential Maintenance**

Control ID: 01.b User Registration  
Control Type: Technical + Operational  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(3)(ii)(B), 164.308(a)(4)(ii)(B), 164.312(d), 164.308(a)(1)(ii)(D)

**Control Objective:**

Ensure that all account types (e.g., individual, system, application, temporary) are identified, group/role conditions are clearly defined, and shared credentials are updated promptly when membership changes.

**Technical Implementation**

**Account Type Identification**

* IAM Role tagging strategy:

  + Roles and users are tagged by type using enforced metadata (`Account_Type = "System" | "Application" | "Emergency" | "Guest"`).
  + Examples:

    - Individual: Federated Identity via IAM Identity Center (e.g., `jane.doe@company.com`)
    - Application: IAM Role for Lambda, ECS, EC2 instance profile
    - Temporary: STS AssumeRole sessions with TTL ≤ 1 hour
    - Emergency: Designated break-glass roles with `Condition`-based constraints and audit logging
* AWS Config Rules / Custom Lambda continuously enforce tagging schema and alert on unclassified identities.

**Group and Role Membership Conditions**

* IAM Identity Center or federated IdP (Okta) enforces group-based role assignments via:

  + SCIM provisioning
  + Job function mapping (`HRTitle` → `PermissionSet`)
  + Nested group access prohibited unless explicitly whitelisted
* For IAM Roles, access is managed via:

  + Trust policies scoped to expected principals
  + Tags and Conditions restricting invocation by user or environment
* Group role assumptions are logged with `CloudTrail` and reviewed quarterly.

**Credential Rotation for Shared/Group Accounts**

* Use of shared credentials is prohibited unless explicitly allowed for legacy systems or automation accounts.
* Where shared credentials must exist:

  + Credentials are stored in AWS Secrets Manager with automatic rotation enabled.
  + Secrets access is scoped via resource policies and logged.
  + Upon user removal, the relevant secret is rotated immediately via:

    - Triggered Lambda function
    - Automated ticket workflow
* IAM Access Analyzer + Config Rules detect:

  + Orphaned principals
  + Overlapping or legacy group memberships

📋 **Possible Evidence to Collect**

* IAM Role inventory with `Account_Type` tags
* Secrets Manager configuration showing credential rotation
* Sample CloudTrail logs showing assumed roles with unique session tags
* Screenshot of Identity Center / IdP SCIM-based role mapping
* Config Rule reports on untagged or misclassified roles
* SOP for emergency account creation and expiration policy
* AWS Access Analyzer finding reports
* Lambda remediation script logs for credential rotation
* Documentation on break-glass role usage
* Policy document outlining group membership criteria

---

**HITRUST Requirement – Proper Identification for Account Requests and Approval**

Control ID: 01.b User Registration  
Control Type: Operational + Technical  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(3)(ii)(B), 164.308(a)(4)(ii)(B) , 164.308(a)(1)(ii)(D) , 164.312(d)

**Control Objective:**

Ensure that the identity of users requesting and approving the creation of information system accounts is validated, logged, and follows a defined authorization process.

**Technical Implementation**

**Identity Verification for Account Provisioning**

* AWS accounts use IAM Identity Center (SSO) or SAML Federation for onboarding:

  + All access requests originate from corporate identity providers (like Okta).
  + Users must authenticate using MFA-enabled credentials before provisioning.
  + SCIM provisioning from HR system to IdP ensures identity traceability (HR + IT approval flow).
* If provisioning IAM users (discouraged):

  + Request is initiated through a ticketing system (e.g., Jira, ServiceNow).
  + Request includes user’s verified identity, business justification, and approvals.

**Approval Workflow Integration**

* Access requests are routed through automated workflows:

  + ServiceNow or Jira → Approval by manager + system owner → Identity Center or IAM account provisioning
  + Workflow captures:

    - Requestor’s identity
    - Approver’s identity
    - Timestamp
    - Role/profile requested
    - Associated risk level
* AWS Identity Center logs all permission set assignments and delegated administration changes.
* AWS CloudTrail records IAM role creation, permission changes, and user provisioning events.

**Auditing & Traceability**

* Security Hub or custom Lambda functions alert on account creation outside approved workflows.
* Regular audits ensure:

  + No accounts exist without corresponding request/approval record
  + No break-glass or test users provisioned without chain of custody

📋 **Possible Evidence to Collect**

* Sample access request ticket with user identity and approval history
* SCIM provisioning logs from IdP (e.g., Okta audit logs)
* IAM Identity Center audit trail showing who assigned access
* CloudTrail logs for user/role creation events
* ServiceNow/Jira workflow documentation and approval flow
* Identity verification SOP or policy for account requests
* IAM user creation Config Rule findings
* HR to IT provisioning policy showing identity validation and approval steps
* Sample email or signed form for emergency or exception-based account creation

---

**HITRUST Requirement – Notification and Response to Changes in User Status**

Control ID: 01.b User Registration  
Control Type: Operational + Technical  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(3)(ii)(C), 164.308(a)(3)(ii)(A), 164.308(a)(4)(ii)(C), 164.308(a)(1)(ii)(D)

**Control Objective:**

Ensure that account managers are promptly notified of user status changes (termination, transfer, access need changes) and take appropriate actions to modify or revoke system access.

### 🔧 **Technical Implementation**

**HR/IT Notification Integration**

* HR systems (e.g., Workday, BambooHR) are integrated with Identity Providers (IdPs) like Okta via SCIM:

  + Termination → triggers deactivation in IdP → triggers access removal in IAM Identity Center
  + Transfers or role changes → SCIM re-syncs updated job title/group mapping → access is re-evaluated
  + Change detection is automated using event-driven workflows (e.g., Okta Workflows, Lambda)

**Automated Account Deactivation**

* IAM Identity Center synchronizes user permissions to AWS accounts:

  + On termination, all permission sets are revoked
  + Access to AWS resources is removed instantly
  + Logs are preserved via CloudTrail and Access Analyzer
* IAM roles or access granted via `sts:AssumeRole` are audited:

  + Temporary or emergency roles (e.g., `BreakGlassSupport`) have TTL + mandatory justification
  + Shared/group access (discouraged) triggers rotation or disabling upon any membership change

**Manual Review and Oversight**

* Weekly or real-time reports are sent to account managers (e.g., Security, IT) containing:

  + Users terminated in HR but still active in AWS
  + Users who’ve changed business units or teams
  + Orphaned or stale roles not linked to current users
* IAM Access Analyzer or AWS Config Rules detect:

  + Active IAM users not used in 90 days
  + Resources accessed by users no longer in mapped roles

**Remediation**

* Lambda functions or ticket automation initiate:

  + Credential/key deactivation
  + Role revocation
  + Secret rotation (if shared access previously existed)
* SSM Automation can be triggered to:

  + Decommission EC2 or container resources tied to departing users
  + Notify SOC if activity continues post-termination

📋 **Possible Evidence to Collect**

* SCIM or HR→IdP workflow screenshots/logs
* IAM Identity Center access removal logs
* CloudTrail entries for role revocation or policy changes
* Access Analyzer reports of orphaned identities
* Weekly audit report sample (e.g., PDF or email digest)
* IAM Credential Reports showing key/console usage trends
* Termination procedure documentation with system owner responsibilities
* Ticket evidence for user offboarding actions
* SSM or Lambda script used for access revocation
* SOP for access modification on transfer or privilege change

---

**HITRUST Requirement – User Registration and Deregistration**

Control ID: 01.b User Registration  
Control Type: Operational + Technical  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(3)(ii)(A–C) , 164.308(a)(4)(ii)(C) , 164.312(a)(1), 164.312(d) , 164.308(a)(5)(ii)(C–D)

**Control Objective:**

Ensure that processes for user onboarding, access provisioning, and deregistration follow least privilege principles, include authorization controls, track access formally, and remove inactive or unnecessary accounts timely.

**Technical Implementation**

**1. Password Procedures & User Understanding**

* Federated Identity via IdP (e.g., Okta, Azure AD) enforces corporate password policy.
* Users are shown Acceptable Use Policy (AUP) or security acknowledgment via:

  + IdP prompt during first login
  + Corporate onboarding checklist

**2. Granular Access, Authorization Checks, and Approval Separation**

* Access is role-based via IAM Identity Center permission sets.

  + Mapped by job title or SCIM attributes (e.g., `Department`, `JobCode`)
  + Fine-grained access enforced using IAM policies, tags, and conditions
* Approvals are separated:

  + Request: by employee or manager
  + Review: by security or system owner
  + Enforced via ServiceNow/Jira workflows with audit trails
* Sensitive roles (e.g., `AdministratorAccess`) require risk-based approval or compensating controls (MFA, time-limited elevation)

3. User Awareness of Access Rights

* IAM Identity Center and ticketing workflows provide:

  + List of roles granted (attached permission sets)
  + Acknowledgment messages in onboarding workflows
* Access review process includes confirmation of granted access and responsibilities

**4**. Vendor/Service Provider Restrictions

* AWS IAM policies and resource-based policies ensure:

  + External roles/users must be explicitly approved
  + No access unless part of pre-approved trust relationship (e.g., `sts:AssumeRole` from trusted account)

**5. Formal Registration Record**

* SCIM provisioning logs, ticketing system, and IAM Identity Center provide:

  + Centralized record of who was onboarded and when
  + CloudTrail logs supplement with activity history

#### 6. Timely Deactivation & Inactivity Management

* Termination via HR triggers automated SCIM deprovisioning:

  + Identity removed from IdP, access removed from AWS
  + Critical access roles removed immediately
* IAM Access Analyzer + Config Rules monitor:

  + Inactive credentials (60+ days)
  + Non-critical access removed via Lambda automation within 24 hours
* IAM Credential Report used for periodic manual/automated review

📋 **Possible Evidence to Collect**

* SCIM/IdP logs of onboarding and offboarding
* Sample onboarding ticket or approval record
* Screenshot of IAM Identity Center permission sets
* CloudTrail logs for IAM and role events
* IAM Credential Report filtered for inactive users
* Config Rules finding reports:

  + `access-keys-rotated`
  + `iam-user-unused-credentials-check`
* Access Review documentation (quarterly or ad hoc)
* Policy requiring written acknowledgment of access rights
* Workflow or form template for critical/non-critical access revocation
* Lambda or SSM automation script for access cleanup
* Exception list for approved inactive accounts (e.g., service accounts)

---

**HITRUST Requirement – User Access Statement and Special Account Governance**

Control ID: 01.b User Registration  
Control Type: Operational + Technical  
Control Level: Organizational Control  
HIPAA Mapping: 164.312(d) , 164.308(a)(3)(ii)(A–C) , 164.308(a)(4)(ii)(C) ,164.308(a)(5)(ii)(C–D)

**Control Objective:**

Ensure users are informed of their access rights and responsibilities, and that all use of guest, anonymous, shared/group, emergency, and temporary accounts is specifically authorized and continuously monitored.

**Technical Implementation**

#### **1. Written Statement of Access Rights**

* IAM Identity Center shows assigned permission sets per user.
* Users receive an automated onboarding email or workflow output showing:

  + Resources they have access to
  + Their role and privilege level
* Access rights are reviewed quarterly and documented (PDF, form, or dashboard view).

#### **2. Acknowledgment of Access Conditions**

* During onboarding:

  + Corporate identity providers (Okta, Azure AD) present Acceptable Use Policies or access terms.
  + Users must digitally sign acknowledgment forms via onboarding portal (e.g., HRIS, BambooHR, ServiceNow).
* Acknowledgments are stored and referenced during access reviews and audits.

#### **3. Authorization of Special Accounts**

* Guest, shared/group, emergency, and temporary IAM users/roles must:

  + Be registered in a justification log or ticketing system
  + Include an expiration date, owner, and business justification
* Shared credentials (e.g., for CI/CD or third-party automation):

  + Managed in AWS Secrets Manager
  + Access controlled via resource-based policies
  + Access only allowed through approved roles or service accounts

#### **4. Monitoring of Special Account Usage**

* Use of these account types is continuously monitored via:

  + CloudTrail logs, with alerts triggered in Security Hub or Amazon GuardDuty
  + IAM Access Analyzer or AWS Config Rules to detect:

    - Creation or reuse of special account types
    - Unusual or unauthorized access patterns
* Emergency roles (e.g., `BreakGlassAdmin`) are:

  + Logged with CloudTrail
  + Limited to short durations via IAM session policies
  + Reviewed post-usage by the security team

📋 **Possible Evidence to Collect**

* Onboarding workflow showing user access acknowledgment
* Signed AUP/access condition statements from HR or onboarding system
* IAM Identity Center permission set summary for a sample user
* Access justification ticket for emergency/shared account
* IAM policy with expiration or access scope for special roles
* Secrets Manager configuration logs (accessed by whom, when)
* CloudTrail log for emergency role assumption
* GuardDuty alerts or findings for guest/shared account access
* Config Rule or Lambda enforcement on tag: `Account_Type` = `Shared`, `Temporary`, `Guest`, etc.
* Quarterly report of all special account usage reviewed by IT/security

---

**HITRUST Requirement – Maintain Listing of Sensitive Data Access Holders**

Control ID: 01.b User Registration  
Control Type: Operational + Technical  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(3)(ii)(A–C),164.308(a)(4)(ii)(C), 164.308(a)(1)(ii)(D)

### **Control Objective:**

Maintain an up-to-date inventory of all individuals, contractors, vendors, and business partners who have access to sensitive information (e.g., PII), ensuring visibility and accountability for authorized data access.

### **Technical Implementation**

#### **Identity Inventory and Role Mapping**

* All identities are managed via:

  + IAM Identity Center (SSO) or SAML Federation with identity providers (e.g., Okta, Azure AD)
  + SCIM provisioning from HR/contractor systems maintains up-to-date workforce population
* AWS tagging policy requires:

  + All IAM roles, users, and federated identities to be tagged with:

    - `Access_Level = "PII" | "PHI" | "Internal"`
    - `Owner`, `Department`, and `Contractor_Status`

#### **Sensitive Access Role Tracking**

* IAM roles granting access to PII-tagged resources (e.g., S3 buckets labeled `Data_Class = PII`) are tracked via:

  + AWS Config Rules
  + Resource Access Manager (RAM)
  + Service Control Policies (SCPs) for OU-wide enforcement
* Periodic exports from IAM, Identity Center, and Secrets Manager access logs are reviewed and correlated with:

  + HR roster (employees, contractors)
  + Vendor registry
  + Role assignment logs

#### **3rd Party and Business Partner Access**

* Third-party access:

  + Must go through pre-authorization and risk assessment
  + Is restricted using IAM roles with external `sts:AssumeRole`trust policies
  + All accesses are logged (CloudTrail) and flagged in Security Hub

📋 **Possible Evidence to Collect**

* Exported list of IAM roles and permission sets tagged with `Access_Level = "PII"`
* IAM Identity Center audit log showing active users and roles
* Vendor access records, including role trust relationships
* SCIM provisioning logs from IdP (showing contractors vs. employees)
* S3 bucket/resource policy mapping to roles with PII access
* Quarterly review reports of access to sensitive data
* Identity inventory spreadsheets with role, type (employee/vendor), and last access
* SOP or policy requiring tagging and registration of sensitive-data access roles

---

**HITRUST Requirement – User Registration, De-registration, and Access Verification**

Control ID: 01.b User Registration  
Control Type: Operational + Technical  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(3)(ii)(A–C) , 164.308(a)(4)(ii)(C) , 164.308(a)(1)(ii)(D) , 164.312(a)(1), 164.312(d)

**Control Objective:**

Ensure that account management processes address the full lifecycle of user accounts, including submission and authorization workflows for system and sensitive information access, and that access levels are periodically verified.

### 🔧 **Technical Implementation**

#### **1. Account Lifecycle Management (Establish, Activate, Modify, Review, Disable, Remove)**

* IAM and federated accounts (via Identity Center) follow a defined lifecycle managed through:

  + ServiceNow / Jira workflows integrated with SCIM provisioning
  + IAM Identity Center for access assignment and deprovisioning
* Modification and removal:

  + Handled via ticketing triggers or HRIS integration
  + Enforced through automatic deactivation of SCIM-linked identities
* Quarterly access reviews verify continued access need and role accuracy

  + Reports pulled from IAM, Identity Center, and CloudTrail

#### **2. System Access Request and Granting Process**

* Access to AWS systems is:

  + Requested through a formal workflow (e.g., Jira/ServiceNow)
  + Approved by manager + system owner
  + Granted via IAM Identity Center permission set mapping
* Each request logs:

  + Requestor identity
  + Purpose
  + Approval chain
  + Role assigned

#### **3. Sensitive Information Access Request and Granting**

* PII / PHI / Confidential information access is:

  + Requested with separate justification
  + Subject to data classification tagging (e.g., S3 with `Data_Class = "Confidential"`)
  + Granted via distinct IAM roles with limited permissions
* Secrets Manager, KMS, and RDS IAM Authentication are used to protect sensitive credentials and database access

#### **4. Verification of Authorization and Approvals**

* Every request must include:

  + Approval from data owner or security approver
  + Mandatory reviewer confirmation via documented workflow
* Config Rules or Lambda validations ensure:

  + All roles with elevated access have `Approved_By` tags
  + Missing or unauthorized assignments trigger remediation workflows

#### **5. Ongoing Access Verification of Sensitive Data Holders**

* Workforce access to confidential data is:

  + Reviewed quarterly against HR roster and access inventory
  + Audited using CloudTrail, Access Analyzer, and Config Rules
  + Verified with business system owners or data stewards
* IAM reports are filtered for:

  + `Access_Level = "Confidential"`
  + Activity timestamps (to detect dormant users)

📋 **Possible Evidence to Collect**

* Onboarding and offboarding workflow diagram
* Sample request + approval record for system and data access
* IAM role creation logs with attached permissions
* Identity Center assignment and audit logs
* Quarterly access review output (for sensitive-data holders)
* Config Rule snapshots showing sensitive access roles
* Policy documents outlining data classification and role sensitivity
* Tagging schema documentation: `Access_Level`, `Approved_By`, `Data_Sensitivity`
* S3 bucket policies granting or denying access to confidential data
* CloudTrail logs showing access to sensitive resources

---

### **HITRUST Requirement – Privilege Allocation for Systems and Components**

Control ID: 01.c Privilege Management  
Control Type: Technical + Operational  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(3)(ii)(B), 164.308(a)(4)(ii)(B–C) , 164.312(a)(1) , 164.308(a)(1)(ii)(D)

**Control Objective:**

Ensure all system and application privileges are allocated based on a formal, documented authorization process using the principle of least privilege and need-to-use for the user’s functional role.

🔧 **Technical Implementation**

#### **1. Formal Authorization Process for Privilege Allocation**

* Access is requested via ServiceNow, Jira, or an internal request form.
* Each request must be approved by the resource/system owner and reviewed by Security or Compliance for high-privilege roles.
* AWS Identity Center (SSO) permission sets are only assigned following documented approval.
* Break-glass or elevated privileges (e.g., `AdministratorAccess`) are only granted with:

  + Time-bound access
  + Justification
  + Logging via CloudTrail

#### **2. Mapping Access Privileges per System/Product**

* IAM policies and roles are:

  + Defined per system (e.g., EC2, RDS, KMS, S3, Lambda, IAM)
  + Documented in an internal Access Control Matrix (ACM) or Tagged using `System_Name` **and** `Privilege_Level` on roles
* Permissions for third-party SaaS (e.g., Datadog, GitHub) are managed via SCIM and mapped against job titles/functional duties.

#### **3. Identifying Users per System Needing Privileges**

* Identity Center provides a centralized view of role-to-user mapping.
* IAM roles that support cross-service/system access are labeled and tracked (e.g., `RDSReadRole`, `KMSRotator`, `AdminEC2Ops`).
* Config Rules or Lambda scripts enforce a one-to-one mapping for sensitive systems (e.g., KMS Admin → 2 people max).

#### **4. Need-to-Use + Event-Based Allocation**

* AWS Just-In-Time (JIT) Access Model:

  + Implemented using IAM Role Chaining, session-based access (STS), and access duration controls
  + Common for:

    - On-call support
    - Emergency patching
    - Sensitive data access reviews
* Automated tools like Symphony, StrongDM, or custom Lambda enforce:

  + Time-bound roles
  + Removal post-task completion
* All event-based access is:

  + Logged in CloudTrail and reviewed in quarterly audits
  + Assigned via automation tools with expiration timestamps

📋 **Possible Evidence to Collect**

* Access Control Matrix (ACM) mapping users/roles/systems
* Ticket sample showing privilege request → approval → provisioning
* Identity Center role-to-user assignment export
* IAM policy JSONs showing system/product-specific permissions
* Config Rule snapshots verifying minimal privilege and correct tags
* Lambda/JIT tool logs showing temporary role assumption
* CloudTrail entries showing sensitive role usage
* SOP for elevated access (including JIT use cases)
* Quarterly access review report
* Break-glass access approval form or audit record

---

**HITRUST Requirement – Privileged Account Authorization and Monitoring**

Control ID: 01.c Privilege Management  
Control Type: Technical + Operational  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(3)(ii)(B), 164.308(a)(1)(ii)(D), 164.312(a)(1)

**Control Objective:**

Ensure privileged access is strictly limited to an approved list of users and that such privileged role assignments are continuously tracked and monitored for misuse or drift.

🔧 **Technical Implementation**

#### **1. Limit Authorization to Privileged Accounts**

* **Privileged roles** (e.g., `AdministratorAccess`, `PowerUserAccess`, `BillingAdmin`, `IAMFullAccess`) are:

  + Predefined and managed centrally in AWS IAM Identity Center (SSO) or via IAM Roles with strict trust policies
  + Assigned only to named individuals who are on an approved privileged access list (PAL)
* Access is granted only after:

  + Manager + Security approval
  + Business justification submission via ticketing (Jira/ServiceNow)
  + Optional background check or enhanced verification (depending on role)
* **IAM policies and SCPs** explicitly restrict privilege escalation (e.g., no `iam:CreateRole` without oversight)

#### **2. Track and Monitor Privileged Role Assignments**

* Role assignments and assumptions are monitored via:

  + AWS CloudTrail – logs all `AssumeRole`, `AttachPolicy`, `CreateUser` actions
  + IAM Access Analyzer – detects overly permissive roles and cross-account risk
  + Security Hub & GuardDuty – generate alerts for:

    - Unusual privileged activity (e.g., root usage)
    - Access from unrecognized IPs or geolocations
* Privileged accounts are:

  + Tagged with `Privileged = True`
  + Reviewed quarterly through an access recertification process
  + Monitored using AWS Config Rules:

    - `iam-user-no-policies-check`
    - `iam-user-unused-credentials-check`
    - `root-account-mfa-enabled`
* Optional: Use third-party tools to enhance visibility and approval workflows for privileged access

📋 **Possible Evidence to Collect**

* Privileged Access List (PAL) maintained in GRC or IAM Identity Center
* Sample access request ticket with justification and approval
* IAM policy documents for privileged roles
* CloudTrail logs for `AssumeRole` events into privileged roles
* Security Hub findings or alerts related to privileged role usage
* IAM Access Analyzer reports on privileged access risks
* Config Rule results confirming proper privilege assignment hygiene
* Quarterly privileged access review report
* SCPs limiting privilege escalation

---

**HITRUST Requirement – Separation of Privileged and Non-Privileged User Activity**

Control ID: 01.c Privilege Management  
Control Type: Technical + Operational  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(3)(ii)(B), 164.308(a)(1)(ii)(D), 164.312(a)(1), 164.312(d)

**Control Objective:**

Ensure system administrators only use privileged accounts for administrative actions and maintain a separate account for routine or non-privileged activities.

🔧 **Technical Implementation**

#### **1. Use of Privileged Access Accounts for Admin Duties Only**

* Admin access is provisioned through:

  + IAM Identity Center roles (e.g., `AdminAccess`, `IAMManager`)
  + STS AssumeRole pattern for time-bound privileged access
* All privileged access must:

  + Be assumed explicitly and temporarily
  + Trigger CloudTrail logs, which are monitored by Security Hub
  + Be granted only for a specific purpose or support incident
* Use of the AWS root account is prohibited except under break-glass procedures and logged with CloudTrail

#### **2. Separate Standard Accounts for Non-Privileged Activities**

* Admins are required to:

  + Access AWS for general monitoring or light usage (e.g., read-only dashboards) through a non-privileged SSO role
  + Perform general internet use, email, and SaaS platform activities through a separate workstation identity (managed via IdP like Okta)
* This separation is enforced via:

  + Identity provider policies
  + Workstation OS and browser-based profiles (e.g., Chrome/Edge profiles)
  + Optional endpoint DLP or CASB controls

📋 **Possible Evidence to Collect**

* IAM Identity Center configuration showing separate standard and admin roles for sysadmins
* Sample of CloudTrail log for privileged role assumption
* Screenshot of STS `AssumeRole` or permission set assignment
* Policy document requiring use of separate accounts for admin vs. standard tasks
* Config Rule or IAM Access Analyzer evidence restricting use of persistent admin accounts
* Ticket or SOP for break-glass admin role usage
* Security awareness training records for system administrator account hygiene
* Endpoint management policy showing browser/profile separation for admin vs. non-admin accounts

---

**HITRUST Requirement – Role-Based Access Controls (RBAC)**

Control ID: 01.c Privilege Management  
Control Type: Technical  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(4)(ii)(B–C), 164.312(a)(1)

**Control Objective:**

Ensure role-based access controls are implemented such that users are assigned to one or more roles, and roles are tied to specific system functions, in accordance with least privilege principles.

🔧 **Technical Implementation**

#### **1. RBAC is Implemented**

* AWS IAM Identity Center (SSO) is used to implement centralized RBAC:

  + Each user is assigned one or more permission sets (i.e., roles)
  + Roles define system-level access via managed IAM policies
* IAM Roles are used for:

  + Application-to-application access (Lambda, EC2, ECS)
  + Human access (admin, read-only, devops, auditor)
* Roles are tagged with metadata such as:

  + `Role_Type = "ReadOnly" | "Admin" | "Support"`
  + `Function = "Billing" | "EC2 Management" | "S3 Access"`

#### **2.** Map Each User to One or More Roles

* User → Role mapping is maintained via:

  + SCIM provisioning from IdP (e.g., Okta, Azure AD)
  + Identity Center audit logs
  + Access Reviews conducted quarterly
* Mapping can also be exported via:

  + `list-account-assignments` (AWS CLI for Identity Center)
  + IAM credential report (for non-SSO accounts)

#### **3. Map Each Role to One or More System Functions**

* Each IAM role or permission set is linked to:

  + Specific AWS service actions (`ec2:DescribeInstances`, `s3:GetObject`, `kms:Encrypt`)
  + Tied to system functions, such as:

    - Instance management
    - Database read/write
    - KMS key rotation
    - Billing dashboard view
* RBAC implementation is enforced through:

  + Policy boundary documents
  + SCPs to restrict over-privileged use
  + AWS Config Rules to ensure no deviation from RBAC mappings

📋 **Possible Evidence to Collect**

* Identity Center role-to-user assignment export
* IAM policy JSONs showing specific system function permissions
* Tags on IAM roles (`Function`, `System`)
* Screenshot of SCIM group-to-role mapping
* Access Review records showing role assignment review
* Config Rules report verifying adherence to RBAC
* SOP documenting RBAC design and updates
* Crosswalk mapping of `User → Role → Permissions → Function`
* List of roles/functions by business unit/system

---

**HITRUST Requirement – Default Deny-All for Covered Information Systems**

Control ID: 01.c Privilege Management  
Control Type: Technical  
Control Level: System-Level Control  
HIPAA Mapping: 164.312(a)(1) , 164.308(a)(4)(ii)(B–C), 164.308(a)(1)(ii)(D)

**Control Objective:**

Ensure that systems storing, processing, or transmitting covered information (e.g., PHI, PII, confidential data) are configured with a default "deny-all" access control setting, requiring explicit permissions to allow access.

**Technical Implementation**

#### **Default Deny-All in AWS**

* AWS security best practice is **implicit deny by default**:

  + IAM users, roles, and groups have **no permissions unless explicitly granted**
  + Explicit `Deny` takes precedence over `Allow` in IAM and resource-based policies

#### **Covered Systems Implementation**

* For systems handling sensitive or covered data (e.g., PII, PHI):

  + **S3 buckets**, **KMS keys**, **RDS databases**, **EC2 instances**:

    - Use **resource policies** or **VPC endpoint policies** with default `Deny-All`, allowing access only to tagged, authorized roles
  + **IAM permission boundaries** and **SCPs** enforce deny-by-default on:

    - Cross-account access
    - Privileged actions (e.g., `s3:PutObject`, `kms:Decrypt`)

#### **Network-Level Deny-By-Default**

* Security Groups and NACLs:

  + Default to blocking all inbound traffic
  + Access only opened explicitly by port, protocol, and CIDR
* AWS Network Firewall or VPC Traffic Mirroring:

  + Enforce policy-based control for east-west and north-south traffic

#### **Optional Enhancements**

* **AWS Config Rules** monitor and auto-remediate resources not aligned with deny-by-default (e.g., open S3 buckets)
* Tags like `Data_Class = PII` or `Compliance = HIPAA` trigger Lambda-based enforcement logic

📋 **Possible Evidence to Collect**

* IAM policy with no default allow and explicit permissions only
* S3 bucket policy with explicit deny or no wildcard permissions
* SCPs blocking wildcard access or privilege escalation
* Security Group or NACL screenshots showing deny-by-default posture
* Config Rule snapshots (e.g., `s3-bucket-public-read-prohibited`)
* CloudTrail logs confirming no access prior to permission grant
* KMS key policy requiring explicit principal reference
* VPC endpoint policy blocking all except defined service roles

---

**HITRUST Requirement – Promote Systems That Avoid Elevated Privileges**

Control ID: 01.c Privilege Management  
Control Type: Technical + Developmental  
Control Level: Organizational + System-Level Control  
HIPAA Mapping: 164.308(a)(3)(ii)(B), 164.312(a)(1), 164.308(a)(1)(ii)(D)

**Control Objective:**

Encourage the design and implementation of system routines and applications that do not require elevated or administrative privileges, minimizing risk from privilege misuse or compromise.

### **Technical Implementation**

#### **Principle of Least Privilege in System Design**

* **Developers and DevOps teams are trained** to:

  + Avoid use of admin privileges in Lambda functions, EC2 user-data scripts, or containers
  + Leverage scoped-down IAM roles instead of `AdministratorAccess`
  + Use assume-role with limited actions, tagged per function or service
* AWS enforces least privilege defaults:

  + IAM roles for Lambda, EC2, ECS, Batch include only the exact actions required
  + IAM policy simulators and Access Analyzer help validate overly broad permissions

#### Privileged Function Avoidance in CI/CD

* Build/deployment pipelines use:

  + Dedicated service roles with minimal access
  + Role switching for temporary elevation via GitHub Actions OIDC + AWS, or CodePipeline
* Static scanning tools like:

  + `checkov`, `tfsec`, `aws-iam-lint` are used to catch excessive permissions at the IaC level

#### **Privileged Escalation Prevention**

* Use of:

  + IAM policy conditions to prevent privilege escalation (e.g., `iam:PassRole` restricted by tag)
  + Session policies for temporary sessions to restrict role elevation
  + SCPs at the AWS Organizations level to block use of wildcard (`*`) permissions or risky actions

📋 **Possible Evidence to Collect**

* Sample IAM policy granting only scoped, non-admin privileges
* Role policies for Lambda, ECS, EC2 showing non-root-level permissions
* DevSecOps SOP or training material promoting non-admin routines
* CodePipeline or GitHub Actions role assumption logs
* Access Analyzer or IAM policy simulator output with privilege reduction evidence
* SCPs and permission boundaries restricting elevation
* Config Rule findings detecting use of `AdministratorAccess`
* Security training or policy requiring least privilege programming principles

---

**HITRUST Requirement – Separation and Minimization of Elevated Privileges**

Control ID: 01.c Privilege Management  
Control Type: Technical + Operational  
Control Level: Organizational + System-Level Control  
HIPAA Mapping: 164.308(a)(3)(ii)(B), 164.312(a)(1) , 164.308(a)(1)(ii)(D)

**Control Objective:**

Ensure that elevated privileges are used only when necessary, assigned separately from standard user identities, accessed through a distinct role during each session, and their use is minimized in line with least privilege principles.

**Technical Implementation**

**1. Assign Elevated Privileges to a Different Identity**

* **Admin privileges are not assigned to users’ default identity**:

  + Standard user accounts are mapped to least-privilege roles (e.g., `ReadOnly`, `BillingView`)
  + Admin access is provided through **assume-role into elevated IAM roles**, such as `SecurityAdminRole`, `IAMManagerRole`
  + Role names and session tags clearly differentiate elevated access (e.g., `AssumedRole: j.doe-admin`)
* IAM Identity Center (SSO) or IdP integration (Okta/Azure AD) separates permission sets:

  + E.g., "UserAccessRole" for daily use, "PrivilegedRoleAccess" for elevated duties

**2. Enforce Single Role Access per Session**

* IAM Identity Center requires:

  + Selection of a single permission set (role) per session
  + Separate login events or assume-role operations for elevated access
* AWS CLI / Console access via STS AssumeRole sessions:

  + Logs role transitions in CloudTrail
  + Enforces temporary, auditable sessions rather than static credentials

**3. Minimize Use of Administrative Privileges**

* Elevated privileges are:

  + Time-limited via IAM session policies or JIT access tools
  + Provided only with business justification and approval (via Jira, ServiceNow)
  + Reviewed quarterly by security/compliance teams
* Additional enforcement includes:

  + IAM Access Analyzer to detect unused or overbroad elevated permissions
  + SCPs to restrict access to sensitive APIs like `iam:PassRole`, `kms:CreateKey`
  + Static scans of IaC (Terraform/CloudFormation) for `AdministratorAccess` policy usage

📋 **Possible Evidence to Collect**

* IAM Identity Center assignment exports showing separate permission sets
* CloudTrail logs showing STS `AssumeRole` sessions for privileged roles
* IAM role tagging policy (`Access_Type = Elevated`)
* ServiceNow/Jira ticket approving elevation for a specific user
* Quarterly access review logs showing justification and role use
* IAM policy JSON for elevated roles (narrowed by service/function)
* IAM Access Analyzer findings for privilege minimization
* SCP document restricting privilege escalation or wildcard access
* SOP describing privilege separation and session role use

---

**HITRUST Requirement – Privileged Function and Security Info Access Restrictions**

Control ID: 01.c Privilege Management  
Control Type: Technical + Operational  
Control Level: System-Level Control  
HIPAA Mapping:164.312(a)(1), 164.312(d), 164.308(a)(4)(ii)(B) , 164.308(a)(1)(ii)(D)

**Control Objective:**

Ensure access to privileged functions—whether embedded in hardware, software, or firmware—is restricted to only explicitly authorized individuals, and that access to any security-sensitive data is similarly controlled.

**Technical Implementation**

**1–3. Restrict Access to Privileged Functions in Hardware, Software, Firmware**

* Hardware (e.g., EC2 hosts, AWS-managed infrastructure):

  + Physical access is controlled by AWS and documented in AWS SOC 2, ISO 27001, and FedRAMP reports.
  + AWS Nitro System architecture isolates hypervisor access—no customer or internal admin can access firmware directly.
* Software / Utilities / Scripts:

  + Access to AWS privileged services (e.g., IAM, KMS, CloudTrail, Security Hub) is restricted via:

    - IAM policies tied to least-privilege roles
    - Permission boundaries and `Condition` clauses (e.g., deny if `aws:PrincipalTag != SecurityTeam`)
  + Scripts (e.g., Lambda, SSM documents) with elevated functions are:

    - Version-controlled (e.g., in CodeCommit or GitHub)
    - Restricted by resource-based policies
    - Deployed through CI/CD pipelines with audit trails
* Firmware / Boot-level operations:

  + AWS customers cannot access firmware-level controls on managed services (e.g., EC2 hypervisor, Nitro, EBS).
  + AWS internal controls handle firmware updates, and logs are made available under NDA if required.

#### **Restrict Access to Security-Relevant Information**

* Logs and sensitive diagnostic data (e.g., CloudTrail, GuardDuty, Config, Security Hub findings):

  + Are only accessible to explicitly authorized individuals or groups (e.g., `SecurityAuditRole`, `SecOpsViewer`)
  + IAM access is granted via:

    - Identity Center roles
    - Just-in-time STS `AssumeRole` usage for sensitive diagnostics
* Data classification tags (e.g., `Data_Type = SecurityLog`, `Confidentiality = High`) are enforced in:

  + S3 bucket policies
  + KMS key policies
  + CloudWatch log group resource policies

📋 **Possible Evidence to Collect**

* IAM policy and permission set for security diagnostic access
* CloudTrail logs showing role assumption for security tooling
* Identity Center export of who has access to KMS, CloudTrail, IAM
* Config Rule outputs: enforcement of logging and restricted diagnostics
* GuardDuty findings report with access trace
* Evidence of CI/CD deployment roles and audit trail (CodePipeline logs)
* AWS Artifact download of AWS SOC 2 or ISO 27001 with physical control mapping
* Documented role tagging: `Security_Function = True`, `Privileged_Tool = Yes`
* SOP or architecture diagram showing privileged access pathways

---

**HITRUST Requirement – Controlled Information Sharing with Business Partners**

Control ID: 01.c Privilege Management  
Control Type: Operational + Technical  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(4)(ii)(B), 164.312(a)(1), 164.308(a)(8), 164.308(b)(1)

**Control Objective:**

Ensure that business partner access authorizations align with access restrictions on shared information, and that authorized users are supported in making information-sharing decisions via manual or automated mechanisms.

**Technical Implementation**

**1. Alignment of Access Authorizations with Data Restrictions**

* AWS enforces least-privilege access for third-party users/business partners via:

  + Cross-account IAM roles with explicit trust and condition policies
  + Resource tagging + ABAC (Attribute-Based Access Control) to enforce:

    - `Data_Classification = "Confidential"`, `Data_Owner = "BusinessUnitX"`
* Sharing restrictions are embedded into:

  + S3 bucket policies with tag-based conditionals
  + KMS key policies that restrict decryption only to pre-approved roles
  + PrivateLink + VPC Endpoint policies for limiting API access to specific partners
* Data owners can verify third-party access configuration through:

  + IAM Access Analyzer
  + CloudTrail logs that show who accessed what and when

**2. Manual or Automated Decision Support for Info Sharing**

* Information sharing decisions are supported through:

  + Internal data-sharing approval workflows (e.g., Jira, ServiceNow forms for reviewing/approving external access)
  + Automated tagging & access enforcement via:

    - Lambda functions that validate tag + policy consistency
    - S3 Object Lambda for conditional access logic
  + Data owners can leverage QuickSight dashboards or Athena queries on CloudTrail/Access Logs to evaluate risk
* Optional: integration with third-party tools like Collibra, BigID, or Varonis for sensitive data access governance

📋 **Possible Evidence to Collect**

* IAM trust policy for business partner cross-account role
* S3 bucket or KMS key policies with tag-based or conditional access
* Config Rule or Lambda scripts validating tagging and access logic
* Access request/approval ticket (manual) for a data share event
* IAM Access Analyzer report showing external principal analysis
* CloudTrail logs showing access to data tagged `Confidential`
* Screenshots or exports from QuickSight/Athena sharing audit reports
* Internal SOP for data sharing requests and business partner access review
* Data-sharing agreements with conditions on usage and scope

---

**HITRUST Requirement – Periodic Review of Accounts and Privileges**

Control ID: 01.e Review of User Access Rights  
Control Type: Operational + Technical  
Control Level: Organizational Control  
HIPAA Mapping:164.308(a)(3)(ii)(B–C), 164.308(a)(4)(ii)(C), 164.308(a)(1)(ii)(D), 164.312(a)(1)

**Control Objective:**

Ensure that all accounts and their associated privileges are reviewed periodically—at least annually—to confirm their appropriateness, detect unused or overprivileged accounts, and maintain least-privilege access.

**Technical Implementation**

#### **1.** Review of All Accounts (User, Privileged, System, Shared, Seeded)

* Account types tracked include:

  + IAM users (if used)
  + IAM roles for applications, break-glass, admin, and service accounts
  + Identity Center (SSO) user assignments
  + Cross-account roles (shared/business partner use)
* Periodic (typically quarterly or annual) reviews are conducted using:

  + IAM Credential Reports
  + Access Analyzer findings
  + Identity Center exports (via `list-account-assignments`)
  + Custom dashboards built in AWS QuickSight or queried via Athena on CloudTrail/Config logs
* Seeded/system accounts (e.g., `ec2-user`, `lambda.amazonaws.com`) are tracked via:

  + Terraform, CloudFormation, or other IaC inventories
  + CMDB or DevOps pipeline logs

**2. Review of Privileges (User-to-Role and User-to-Object Assignments)**

* All user-to-role and role-to-resource mappings are reviewed for:

  + Excessive privileges
  + Orphaned access
  + Violation of segregation of duties (SoD) policies
* Tools used may include:

  + IAM Policy Simulator
  + Config Rules (e.g., `iam-user-unused-credentials-check`, `iam-policy-no-statements-with-admin-access`)
  + AWS Access Analyzer
* Manual or automated review workflows (via ServiceNow, Jira, GRC platform) document:

  + Reviewer identity
  + Justification to retain or remove access
  + Risk or exceptions noted

📋 **Possible Evidence to Collect**

* Quarterly or annual access review reports (PDF or CSV export)
* IAM Credential Report showing user activity and keys
* Access Analyzer results or IAM policy validation output
* Identity Center role assignment audit logs
* Privileged access listing (e.g., list of users with `AdministratorAccess`)
* Review sign-off tickets or GRC workflows showing manager/system owner approval
* CloudTrail access logs for inactive accounts
* List of IAM roles with last assumed timestamps
* Config Rule compliance status for privilege checks
* SOP for access review frequency and method

---

**HITRUST Requirement – Maintain List of Authorized Users of Information Assets**

Control ID: 01.e Review of User Access Rights  
Control Type: Operational + Technical  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(3)(ii)(B), 164.308(a)(4)(ii)(C), 164.312(a)(1) – Access control

**Control Objective:**

Ensure a current and documented list is maintained of all individuals who are authorized to access information assets, for accountability and access governance purposes.

**Technical Implementation**

#### **Identity Inventory for Authorized Access**

* AWS uses IAM Identity Center (SSO) or federated identity providers (Okta, Azure AD) to:

  + Maintain a live, queryable list of users mapped to AWS accounts and permission sets
  + Automatically provision and deprovision access via SCIM sync from HR systems
* Authorized user-to-asset mapping is maintained by:

  + Tags on IAM roles/resources (`Asset_Owner`, `Asset_Type`, `Confidentiality_Level`)
  + Crosswalk between roles and protected information assets (e.g., S3 buckets with PHI)
* Authorized users of critical systems (e.g., KMS, S3, CloudTrail) are tracked using:

  + Access Analyzer reports
  + QuickSight dashboards built from CloudTrail logs
  + Athena queries for `AssumeRole`, `PutObject`, `Decrypt` actions

#### **Documentation and Review**

* The list of authorized users is:

  + Stored as an exportable artifact (e.g., Identity Center CSV or GRC report)
  + Reviewed quarterly or annually by data owners or system owners
  + Version-controlled or retained in GRC tools (Vanta, Drata, Archer, etc.)
* Changes to authorized user lists are tied to:

  + Onboarding/offboarding workflows in ServiceNow/Jira
  + Automated notifications to compliance teams for privilege escalation or admin role assignment

📋 **Possible Evidence to Collect**

* IAM Identity Center export of active user-to-permission set mappings
* IAM roles with tag metadata linking them to specific assets
* Screenshot or CSV of crosswalk table: `User → Role → Information Asset`
* Access Analyzer summary of active access per sensitive resource
* CloudTrail or Athena report of actual access actions by user
* Sample access review sign-off for a key system (e.g., S3 buckets storing PII)
* ServiceNow/Jira tickets for access approvals
* Documentation of the identity governance process and its integration with HR systems

---

**HITRUST Requirement – 60- and 90-Day Review of Accounts and Privileged Access**

**Control ID:** 01.e Review of User Access Rights  
**Control Type:** Operational + Technical  
**Control Level:** Organizational Control  
**HIPAA Mapping:** 164.308(a)(3)(ii)(B), 164.308(a)(4)(ii)(C), 164.308(a)(1)(ii)(D), 164.312(a)(1)

**Control Objective:**

Ensure that all user accounts and access authorizations are reviewed at least every 90 days, while critical system accounts and special privileged access rights are reviewed every 60 days, to maintain least privilege and reduce risk of unauthorized access.

**Technical Implementation**

**90-Day Review (General Accounts and Access Authorizations)**

* Applies to:

  + All IAM users and roles
  + IAM Identity Center (SSO) permission set assignments
  + Third-party/vendor access roles
* Review performed using:

  + IAM Credential Reports (for user activity and key usage)
  + Access Analyzer (for unused or overprivileged roles)
  + Config Rules like:

    - `iam-user-unused-credentials-check`
    - `iam-policy-no-statements-with-admin-access`
  + Exported user-to-role mappings from Identity Center (`list-account-assignments`)
* Change control tracked in:

  + ServiceNow, Jira, or GRC tools (Vanta, Drata, OneTrust)

**60-Day Review (Critical and Privileged Accounts)**

* Applies to:

  + Roles with `AdministratorAccess`, `IAMFullAccess`, `KMSFullAccess`, or `Billing`
  + Critical system accounts (e.g., EC2 automation roles, break-glass accounts)
* Tracked using:

  + Tagged IAM roles: `Access_Level = "Privileged"`, `Critical_Account = True`
  + Custom Athena queries on CloudTrail (e.g., role assumption or creation logs)
  + Periodic manual reviews or automated reports triggered every 60 days
* Alerts set up via:

  + Security Hub or Config Rules for changes to privileged roles
  + AWS Lambda functions to detect stale or dormant privileged access

📋 **Possible Evidence to Collect**

* 90-day and 60-day access review logs (CSV, PDF, GRC export)
* IAM Credential Report showing inactive users/keys
* Access Analyzer reports on overbroad or unused privileges
* CloudTrail logs for privileged role assumption
* Tags on IAM roles indicating `Privileged = True` or `Critical_Account = True`
* Sample Jira/ServiceNow ticket documenting access change reviews
* SOP documenting 60-/90-day review cycles and assigned reviewers
* Identity Center export showing user-to-permission set mappings
* Config Rule compliance snapshots for IAM review policies

---

**HITRUST Requirement – Review of Access Rights Following Personnel Events**

Control ID: 01.e Review of User Access Rights  
Control Type: Operational + Technical  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(3)(ii)(B–C), 164.308(a)(4)(ii)(C), 164.312(a)(1)

**Control Objective:**

Ensure user access rights are reviewed and updated immediately following promotions, demotions, terminations, or transfers to reflect their new responsibilities and prevent unauthorized access.

**Technical Implementation**

#### **Triggered Access Reviews Based on HR Events**

* AWS access is linked to HRIS platforms (e.g., Workday, BambooHR) via SCIM + Identity Provider (Okta, Azure AD)
* For:

  + Promotions – users are moved to new Identity Center permission sets
  + Demotions – existing roles are revoked and downgraded upon manager/system owner approval
  + Terminations – trigger automatic SCIM deprovisioning, revoking all AWS access
  + Transfers – initiate a review workflow to reassign roles/permissions per the new function

**Technical Enforcement Mechanisms**

* IAM Identity Center syncs with IdP:

  + New job codes or org unit changes re-map users to appropriate permission sets
* Config Rules or Lambda functions monitor for:

  + Users with access that doesn’t match their business unit tag
  + Privileged access retained after role change
* ServiceNow or Jira ticketing used for:

  + Role reassignment workflow approvals
  + HR change notifications linked to IT access review triggers

#### **Audit and Recertification**

* Managers and system owners review:

  + Role assignments and CloudTrail logs for anomalous access after personnel changes
  + Access reviews occur within 24–48 hours of event for terminations and within a week for promotions/transfers

📋 **Possible Evidence to Collect**

* SCIM provisioning logs with access changes triggered by HR updates
* IAM Identity Center assignment logs showing role updates by job title
* Sample Jira/ServiceNow ticket documenting transfer or promotion access changes
* CloudTrail logs showing account deactivation after termination
* Config Rule compliance checks on post-change role alignment
* Quarterly access review reports listing users by status change
* Policy or SOP outlining timing and process for access right review after job changes
* Workflow automation logic for transfer access reassignment

---

**HITRUST Requirement – Protection of Covered or Critical Business Information**

Control ID: 01.h Clear Desk and Clear Screen Policy  
Control Type: Physical + Operational  
Control Level: Organizational + Facility-Level Control  
HIPAA Mapping:164.310(b), 164.310(c), 164.310(d)(1), 164.312(a)(1)

**Control Objective:**

Ensure that physical and procedural safeguards protect covered or critical business information, including proper handling of documents, physical workstations, and inter-office transport of sensitive data.

**Technical & Physical Implementation**

#### **1.** Locking Away Covered or Critical Business Information

* AWS Shared Responsibility Model: Physical security of AWS-managed data centers is covered by AWS and verified through:

  + SOC 2 Type II, ISO 27001, and FedRAMP certifications
  + Physical access is controlled via biometric scanners, surveillance, and security personnel
* For customer-controlled environments:

  + Information stored on local devices or printed documents must be locked in secure filing cabinets, safes, or badge-controlled rooms
  + Documented via internal security policies or audit logs (e.g., physical key sign-out logs)

#### 2. Workstation Protection

* Organizational workstations are configured to:

  + Auto-lock when idle using GPO (Windows) or MDM (Mac/Linux)
  + Enforce full-disk encryption, password-protected login, and screen lock timeouts
  + Optional: Use Yubikey or smart card authentication
* AWS Console access:

  + Requires MFA
  + Session timeout enforced via IdP or Identity Center configuration
  + Logged via CloudTrail and Security Hub

#### 3. Secure Handling of Printed Documents

* Sensitive prints are:

  + Controlled using badge-release printers
  + Removed immediately by users per company policy
  + Logged by print management solutions (e.g., PaperCut, PrinterLogic)
* AWS customer environments are expected to:

  + Prohibit the printing of PII/PHI unless operationally necessary
  + Enforce print policies through endpoint controls and security training

#### 4. Concealing Confidential Documents in Transit

* Sensitive information transported between departments or buildings must:

  + Be enclosed in opaque envelopes or sealed folders
  + Be labeled with confidentiality markings (e.g., "Internal Use Only")
  + Avoid open delivery unless via secure inter-office mail systems
* AWS alternatives:

  + Sensitive file sharing occurs via encrypted channels only (e.g., S3 presigned URLs, AWS Transfer Family with TLS)
  + All access is logged, and KMS encryption protects data at rest and in transit

📋 **Possible Evidence to Collect**

* Physical security policy requiring locked storage of paper records
* Workstation configuration profiles enforcing auto-lock and login protection
* Screenshot of MDM enforcement (e.g., Jamf, Intune, Kandji)
* Print management logs showing release/print timestamp per user
* SOP for inter-office transport of documents with sensitive labels
* Security awareness training logs highlighting physical document handling
* AWS Artifact reports (SOC 2, ISO 27001) for AWS physical security controls
* AWS CloudTrail logs showing MFA use and session timeouts

---

**HITRUST Requirement – Remote Access by Vendors and Business Partners**

Control ID: 01.j User Authentication for External Connections  
Control Type: Technical + Operational  
Control Level: Organizational Control  
HIPAA Mapping: 164.308(a)(3)(ii)(B), 164.308(a)(4)(ii)(B), 164.312(a)(1), 164.308(b)(1)

**Control Objective:**

Ensure that remote access by vendors or business partners is disabled by default and only granted with explicit management approval. Remote access must be promptly deactivated after use.

**Technical Implementation**

**1. Remote Access Is Disabled Unless Explicitly Authorized**

* **Vendor access is disabled by default** through:

  + **IAM deny-by-default** posture (no access unless granted via trust policy or Identity Center assignment)
  + Cross-account role assumption allowed only when:

    - **Explicit trust relationship is defined**
    - `Condition` includes `StringEquals` for `aws:PrincipalOrgID` or vendor tags
* Management approval for access is enforced by:

  + Creating access request tickets in ServiceNow, Jira, or GRC tools
  + Assigning short-lived permission sets (via IAM Identity Center) or temporary IAM roles
* Access is logged via:

  + CloudTrail
  + GuardDuty (for anomaly detection)
  + Security Hub (for alert correlation)

#### **2. Vendor Access Is Deactivated Immediately After Use**

* Temporary access is time-bound using:

  + **STS** `AssumeRole` **sessions** with TTL (15 mins to 1 hour)
  + IAM roles with scheduled expiration via Lambda cleanup scripts
  + Access expiration tags (e.g., `Access_Expiry: 2025-07-08`) monitored by AWS Config Rules
* After completion:

  + Role access is disabled or deleted
  + SSO permission sets are removed
  + Alerts are triggered if access remains beyond approved time

📋 **Possible Evidence to Collect**

* Sample cross-account IAM role trust policy with vendor restrictions
* ServiceNow or Jira ticket showing management approval for vendor access
* CloudTrail logs showing AssumeRole events with vendor identity
* Screenshot of temporary IAM role assignment with TTL
* Lambda or automation script for deactivating vendor access post-use
* AWS Config Rule output for expired or unauthorized vendor roles
* GuardDuty findings related to vendor account behavior
* SOP requiring vendor access approval + immediate revocation policy
* Identity Center audit logs showing permission removal timestamps

---

**HITRUST Requirement – Remote Access Authentication and Control**

Control ID: 01.j User Authentication for External Connections  
Control Type: Technical + Operational  
Control Level: Organizational + Network Control  
HIPAA Mapping:164.312(d), 164.312(a)(1), 164.308(a)(3)(ii)(B), 164.308(a)(1)(ii)(D)

**Control Objective:**

Ensure that remote users (including vendors) authenticate through cryptographically secure mechanisms, that access is tightly managed, and that all access is both authorized and logged.

**Technical Implementation**

#### **1. Authentication via VPN or Cryptographic-Based Technique**

* Remote users authenticate using:

  + AWS Client VPN with mutual TLS + IAM Identity Center SSO + MFA
  + AWS Site-to-Site VPN or Direct Connect for dedicated, high-assurance connections
  + Hardware tokens / U2F (e.g., YubiKeys) for console or IdP-based access
* Encryption enforced via:

  + TLS 1.2 or higher
  + AWS KMS for encrypting sensitive config credentials and session tokens

#### **2. Managed Access Control Points**

* Access is restricted via:

  + Bastion hosts (jump boxes) or AWS Systems Manager Session Manager
  + NACLs and Security Groups scoped to known IPs and roles
  + Zero Trust VPN endpoints and policy-based access (e.g., based on tags or IAM role)

#### **3. Vendor Access Authentication**

* Vendors use:

  + Federated user IDs via SAML with scoped permissions
  + OR are temporarily provisioned IAM roles with unique identifiers (e.g., `vendor_abc_role`)
  + Access granted only after management approval (logged in Jira/ServiceNow)
* Authentication always occurs via standard methods:

  + IAM Identity Center, SAML, or IAM credentials with MFA

#### **4. Access is Authorized**

* Access is:

  + Provisioned through workflow (ServiceNow, Jira, HR onboarding system)
  + Reviewed by security or system owner
  + Bound to job function via IAM role or permission set

#### **5. Access is Logged**

* All access events are logged in : AWS CloudTrail, VPC Flow Logs, AWS Client VPN logs (if used), AWS Systems Manager Session Manager logs (CloudWatch).
* Optional: Enable Amazon Security Lake to centralize access logs and analytics

📋 **Possible Evidence to Collect**

* AWS Client VPN configuration with mTLS + SSO setup
* IAM Identity Center audit logs showing vendor access
* Screenshot of Session Manager activity log
* CloudTrail entries for role assumption, login, and session actions
* ServiceNow or Jira ticket approving vendor remote access
* Sample IAM policy for vendor role
* Config Rule compliance showing least privilege and session duration
* VPC security group and NACL configs showing restricted ingress
* Policy requiring use of MFA and encrypted VPN connections

---

**HITRUST Requirement – Prevent Unanticipated Dial-Up Access**

Control ID: 01.j User Authentication for External Connections  
Control Type: Technical  
Control Level: System + Infrastructure  
HIPAA Mapping: 164.312(a)(1) – Access Control, 164.312(b) – Audit Controls

**Control Objective:**

Ensure that installed infrastructure does not expose unapproved or insecure remote connectivity mechanisms such as dial-up modems or out-of-band communications that bypass standard access controls.

**Technical Implementation**

#### **1**. Preventing Unanticipated Dial-Up Capabilities in AWS

* AWS-native services do not support legacy dial-up protocols like PPP or modem-based access; infrastructure components (EC2, VPC, etc.) are inherently modern and IP-based.
* As part of baseline hardening and secure configuration:

  + Systems Manager Inventory + Patch Manager is used to detect unauthorized software or device drivers that might emulate dial-up functionality.
  + Config Rules and AWS Inspector scan EC2 and hybrid (on-prem) instances for unusual or outdated hardware emulation (e.g., legacy COM port drivers).
  + AWS Config Rules can trigger alerts for:

    - Unknown device types
    - Non-standard ports (e.g., ports 1723 or 23)
    - Outbound connections to legacy telco endpoints

#### 2. Hybrid/On-Prem Equipment Monitoring

* If using hybrid environments via AWS Outposts or Snowball Edge, monitoring includes:

  + Validating that network interfaces and firmware don’t support dial-up fallback modes
  + Running custom Config conformance packs to verify device compliance (no modems, no legacy AT commands support)
* AWS Security Hub + Amazon GuardDuty flags any unusual remote connectivity behavior or traffic to suspicious endpoints.

📋 **Possible Evidence to Collect**

* Systems Manager Inventory reports: No dial-up capable device drivers
* Config Rule output: No legacy communication stack (e.g., PPP) in use
* Security Hub finding reports: No anomalous outbound traffic
* Custom Lambda or Inspector rule results on EC2 instances
* Approved baseline configuration documents for instance images (AMI)
* GuardDuty/CloudTrail events showing blocked legacy port/protocol usage

---

**HITRUST Requirement – Remote User Authentication Uses MFA**

Control ID: 01.j User Authentication for External Connections  
Control Type: Technical  
Control Level: System-Level  
HIPAA Mapping: 164.312(d), 164.312(a)(2)(iii), 164.308(a)(5)(ii)(D)

**Control Objective:**

Ensure that all remote user access is authenticated using strong multi-factor authentication (MFA), combining passwords or passphrases with at least one additional secure method (e.g., biometrics, tokens, certificates).

### **Technical Implementation**

#### **1.** AWS IAM Identity Center (formerly AWS SSO)

* MFA enforced for all remote access to AWS environments:

  + Something the user knows: Password or passphrase
  + Something the user has: TOTP-based MFA (e.g., Google Authenticator), hardware token (e.g., YubiKey), or biometric auth if federated (Okta, Azure AD)

#### **2.** AWS IAM MFA Requirements

* Console access requires MFA:

  + Enforced via IAM policies or Service Control Policies (SCPs) in AWS Organizations
* CLI/API access:

  + Session tokens via STS must be requested using MFA credentials
  + Can enforce with condition keys like `aws:MultiFactorAuthPresent`

#### **3.** VPN & Remote Access Tools

* AWS Client VPN or third-party VPN:

  + Must support mutual TLS authentication + certificate-based access
  + Can optionally integrate with Identity Center for federated MFA
* AWS Systems Manager (Session Manager):

  + Uses IAM roles + MFA enforcement
  + Access logged via CloudTrail and optionally authorized only with `RequireMFA` conditions

📋 **Possible Evidence to Collect**

* IAM Policy requiring MFA (with `aws:MultiFactorAuthPresent`)
* MFA enforcement setting in IAM Identity Center or AWS SSO
* Screenshot or config of Client VPN profile showing certificate + MFA auth
* GuardDuty or CloudTrail logs showing MFA-enabled login events
* SCP configuration restricting access to only MFA-authenticated roles
* Device enrollment records for hardware/software tokens
* Training records for password/MFA use by workforce

---

**HITRUST Requirement – Review of Vendor User IDs**

Control ID: 01.j User Authentication for External Connections  
Control Type: Administrative  
Control Level: Moderate  
HIPAA Mapping:164.308(a)(3)(ii)(B), 164.312(a)(1)

🎯 **Control Objective**

Ensure that vendor access to information systems is periodically reviewed to confirm that access remains necessary and appropriate.

**Technical Implementation**

The organization ensures:

1. User IDs assigned to vendors are reviewed in accordance with the organization’s access review policy, and at a minimum, annually.

This review includes validating:

* whether the vendor user ID is still required,
* if access levels are appropriate, and
* whether access should be modified or revoked.

📋 **Possible Evidence to Collect**

* Access review logs for vendor accounts
* Policy document outlining frequency and scope of access reviews
* Completed access review reports or attestations
* Email records or tickets showing vendor access validation
* Account deactivation logs

---

**HITRUST Requirement – Node Authentication for Remote User Groups**

Control ID: 01.j User Authentication for External Connections  
Control Type: Technical  
Control Level: Moderate  
HIPAA Mapping: 164.312(d), 164.308(a)(5)(ii)(D)

🎯 **Control Objective**

Support secure authentication for groups of remote users by leveraging node-based methods when individual user authentication is not practical.

**Technical Implementation**

Node authentication, including cryptographic techniques (e.g., machine certificates):

1. Can serve as an alternative means of authenticating groups of remote users when they are connected to a secure, shared computer facility.

This is typically applicable in environments such as shared terminals or kiosks within a trusted network zone, where the endpoint’s identity can be validated as a proxy for the users.

📋 **Possible Evidence to Collect**

* Configuration files showing implementation of machine certificate authentication
* Security architecture diagrams illustrating node authentication
* Policies detailing when node authentication is permitted
* Logs of certificate issuance and usage
* Remote access rules referencing node-based access validation

---

**HITRUST Requirement – Wireless Access Authentication**

Control ID: 01.j User Authentication for External Connections  
Control Type: Technical  
Control Level: Moderate  
HIPAA Mapping: 164.312(d), 164.312(c)(1) , 164.312(a)(2)(iii)

🎯 **Control Objective**

Ensure secure access to systems containing sensitive information over wireless networks by enforcing authentication of both the user and the device.

**Technical Implementation**

The organization protects wireless access to systems containing sensitive information by:

1. Authenticating users – through centralized identity providers (e.g., Active Directory, RADIUS, SAML, or MFA solutions).
2. Authenticating devices – using MAC address filtering, device certificates (e.g., IEEE 802.1X/EAP-TLS), or mobile device management (MDM) enforcement.

This dual-authentication model helps ensure that both the user identity and the endpoint device are trusted before granting access to sensitive data via wireless connections.

📋 **Possible Evidence to Collect**

* Wireless access control policies
* WLAN controller configurations (e.g., 802.1X, WPA2-Enterprise logs)
* Authentication logs showing user/device ID pairings
* Certificates issued to devices for wireless access
* Screenshots of MDM policies enforcing device identity
* Access point security settings (SSID configuration, VLAN tagging, encryption settings)

---

**HITRUST Requirement – Remote Access Authentication**

Control ID: 01.j User Authentication for External Connections  
Control Type: Technical  
Control Level: Moderate  
HIPAA Mapping: 164.312(d) , 164.312(a)(1) , 164.312(e)(1)

🎯 **Control Objective**

Ensure that remote access to business information over public networks is strictly controlled through proper identification and authentication mechanisms.

🛡️ **Technical Implementation**

Remote access to business information across public networks:

1. Only takes place after successful identification and authentication of the user, using centralized authentication services.

Typical implementations include:

* VPN with multi-factor authentication (MFA)
* Zero Trust Network Access (ZTNA) or software-defined perimeter controls
* TLS client authentication
* SSO solutions integrated with access gateways or remote desktops

These safeguards ensure that only authenticated individuals can access systems remotely, protecting business data in transit and at rest.

📋 **Possible Evidence to Collect**

* VPN configuration showing authentication requirements
* Authentication logs (successful remote login events)
* Access control policy for remote users
* MFA logs or screenshots showing enforcement
* Security gateway configuration screenshots
* Remote access training logs and user provisioning records

---

**HITRUST Requirement – Remote Access Monitoring and Control**

Control ID: 01.j User Authentication for External Connections  
Control Type: Technical  
Control Level: Moderate  
HIPAA Mapping:164.312(b), 164.312(a)(1)

🎯 **Control Objective**

Ensure the organization actively monitors and controls all remote access methods to maintain the confidentiality, integrity, and availability of information systems.

🛡️ **Technical Implementation**

The organization’s information system:

1. **Monitors** all remote access methods, capturing logs of remote sessions, including source IPs, user identities, session durations, and activities.
2. **Controls** remote access by enforcing access rules, time-of-day restrictions, device compliance policies, and network segmentation.

Common tools and techniques:

* SIEM tools for logging and alerting on remote access patterns
* Conditional access policies based on user/device/risk posture
* Remote session timeout and re-authentication settings
* Geo-blocking or region-specific controls for added protection

📋 **Possible Evidence to Collect**

* Audit logs showing remote access events
* VPN/session monitoring reports from SIEM or firewall logs
* Access control configuration screenshots
* Policy documents governing remote access methods
* Alerts and notifications tied to remote session anomalies

---

**HITRUST Requirement – Secure Remote Administration**

Control ID: 01.j User Authentication for External Connections  
Control Type: Technical  
Control Level: Moderate  
HIPAA Mapping:164.312(a)(1) – Access Control, 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Ensure remote administration of systems is conducted securely to prevent unauthorized access, interception, or compromise.

🛡️ **Technical Implementation**

Remote administration sessions are:

1. **Authorized** through role-based access control (RBAC), ensuring only approved personnel can initiate remote admin access.
2. **Encrypted** using secure protocols such as SSH, TLS, or IPsec to protect session data in transit.
3. **Hardened with additional security** such as MFA, jump boxes, bastion hosts, IP whitelisting, or time-limited session tokens.

Additional controls may include:

* Restricting admin access to VPN or trusted network zones
* Logging and alerting on privileged activity
* Session recording for audit and review

📋 **Possible Evidence to Collect**

* Access control lists showing authorized admin users
* System configurations or logs demonstrating encryption protocols (e.g., SSH logs)
* MFA or bastion host configurations
* Remote administration security policy
* SIEM reports capturing administrative session activity

---

**HITRUST Requirement – Eliminate Unnecessary Services**

Control ID: 01.l Remote Diagnostic and Configuration Port Protection  
Control Type: Technical  
Control Level: Moderate  
HIPAA Mapping:164.310(c) – Workstation Security, 164.312(a)(1) – Access Control

🎯 **Control Objective**

Ensure that only business-essential ports, services, and applications are enabled to reduce the attack surface of information systems.

🛡️ **Technical Implementation**

Ports, services, and applications that are not explicitly required for business functionality:

1. Are disabled or removed during system hardening and provisioning.
2. Reviewed regularly as part of configuration management and vulnerability assessments.
3. Are tracked using secure baseline images and validated against CIS Benchmarks or STIGs.
4. Automated scripts or configuration management tools (e.g., Ansible, Chef, Terraform, or AWS Systems Manager) may be used to enforce compliance.

Common examples:

* Disabling Telnet, FTP, SMBv1, and unnecessary web services
* Removing default applications on Linux/Windows servers
* Restricting outbound application traffic with firewall rules

📋 **Possible Evidence to Collect**

* System hardening checklists
* Configuration baselines showing disabled services
* Screenshots or exported settings from `netstat`, `services.msc`, or `systemctl`
* Results from vulnerability scans highlighting closed/filtered ports
* CMDB or configuration management platform records
* Documentation or policy mandating service minimization

---

**HITRUST Requirement – Secure Diagnostic and Configuration Interfaces**

Control ID: 01.l Remote Diagnostic and Configuration Port Protection  
Control Type: Physical & Technical  
Control Level: Moderate  
HIPAA Mapping: 164.310(a)(1) – Facility Access Controls, 164.312(a)(1) – Access Control

🎯 **Control Objective**

Prevent unauthorized access to diagnostic and configuration interfaces by enforcing physical and procedural controls.

**Technical & Physical Implementation**

Controls for access to diagnostic and configuration ports:

1. Include the use of physical locks (e.g., key lock mechanisms) on ports or chassis to prevent tampering.
2. Supporting procedures are implemented to ensure:

   * Access to such ports is only provided under documented arrangements between the IT service manager and hardware/software support personnel.
   * Ports are either disabled or protected when not in use.
   * Logs or physical sign-out records are maintained for access.

This applies to routers, firewalls, servers, and any devices with physical interfaces for maintenance.

📋 **Possible Evidence to Collect**

* Photographic evidence of physical key locks
* SOPs detailing access arrangements to diagnostic/config ports
* Access request forms or change management records for support access
* Visitor logs or escorted access records for on-site maintenance
* Asset security policy referencing these procedures

---

**HITRUST Requirement – Periodic Review of Functions and Services**

Control ID: 01.l Remote Diagnostic and Configuration Port Protection  
Control Type: Technical  
Control Level: Moderate  
HIPAA Mapping:164.308(a)(1)(ii)(A) – Risk Analysis, 164.308(a)(1)(ii)(B) – Risk Management, 164.312(a)(1) – Access Control

🎯 **Control Objective**

Ensure that only required and secure services, ports, and protocols are active on systems by conducting regular reviews and deactivating any that are unnecessary or insecure.

### 🛡️ **Technical Implementation**

The organization:

1. Reviews all information systems at least once every 365 days to identify:

   * Unused or legacy services and ports
   * Non-secure or deprecated protocols (e.g., Telnet, FTP)
   * Misconfigured or risky functions (e.g., debug mode, SNMP v1)
2. Disables or removes the identified services unless explicitly required and justified.

These reviews are often driven by asset management tools, vulnerability scans, configuration management databases (CMDB), or manual server/application configuration checks.

📋 **Possible Evidence to Collect**

* Audit logs of annual port/protocol reviews
* Ticketing system entries showing remediation or deactivation
* Vulnerability scan results highlighting insecure services
* System baseline configurations pre/post review
* Change control documentation for service modifications

---

**HITRUST Requirement – Unauthorized Software Control**

Control ID: 01.l Remote Diagnostic and Configuration Port Protection  
Control Type: Technical  
Control Level: Moderate  
HIPAA Mapping: 164.308(a)(1)(ii)(A) – Risk Analysis, 164.308(a)(1)(ii)(B) – Risk Management, 164.312(b) – Audit Controls

🎯 **Control Objective**

Prevent unauthorized or malicious software from executing on organizational systems by defining, enforcing, and regularly updating control measures.

**Technical Implementation**

The organization:

1. Identifies unauthorized software through automated tools such as endpoint detection and response (EDR), antivirus, or software asset management systems.
2. Enforces an allow-all, deny-by-exception policy, using application control tools (e.g., Microsoft AppLocker, CrowdStrike, SentinelOne) to prevent unauthorized software execution.
3. Reviews and updates the list of unauthorized software at least annually, adjusting for new threats, software inventory changes, and evolving business requirements.

This policy applies to workstations, servers, cloud-based assets, and virtualized environments.

📋 **Possible Evidence to Collect**

* Software inventory and comparison logs
* List of unauthorized software and last review timestamp
* Policy or configuration of deny-by-exception enforcement
* Endpoint security reports showing block events
* Audit trails or SIEM alerts related to unauthorized software attempts

---

**HITRUST Requirement – Disabling Unnecessary/Non-Secure Protocols**

Control ID: 01.l Remote Diagnostic and Configuration Port Protection  
Control Type: Technical  
Control Level: Moderate  
HIPAA Mapping:164.308(a)(1)(ii)(A) – Risk Analysis, 164.312(a)(1) – Access Control

🎯 **Control Objective**

Reduce the risk of unauthorized data access and lateral movement by disabling unnecessary or insecure communication protocols, such as Bluetooth and peer-to-peer networking.

🛡️ **Technical Implementation**

The organization:

1. Identifies unnecessary or non-secure protocols such as Bluetooth, AirDrop, Infrared, or P2P (e.g., BitTorrent) based on environment and risk profile.
2. Disables these protocols across applicable systems via group policy objects (GPOs), mobile device management (MDM), or configuration management tools (e.g., Intune, JAMF, AWS Systems Manager, or Chef).
3. Ensures technical enforcement through host-based firewalls, registry settings, kernel modules, or system preferences.
4. Applies configuration baselines during device provisioning and monitors deviations through continuous compliance tools or periodic audits.

This is enforced across laptops, desktops, mobile devices, servers, and virtual machines handling covered or sensitive information.

📋 **Possible Evidence to Collect**

* Screenshot or export of GPO/MDM profiles disabling Bluetooth or AirDrop
* AWS Systems Manager compliance status (for EC2s)
* Mobile compliance policy logs (from MDMs like Intune or Kandji)
* Endpoint logs or firewall rules showing protocol restrictions
* Written policy specifying disallowed protocols

---

**HITRUST Requirement – Account Lockout Controls**

**Control ID:** 01.p Secure Log-on Procedures  
**Control Type:** Technical  
**Control Level:** Moderate  
**HIPAA Mapping:** 164.308(a)(5)(ii)(C) – Log-in Monitoring, 164.312(a)(1) – Access Control

🎯 **Control Objective**

Prevent brute-force login attacks and unauthorized access attempts by enforcing account lockout after a defined number of failed login attempts.

🛡️ **Technical Implementation**

The organization:

1. **Documents a formal policy** defining account lockout thresholds (e.g., 5 failed login attempts), lockout duration (e.g., 15 minutes), and conditions for reset (manual or automatic).
2. **Enforces the policy** via technical controls across all applicable systems, including:

   * Active Directory Group Policy (Windows)
   * PAM/SSSD or `pam_tally2` (Linux/Unix)
   * Identity providers (e.g., Okta, Azure AD, AWS IAM, Duo, etc.)
3. Applies the policy to **interactive logins, remote access, and web-based application login pages** that are within the system boundary.
4. Continuously **monitors lockout events** using SIEM tools and correlates failed login attempts to detect anomalies or brute-force attacks.

📋 **Possible Evidence to Collect**

* Screenshot or config export from AD GPO or `/etc/pam.d/system-auth`
* Lockout policy settings in Okta or Azure AD
* IAM policy or guardrail documentation (e.g., SCPs in AWS)
* Logs from SIEM showing lockout events
* Policy document describing thresholds and reset logic

---

**HITRUST Requirement – Unique User ID Assignment**

**Control ID:** 01.q User Identification and Authentication  
**Control Type:** Technical / Administrative  
**Control Level:** Moderate  
**HIPAA Mapping:** 164.312(a)(1) – Access Control, 164.312(a)(2)(i) – Unique User Identification

🎯 **Control Objective**

Ensure that all user activity on the information system can be traced to a specific, named individual to maintain accountability and enable audit readiness.

🛡️ **Technical and Administrative Implementation**

The organization ensures:

1. **Every user ID** (including non-privileged, privileged, seeded, and service accounts) is **uniquely assigned** to an individual whose identity is verified and recorded at the time of account provisioning.
2. **Privileged and service accounts** are explicitly assigned to a named individual or group owner responsible for oversight and accountability.
3. No shared or generic accounts are permitted unless technically justified, formally documented, and approved with enhanced logging and monitoring.
4. User-to-account mappings are maintained in:

   * HRIS for employees
   * ITSM/IAM tools (e.g., Okta, Active Directory, AWS IAM)
   * Account inventory documentation
5. Access logs and audit trails **reflect the individual user** behind every action, supporting forensic readiness and compliance.

📋 **Possible Evidence to Collect**

* User provisioning logs or IAM screenshots showing named assignments
* Account inventory spreadsheet showing ownership
* Access control policies prohibiting shared accounts
* Audit log showing specific user actions (e.g., AWS CloudTrail, AD logs)

---

**HITRUST Requirement – MFA for Privileged Access**
---------------------------------------------------

**Control ID:** 01.q User Identification and Authentication  
**Control Type:** Technical  
**Control Level:** Moderate to High  
**HIPAA Mapping:**

* 164.312(d) – Person or Entity Authentication

### 🎯 **Control Objective**

Ensure that access to privileged accounts is protected through strong authentication mechanisms, reducing the risk of unauthorized administrative access.

### 🛡️ **Technical Implementation**

The organization:

1. **Requires multi-factor authentication (MFA)** for all access—both network-based and local—to privileged accounts (e.g., root, domain admin, local admin, and service accounts with elevated permissions).
2. Applies MFA using at least two of the following authentication factors:

   * **Something you know** (e.g., password or passphrase)
   * **Something you have** (e.g., hardware token, mobile authenticator, smart card)
   * **Something you are** (e.g., biometric ID)
3. Configures all administrative endpoints to **enforce MFA** at login time via:

   * IAM policies (AWS, Azure, GCP)
   * Active Directory Group Policy
   * Local system configurations
4. Includes **jump servers or bastion hosts** that enforce MFA where direct privileged access is required to internal infrastructure.
5. Periodically tests MFA enforcement and reviews access logs for anomalies or bypass attempts.

### 📋 **Possible Evidence to Collect**

* Screenshots or configuration exports from Okta/Duo/Azure AD showing MFA policies
* AD or system logs showing MFA enforcement for admin logins
* Sample login attempts showing MFA challenge and approval
* Access control policy referencing MFA for elevated accounts

---

**HITRUST Requirement – MFA for Non-Privileged Remote Access**
--------------------------------------------------------------

**Control ID:** 01.q User Identification and Authentication  
**Control Type:** Technical  
**Control Level:** Moderate  
**HIPAA Mapping:**

* 164.312(d) – Person or Entity Authentication
* 164.312(a)(2)(iii) – Access Control: Automatic Logoff

### 🎯 **Control Objective**

Ensure secure access to information systems by requiring strong authentication for users accessing systems from remote networks, even if those users are non-privileged.

### 🛡️ **Technical Implementation**

The organization:

1. **Enforces multi-factor authentication (MFA)** for all access to **non-privileged user accounts** when accessed from **remote networks**, including:

   * Web applications (e.g., email, portals, SaaS platforms)
   * VPN clients and remote desktop environments
2. Configures remote access solutions (e.g., VPN, Citrix, web proxies, AWS SSO, or Azure AD) to **require a second factor**:

   * One-time passwords (OTP)
   * Push notifications via authenticator apps (e.g., Duo, Okta Verify)
   * Hardware tokens or smart cards
3. Disallows password-only authentication for remote access scenarios involving sensitive data or systems.
4. Implements contextual MFA where possible (e.g., IP-based enforcement, geo-location, or device trust posture).
5. Ensures Web applications authenticate users via MFA before granting access to sensitive functionality or data, even for general users.

### 📋 **Possible Evidence to Collect**

* VPN configuration screenshots showing MFA requirements
* Web app SSO/MFA policy screenshots from identity provider (IdP)
* Authentication logs with timestamps showing MFA challenge/responses
* Policy documents or procedures requiring MFA for remote access
* Contracts with third-party vendors enforcing MFA on user portals

---

**HITRUST Requirement – Strong Authentication for External Network Communications**
-----------------------------------------------------------------------------------

**Control ID:** 01.q User Identification and Authentication  
**Control Type:** Technical  
**Control Level:** Moderate  
**HIPAA Mapping:**

* 164.312(d) – Person or Entity Authentication
* 164.312(e)(2)(ii) – Integrity Controls

### 🎯 **Control Objective**

Ensure that access over external or non-organization-controlled networks is secured with strong authentication mechanisms to prevent unauthorized access and data breaches.

### 🛡️ **Technical Implementation**

The organization:

1. **Implements strong authentication mechanisms**, such as:

   * Multi-factor authentication (MFA),
   * Federated identity with assertion-based access (e.g., SAML, OIDC),
   * Client certificates or cryptographic authentication,
2. Applies strong authentication requirements to all communications involving:

   * External, non-organization-controlled networks (e.g., the Internet),
   * Remote users accessing sensitive systems,
   * APIs and external integrations that access internal services,
3. Ensures that **password-only authentication is not accepted** for external access to sensitive systems or data,
4. Requires authentication policies to be enforced through a central identity provider (e.g., Okta, Azure AD, AWS IAM Identity Center),
5. Conducts periodic **audits and tests of authentication controls** to confirm enforcement across all entry points.

### 📋 **Possible Evidence to Collect**

* Authentication policy specifying requirements for external access
* System configuration showing use of MFA or cryptographic tokens
* Web application settings showing HTTPS + strong auth controls
* Logs showing MFA enforcement from external IP addresses
* Architecture diagrams identifying boundaries and auth controls

---

**HITRUST Requirement – Identification and Authentication of Non-Organizational Users**
---------------------------------------------------------------------------------------

**Control ID:** 01.q User Identification and Authentication  
**Control Type:** Technical  
**Control Level:** Moderate  
**HIPAA Mapping:**

* 164.312(d) – Person or Entity Authentication
* 164.308(a)(3)(ii)(A) – Access Authorization

### 🎯 **Control Objective**

Ensure non-organizational users (or systems acting on their behalf) are uniquely identified and authenticated before being granted access to information residing on the organization’s systems.

### 🛡️ **Technical Implementation**

The organization:

1. **Determines the necessity of access** for non-organizational users (e.g., contractors, third-party vendors, auditors, outsourced developers),
2. **Assigns unique identifiers** to each non-organizational user or associated service/process, avoiding the use of shared or generic accounts,
3. **Authenticates each user or process** using secure methods such as:

   * MFA,
   * Federated identity with organization-trusted IdP,
   * Digital certificates or token-based identity assertions,
4. Ensures **access is logged** and linked back to a specific individual or system for accountability,
5. **Revokes access** promptly when it is no longer required or when a contract ends.

### 📋 **Possible Evidence to Collect**

* Third-party access control policy
* List of non-org user accounts and corresponding identity proof
* Logs showing unique identifiers and auth events
* Access approval requests and termination logs
* Identity federation agreements with partners/vendors

---

**HITRUST Requirement – Use of Shared and Generic User IDs**
------------------------------------------------------------

**Control ID:** 01.q User Identification and Authentication  
**Control Type:** Technical/Administrative  
**Control Level:** Moderate  
**HIPAA Mapping:**

* 164.312(a)(1) – Unique User Identification
* 164.308(a)(4)(ii)(C) – Access Control Procedures

### 🎯 **Control Objective**

Ensure shared or generic user IDs are only used under tightly controlled and documented circumstances that do not compromise accountability, traceability, or security.

### 🛡️ **Technical & Administrative Implementation**

The organization:

1. **Restricts the use of shared/group user IDs** to exceptional cases where a clear and documented business justification exists (e.g., kiosk stations, batch processing jobs).
2. **Requires management approval** for all use cases involving shared IDs and **documents such approval** in an auditable record.
3. Implements **compensating controls** to ensure accountability when shared/group IDs are used, such as:

   * Session recording or command logging,
   * Time-bound access,
   * Mandatory MFA even for shared IDs.
4. **Allows generic IDs** (such as “readonly\_user”) only when:

   * No individual accountability is required, and
   * The access is read-only or minimal-impact (e.g., view-only dashboards).
5. **Prohibits use of shared IDs** for privileged functions, configuration, or system administration.

### 📋 **Possible Evidence to Collect**

* Shared ID use policy and procedures
* Management approval records for each shared/generic ID
* Logs showing usage of shared IDs with traceable metadata
* Technical controls demonstrating session monitoring or MFA on shared accounts
* Justification forms for non-individual accounts

---

**HITRUST Requirement – Replay-Resistant Authentication for Privileged Accounts**
---------------------------------------------------------------------------------

**Control ID:** 01.q User Identification and Authentication  
**Control Type:** Technical  
**Control Level:** Moderate/High  
**HIPAA Mapping:**

* 164.312(d) – Person or Entity Authentication
* 164.312(a)(2)(iii) – Unique User Identification

### 🎯 **Control Objective**

Prevent unauthorized reuse of authentication credentials and reduce risk of credential replay attacks when accessing privileged accounts.

### 🛡️ **Technical Implementation**

The information system:

1. **Implements replay-resistant authentication mechanisms** for privileged account access over the network. These mechanisms include:

   * One-time passwords (OTP) (e.g., TOTP-based MFA),
   * Time-stamped tokens (e.g., expiring SAML or JWT tokens),
   * Cryptographic nonce values that are never reused with the same key.
2. Leverages **industry-standard protocols** such as:

   * Kerberos with ticket lifetimes and renewable tickets,
   * TLS with mutual authentication and ephemeral keys,
   * Challenge-response authentication models (e.g., SCRAM, EAP).
3. Validates freshness and uniqueness of credentials during session establishment.
4. Ensures that authentication data **cannot be intercepted and replayed** by implementing transport encryption (e.g., TLS 1.2+ with strong cipher suites).
5. Applies these protections specifically for **privileged roles** such as system administrators, database administrators, and domain admins.

### 📋 **Possible Evidence to Collect**

* Technical documentation of authentication flows (e.g., Kerberos ticket validation, MFA OTP integration)
* Logs from authentication systems showing nonce or time-based usage
* Configuration screenshots or system settings of protocols enforcing replay protection
* Audit trails of privileged account logins
* Evidence of TLS configuration with unique session keys

---

**HITRUST Requirement – PKI Certificate Validation for Authentication**
-----------------------------------------------------------------------

**Control ID:** 01.q User Identification and Authentication  
**Control Type:** Technical  
**Control Level:** Moderate/High  
**HIPAA Mapping:**

* 164.312(d) – Person or Entity Authentication
* 164.312(c)(1) – Integrity

### 🎯 **Control Objective**

Ensure that when Public Key Infrastructure (PKI) is used for authentication, certificates are validated to prevent unauthorized access and ensure system integrity.

### 🛡️ **Technical Implementation**

When PKI-based authentication is used, the information system:

1. **Constructs and verifies a certification path** to a valid trust anchor (e.g., root CA), including validation of:

   * Intermediate certificate chains, and
   * Certificate status via Online Certificate Status Protocol (OCSP) or Certificate Revocation Lists (CRLs).
2. **Enforces access control** to corresponding private keys by:

   * Ensuring keys are securely stored (e.g., within TPMs, HSMs, or encrypted local stores),
   * Restricting private key access to authorized processes or users only.
3. **Maps digital certificates to user or group accounts** to ensure proper role-based access and auditability.
4. **Implements local caching** of revocation data:

   * To support continued validation when revocation servers (e.g., OCSP responders) are unavailable,
   * Ensuring certificate trust decisions can still be made during offline or degraded network conditions.

### 📋 **Possible Evidence to Collect**

* System configuration files or screenshots (e.g., `/etc/ssl/openssl.cnf`, Windows Certificate Services settings)
* CA trust chain and OCSP/CRL integration documentation
* Private key storage configuration (e.g., TPM/HSM integration docs)
* PKI certificate-to-account mapping tables or logs
* Logs showing use of cached revocation data
* Sample certificate validation paths including trust anchor resolution

---

**HITRUST Requirement – Help Desk Authentication for Security-Related Requests**
--------------------------------------------------------------------------------

**Control ID:** 01.q User Identification and Authentication  
**Control Type:** Administrative  
**Control Level:** Moderate/High  
**HIPAA Mapping:**

* 164.312(d) – Person or Entity Authentication
* 164.308(a)(3)(ii)(B) – Access Authorization

### 🎯 **Control Objective**

Prevent unauthorized changes or disclosure of information by ensuring that help desk support transactions related to security are performed only after confirming user identity.

### 🛡️ **Implementation**

Help desk support:

1. **Requires user identification** before proceeding with any request that could affect information security, such as:

   * Password resets
   * Access provisioning or de-provisioning
   * Role changes or escalations
   * Requests for sensitive data
   * Account unlocks or MFA resets
2. Acceptable forms of identification may include:

   * Verification via registered contact details (e.g., callback to known phone number, code sent to MFA device)
   * Use of a unique ticketing system with pre-authenticated user login
   * Verification against identity data already on file

### 📋 **Possible Evidence to Collect**

* Help desk procedures or SOPs requiring identity verification
* Ticket logs showing verification steps (e.g., identity validation notes)
* Help desk training materials covering security identification protocol
* System screenshots showing ID-verification workflows
* Incident response logs involving help desk impersonation detection/prevention

---

**HITRUST Requirement – Unique User Identification and Access Management**
--------------------------------------------------------------------------

**Control ID:** 01.q User Identification and Authentication  
**Control Type:** Technical  
**Control Level:** Moderate/High  
**HIPAA Mapping:**

* 164.312(a)(2)(i) – Unique User Identification
* 164.312(d) – Person or Entity Authentication

### 🎯 **Control Objective**

Ensure accountability and prevent unauthorized access by uniquely identifying and authenticating each user for both local and remote access.

### 🛡️ **Implementation**

The organization:

1. **Ensures redundant user IDs are not re-issued** to multiple individuals.

   * Each user ID must be unique and assigned to a single named individual.
   * Reuse of deactivated or former employee user IDs is restricted unless formally retired from use.
2. **Uniquely identifies and authenticates users** prior to:

   * **Local access** to endpoints, servers, or systems
   * **Remote access** via VPN, remote desktop, or cloud-based applications
3. Supports this control through:

   * Centralized identity and access management systems (e.g., Active Directory, Okta)
   * Multi-factor authentication mechanisms
   * User lifecycle management workflows (provisioning, deprovisioning, disabling inactive accounts)

### 📋 **Possible Evidence to Collect**

* Identity and access management (IAM) policies or procedures
* System configurations enforcing unique user IDs
* Screenshots of access control settings
* User access logs demonstrating successful authentication for local and remote sessions
* Identity provider logs showing no duplicate usernames

---

**HITRUST Requirement – Multifactor Authentication for Access Control**
-----------------------------------------------------------------------

**Control ID:** 01.q User Identification and Authentication  
**Control Type:** Technical  
**Control Level:** Moderate/High  
**HIPAA Mapping:**

* 164.312(d) – Person or Entity Authentication
* 164.312(a)(1) – Access Control

### 🎯 **Control Objective**

Ensure that access to systems—especially from remote networks and for privileged users—is secured with strong, multifactor authentication to prevent unauthorized access and preserve system confidentiality, integrity, and availability.

### 🛡️ **Implementation**

The organization:

1. **Implements multifactor authentication (MFA)** for **remote network access** to both:

   * **Privileged accounts** (e.g., system administrators, domain admins)
   * **Non-privileged accounts** (e.g., standard users accessing web apps or VPN)
2. Ensures that **one of the authentication factors is physically separate** from the device requesting access (e.g., smart card, hardware token, authenticator app on another device).
3. **Enforces MFA for local access to privileged accounts**, including:

   * Workstations and servers
   * Systems used for **non-local maintenance and diagnostic sessions**
   * Jump boxes or bastion hosts
4. Applies this requirement through:

   * Use of identity providers (e.g., Okta, Duo, Microsoft Entra ID)
   * OS-level MFA enforcement (e.g., Windows Hello for Business, PAM integration)
   * Conditional access policies restricting access based on context

### 📋 **Possible Evidence to Collect**

* Access control and authentication policies
* Configuration of MFA for VPN, remote desktop, and endpoint login
* Screenshots from MFA dashboards or identity provider settings
* Logs showing MFA challenge and verification steps
* Evidence of device separation (e.g., phone-based OTP for workstation login)
* Proof of enforcement for local administrative login

---

**HITRUST Requirement – System Utility Access Control**
-------------------------------------------------------

**Control ID:** 01.s Use of System Utilities  
**Control Type:** Technical  
**Control Level:** Moderate/High  
**HIPAA Mapping:**

* 164.312(a)(1) – Access Control
* 164.312(c)(1) – Integrity
* 164.308(a)(3)(ii)(B) – Workforce Clearance Procedures

### 🎯 **Control Objective**

Restrict and monitor the use of system utilities to protect against unauthorized or inadvertent system-level changes that may compromise confidentiality, integrity, or availability of systems and data.

### 🛡️ **Implementation**

The organization controls the use of system utilities by implementing the following safeguards:

1. **Identification, Authentication, and Authorization Procedures:**

   * Access to system utilities (e.g., PowerShell, root shell, registry editors) is limited via role-based access control (RBAC), enforced using OS-level and identity provider configurations.
   * MFA is required for elevated sessions.
   * All access is logged and monitored.
2. **Segregation from Application Software:**

   * System utilities are logically and technically separated from business applications.
   * Application users do not have access to administrative utilities or environments.
   * System utilities are managed on hardened administrative environments or jump servers.
3. **Access Minimization:**

   * Access to system utilities is limited to the minimum number of trusted, authorized users with a documented business need.
   * Regular reviews are conducted to remove excess or outdated access.
   * Privilege elevation (e.g., Just-In-Time access) is used for time-bound admin activity.

### 📋 **Possible Evidence to Collect**

* System and domain-level RBAC policy documentation
* Identity provider or PAM tool configurations showing utility access restrictions
* Logs from utilities (e.g., `sudo`, PowerShell, Sysinternals, GPO logs)
* List of users with elevated utility access
* Screenshots of utility segregation (e.g., application server GPOs)
* Access review records and role approval workflows

---

**HITRUST Requirement – Session Timeout Controls for Devices**
--------------------------------------------------------------

**Control ID:** 01.t Session Time-out  
**Control Type:** Technical  
**Control Level:** Moderate/High  
**HIPAA Mapping:**

* 164.312(a)(2)(iii) – Automatic Logoff
* 164.308(a)(3)(ii)(C) – Termination Procedures

### 🎯 **Control Objective**

Ensure that inactive sessions on all devices accessing organizational systems—whether personal (BYOD) or company-owned—are secured by enforcing automatic session timeouts via technical controls.

### 🛡️ **Implementation**

The organization enforces automatic session timeout configurations through centrally managed policies across both personal and organizational assets:

1. **Company-Owned Devices**

   * Devices are managed via MDM solutions (e.g., Microsoft Intune, Jamf) that enforce inactivity-based lockout (e.g., 5–15 minutes of inactivity).
   * Device-level settings (e.g., GPO, configuration profiles) ensure that screens lock automatically and require reauthentication upon resumption.
2. **Bring Your Own Devices (BYOD)**

   * Participation in the BYOD program is conditional upon enrollment in the organization’s MDM or mobile security platform.
   * Time-out policies are pushed via MDM or endpoint security agents (e.g., VMware Workspace ONE, Intune, MobileIron).
   * The organization reserves the right to revoke access to corporate apps and data if time-out configurations are tampered with or non-compliant.
3. **Enforcement and Monitoring**

   * System and security teams regularly verify compliance via endpoint health checks and policy compliance reports.
   * Devices that fail compliance checks are quarantined or blocked from network/app access using conditional access policies.

### 📋 **Possible Evidence to Collect**

* Screenshot or export of session timeout policy from MDM or device config
* MDM policy documentation for time-out enforcement on macOS, Windows, iOS, Android
* Conditional access policy for BYOD devices
* Device compliance reports
* Screenshots from sample device showing enforced timeout and re-authentication
* BYOD enrollment agreements outlining device policy expectations

---

**HITRUST Requirement – Connection Time Controls**
--------------------------------------------------

**Control ID:** 01.u Limitation of Connection Time  
**Control Type:** Technical  
**Control Level:** Moderate/High  
**HIPAA Mapping:**

* 164.312(a)(1) – Access Control
* 164.312(a)(2)(iii) – Automatic Logoff

### 🎯 **Control Objective**

Ensure that system access for sensitive applications is restricted based on connection time, reducing exposure from high-risk or unmanaged environments.

### 🛡️ **Implementation**

The organization implements time-based controls to limit the window of access to sensitive systems, reducing the risk of compromise:

1. **Application of Connection Time Controls**

   * Applied to critical applications or systems processing PHI, financials, or intellectual property.
   * Enforced more stringently for users connecting from high-risk environments (e.g., airports, home networks without VPN).
2. **Time Slot Scheduling**

   * Automated workflows restrict access to predefined windows, e.g., during batch processing or routine data transfers.
   * Example: SFTP access for billing files allowed only between 1:00 a.m.–3:00 a.m.
3. **Business Hour Enforcement**

   * Administrative interfaces and developer portals are restricted to working hours unless exceptions are documented.
   * Conditional Access and IAM policies (e.g., in Azure AD, Okta) prevent logins during off-hours unless job-critical.
4. **Timed Re-authentication**

   * Session tokens expire after a defined duration (e.g., 30–60 minutes) requiring user re-authentication for continued access.
   * Implemented via identity providers or application-level security configurations (e.g., reauth on elevated privileges).

### 📋 **Possible Evidence to Collect**

* Screenshots or exports of Conditional Access policies enforcing time windows
* VPN or firewall logs showing allowed connection schedules
* Configuration of re-authentication timeout policies in apps or IAM platforms
* Policy documents referencing time-based access enforcement
* Workflow schedule for batch connections
* Sample alert or incident showing blocked access during unauthorized time

---

**HITRUST Requirement – Application and Function Access Control**
-----------------------------------------------------------------

**Control ID:** 01.v Information Access Restriction  
**Control Type:** Technical  
**Control Level:** Moderate/High  
**HIPAA Mapping:**

* 164.308(a)(4) – Information Access Management
* 164.312(a)(1) – Access Control

### 🎯 **Control Objective**

Ensure access to applications and their functions is restricted based on user roles, least privilege, and job responsibilities to protect sensitive systems and data.

### 🛡️ **Implementation**

The organization enforces granular access control at the application level using multiple technical mechanisms:

1. **Menu-Driven Access Control**

   * Role-Based Access Control (RBAC) is implemented in applications to show/hide functions based on user role.
   * Example: A billing clerk may only view and enter payment data but cannot delete patient records.
2. **Granular Permissions by Function**

   * Permissions include specific access modes: read, write, delete, execute, and admin.
   * Enforced via IAM systems or within the application’s security configuration (e.g., Salesforce, EHR platforms).
3. **Cross-Application Access Control**

   * Where integrations exist (e.g., EHR ↔ billing), permissions limit what data an external application can access or modify.
4. **Output Limitations**

   * Reports and exports are tailored to avoid unnecessary data exposure.
   * Sensitive outputs (e.g., SSNs or treatment history) are masked or redacted unless access is specifically authorized.
5. **Physical/Logical Isolation**

   * Access to sensitive apps (e.g., clinical, financial, or admin) is isolated via VLANs, VPC security groups, or logical segmentation.
   * Administrative and operational environments are separated to minimize risk.

### 📋 **Possible Evidence to Collect**

* Screenshots of application role/permission matrix
* Application configuration files showing menu access restrictions
* Logs of access attempts to restricted functions
* Network diagrams showing logical isolation zones
* Sample audit trail showing permitted vs. denied access actions
* Access review reports for sensitive application modules

---

**HITRUST Requirement – Application-to-Application Access Rights**
------------------------------------------------------------------

**Control ID:** 01.v Information Access Restriction  
**Control Type:** Technical  
**Control Level:** Moderate/High  
**HIPAA Mapping:**

* 164.308(a)(4) – Information Access Management
* 164.312(a)(1) – Access Control

### 🎯 **Control Objective**

Ensure that access rights to other applications are granted and maintained in accordance with defined access control policies, minimizing unauthorized system-to-system interactions.

### 🛡️ **Implementation**

The organization manages access rights between applications through policy-driven controls, including:

1. **Policy-Aligned Permissions**

   * Access between applications (e.g., via APIs or direct integration) is governed by documented access control policies that specify which services or applications may access others and under what conditions.
2. **Role and Purpose-Based Interconnection**

   * Only applications or services with a defined business need (e.g., EHR to billing integration, monitoring tool access to production systems) are granted access.
   * All application interconnections are documented with purpose and approval.
3. **Service Accounts with Least Privilege**

   * Inter-app communication is performed using dedicated service accounts or API tokens scoped to the minimum required permissions.
4. **Integration Gateways and Access Brokers**

   * Where applicable, access between applications is managed via secure API gateways or service mesh with mutual TLS, access validation, and logging.
5. **Review and Revocation**

   * Access to other applications is reviewed periodically (e.g., quarterly or upon system change).
   * Access is revoked when no longer required, or when the underlying policy changes.

### 📋 **Possible Evidence to Collect**

* List of applications and documented interconnections
* Sample access control policy governing application integrations
* Screenshots of service account or API token configurations with access scopes
* Logs or audit reports showing inter-application access activity
* Change control or request ticket approving access to another application
* Role-based access configurations showing service-to-service permissions

---

**HITRUST Requirement – Output Control for Covered Information**
----------------------------------------------------------------

**Control ID:** 01.v Information Access Restriction  
**Control Type:** Technical  
**Control Level:** Moderate/High  
**HIPAA Mapping:**

* 164.312(e)(1) – Transmission Security
* 164.308(a)(3) – Workforce Security

### 🎯 **Control Objective**

Ensure outputs from application systems handling covered information are limited to relevant content and are securely transmitted only to authorized endpoints.

### 🛡️ **Implementation**

The organization implements the following controls to protect outputs from applications processing covered information (e.g., PHI, PII):

1. **Output Minimization**

   * Application logic and export/reporting templates are configured to include only data fields relevant to the purpose of the output (e.g., redacting SSNs or clinical notes from billing exports).
   * Role-based views and filtered exports ensure sensitive fields are excluded for users who do not require them.
2. **Restricted Output Destinations**

   * Print jobs and exported files are sent only to authorized destinations such as secure print queues, designated workstations, or encrypted email addresses.
   * System configurations restrict access to data exports, APIs, or reports to validated and authenticated endpoints.
3. **Data Loss Prevention (DLP) Integration**

   * DLP tools are used to inspect outbound data for policy violations, particularly in high-risk workflows such as email, file transfers, and browser-based exports.
4. **Secure Logging & Monitoring**

   * All outbound data transmissions involving covered information are logged, including destination, file size/type, and user/application initiating the action.
   * Alerts are configured for large or unauthorized exports.
5. **Policy Enforcement**

   * Output controls are supported by policies defining authorized endpoints (e.g., finance terminals, fax locations, or secure portals) and authorized personnel.
   * Deviations from policy are documented and reviewed.

### 📋 **Possible Evidence to Collect**

* Screenshots of application export/report configuration
* Output samples redacting non-relevant information
* Print/fax/email routing controls and allowed destination list
* Role-based access control (RBAC) settings for data views
* Logs showing report export activity
* Output policy document and recipient authorization list
* DLP configuration showing rules on PHI/PII transmission

---

**HITRUST Requirement – Protection of Data Stored in Information Systems**
--------------------------------------------------------------------------

**Control ID:** 01.v Information Access Restriction  
**Control Type:** Technical  
**Control Level:** Moderate/High  
**HIPAA Mapping:**

* 164.308(a)(1)(ii)(C) – Information System Activity Review
* 164.312(a)(1) – Access Control
* 164.312(a)(2)(iv) – Encryption and Decryption
* 164.312(c)(1) – Integrity

### 🎯 **Control Objective**

Ensure that stored data is protected against unauthorized access, exposure in non-secure environments, and unnecessary retention.

### 🛡️ **Implementation**

The organization implements the following layered security controls for stored data:

1. **System Access Controls**

   * Data in file systems, databases, and applications is governed by access control lists (ACLs) tailored to each environment (e.g., NTFS ACLs, database-level GRANTs, or S3 bucket policies).
   * Access permissions are role-based, with least privilege enforced through automated IAM provisioning.
2. **Encryption of Data at Rest in Non-Secure Areas**

   * Data residing outside of logically or physically secured boundaries (e.g., endpoints, removable storage, or BYOD environments) is encrypted using FIPS 140-2 validated algorithms (e.g., AES-256).
   * Cloud-based storage (e.g., AWS S3, EBS, RDS) is configured to enforce encryption at rest.
3. **Periodic Output Review & Data Minimization**

   * Reports, logs, and temporary files are reviewed on a scheduled basis (at least quarterly or in alignment with data retention policies) to identify and delete redundant or obsolete information.
   * Automated scripts may purge files from designated directories or enforce data lifecycle rules (e.g., AWS S3 object expiration, Windows file cleanup).
4. **Secure Configuration Management**

   * Hardening standards ensure data repositories are configured to prevent unauthorized browsing, directory listings, or dumping of sensitive content.
   * Regular audits validate that access permissions and encryption settings are intact and compliant.

### 📋 **Possible Evidence to Collect**

* Screenshots of file/folder/database ACLs
* Encryption configurations for non-secure storage (e.g., BitLocker, S3, EBS, endpoint encryption)
* Data retention/review logs or cleanup job schedules
* Sample reports showing deletion of outdated exports or reports
* Data protection policy and review frequency documentation
* Audit results from encryption or access control reviews
* Role-based access matrix and provisioning workflows

---

**HITRUST Requirement – Actions Without Identification and Authentication**
---------------------------------------------------------------------------

**Control ID:** 01.v Information Access Restriction  
**Control Type:** Technical / Policy  
**Control Level:** Moderate/High  
**HIPAA Mapping:**

* 164.312(a)(1) – Access Control
* 164.308(a)(3)(ii)(B) – Workforce Clearance Procedure

### 🎯 **Control Objective**

Ensure that actions performed without user identification or authentication are strictly limited to those necessary for achieving core mission objectives and pose minimal risk.

### 🛡️ **Implementation**

The organization enforces access control boundaries that permit unauthenticated actions **only** when:

1. **They Are Mission-Critical and Low-Risk**

   * Examples may include publicly accessible health and safety alerts, marketing content, or application welcome screens that do not expose sensitive or regulated data.
   * These unauthenticated functions are pre-approved during the design phase through risk-based analysis.
2. **They Are Explicitly Approved**

   * All unauthenticated functions are documented and reviewed by the information security and compliance team.
   * Change control processes ensure that new unauthenticated access points are evaluated for necessity and risk.
3. **They Are Segregated from Sensitive Functions**

   * System design ensures that unauthenticated areas cannot pivot or escalate into privileged environments.
   * Technical measures (e.g., reverse proxies, web application firewalls) isolate anonymous endpoints.
4. **They Are Reviewed Periodically**

   * Information systems are reviewed at least annually or after significant updates to validate that all unauthenticated functionalities still serve a necessary purpose.
   * Any deprecated or unnecessary exposure is remediated.

### 📋 **Possible Evidence to Collect**

* List of approved unauthenticated endpoints or features
* Screenshots or configurations showing segregation between anonymous and authenticated functionality
* Risk assessments or threat models for public-facing components
* Access control policy stating when unauthenticated access is permitted
* Documentation from change review board or security architect approval
* Web server configuration showing access restrictions

---

**HITRUST Requirement – Protection of Sensitive Information in Remote Access**

Control ID: 01.v Information Access Restriction  
Control Type: Technical / Policy  
Control Level: Moderate/High  
HIPAA Mapping:164.310(d)(1) – Device and Media Controls, 164.312(a)(1) – Access Control, 164.312(c)(1) – Integrity

🎯 **Control Objective**

Prevent unauthorized duplication, distribution, or local storage of sensitive information accessed remotely, thereby reducing the risk of data leakage or exposure.

**Technical** **Implementation**

The organization implements technical and procedural controls to **prohibit** the following actions during remote access to sensitive data unless specifically authorized:

1. **Copying or Moving Data**

   * Copy-paste functionality and file download operations are disabled within virtual desktop infrastructure (VDI), Citrix, or browser-based applications when accessing ePHI or cardholder data remotely.
2. **Printing and Screen Capturing**

   * Remote access sessions disable local printing and block screen capture using group policy objects (GPO), data loss prevention (DLP), or session policies in secure access platforms (e.g., Microsoft Entra ID, ZScaler, Palo Alto Prisma).
3. **Storage on Local Media**

   * Saving to local drives or USB devices is restricted via endpoint security agents. Exceptions are granted only through documented business justifications, reviewed and approved by the Information Security Officer or equivalent authority.
4. **Monitoring and Enforcement**

   * DLP tools continuously monitor remote sessions for any attempt to extract sensitive data.
   * Alerts are configured for activities such as attempted copy-paste or file transfers during remote sessions.
5. **Awareness and Acknowledgment**

   * Users accessing sensitive data remotely are required to acknowledge data handling restrictions during login or VPN session initiation.

📋 **Possible Evidence to Collect**

* Screenshots of DLP or endpoint protection software policies
* VPN or remote access solution configuration (e.g., print and clipboard blocking)
* Access control policy referencing remote access restrictions
* Change request or approval form for authorized exceptions
* Audit logs showing policy enforcement during remote sessions
* Acceptable use policy or user attestation records

---

**HITRUST Requirement – Termination Checklist for Offboarding**

Control ID: 02.g Termination or Change Responsibilities  
Control Type: Administrative / Operational  
Control Level: All Levels  
HIPAA Mapping: 164.308(a)(3)(ii)(C) – Termination Procedures

🎯 **Control Objective**

Ensure that all steps necessary for secure offboarding of personnel are followed to prevent unauthorized access and recover organizational assets.

🛡️ **Implementation**

The organization maintains a **documented termination checklist** that is followed when an employee, contractor, or vendor is offboarded. The checklist:

1. **Specifies Required Steps**

   * Notifies HR, IT, Security, and relevant department managers.
   * Includes timing of access deactivation for systems, VPN, email, physical entry badges, etc.
   * Ensures updates in directory services (e.g., Okta, AD) to deactivate accounts immediately upon termination.
2. **Details Assets to Be Collected**

   * Laptops, mobile devices, access cards, tokens, hardware keys (e.g., YubiKey), and storage devices.
   * Software licenses and cloud-based tool credentials are revoked or reassigned.
3. **Roles and Responsibilities**

   * HR coordinates the process.
   * IT and Security ensure technical access is removed.
   * A manager or department head confirms the return of organizational assets.
4. **Monitoring and Review**

   * Periodic audits are performed to verify deprovisioning and asset return are completed within 24–48 hours of termination.
   * Exceptions are documented and approved through an escalation process.
5. **Storage and Evidence**

   * Signed checklists and offboarding records are stored securely (e.g., in the HRIS or ticketing system).
   * All deprovisioning activities are logged and timestamped in identity/access management systems.

📋 **Possible Evidence to Collect**

* Sample termination checklist
* Policy/procedure referencing checklist usage
* Screenshots of deprovisioning in identity management systems (Okta, AD)
* Asset return log or receipt
* HRIS system record of offboarding
* Audit trail showing user account disablement and asset return completion

---

**HITRUST Requirement – Return of Organizational Assets During Termination**

Control ID: 02.h Return of Assets  
Control Type: Operational  
Control Level: All Levels  
HIPAA Mapping: 164.308(a)(3)(ii)(C) – Termination Procedures

🎯 **Control Objective**

Ensure that all organizational property is returned by the individual upon termination to prevent loss or unauthorized access to organizational assets and data.

**Technical Implementation**

The organization enforces a formal **termination process** that mandates the return of all assigned assets and materials. This process includes the return of:

1. **Previously Issued Software**

   * Any licensed or organization-developed software installed on personal or company-issued devices.
   * Licenses and entitlements are revoked, and endpoints are scanned to verify removal.
2. **Corporate Documents**

   * Any physical or digital documents, reports, manuals, or confidential printouts provided during employment.
   * Stored data is reviewed and archived or deleted as needed.
3. **Equipment**

   * All hardware such as laptops, docking stations, monitors, mobile phones, and peripherals are returned.
   * Items are logged in the asset management system with condition noted.
4. **Other Organizational Assets**

   * Items such as access cards, key fobs, credit cards, USB drives, SIM cards, company manuals, and any data stored on electronic media.
   * These are inventoried and verified against issuance logs.

Return of these assets is documented on a **termination checklist**, and must be signed off by IT, HR, and the employee’s supervisor. All returned items are reconciled with asset registers and licensing records.

📋 **Possible Evidence to Collect**

* Termination policy or SOP referencing asset return
* Sample completed termination checklists
* Asset management logs (e.g., ServiceNow, JAMF, Intune)
* Screenshots of software license revocation
* Access card/logs showing badge return
* Return receipts for equipment or mobile devices

---

**HITRUST Requirement – Review and Revocation of Access Upon Role or Employment Change**

Control ID: 02.i Removal of Access Rights  
Control Type: Operational  
Control Level: All Levels  
HIPAA Mapping: 164.308(a)(3)(ii)(B) – Workforce Clearance Procedure

🎯 **Control Objective**

Ensure that individuals only retain access to information systems and equipment appropriate to their current roles or employment status, by promptly updating or revoking access when changes occur.

**Technical Implementation**

The organization enforces a structured process to manage **logical and physical access authorizations** to systems and equipment. These authorizations are:

1. **Reviewed** – Periodically and upon notification of a change in user status.
2. **Updated** – To reflect revised access needs following changes in job responsibilities.
3. **Revoked** – When access is no longer justified due to termination or reassignment.

The process is triggered by:

* **Change in Responsibility**

  + When an employee is promoted, transferred, or changes departments.
  + Access reviews are initiated by the manager or through automated HR feeds.
* **Change in Employment**

  + When an individual exits the organization (voluntarily or involuntarily).
  + Access to all logical systems (e.g., email, databases, applications) and physical entry systems (e.g., badge readers) is revoked within a defined SLA.

Access logs and user entitlements are reconciled through IAM platforms (e.g., Okta), and physical badge systems are cross-referenced for deactivation. Role-based access control (RBAC) ensures that users only have access consistent with least privilege.

📋 **Possible Evidence to Collect**

* Access control policy referencing changes in role/employment
* Termination checklist showing access removal steps
* Sample user access review logs
* Change ticket logs tied to access changes (e.g., Jira, ServiceNow)
* Screenshots of IAM system logs (Okta, Azure AD, etc.)
* Deprovisioning confirmation from physical access control systems

---

**HITRUST Requirement – Immediate Termination of Access Upon Notice of Resignation or Dismissal**

Control ID: 02.i Removal of Access Rights  
Control Type: Operational  
Control Level: All Levels  
HIPAA Mapping: 164.308(a)(3)(ii)(C) – Termination Procedures

🎯 **Control Objective**

Ensure prompt revocation of access rights when a user resigns, is dismissed, or is terminated to mitigate risks related to unauthorized system or facility access.

**Technical Implementation**

The organization enforces a formal procedure to immediately terminate access rights for users who have submitted a resignation notice or received **notice of dismissal**. The process includes:

1. **Logical Access Termination:**

   * Access to all information systems (email, databases, SaaS tools, etc.) is revoked at the time notice is received or during the termination process.
   * IAM tools (e.g., Okta, Azure AD) automatically trigger access revocation workflows.
2. **Physical Access Termination:**

   * Access to facilities (badges, entry gates, etc.) is revoked in coordination with security and HR.
3. **Escorted Termination (if needed):**

   * In cases involving serious misconduct or elevated risk, the organization supports immediate physical removal from the premises with security escort.

This dual approach ensures personnel cannot access sensitive systems or facilities beyond the point of notification, preserving organizational security and compliance.

📋 **Possible Evidence to Collect**

* Termination policy/procedure document
* Termination checklist including access removal steps
* IAM system logs showing time-stamped access revocation
* Badge deactivation records from physical access systems
* HR incident/ticket demonstrating immediate termination protocol
* Screenshots or logs from emergency deprovisioning process

---

**HITRUST Requirement – Reevaluation of Access Upon Change of Role and Confidentiality During Termination**

Control ID: 02.i Removal of Access Rights  
Control Type: Operational  
Control Level: All Levels  
HIPAA Mapping: 164.308(a)(3)(ii)(B) – Workforce Clearance Procedures

🎯 **Control Objective**

Ensure that access rights are appropriate to the workforce member’s current role and that confidentiality obligations are reinforced during the termination process.

**Technical Implementation**

The organization implements a structured process for re-evaluating access controls and reinforcing confidentiality obligations under the following circumstances:

1. **Access Reevaluation Upon Role Change**

   * When a workforce member transitions to a new position of trust, logical and physical access privileges are re-evaluated within 30 days of the role change.
   * This review ensures that access is aligned with principle of least privilege, removing rights no longer required and provisioning only those relevant to the new responsibilities.
   * The reevaluation process is supported through HR-IT workflows and identity governance solutions (e.g., Okta).
2. **Confidentiality Reinforcement at Termination**

   * During the termination process, departing employees are reminded of their obligation to maintain the confidentiality of any sensitive or covered information they accessed while employed.
   * This is typically addressed in the exit interview and documented via a signed confidentiality acknowledgment form or referenced from the employment agreement.

📋 **Possible Evidence to Collect**

* Access review policy for role changes
* Logs or tickets showing access rights re-evaluation within 30 days
* Role change communication templates (e.g., HRIS or email notices triggering access review)
* Exit interview checklist referencing confidentiality obligations
* Signed confidentiality agreement (on hire or during exit)
* Audit logs showing removal/addition of access entitlements during role change

---

**HITRUST Requirement – Access Rights Removal or Reduction Based on Risk During Termination or Change of Employment**

Control ID: 02.i Removal of Access Rights  
Control Type: Operational  
Control Level: All Levels  
HIPAA Mapping: 164.308(a)(3)(ii)(C) – Termination Procedures

🎯 **Control Objective**

Ensure access to information assets and facilities is appropriately removed or reduced in a timely manner during changes in employment or workforce arrangements, based on the evaluation of risk.

**Technical Implementation**

The organization has implemented procedures to manage **access rights reduction or removal** for all users—employees, contractors, third-party users, or other workforce members—prior to or during termination or a change in work status.

1. Pre-Termination Access Removal

   * Logical and physical access to information systems, applications, and facilities is reduced or revoked before employment ends or upon change in workforce status.
   * This process is proactively triggered by HR, people operations, or contract management workflows and is integrated with the organization's identity and access management (IAM) system.
2. Risk-Based Evaluation Criteria  
   Access changes are informed by a risk evaluation based on:

   * Initiator of Termination/Change: Whether initiated by the individual or by management.
   * Reason for Termination: Voluntary departure, misconduct, layoffs, contract expiration, etc.
   * Current Responsibilities: The sensitivity and scope of the data/systems the individual currently accesses.
   * Asset Value: The criticality and confidentiality of the information assets and physical areas accessible to the individual.
3. Workflow Enforcement

   * Access changes are documented via support tickets or HRIS-linked workflows and require management approval.
   * All access removals are reviewed post-action for completion and logged for audit readiness.

📋 **Possible Evidence to Collect**

* Access control and termination/change-of-role policy
* Risk evaluation matrix or checklist used during termination or transfer
* Termination/change request tickets referencing access removal timing
* IAM logs showing access revocation events prior to or during termination
* Evidence of HR or manager signoff on access removal
* Audit reports showing access de-provisioning timelines compared to termination dates

---

**HITRUST Requirement – Computer Login Banners and User Acknowledgment**

Control ID: 06.e Prevention of Misuse of Information Assets  
Control Type: Technical  
Control Level: All Levels  
HIPAA Mapping: 164.308(a)(5)(ii)(C) – Security Awareness and Training

🎯 **Control Objective**

Ensure users are notified of acceptable use and privacy expectations before accessing organizational systems, and that their acknowledgment is captured.

**Technical Implementation**

The organization enforces the use of login banners on all managed computing systems (e.g., Windows, macOS, Linux, virtual desktops) to provide clear communication of security, privacy, and usage expectations. These banners are configured to display prior to granting system access and include the following key elements:

1. Privacy Notice

   * A statement that the system is private property of the organization.
2. Prohibition of Unauthorized Access

   * A message clearly indicating that unauthorized use is prohibited and may be subject to monitoring and disciplinary action.
3. Acceptable Use Conditions

   * Conditions for use, including authorized business use only, and expectations for responsible behavior.
4. Security and Monitoring Disclosure

   * Notification that system activity may be monitored, logged, and disclosed to authorized parties, including law enforcement.
5. User Acknowledgment Requirement

   * Login is blocked until the user accepts the banner or clicks an “OK/Acknowledge” button to proceed.

These banners are centrally managed via Group Policy Objects (GPOs) for Windows systems, Jamf Pro for macOS, and custom pre-login scripts or display managers on Linux environments.

📋 **Possible Evidence to Collect**

* Screenshot or configuration of login banner text
* Policy or procedure detailing login banner requirements
* GPO or MDM profile configuration showing enforcement
* Access logs confirming login banner display prior to session start
* Audit logs showing banner acknowledgment
* Sample user attestation (if captured)

---

**HITRUST Requirement – Employee Notification and Consent to Monitoring**

Control ID: 06.e Prevention of Misuse of Information Assets  
Control Type: Administrative  
Control Level: All Levels  
HIPAA Mapping: 164.308(a)(1)(ii)(A) – Risk Management; 164.308(a)(5)(ii)(C) – Security Awareness and Training

🎯 **Control Objective**

Ensure users are aware that their use of information systems may be monitored and that consent is documented in compliance with applicable legal requirements.

Technical **Implementation**

The organization has implemented a formal **Acceptable Use Policy (AUP)** that clearly notifies all employees and applicable workforce members that:

1. **Monitoring of Information Asset Use**

   * All actions performed on information systems may be monitored, recorded, and subject to review by authorized personnel to ensure compliance with organizational policies and legal obligations.
2. **Consent to Monitoring**

   * Employees provide explicit written consent to such monitoring by signing the Acceptable Use Agreement (AUA) during onboarding and any time the policy is updated.
3. **Legal Compliance**

   * The language within the AUP and related monitoring notifications is reviewed by legal counsel to ensure compliance with applicable jurisdictional laws, including employee privacy and electronic monitoring regulations (e.g., U.S. federal/state laws, GDPR where applicable).
4. **Policy Communication**

   * The AUP and monitoring notice are communicated via:

     + New hire orientation
     + Mandatory annual security training
     + Employee handbook and intranet
     + Pop-up acknowledgment banners (where applicable)
5. **Record Retention**

   * Signed Acceptable Use Agreements are retained in the employee’s HR record and stored in a centralized document management system for audit purposes.

📋 **Possible Evidence to Collect**

* Copy of the Acceptable Use Policy and Monitoring Notice
* Record of signed employee agreements (sample redacted)
* Training logs or acknowledgment receipts
* Screenshot of login banner or intranet notice
* Legal review or compliance memo for monitoring policy
* HR system export showing consent collection and retention

---

**HITRUST Requirement – Segregation of Access Authorization Duties**

Control ID: 09.c Segregation of Duties  
Control Type: Administrative / Technical  
Control Level: All Levels  
HIPAA Mapping: 164.308(a)(4)(ii)(B) – Access Authorization

🎯 **Control Objective**

To ensure no single individual has sole control over access authorization processes, thereby reducing the risk of unauthorized access and enforcing proper oversight.

**Technical Implementation**

The organization enforces **segregation of duties (SoD)** in its access authorization process to maintain integrity and reduce the risk of abuse or error. This is accomplished through the following measures:

1. **Access Requests**

   * Users submit access requests via a centralized identity and access management (IAM) system (e.g., Okta) which captures requestor identity, requested roles or privileges, and business justification.
2. **Approval Workflow**

   * Access requests are routed for approval to the appropriate manager (typically the requestor’s functional supervisor) and, where applicable, the data or application owner.
   * Approvals are documented and cannot be self-approved. The system enforces this restriction by design.
3. **Provisioning Segregation**

   * System administrators or IT support staff are responsible for provisioning access but do not have authority to approve access.
   * Provisioning tasks are performed only after approval is completed and logged.
4. **Audit Logging and Oversight**

   * All stages of the access authorization lifecycle (request, approval, provisioning, and revocation) are fully logged and auditable.
   * Periodic access reviews confirm that access aligns with approval records.
5. **Segregation Verification**

   * Internal audits or compliance reviews verify that no single individual has combined control over request, approval, and provisioning stages.
   * System configuration enforces these boundaries where feasible.

📋 **Possible Evidence to Collect**

* Workflow diagram of the access request and provisioning process
* Role-based access control matrix separating duties
* Sample access request with documented approval trail
* IAM system screenshots showing enforced approval steps
* Audit logs showing approval and provisioning by separate individuals
* Internal policy stating segregation of duties for access provisioning

---