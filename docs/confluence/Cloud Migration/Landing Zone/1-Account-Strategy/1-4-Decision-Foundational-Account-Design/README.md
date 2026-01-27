# 1-4-Decision-Foundational-Account-Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867065111/1-4-Decision-Foundational-Account-Design

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Gary Edwards on July 11, 2025 at 03:33 AM

---

---

title: 1.4 Decision Foundational Account Design
-----------------------------------------------

**Purpose**
-----------

To deploy Landing Zone Accelerator (LZA) on AWS requires a multi-account structure with a minimum of 3 accounts: Management, LogArchive, and Audit. Additional accounts will be added to support the migration. Use this page to document the decisions and design details for your foundational accounts.

**Decision**

HealthEdge has decided to deploy LZA with [AWS Control Tower](https://aws.amazon.com/controltower/). In addition, [AWS Organizations](https://aws.amazon.com/organizations/) will also be deployed as required to support the landing zone.

**Foundational Accounts**
-------------------------

### **Root (Management) Account**

**This account is a mandatory account for Control Tower and required for the LZA deployment.**

Charges for all Organization member accounts roll up into the management account. All member accounts will be linked to this billing account via AWS Organizations consolidated billing feature. This account will store detailed billing reports for all Organization member accounts, analyze the AWS usage and spend, and have preset budgets with billing alarms to provide notification in case of any budget threshold breach.

Additionally, this account serves as the AWS Organizations management account, and has the capability to create other AWS accounts. Every new account created is automatically linked to the management account for consolidated billing.  
This account should not contain any application workloads, it should only deploy solutions or tools that are necessary for account and cost management. Business level support is recommended as a minimum for the management account.

|  |  |
| --- | --- |
| **Users** | CCOE Team |
| **Typical Components** | * AWS Organizations * Control Tower * IAM Identity Center * Solutions: Landing Zone Accelerator |

### **LogArchive Account**

**This account is is a mandatory account for Control Tower and required for the LZA deployment.**

This account is used for security and compliance-related logging activities. It hosts the aggregated CloudTrail, Config, and CloudWatch logs from all Organization member accounts. These logs can be analyzed using native AWS services or ingested into third-party log analysis tools.

|  |  |
| --- | --- |
| **Users** | Security/Compliance Team |
| **Typical Components** | * S3 bucket for centralized logs of all Organization member accounts |

### **Audit Account**

**This account is is a mandatory account for Control Tower and required for the LZA deployment.**

This account is for security auditing activities. This account is also responsible for maintenance of the overall security posture of all Organization member accounts as it can scan for vulnerabilities (i.e., ports open to the world) at periodic intervals. It may either take a corrective action or alert the user of any security or compliance events.

|  |  |
| --- | --- |
| **Users** | Security/Compliance Team |
| **Typical Components** | * Cross-account role for administrator access to all Organization member accounts * Security Hub delegated administrator * GuardDuty delegated administrator * Macie delegated administrator |

### **Network Account**

**Decision: Use Networking account**

This account acts as the global network transit center connecting VPCs among Organization member accounts and remote networks.

|  |  |
| --- | --- |
| **Users** | Infrastructure/Network Team |
| **Typical Components** | * Transit Gateway * Direct Connect Gateways * Centralized Network Firewall * VPN Site to Site Termination * Centralized VPC Endpoints |

### **Shared-Services Account**

**Decision: Use SharedServices Account**

This account hosts common services that can be shared by applications or workloads among Organization member accounts. It can be used to host golden AMIs or service catalog portfolios that are shared with application accounts.

|  |  |
| --- | --- |
| **Users** | Infrastructure/Network Team |
| **Typical Components** | * IAM Identity Center delegated administrator * AD, DNS, etc., services * Service Catalog shared portfolios * Golden AMI repository |

### **Migration Account**

**Decision: Use Migration Account**

This account hosts Cloud Migration Factory and a common VPC that will be used to share subnets to all workload accounts. This migration VPC exists to support staging the server before cut-over. After the migration is complete, this migration account can be removed.

|  |  |
| --- | --- |
| **Users** | Migration Team |
| **Typical Components** | * VPC to share to workload accounts to support staging migration instances * Solutions: Cloud Migration Factory |

**Optional Accounts by LOB, Applications, Projects**
----------------------------------------------------

### **Sandbox Account**

This is a time- and financially-boxed experimental account for developers to try new services. It does not have network connectivity to any other VPCs in the landing zone or remote networks. Services use should be short lived with no production class data being stored in these account types. Usually more permissive to allow new service testing with preset budget limits and alerts. Resources in these accounts are expected to be temporary.

### **Dev/Test Accounts**

These application accounts are used for development and testing. They have network connectivity across the landing zone and to external networks. They will have a more stringent security and compliance baseline compared to sandbox accounts but less stringent than production accounts.

### **Production Accounts**

These accounts host the production version of applications. They have a similar setup as the Dev/Test accounts with the highest level of security and compliance controls. Business level support is recommended as a minimum for production accounts. Larger multi account customer should consider Enterprise support which is organization-wide, opposed to business support which is based per account.

**Account Design**
------------------

Complete the table below with information specific to your accounts.

| **Account Name** | **OU Name** | **Role** | **Email** | Billing Contact | Operations Contact | Security Contact | **Account ID** | **Organization ID** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Management\* | Root | Management Billing and Root AWS Organizations Account | [aws@healthedge.com](mailto:aws@healthedge.com) | Full Name:  Title:  Email: [aws-billing@healthedge.com](mailto:aws-billing@healthedge.com)  Phone #: | Full Name:  Title:  Email: [aws-operations@healthedge.com](mailto:aws-operations@healthedge.com)  Phone #: | Full Name:  Title:  Email: [aws-security@healthedge.com](mailto:aws-security@healthedge.com)  Phone #: | xxxxxxxxxxxx | x-xxxxxxxxxx |
| LogArchive\* | Security | Central security log aggregation account | [aws+log-archive@healthedge.com](mailto:aws+log-archive@healthedge.com) |  |  |  | xxxxxxxxxxxx | NA |
| Audit\* | Security | Central security audit account | [aws+audit@healthedge.com](mailto:aws+audit@healthedge.com) |  |  |  | xxxxxxxxxxxx | NA |
| SharedServices | Infrastructure | Central shared services account | [aws+shared-services@healthedge.com](mailto:aws+shared-services@healthedge.com) |  |  |  | xxxxxxxxxxxx | NA |
| Network | Infrastructure | Central networking resources | [aws+network@healthedge.com](mailto://aws+network@healthedge.com) |  |  |  | xxxxxxxxxxxx | NA |
| Migration | Infrastructure | An account dedicated to Cloud Migration Factory | [aws+migration@healthedge.com](mailto://aws+migration@healthedge.com) |  |  |  | xxxxxxxxxxxx | NA |
| <<TBD>> | Workloads | Your first workload account |  |  |  |  |  |  |

*\*Mandatory accounts for Landing Zone Accelerator deployment*