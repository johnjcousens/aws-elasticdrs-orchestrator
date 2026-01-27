# [To Be Deleted] - Password Management

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4982177857/%5BTo%20Be%20Deleted%5D%20-%20Password%20Management

**Created by:** Alexandria Burke on August 04, 2025  
**Last modified by:** Shreya Singh on August 08, 2025 at 06:23 PM

---

**HITRUST Requirement: Password Policy documentation and enforcement**  
Control ID: 01.f – Password Policy Enforcement  
Control Type: Technical  
Control Level: Implementation  
HIPAA Mapping: 45 CFR §164.308(a)(5)(ii)(D) – Log-in Monitoring

**Control Objective:**  
Ensure secure authentication by documenting and enforcing password requirements through technical mechanisms that prevent weak or unauthorized credentials.

AWS Technical & Operational Implementation:

Password Policy Configuration  
Use AWS IAM password policy to define and enforce password complexity, rotation frequency, minimum length, reuse prevention, and MFA requirements.  
Enforce IAM best practices, including enabling IAM Identity Center for centralized user authentication and policy enforcement across AWS accounts.

Technical Enforcement Controls  
Enable IAM Identity Center or integrate with external identity providers like Okta or Azure AD via SAML to enforce enterprise-grade password policies and single sign-on.  
Leverage AWS Config to continuously audit password policy compliance.  
Use AWS Organizations Service Control Policies (SCPs) to restrict IAM password policy overrides or misconfigurations.  
Enable IAM Access Analyzer to monitor for unintended access paths and credential exposures.

Monitoring and Logging  
Track all IAM authentication and password policy events using AWS CloudTrail and analyze them in CloudWatch Logs or AWS Security Hub.  
Configure Amazon GuardDuty to detect brute-force login attempts or unusual IAM activity.

Evidence to Collect:  
IAM password policy configuration screenshot or Terraform code  
CloudTrail logs showing password policy enforcement or MFA usage  
GuardDuty alerts for login anomalies  
Config rule evaluation history for password policy compliance  
Identity Center configuration details showing enforced password requirements and integrations