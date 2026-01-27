# Network Protection

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4910383122/Network%20Protection

**Created by:** Alexandria Burke on July 04, 2025  
**Last modified by:** Shreya Singh on August 12, 2025 at 05:25 PM

---

**HITRUST Requirement – Policy on the Use of Network Services: 08 – Network Protection**  
Control ID: 01.i Policy on the Use of Network Services  
Control Type: Technical + Operational  
Control Level: Organizational Control  
HIPAA Mapping: 164.312(a)(1), 164.312(c)(1), 164.312(d), 164.308(a)(1)(ii)(D) ,164.308(a)(5)(ii)(C)

**Control Objective:** To ensure that only authorized users and systems may access internal network services using approved and secure protocols. The organization must:

* Maintain and enforce a network services usage policy
* Prevent the use of unauthorized or insecure services
* Require secure authentication for internal and remote device access
* Ensure external and third-party devices meet minimum-security standards
* Continuously review and document which protocols/services are in use

**Technical Implementation**

All network service access is scoped using:

* AWS Security Groups (SGs) with deny-by-default posture
* AWS Network Firewall to restrict protocol/port traffic
* VPC endpoint policies to enforce PrivateLink-only access for services like S3, KMS

A living Approved Services & Protocols Matrix defines which ports/services are allowed (e.g., HTTPS 443, DNS 53):

* Any legacy/insecure protocols (FTP, Telnet) are explicitly blocked
* Use of such protocols must be documented and justified through risk exception process

Remote access to AWS environments is restricted to:

* AWS Client VPN with mutual TLS + IAM Identity Center
* AWS Systems Manager Session Manager with IAM-based session control and CloudWatch logging

All enterprise and third-party endpoints accessing the internal network must:

* Be enrolled in AWS Systems Manager Inventory (or MDM if on-prem)
* Meet baseline standards (patched, tagged, software profiled)
* Be scanned by GuardDuty and logged in Security Lake

Any third-party access (e.g., research partners) must:

* Route through secure VPN
* Be validated against published minimum-security requirements
* Be pre-registered in the system with device and contact metadata

Config Rules monitor for:

* Unauthorized open ports
* Unapproved protocol usage
* Missing tags for device identity (`Device-ID`, `PHI\_Access`)

**Possible Evidence to Collect**

* Network Services Usage Policy
* Approved Protocol & Port Matrix
* Security Group Baseline
* AWS Config Rule Snapshots
* Client VPN Configuration w/ mTLS
* SSM Device Inventory Export
* Patch Compliance Report
* GuardDuty Finding Export (related to services)
* Exception Forms for Unusual Protocols
* Quarterly Network Access Review Notes

---

**HITRUST Requirement – Equipment Identification and Network Access Control Domain: 08 – Network Protection**  
Control ID: 01.k Equipment Identification in Networks  
Control Type: Technical  
Control Level: System Control  
HIPAA Mapping: 45 CFR §164.312(a)(1), (c)(1), (d)

**Control Objective**

The organization must uniquely identify and authenticate network devices before granting them access to the network, especially in scenarios involving remote access. Shared device attributes (e.g., MAC address, IP, certificates) may be used as part of the access control mechanism.

**Technical Implementation**

* Device Identification: All EC2, WorkSpaces, and VPN clients must have identifying tags such as Device-ID, PHI\_Access, and Owner. Enforce tagging with AWS Config managed rules.
* Remote Device Access: Only permit remote device access via AWS Client VPN using mutual TLS authentication (client certificate + IAM Identity Center user).
* Endpoint Service Control: Use VPC Interface Endpoints (PrivateLink) with strict endpoint policies to allow access only from identified, tagged resources.
* EC2 Identity Verification:Enforce IAM instance profiles and require all EC2-based access to use AWS Systems Manager Session Manager. SSH must be blocked via Security Groups.
* Tag Enforcement + Monitoring: Apply AWS Config rules: required-tags, restricted-common-ports, and ec2-instance-managed-by-ssm.
* Logging & Auditability: Enable CloudTrail, VPC Flow Logs, and SSM session logging to S3 with centralized access via Security Hub/SIEM.
* MAC/IP Filtering: If additional network layer filtering is required, implement AWS Network Firewall with domain/IP allow-lists per zone.

**Possible Evidence to Collect**

* Client VPN Configuration
* SSM Device Inventory Export
* Tag Compiance Rule Screenshot
* VPC Endpoint Policy (PHI Zone)
* Sample Flow Log of Device Session

---

**HITRUST Requirement – Firewall and Wireless Network Segmentation**

Control ID: 01.m Segregation in Networks  
Control Type: Technical  
Control Level: System + Infrastructure  
HIPAA Mapping: 164.312(a)(1) – Access Control , 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Protect internal systems and confidential information by enforcing network perimeter controls through firewalls and ensuring wireless networks are segmented and controlled.

🔧 **Technical Implementation**

1. **VPC Security Gateways**:

   * AWS implements security gateways between VPCs, on-prem environments (via Direct Connect or VPN), and the Internet using services like AWS Network Firewall, VPC route tables, and security groups.
   * Gateways protect traffic flowing between public subnets (DMZ) and internal workloads.
2. **Internal Network Segmentation**:

   * Subnets are segmented into public, private, and isolated zones using VPC architecture.
   * Network ACLs (NACLs) and Security Groups filter inbound and outbound traffic between tiers.
   * AWS Transit Gateway or third-party firewall appliances enforce inter-VPC policies.
3. **Firewall Enforcement**:

   * AWS Network Firewall and WAF (Web Application Firewall) enforce granular policies including domain/IP filtering, protocol controls, and deep packet inspection.
   * Unauthorized connections are logged and blocked in accordance with AWS Firewall Manager policies.
4. **Wireless Network Segregation (Hybrid)**:

   * In hybrid or on-prem environments connected via AWS Outposts, Wi-Fi networks are segmented at the switch level and VLANs route through firewalled connections before reaching AWS environments.
   * Wireless access points do not bridge directly to AWS-connected infrastructure.
5. **Wireless-to-Confidential Systems Isolation**:

   * AWS policies mandate a firewall or secure proxy between wireless systems and any environment that processes PHI or sensitive business data.
   * For workloads accessible via wireless devices, authentication and encryption are enforced (e.g., via Amazon WorkSpaces, Client VPN with MFA).

📋 **Possible Evidence to Collect**

* AWS Network Firewall or third-party firewall configuration screenshots
* VPC architecture diagram showing DMZ, private zones, and interconnects
* Security group and NACL configuration files
* Config Rule findings validating segmentation
* Firewall Manager policy documents
* Documentation showing that wireless devices route through gateway/proxy
* Network topology showing isolation of Wi-Fi to confidential infrastructure
* CloudTrail or GuardDuty alerts related to unauthorized access attempts

---

**HITRUST Requirement – Logical Network Segmentation and Domain Separation**

Control ID: 01.m Segregation in Networks  
Control Type: Technical  
Control Level: System + Infrastructure  
HIPAA Mapping: 164.308(a)(1)(ii)(A) – Risk Analysis, 164.308(a)(7)(ii)(B) – Disaster Recovery , 164.312(a)(1) – Access Control

🎯 **Control Objective**

Reduce security risk and service disruption impact by segmenting networks into logical domains based on risk and business function. Ensure secure separation between internal and external systems, including isolation of public-facing infrastructure.

🔧 **Technical Implementation**

1. **Logical Domain Segmentation**:

   * AWS uses Virtual Private Cloud (VPC) constructs to define internal vs. external network domains.
   * Public subnets are used for Internet-facing systems (e.g., ALBs, bastions) and private subnets for internal workloads.
   * Security groups and network ACLs enforce access restrictions at both instance and subnet level.
2. **Flow Control Using Routing**:

   * Route tables and NACLs control traffic flow between subnets.
   * Internet gateways, NAT gateways, and VPC peering connections are configured with strict access policies.
3. **Risk-Based Domain Definition**:

   * Organizations define subnet and workload placement using threat models and criticality (e.g., PHI-handling workloads in isolated private subnets).
   * AWS Landing Zones or Control Tower baselines enforce this architecture.
4. **Graduated Set of Controls by Environment Type**:

   * Different control sets are applied to staging, production, and public-facing tiers via AWS Service Control Policies (SCPs) or IAM boundary policies.
   * For example, production environments are locked down via restricted IAM roles and deny-all SCPs.
5. **Public Subnet Separation**:

   * Systems that require public IPs (e.g., ALBs, public bastions) reside in public subnets with limited routing and security groups to access private systems.
   * Private resources like EC2 instances, RDS databases, and S3 buckets use private subnets with no direct Internet routing.
6. **Verification of Internet-Accessible Servers**:

   * AWS Config or Security Hub is configured to detect EC2 instances with public IPs and flag those that aren’t tagged for business need.
   * Unnecessary public instances are moved to private subnets or flagged for remediation.
7. **Cost-Performance-Aware Segmentation**:

   * AWS network segmentation architecture (e.g., use of Transit Gateways or VPC endpoints) is chosen based on required isolation level and latency or throughput needs.
8. **Information Classification-Based Segregation**:

   * High-trust workloads (e.g., handling PII or PHI) are logically isolated using dedicated VPCs or accounts, and accessed only through approved IAM roles and VPNs.
   * Resource tags and AWS Organizations’ service control policies enforce segregation by business function or trust level.

📋 **Possible Evidence to Collect**

* VPC architecture diagrams showing public vs. private segmentation
* Subnet and route table configuration screenshots
* AWS Config rules enforcing isolation of public EC2 instances
* Security group and NACL definitions
* Network segmentation policy or baseline architecture documentation
* Evidence of SCPs and IAM boundaries per environment
* GuardDuty or Security Hub findings related to misconfigured public access
* Asset classification matrix showing network mapping to data criticality
* AWS Trusted Advisor checks for public access misconfigurations

---

**HITRUST Requirement – Network Segregation During Migration to Virtualized Servers**

Control ID: 01.m Segregation in Networks  
Control Type: Technical  
Control Level: System + Infrastructure  
HIPAA Mapping: 164.308(a)(1)(ii)(A) – Risk Analysis, 164.308(a)(1)(ii)(B) – Risk Management , 164.312(a)(1) – Access Control

🎯 **Control Objective**

Ensure that production-level networks are protected from risks introduced during migration processes by isolating transitional workloads—such as physical-to-virtual (P2V) servers, applications, and data—in segregated network environments.

🔧 **Technical Implementation**

1. **Network Isolation During Migration**:

   * During migration to AWS (e.g., via AWS Application Migration Service or AWS Snowball), workloads are placed in staging or isolated subnets/VPCs.
   * AWS Landing Zone architectures or Control Tower guardrails ensure non-production workloads are segmented from production environments.
2. **Staging Zones for Transitional Assets**:

   * Migrated EC2 instances or containerized workloads are deployed to a quarantine VPC or a dedicated migration account until tested, hardened, and validated.
   * IAM roles and VPC security groups restrict cross-environment access.
3. **Application-Level Segmentation**:

   * AWS Resource Access Manager (RAM) and Service Control Policies (SCPs) prevent migrated resources from interacting with production services until promotion.
   * Services like AWS Firewall Manager and VPC Traffic Mirroring are used to inspect traffic patterns before production release.
4. **Data Transfer Controls**:

   * When data is migrated using AWS DataSync or Snowball, it is first stored in temporary S3 buckets or EBS volumes that are not directly accessible from production systems.
   * Lifecycle policies ensure data is promoted only after integrity and classification checks.
