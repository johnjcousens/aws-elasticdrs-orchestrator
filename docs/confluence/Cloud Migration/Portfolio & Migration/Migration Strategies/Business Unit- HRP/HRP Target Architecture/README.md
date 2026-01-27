# HRP Target Architecture

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5118230559/HRP%20Target%20Architecture

**Created by:** Khalid Ahmed on September 23, 2025  
**Last modified by:** Khalid Ahmed on September 23, 2025 at 02:56 PM

---

**Document Objective**
======================

This Design Document outlines the architectural framework and general information for the HealthEdge HRP implementation in the AWS cloud. This document is intended for technical personnel with working knowledge of AWS services and terminology.

Background
==========

This document outlines the “HRP Architecture Design for AWS Cloud” and is subject to client review, modifications, and approvals prior to implementation. Upon reviewing this document, readers will gain a comprehensive understanding of HRP business units target architecture for its AWS environment, as well as the key elements that need to be addressed to successfully implement this strategy. It is important to note that this strategy is expected to be dynamic and evolve over time as additional perspectives and considerations come to light.

Target State
============

Below diagram shows the target state for Health Rules Payor (HRP)  in AWS. This architecture diagram follows the Re-host migration strategy. Each key component is described in detail in the architectural components table section below.

![HRP-Target-Architecture.drawio_(2).png](images/HRP-Target-Architecture.drawio_(2).png)

*Target Architecture*

The HealthRules Payor (HRP) migration to AWS employs a strategic "lift and shift" approach using AWS Application Migration Service (MGN) for the majority of infrastructure components. This rehost strategy will maintain the existing architectural relationships shown in the diagram while transitioning key servers—Load Balancer, Connector, Payor, PIK, MQ, Answers, and standalone database servers—to Amazon EC2 instances through block-level replication. The migration preserves critical application configurations and interdependencies, with IP address modifications being the primary change to the operational environment. This approach minimizes risk while ensuring continuity of the complex communication patterns visible in the architecture diagram.

For specialized components, the solution implements tailored migration strategies. The Delphix Engine migration follows a collaborative approach where AWS teams provision the necessary infrastructure (EC2 instances, security groups, EBS volumes) while leveraging Delphix's native replication capabilities to transfer data and re-provision Virtual Databases. Meanwhile, containerized workloads like WebUI and MelissaData services will transition from on-premises Rancher-managed Kubernetes clusters to Amazon EKS, integrating with AWS-native services for enhanced manageability, persistent storage, and observability.

The target architecture maintains existing connectivity patterns for customers through dedicated circuits and VPN connections, with AWS Direct Connect providing secure, high-bandwidth connectivity between environments. The Apache load balancer servers will preserve their multi-function configuration (supporting UI load balancing with session affinity and EDI load balancing with round-robin distribution on different ports), ensuring minimal disruption to customer integrations. This comprehensive approach allows HRP to benefit from AWS's reliable infrastructure while maintaining operational consistency and minimizing business disruption during the transition.

Architectural Components
========================

Below table describes the architectural component that makes up the to-be architecture diagram of Health Rules Payor (HRP).

|  |  |  |  |
| --- | --- | --- | --- |
| Ref# | Logical Component Name | Description | Details |
| 1 | Direct Connect | AWS Direct Connect establishes a private, consistent, high-bandwidth network connection between your on-premises network and AWS | 10 Gbps link from on-premises |
| 2 | AWS Region | Region for this application | us-east-1, us-west-2 |
| 3 | VPC | A virtual private cloud (VPC) is a secure, isolated private cloud hosted within a public cloud | Segregated based on environment (Need Confirmation from Network team) |
| 4 | Private Subnets | Private subnet used for Web, App & DB servers | Set up in all defined AWS Accounts as baseline |
| 5 | Amazon EC2 | All EC2 instances will be rehosted using CMF and AWS MGN outside of Delphix and clustered database servers. | This includes Answers, Connector, Load Balancer, Payor, PIK, and MQ |
| 6 | Amazon EKS | Amazon EKS is a managed service and certified Kubernetes conformant to run Kubernetes on AWS and on-premises. | EKS will be utilized for WebUI and Melissadata Micro Services. |
| 7 | Security Groups | Controls the traffic that is inbound and outbound for each Amazon EC2 instance | Will be deployed and utilized for all instances in a given account. |
| 8 | AWS Transfer Family | AWS Transfer Family is a managed file transfer service that enables secure file exchanges using industry standard protocols like SFTP, FTPS, FTP and AS2. | Will be deployed for MoveIT SFTP servers |
|  |  |  |  |