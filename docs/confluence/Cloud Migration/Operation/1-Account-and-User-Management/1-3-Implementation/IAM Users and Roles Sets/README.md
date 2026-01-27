# IAM Users and Roles Sets

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4965630444/IAM%20Users%20and%20Roles%20Sets

**Created by:** Lei Shi on July 29, 2025  
**Last modified by:** Lei Shi on July 29, 2025 at 02:38 PM

---

Health Edge IAM roles Design
============================

Below are breakdown of initial IAM roles design pattern for Health Edge various teams and responsibilities:

**Platform Team**


```
- PlatformAdmin
  * Access to shared services management
  * Control Tower and Landing Zone Accelorator administration
  * Organization policy management
  * Cross-account role management

- PlatformEngineer
  * Access to service catalog
  * Limited access to shared resources
  * Access to automation tools
```


**CloudOps Team**


```
- CloudOpsAdmin
  * Full access to EC2, ECS, EKS, Lambda
  * Limited access to network configuration
  * Access to CloudWatch, Systems Manager
  * Access to CI/CD services

- CloudOpsEngineer
  * Read access to all resources
  * Limited write access to compute resources
  * Access to deployment tools
  * Access to monitoring and logging

- CloudOpsReadOnly
  * Read-only access to all operational resources
  * View logs and metrics
```


**Network Team**


```
- NetworkAdmin
  * Full access to VPC, Transit Gateway, Direct Connect
  * Access to Route53, CloudFront
  * Network ACLs and Security Groups management
  * VPN and connectivity configuration

- NetworkEngineer
  * Modify network configurations
  * View and modify routing tables
  * Limited security group modifications
  * Read access to all network resources
```


**Security Team**


```
- SecurityAdmin
  * Full access to IAM, Organizations, Control Tower
  * Access to GuardDuty, Security Hub, Macie
  * Access to AWS Config, CloudTrail
  * KMS and certificate management

- SecurityAnalyst
  * Read access to security services
  * Access to security findings
  * Limited IAM read access
  * Access to compliance reports
```


**FinOps Team**


```
- FinOpsAdmin
  * Full access to Cost Explorer, Budgets
  * Access to Organizations for billing
  * Read access to resource inventory
  * Access to Savings Plans and Reserved Instances

- FinOpsAnalyst
  * Read access to billing and cost management
  * Access to cost optimization recommendations
  * View resource utilization metrics
```


**Application Teams**


```
- ApplicationDeveloper
  * Access to specific application resources
  * Limited to dev/test environments
  * Access to relevant CI/CD tools
  * Read-only access to logs

- ApplicationAdmin
  * Full access to application resources
  * Access to production deployments
  * Database management access
```


**Other Common Cross-Cutting Permissions:**


```
- Break-Glass Role
  * Emergency full admin access
  * Heavily audited and monitored
  * Requires multi-person approval

- ReadOnly Role
  * Organization-wide read access
  * Available to all technical staff
  * No modify permissions

- Audit Role
  * Access to logs and audit trails
  * Cross-account access for auditing
  * Read-only access to configurations
```


**Best Practices:**

1. Implement least privilege principle
2. Use AWS managed policies where possible
3. Implement role assumption with MFA
4. Regular access reviews
5. Use tags for resource-based access control
6. Implement separation of duties
7. Use permission boundaries for delegation
8. Implement emergency access process

**This pattern should be:**

* Implemented with AWS Organizations
* Enforced with Service Control Policies (SCPs)
* Monitored with AWS CloudTrail
* Automated with IaC (Terraform/CloudFormation)
* Integrated with corporate identity provider
* Regularly reviewed and updated

Note: Adapt these patterns based on specific organizational requirements, compliance needs, size of teams, application architecture, and security requirements. These factors should inform how you customize and implement the IAM role patterns while maintaining proper access controls and security posture.