5. **Validation Gates Before Promotion**:

   * Pre-production environments include automated security assessments (e.g., using Amazon Inspector or custom Lambda scripts) before migrated resources are released to production.
   * AWS Config ensures baseline conformance before tagging workloads as production-ready.

📋 **Possible Evidence to Collect**

* AWS account/VPC architecture diagram showing isolation of migration environments
* Security group and route table configurations for staging vs. production
* SCP or organizational unit policies restricting resource movement
* CloudTrail logs showing creation and movement of migrated workloads
* Output from AWS Config conformance packs applied to new resources
* Inspector or GuardDuty findings pre- and post-migration
* DataSync job logs showing isolation of data storage
* Documentation of promotion process and change control approvals
* Evidence of firewall rules or subnet segmentation during migration phase

---

**HITRUST Requirement – Deny-by-Default Network Interface Policy**

Control ID: 01.n Network Connection Control  
Control Type: Technical  
Control Level: System + Infrastructure  
HIPAA Mapping: 164.312(a)(1) – Access Control, 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Ensure that network traffic is tightly controlled at managed interfaces by applying a default-deny policy, allowing only explicitly authorized traffic to flow in accordance with access control policies and business application requirements.

🔧 **Technical Implementation**

1. **Default-Deny Firewall Posture**

   * AWS implements deny-by-default across:

     + Security Groups: No inbound traffic is permitted unless explicitly allowed.
     + Network ACLs: Can be configured with deny-all default rules.
     + AWS WAF: Configured with default action = block unless overridden by a permit rule.
2. **Managed Interface Control Points**

   * Interfaces such as VPC Internet Gateways, NAT Gateways, and Transit Gateways enforce access control via:

     + Routing tables
     + Firewall policies
     + AWS Network Firewall rules
3. **Segmentation and Business Application Enforcement**

   * VPCs and subnets are designed based on application roles. Only required services (e.g., ALB for a public app) have network access.
   * PrivateLink is used to restrict internal connectivity to specific AWS services.
   * IAM policies and VPC endpoints control application-layer access to services from specific subnets or endpoints.
4. **User-Based Restrictions**

   * End-user access to internal networks (via Client VPN or Direct Connect) is:

     + Limited by authorization rules tied to identity (IAM/SSO).
     + Further restricted via security groups, route tables, and AWS Verified Access (for browser-based internal access).

📋 **Possible Evidence to Collect**

* Security Group configurations showing default deny (no inbound unless explicitly permitted)
* Network ACLs with explicit deny rules for unmanaged or unapproved traffic
* AWS WAF policies with default action set to block
* AWS Network Firewall rule sets demonstrating default-deny
* VPC route tables and interface endpoint policies
* IAM or Verified Access policies limiting user access based on application need
* CloudTrail logs showing attempted denied connections
* Documentation of network segmentation strategy aligned to application roles
* Change control records for exceptions to the default-deny policy

---

**HITRUST Requirement – Control of External Connections and Managed Interfaces**

Control ID: 01.n Network Connection Control  
Control Type: Technical  
Control Level: System + Infrastructure  
HIPAA Mapping: 164.312(a)(1) – Access Control , 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Ensure that user and system communications are restricted, monitored, and secured through defined interfaces, including firewalls and managed gateways. Prevent unauthorized transmission of data, enforce communication policies, and protect the confidentiality and integrity of information in transit.

**🔧 Technical Implementation**

1. **User Connection Restrictions via Network Gateways**

   * AWS Security Groups, Network ACLs, and AWS Network Firewall enforce traffic filtering at both instance and subnet levels.
   * Traffic rules include protocol, port, IP address, and time-based rules (via Lambda or Firewall Manager custom rules).
2. **Restricted Protocols and Applications**

   * Outbound access to FTP, peer-to-peer services, and unauthorized email clients is blocked using:

     + VPC egress rules
     + AWS Network Firewall stateless rule groups
     + Route 53 DNS Firewall to prevent resolving prohibited domains
3. **Time-Based Access Controls**

   * AWS IAM policies and Lambda automation can restrict access to services by time-of-day (e.g., block Console or API access outside business hours).
   * Custom AWS WAF rate-based rules or GuardDuty alerts can trigger temporary IP blocking.
4. **Limiting External Network Connections**

   * Direct access to external networks is controlled via:

     + NAT Gateways
     + VPC Endpoints (used in lieu of open internet routing)
     + PrivateLink for SaaS access
   * AWS Config + Firewall Manager policies flag usage of unnecessary egress paths (e.g., desktop modems or unmanaged tunnels).
5. **Managed Interfaces for External Communication**

   * Each VPC or site-to-site VPN/Direct Connect interface is monitored by AWS CloudWatch and VPC Flow Logs.
   * External transmission interfaces (VPNs, Direct Connect, Internet Gateways) are logged and monitored via CloudTrail, Flow Logs, and Firewall Insights.
6. **Traffic Flow Policy Per Interface**

   * Defined through AWS Network Firewall policies, Security Groups, and AWS Firewall Manager rulesets.
   * AWS Service Control Policies (SCPs) prevent services from initiating network egress if not approved.
7. **Confidentiality and Integrity Protections**

   * TLS 1.2+ enforced for data in transit (via ALB, API Gateway, CloudFront).
   * Client VPN or Site-to-Site VPNs for encrypted tunnels.
   * Macie flags sensitive data moving through S3 or to external domains.
   * KMS-integrated TLS and SSL inspection with third-party gateways for high-sensitivity data.

📋 **Possible Evidence to Collect**

* Security Group and Network ACL rule sets
* AWS Network Firewall rule groups and policy definitions
* IAM time-based policy scripts or Lambda access controllers
* Route 53 DNS Firewall logs blocking peer-to-peer domains
* Flow Logs and CloudTrail showing traffic direction, protocol, and interface used
* AWS Config Rule output: External network interfaces tracked
* Firewall Manager audit reports per managed interface
* VPN or Direct Connect configuration audit trail
* TLS configurations on ELBs and CloudFront
* Macie or GuardDuty findings showing protection of sensitive data in transit

---

**HITRUST Requirement – Secure Transmission of Sensitive Information**

Control ID: 01.n Network Connection Control  
Control Type: Technical  
Control Level: System + Infrastructure  
HIPAA Mapping: 164.312(e)(1) – Transmission Security, 164.312(e)(2)(ii) – Encryption

🎯 **Control Objective**

Ensure that sensitive information is protected during transmission, particularly over open or public networks, by enforcing encryption and other security controls that maintain confidentiality and integrity.

🔧 Technical Implementation

1. **Encryption for Sensitive Data Transmission**

   * All services that transmit sensitive data (e.g., APIs, storage uploads, email) are configured to require encryption in transit.
   * TLS 1.2 or 1.3 is enforced using:

     + Elastic Load Balancer (ELB) or Application Load Balancer (ALB) listeners
     + CloudFront distributions with TLS-only viewer protocols
     + API Gateway enforcing HTTPS endpoints only
     + AWS Transfer Family with FTPS/SFTP enforced
   * For internal services, PrivateLink, Client VPN, or Site-to-Site VPN is used to protect non-public transmission.
2. **Service-Specific Encryption Enforcement**

   * S3 Buckets have `aws:SecureTransport` enforced via bucket policies to block unencrypted HTTP requests.
   * AWS WorkMail, SES, and SNS use STARTTLS for SMTP and TLS over HTTPS.
   * AWS Kinesis, Redshift, and RDS enforce SSL/TLS for connections.
3. **Public Network Protection**

   * Any data sent over the Internet (e.g., SaaS integrations, end-user apps) is wrapped with end-to-end TLS and optionally signed using:

     + AWS Certificate Manager (ACM) for server certificates
     + AWS Signer or customer PKI infrastructure
4. **Automated Detection and Enforcement**

   * Amazon Macie detects PII or sensitive data moving unencrypted.
   * AWS Config Rules can check for services not enforcing TLS.
   * GuardDuty alerts on suspicious exfiltration attempts or data transfers to untrusted endpoints.

📋 **Possible Evidence to Collect**

* TLS configuration policies from CloudFront, ALB, and API Gateway
* S3 bucket policies enforcing SecureTransport
* Certificate usage reports from ACM
* VPN or PrivateLink configurations used for non-Internet paths
* AWS Config rule evaluations on encryption-in-transit settings
* GuardDuty or Macie findings on plaintext traffic or unencrypted sensitive data
* Security Group rules showing blocked ports for non-TLS protocols
* Documentation of system architecture diagrams showing encrypted pathways

---

**HITRUST Requirement – Manage Exceptions to Traffic Flow Policy**

Control ID: 01.n Network Connection Control  
Control Type: Technical  
Control Level: System + Infrastructure  
HIPAA Mapping:

* 164.308(a)(1)(ii)(D) – Information System Activity Review
* 164.312(a)(1) – Access Control

🎯 **Control Objective**

Ensure that any exceptions to defined traffic flow policies are justified, time-bound, periodically reviewed, and removed once the business need no longer exists, reducing unnecessary exposure and maintaining a least-privilege network model.

🔧 **Technical Implementation**

1. **Documenting Traffic Flow Exceptions**

   * All non-standard or exception-based security group rules, NACL configurations, or VPC route table entries must be:

     + Tracked using AWS Systems Manager Parameter Store or AWS Config Custom Rules tagged with:

       - `business-justification`
       - `expiration-date`
     + Managed via Infrastructure as Code (IaC) templates like Terraform or AWS CloudFormation for traceability.
2. **Duration Tracking and Expiry Enforcement**

   * Expiration dates for traffic flow exceptions are enforced via:

     + Custom Lambda functions or EventBridge rules that disable or notify when rules near expiration.
     + Security Hub findings and Config Rules integrated with AWS ChatOps or ticketing systems for review cycles.
3. **Annual Review**

   * Exceptions are evaluated at least once every 365 days by:

     + AWS Config conformance packs evaluating security group rules marked as “temporary” or “exception.”
     + Automated Security Review Workflows triggered through AWS Audit Manager or JIRA automation integrated with code repositories (e.g., pull request reminders).
     + Tag compliance audits using tools like Steampipe, AWS CLI scripts, or CloudQuery.
4. **Exception Removal**

   * Traffic flow exceptions are automatically removed or flagged when:

     + The associated EC2 instance, ECS task, or Lambda function is terminated.
     + The `business-justification` tag is missing or expired.
     + Exception is not renewed through approval systems tracked in AWS Service Catalog or custom approval workflows.

📋 **Possible Evidence to Collect**

* Security group rule inventory with attached `business-justification` and `expiration` tags
* AWS Config rule outputs showing exceptions under review or expired
* Lambda or EventBridge automation logs enforcing expiration policy
* Terraform/CloudFormation templates with comments or parameters identifying temporary network exceptions
* Audit logs showing approval workflows (e.g., tickets, pull requests)
* Screenshots of removal activity or CloudTrail entries logging deletion of expired rules
* Documented exception review reports for past 12 months

---

**HITRUST Requirement – Prevent Simultaneous Remote and Non-Remote Connections**

Control ID: 01.n Network Connection Control  
Control Type: Technical  
Control Level: System + Endpoint  
HIPAA Mapping: 164.312(a)(1) – Access Control, 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Prevent remote devices from creating simultaneous secure (non-remote) and insecure (external) network connections to reduce the risk of data leakage, unauthorized access, and split-tunneling vulnerabilities.

🔧 **Technical Implementation**

