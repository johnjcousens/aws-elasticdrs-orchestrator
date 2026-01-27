# Decision---IAM-Users-Credentials-Management-Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867098050/Decision---IAM-Users-Credentials-Management-Design

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Kyle Pearson (Deactivated) on August 12, 2025 at 02:30 PM

---

### Document Lifecycle Status

**Purpose**
-----------

This document describes controls which will be implemented to protect AWS Accounts IAM Users.

**Implementation**
------------------

Use Break the Glass IAM User for emergency access during SAML federation environment failures. IAM Users with access keys but without console passwords will be permitted in limited use cases if a business justification is provided and explicit approval is received. Any other IAM users with console passwords will not be permitted.

BreakGlass IAM User will be configured in the Management account. Break the Glass user will have to assume BreakGlass IAM Role (link to Human IAM Roles design page) in an account before being able to perform any actions.

Complete the following table with details of Break Glass User(s) to be implemented through Landing Zone Accelerator

| User | Purpose | Capabilities | Access Policy |
| --- | --- | --- | --- |
| he-user-breakglass | Emergency access in case Okta is down | Ability to assume breakglass IAM Role in all accounts | he-user-breakglass Access Policy {  "Version": "October 17, 2012",  "Statement": \[  {  "Effect": "Allow",  "Action": "sts:AssumeRole",  "Resource": "arn:aws:iam::\\*:role/he-role-breakglass"  }  \]  } |

**IAM Users Security Preventative Guardrails**

HealthEdge will enforce a set of preventative and detective security controls to protect AWS accounts credentials and prevent deviations from the developed IAM credentials management baseline.

HealthEdge will implement the following security measures to properly protect the password associated with the Break the Glass user:

1. Strong password policy will be configured for all AWS Accounts which will:

   1. Require a minimum password length of 8 (recommended ≥ 12);
   2. Require at least one uppercase latter;
   3. Require at least one lowercase letter;
   4. Require at least one number;
   5. Require at least one non-alphanumeric character;
   6. Prevent password reuse (number of passwords to remember 6);
   7. Enable password expiration (90 days);
   8. Allow users to change their own passwords;

      1. Except for shared breakglass/emergency accounts;
2. Break the Glass password will be managed in HealthEdge Secrets Server.
3. No access key will be generated for the Break the Glass user.
4. MFA will be enabled through using Yubikeys.

   1. One key will be stored in the Boston office;
   2. One key will be stored in the Alexandria office;
5. Additional preventative controls will be implemented using AWS Organizations Service Control Policies (SCPs) (link to Service Control Policies (SCPs) Design artifact).

There might be other use cases when HealthEdge would have to create IAM Users for programmatic access (e.g. for applications which do not support temporary credentials). HealthEdge will implement the following security measures to properly protect the access keys associated with these users:

1. Access Keys will be rotated at least every 90 days.

In addition, a process for requesting a creation of IAM Users using standard change request procedures will be implemented to strictly regulate the amount of permanent credentials present in AWS accounts.

#### **IAM Users Security Detective Guardrails**

1. Detective controls will be implemented using a combination of AWS Config Rules and AWS CloudWatch Alarms (link to Detective Controls Design artifact). In order to detect unused credentials, HealthEdge will implement an AWS managed Config Rule (“Detect unused credentials”) which will periodically evaluate AWS accounts and detect any passwords or access keys which have not been used within 90 days.
2. HealthEdgewill also use a set of manual procedures to detect unused privileges which can be automated in the future.