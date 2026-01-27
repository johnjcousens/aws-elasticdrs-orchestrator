# AWS-Services

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867032943/AWS-Services

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:20 AM

---

List of AWS Services
--------------------

* [*Amazon EventBridge*](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html)
  **Required**. Used to accept Lambda events into a single EventBridge event bus; used to start events from the Runbook Management System.
* [*AWS Lambda*](https://aws.amazon.com/lambda/)
  **Required**. Used to operate the solution and by automations.
* [*AWS Step Functions*](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html)   
  **Required**. Used for long-lived automations (e.g., automations that require to run for more than 24hs).
* [*Amazon DynamoDB*](https://aws.amazon.com/dynamodb/)
  **Required**. Used as part of the automation timeout feature; step function polls for a complete automation, DynamoDB will capture a ‘task complete’ table for logs.
* [*Amazon API Gateway*](https://aws.amazon.com/api-gateway/)
  **Required unless Cutover Connect is used for integration**. Used for integration with Cutover.com.
* [*AWS Secrets Manager*](https://aws.amazon.com/secrets-manager/)  
  **Required**. Used to store secrets (e.g., API tokens, server credentials).
* [*AWS Identity Access Management*](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html)   
  **Required**. Authentication for automations, services, or personnel.
* [*Amazon Simple Queue Service*](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html)
  **Optional**. Queue used in Runbook Management system to poll for events when using Cutover Connect
* [*AWS CloudFormation*](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html)   
  **Required**. Used to deploy the solution and automations.
* [*Amazon Simple Storage Service*](https://aws.amazon.com/s3/)
  **Required**. S3 buckets are used to store logs, metadata, and others.
* [*AWS Systems Manager*](https://aws.amazon.com/systems-manager/)
  **Required**.Supports the running of automation packages on the customer provided Automation server. Supports for using SSM Parameter Store to keep a reference to API URLs.
* [*AWS CloudWatch*](https://aws.amazon.com/cloudwatch/)   
  **Required**. AWS CloudWatch is used to securely store automation logs that are used to monitor the status of running automations.
* [*Amazon QuickSight*](https://aws.amazon.com/quicksight/)
  **Optional**. Used for collecting data from Cloud Migration Factory (CMF), Runbook Management system, and others, to create additional migration dashboards and reports.
* [*AWS Glue*](https://aws.amazon.com/glue/)
  **Optional**. Regularly extracts data held in Cutover.com to Amazon S3, providing reporting data for use in Amazon Athena and Amazon QuickSight dashboards
* [*Amazon Athena*](https://aws.amazon.com/athena/)
  **Optional**. Provides access to reporting data extracted by AWS Glue from the migration metadata, allowing dashboards to be created using Amazon QuickSight
* [*Amazon Cognito*](https://aws.amazon.com/cognito/)
  **Required**. CMF - User authorization and authentication, optional federation with other IDPs is also achieved through Amazon Cognito.
* [*Amazon EC2*](https://aws.amazon.com/ec2/)
  **Optional**. CMF - Automation server running AWS Systems Manager agents to allow running of automation packages.
* [*Amazon CloudFront*](https://aws.amazon.com/cloudfront/)
  **Optional**. CMF - For standard deployments Amazon CloudFront provides the distribution of the web interface content from Amazon S3, making it highly available globally, and providing secure TLS access to the web interface content from anywhere.
* [*Amazon Application Migration Service (AWS MGN)*](https://aws.amazon.com/application-migration-service/)
  **Optional**. CMF - When performing rehost migrations of Windows or Linux workloads, Cloud Migration Factory on AWS uses AWS MGN to facilitate the system migration to Amazon EC2.
* [*AWS Web Application Firewall)*](https://aws.amazon.com/waf/)
  **Optional**. CMF - Apply additional security on the endpoints for Amazon API Gateway and Amazon CloudFront to restrict access to specific devices based on source IP address or other access