1. **Enforcing Single Network Path Access (Disabling Split Tunneling)**

   * AWS VPN Client configuration or third-party VPN solutions (e.g., OpenVPN, Prisma Access) are set to disable split tunneling:

     + Configure the VPN to tunnel all traffic (0.0.0.0/0) through the corporate network.
     + Ensure no local LAN access is allowed while the VPN session is active.
2. **Conditional Access Enforcement via Device Posture Checks**

   * Use AWS Verified Access or integrate with AWS Identity Center (IAM Identity Center) and device trust policies (e.g., CrowdStrike, Jamf, Intune) to:

     + Ensure device posture is verified before access to sensitive AWS resources is granted.
     + Prevent access if a non-approved connection route exists.
3. **Endpoint Enforcement**

   * Use AWS WorkSpaces or AppStream 2.0 with session controls:

     + Ensure virtual desktop infrastructure prevents use of local storage, USB, or secondary interfaces.
     + Block split network paths via Group Policy Objects (GPOs) or endpoint firewall rules.
4. **Monitoring for Dual-Path Connections**

   * AWS GuardDuty or CloudWatch custom metrics can alert if traffic from a remote user is simultaneously seen from unapproved IP ranges or ASN (Autonomous System Numbers).
   * VPN appliance logs are centralized in CloudWatch Logs and scanned for connection anomalies.

📋 **Possible Evidence to Collect**

* VPN client configuration screenshots or profiles showing “Disable split tunneling” enabled
* IAM Identity Center or Verified Access policies enforcing device posture
* Endpoint management policy (e.g., GPO or MDM) enforcing network access restrictions
* Logs from AWS WorkSpaces or AppStream sessions restricting secondary network interfaces
* Security incident reports showing detection of split tunneling attempt
* Documentation from vulnerability management tool confirming dual-path access is blocked
* Screenshot or CLI output of `route` or `ipconfig` during VPN session showing full-tunnel enforced

---

**HITRUST Requirement – Enforce Secure Proxy and Network Routing Controls**

Control ID: 01.o Network Routing Control  
Control Type: Technical  
Control Level: Network + Infrastructure  
HIPAA Mapping: 164.312(a)(1) – Access Control, 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Ensure that outbound traffic to external networks is filtered, logged, and routed through secure, authenticated proxies in order to enforce access restrictions, prevent data leakage, and conceal internal assets.

🔧 **Technical Implementation**

1. **Firewall Enforcement and Address Validation**

   * AWS Network Firewall or WAF is deployed at network control points to:

     + Validate source/destination IPs and ports.
     + Enforce geofencing, IP reputation, or block known malicious IPs.
     + Use stateful rules to inspect outbound connections.
2. **Proxy-Based Internet Access Control**

   * Configure AWS PrivateLink or NAT Gateway to route all internet-bound traffic through:

     + A central proxy server such as Squid, Zscaler, or Palo Alto VM-Series in a dedicated VPC.
     + Or use AWS Network Firewall with FQDN allowlists to restrict outbound domains.
3. **Decryption, Logging, and Filtering at the Application Layer**

   * Use a transparent forward proxy (like Squid or a third-party virtual appliance):

     + Enable TLS inspection for HTTPs traffic (decrypt + re-encrypt via proxy).
     + Enable deep packet inspection (DPI) and log full TCP sessions.
     + Block by domain, IP, and path using ACLs and custom policy rules.
4. **Enforced Routing via Authenticated Proxy**

   * AWS Route Tables, Security Groups, and NACLs ensure that direct outbound access is denied unless traffic is routed through the proxy.
   * Use IAM roles + AWS Client VPN or SSO to enforce user-level authentication for outbound proxy access.
5. **Internal Address Protection**

   * Use Private IP ranges, VPC Subnets, and Route 53 private DNS to:

     + Hide directory services (e.g., AWS Managed AD) from external resolution.
     + Deny internet access to internal IP spaces using NAT Gateway controls.
6. **Routing Control Based on Access Policy**

   * Leverage AWS Network ACLs, Transit Gateway route tables, and AWS Firewall Manager policies:

     + Ensure routing rules conform to least privilege and compliance policies.

📋 **Possible Evidence to Collect**

* AWS Network Firewall policies and rule groups showing domain/IP blocking
* Proxy configuration files or screenshots (Squid, Zscaler, etc.)
* VPC Route Table and Security Group outputs showing internet-bound traffic routing through proxy
* Session logs or CloudWatch logs showing TCP session logging and URL filtering
* TLS decryption policies showing MITM proxying configuration
* Network ACL and NAT Gateway rules enforcing non-bypassable outbound paths
* Evidence of IAM-based authentication for proxy access
* AWS Config rules showing private IP spaces are not routable externally

---

**HITRUST Requirement – Application Sensitivity Identification and Documentation**

Control ID: 01.w Sensitive System Isolation  
Control Type: Administrative  
Control Level: Application/System Ownership  
HIPAA Mapping: 164.308(a)(1)(ii)(A) – Risk Analysis, 164.308(a)(7)(ii)(E) – Applications and Data Criticality Analysis

🎯 **Control Objective**

Ensure that the sensitivity of each application or system is properly assessed and documented by responsible system owners to guide the implementation of appropriate security measures and support compliance efforts.

🔧 **Technical Implementation**

1. **Application Sensitivity Identification**

   * Application/system owners (e.g., service or product managers) are required to:

     + Classify applications as High, Moderate, or Low sensitivity based on the data they process (e.g., PHI, PII, PCI).
     + Use the AWS Data Classification Tagging Framework to tag AWS resources such as EC2, RDS, Lambda, and S3 with sensitivity levels (e.g., `DataSensitivity: PHI`).
2. **Documentation and Ownership Accountability**

   * Document sensitivity levels in:

     + AWS Service Catalog portfolios or Systems Manager Application Manager.
     + A central configuration management database (CMDB) or AWS Config + AWS Systems Manager Inventory.
   * Ownership is enforced using IAM resource tags (e.g., `Owner: app-team@example.com`).
3. **Link to Risk and BCDR Processes**

   * AWS Backup and BCDR settings (e.g., recovery points, cross-region replication) are tailored based on application sensitivity.
   * Sensitive applications are prioritized for encryption, logging, access control and guardrail enforcement (e.g., via SCPs and Config conformance packs).

📋 **Possible Evidence to Collect**

* List of applications with associated `DataSensitivity` and `Owner` resource tags
* Documentation or screenshots of AWS Systems Manager Application Manager inventory
* Policies or SOPs defining sensitivity levels and classification guidelines
* Application sensitivity registry or inventory report
* Change management tickets showing classification reviews during deployment
* AWS Config resource compliance reports aligned to sensitivity levels
* Audit logs showing sensitivity-tagged resources are subject to stricter controls

---

**HITRUST Requirement – Isolation of Sensitive Application Systems**

Control ID: 01.w Sensitive System Isolation  
Control Type: Technical + Administrative  
Control Level: System + Application  
HIPAA Mapping: 164.308(a)(1)(ii)(A) – Risk Analysis, 164.312(c)(1) – Integrity, 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Ensure sensitive applications operate in secure environments that prevent unauthorized access, minimize shared exposure, and maintain data confidentiality and integrity. When sharing resources is required, risks must be assessed and formally accepted.

🔧 **Technical Implementation**

1. **Dedicated or Trusted Resource Allocation**

   * Sensitive applications are deployed on:

     + Dedicated EC2 instances or Dedicated Hosts, or
     + Dedicated VPCs with strict security group and NACL configurations.
   * If sharing infrastructure, workloads are limited to same trust boundary (e.g., all HIPAA workloads in a HIPAA-compliant VPC).
2. **Physical or Logical Isolation**

   * Logical isolation is achieved using:

     + Separate VPCs or Subnets for different sensitivity tiers.
     + IAM roles and policies to restrict cross-service access.
     + KMS keys with resource policies limiting decryption to authorized services only.
   * Physical isolation options include AWS Outposts for sensitive workloads or Dedicated Hosts.
3. **Risk Identification and Acceptance in Shared Environments**

   * Before co-hosting a sensitive application:

     + Security and DevOps teams identify all systems sharing resources (e.g., same ECS cluster, Kubernetes node group).
     + A risk assessment is performed and documented in a central GRC tool or audit system (e.g., Vanta, Archer, ServiceNow).
     + Application/system owner formally approves the risk and any compensating controls.

📋 **Possible Evidence to Collect**

* Architecture diagram showing isolated/dedicated deployment (e.g., separate VPC, subnet)
* EC2 instance metadata or launch configuration showing dedicated host usage
* AWS Config conformance reports showing logical separation
* Risk assessment documentation or ticket referencing shared environment approval
* Owner acknowledgment (signed digitally or via workflow) of risk acceptance
* KMS key policies restricting access by application workload
* CloudTrail logs showing no unauthorized cross-application access
* Terraform or CloudFormation templates enforcing separation policies

---

**HITRUST Requirement – Implement and Maintain IDS/IPS Across Critical Network Points**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: System + Network  
HIPAA Mapping: 164.308(a)(1)(ii)(A) – Risk Analysis, 164.308(a)(1)(ii)(B) – Risk Management, 164.312(b) – Audit Controls, 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Deploy and manage intrusion detection and prevention technologies at key network locations, including wireless entry points, to monitor and control traffic, detect anomalous activity, and prevent unauthorized access or data exfiltration.

🔧 **Technical Implementation**

1. **Perimeter and Internal IDS/IPS Deployment**

   * AWS Network Firewall and GuardDuty act as perimeter defense and intrusion detection tools.
   * GuardDuty continuously monitors for malicious behavior at the VPC level and CloudTrail logs, acting as a lightweight IDS.
   * AWS Gateway Load Balancer + Suricata-based IDS/IPS (e.g., from Palo Alto, Fortinet, or open-source AMIs) can be deployed at:

     + VPC ingress/egress points
     + Within sensitive subnets or internal tiers (east-west traffic)
2. **Wireless IDS (WIDS) Configuration**

   * In hybrid or on-prem wireless environments, WIDS tools (e.g., Aruba, Cisco, or Ubiquiti platforms) are deployed on the wireless side of firewalls.
   * In AWS-only environments, wireless access is typically restricted. However, VPN entry points (e.g., Client VPN) are monitored using VPC Flow Logs + CloudWatch alerts.
3. **Signature & Engine Updates**

   * For third-party IDS/IPS solutions in AWS or on-prem:

     + Ensure automatic updates of signature databases (e.g., Snort or Suricata rules) are enabled.
     + Confirm that detection baselines and engines are tuned periodically (monthly or based on threat intel updates).
   * Managed services like AWS GuardDuty auto-update their detection engines from AWS Threat Intel.

📋 **Possible Evidence to Collect**

* GuardDuty findings summary over last 90 days
* IDS/IPS configuration files or vendor documentation showing deployment points
* Screenshots or logs of WIDS running and integrated with firewalls
* Configuration management records showing:

  + Enabled auto-updates for signatures (Snort/Suricata)
  + Monthly or quarterly tuning review logs
* AWS Config or Inspector reports validating proper VPC protection setup
* Incident response tickets showing IDS/IPS alerts acted upon
* Internal network diagrams with IDS/IPS placement points clearly marked
* List of rule updates and patch history for intrusion tools

---

**HITRUST Requirement – Block Access to Known Malicious Internet Domains**

**Control ID:** 09.m Network Controls  
**Control Type:** Technical  
**Control Level:** System + Network  
**HIPAA Mapping:**

