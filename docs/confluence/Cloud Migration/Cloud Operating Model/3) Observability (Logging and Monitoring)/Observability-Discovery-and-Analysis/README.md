# Observability-Discovery-and-Analysis

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5054398569/Observability-Discovery-and-Analysis

**Created by:** David Helmuth on August 28, 2025  
**Last modified by:** David Helmuth on September 12, 2025 at 02:37 PM

---

---

---

Overview
========

![image-20250828-154344.png](images/image-20250828-154344.png)

Workshop Logistics
------------------

### **Current State Meeting Date Time**: 07/23/2025 - 1:00 PM Eastern

### Meeting Recap: [Recap: AWS Migrations: Current State Workshop - Observability (Logging and Monitoring) July 23 | Meeting | Microsoft Teams](https://teams.microsoft.com/l/meetingrecap?driveId=b%21DB_OfQ-W_k6DoO-fS6Jw4YoE7vNKRg1Gun3YRU7wS_sYc6TQyp3_Q4FbkV6MJhPe&driveItemId=01FHYOWIXZ6BVENAQHGBC3NSO5JSFBNVWA&sitePath=https%3A%2F%2Fhealthedgetrial-my.sharepoint.com%2F%3Av%3A%2Fg%2Fpersonal%2Fdavid_helmuth_healthedge_com%2FEfnwakaCBzBFtsndTIoW1sABotC5Q6axAxxROOemoYtzKg&fileUrl=https%3A%2F%2Fhealthedgetrial-my.sharepoint.com%2Fpersonal%2Fdavid_helmuth_healthedge_com%2FDocuments%2FRecordings%2FAWS%2520Migrations%2520Current%2520State%2520Workshop%2520-%2520Observability%2520%28Logging%2520and%2520Monitoring%29-20250723_120454-Meeting%2520Recording.mp4%3Fweb%3D1&iCalUid=040000008200E00074C5B7101A82E0080000000065EAA228DCF5DB01000000000000000010000000BD20F2EDA046A643A193CDBBD6F08E39&threadId=19%3Ameeting_ZTQ4M2U3MGUtOGFlNi00OTE3LTg2OTgtM2MxZTE2NmQ0ZjRk%40thread.v2&organizerId=9a861b6c-a7c1-4635-82f7-eed113ca1cb5&tenantId=9c9d9fee-9dfb-4e27-b259-10369fa1acf2&callId=bf793bc8-45cd-4bbd-9a0a-746531131a70&threadType=meeting&meetingType=Scheduled&subType=RecapSharingLink_RecapCore)

HealthEdge Current State Summary
================================

Observability (Logging and Monitoring) capability at HealthEdge encompasses comprehensive monitoring and logging across multiple business units (HRP, WellFrame, Source, and Guiding Care), each with their own distinct approaches while sharing some common elements. The capability focuses on gaining actionable insights from infrastructure and application data, enabling proactive identification of issues before they impact customer experience. This includes monitoring of critical healthcare applications, infrastructure components, database performance, and security events, with an emphasis on maintaining high availability and meeting customer SLAs.

Policy
------

### Summary

The organization maintains strict uptime requirements (generally 99.9%) across all products, with some customers having more stringent requirements. Production environments are monitored 24/7, while non-production environments have limited monitoring. The approach is to identify the most restrictive customer commitment and use that as the standard for all operations, ensuring consistent service delivery across the customer base.

### Headlines

* Production environments are monitored 24/7, while non-production environments have limited monitoring
* Contractual SLA requirements vary by product:

  + HRP, WellFrame, Source, and Guiding Care: 99.9% uptime requirement
  + Some customers (especially Blues plans) have more restrictive requirements
  + Source has specific transaction processing requirements (under 400ms)
* Internal policy is to identify the most restrictive customer commitment and use that as the standard for all
* Main contractual obligations focus on uptime and transaction processing tracking

Process
-------

### Summary

A tiered monitoring approach is implemented where production environments receive 24/7 monitoring with immediate response for SEV1 issues, while non-production environments have more limited coverage. Daily health checks are performed (2:00 AM ET for production, 4:00 AM ET for non-production), with production issues taking priority. A robust incident management process includes RCA following the "never again" framework, ensuring lessons learned are implemented to prevent recurrence.

### Headlines

* Production Environment:

  + 24/7 monitoring with immediate response for SEV1 issues
  + Critical alerts routed through PagerDuty
  + Daily health checks run at 2:00 AM ET with issues resolved by 9:00 AM ET
  + Proactive Salesforce cases opened for production issues
  + RCA (Root Cause Analysis) process follows "never again" framework
* Non-Production Environment:

  + Limited monitoring (no SEV1)
  + Daily health checks run at 4:00 AM ET
  + Production issues take priority over non-prod issues
  + Email notifications for critical alerts

Tools
-----

### Summary

Each business unit employs different tool sets tailored to their needs, though some commonality exists. HRP uses AppDynamics, SolarWinds, and ELK Stack; WellFrame utilizes Open Telemetry and Datadog; Source relies on Azure Monitor and Application Insights; and Guiding Care uses Datadog. PagerDuty is used across all units for alert aggregation, while Grafana Enterprise serves as a common visualization layer for executive dashboards.

### Headlines

HRP:

* AppDynamics (application monitoring)
* SolarWinds (uptime and network monitoring)
* ELK Stack (application logs)
* PagerDuty (alert aggregation)
* Oracle OEM (database monitoring)
* Custom Azure monitoring tools

WellFrame:

* Open Telemetry
* Datadog
* PagerDuty
* Custom tool "Jordy" for Kafka stream monitoring

Source:

* Azure Monitor (comprehensive monitoring)
* Application Insights
* Azure Log Analytics
* PagerDuty

