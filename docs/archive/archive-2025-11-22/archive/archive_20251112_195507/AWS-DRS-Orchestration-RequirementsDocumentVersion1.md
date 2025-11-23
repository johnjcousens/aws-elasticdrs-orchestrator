1. - AWS DRS Enterprise Orchestration and Automation Solution: Detailed Requirements

     **Version:** 1.4
     **Date:** November 8, 2025
     **Target Audience:** Development Team (Anthropic Claude, AWS Developers)

     This document outlines the detailed requirements for developing a comprehensive Disaster Recovery (DR) orchestration solution that leverages AWS Elastic Disaster Recovery (AWS DRS). The solution aims to achieve functional parity with VMware Site Recovery Manager (SRM) features (Protection Groups, Recovery Plans, detailed UI), utilizing modern, serverless AWS architecture, deployed via a single CloudFormation template.

     The reference architecture provided in the GitHub repository `aws-samples/drs-tools/drs-plan-automation` serves as the foundational approach for API interactions and general structure, but the requirements below introduce significant enhancements in UI features, data persistence, and deployment methodology.

     ------

     1. Project Goal

     The primary objective is to build a robust, observable, and automated DR management platform. This platform will enable users to define, execute, and monitor complex failover/failback procedures for multi-tier applications running on various source environments (on-prem, other clouds) into native AWS EC2 instances. The user experience must be a web-based, self-service interface that abstracts the underlying AWS complexity, similar to the operational simplicity of VMware SRM.

     2. Technology Stack & Architecture

     The solution must use the *latest* available versions of all specified AWS services and adhere to a serverless-first design principle.

     | Component                  | Technology/Service          | Role                                | Constraint                                           |
     | :------------------------- | :-------------------------- | :---------------------------------- | :--------------------------------------------------- |
     | **IaC**                    | AWS CloudFormation          | Full stack deployment/management    | Single Master Template (YAML), Nested Stacks allowed |
     | **Frontend**               | React SPA, S3, CloudFront   | User Interface Hosting/Delivery     | Modern React framework (latest version)              |
     | **API Backend**            | Amazon API Gateway (REST)   | Secure API Endpoint                 | REST API, Cognito Authorizers                        |
     | **Authentication**         | Amazon Cognito              | User Management/Auth                | User Pools & Identity Pools                          |
     | **Business Logic**         | AWS Lambda                  | Backend Processing, API Calls       | Python 3.12+ runtime, Boto3 SDK                      |
     | **Orchestration**          | AWS Step Functions          | Workflow Automation                 | Standard Workflows (for reliability/history)         |
     | **Configuration Data**     | Amazon DynamoDB             | Persistent Storage for Plans/Groups | Serverless NoSQL DB                                  |
     | **DR Service**             | AWS DRS                     | Replication & Instance Launch       | Core Service API Integration                         |
     | **In-Instance Automation** | AWS SSM Documents/Agent     | Post-launch scripting               | OS-agnostic scripts (Bash, PS, etc.)                 |
     | **Observability**          | CloudWatch Logs/Events, SNS | Monitoring & Notification           | Comprehensive logging required                       |

     3. Functional Requirements

     3.1 User Interface (UI) - SRM Parity Features

     The web-based UI is a critical component for ease of use and management, hosted as a Single Page Application (SPA) on S3/CloudFront.

     - **Authentication:** Must utilize the Amazon Cognito User Pool for secure user login.
     - **Protection Group Management View:**
       - An interface to list all discovered AWS DRS Source Servers.
       - Ability to select servers and assign them to a user-defined "Protection Group".
       - A server can belong to only one active Protection Group at a time, mirroring SRM behavior.
     - **Recovery Plan Builder View:**
       - An interface to create, edit, and save "Recovery Plans".
       - Plans define the sequence of execution using configured Protection Groups (e.g., Wave 1: DB Group, Wave 2: App Group).
       - The UI must allow configuration of dependency mapping (e.g., "Wait until EC2 instance 'DB-Prod-01' is running and healthy before launching 'Web-Prod-01'").
       - Allows configuration of wait times, manual approval steps (if possible via Step Functions/SNS integration), and specific SSM Document runs per group/server.
     - **Execution Status Dashboard:**
       - Provides a real-time, visual representation of an active Recovery Plan execution (similar to the SRM runbook view).
       - Clearly highlights current step, status (Running, Success, Failed), and associated logs.
       - Provides historical job execution logs.

     3.2 Backend API & Data Persistence

     A secure API layer handles all frontend requests and manages the application state.

     - **Amazon API Gateway:** Must expose secure REST endpoints (`/plans`, `/groups`, `/execute`, `/status`, etc.), authorized by Amazon Cognito.
     - **Python Lambda Functions:**
       - Handle data validation and persistence to Amazon DynamoDB.
       - Translate high-level "Recovery Plan" requests into specific AWS API calls (DRS API calls via Boto3, starting Step Functions executions).
       - Functions must follow Python 3.12+ best practices.
     - **Amazon DynamoDB:**
       - Stores `DRProtectionGroup` definitions (Group Name, Server IDs).
       - Stores `RecoveryPlan` definitions (Plan Name, Execution Order, Dependencies, Waves).
       - Stores historical execution metadata for fast dashboard loading.

     3.3 Orchestration and Automation Flow

     The core logic uses AWS Step Functions to manage the complex, multi-stage recovery process reliably.

     - **AWS Step Functions (Standard Workflow):**
       - The primary orchestrator launched by a backend Lambda function.
       - Input to the state machine will be the specific `RecoveryPlan` data fetched from DynamoDB.
       - The state machine logic must implement the wave sequencing and dependency checks defined in the plan.
       - Includes robust error handling, automated retries, and failure notifications.
     - **AWS DRS Integration:** Lambda functions within the Step Functions workflow will initiate `StartRecovery` API calls for specific Source Server IDs extracted from the plan data.
     - **Post-Launch Actions (SSM Documents):**
       - AWS DRS's built-in "Post-launch actions" will be enabled and pre-configured via CloudFormation templates.
       - SSM Documents must be created and included in the deployment package.
       - Scripts within these documents can use *any* language available on the source OS (Bash, PowerShell, Python, custom binaries) and are designed to run configuration and health checks *within* the recovered instance.

     3.4 Triggering and Management

     - **Web UI Trigger:** Primary method of interaction (via API Gateway -> Lambda -> Step Functions).
     - **SSM Automation Secondary Trigger:** An SSM Automation Runbook must be included in the CloudFormation deployment package that allows triggering the Step Functions execution via AWS CLI or other automation tools, providing operational flexibility.
     - Deployment and Infrastructure (IaC)

     Deployment must prioritize simplicity for the end-user/customer.

     - **Single Master CloudFormation Template:** All AWS resources are defined within a single, deployable YAML CloudFormation template.
     - **Nested Stacks:** The master template will deploy nested stacks (e.g., `FrontendStack`, `BackendAPILambdaStack`, `DRSOrchestrationStack`) to organize resources logically.
     - **Clean Deployment/Deletion:** The template should facilitate a single-click deployment and, importantly, a single-click deletion of all components. *Note:* If the S3 bucket is not empty upon deletion, CloudFormation will fail; this must be handled either by a custom resource to empty the bucket or clearly documented for the user.
     - **Latest Versions:** Ensure all IAM roles and policies follow the principle of least privilege and use the latest supported AWS managed policy versions or defined inline policies.

