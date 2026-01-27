# MRF Target Architecture

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5373853705/MRF%20Target%20Architecture

**Created by:** Sreenivas Algoti on December 19, 2025  
**Last modified by:** Sreenivas Algoti on January 12, 2026 at 12:49 AM

---

1. MRF Solution Architecture - Target State (Proposed)
======================================================

![HealthEdge_PDM_Migration-MRF_Logical.drawio-20260108-205313.png](images/HealthEdge_PDM_Migration-MRF_Logical.drawio-20260108-205313.png)

2. MRF Physical Architecture - Target State (Proposed)
======================================================

![HealthEdge_PDM_Migration-MRF_Physical.drawio-20260108-214833.png](images/HealthEdge_PDM_Migration-MRF_Physical.drawio-20260108-214833.png)

3. Architectural Components
===========================

| **Component/Service Name** | **Description** | **Comments** |
| --- | --- | --- |
| EKS | Managed Kubernetes service that runs containerized applications with automatic scaling and high availability |  |
| EC2 | Virtual servers (instances) in the cloud providing scalable compute capacity for various workloads |  |
| Amazon S3 | Scalable object storage service for storing and retrieving any amount of data from anywhere. |  |
| Amazon DocumentDB | Fully managed, MongoDB-compatible document database service designed for storing, querying, and indexing JSON data at scale. |  |
| Amazon Simple Notification Service (SNS) | Pub/Sub messaging service for sending notifications to distributed systems, microservices, and end users. |  |
| Amazon Simple Queue Service (SQS) | Fully managed message queuing service for decoupling and scaling distributed systems and microservices. |  |
| Amazon Elastic Container Registry (ECR) | Fully managed Docker container registry for storing, managing, and deploying container images. |  |
| AWS WAF | Web Application Firewall that protects applications from common web exploits, bots, and malicious traffic. |  |
| AWS Secrets Manager | Service for securely storing, rotating, and managing access to secrets like database credentials and API keys. |  |
| AWS Key Management Service (AWS KMS) | Managed service for creating and controlling cryptographic keys used to encrypt your data. |  |
| Parameter Store (AWS AWS Systems Manager Parameter Store) | Secure hierarchical storage for configuration data, plain text, or encrypted secrets. |  |
| Amazon CloudWatch | Monitoring and observability service for collecting metrics, logs, and events from AWS resources and applications. |  |
| Private ALB | Internal Application Load Balancer that routes HTTP/HTTPS traffic between services within a VPC without internet exposure. |  |
| Internet Gateway | VPC component enabling bidirectional communication between VPC resources and the internet. |  |
| NAT Gateway | Managed service allowing private subnet resources to access the internet while preventing inbound connections. |  |
| Transit Gateway | Central hub connecting multiple VPCs, on-premises networks, and VPNs through a single gateway. |  |
| VPC Endpoint | Private connection enabling VPC resources to access AWS services without traversing the public internet. |  |
| Public Subnet | Subnet with a route table entry directing traffic to an Internet Gateway for public internet access. |  |
| Private Subnet | Subnet without direct internet access, typically routing outbound traffic through a NAT Gateway. |  |
| AWS Site-to-Site VPN | Encrypted IPsec VPN connection between your on-premises network and your AWS VPC over the public internet. |  |
| AWS Virtual Private Gateway | VPN concentrator on the AWS side of a Site-to-Site VPN connection that attaches to your VPC. |  |
| Customer Gateway | Resource representing your on-premises VPN device or software application in your AWS configuration. |  |