# Data Protection and Privacy

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4937580620/Data%20Protection%20and%20Privacy

**Created by:** Alexandria Burke on July 16, 2025  
**Last modified by:** Alexandria Burke on July 23, 2025 at 08:44 PM

---

**HITRUST Requirement – Confidentiality Agreements**  
Control ID: 05.e   
Control Type: Administrative  
Control Level: Organizational  
HIPAA Mapping:§164.308(a)(3)(ii)(A) ,§164.308(a)(3)(ii)(B),§164.308(a)(5)(i),§164.308(a)(8)

**Control Objective:**

Requirements for confidentiality and non-disclosure agreements are reviewed

1. at least annually and
2. when changes occur that influence these requirements.  
   Confidentiality and non-disclosure agreements
3. comply with all applicable laws and regulations for the jurisdiction to which it applies.

**Technical Implementation:**  
Policy & Governance:

A formal NDA policy is in place requiring all workforce members and third parties to sign an NDA prior to access. Annual reviews are scheduled.

HR/Contract Workflow:

Systems like Workday DocuSign are configured to:  Require NDA signature on on-boarding  - Track NDA dates  - Alert for re-review needs  
Access Control:

Access to systems handling PHI or CUI is gated by NDA compliance status. Users without a valid NDA cannot access sensitive systems.  
Audit & Logging:

All signed NDAs are stored securely and versioned. Audit logs track NDA acknowledgment, policy updates, and review activity.

📋 **Possible Evidence to Collect:**  
Sample of signed NDAs for employees, contractors, and third parties  
Current version of confidentiality/NDAs policy, including version history  
Documentation or calendar entries showing scheduled NDA reviews  
Records of NDA updates following regulatory, contractual, or operational changes  
Logs or screenshots showing system access is granted only post-NDA  
Evidence that NDA signing is part of personnel onboarding and offboarding processes

**HITRUST Requirement – Addressing Security When Dealing with Customers**  
Control ID: 05.j  
Control Type: Administrative  
Control Level: Organizational  
HIPAA Mapping:164.520, 164.530(a), 164.522

**Control Objective:**

The organization ensures that the public

1. has access to information about its privacy activities and
2. is able to communicate with its senior privacy official (e.g., Chief Privacy Officer, Chief Data Protection Officer).

**Technical Implementation:**  
Organizations should:

Maintain a publicly available privacy notice (e.g., on the company website) that outlines:

Categories of personal data collected,

Purpose for collection and processing,

Rights of individuals (e.g., access, correction, deletion),

How data is protected,

Who to contact regarding privacy concerns.

Clearly identify and publish contact information for a senior privacy official (e.g., CPO or DPO).

Ensure the privacy official is empowered to respond to inquiries and oversee privacy compliance.

Provide multiple communication channels for users to reach out (e.g., email, web form, mailing address).

Ensure periodic review and update of published privacy statements and contact information.

Integrate privacy contact points into incident response processes where applicable.

📋 **Possible Evidence to Collect:**  
Privacy Policy:URL or screenshot of public privacy notice  
Senior Privacy Contact :Organizational chart, job description, or announcement identifying the CPO/DPO  
Communication Logs:Inquiries submitted by the public and corresponding responses  
Review Records:Change logs showing periodic updates to privacy notices or contact info  
Website Screenshots:Confirmation of privacy contact info visible and accessible on public website

**HITRUST Requirement – Intellectual Property Rights**  
Control ID: 06.b  
Control Type: Administrative  
Control Level: Organizational  
HIPAA Mapping:164.308(a)(1)(ii)(B), 164.308(a)(3)(ii)(C), 164.312(c)(1)

**Control Objective:**

The organization

1. establishes restrictions on the use of open source software.  
   Open source software used by the organization is
2. legally licensed
3. authorized, and
4. adheres to the organizations secure configuration policy.

**Technical Implementation:**  
Organizations should:

Maintain an inventory of all installed software, including license status, version, and origin (open-source vs. proprietary).

Implement a formal software approval and procurement process, requiring:

Business justification,

License validation,

Security review (e.g., vulnerabilities, EOL status),

Compatibility with existing systems.

Establish a deny-by-default software policy, only permitting installation of pre-approved software.

Use configuration management tools to enforce secure installation and ensure security baselines are applied.

Monitor software usage and regularly audit for unlicensed or unauthorized software.

Define acceptable use of open-source software (e.g., Apache, GNU GPL) with required legal and security vetting.

📋 **Possible Evidence to Collect:**  
Software Inventory: List of software titles, license status, installation locations  
Software Policy:Formal policy restricting unlicensed/open-source use without approval  
Software Approval Records :Software request forms, security reviews, legal license verifications  
Configuration Documentation:Secure configuration standards or STIGs applied to installed software  
Audit Logs: Endpoint scans or asset management reports showing compliance with approved software list

**HITRUST Requirement – Protection of Organizational Records**  
Control ID: 06.c  
Control Type: Administrative  
Control Level: Organizational  
HIPAA Mapping:

**Control Objective:**

Guidelines are issued and implemented by the organization on the

1. ownership
2. classification
3. retention
4. storage
5. handling, and
6. disposal

of all records and information.

**Technical Implementation:**  
Organizations should:

Maintain an inventory of all installed software, including license status, version, and origin (open-source vs. proprietary).

