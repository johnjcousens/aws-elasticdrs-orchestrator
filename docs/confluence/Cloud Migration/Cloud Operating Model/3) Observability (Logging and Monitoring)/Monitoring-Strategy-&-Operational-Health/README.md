# Monitoring-Strategy-&-Operational-Health

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866051040/Monitoring-Strategy-%26-Operational-Health

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:03 AM

---

[Building & Implementing a Robust Monitoring Strategy Virtual Workshop Recording](https://www.youtube.com/watch?v=Mj-5oqUYKD8)

Operational Health
------------------

It is important to define, capture, and analyze operations metrics to gain visibility to operations
events so that you can take appropriate action. The following best practices from the [Operational Excellence pillar of the AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html) will help you understand the health of your operations.  Specifically, the goal is [understanding workload health](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/understanding-workload-health.html) for systems and applications in AWS.

**Identify key** [**performance**](https://wa.aws.amazon.com/wat.pillar.performance.en.html) **indicators**: Identify key [performance](https://wa.aws.amazon.com/wat.pillar.performance.en.html) indicators (KPIs) based on desired business and customer outcomes. Evaluate KPIs to determine [operations](https://wa.aws.amazon.com/wat.pillar.operationalExcellence.en.html) success.  Some examples of Key performance indicators are: orders processed, transaction volume, deliveries, and executions completed.

**Define** [**operations**](https://wa.aws.amazon.com/wat.pillar.operationalExcellence.en.html) **metrics**: Define [operations](https://wa.aws.amazon.com/wat.pillar.operationalExcellence.en.html) metrics to measure the achievement of KPIs. Define [operations](https://wa.aws.amazon.com/wat.pillar.operationalExcellence.en.html) metrics to measure the health of the [operations](https://wa.aws.amazon.com/wat.pillar.operationalExcellence.en.html). Evaluate metrics to determine if the [operations](https://wa.aws.amazon.com/wat.pillar.operationalExcellence.en.html) are achieving desired outcomes, and to understand the health of operations.

Resources:

* [Publish custom metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html?ref=wellarchitected)
* [Searching and filtering log data](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html?ref=wellarchitected)
* [Amazon CloudWatch metrics and dimensions reference](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CW_Support_For_AWS.html?ref=wellarchitected)

**Collect and analyze** [**operations**](https://wa.aws.amazon.com/wat.pillar.operationalExcellence.en.html) **metrics**: Perform regular proactive reviews of metrics to identify trends and determine where appropriate responses are needed.  
Resources:

* [Using Amazon CloudWatch metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/working_with_metrics.html?ref=wellarchitected)
* [Amazon CloudWatch metrics and dimensions reference](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CW_Support_For_AWS.html?ref=wellarchitected)
* [Collect metrics and logs from Amazon EC2 instances and on-premises servers with the CloudWatch Agent](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Install-CloudWatch-Agent.html?ref=wellarchitected)

**Establish** [**operations**](https://wa.aws.amazon.com/wat.pillar.operationalExcellence.en.html) **metrics baselines**: Establish baselines for metrics to provide expected values as the basis for comparison and identification of under and over performing processes.

* [Creating Amazon CloudWatch alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html?ref=wellarchitected)

**Learn the expected patterns of activity for** [**operations**](https://wa.aws.amazon.com/wat.pillar.operationalExcellence.en.html): Establish baselines for metrics to provide expected values as the basis for comparison.

**Alert when** [**operations**](https://wa.aws.amazon.com/wat.pillar.operationalExcellence.en.html) **outcomes are at risk**: Raise an alert when [operations](https://wa.aws.amazon.com/wat.pillar.operationalExcellence.en.html) outcomes are at risk so that you can respond appropriately if required.  
**Alert when** [**operations**](https://wa.aws.amazon.com/wat.pillar.operationalExcellence.en.html) **anomalies are detected**: Raise an alert when [operations](https://wa.aws.amazon.com/wat.pillar.operationalExcellence.en.html) anomalies are detected so that you can respond appropriately if required.

* [What is Amazon CloudWatch Events?](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/WhatIsCloudWatchEvents.html?ref=wellarchitected)
* [Creating Amazon CloudWatch alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html?ref=wellarchitected)
* [Invoking Lambda functions using Amazon SNS notifications](https://docs.aws.amazon.com/sns/latest/dg/sns-lambda.html?ref=wellarchitected)

**Validate the achievement of outcomes and the effectiveness of KPIs and metrics** : Create a business-level view of your [operations](https://wa.aws.amazon.com/wat.pillar.operationalExcellence.en.html) activities to help you determine if you are satisfying needs and to identify areas that need improvement to reach business goals. Validate the effectiveness of KPIs and metrics and revise them if necessary.

Cost Optimization
-----------------

To align to the [Cost Optimization pillar of the Well-Architected framework](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html), establish policies and mechanisms to ensure that appropriate costs are incurred while objectives are achieved. By employing a checks-and-balances approach, you can innovate without overspending. The following best practices will help you achieve this:

**Govern Usage**: Develop policies that define how resources are managed by your organization. Policies should cover cost aspects of resources and workloads, including creation, modification and decommission over the resource lifetime. Workloads and accounts have different objectives and attributes; ensure your goals reflect this. Development or test environments should have higher levels of elasticity than production. Production environments should have higher levels of reserved capacity. Workloads should become more efficient over time; ensure goals reflect this. Implementing a structure of accounts that maps to your organization will assist in allocating and managing costs throughout your organization. Implement groups and roles that align to your policies and control who can create, modify, or decommission instances and resources in each group; for example, development, test, and production groups. This applies to AWS services and third-party solutions. Implement controls based on organization policies and defined groups and roles. These ensure that costs are only incurred as defined by organization requirements; for example, control access to regions or resource types with IAM policies.

**Monitor usage and cost:** Configure the AWS Cost and Usage Report to capture detailed usage and billing information. Identify organization categories that could be used to allocate cost within your organization. Establish the organization metrics that are required for this workload. Example metrics of a workload are customer reports produced or web pages served to customers. Configure AWS Cost Explorer and AWS Budgets inline with your organization policies.

**Consider how you evaluate cost when you select a service:**Ensure every workload component is analyzed, regardless of current size or current costs. Review effort should reflect potential benefit, such as current and projected costs. Look at overall cost to the organization of each component. Look at total cost of ownership by factoring in cost of operations and management, especially when using managed services. Review effort should reflect potential benefit; for example, time spent analyzing is proportional to component cost. It is best practice to perform cost analysis for different usage over time. Workloads can change over time, and some services or features are more cost effective at different usage levels. By performing the analysis on each component over time and at projected usage, you ensure this workload remains cost effective over its lifetime.

**Appropriate resource type and size selection:** It is best practice to perform cost modeling. Identify organization requirements and perform cost modeling of the workload and each of its components. Perform benchmark activities for the workload under different predicted loads and compare the costs. The modeling effort should reflect potential benefit; for example, time spent is proportional to component cost.  Estimate resource size or type based on workload and resource characteristics; for example, compute, memory, throughput, or write intensive. This estimate is typically made using a previous version of the workload (such as an on-premises version), using documentation, or using other sources of information about the workload.

**Use pricing models to reduce cost:**  Perform an analysis on the workload using the Reserved Instance Recommendations feature in AWS Cost Explorer.

**Attachments:**