* 164.308(a)(1)(ii)(A) – Risk Analysis
* 164.308(a)(1)(ii)(B) – Risk Management
* 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Ensure that enterprise assets are prevented from accessing known malicious IP addresses, URLs, and domains using technical controls like DNS filtering, threat intelligence feeds, browser policies, or endpoint protection tools. Access may be permitted only if a documented business need is reviewed and approved through a formal risk process.

🔧 **Technical Implementation**

1. **DNS-Level Blocking**

   * **Amazon Route 53 Resolver DNS Firewall** is configured to block queries to known malicious domains using managed threat intelligence feeds.
   * Integrate with **AWS Firewall Manager** to apply policies across multiple accounts via AWS Organizations.
2. **Endpoint Protection + Browser Configurations**

   * **Amazon WorkSpaces** or EC2-based desktops have:

     + Group Policy Objects (GPOs) that restrict access to known malicious URLs/domains.
     + Endpoint Detection and Response (EDR) software (e.g., CrowdStrike, SentinelOne) with URL filtering and DNS sinkholing enabled.
3. **Proxy and Threat Intel Subscriptions**

   * Use **application layer filtering proxies** like **Zscaler**, **Cisco Umbrella**, or **Cloudflare Gateway** to block access based on known bad reputation.
   * Integrate **AWS Network Firewall** with Suricata rules and third-party blocklists (Talos, AlienVault OTX, etc.).
4. **Risk-Based Exceptions**

   * All exceptions to access control (e.g., whitelisting a blocked domain) are:

     + Documented via AWS Security Hub Findings Workflow or ticketing system (e.g., JIRA).
     + Approved only after risk acknowledgment by security leadership.

📋 **Possible Evidence to Collect**

* DNS Firewall policies applied via Route 53 Resolver and their effect logs
* List of domains currently blocked and frequency of denied access logs
* Screenshots or configuration of proxy-based URL filtering (e.g., Zscaler, Umbrella)
* Change control or exception request for whitelisting known domain
* Ticket or document showing risk assessment for allowing access to blocked content
* AWS Config or Firewall Manager policy records enforcing malicious domain restrictions
* Proof of integration with threat intel feed sources
* SIEM (e.g., Splunk, CloudWatch) alerts for attempted access to blocked sites

---

**HITRUST Requirement – Maintain and Update a Current Network Diagram**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: System + Infrastructure  
HIPAA Mapping: 164.308(a)(1)(ii)(A) – Risk Analysis, 164.308(a)(1)(ii)(B) – Risk Management, 164.312(c)(1) – Integrity

🎯 **Control Objective**

Ensure a complete and current network diagram exists and is regularly updated to accurately reflect the current state of network architecture. The diagram must include high-risk zones, data flows, covered information system connections, and legally significant wireless networks to support compliance and risk management.

🔧 **Technical Implementation**

1. Current Network Mapping

   * AWS Config + AWS Organizations used to auto-discover VPCs, subnets, peering connections, route tables, and Direct Connect gateways across accounts.
   * Diagrams generated or updated using CloudMapper, Lucidchart, or Diagrams-as-Code tools like Diagrams (Python) or PlantUML.
2. Inclusion of High-Risk Environments & Data Flows

   * High-risk environments (e.g., subnets containing databases with PHI/PII) are labeled via AWS Tags and AWS Resource Groups.
   * VPC Flow Logs and AWS Traffic Mirroring used to document data flows between network segments and external entities.
3. Covered System and Wireless Network Documentation

   * Network diagram includes all AWS-hosted systems that transmit or store sensitive data (e.g., via S3 buckets, RDS, EC2, or Redshift) and flags VPN, AWS Client VPN, or hybrid wireless connectivity that has compliance implications.
4. Change-Triggered and Periodic Updates

   * CI/CD pipeline triggers update the diagram when infrastructure changes (Terraform apply, CloudFormation deploy).
   * Manual review process ensures diagram is reviewed and validated at least every 6 months, as documented in the change management policy.

📋 **Possible Evidence to Collect**

* Network diagram (e.g., PNG, Lucidchart or architecture PDF) with labels for all required elements
* Git commit log or change tracking report showing date of last update
* Inventory of covered systems and compliance-relevant wireless networks
* VPC and subnet inventory via AWS Config or Trusted Advisor
* Meeting notes or review logs confirming biannual diagram validation
* Tags or labels in AWS showing risk classifications or system roles
* JIRA ticket or policy stating update frequency and change trigger rules

---

**HITRUST Requirement – Monitor and Control Wireless Access Points**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: System + Infrastructure  
HIPAA Mapping: 164.312(b) – Audit Controls, 164.312(c)(1) – Integrity, 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Ensure that all wireless access to the organization's systems is actively monitored and tightly controlled. Only wireless access points (WAPs) that are explicitly authorized are permitted, thereby reducing the risk of unauthorized access and rogue devices.

🔧 **Technical Implementation**

1. Monitoring Wireless Access

   * AWS environments: Native AWS services do not use traditional wireless access, but hybrid environments (e.g., AWS Outposts, WorkSpaces, or on-prem setups) may use WAPs.
   * Wi-Fi Controller Systems (e.g., Cisco Meraki, Aruba, Ubiquiti) are configured to log and alert on unauthorized SSIDs, MAC addresses, and signal anomalies.
   * WIDS/WIPS tools such as AirMagnet, Ekahau, or wireless modules within IDS/IPS platforms (e.g., Palo Alto, FortiGuard) are deployed to detect unauthorized wireless connections.
2. Access Point Authorization

   * Installation of wireless access points (WAPs) must be approved in writing by the CIO or delegate.
   * All authorized WAPs are included in a centralized inventory, tagged with location, approval date, firmware version, and responsible administrator.
   * Configuration management databases (CMDB) track authorized devices; any unregistered WAP triggers an incident alert.
3. Security Configuration

   * WPA3 (or WPA2 Enterprise with RADIUS) used for wireless encryption.
   * MAC filtering and 802.1X authentication enforced.
   * Management interfaces restricted to internal VLANs and accessed only via VPN.

📋 **Possible Evidence to Collect**

* List of authorized wireless access points with CIO/designate approval records
* WIDS/WIPS logs showing active monitoring and alerts for unauthorized wireless activity
* CMDB entries or asset inventories showing registered WAPs
* Policy document requiring written authorization for all new WAPs
* Change management tickets for WAP installation or modification
* Security baseline reports showing encryption standards (e.g., WPA3)
* Screenshot or export from Wi-Fi controller dashboard showing active APs and rogue detection settings
* IDS/IPS or SIEM reports showing no unauthorized wireless connections during audit window

---

**HITRUST Requirement – Define and Monitor VoIP Usage**

Control ID: 09.m Network Controls  
Control Type: Technical + Administrative  
Control Level: System + Infrastructure  
HIPAA Mapping: 164.308(a)(1)(ii)(D) – Information System Activity Review, 164.312(b) – Audit Controls, 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Ensure that the use of Voice over Internet Protocol (VoIP) services is appropriately restricted, authorized, implemented, and monitored. This minimizes exposure to data leakage, eavesdropping, and unapproved use of communication channels.

🔧 **Technical Implementation**

1. Usage Restrictions and Implementation Guidance

   * VoIP usage policies are defined and documented in the organization’s Acceptable Use Policy and Telecom Security Guidelines.
   * Guidelines specify permitted VoIP platforms (e.g., Zoom Phone, RingCentral, Cisco Webex Calling) and prohibit unauthorized third-party softphones or free public services (e.g., Skype, WhatsApp calling for work).
   * AWS-based solutions that integrate with VoIP (e.g., Amazon Chime Voice Connector) follow secure configuration standards including encryption, IAM role control, and logging.
2. VoIP Authorization Process

   * Requests for VoIP accounts, extensions, or services go through an IT service request process.
   * Only approved users/devices are provisioned with VoIP credentials.
   * VoIP services are segmented into VLANs and firewalled from sensitive data environments.
3. Monitoring of VoIP Services

   * VoIP call detail records (CDRs), access logs, and account creation/modification activities are forwarded to SIEM tools (e.g., Splunk, ELK, AWS CloudWatch Logs).
   * Intrusion Detection Systems (IDS) are configured to detect anomalous SIP or RTP traffic patterns.
   * Periodic audit of VoIP accounts and license usage is performed to identify dormant or unauthorized services.

📋 **Possible Evidence to Collect**

* Documented VoIP usage policy and implementation guidelines
* Sample VoIP access request and approval ticket from service desk platform
* List of authorized VoIP users and their assigned extensions
* VLAN configuration or network segmentation diagrams showing VoIP separation
* VoIP system configuration showing encryption settings (e.g., TLS, SRTP)
* Monitoring dashboard screenshots from SIEM showing VoIP call events
* Audit logs of VoIP usage and provisioning/de-provisioning
* Change control records for VoIP configuration updates or onboarding

---

**HITRUST Requirement – Network Protection, Availability, and Operational Separation**

**Control ID:** 09.m Network Controls  
**Control Type:** Technical + Administrative  
**Control Level:** Network Infrastructure + Operations  
**HIPAA Mapping:** 164.308(a)(1)(ii)(A) – Risk Analysis, 164.308(a)(1)(ii)(B) – Risk Management, 164.312(e)(1) – Transmission Security, 164.308(a)(3)(ii)(A) – Workforce Clearance Procedure

🎯 **Control Objective**

Establish and enforce controls that ensure the security and availability of networks and connected services, maintain separation of responsibilities, and implement safeguards for data flowing over public or wireless networks.

🔧 **Technical Implementation**

1. **Network Security and Availability Controls**

   * AWS security groups, Network ACLs, and route tables are configured to restrict unauthorized access.
   * Availability Zones and multi-region failover configurations are used to ensure redundancy of VPC resources, VPN endpoints, and Direct Connect circuits.
   * AWS Transit Gateway enforces controlled routing across environments.
2. **Management of Networking Equipment**

   * On-premises switches, firewalls, and routers are governed by documented SOPs.
   * AWS-native networking (e.g., VPCs, Transit Gateways, Direct Connect) is maintained through Infrastructure-as-Code with change control via Terraform/CloudFormation and Git.
3. **Separation of Duties**

   * Networking teams operate independently of infrastructure teams responsible for server provisioning and OS maintenance.
   * IAM roles are scoped to allow least-privileged access to either network or system management, not both.
4. **Special Controls for Wireless and Public Network Traffic**

   * VPN tunnels, TLS encryption, and network segmentation are enforced for data traversing public or wireless networks.
   * AWS Client VPN and Site-to-Site VPN solutions enforce secure transmission paths.
   * Wireless environments (if any) are isolated from production workloads and protected with WPA2-Enterprise or equivalent.

📋 **Possible Evidence to Collect**

* Documented network architecture and segmentation diagrams
* SOPs and responsibility matrices for network hardware and AWS network components
* IAM policies showing separation of access between network and compute resources
* Terraform/CloudFormation templates managing networking components
* Proof of encryption in transit (e.g., TLS configurations, VPN tunnel status)
* CloudTrail logs showing network control changes
* Incident response logs demonstrating detection and blocking of unauthorized access
* Audit logs from wireless network controllers or public access proxies

---

**HITRUST Requirement – Network Equipment Management and Responsibilities**

**Control ID:** 09.m Network Controls  
**Control Type:** Administrative  
**Control Level:** Organizational & Endpoint Device Layer  
**HIPAA Mapping:** 164.310(d)(1) – Device and Media Controls, 164.310(c) – Workstation Security, 164.308(a)(1)(ii)(D) – Information System Activity Review

