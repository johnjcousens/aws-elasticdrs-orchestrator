# Root-Credentials-Management

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867065430/Root-Credentials-Management

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:34 AM

---

---

**Purpose**
-----------

This document describes controls which will be implemented to protect AWS Accounts' Root user.

**Implementation**
------------------

The AWS Root user is accessed by signing in with the email address and password that were used to create an AWS Account. This user is unconstrained by IAM policies. A set of preventative and detective security controls will be deployed to protect AWS Root credentials and prevent deviations from the developed IAM credentials management baseline, which aligns to Well-Architected best practices.

### **Root user Security Preventative Guardrails**

The following security measures will be implemented to properly protect the Root:

1. Root user will only be used for tasks which require Root credentials. The most up to date list of such tasks can be found [here](https://docs.aws.amazon.com/general/latest/gr/aws_tasks-that-require-root.html).
2. Root password will be generated using a random number generator provided by a Secrets Management platform (e.g. LastPass, CyberArk).
3. Root password will be stored in a Secrets Management platform (e.g. LastPass, CyberArk) and will only be accessible by a limited group of people responsible for AWS accounts administration.
4. Hardware MFA (e.g. YubiKey, Gemalto) will be used for the Root credentials of every AWS account to provide for two-factor authentication.
5. Hardware MFA tokens will be stored in a physical safe located at an IT department office accessible by a limited group of people responsible for AWS accounts administration.
6. No access keys will be created for the Root.
7. Account Security Challenge Questions and Answers will be stored in a Secrets Management platform (e.g. LastPass, CyberArk).

### **Root user Security Detective Guardrails**

1. Detective controls will be implemented using a combination of AWS Config Rules and AWS CloudWatch Alarms (link to Detective Controls Design artifact).

### **Recovery of Root Security Credentials**

1. If Root MFA device is lost or MFA device stopped working, [Customer] can use alternative factors of authentication to log into the account as described in [this document](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa_lost-or-broken.html). In case of any issues with the described procedure, [Customer] can contact AWS Customer Service directly or fill up this online [form](https://aws.amazon.com/forms/aws-mfa-support) to regain access to the account.
2. If Root user password is lost, [Customer] can use AWS Management Console to reset the password as described in this [document](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys_retrieve.html#reset-root-password).
3. AWS Customer Service team can also be contacted in regard to any account access related issues. AWS Customer Service team member may be required to validate your identity by verifying Security Challenge Questions configured in the account.