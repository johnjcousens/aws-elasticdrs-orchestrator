# RelatedResources

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866998816/RelatedResources

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:03 AM

---

These resources can be used to help you design and implement your operations related artifacts and solutions.  You can use the resources here to learn more about AWS so that you can use features that best help meet your requirements.  You should update this document to include additional assets both internal and external that are related to the operations workstream analysis and design activities.

Web
---

* **[AWS Management and Governance Blog](https://aws.amazon.com/blogs/mt/)** - This is your goto location to learn about AWS announcements as well as best practices for AWS Management & Governance Services.  All employees who have a job function that relates to Cloud Operations should keep apprised of the content on this blog to stay current on AWS services and practices.
* **[Use tags to create and maintain Amazon CloudWatch alarms for Amazon EC2 instances](https://aws.amazon.com/blogs/mt/use-tags-to-create-and-maintain-amazon-cloudwatch-alarms-for-amazon-ec2-instances-part-1/)** - This blog and accompanying code provides a way for you to define and automatically create a standard set of CloudWatch alarms for new EC2 instances and lambda functions.  This is especially helpful in a migration so that you can configure and manage standard alarms without any manual effort.

Code
----

* **[amazon-cloudwatch-auto-alarms](https://github.com/aws-samples/amazon-cloudwatch-auto-alarms) -** This open source solution enables you to create a standard set of CloudWatch alarms for Amazon EC2 and AWS Lambda.  It can be used as a part of your solution design for Logging & Monitoring / Incident & Event Management.
* **[logging-monitoring-apg-guide-examples](https://github.com/aws-samples/logging-monitoring-apg-guide-examples) -** This repository contains many different CloudFormation templates and examples for implementing logging and monitoring on Amazon EC2, Amazon ECS, Amazon EKS, and AWS Lambda.

AWS Prescriptive Guidance - Guides
----------------------------------

* **[Designing and implementing logging and monitoring with Amazon CloudWatch](https://docs.aws.amazon.com/prescriptive-guidance/latest/implementing-logging-monitoring-cloudwatch/welcome.html)** -  This guide helps you design and implement logging and monitoring with 
  [Amazon CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html) 
  and related Amazon Web Services (AWS) management and governance services for workloads that use 
  [Amazon Elastic Compute Cloud (Amazon EC2) instances](https://docs.aws.amazon.com/ec2/index.html), 
  [Amazon Elastic Container Service (Amazon ECS)](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html), 
  [Amazon Elastic Kubernetes Service (Amazon EKS)](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html), 
  [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html), and on-premises servers. The guide is intended for operations teams, DevOps engineers, and application engineers that manage workloads on the AWS Cloud.
* **[Backup and recovery approaches on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/backup-recovery/welcome.html)** - This guide covers different backup architectures (cloud-native applications, hybrid, and on-premises environments). It also covers associated Amazon Web Services (AWS) services that can be used to build scalable and reliable data-protection solutions for the non-immutable components of your architecture.
* **[Automated patching for non-immutable instances in the hybrid cloud using AWS Systems Manager](https://docs.aws.amazon.com/prescriptive-guidance/latest/patch-management-hybrid-cloud/welcome.html)** - This prescriptive guide describes an automated patching solution that uses Amazon Web Services (AWS) Systems Manager. You can use this solution to patch both your non-immutable (long-running) Amazon Elastic Compute Cloud (Amazon EC2) instances that span multiple AWS accounts and AWS Regions, and your on-premises instances.

Videos
------

* **[AWS Management and Governance Youtube Series](https://www.youtube.com/playlist?list=PLhr1KZpdzukcaA06WloeNmGlnM_f1LrdP)** - The [AWS Management and Governance services](https://aws.amazon.com/products/management-and-governance/) enable developers with speed and built-in governance control.  This category of AWS services are closely tied to the Operations workstream and related deliverables.  The video series walks you through many different services in the category and can help you get a quick overview before you dive deeper.
* **[re:Invent 2020 Management Tools and Governance Breakout Sessions](https://www.youtube.com/watch?v=jG1g6BM7hsQ&list=PL2yQDdvlhXf-rv9ro9HcHjeutMu4K7pZM)** - This playlist provides deep dives into specific Management & Governance services and their application.