🎯 **Control Objective**

Establish and assign clear responsibilities and documented procedures for managing all equipment on the network—both centralized and distributed—ensuring devices in user-accessible areas are securely managed to prevent unauthorized access or misuse.

🔧 **Technical Implementation**

1. **On-Premise Equipment Responsibilities and Procedures**

   * Defined in SOPs and asset lifecycle documents for switches, routers, access points, laptops, and desktops.
   * User devices are hardened, tracked in asset inventory systems, and tied to access provisioning policies (e.g., via JAMF, Intune, or SCCM).
   * Physical controls (e.g., cable locks, restricted ports, workstation lock screens) are enforced in user areas.
2. **Cloud-Connected Equipment (e.g., via AWS Workspaces, EC2 with End Users)**

   * Asset ownership, tagging, and IAM binding are enforced for cloud instances accessed by end users.
   * Network devices connecting to AWS resources (VPN endpoints, Direct Connect routers) are documented and assigned to responsible teams.
3. **User Area Controls**

   * Devices used in shared areas (e.g., nurses’ stations, kiosks) are locked down via endpoint configuration, user access restrictions, and screen timeout policies.
   * Workstations are restricted from direct access to critical network segments without passing through firewalls or access gateways.

📋 **Possible Evidence to Collect**

* Network equipment management SOPs
* Asset inventory with ownership/responsibility fields
* Screenshots or exports from MDM tools showing enforcement of endpoint controls
* Documentation of workstation security configurations
* Access control records for devices in shared/user areas
* Audit logs or camera footage of device access in secure areas (if applicable)
* Responsibility assignment matrix (e.g., RACI) for networking equipment and endpoints

---

**HITRUST Requirement – Secure Migration to Virtualized Environments**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: System-Level & Infrastructure Layer  
HIPAA Mapping: 164.312(e)(1) – Transmission Security, 164.308(a)(1)(ii)(A) – Risk Analysis, 164.312(a)(2)(iv) – Encryption and Decryption

🎯 **Control Objective**

Ensure confidentiality and integrity of sensitive systems and data during migration to virtualized environments by enforcing encrypted and secured communication channels.

🔧 **Technical Implementation**

1. Encryption in Transit

   * Enforce TLS 1.2+ or IPsec VPN tunnels during migration operations from physical servers to AWS EC2 or VMware vSphere.
   * Use AWS Direct Connect with MACSec or Transit Gateway with AWS VPN for secure data pathing during cross-environment migrations.
2. Data/Application Server Migration

   * Tools such as AWS Server Migration Service (SMS), AWS Application Migration Service (MGN), or third-party solutions like Veeam or Carbonite must be configured with encryption enabled and transport authenticated.
   * SSH, SFTP, HTTPS are used to move application files and configurations securely.
3. Segregated Migration Networks

   * Dedicated staging VLANs or VPCs used for migration are encrypted and monitored separately from production.
   * NACLs or security groups prevent public network exposure during transit.
4. Authentication and Logging

   * Access to migration tools and services is controlled through IAM roles and MFA.
   * All migration activities are logged and monitored via AWS CloudTrail or SIEM (e.g., Splunk, Sumo Logic).

📋 **Possible Evidence to Collect**

* Network architecture diagram showing encrypted migration paths
* Encryption configuration of migration tools (e.g., TLS settings, VPN config)
* Logs from AWS CloudTrail or system logs showing successful secure migration sessions
* Screenshots or CLI outputs confirming use of secured channels (e.g., `openssl`, `ipsec status`, `aws sms get-replication-jobs`)
* Documentation of the server/data/application migration procedure with encryption noted
* Evidence of IAM roles and MFA enforcement for migration-related accounts

---

**HITRUST Requirement – Interconnection Authorization and Controls**

Control ID: 09.m Network Controls  
Control Type: Technical & Administrative  
Control Level: System-Level & Interconnection/Boundary Protection  
HIPAA Mapping: 164.308(a)(1)(ii)(A) – Risk Analysis, 164.308(a)(4) – Information Access Management, 164.312(b) – Audit Controls

🎯 **Control Objective**

Ensure that interconnections between internal systems and external entities are properly authorized, securely configured, and documented to prevent unauthorized data access or transmission.

🔧 **Technical Implementation**

1. Authorization via Agreements

   * All data exchanges or API integrations with third-party systems (e.g., B2B, SaaS, government agencies) are authorized via a signed Interconnection Security Agreement (ISA), Memorandum of Understanding (MoU), or Data Use Agreement (DUA).
   * Examples: AWS PrivateLink to external partners; cross-account VPC peering with formal IAM trust relationships and documented security postures.
2. Documenting Connection Attributes

   * For each external connection, the following are documented in a central system like Confluence or SharePoint:

     + Network interface characteristics (e.g., IP ranges, subnets, endpoints)
     + Security requirements (e.g., TLS 1.2, IP whitelisting, firewall rules, API keys)
     + Data flows and classifications (e.g., PHI, PII, system telemetry)
3. Connection Control Policy

   * Default outbound traffic is denied by AWS security groups or firewall appliances (e.g., Palo Alto, Fortinet).
   * Exceptions for outbound connectivity to external systems must be formally reviewed and approved through a change control process and justified via documented business need.
4. Monitoring and Logging

   * All interconnection traffic is logged (e.g., AWS VPC Flow Logs, GuardDuty, CloudTrail).
   * Alerts configured for unauthorized attempts to establish external connections.

📋 **Possible Evidence to Collect**

* Signed interconnection security agreements or data use agreements
* List of authorized external systems with documented interface specs and data classifications
* Network diagrams showing allowed interconnections
* Change control or ticketing system logs showing business justification and approval for external links
* Screenshots or config exports showing “deny-all, allow-by-exception” firewall/NACL settings
* VPC Flow Logs, AWS Config rules, or CloudTrail evidence for external API traffic

---

**HITRUST Requirement – Controlled and Approved Network Device Configuration Changes**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: Network & Infrastructure  
HIPAA Mapping: 164.308(a)(1)(ii)(A) – Risk Analysis, 164.312(c)(1) – Integrity, 164.312(e)(2)(i) – Integrity Controls

🎯 **Control Objective**

Ensure that all configuration changes to network security infrastructure (firewalls, routers, and switches) are authorized, documented, and reviewed to minimize the risk of misconfiguration and unauthorized traffic flow.

🔧 **Technical Implementation**

1. Network Change Approval Workflow

   * All changes to security group rules, network ACLs, route tables, AWS Network Firewall, and third-party firewalls (e.g., Palo Alto in Transit Gateway) are submitted through an ITSM (e.g., Jira, ServiceNow) and require formal approval.
2. Testing Prior to Deployment

   * Firewall or routing changes are tested in non-production staging environments or via AWS Firewall Manager policies using scoped test accounts.
   * Terraform changes to VPC/network rules use plan+apply stages with approval gates in CI/CD (e.g., GitHub Actions, CircleCI).
3. Change Control and Documentation

   * All deviations from baseline AMI or Terraform configurations are recorded and linked to:

     + A business justification
     + Change owner (e.g., network engineer or security lead)
     + Expected timeframe for the change (e.g., permanent, 30-day rule exception)
4. Traffic Flow Authorization Logging

   * AWS Config Rules track when non-default allow rules are introduced on critical ports or destination IPs.
   * Lambda functions trigger notifications when firewall rules are altered without ticket references.

📋 **Possible Evidence to Collect**

* Change control records from ServiceNow or Jira showing approval workflow
* Terraform plan logs showing firewall/network rule changes
* Git logs with author identity tied to network rule modifications
* AWS Config snapshots showing baseline deviation
* Screenshots or export of firewall rules with tagging for temporary/exception cases
* Documentation of approval, responsible person, business need, and duration for each config change

---

**HITRUST Requirement – Restrict Inbound and Outbound Traffic**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: Network & Infrastructure  
HIPAA Mapping: 164.308(a)(1)(ii)(B) – Risk Management, 164.312(a)(1) – Access Control, 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Ensure firewall configurations are limited to only the minimum inbound and outbound network traffic necessary to support business functions in the covered information systems environment.

🔧 **Technical Implementation**

1. Inbound and Outbound Rule Enforcement

   * AWS security groups are scoped to allow only required inbound ports (e.g., HTTPS/443) from trusted IPs or load balancers.
   * Outbound traffic is tightly controlled using Network ACLs, security groups, and optionally AWS Network Firewall or third-party firewalls.
2. Policy-as-Code Controls

   * Firewall rule changes are implemented via Infrastructure as Code (IaC) (e.g., Terraform or CloudFormation) with CI/CD controls for pre-deployment validation.
   * Rule sets are evaluated against baseline templates ensuring only essential traffic is permitted.
3. Auditing and Drift Detection

   * AWS Config monitors for unexpected changes in security group or NACL rules, generating alerts for unauthorized exposure.
   * AWS Firewall Manager or Conformance Packs enforce central control over distributed firewall policies.
4. Logging and Monitoring

   * VPC Flow Logs, CloudTrail, and GuardDuty help monitor rule effectiveness and detect anomalies in allowed traffic patterns.
   * Alerts are triggered when rules deviate from expected parameters (e.g., allowing 0.0.0.0/0 to sensitive ports).

📋 **Possible Evidence to Collect**

* Terraform configuration showing allowed inbound/outbound ports with descriptions
* AWS Config Rule compliance reports validating traffic restrictions
* Security Group policy reports with attached justifications for each rule
* Firewall Manager audit log showing enforcement of centralized policy
* VPC Flow Logs or GuardDuty events illustrating traffic filtering in practice
* Screenshot or export of security group settings with traffic scope documentation

---

**HITRUST Requirement – Device Identification and Authentication on Networks**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: Network & Endpoint Security  
HIPAA Mapping: 164.312(d) – Person or Entity Authentication, 164.308(a)(5)(ii)(D) – Password Management, 164.312(a)(1) – Access Control

🎯 **Control Objective**

Ensure that all devices connecting to the organization's networks—including wired, wireless, and remote endpoints—are uniquely identified and authenticated prior to gaining network access, based on the sensitivity of the connected system.

🔧 **Technical Implementation**

1. Device Authentication Mechanisms

   * In on-prem or hybrid environments, IEEE 802.1x with EAP-TLS is enforced for device-level authentication at the network layer.
   * RADIUS servers integrated with corporate identity providers (e.g., Active Directory, Okta) validate device trust.
   * MAC and IP address-based filtering is deployed only for low-sensitivity or legacy environments and is monitored for spoofing.
2. Security Categorization Alignment

   * Critical systems are configured to require stronger authentication (e.g., mutual TLS certificates or device posture checks via MDM).
   * Cloud-native environments use AWS Certificate Manager, IAM roles, and Session Manager with trusted device context via Systems Manager.
3. Wireless Network Enforcement

   * Wireless networks (e.g., for employees or contractors) use certificate-based authentication and device compliance validation through MDM platforms (e.g., Jamf, Intune).
   * Guest networks are isolated via VLAN segmentation with bandwidth limits and access restrictions.
4. Monitoring and Alerting

   * CloudTrail, AWS Config, and on-prem NAC (e.g., Cisco ISE) continuously monitor device identities and unauthorized access attempts.
   * Alerts are triggered if an unknown device attempts connection or if the authentication mechanism deviates from the policy.

📋 **Possible Evidence to Collect**