Implement a formal software approval and procurement process, requiring:

Business justification,

License validation,

Security review (e.g., vulnerabilities, EOL status),

Compatibility with existing systems.

Establish a deny-by-default software policy, only permitting installation of pre-approved software.

Use configuration management tools to enforce secure installation and ensure security baselines are applied.

Monitor software usage and regularly audit for unlicensed or unauthorized software.

Define acceptable use of open-source software (e.g., Apache, GNU GPL) with required legal and security vetting.

📋 **Possible Evidence to Collect:**  
Software Inventory:List of software titles, license status, installation locations  
Software Policy:Formal policy restricting unlicensed/open-source use without approval  
Software Approval Records:Software request forms, security reviews, legal license verification  
Configuration Documentation:Secure configuration standards or STIGs applied to installed software  
Audit Logs:Endpoint scans or asset management reports showing compliance with approved software list

**HITRUST Requirement – Protection of Organizational Records**  
Control ID: 06.c  
Control Type: Administrative  
Control Level: Organizational  
HIPAA Mapping:64.310(d)(2)(i), 164.310(d)(2)(ii), 164.308(a)(1)(ii)(C), 164.312(c)(1)

**Control Objective:**

The organization’s established and implemented record retention program addresses:

1. the secure disposal of data when no longer needed for legal, regulatory, or business reasons, including disposal of covered and/or confidential information;
2. all storage of covered and/or confidential information; and
3. a programmatic review process (automatic or manual) to identify and remove covered and/or confidential information that exceeds the requirements of the data retention policy on a quarterly basis.

**Technical Implementation:**  
Organizations should:

Define and document data classification schemas to clearly identify covered and confidential records.

Maintain a data retention schedule, including legal, compliance, and business justifications for each category.

Configure automated purging tools or scheduled data lifecycle jobs to detect and remove stale records based on metadata or policy tags.

Ensure secure disposal methods such as:

DoD 5220.22-M data wipe,

NIST SP 800-88 media sensitization,

Certified shredding for physical records.

Log and monitor all deletion and disposal activities.

Review retention and disposal operations at least quarterly, and document results for audit readiness.

Apply secure storage controls (encryption, access controls, integrity checks) for data in retention.

📋 **Possible Evidence to Collect:**  
Retention Policy: Document outlining data types, retention duration, legal basis  
Disposal Logs: Records showing secure deletion or shredding events  
Quarterly Review Records: Audit logs or review checklists showing quarterly compliance checks  
Purging Tool Configurations: Screenshots or exports from systems (e.g., DLP, ECM) with retention/purge settings  
Training Records: Proof employees understand data disposal and retention handling procedures