Guiding Care:

* Datadog
* PagerDuty

Cross-Organization:

* Grafana Enterprise (visualization layer for executive dashboards)

People
------

### Summary

The organizational structure varies by business unit. HRP maintains a dedicated Incident Management Team with clear delineation of responsibilities between infrastructure, application, and database teams. WellFrame follows a DevOps model where developers are responsible for their services. Source operates with a DevOps and SRE team structure, while Guiding Care utilizes an offshore NOC-style monitoring team. Each approach is tailored to the specific needs and operational model of the business unit.

### Headlines

HRP:

* Incident Management Team (owned by Todd Knight)
* Infrastructure team handles infrastructure alerts
* Application team handles application alerts
* Database team handles database alerts
* Incident Management team handles customer communication and RCA process

WellFrame:

* DevOps team manages core infrastructure monitoring
* Individual service teams responsible for their services
* Developers on call for their owned services
* Rotating RCA responsibility

Source:

* DevOps team receives initial alerts
* Site Reliability Engineering (SRE) team performs daily reviews
* Service owners and application teams engaged based on issue type

Guiding Care:

* Offshore monitoring team (NOC-style operation)
* Team posts alerts to Teams channels
* Ownership structure needs improvement according to recent SWAT team findings

AWS Operational Readiness State
===============================

| Template | DraftGreen | In Review | Baseline |
| --- | --- | --- | --- |

Summary
-------

The Operational Readiness State for HealthEdge's Observability (Logging and Monitoring) capability will be supported by AWS AMS's comprehensive monitoring approach.This includes leveraging AWS AMS's automated monitoring system with 150+ managed guardrails and security checks, along with compliance standards for infrastructure monitoring.[1](https://w.amazon.com/bin/view/AmazonWebServices/ManagedSupport/OperationsProcess/Observability/). The monitoring infrastructure utilizes AWS native tools like CloudWatch for metrics and logs, AWS Config for compliance monitoring, and GuardDuty for threat detection. A dedicated AWS AMS team, including a Cloud Services Delivery Manager and Operations team, provides 24/7 infrastructure support while HealthEdge teams focus on application-level monitoring.The system implements automated alert management through PagerDuty, conducts daily health checks, and follows NIST-based run books for incident management. [2](https://w.amazon.com/bin/view/Victoria/Projects/B2BInsightsMYP/OperationReadiness/). Monthly business reviews with the AMS Cloud Services Delivery Manager ensure continuous evaluation of operational performance, security, and cost optimization. [1](https://w.amazon.com/bin/view/AmazonWebServices/ManagedSupport/OperationsProcess/Observability/)

Policy Changes
--------------

* Implement 24/7 monitoring for production environments with immediate response for SEV1 issues, while maintaining limited monitoring for non-production environments
* Adopt AWS AMS's comprehensive monitoring approach that includes preventative and detective controls with 150+ managed guardrails and security checks
* Follow AWS AMS's compliance standards (PCI, SOC, FedRamp, ISO, HIPPA, CIS) for infrastructure monitoring

Process Changes
---------------

* Leverage AWS AMS's automated monitoring system that includes:

  + Alert aggregation and management through PagerDuty
  + Daily health checks with defined resolution timeframes
  + Incident management following NIST-based runbooks
  + Root Cause Analysis (RCA) process using "never again" framework
* Implement monthly business reviews with AMS Cloud Services Delivery Manager (CSDM) to review operational performance, security, and cost optimization

Tooling Changes
---------------

* Utilize AWS AMS's core monitoring tools:

  + CloudWatch for metrics, logs and alarms
  + AWS Config for compliance monitoring
  + GuardDuty for threat detection
  + AWS Backup for automated backups
* Implement AWS AMS Managed Monitoring Service (MMS) for:

  + Centralized alert management
  + Metric aggregation
  + Automated event handling
  + Integration with incident tracking systems

People/Org Changes
------------------

* Engage with dedicated AWS AMS teams:

  + Named Cloud Services Delivery Manager (CSDM) for operational oversight
  + Cloud Architect (CA) for technical guidance
  + AMS Operations team for 24/7 infrastructure support
* Maintain clear separation of responsibilities:

  + AWS AMS team handles infrastructure and OS-level monitoring
  + HealthEdge team focuses on application-level monitoring and custom requirements

Examples
--------

* Minimize change impact: Separate non production and production accounts, ideally for each major tier 1 application.
* ITSM / Change Tracking tool updated to support change requests for AWS resources.
* Approvers for changes identified and integrated with change request / tracking / notification. (e.g. database change approvers, infrastructure approvers, security change approvers)
* Gated review and approval process to deploy new AWS resources or change AWS resources in production environment
* Rollback process defined for each change applied to production. (Either manual or automated)
* Tests defined for each change applied to production. (Either manual or automated)
* Gated promotion process for new changes introduced into production. (Either via CI/CD or manually)
* Shared change calendar for each account that defines upcoming changes.
* Shared change calendar that defines upcoming changes for all accounts.
* Notification lists for each account and region to provide notification to all stakeholders of upcoming changes implemented as SNS topics.
* Automation runbooks defined for changes in Production (e.g. Stop Instance, Start Instance).
* Automation runbooks integrated with change calendar.
* Permissions to production account authorized and approved by security and management with MFA enabled for these identities.
* Validate least required privilege principle for all production account identities (including roles and credential keys used by automation, third parties, software).
* All configuration files for any standard platform and application software that will change on running instances, checked in and managed in version control.
* Release runbooks or CI/CD pipeline for all Tier 1 applications entering production.
* Defined catalog of standard AWS resources as infrastructure as code, managed in version control
* Published maintenance windows and notifications prior to maintenance windows for each account and region at a predetermined interval.