* Network Access Control (NAC) policies with authentication method details (e.g., 802.1x + RADIUS)
* Screenshots or exports of MDM enforcement policies showing certificate or identity checks
* IAM and Systems Manager configurations enforcing trusted device sessions in AWS
* Logs showing successful/failed authentication attempts by device
* Risk assessment documents showing justification for authentication strength by system classification
* AWS Config rules validating instance access only from known device pools

---

**HITRUST Requirement – Protection of Transmitted Information**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: Network & Data Protection  
HIPAA Mapping:, 164.312(e)(1) – Transmission Security, 164.312(e)(2)(i) – Integrity Controls, 164.312(e)(2)(ii) – Encryption

🎯 **Control Objective**

Ensure that transmitted information—whether in preparation, transit, or upon reception—is protected to maintain confidentiality and integrity against unauthorized disclosure, tampering, or interception.

🔧 **Technical Implementation**

1. Confidentiality Controls

   * All sensitive transmissions use TLS 1.2 or higher (e.g., HTTPS, SMTPS, FTPS).
   * AWS services (e.g., S3, API Gateway, CloudFront) enforce HTTPS-only access.
   * Endpoints interacting with AWS are configured to use certificate pinning or trust store validation to ensure secure peer identity.
2. Integrity Controls

   * Message Authentication Codes (MACs) or digital signatures are used to detect tampering in structured data transmissions (e.g., HL7, JSON Web Tokens).
   * For file transfer protocols like SFTP, hash verification (SHA-256 or better) is automated post-transfer.
3. Pre-Transmission Security

   * Applications and middleware encrypt or redact sensitive fields before initiating transmission.
   * AWS KMS encrypts payloads before being pushed to services like SQS, SNS, or EventBridge.
4. Reception Security

   * Information systems verify signature, integrity hash, and destination IP/domain against approved sources.
   * Serverless and container workloads include integrity checks in API Gateway headers, and log all inbound transmission events via CloudWatch or third-party SIEM.

📋 **Possible Evidence to Collect**

* Encryption configuration for TLS 1.2+ on AWS services (e.g., ELB, API Gateway, S3)
* Screenshots or scripts showing digital signature verification or hashing implementation
* System design documents showing secure data flow, including encryption in preparation and at reception
* AWS KMS or Secrets Manager encryption configuration
* Logging outputs showing inbound data integrity checks
* Network diagrams showing trusted boundary for encrypted and integrity-protected communications

---

**HITRUST Requirement – Device Scanning and Unauthorized Component Detection**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: System Security Monitoring  
HIPAA Mapping: 164.308(a)(1)(ii)(A) , 164.308(a)(1)(ii)(B) , 164.308(a)(5)(ii)(C) , 164.312(b)

🎯 **Control Objective**

Ensure the organization proactively detects unauthorized or unmanaged devices by implementing automated scanning tools and conducting regular audits of the asset landscape.

🔧 **Technical Implementation**

1. Implementation of Scanning Tools

   * AWS-native tools such as AWS Systems Manager Inventory, Amazon Inspector, and GuardDuty are configured to continuously monitor for unauthorized EC2 instances, containers, and connected services.
   * In hybrid environments, tools such as Tenable Nessus, OpenVAS, or Qualys are deployed on-premises and extended to scan VPCs and subnets via AWS Systems Manager or VPN-connected scanning agents.
2. Quarterly Unauthorized Device Scans

   * Scheduled quarterly scans are performed across all environments to detect:

     + Shadow IT devices or rogue hardware
     + Virtual machines or containers not registered in CMDB
     + Network components with unauthorized MAC/IP addresses
   * Asset inventory from AWS Config, CloudTrail, and Systems Manager is reconciled with internal asset registers to detect gaps or anomalies.
3. Alerting and Response

   * Alerts for unknown devices are routed to a SIEM or SOAR platform (e.g., Splunk, Datadog, or AWS Security Hub) for triage and remediation.
   * Events triggering AWS Config non-compliance rules for unauthorized resource types result in Lambda-triggered tagging, quarantine, or shutdown actions.

📋 **Possible Evidence to Collect**

* Configuration screenshots of scanning tools (e.g., Amazon Inspector, Nessus)
* Logs or reports showing quarterly scan execution and findings
* Reconciled asset inventory and anomaly reports
* Security Hub or SIEM alerts related to unauthorized device detection
* AWS Config compliance rule definitions and remediation logs
* Screenshots showing Systems Manager Inventory or CMDB updates
* Policies or SOPs outlining the scan cadence and review responsibilities

---

**HITRUST Requirement – Firewall Configuration and Documentation Maintenance**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: Network Security  
HIPAA Mapping: 164.308(a)(1)(ii)(A) , 164.308(a)(1)(ii)(B) , 164.312(e)(1)

🎯 **Control Objective**

Establish firewall configurations to restrict traffic from untrusted networks and ensure network diagrams reflect changes to firewall configurations to support accurate documentation and secure architecture.

🔧 **Technical Implementation**

1. Firewall Configuration Enforcement

   * All internet-facing workloads in AWS are protected using AWS Network Firewall, Security Groups, and NACLs to enforce least-privilege traffic rules.
   * In hybrid or on-prem environments, stateful firewalls such as Palo Alto or Fortinet are configured to prevent untrusted external access to sensitive system components.
2. Architecture and Network Diagrams

   * The architecture team maintains up-to-date network diagrams in version-controlled documentation repositories (e.g., Confluence, Lucidchart integrated with Git, or AWS Perspective).
   * Firewall rule changes or security group modifications are logged via AWS Config and recorded in the network diagram update workflow.
3. Change Management

   * All firewall rule changes go through a documented change control process. The network team coordinates updates in diagrams to reflect the change, including rationale and timestamps.

📋 **Possible Evidence to Collect**

* Exported Security Group or AWS Network Firewall rule definitions
* Change tickets showing approval of firewall rule changes
* Screenshots of updated network diagrams highlighting firewall zones
* AWS Config rule history showing modifications to firewall components
* Documentation or SOP outlining change control process and diagram maintenance
* Evidence of review or versioning in network documentation platforms

---

**HITRUST Requirement – Network Service Loss Impact Definition**

Control ID: 09.m Network Controls  
Control Type: Organizational / Risk Management  
Control Level: Foundational  
HIPAA Mapping: 164.308(a)(1)(ii)(A), 164.308(a)(7)(ii)(A) , 164.308(a)(7)(ii)(B)

🎯 **Control Objective**

Ensure the organization defines and documents the potential impact of network service disruptions to support appropriate business continuity and recovery strategies.

🔧 **Technical Implementation**

1. Business Impact Assessment (BIA)

   * The organization conducts a Business Impact Analysis to determine the criticality of network-dependent systems. The BIA identifies the Recovery Time Objective (RTO) and Recovery Point Objective (RPO) for all systems reliant on network availability.
2. Service Dependency Mapping

   * Tools such as AWS Application Discovery Service, Service Catalogs, or internal CMDBs (e.g., ServiceNow) are used to track application and system dependencies on networking infrastructure.
3. Availability Classifications

   * Network services are classified by their business impact rating (e.g., critical, high, moderate, low), which informs incident response priorities, DR strategies, and failover configurations (e.g., AWS Route 53 failover, Transit Gateway routing).
4. Integration with Risk Register and DR Plans

   * Defined impacts are captured in the risk register, linked to resilience controls (e.g., AWS multi-AZ failover, ExpressRoute/Direct Connect redundancy), and referenced in DR playbooks.

📋 **Possible Evidence to Collect**

* Completed Business Impact Analysis (BIA) documentation with network service entries
* Network dependency matrix or mapping diagram
* Risk register entries outlining impact of network outages
* DR/BCP documentation with defined RTOs/RPOs for network loss
* Meeting notes or approvals of risk acceptance or prioritization decisions

---

**HITRUST Requirement – DMZ and Public Access Restrictions**

Control ID: 09.m Network Controls  
Control Type: Technical / Network Security  
Control Level: Moderate  
HIPAA Mapping: 164.308(a)(1)(ii)(A) , 164.312(e)(1), 164.312(c)(1) , 164.312(a)(1)

🎯 **Control Objective**

Prevent unauthorized or unmonitored access to internal system components by ensuring that all public-facing network interactions are segmented and filtered using appropriate security zones such as DMZs.

🔧 **Technical Implementation**

1. DMZ Architecture in AWS and Hybrid Environments

   * Use VPC public subnets (e.g., for web servers) and private subnets (for app and DB layers).
   * Public-facing endpoints (e.g., Elastic Load Balancers or API Gateways) terminate traffic at the edge; internal systems are not directly addressable from the internet.
2. Restrict Direct Traffic Routing

   * Use AWS Security Groups, NACLs, and route tables to enforce segmentation between public and private zones.
   * Disable default routes from private subnets to the internet unless required (e.g., use NAT Gateway for limited egress).
3. Address Filtering and NAT

   * Enforce private IP address ranges within the covered environment.
   * Use NAT Gateways or NAT Instances to ensure only egress with IP-masked outbound traffic.
4. Proxy and Filtering

   * Route outbound traffic through Squid proxy, Zscaler, or AWS Network Firewall.
   * Disable unnecessary protocols and ports and filter routes via dynamic routing policies.
5. Logical Segregation of Systems

   * Application servers and databases are deployed in private subnets or isolated VPCs, only accessible via bastion or VPN tunnels.
   * Use AWS Security Hub, Inspector, or GuardDuty to detect misconfigurations or violations of zone boundaries.
6. Infrastructure as Code Controls

   * Terraform, CloudFormation, or AWS Config rules define and continuously monitor DMZ and subnet structure to ensure compliance with design.

📋 **Possible Evidence to Collect**

* VPC/subnet architecture diagram showing DMZ and internal networks
* Terraform or CloudFormation templates with subnet segmentation and NAT/proxy routing
* AWS Config compliance results enforcing network flow rules
* Security Group and NACL configurations showing public/private boundaries
* Penetration test or vulnerability scan reports confirming no public access to sensitive components
* Logging evidence from proxy/firewall showing enforced access patterns
* Internal policy or network architecture documents explaining placement of databases, app servers, and web servers

---

**HITRUST Requirement – Redundant DNS Server Configuration**

Control ID: 09.m Network Controls  
Control Type: Technical / Network Services  
Control Level: Moderate  
HIPAA Mapping:164.308(a)(1)(ii)(A), 164.308(a)(1)(ii)(B) , 164.308(a)(7)(ii)(A), 164.308(a)(7)(ii)(B)

🎯 **Control Objective**

Ensure availability and resiliency of Domain Name System (DNS) services by implementing multiple, diversified DNS servers to avoid single points of failure and support business continuity.

🔧 **Technical Implementation**

1. Multiple DNS Servers in Different Subnets

   * Configure DNS infrastructure such that at least two DNS resolvers or authoritative servers are placed in distinct network subnets (e.g., separate Availability Zones in AWS or different VLANs on-prem).
2. Geographic Separation

   * In AWS, deploy DNS servers or route resolver endpoints in multiple regions or AZs.
   * On-premises or hybrid: use split-horizon DNS with geographically separated servers, e.g., East/West Coast data centers.
3. Separation of Roles – Internal vs. External

   * Internal DNS servers handle internal name resolution, directory integration (e.g., with Active Directory), and access to internal-only services.
   * External DNS servers (e.g., Route 53, Cloudflare, NS1) respond to public queries with firewalled access and restricted records.
4. Resilience and Failover Configuration

   * Use Route 53 Health Checks and failover routing policies to automatically switch to healthy endpoints.
   * Enable DNSSEC and TTL tuning to ensure continuity during failover events.