Comparison: AWS DRS Custom Solution vs. VMware Site Recovery Manager 8.8

| Feature              | VMware Site Recovery Manager (SRM) 8.8                       | AWS DRS Custom Solution (Proposed)                           |
| :------------------- | :----------------------------------------------------------- | :----------------------------------------------------------- |
| **Primary Use Case** | Orchestrated DR for VMware environments (on-prem to on-prem, or to VMware Cloud on AWS/Azure). | DR for diverse environments (physical, virtual, other clouds) into native AWS EC2. |
| **UI**               | Integrated HTML5 vCenter web client interface ("Clarity UI"). | Custom, modern web UI (React SPA) hosted on S3/CloudFront, integrated with API Gateway [3.1, 3.2]. |
| **Orchestration**    | Built-in "Recovery Plans" with predefined steps, priority tiers, and VM dependencies managed via the UI. | Highly customizable workflow defined in AWS Step Functions, allowing complex branching logic, retries, and explicit sequencing (wave-based recovery) [3.2, 3.2]. |
| **Automation**       | PowerCLI (PowerShell module), REST API, and VMware Aria Automation Orchestrator plug-in for external scripting/automation. | AWS Lambda (Python) for control plane API calls and OS-agnostic SSM Documents for in-instance automation [3.2, 3.4]. |
| **Grouping**         | Uses "Protection Groups" (groups of VMs, datastores) which are then assigned to recovery plans. A VM can only be in one Protection Group. | Uses native AWS tagging and API filters to group source servers dynamically, providing more flexible grouping logic within custom Lambda functions. |
| **Testing**          | Non-disruptive testing using isolated test networks, a key built-in feature. | Non-disruptive testing capabilities are inherent to AWS DRS, with the custom solution orchestrating the launch of recovery instances in an isolated VPC for testing. |
| **Deployment**       | Appliance-based deployment, involving installation and configuration of SRM and vSphere Replication appliances and software at both sites. | Fully automated deployment via a single AWS CloudFormation master template (using nested stacks), providing ease of deployment and cleanup [4.1, 4.1]. |
| **Failback**         | Integrated "Reprotect" and "Recovery" wizards within the UI. | Automated through the DRS Mass Failback Automation client (DRSFA) or orchestrated via custom Step Functions/SSM Automation for increased control. |



VMware Site Recovery Manager References:

https://techdocs.broadcom.com/us/en/vmware-cis/live-recovery/site-recovery-manager/8-8.html

https://techdocs.broadcom.com/us/en/vmware-cis/live-recovery/site-recovery-manager/8-8/site-recovery-manager-installation-and-configuration-8-8.html

https://techdocs.broadcom.com/us/en/vmware-cis/live-recovery/site-recovery-manager/8-8/site-recovery-manager-api-developer-s-guide-8-8.html

https://github.com/vmware-samples/site-recovery-manager-rest-api-examples/tree/8481ff31987971a7466509edec8b95fb16b5aa8e

https://developer.broadcom.com/xapis/srm-appliance-config-api/latest/

https://www.vmware.com/docs/vmware-site-recovery-technical-overview

https://learn.microsoft.com/en-us/azure/azure-vmware/disaster-recovery-using-vmware-site-recovery-manager

