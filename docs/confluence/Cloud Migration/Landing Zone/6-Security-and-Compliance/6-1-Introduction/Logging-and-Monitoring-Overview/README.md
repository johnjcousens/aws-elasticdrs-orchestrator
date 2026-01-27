# Logging-and-Monitoring-Overview

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867033939/Logging-and-Monitoring-Overview

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:33 AM

---

Monitoring is an important part of maintaining the reliability, availability, and performance of AWS Identity and Access Management (IAM), AWS Security Token Service (AWS STS) and your other AWS solutions. AWS provides several tools for monitoring your AWS resources and responding to potential incidents:

* *AWS CloudTrail* captures all API calls for IAM and AWS STS as events, including calls from the console and API calls. To learn more about using CloudTrail with IAM and AWS STS, see [**Logging IAM and AWS STS API calls with AWS CloudTrail**](https://docs.aws.amazon.com/IAM/latest/UserGuide/cloudtrail-integration.html). For more information about CloudTrail, see the [**AWS CloudTrail User Guide**](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/).
* *AWS Identity and Access Management Access Analyzer* helps you identify the resources in your organization and accounts, such as Amazon S3 buckets or IAM roles, that are shared with an external entity. This helps you identify unintended access to your resources and data, which is a security risk. To learn more, see [**What is IAM Access Analyzer?**](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html)
* *Amazon CloudWatch* monitors your AWS resources and the applications that you run on AWS in real time. You can collect and track metrics, create customized dashboards, and set alarms that notify you or take actions when a specified metric reaches a threshold that you specify. For example, you can have CloudWatch track CPU usage or other metrics of your Amazon EC2 instances and automatically launch new instances when needed. For more information, see the [**Amazon CloudWatch User Guide**](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/)**.**
* *Amazon CloudWatch Logs* helps you monitor, store, and access your log files from Amazon EC2 instances, CloudTrail, and other sources. CloudWatch Logs can monitor information in the log files and notify you when certain thresholds are met. You can also archive your log data in highly durable storage. For more information, see the [**Amazon CloudWatch Logs User Guide**](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/)**.**

### Want to learn more?

<https://docs.aws.amazon.com/IAM/latest/UserGuide/security-logging-and-monitoring.html>