5. Monitoring and Logging

   * Enable Amazon Route 53 Query Logging, VPC DNS logs, or bind/named logs for on-prem solutions.
   * Integrate DNS log sources with SIEM for anomaly detection (e.g., DGA domains, DNS tunneling).

📋 **Possible Evidence to Collect**

* Network architecture diagram showing multiple DNS servers across subnets and geographies
* Route 53 configuration (hosted zones, health checks, resolver endpoints)
* Configuration files or screenshots of BIND/unbound/Windows DNS roles
* Evidence of internal vs. external DNS role definitions
* DNS logs showing load distribution or failover behavior
* Business continuity/disaster recovery documentation referencing DNS architecture
* Internal DNS change control logs and audit trails

---

**HITRUST Requirement – Logical Management of Network Components**

Control ID: 09.m Network Controls  
Control Type: Organizational / Governance  
Control Level: Moderate  
HIPAA Mapping**:** 164.308(a)(1)(ii)(D) – Information System Activity Review, 164.308(a)(6)(ii) – Security Incident Procedures, 164.308(a)(7)(ii)(A) – Contingency Planning

🎯 **Control Objective**

Ensure consistent and coordinated management of network infrastructure elements by clearly defining and documenting the roles, groups, and responsibilities involved in the logical oversight of network components.

**Technical & Organizational Implementation**

1. Coordination of Network Elements

   * Network architecture and configuration changes are coordinated centrally to ensure consistency across VPCs, subnets, NACLs, and route tables in AWS or across VLANs and firewalls on-premises.
2. Defined Groups, Roles, and Responsibilities

   * Documented network operations team structure (e.g., network engineers, cloud security architects).
   * Each role (e.g., firewall administrator, router configuration owner, IAM network policy lead) is assigned distinct responsibilities.
3. Access Governance

   * Logical responsibilities are mapped to least privilege access in systems like AWS IAM, Okta, Active Directory, or Cisco ISE.
   * Use of role-based access control (RBAC) to limit network modification rights.
4. Change Management Integration

   * All changes to routing, DNS, or firewall rules are routed through a formal change control process tied to ownership roles.
   * Incident response and monitoring functions are aligned with assigned roles for detection and escalation.
5. Network Management Policy

   * Network operations manual or SOPs describe:

     + Groups managing each network zone
     + Approval process for routing/firewall changes
     + Responsibility for documentation and updates

📋 **Possible Evidence to Collect**

* Network operations org chart with assigned groups and roles
* Document describing responsibilities for logical network components (e.g., cloud, on-prem, hybrid)
* Sample network change request with approval traceability to named responsible individual
* RBAC policies or IAM roles for network changes
* Network management SOP or playbooks
* Minutes of coordination meetings involving network and security teams

---

**HITRUST Requirement – Wireless Access Point Security**

Control ID: 09.m Network Controls  
Control Type: Technical & Physical  
Control Level: Moderate  
HIPAA Mapping:164.310(b) – Workstation Use, 164.312(e)(1) – Transmission Security, 164.308(a)(5)(ii)(D) – Log-in Monitoring

🎯 **Control Objective**

Ensure wireless access points (WAPs) are physically secured and only available during authorized timeframes to reduce the attack surface and prevent unauthorized access.

**Technical & Physical Implementation**

1. Physical Security of WAPs

   * Wireless access points are deployed in physically secure locations such as locked telecom closets, ceilings in badge-protected office spaces, or areas monitored by CCTV.
   * WAPs are installed with tamper-resistant enclosures where feasible.
2. Controlled Availability of Wireless Services

   * Wireless networks are automatically disabled during non-business hours (e.g., evenings, weekends) using access point scheduling tools in controllers (e.g., Cisco WLC, Aruba Central, Ubiquiti UniFi).
   * Scheduled shutdowns are configured via enterprise network management platforms or via cron jobs/scripts in smaller environments.
3. Monitoring and Alerting

   * Wireless access logs are monitored via SIEM (e.g., Splunk, Wazuh) to detect activity during off-hours.
   * Unauthorized activation or physical relocation of access points triggers alerts.
4. Policy Enforcement

   * Network security policies explicitly define physical placement and operational hours for wireless networks.
   * Policy reviewed annually or after office layout changes.

📋 **Possible Evidence to Collect**

* Floor plans showing secure WAP placement
* Photos or inventory showing WAPs mounted in locked or monitored areas
* Controller or dashboard screenshots showing scheduled WAP shutdown rules
* Change request logs for WAP relocation or reconfiguration
* Security policy or SOP stating wireless network operating hours and access restrictions
* Audit log samples showing wireless activity limited to business hours

---

**HITRUST Requirement – Router Configuration File Integrity**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: Moderate  
HIPAA Mapping: 164.308(a)(1)(ii)(B) – Risk Management, 164.308(a)(7)(ii)(C) – Emergency Mode Operation Plan, 164.312(c)(1) – Integrity

🎯 **Control Objective**

Ensure that router configuration files are both secured against unauthorized access and synchronized across redundant or backup systems to maintain operational continuity and configuration integrity.

🛠️ **Technical Implementation**

1. Securing Router Configuration Files

   * Router configuration files are stored on hardened, access-controlled systems (e.g., TFTP/SCP/FTP over TLS servers) with access limited to authorized network administrators only.
   * Files are encrypted in transit (e.g., via SCP or HTTPS) and optionally at rest.
   * Change logs are maintained, and access attempts are logged for auditing.
2. Synchronizing Configuration Files

   * Router configurations are regularly backed up and synchronized across redundant systems to ensure failover and restore capability.
   * Automated scripts (e.g., Ansible, RANCID, Oxidized) or backup jobs copy the configurations daily or after every approved change.
   * Configurations are version-controlled to allow rollback in the event of a misconfiguration or failure.
3. Configuration Integrity Monitoring

   * Tools such as Tripwire, AIDE, or built-in router configuration validation features are used to detect unauthorized changes.
   * Alerts are generated upon detection of deviations from baseline configurations.

📋 **Possible Evidence to Collect**

* System logs showing restricted access to config file directories
* Evidence of encrypted transfer (e.g., SCP job output or policy config)
* Backup logs or version control diffs showing sync and change history
* Screenshots from Oxidized or RANCID showing last pull and sync times
* Policy or SOP detailing router configuration management and access control
* Incident response records showing restoration of configuration from backup

---

**HITRUST Requirement – Proxy Access Control**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: Moderate  
HIPAA Mapping:164.312(a)(1) – Access Control, 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Ensure that access to proxy servers is restricted only to explicitly authorized hosts, ports, and services to minimize exposure and reduce the attack surface.

🛠️ **Technical Implementation**

1. Default Deny Policy on Proxy Access

   * All inbound and outbound proxy access is denied by default, unless explicitly permitted via defined access control lists (ACLs) or firewall rules.
   * Only authorized IP addresses, ports, and protocols (e.g., HTTPS for outbound browsing, specific vendor update servers) are whitelisted.
2. Configuration of Proxy ACLs

   * ACLs are enforced on the proxy layer (e.g., Squid, Zscaler, Palo Alto) to limit proxy usage.
   * Access is typically limited to specific subnets or user roles with a least privilege model.
   * Outbound rules include explicit allow lists for essential services (e.g., software updates, critical APIs).
3. Monitoring and Logging

   * Proxy logs are reviewed via SIEM (e.g., Splunk, Sentinel) for any attempts to access disallowed hosts.
   * Alerts are generated for unexpected or anomalous access patterns.
4. Periodic Review of Rules

   * Firewall and proxy rules are reviewed quarterly or after any significant network change.
   * Changes to the ACLs require documented approval tied to a business justification.

📋 **Possible Evidence to Collect**

* Proxy configuration files or screenshots showing deny-by-default policies
* Firewall rules tied to proxy interfaces
* SIEM logs showing blocked and allowed connections
* Documentation of proxy access requests and approvals
* Network architecture diagram showing proxy segmentation
* Policy/SOP covering proxy access management and review cycle

---

**HITRUST Requirement – Segregation of DNS Roles**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: Moderate  
HIPAA Mapping:164.312(a)(1) – Access Control, 164.308(a)(1)(ii)(B) – Risk Management

🎯 **Control Objective**

Ensure DNS servers are configured to prevent unauthorized access to internal network information and reduce exposure to external threats.

🛠️ **Technical Implementation**

1. Separation of Internal and External DNS Functions

   * Internal DNS servers provide name/address resolution for both internal and approved external IT resources.
   * External DNS servers are limited to responding only with name/address information for public-facing resources (e.g., websites, mail gateways).
2. Zoning and Role Assignment

   * Role-based DNS zoning is applied:

     + *Internal zones* (e.g., corp.local, \*.internal.example.com) are only resolvable internally.
     + *External zones* are maintained separately with limited information.
3. Network Isolation

   * Internal DNS servers are hosted behind the internal firewall and are not accessible from the Internet.
   * External DNS servers are placed in the DMZ and do not store or replicate internal DNS records.
4. Security Hardening

   * DNS servers run minimal services, have logging enabled, and are patched regularly.
   * Split-horizon DNS configuration is enforced to prevent data leakage.
5. Monitoring and Logging

   * All DNS queries are logged and monitored.
   * Alerts are configured for abnormal DNS activity (e.g., exfiltration via DNS tunneling).

📋 **Possible Evidence to Collect**

* Network diagram showing DNS server roles and zones
* DNS server configuration files (e.g., BIND `named.conf`, Windows DNS settings)
* Access control rules/firewall rules restricting internal DNS to internal networks
* Screenshots or logs of internal vs. external DNS query results
* Change control tickets for DNS role changes
* Policy or procedure on DNS server role separation

---

#### **HITRUST Requirement – Firewall and Router Configuration Standards**

#### Control ID: 09.m Network Controls Control Type: Technical Control Level: Moderate HIPAA Mapping: 164.308(a)(1)(ii)(A) – Risk Analysis, 164.312(a)(1) – Access Control

🎯 **Control Objective**

Ensure firewall and router configurations follow documented security standards to protect systems handling sensitive data.

🛠️ **Technical Implementation**

1. Defined Configuration Standards

   * Written standards exist for: Firewall configuration and Router configuration.
2. Coverage of Sensitive Information Connections

   * Standards:

     + Explicitly address all connections to systems handling covered information, including wireless networks.
3. Business Justification

   * All services, ports, and protocols allowed are:

     + Documented
     + Supported by a business need
     + Reviewed as part of access change or firewall rule change process
4. Handling of Insecure Protocols

   * When insecure protocols (e.g., FTP, Telnet) are used:

     + Security features (e.g., tunneling, encryption) are documented and implemented.
5. Firewall and Router Rule Set Maintenance

   * Rules are:

     + Reviewed and updated at least every 180 days
     + Reviewed more frequently upon system or network architecture changes

📋 **Possible Evidence to Collect**

* Firewall/router configuration standards document
* Rule review logs or review tickets from past 6 months
* List of approved services/ports with business justification
* Change request or risk acceptance documentation for insecure protocol use
* Network architecture diagrams showing firewall and router placement
* Screenshots of configuration rule sets and rule revision history

---

**HITRUST Requirement – Wireless Network Identification and Control**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: Moderate  
HIPAA Mapping:164.312(a)(1) – Access Control, 164.312(c)(1) – Integrity

### 🎯 **Control Objective**

Ensure that wireless networks implement strong access restrictions and device identification through MAC address authentication and static IP assignments.

**Technical Implementation**

