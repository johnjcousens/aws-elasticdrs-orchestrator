# Incident and Problem Management-Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866998924/Incident%20and%20Problem%20Management-Design

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** David Helmuth on September 12, 2025 at 02:42 PM

---

Event and Incident Management enable enterprises to control and restore cloud services. The focus of event management is to detect events, assess their potential impact, and determine the appropriate control action.  Incident Management restores normal service operation as quickly as possible and minimizes the adverse impact upon business operations, thus ensuring that the best possible levels of service quality and availability are maintained.

Event Management
================

| **AWS Recommended Cloud Approach** |
| --- |
| **Event Management** Event Management aids in understanding what is happening with a service right now. It provides a way of comparing actual performance and behavior against design standards and organizational SLA's.   * Provides the ability to detect, interpret and initiate appropriate action for events. * Basis for operational monitoring and control and entry point for many service operation activities. * Provides operational information, as well as warnings and exceptions, to aid automation. * Supports continual service improvement activities of service assurance and reporting and service improvement.  image2019-6-23_10-54-1.pngimage2019-6-23_10-54-58.png |

---

| **Operational Readiness State** |
| --- |
| For the Operational Readiness State, the customer should have logging and monitoring standards and capabilities for all workloads entering product.  At a minimum, operating system metrics and alarms should be configured for standard metrics such as CPU Utilization, Memory Utilization, and % Disk Space free.  Additional alarms should be identified and configured by the application / workload owners.  Notifications for alarms should be configured to notify the application teams and any central cloud operations teams.  Alarms should be simulated and tested.  At a minimum, operating system logs should be captured and available for troubleshooting and analysis.  Additional logs should be identified and configured by the application / workload owners.  Logs should be accessible by application teams, central operations, and support.  Refer to the Logging and Monitoring section for more details.  Refer to [Designing and Implementing logging and monitoring with Amazon CloudWatch AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/implementing-logging-monitoring-cloudwatch/welcome.html) to support your design and implementation.  Game day scenarios should be defined and run with all stakeholders for workloads entering production.  Any issues identified during the game day should be documented and addressed prior to production go live.  AWS recommends that the use of [AWS Health](https://docs.aws.amazon.com/health/latest/ug/what-is-aws-health.html)  for ongoing visibility into AWS resource performance and the availability of your AWS services and accounts.  At a minimum, \[Customer\] should have visibility of AWS health events with automated notification using communication channels that provide sufficient and timely visibility.  Game day scenarios should be considered to prepare for AWS service related health events and runbooks should be defined to sufficiently respond to them.  AWS support provides the  [aws-health-tools](https://github.com/aws/aws-health-tools)  repository to help you implement notification and automation for AWS Health related events. |

---

| **Recommendations for Future Enhancements** |
| --- |
| For a Future State, an iterative event management process should be established through:   * Establishing an event store pattern * Establishing and integrating event management process to \[Customer\]'s upcoming ServiceNow platform * Finally integrating event management with other ITSM process such as Incident and Change Management |

---

Incident and Problem Management/Operations Support Tiers
========================================================

| **AWS Recommended Cloud Approach** |
| --- |
| **Incident Management** Operating models for cloud solutions generally requires minimal change to current incident management procedures. If customers utilize cloud-native tools, such as AWS CloudWatch, for monitoring, then these tools need to be integrated into the incident management process. As the enterprise matures its cloud operation processes, incident management will need to be integrated to other ITSM processes and tooling such as event, change and configuration (CMDB) management.  image2019-6-23_11-24-32.png   **Problem Management** The fundamental approach to problem management does not change within the AWS environment. AWS itself has a systematic approach to root cause analysis that is built on the foundational elements of problem management.  image2019-6-23_11-25-15.png   One distinguishing feature of problem management within a cloud environment is the ability to view and aggregate large volumes of data, using AWS tools such as Kinesis to provide more comprehensive and timely views on the environment.  **Operations Support Tiers** An escalation path to AWS would be incorporated to help troubleshoot incidents that utilize AWS services. Below are the AWS Support Plans with suggestions on aligning to customer organization's use case.   * Production use of AWS. Businesses looking for guidance and best practices to enable availability, scalability, and security of production workloads -reducing the need for reactive support.    + Recommended Plan: **Business Support**  * Business Critical use of AWS. Businesses whose success is directly linked with the performance of workloads and applications, benefiting from high-touch, proactive/preventive service.    + Recommended Plan: **Enterprise Support**   As workloads migrate to the cloud, application and infrastructure teams need to provide operations transitional procedures that include escalation paths for cloud services. |

---

| **Operational Readiness State** |
| --- |
| **Incident and Problem Management** For Operational Readiness State of application/infrastructure workloads on AWS, \[Customer\] will utilize their existing Incident process. These processes are initiated and tracked via <Insert Customer's ISTM tool>. **To demonstrate the incident management process in the Operational Readiness State, \[Customer\] will provide Infrastructure Architecture, Application Delivery and Operations teams an ITWRS** **(Remedy) queue and instruction on how to use the queue.** **Operations Support Tiers** For Operational Readiness State, \[Customer\] will continue to follow current Operations Support Tiers for cloud services. The following figure illustrates \[Customer\]'s Operational Readiness State application support tiers.  \[Insert Operations Tiers Here\] ***\[Customer\] Operational Readiness State  Operation Support Tiers Example***  **\[Customer\]** **Operations Contact Information**   * **Production Center of Excellence**: (XXX) XXX-XXXX; \[Insert Email and website links\] * **Application Delivery Teams**: \[Insert Contact Information\] * **Infrastructure Architecture**: \[Insert Contact Information\] * **AWS -** ***Enterprise Support*****: AWS Management Console for dedicated TAM –** [**aws.amazon.com**](http://aws.amazon.com)    + **\[Customer\] Enterprise Support Team email address: \[aws-\[Customer\]-team@**[**amazon.com**](http://amazon.com)**\]**   **The following table describes the AWS Support response times:** image2019-6-23_11-31-6.png |

---

| **Recommendations for Future Enhancements** |
| --- |
| **Incident and Problem Management** As noted, AWS provides customers with the ability to rapidly aggregate large volumes of data. Whether this is done using AWS capabilities, or a commercial tool such as Splunk, systematic reviews of the operational environment for trends, or outliers should be used to trigger the incident and problem management process.    \[Customer\] should also establish a problem management process in the Future State to evaluate root causes and proactively resolve issues.    Additionally, AWS recommends that \[Customer\]'s Cloud Center of Excellence evaluate how incidents may change for cloud services if an ITSM, like ServiceNow, is being used. **Operations Support Tiers** As \[Customer\] migrates more workloads to the AWS platform and cloud operations matures, the support tiers for cloud services may need to change. AWS recommends a review of the current support tiers after two waves of applications migrate to the AWS platform. |

---

Logging and Monitoring
======================

| **AWS Recommended Cloud Approach** |
| --- |
| Creating a logging and monitoring solution designed for the AWS Cloud is integral for achieving the [six advantages of cloud computing](https://docs.aws.amazon.com/whitepapers/latest/aws-overview/six-advantages-of-cloud-computing.html). Your logging and monitoring solution should help your IT organization achieve business outcomes that benefit your business processes, business partners, employees, and customers.  Implementing a logging and monitoring solution that provides support for Amazon EC2 and AWS services can be achieved by implementing Amazon CloudWatch and is the recommended approach for baseline operational readiness.  Refer to [Designing and Implementing logging and monitoring with Amazon CloudWatch AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/implementing-logging-monitoring-cloudwatch/welcome.html) to support your design and implementation.   **Logging** ***Platform (infrastructure) Logging*** Organizations building or migrating applications in the cloud have an opportunity to design centralized platform logging as part of the initial architecture. This brings new insight into the health of a given environment and reduces incident resolution times and drive improvements to the solution. Below are the options available to support a platform logging solution in the cloud. Enabling logging where available to monitor your workloads in all tiers to detect failure is a Well-Architected best practice.   * Amazon CloudWatch is a logging and monitoring service. CloudWatch tracks metrics, monitors log files, sets alarms and reacts to changes in your AWS resources. Amazon CloudWatch is used to gain system-wide visibility into resource utilization, application performance, and operational health * Amazon CloudWatch logs can be consumed by your existing log aggregate tool. * AWS Marketplace and the open source community offer a variety of solutions for centralized logging and analytics   AWS CloudTrail is a web service that records activity made on your account and delivers log files to your Amazon S3 bucket. Activity information for services with regional end points (EC2, RDS etc.) is captured and processed in the same region as to which the action is made and delivered to the region associated with your Amazon S3 bucket. Action information for services with single end points (IAM, STS, etc.) is captured in the region where the end point is located, processed in the region where the CloudTrail trail is configured and delivered to the region associated with your Amazon S3 bucket. **Application Logging** Organizations building new applications in the cloud have an opportunity to design centralized application logging as part of the initial application architecture. This brings new insight into the health of an application that can reduce incident resolution times and drive improvements to the application. Identifying key performance indicators based on desired business and customer outcomes, and defining workload metrics, and baselines for workload metrics, to measure the health of the workload and its individual components aligns to Well-Architected best practices. Evaluate metrics to determine if the workload is achieving desired outcomes including the achievement of KPIs, and to understand the health of the workload. Below are the options available to support an application logging solution in the cloud.   * New applications being designed for the cloud often utilize centralized logging. AWS offers Amazon CloudWatch logs to provide centralized logging and analytics. * AWS Marketplace and the open source community offer a variety of solutions for centralized logging and analytics   Existing applications that have been migrated to the cloud can also take advantage of centralized logging, but may require minor refactoring by inserting additional API calls into the code base. **Monitoring** Monitoring is key to successful operations support. Monitoring is not only for events, incidents, and problems in the environment but for viewing spikes and patterns needed for largely automated applications. *Why cloud monitoring is different*   * Resources are elastic and ephemeral * Infrastructure can be tightly coupled to events (i.e., scale-in, scale-out, replace instance) * All changes can be tracked * All access can be tracked     **Application Telemetry Resources** **Event Monitoring** Most organizations initially maintain their existing event monitoring solution and incident management processes to avoid friction in cloud adoption. However, as your adoption extends and matures, organizations select a blend of monitoring and incident management options from the list outlined below: Options:   * Maintain current monitoring solution and incident management processes for Amazon EC2 instances * A hybrid of existing monitoring solutions and AWS monitoring service (e.g. Amazon CloudWatch), as well as AWS Partner monitoring solutions. * When using Amazon EC2 Auto Scaling consider a monitoring solution that is aware of scale out and scale in events. * Most AWS services outside of Amazon EC2 require a cloud aware event monitoring solution.  Amazon CloudWatch provides native, automatic support for monitoring AWS services. * Use Amazon CloudWatch for all event monitoring to gain system-wide visibility into resource utilization, application performance, and operational health using a combination of built-in metrics as well as custom metrics generated by your application.  image2019-6-23_11-38-31.png Implementing application telemetry aligns to Well-Architected Operational Excellence best practices. Instrument your application code to emit information about its internal state, status, and achievement of business outcomes. For example, queue depth, error messages, and response times. Use this information to determine when a response is required.  **Resources for implementing log and metric telemetry to determine when a response is required:**   * [Gaining better observability of your VMs with Amazon CloudWatch - AWS Online Tech Talks](https://www.youtube.com/watch?v=1Ck_me4azMw&feature=youtu.be&ref=wellarchitected) * [How Amazon CloudWatch works](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_architecture.html?ref=wellarchitected) * [What is Amazon CloudWatch?](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html?ref=wellarchitected) * [Using CloudWatch metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/working_with_metrics.html?ref=wellarchitected) * [What is Amazon CloudWatch Logs?](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html?ref=wellarchitected)   **Resources for implementing application telemetry (emitting information about queue depth, error messages, and response times):**   * [Collect metrics and logs from Amazon EC2 Instances and on-premises servers with the CloudWatch Agent](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Install-CloudWatch-Agent.html?ref=wellarchitected) * [Using CloudWatch Logs with container instances](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using_cloudwatch_logs.html?ref=wellarchitected) * [Accessing Amazon CloudWatch Logs for AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-functions-logs.html?ref=wellarchitected) * [Publish custom metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html?ref=wellarchitected)   **Resources for implementing and confirguring workload telemetry (API call volume, HTTP status codes, and scaling events)**   * [Amazon CloudWatch metrics and dimensions reference](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CW_Support_For_AWS.html?ref=wellarchitected) * [AWS CloudTrail](https://aws.amazon.com/cloudtrail/?ref=wellarchitected) * [What Is AWS CloudTrail?](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html?ref=wellarchitected) * [VPC flow logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html?ref=wellarchitected) |

---

| **Operational Readiness State** |
| --- |
| **Log Management** ***Platform (Infrastructure) and Application Logging*** \[Customer\] will use CloudWatch for monitoring AWS services. The Application Delivery and Operations teams are responsible for identifying and implementing specific monitors based on their customer requirements and application knowledge.  **For Operational Readiness State, the first wave of migrated applications delivery teams (Insert Customer applications) as well as the Operations team will demonstrate the ability to access and review monitoring and logging in CloudWatch.**  This approach has the immediate benefit of providing insight into the infrastructure, which may not have been previously available or utilized. This allows \[Customer\] to right-size the infrastructure as well as understand relationships across the environment, potentially reducing response and recovery time. **Monitoring** Application workloads will use SCOM to determine the health of the application and related services. Learning expected patterns of activity for a workload, and performing regular proactive reviews of metrics to identify trends and determine where appropriate responses are needed follows Well-Architected best practices. For Operational Readiness State, there is no plan to change, modify or otherwise aggregate these event monitors.  As a part of Operational Readiness State, \[Customer\] will install the SCOM agent, **\[Insert URL\]** and begin to use the basic monitors established by the Infrastructure Architecture Team. Lacking any other information or guidance, the minimum monitors are shown in the table below.  **For Operational Readiness State, the Infrastructure Architecture Team, will provide the Application Delivery Teams and Operations Team's requested alerting via defined method (email, text and/or other method)**  As guidance, alerting when workload outcomes are at risk and when workload anomalies are detected so that teams can respond appropriately if required are Well-Architected best practices. Validating the achievement of outcomes and effectiveness of KPIs and metrics can be accomplished through a business level view of your workload operations. The following resources are useful for creating alerts and dashboards: [What is Amazon CloudWatch Events?](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/WhatIsCloudWatchEvents.html?ref=wellarchitected), [Creating Amazon CloudWatch alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html?ref=wellarchitected), [Invoking Lambda functions using Amazon SNS notifications](https://docs.aws.amazon.com/sns/latest/dg/sns-lambda.html?ref=wellarchitected), [Using Amazon CloudWatch dashboards](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Dashboards.html?ref=wellarchitected), [What is log analytics?](https://aws.amazon.com/log-analytics/?ref=wellarchitected) |



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table ac:local-id="0036d919-41e8-4712-b2ee-aee4f27fbeda" data-layout="default" data-table-width="1800"><tbody><tr><th colspan="4"><h4><strong><span>Basic Infrastructure Monitors</span></strong></h4></th></tr><tr><td rowspan="2"><strong><span>Logical Disk Free Space System Drive</span></strong>

<br/>
</td><td><span>Lower Threshold</span>
</td><td><span>5%</span>
</td><td><span>300 MB</span>
</td></tr><tr><td><span>Higher threshold</span>
</td><td><span>10%</span>
</td><td><span>500 MB</span>
</td></tr><tr><td rowspan="2"><strong><span>Logical Disk Free Space Non-System Drive</span></strong>

<br/>
</td><td><span>Lower Threshold</span>
</td><td><span>5%</span>
</td><td><span>1000 MB</span>
</td></tr><tr><td><span>Higher threshold</span>
</td><td><span>10%</span>
</td><td><span>2000 MB</span>
</td></tr><tr><td rowspan="2"><strong><span>Total CPU Utilization Percentage</span></strong>

<br/>
</td><td><span>CPU Utilization Threshold</span>
</td><td><span>95%</span>
</td><td><span>3 Samples (15 Min)</span>
</td></tr><tr><td><span>CPU Queue Threshold</span>
</td><td><span>15</span>
</td><td><span>2 Samples (15 Min)</span>
</td></tr><tr><td><strong><span>Available Megabytes of Memory</span></strong>
</td><td>
<br/>
</td><td><span>100 MB</span>
</td><td><span>3 Samples (15 Min)</span>
</td></tr><tr><td><strong><span>Failed to Connect to Computer (Availability)</span></strong>
</td><td><span>IF SCOM Agent on the server is stopped</span>
</td><td><span>TBD</span>
</td><td><span>Server out not pinging</span>
</td></tr></tbody></table>



---

| **Recommendations for Future Enhancements** |
| --- |
| It's recommended that the \[Customer\] review Amazon Prescriptive Guidance for [Designing and implementing logging and monitoring with Amazon CloudWatch](https://docs.aws.amazon.com/prescriptive-guidance/latest/implementing-logging-monitoring-cloudwatch/welcome.html) to consider additional logging and monitoring capabilities. Customer can consider automating their logging and monitoring configuration using the examples in [this github repository](https://github.com/aws-samples/logging-monitoring-apg-guide-examples). |

**Attachments:**

[image2019-6-23\_10-53-25.png](../../attachments/image2019-6-23_10-53-25.png)

[image2019-6-23\_10-54-1.png](../../attachments/image2019-6-23_10-54-1.png)

[image2019-6-23\_10-54-58.png](../../attachments/image2019-6-23_10-54-58.png)

[image2019-6-23\_11-24-32.png](../../attachments/image2019-6-23_11-24-32.png)

[image2019-6-23\_11-25-15.png](../../attachments/image2019-6-23_11-25-15.png)

[image2019-6-23\_11-31-6.png](../../attachments/image2019-6-23_11-31-6.png)

[image2019-6-23\_11-38-31.png](../../attachments/image2019-6-23_11-38-31.png)