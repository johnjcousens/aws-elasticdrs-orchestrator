# Sandbox Accounts - Proposed Approach

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4942857260/Sandbox%20Accounts%20-%20Proposed%20Approach

**Created by:** Chris Falk on July 18, 2025  
**Last modified by:** Chris Falk on July 29, 2025 at 02:20 PM

---

Executive Summary
-----------------

This document outlines the recommended approach for providing AWS sandbox environments that enable innovation while maintaining appropriate security controls and avoiding shadow IT. The strategy provides two tiers of environments with different security postures and capabilities.

Current State & Requirements
----------------------------

The need for AWS experimentation and innovation across multiple teams requires a balanced approach that enables rapid prototyping while maintaining appropriate security controls. Teams across the organization, including data platform, BI, DevOps, and others need environments to explore new AWS services, develop skills, and prototype solutions for specific projects. Because sandbox requirements are a subset of the full landing zone requirements, they can be made available sooner than the point of full landing zone migration readiness, in order to unblock work awaiting AWS availability.

In the absence of a balanced sandbox approach that enables users to innovate quickly, it is likely that teams may open their own AWS accounts with no restrictions, resulting in shadow IT risk that is difficult to identify and rein in.

Proposed Approach
-----------------

### Environment Types

To address these needs, we propose implementing two distinct environment types. Pure sandbox environments will provide isolated spaces for experimentation with no connectivity to corporate networks. These environments will be temporary by design, automatically cleaning up after periods of inactivity while maintaining basic security controls and security/cost monitoring. This approach allows for rapid provisioning with minimal overhead while still protecting organizational assets.

In parallel, as part of the full landing zone implementation, we will establish more controlled development environments for teams requiring connectivity to on-premises systems. These environments will implement full security controls and monitoring, support longer-lived resources, and require architectural review board approval for significant changes.

As the landing zone matures in the coming months, additional security and other capabilities can be retroactively implemented in sandbox accounts to further improve preventative and detective controls.

### Sandbox Usage Policy

Teams should use sandbox environments for initial AWS service experimentation, learning, and proof-of-concept work where no production data or on-premises connectivity is required. Sandboxes are temporary environments that will be automatically decommissioned after periods of inactivity, and teams should expect resources to be regularly cleaned up. These environments have basic security controls but limited connectivity options.

In contrast, development accounts should be used when teams are ready to build actual solutions that require connectivity to on-premises systems, need to persist beyond short experimental phases, or require integration with other corporate resources. Development accounts have stricter security controls, require architectural review board approval, and support proper lifecycle management of resources. Teams should understand that work in sandboxes cannot be directly promoted to production - instead, successful prototypes must be rebuilt in development environments following proper security and architectural standards. Sandbox environments are ideal for teams learning new AWS services or validating technical approaches, while development accounts are for building actual solutions intended for eventual production use.

### Prerequisites

Before implementation can begin, several prerequisites must be in place. These include:

* Deploying the Landing Zone Accelerator and initial security controls, SCPs
* Completing Okta integration and defining initial user personas and IAM roles
* Implementing additional security controls detailed in the following section
* Establishing an initial budget and cost management framework, using AWS Budgets and alerts
* Defining VPC structure and network restrictions
* Initial service quotas reviewed and any increase needs determined

Initial security controls (for example, the Control Tower [strongly recommended controls](https://docs.aws.amazon.com/controltower/latest/controlreference/strongly-recommended-detective-controls.html)) will be determined and enabled in Control Tower using LZA automation, and AWS Service Control Policies (SCPs) will define the allowed services for all environments. As new services are needed, they can be added to the SCPs.

A VPC structure will need to be defined that allows for minimal friction to avoid users having to repeatedly ask for elevation of privileges or additional functionality, and this VPC will be implemented with a CDK stack at account vending, with distinct CIDR blocks allocated from AWS IPAM. Users will be prohibited from modifying the fundamental VPC structure and capabilities.

### Minimum Security Controls for Sandboxes

Even in sandbox environments, we will maintain essential security controls, though initially they may be less comprehensive than they will be at the completion of landing zone implementation. Within two months of implementation of the sandbox approach, a mechanism will be implemented for automated stop and cleanup of unused resources. The initial minimum security requirements for sandbox accounts include:

* Deployed by AWS Professional Services Team

  + Control Tower controls to restrict dangerous actions (e.g. public S3 buckets, 0.0.0.0/0 RDP/SSH, etc.)
  + Service Control Policies (SCPs) to:

    - Restrict AWS marketplace access
    - Restrict unused or undesired services (e.g. WorkSpaces) and permit only [HIPAA-eligible](https://aws.amazon.com/compliance/hipaa-eligible-services-reference/) services
    - Prevent creation of new VPCs in sandbox accounts
  + VPC template for a basic, isolated VPC with Internet access

    - Proposed structure: VPC with four subnets, 2 public, 2 private, IGW, NAT Gateway (across 2 AZs) with **no VPN or other connectivity to on-prem or other AWS networks**
  + Guard Duty enablement including optional runtime protection for EC2 and EKS workloads
  + Macie enabled for detection of PHI
  + Define and implement initial Sandbox IAM persona (Admin with a deny all on specific services disallowed above)
  + As a shared responsibility with the HealthEdge security team, support the implementation of CloudTrail centralized log ingestion into CrowdStrike Falcon
* HealthEdge Security Team and leadership responsibilities

  + CPSM integration with Wiz
  + Perform CloudTrail log ingestion implementation with CrowdStrike with the assistance of the AWS ProServe team
  + Provide a list of services that HealthEdge does not want enabled
  + Define and communicate a clearly defined policy for sandbox use versus dev account use

### Timeline

The implementation will follow a phased approach. In the initial phase, lasting 2-3 weeks, we will deploy basic sandbox capabilities with essential security controls and identity integration. The second phase, implemented alongside landing zone completion, will encompass network-connected development environments, complete security tooling integration, and establishing the full governance framework.

Phase 0 (by Friday, August 1)

* AWS and HealthEdge teams to complete the above responsibilities, assuming blocked service list provided by end of day Wednesday, July 30
* Vend one initial sandbox account for validation

Phase 1 (sprints O+P, 4 weeks, ending August 13, or earlier):

* Vend additional accounts needed at this time
* User access provisioned

Phase 2 (sprints Q+R+S, 6 weeks):

* Network-connected development environments
* Full security tooling integration
* Complete governance framework
* Stand up “dev” environments

### Risk Management

Risk management remains a key consideration. During initial deployment, we will mitigate security exposure through clear usage guidelines, monitoring, and limited access. Cost management concerns will be addressed through budget monitoring and automated cleanup procedures. To prevent shadow IT, we will establish clear promotion paths to development and higher environments that require architectural review.

This strategy balances the need for innovation with security requirements, providing a structured approach to AWS experimentation while maintaining appropriate controls and governance.

Questions & Next Steps
----------------------

Several key questions require clarification to refine this approach, including the expected number of sandbox environments, maximum duration for sandbox resources, specific compliance requirements, and the process for promoting sandbox work to production. Moving forward, we will need to review and approve minimum security controls, define detailed implementation plans, create account provisioning automation, develop user guidelines, and establish monitoring and feedback processes.