1. MAC Address Authentication

   * Wireless access points and controllers are configured to:

     + Allow network access only to devices with known, pre-authorized MAC addresses.
     + Enforce this policy via centralized wireless management platforms (e.g., Cisco ISE, Aruba ClearPass).
2. Static IP Address Assignment

   * Wireless devices connected to sensitive systems:

     + Are assigned static IP addresses.
     + Static IPs are managed through DHCP reservations or manual configuration.
     + Used in conjunction with firewall rules to restrict traffic and enhance traceability.

📋 **Possible Evidence to Collect**

* Configuration screenshots of wireless controller enforcing MAC address filtering
* List of approved device MAC addresses
* DHCP configuration files showing static IP reservations
* Network diagram highlighting wireless IP assignments
* Logs demonstrating denied connections due to MAC/IP mismatches
* Policy documentation outlining wireless network controls

---

**HITRUST Requirement – Multi-Vendor Firewall Architecture**

Control ID: 09.m Network Controls  
Control Type: Technical  
Control Level: High  
HIPAA Mapping: 164.312(c)(1) – Integrity, 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Reduce single points of failure and improve traffic inspection capabilities by implementing layered firewall defenses using different vendors and technologies.

🛠️ **Technical Implementation**

1. Vendor Diversity

   * The organization deploys firewalls from at least two distinct vendors (e.g., Palo Alto and Fortinet).
   * This ensures that vulnerabilities in one vendor’s platform do not compromise all firewall protections.
2. Stateful Packet Inspection

   * All firewalls in use employ stateful packet inspection (SPI):

     + Also referred to as dynamic packet filtering.
     + Monitors active connections and allows or blocks traffic based on state, port, and protocol.
     + Ensures that only legitimate, established sessions are permitted.
3. Zoned Architecture

   * Firewalls are deployed at different zones (e.g., external perimeter, DMZ, internal segmentation) to enforce layered defenses.

📋 **Possible Evidence to Collect**

* Network architecture diagram showing different firewall zones and vendors
* Vendor purchase orders or service contracts
* Configuration exports confirming SPI is enabled
* Screenshots from both firewall platforms demonstrating operational status
* Internal security policy requiring multi-vendor firewall deployment
* Change logs showing configuration management across vendors

---

**HITRUST Requirement – Network Service Provider Management**

Control ID: 09.n Security of Network Services  
Control Type: Administrative  
Control Level: Moderate  
HIPAA Mapping: 164.308(a)(1)(ii)(A) – Risk Analysis, 164.308(a)(8) – Evaluation, 164.308(b)(1) – Business Associate Contracts

🎯 **Control Objective**

Ensure that third-party network service providers deliver secure, monitored, and auditable services that meet documented security and management requirements.

🛠️ **Administrative Implementation**

1. Capability Assurance

   * The organization evaluates the provider’s ability to securely deliver services through:

     + Pre-contract due diligence.
     + Periodic reassessments and monitoring of service delivery.
2. Audit Rights

   * Right to audit is included in contractual agreements for each network service provider, ensuring visibility and accountability.
3. Security & Service Agreements

   * For each critical network service, the following are identified and documented:

     + Security features (e.g., encryption, DDoS protection).
     + Service levels (SLAs) including availability, latency, and uptime commitments.
     + Management requirements, including escalation procedures, incident response participation, and reporting obligations.

📋 **Possible Evidence to Collect**

* Third-party risk assessments
* Service provider contracts including audit clauses and security SLAs
* Monitoring reports and metrics reviews
* Documentation of identified security features, SLAs, and management responsibilities
* Audit reports or third-party SOC 2 attestations
* Vendor management policies

---

**HITRUST Requirement – Interconnection Security Agreements**

Control ID: 09.n Security of Network Services  
Control Type: Administrative  
Control Level: Moderate  
HIPAA Mapping: 164.308(a)(1)(ii)(D) – Information System Activity Review, 164.308(b)(1) – Business Associate Contracts, 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Ensure that all system interconnections with external or internal parties are formally authorized and well-documented to enforce accountability, traceability, and appropriate security controls.

🛠️ **Administrative Implementation**

1. Formal Authorization

   * The organization requires formal interconnection security agreements (ISAs) or other written agreements prior to establishing any system-to-system connections.
2. Central Documentation  
   The organization maintains centralized records that include:

   * Interface characteristics (e.g., protocols used, directionality, logical boundaries).
   * Security requirements (e.g., encryption, access controls, monitoring expectations).
   * Information communicated (e.g., data types, sensitivity levels, classification).

📋 **Possible Evidence to Collect**

* Interconnection Security Agreements (ISAs)
* Data flow diagrams highlighting authorized interconnections
* System Security Plans (SSPs) documenting interface characteristics
* Network architecture or integration documentation
* Inventory of authorized connections with documented metadata
* Audit trail or version history of interconnection agreements

---

**HITRUST Requirement – External System Interconnection Controls**

Control ID: 09.n Security of Network Services  
Control Type: Administrative  
Control Level: High  
HIPAA Mapping: 164.308(a)(1)(ii)(D) – Information System Activity Review, 164.308(b)(1) – Business Associate Contracts, 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Ensure that external system interconnections are secured through formal agreements that define responsibilities, enforce security requirements, and ensure accountability for protecting covered information.

🛠️ **Administrative Implementation**

The organization requires that interconnection agreements or equivalent formal documentation:

1. Mandate compliance with the organization’s information security policies and standards.
2. Enforce security controls aligned with applicable federal laws, Executive Orders, regulations, and guidance.
3. Define and document roles and responsibilities, including oversight and user access for external system services.
4. Authorize organizational monitoring of provider’s compliance with security controls.
5. Require FIPS-validated encryption or alternative physical protections for data transmissions.
6. Assign accountability to the external provider for protecting covered information.

📋 **Possible Evidence to Collect**

* Interconnection Security Agreements (ISAs) or Memoranda of Understanding (MOUs)
* Risk assessments of connected systems
* Audit logs showing monitoring of external interconnections
* Contracts that reference FIPS-compliant encryption
* Compliance reports or attestations from service providers
* Documentation of roles and responsibilities for external services

---

**HITRUST Requirement – Interconnection Agreement Review & Verification**

Control ID: 09.n Security of Network Services  
Control Type: Administrative  
Control Level: Moderate  
HIPAA Mapping:164.308(b)(1) – Business Associate Contracts and Other Arrangements, 164.308(a)(1)(ii)(D) – Information System Activity Review

🎯 **Control Objective**

Ensure that interconnection security agreements are consistently maintained and enforced to support continued protection of information shared across systems.

🛠️ **Administrative Implementation**

The organization:

1. Reviews and updates interconnection security agreements (ISAs), memoranda of understanding (MOUs), or similar formal documents on an ongoing basis, particularly after significant changes to systems, providers, or threats.
2. Verifies enforcement of security requirements agreed upon in interconnection agreements, including through monitoring, audits, or third-party assessments.

📋 **Possible Evidence to Collect**

* Revision history or change logs of interconnection agreements
* Records of periodic ISA review schedules or completion reports
* Monitoring reports confirming third-party enforcement of security terms
* Audit logs or findings of compliance verification efforts
* Documentation of updates following system or provider changes
* Records of internal risk assessments related to interconnection points

---

**HITRUST Requirement – Formal Connection Policy for External Systems**

Control ID: 09.n Security of Network Services  
Control Type: Administrative  
Control Level: Moderate

🎯 **Control Objective**

Ensure that connections to external information systems are explicitly authorized and governed under formalized, risk-based access policies.

🛠️ **Administrative Implementation**

The organization:

1. Documents in a formal agreement or applicable security documentation a defined policy that governs connections to external information systems.
2. Applies either:

   * Allow-all, deny-by-exception, or
   * Deny-all, permit-by-exception *(preferred)*  
     approach to manage external system connections.
3. Ensures policies are defined per system and reflected in associated interconnection agreements, risk acceptance records, or system security plans.

📋 **Possible Evidence to Collect**

* Interconnection Security Agreements (ISA) or MOUs with documented access policy
* System Security Plans referencing access rules to external systems
* Network diagrams showing approved connections
* Risk acceptance memos documenting exceptions
* Policy documents establishing the deny-all/permit-by-exception model
* Logs or records of exceptions granted and reviewed

---

**HITRUST Requirement – External Service Provider Network Specifications**

Control ID:09.n Security of Network Services  
Control Type: Administrative  
Control Level: Moderate  
HIPAA Mapping: 164.308(b)(1) – Business Associate Contracts and Other Arrangements, 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Ensure the organization maintains visibility and control over the network behavior of external or outsourced service providers to manage risk to systems and data.

🛠️ **Administrative Implementation**

The organization requires external or outsourced service providers to explicitly identify and document the:

1. Functions they perform that require network access,
2. Ports used to enable the communication of services, and
3. Protocols necessary for service delivery.

This information is collected during onboarding and updated whenever services or configurations change. The data is incorporated into risk assessments, access control rules, and firewall configurations as needed.

📋 **Possible Evidence to Collect**

* Completed network access request forms from third parties
* Service Level Agreements (SLAs) or contracts identifying port/protocol usage
* Technical documentation or runbooks from the vendor
* Change control tickets showing port/protocol updates
* Firewall rule documentation referencing vendor-specific traffic
* External system risk assessment records

---

**HITRUST Requirement – Contractual Responsibility for Covered Information**

Control ID: 09.n Security of Network Services  
Control Type: Administrative  
Control Level: Moderate  
HIPAA Mapping: 164.308(b)(1) – Business Associate Contracts and Other Arrangements

🎯 **Control Objective**

Ensure external or outsourced service providers are contractually obligated to safeguard covered information.

🛠️ **Administrative Implementation**

The organization ensures that contracts with external or outsourced service providers:

1. Explicitly include language specifying that the service provider is responsible for the protection of covered information shared during the course of service delivery.

This requirement is enforced during vendor onboarding, contract negotiation, and periodic vendor reviews.

📋 **Possible Evidence to Collect**

* Business Associate Agreements (BAAs)
* Signed vendor contracts or master service agreements (MSAs)
* Contract clauses highlighting data protection responsibilities
* Third-party risk assessment documentation
* Compliance review checklists confirming contract terms
* Legal review records for vendor agreements

---

**HITRUST Requirement – Application and Network Firewalls for Public-Facing Systems**

Control ID: 10.b Input Data Validation  
Control Type: Technical  
Control Level: Moderate  
HIPAA Mapping: 164.312(e)(1) – Transmission Security

🎯 **Control Objective**

Ensure that appropriate firewalls are in place for public-facing applications, whether web-based or otherwise, and that encrypted traffic is properly inspected.

🛡️ **Technical Implementation**

The organization ensures:

1. Application-level firewalls (e.g., Web Application Firewalls – WAFs) are implemented for all public-facing web applications.
2. For non-web-based public-facing applications, network-based firewalls are implemented that are specific to the application type.
3. If traffic to the public-facing application is encrypted, the inspecting device:

   * either resides behind the encryption termination point, or
   * is capable of decrypting the traffic prior to performing inspection or analysis.

📋 **Possible Evidence to Collect**

* WAF deployment diagrams and configuration screenshots
* Firewall rulesets or configuration settings for application-specific protection
* Architecture diagrams showing placement of decryption devices (TLS termination points)
* Logs from decrypted traffic inspection systems
* Change control records for firewall deployments
* Penetration testing results showing firewall coverage

---

Note: Some controls will not be applicable to the Landing Zone build such as VOIP and Wireless Technologies. The controls have been accounted for in the above documentation for informational purposes.