**HITRUST Requirement – Protection of Organizational Records**  
Control ID: 06.c  
Control Type: Administrative, Technical   
Control Level: Organizational  
HIPAA Mapping:164.308(a)(1)(ii)(D, 164.310(d)(2)(i), 164.310(d)(2)(ii), 164.308(a)(1)(ii)(C),164.312(a)(2)(iv), 164.312(c)(1)

**Control Objective:**

A retention schedule

1. is drawn up identifying essential record types and the period of time for which they must be retained.  
   An inventory of sources of key information
2. is maintained.  
   Any related cryptographic keys
3. are kept securely and made available only when necessary.  
   Any related cryptographic keying material and programs associated with encrypted archives or digital signatures
4. are also stored to enable decryption of the records for the length of time the records are retained.  
   Records
5. are securely destroyed when retention is no longer necessary per the organization‘s record retention schedule.

**Technical Implementation:**  
In AWS, organizations should:

Define and Document a Retention Schedule:

* Create a data classification and retention matrix in a central documentation repository (e.g., AWS Systems Manager Parameter Store or Confluence).
* Categorize records such as logs (CloudTrail, Config), backups (RDS snapshots, S3), transaction data, audit reports, PHI/PII, etc.
* Include legal, regulatory, and business justification for each retention period.

Maintain Inventory of Record Sources and Cryptographic Dependencies:

* Maintain an inventory of encrypted data sources, including:
* S3 buckets with KMS encryption,
* Encrypted EBS volumes,
* RDS/Aurora backups,
* Secrets Manager or Parameter Store entries.
* Tag all data sources using AWS Resource Tags for classification and retention tracking.

Cryptographic Key and Tool Retention:

* Manage all cryptographic keys via AWS Key Management Service (KMS).
* Set key rotation policies aligned with data retention requirements.
* Store associated decryption tools or access metadata in a secure repository (e.g., S3 with limited access or Systems Manager Documents).
* Document key-material retention policy, and ensure KMS keys are retained and not deleted before all associated records are expired and purged.

Ensure Long-Term Decryptability:

* Implement key lifecycle controls to prevent deletion of KMS keys while encrypted data is within its retention period.
* Consider exporting encrypted archives along with their decryption metadata to Glacier Deep Archive or a vaulted S3 bucket for immutable storage.

Secure Disposal of Expired Records:

* Use S3 lifecycle policies, AWS Backup vault retention rules, and Config rules to automate deletion of data past its required lifecycle.
* Log all deletion events using AWS CloudTrail and validate compliance quarterly.
* Use AWS Certificate Manager and KMS policy enforcement to ensure expired keys are securely retired only after associated records are destroyed.

📋 **Possible Evidence to Collect:**  
  
Retention Schedule: Document or parameter file showing data categories and retention time frames  
AWS Config Rules :Evidence of rules enforcing S3/Backup/EBS lifecycle retention  
KMS Key Policies :Key policy statements showing protection and rotation settings  
Key Inventory: Exported KMS key metadata with usage and tags  
Destruction Logs: S3 or CloudTrail logs showing data and key deletion after expiration  
Tagging Reports: Reports showing proper tagging of classified resources with retention metadata

**HITRUST Requirement – Protection of Organizational Records**  
Control ID: 06.c  
Control Type: Administrative  
Control Level: Organizational  
HIPAA Mapping: §164.308(a)(1)(ii)(A) , §164.308(a)(1)(ii)(B), §164.316(b)(1) ,§164.530(j)

**Control Objective:**

Designated senior management within the organization reviews and approves the

1. security categorizations and
2. associated guidelines.

**Technical Implementation:**  
Develop a record classification scheme based on sensitivity, legal impact, and business function.

Use frameworks like FIPS 199 or NIST SP 800-60 to guide security categorization of information types (e.g., Low/Moderate/High).

Define handling guidelines (e.g., encryption, access control, disposal method) for each classification.

Define retention guidelines (e.g., 7 years for financial records, 6 years for HIPAA-related records).

Assign a Senior Management Authority (SMA) or Records Officer to formally review and approve:

Security categorization schema

Data handling guidelines

Retention schedules

Document approval decisions in a policy register or minutes from governance/oversight meetings.

Integrate approvals into the Information Governance or Risk Management Committee processes.

📋 **Possible Evidence to Collect:**

Signed or digitally approved record of security categorization framework (e.g., classification policy).

Meeting minutes or approval memo from senior management documenting formal review/approval.

Version-controlled handling guidelines and retention schedules.

Documentation showing mapping of record types to categories and retention policies.

Audit logs or policy repository entries showing senior management sign-off.

**HITRUST Requirement – Protection of Organizational Records**  
Control ID: 06.c  
Control Type: Administrative, Technical  
Control Level: Organizational  
HIPAA Mapping: §164.308(a)(3)(ii)(A) ,§164.312(a)(1) ,§164.312(c)(1) ,§164.312(e)(1) ,§164.310(c) ,§164.310(d)(1) ,§164.308(a)(7)(ii)(A–B)

**Control Objective:**

Important records, such as contracts, personnel records, financial information, client/customer information

1. are protected from loss, destruction, and falsification.  
   Security controls, such as access controls, encryption, backups, electronic signatures, locked facilities, or containers
2. are implemented to protect these essential records and information.

**Technical Implementation:**  
Identify and inventory essential records by category (e.g., contracts, HR records, financial, customer data).

Apply access control mechanisms (e.g., role-based access, least privilege) to limit exposure.

Implement encryption:

At rest (e.g., encrypted file systems, database encryption)

In transit (TLS/HTTPS for data transfer)

Enable automated and redundant backup systems with:

Versioning

Secure storage

Regular integrity testing

Use electronic signatures with audit trails for validation of authenticity and non-repudiation.

Store physical records in locked filing cabinets or restricted-access facilities with surveillance and badge control.

Track access to records and flag modifications with audit logging and monitoring tools.

Include records protection within the business continuity and disaster recovery plans.

📋 **Possible Evidence to Collect:**

Data classification registry showing list of important records and protection mechanisms.

Access control lists or IAM role definitions for sensitive record types.

Encryption configuration screenshots or policy documentation.

Backup schedules, retention policies, and last successful restore test report.

Electronic signature system logs or policy.

Physical security policy and facility access logs.

Audit logs showing access and modification attempts.

DR/BCP test results related to record recovery.

**HITRUST Requirement – Protection of Organizational Records**  
Control ID: 06.c  
Control Type: Administrative  
Control Level: Organizational  
HIPAA Mapping: §164.316(b)(2)(i) ,§164.528(b)(1) ,§164.530(j) ,§164.308(a)(1)(ii)(A) ,§164.308(a)(8)

**Control Objective:**

The organization’s

1. formal policies
2. formal procedures
3. other critical records (e.g., results from a risk assessment), and
4. disclosures of individuals’ protected health information  
   are retained for a minimum of six years.  
   For electronic health records, the organization
5. must retain records of disclosures to carry out treatment, payment and healthcare operations for a minimum of three years.

**Technical Implementation:**  
Store formal documents (policies, procedures, risk assessments, and PHI disclosure logs) in Amazon S3 with:

Versioning enabled for immutability and audit trails

Object Lock (Compliance Mode) for retention enforcement

S3 Lifecycle Policies to manage archive and deletion timelines (≥6 years for general, ≥3 years for EHR disclosures)

Tag and classify S3 objects using AWS Resource Tags (e.g., RecordType=RiskAssessment, Retention=6Years)

Use AWS KMS to encrypt records at rest (automated key rotation recommended)

Restrict access using S3 bucket policies, IAM roles, and AWS Organizations SCPs for organizational units

Maintain PHI disclosure logs in Amazon DynamoDB or RDS/Aurora, with:

Database snapshot retention (manual snapshots stored in S3 or Glacier Deep Archive)

Audit logging via AWS CloudTrail and Amazon RDS Enhanced Monitoring

Establish backup and disaster recovery using AWS Backup with defined backup plans and cross-region replication

Audit compliance using AWS Config Rules and AWS Security Hub for record retention enforcement and configuration drift

📋 **Possible Evidence to Collect:**

Retention policy documentation aligned with HIPAA (6 years for policies, 3 years for EHR disclosures)

S3 configuration:

Screenshot of versioning and Object Lock enabled

Lifecycle rule settings (retention policies)

Backup plan from AWS Backup showing frequency, duration, and storage class

Sample access control settings from IAM or S3 bucket policy

PHI disclosure log format and access permissions

CloudTrail logs showing access to protected records

AWS Config or Security Hub reports validating enforcement of retention policy

Audit logs of access or changes to policies and risk assessments

**HITRUST Requirement – Data Protection and Privacy of Covered Information**  
Control ID: 06.d  
Control Type: Administrative, Technical  
Control Level: Organizational  
HIPAA Mapping§164.312(a)(2)(iv) ,§164.312(e)(2)(i), §164.312(d) ,§164.308(a)(1)(ii)(A) ,§164.308(a)(1)(ii)(B) ,§164.310(d)(1)

**Control Objective:**

Covered and/or confidential information, at minimum

1. is rendered unusable, unreadable, or indecipherable anywhere it is stored, including on personal computers (laptops, desktops) portable digital media, backup media, servers, databases, or in logs.  
   Exceptions to encryption requirements
2. are authorized by management and documented.  
   Encryption
3. is implemented via one-way hashes, truncation, or strong cryptography and key-management procedures.  
   For full-disk encryption, logical access
4. is independent of O/S access.  
   Decryption keys
5. are not tied to user accounts.  
   If encryption is not applied because it is determined to not be reasonable or appropriate, the organization
6. documents its rationale for its decision or uses alternative compensating controls other than encryption if the method is approved and reviewed annually by the CISO.

**Technical Implementation:**  
Encrypt all stored covered/confidential information using FIPS 140-2 validated modules or equivalent:

File-level: BitLocker, FileVault, or S3 SSE (Server-Side Encryption)

Database: TDE (Transparent Data Encryption) in RDS/Aurora, DynamoDB Encryption at Rest

Backup media: Encrypted snapshots and backups via AWS Backup with KMS

Do not tie encryption keys to user accounts; use service accounts or HSMs

Implement one-way hashes or tokenization for data that doesn’t need reversibility (e.g., passwords, tracking IDs)

Ensure logical access to encryption keys is managed through:

AWS KMS or CloudHSM for cloud-based key management

Role-based access controls via IAM, with logging via CloudTrail or SIEM

Document all exceptions to encryption in an “Encryption Exception Register” and include:

Risk acceptance memo

Technical justification

Compensating controls (e.g., network segmentation, access control, masking)

CISO must review and reauthorize exceptions annually

Enable encryption of logs and audit trails, using centralized logging platforms (e.g., Amazon CloudWatch Logs with encryption, ELK Stack with encrypted indices)

📋 **Possible Evidence to Collect:**

Encryption policy and key management procedures

Screenshot or configuration evidence from:

AWS KMS key setup

Encrypted EBS volumes or S3 buckets

TDE-enabled database instances

Copy of encryption exception register and approval memos

Audit logs from key access events (CloudTrail, SIEM)

Documentation of compensating controls used in lieu of encryption

CISO-signed review of encryption exceptions (annual)

Screenshot of hashed/tokenized sample data or architectural diagram

**HITRUST Requirement – Data Protection and Privacy of Covered Information**  
Control ID: 06.d  
Control Type: Administrative, Technical  
Control Level: Organizational  
HIPAA Mapping:§164.306(a)(3) ,§164.308(a)(1)(ii)(A–B) ,§164.308(a)(8) ,§164.310(d)(1) ,§164.316(b)(2)(i)

**Control Objective:**

The organization limits the covered information

1. storage amount and
2. retention time  
   to that which is required for business, legal, and/or regulatory purposes, as documented in the data retention policy.  
   Covered and/or confidential information storage
3. is kept to a minimum.

**Technical Implementation:**  
Establish and enforce a formal data retention policy that defines:

Maximum retention periods per data category (e.g., PHI, PII, financial records)

Legal, regulatory, and business justification for each retention schedule

Classify covered/confidential information using data tagging and classification tools

Implement automated lifecycle management for stored data:

AWS S3 Lifecycle Policies to move data to Glacier or delete after set timeframes

Database record archival and purging based on timestamps or status flags

Log retention controls in centralized logging systems (e.g., CloudWatch, Splunk)

Use data minimization practices in systems and forms (collect only required fields)

Conduct periodic reviews (quarterly/annually) to:

Identify data that exceeds retention thresholds

Ensure old data is archived or deleted securely

Ensure systems storing covered information enforce automatic data purging after expiration

Document decisions to retain beyond normal thresholds with legal or executive approval

Apply encryption, masking, or tokenization to stored data awaiting purging

📋 **Possible Evidence to Collect:**

Data retention policy and classification matrix

Proof of lifecycle rules (e.g., AWS S3 lifecycle JSON or screenshot)

Log of purged or archived data (e.g., deletion reports, archival activity logs)

Audit trail of reviews or clean-up activities

System configuration showing data expiration settings (e.g., TTL in DynamoDB, log retention in CloudWatch)

Justifications and approvals for any extended retention exceptions

Documentation of data minimization practices in intake forms or system design

**HITRUST Requirement – Data Protection and Privacy of Covered Information**  
Control ID: 06.d  
Control Type: Administrative, Technical  
Control Level: Organizational  
HIPAA Mapping: §164.308(a)(1)(ii)(A) ,§164.308(a)(1)(ii)(B) ,§164.312(a)(1) ,§164.312(b) ,§164.306(a)(1–3)

**Control Objective:**

The organization

1. implements technical means to ensure covered information is stored in organization-specified locations.

**Technical Implementation:**  
Define and document authorized storage locations in a formal data storage policy:

Approved AWS regions (e.g., us-east-1, us-west-2)

Approved storage types (e.g., S3, RDS, DynamoDB, EBS)

Approved virtual environments -Commercial Cloud

Enforce region-based restrictions using:

AWS SCPs (Service Control Policies) at the organization or OU level to restrict resource creation to specific AWS regions

IAM policies that allow only designated storage services and buckets

S3 bucket policies and VPC endpoint policies to restrict data flow only to approved destinations

Use AWS Config Rules and AWS Security Hub to monitor for:

Storage in unauthorized regions

Use of unapproved storage services

Cross-region data replication

Implement data tagging (e.g., Data Classification=Covered, Approved Location=TRUE) and Config conformance packs to audit alignment

Disable or restrict use of personal/local storage via:

Endpoint Detection and Response (EDR) tools

DLP software to block unapproved data storage/syncing (e.g., Dropbox, USBs)

VDI (Virtual Desktop Infrastructure) enforcing centralized storage

Enable Amazon Macie to detect the presence of sensitive data in unauthorized S3 buckets

📋 **Possible Evidence to Collect:**

Data storage policy and list of approved storage locations/services

Screenshot or JSON config of:

SCPs and IAM policies enforcing region/service restrictions

S3 bucket policy enforcing access only from specific accounts or VPCs

AWS Config rule output showing enforcement of region or service compliance

Alerts or dashboards from AWS Security Hub or Amazon Macie

Asset inventory showing location of covered data (e.g., via AWS Resource Groups)

Proof of restricted endpoint access and DLP policy enforcement

Audit logs (CloudTrail) showing access to covered data only from approved services

**HITRUST Requirement – Data Protection and Privacy of Covered Information**  
Control ID: 06.d  
Control Type: Administrative  
Control Level: Organizational  
HIPAA Mapping: §164.312(e)(1) ,§164.312(e)(2)(ii) ,§164.308(a)(1)(ii)(B) ,§164.308(a)(3)(ii)(A) ,§164.310(b) ,§164.312(c)(1)

**HITRUST Requirement – Data Protection and Privacy of Covered Information**  
Control ID: 06.d  
Control Type: Administrative  
Control Level: Organizational  
HIPAA Mapping: §164.312(e)(1) ,§164.312(e)(2)(ii) ,§164.308(a)(1)(ii)(B) ,§164.308(a)(3)(ii)(A) ,§164.310(b) ,§164.312(c)(1)

**Control Objective:**

The organization

1. explicitly identifies and ensures the implementation of security and privacy protections for the transfer of organizational records, or extracts of such records, containing sensitive personal information to a state or federal agency or other regulatory body that lawfully collects such information.

**Technical Implementation:**  
Define and document a data transfer policy governing when and how organizational records containing Sensitive Personal Information (SPI) may be transferred externally to a regulatory entity.

Identify all types of sensitive personal information (SPI) subject to transfer, such as:

PHI (Protected Health Information)

PII (Personally Identifiable Information)

Financial records

Risk assessments and incident reports

Implement technical controls for secure data transfers:

Use FIPS 140-2 validated encryption during transmission (e.g., SFTP, HTTPS, TLS 1.2+)

Package and transmit data using secure file exchange platforms (e.g., AWS Transfer Family, AWS S3 pre-signed URLs, or FedRAMP Moderate secure portals)

Enable logging and audit trails of file generation, transfer, and acknowledgment

Apply data minimization and redaction techniques to only transmit necessary fields

Ensure recipient validation (agency verification) and dual authorization for transmission (e.g., data owner + compliance officer)

Use DLP (Data Loss Prevention) solutions to prevent unauthorized outbound transfers

Store transfer evidence (metadata, audit logs, confirmations) for regulatory retention periods

📋 **Possible Evidence to Collect:**

Written data transfer policy specifying requirements for SPI transmissions to agencies

* Encryption configuration and protocol logs showing secure transfer methods (SFTP, HTTPS)
* Audit logs or CloudTrail events showing file access, packaging, and transfer
* Secure file exchange logs or confirmation receipts from regulatory portals
* Records of dual authorization approvals for sensitive data exports
* DLP logs or policies related to outbound transfer monitoring
* Documented SPI classification schema with mapping to transfer workflows

The organization

1. explicitly identifies and ensures the implementation of security and privacy protections for the transfer of organizational records, or extracts of such records, containing sensitive personal information to a state or federal agency or other regulatory body that lawfully collects such information.

**Technical Implementation:**  
Define and document a data transfer policy governing when and how organizational records containing Sensitive Personal Information (SPI) may be transferred externally to a regulatory entity.

Identify all types of sensitive personal information (SPI) subject to transfer, such as:

PHI (Protected Health Information)

PII (Personally Identifiable Information)

Financial records

Risk assessments and incident reports

Implement technical controls for secure data transfers:

Use FIPS 140-2 validated encryption during transmission (e.g., SFTP, HTTPS, TLS 1.2+)

Package and transmit data using secure file exchange platforms (e.g., AWS Transfer Family, AWS S3 pre-signed URLs, or FedRAMP Moderate secure portals)

Enable logging and audit trails of file generation, transfer, and acknowledgment

Apply data minimization and redaction techniques to only transmit necessary fields

Ensure recipient validation (agency verification) and dual authorization for transmission (e.g., data owner + compliance officer)

Use DLP (Data Loss Prevention) solutions to prevent unauthorized outbound transfers

Store transfer evidence (metadata, audit logs, confirmations) for regulatory retention periods

📋 **Possible Evidence to Collect:**

Written data transfer policy specifying requirements for SPI transmissions to agencies

* Encryption configuration and protocol logs showing secure transfer methods (SFTP, HTTPS)
* Audit logs or CloudTrail events showing file access, packaging, and transfer
* Secure file exchange logs or confirmation receipts from regulatory portals
* Records of dual authorization approvals for sensitive data exports
* DLP logs or policies related to outbound transfer monitoring
* Documented SPI classification schema with mapping to transfer workflows

**HITRUST Requirement – Data Protection and Privacy of Covered Information**  
Control ID: 06.d  
Control Type: Administrative  
Control Level: Organizational  
HIPAA Mapping: §164.506 ,§164.510(b)

GLBA – Requires opt-out for sharing nonpublic personal information

GDPR Art. 6(1)(a) – Lawful processing based on data subject consent

State-specific privacy laws – e.g., CCPA, CPRA, Virginia CDPA, requiring consent or opt-out rights

**Control Objective:**

Where required by legislation

1. consent is obtained before any PII (e.g., about a client/customer) is emailed, faxed, or communicated by telephone conversation, or otherwise disclosed to parties external to the organization.

**Technical Implementation:**  
Establish a privacy and data sharing policy that defines when consent is required for sharing PII with external parties.

Implement a consent management process that:

Captures client/customer consent during intake, onboarding, or prior to disclosure

Records the scope, method (written/verbal/electronic), and date of consent

Stores the consent in a system accessible to staff prior to any disclosure

Integrate technical safeguards in communication channels:

Email systems with DLP and encryption controls to flag or block unapproved PII disclosures

Fax systems that require verification and approval

Softphone or VoIP systems with call monitoring or audit tags for verified disclosures

Apply role-based access controls to consent data and restrict disclosures to authorized personnel only

**Train personnel on:**

When consent is required

How to confirm consent is documented

What methods of communication are approved

Monitor and audit all PII disclosure activity to verify compliance with consent policies

📋 **Possible Evidence to Collect:**

Copy of privacy or consent policy aligned with applicable legislation (e.g., HIPAA, GLBA, state laws)

Sample consent forms (electronic or signed paper) and system screenshots where consent is tracked

System logs of communications involving PII with proof of consent

Access control logs showing only authorized users accessed or transmitted PII

DLP alerts or email system audit trails showing enforcement of disclosure rules

Staff training records on consent and disclosure procedures

Reports from consent management or CRM system showing consent tracking and expiration

**HITRUST Requirement – Regulation of Cryptographic Controls**  
Control ID: 06.f  
Control Type: Technical  
Control Level: Organizational  
HIPAA Mapping: §164.312(a)(2)(iv) , §164.312(e)(2)(ii) – Encryption of ePHI in transit

* NIST SP 800-53 Rev. 5 – SC-12 (Cryptographic Key Establishment), SC-13 (Use of Validated Cryptography)
* FIPS [140-2 / 140-3](tel:140-2/140-3) – Security requirements for cryptographic modules

**Control Objective:**

The encryption policy addresses the

1. type and strength of the encryption algorithm and
2. when used to protect the confidentiality of information.  
   The organization employs cryptographic modules
3. that are certified and
4. that adhere to the minimum applicable standards.

**Technical Implementation:**  
Establish an encryption policy that includes:

Approved encryption algorithms (e.g., AES-256, RSA 2048+, SHA-256+)

Minimum key lengths based on data classification

Protocols for encryption in transit (e.g., TLS 1.2 or higher) and at rest

Requirements to use FIPS 140-2/3 validated cryptographic modules for all encryption operations

Applicability guidance for different data types (e.g., PII, PHI, CUI)

Maintain an inventory of approved encryption libraries and tools (e.g., AWS KMS, OpenSSL FIPS mode, Microsoft CNG)

Configure systems to enforce use of compliant encryption, such as:

Enabling FIPS mode on Windows/Linux servers

Using FIPS-validated modules in cloud services (e.g., AWS CloudHSM, Azure Key Vault FIPS-compliant mode)

Enforcing encryption at rest and in transit across all cloud services (S3, EBS, RDS, etc.)

Train technical staff on selecting and using only approved cryptographic solutions.

Periodically review and update the encryption policy to align with current NIST and industry guidance.

📋 **Possible Evidence to Collect:**

Encryption policy document defining algorithm types, key strengths, and certification requirements

List of approved cryptographic libraries/modules with FIPS validation references

System configuration screenshots showing use of compliant encryption (e.g., FIPS mode = enabled)

Sample AWS KMS key configuration showing key spec (e.g., AES-256, RSA\_2048)

Cloud provider evidence of FIPS 140-2 validated cryptographic backends (e.g., AWS Artifact reports)

Training records for administrators and developers on encryption policy requirements

Audit logs or scanning tool reports verifying use of approved algorithms

**HITRUST Requirement – Information Labeling and Handling**  
Control ID: 07.e  
Control Type: Administrative, Technical  
Control Level: Organizational  
HIPAA Mapping: §164.312(a)(1) ,§164.306(a)(1–3)

**Control Objective:**

The organization

1. physically and/or electronically labels and handles sensitive information commensurate with the risk of the information or document.  
   Labeling
2. reflects the classification according to the rules in the information classification policy.

**Technical Implementation:**  
**Develop and maintain an Information Classification and Handling Policy that defines:**

Classification levels (e.g., Public, Internal, Confidential, Restricted)

Labeling standards for both physical and electronic documents

Handling rules per classification (e.g., storage, transmission, disposal)

Apply automated labeling tools for digital files and emails:

Use tools like Microsoft Purview Information Protection, AWS Macie, or custom DLP systems

Enforce mandatory metadata tagging and document watermarks for higher classifications

**For physical media/documents:**

Apply classification labels (e.g., stickers or stamps) to printed files

Store restricted materials in locked cabinets or controlled-access areas

Embed labeling in document templates or auto-tagging rules via DLP, email gateways, or file servers

Train users to recognize classification labels and follow handling requirements

Implement monitoring to detect unlabeled sensitive information and generate alerts

📋 **Possible Evidence to Collect:**

Information classification and labeling policy

Screenshots or exports showing labeling applied to emails/documents

Sample physical labels and photographs of labeled storage areas

Configuration of auto-labeling tools (Microsoft Purview, AWS Macie rules)

Audit logs from DLP or classification systems showing classification enforcement

Training records on classification and labeling procedures

Exception logs or alerts for unlabeled sensitive content

**HITRUST Requirement – Publicly Available Information**  
Control ID: 09.z  
Control Type: Administrative, Technical  
Control Level: Organizational  
HIPAA Mapping: §164.308(a)(3)(ii)(A), §164.530(c)

**Control Objective:**

The organization

1. designates individuals authorized to post information onto a publicly accessible information system, and
2. trains these individuals to ensure that publicly accessible information does not contain nonpublic information.

**Technical Implementation:**

**Develop a Public Information Posting Policy that includes:**

Definition of publicly accessible systems (e.g., external websites, social media, public portals)

Criteria for who may post and what content is permitted

Requirement to review content for non-public information before publishing

Designate and maintain a list of authorized individuals or roles (e.g., Communications, Marketing, PR)

Require training for authorized users on:

The difference between public vs. non-public information (e.g., PHI, PII, CUI, proprietary data)

Content review procedures and pre-approval workflows

Legal, compliance, and reputational risks of public disclosures

Implement a content review and approval workflow, such as:

Pre-publishing checklists

Two-person verification before posting

Centralized publishing tools with approval stages (e.g., CMS with role-based publishing rights)

Audit public content periodically to detect unauthorized or inappropriate disclosures

📋 **Possible Evidence to Collect:**

Public posting policy or standard operating procedure

List of personnel or roles designated as authorized to publish publicly

Training logs and completion certificates for authorized individuals

Sample pre-approval checklist or workflow diagram

Screenshots or exports from CMS showing restricted publishing roles

Records of public content audits or takedown actions

Incident reports or DLP alerts for accidental public posting of sensitive info

**HITRUST Requirement – Control of Internal Processing**  
Control ID: 10.c  
Control Type: Administrative, Technical  
Control Level: Organizational  
HIPAA Mapping: §164.308(a)(8) , §164.308(a)(1)(ii)(D) , §164.308(a)(6)(ii) ,§164.312(b)

**Control Objective:**

The organization:

1. develops and documents system and information integrity policy and procedures;
2. disseminates the system and information integrity policy and procedures to appropriate areas within the organization; and
3. reviews and updates defined system and information integrity requirements no less than annually.

**Technical Implementation:**

**Develop a System and Information Integrity (SII) Policy that includes:**

Monitoring and alerting practices (e.g., GuardDuty, CloudWatch, Security Hub)

Vulnerability management and patching

File integrity monitoring (e.g., AWS Systems Manager + AWS Config)

Incident detection and response processes

Document associated procedures that support the policy:

Daily log review and alert triage

Use of AWS Inspector for vulnerability scans

Use of AWS CloudTrail to audit API-level activity

Disseminate the policy and procedures:

Store policy documents in an internal Confluence page or AWS WorkDocs with access controls

Assign SII responsibilities to DevOps, Cloud Security, or Infrastructure teams

Include SII policies in onboarding and refresher training for engineering and IT staff

Review and update the SII policy annually:

Trigger a recurring annual review task in a GRC tool (e.g., Jira, ServiceNow, AWS Audit Manager)

Incorporate feedback from incidents, audit results, AWS service changes, or threat intel

Link controls to AWS-native services:

AWS Config for continuous compliance with integrity configurations

Amazon Macie for integrity of sensitive data

AWS CloudTrail + CloudWatch Logs for SIEM/SOC integration

AWS Systems Manager Patch Manager for managed OS-level patch compliance

📋 **Possible Evidence to Collect:**

Copy of the current SII policy and procedures (version-controlled)

Distribution log or evidence of availability (e.g., shared Confluence space, training platform record)

Role-based access evidence showing who can view/modify SII documents

Review log or calendar entry for last policy review/update

AWS Config snapshots showing continuous monitoring of integrity settings

CloudWatch dashboard or SIEM logs validating SII monitoring in place

Patch Manager configuration and recent compliance reports

Audit log showing dissemination or training participation

**HITRUST Requirement – Output Data Validation**  
Control ID: 10.e  
Control Type: Administrative, Technical  
Control Level: Organizational  
HIPAA Mapping: §164.312(c)(1) , §164.308(a)(1)(ii)(D)

**Control Objective:**

When doing system development (e.g., applications, databases), output validation:

1. is manually or automatically performed;
2. includes plausibility checks to test whether the output data is reasonable;
3. includes reconciliation control counts to ensure processing of all data;
4. includes providing sufficient information for a reader (e.g., to ensure that the client/customer they are serving matches the information retrieved, or subsequent processing system to determine the accuracy, completeness, precision, and classification of the information);
5. includes procedures for responding to output validation tests;
6. includes defining the responsibilities of all personnel involved in the data output process;
7. includes creating an automated log of activities in the data output validation process.

**Technical Implementation:**

Design validation logic within application code or AWS services (e.g., Lambda, Step Functions, Glue Jobs) to perform:

Reasonableness checks (e.g., output totals, expected ranges, null detection)

Reconciliation logic between input and output record counts or hash totals

Data format validation (e.g., schema validation, field presence)

Log all validation checks and results using:

Amazon CloudWatch Logs

AWS CloudTrail for process-level audit trails

AWS Lambda and Step Functions logs for data processing paths

Create structured output logs or validation status summaries in:

Amazon S3 (for archival with object-level immutability)

DynamoDB or Amazon Athena (for structured queries/reporting)

Define and document:

Personnel roles and responsibilities (e.g., DevOps, QA, Data Engineers)

Error handling procedures for failed validation (e.g., SNS alerts, automated remediation)

Use CI/CD pipeline integration (e.g., AWS CodePipeline, GitHub Actions) to test output validity during development stages.

Provide meaningful and labeled output summaries to end-users or consumers, using:

Custom reports stored in S3, QuickSight dashboards, or exported via API Gateway

Define escalation procedures for output validation failures (e.g., notify QA lead or compliance officer).

📋 **Possible Evidence to Collect:**

Output validation SOPs or architecture documentation

Application code or Lambda function logic showing output validation routines

CloudWatch or S3 logs demonstrating reasonableness/reconciliation checks

Sample output logs with success/failure indicators

Output validation summary/report delivered to users

Role assignment or RACI matrix for personnel responsibilities

Screenshots of alert configurations (SNS, EventBridge, etc.) for failed validations

CI/CD job logs including test case for output validation

Access logs from CloudTrail or IAM showing personnel activity related to output validation

**HITRUST Requirement – Protection of System Test Data**  
Control ID: 10.i  
Control Type: Administrative, Technical  
Control Level: Organizational  
HIPAA Mapping: §164.308(a)(1)(ii)(A) , §164.308(a)(3)(ii)(A) , §164.312(c)(1) , §164.308(a)(4)

**Control Objective:**

The use of operational databases containing covered and/or confidential information for non-production (e.g., testing) purposes

1. is avoided; however, if covered and/or confidential information is used for testing purposes, all sensitive details and content is removed or modified beyond recognition (i.e., de-identified) before use.

**Technical Implementation:**

**Establish a Test Data Management Policy that explicitly:**

Prohibits direct use of production data in test/dev environments unless formally approved

Requires de-identification, redaction, or synthetic generation of test data

Defines roles responsible for data sanitization and review

Use data masking, anonymization, or tokenization tools to sanitize data before use:

AWS Glue with PII redaction scripts

Amazon Macie for identifying sensitive data prior to transfer

Custom Lambda scripts for pseudonymization or value substitution

Tools like Informatica TDM, Delphix, or DataVeil for advanced masking

Automate detection of sensitive data before use in lower environments:

Scan test datasets with Amazon Macie for PII/PHI patterns

Enforce tagging or data classification of test vs. production assets

Ensure all test environments are isolated and access-controlled:

Use separate AWS accounts or isolated VPCs for test/dev

Apply least-privilege IAM roles and deny access to masked fields where appropriate

Log and review test dataset creation, access, and sanitization:

Use CloudTrail, CloudWatch, or a CMDB to audit data movement

Keep records of data transformation steps and approvals

📋 **Possible Evidence to Collect:**

Test Data Management Policy or SOP

Approval records or change tickets for production-to-test data use

Masked data samples or transformation scripts

Amazon Macie findings reports for sanitized test sets

Screenshots or logs showing masking, redaction, or tokenization configuration

Network diagrams showing separation of test and production environments

IAM access control logs limiting access to test datasets

Audit logs showing deletion or expiration of test dataset