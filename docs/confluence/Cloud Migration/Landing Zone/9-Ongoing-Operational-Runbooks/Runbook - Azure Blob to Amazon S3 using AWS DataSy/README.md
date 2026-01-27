# Runbook - Azure Blob to Amazon S3 using AWS DataSync - Agentless Deployment

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5251596289/Runbook%20-%20Azure%20Blob%20to%20Amazon%20S3%20using%20AWS%20DataSync%20-%20Agentless%20Deployment

**Created by:** Himanshu Gupta on November 19, 2025  
**Last modified by:** Himanshu Gupta on November 27, 2025 at 07:06 AM

---

AWS DataSync is a secure, online data transfer service that simplifies, automates, and accelerates moving data between on-premises storage systems and AWS storage services. For HealthEdge's migration journey, DataSync provides a robust solution for transferring large volumes of healthcare data while maintaining data integrity and security compliance.

DataSync supports transfers from Network File System (NFS), Server Message Block (SMB), Hadoop Distributed File System (HDFS), self-managed object storage, Azure Blob and other cloud storage systems to Amazon S3, Amazon EFS, Amazon FSx for Windows File Server, Amazon FSx for Lustre, Amazon FSx for OpenZFS, and Amazon FSx for NetApp ONTAP.

DataSync supports agentless transfers between Azure Blob Storage and Amazon S3 when using Enhanced mode. This means you don't need to deploy or manage any DataSync agents - the service handles the transfer directly between the cloud storage services.

### Key benefits of DataSync:

* Automate data movement - DataSync makes it easier to transfer data over the network between storage systems and services, automating both the management of data-transfer processes and the infrastructure required for high performance and secure data transfers
* Transfer data securely - DataSync provides end-to-end security, including encryption and data integrity validation using Transport Layer Security (TLS), to help ensure that your data arrives securely, intact, and ready to use
* Built-in scheduling mechanism - Periodically run data transfer tasks to detect and copy changes with hourly, daily, or weekly options
* Comprehensive monitoring and auditing - Integration with Amazon CloudWatch for monitoring transfer status and AWS CloudTrail for audit logging
* HIPAA eligible service - AWS DataSync is a HIPAA eligible service that can be used by covered entities and business associates to process, maintain, and store protected health information when used with a signed Business Associate Agreement (BAA)

### Architecture Diagram

![AzureBlobtoS3.png](images/AzureBlobtoS3.png)![AzureBlobtoS3_flow.png](images/AzureBlobtoS3_flow.png)

### Azure Infrastructure:

* Blob Containers
* SAS Token with read and list permissions for each Blob container. Make sure that your SAS doesn't expire before you expect to finish your transfer.

#### AWS Cloud Infrastructure:

* SAS Token stored in AWS Secrets manager
* Amazon S3 target bucket
* Amazon IAM Role to read SAS token stored in AWS Secrets manager and permissions list and write to the S3 bucket
* Sample IAM Role policy - *Change Account ID, Region and ARNs as required*


```
IAM Role Policy Example

{
	"Version": "October 17, 2012",
	"Statement": [
		{
			"Sid": "AllowDataSyncSecretsManagerAccess",
			"Effect": "Allow",
			"Action": [
				"secretsmanager:GetSecretValue",
				"secretsmanager:DescribeSecret"
			],
			"Resource": "arn:aws:secretsmanager:us-east-1:827859360968:secret:AzureBlobSAStoken*"
		},
		{
			"Sid": "AllowListSecrets",
			"Effect": "Allow",
			"Action": [
				"secretsmanager:ListSecrets"
			],
			"Resource": "*"
		},
		{
			"Sid": "AllowS3BucketAccess",
			"Effect": "Allow",
			"Action": [
				"s3:GetBucketLocation",
				"s3:ListBucket",
				"s3:ListBucketMultipartUploads"
			],
			"Resource": [
				"arn:aws:s3:::hrp-s3-jenk-dev-use1",
				"arn:aws:s3:::hrp-s3-dbbackup-dev-use1",
				"arn:aws:s3:::hrp-s3-datasync-transferlogs-use1"
			]
		},
		{
			"Sid": "AllowS3ObjectAccess",
			"Effect": "Allow",
			"Action": [
				"s3:AbortMultipartUpload",
				"s3:DeleteObject",
				"s3:GetObject",
				"s3:GetObjectTagging",
				"s3:GetObjectVersion",
				"s3:GetObjectVersionTagging",
				"s3:ListMultipartUploadParts",
				"s3:PutObject",
				"s3:PutObjectTagging"
			],
			"Resource": [
				"arn:aws:s3:::hrp-s3-jenk-dev-use1/*",
				"arn:aws:s3:::hrp-s3-dbbackup-dev-use1/*",
				"arn:aws:s3:::hrp-s3-datasync-transferlogs-use1/*"
			]
		},
		{
			"Sid": "AllowCloudWatchLogsAccess",
			"Effect": "Allow",
			"Action": [
				"logs:CreateLogGroup",
				"logs:CreateLogStream",
				"logs:PutLogEvents",
				"logs:DescribeLogGroups",
				"logs:DescribeLogStreams"
			],
			"Resource": "arn:aws:logs:us-east-1:827859360968:log-group:/aws/datasync:*"
		}
	]
}
```


### AWS DataSync Config and Transfer steps:

1. Identify the Azure blob container you wish to migrate, go to blob setting and generate the SAS token. Make sure that your SAS doesn't expire before you expect to finish your transfer.

   1. [Create SAS Token via Azure Portal](https://learn.microsoft.com/en-us/azure/ai-services/translator/document-translation/how-to-guides/create-sas-tokens?tabs=Containers#create-sas-tokens-in-the-azure-portal)
   2. [Create SAS Token via Azure Storage Explorer](https://learn.microsoft.com/en-us/azure/ai-services/translator/document-translation/how-to-guides/create-sas-tokens?tabs=Containers#create-sas-tokens-with-azure-storage-explorer)
2. Save SAS Token in Secrets Manager

   1. Go to AWS console
   2. Search and navigate to Secrets Manager
   3. Create new secret > Other type of secret > plain text and store the SAS token (Token only not URL+Token, e.g.)

![image-20251119-145800.png](images/image-20251119-145800.png)

3. Create the source location on AWS DataSync console

   1. Go to AWS console
   2. Search and Navigate to DataSync page
   3. Go to location > create location > select the location type as Azure Blob and provide the required details
   4. Select Use a Secrets Manager secret for SAS token and select the IAM role and AWS Secrets manager ARN

![Screenshot_2025-11-19_at_4.44.01_PM.png](images/Screenshot_2025-11-19_at_4.44.01_PM.png)

[Creating Azure Blob source location](https://docs.aws.amazon.com/datasync/latest/userguide/creating-azure-blob-location.html#creating-azure-blob-location-how-to)

2. Create the target location

   1. Go to AWS console
   2. Search and Navigate to DataSync page
   3. Go to location > create location > select the location type as S3 and provide the required details and create the location

[Creating S3 target location](https://docs.aws.amazon.com/datasync/latest/userguide/create-s3-location.html#create-s3-location-how-to)

3. Create DataSync task

   1. Go to AWS console
   2. Search and Navigate to DataSync page
   3. Go to task > Select source and target location > select the required options and create the task
   4. Select and execute the task either with defaults or override with options
   5. Once the task is executed go to task history to monitor transfer

[Creating a task](https://docs.aws.amazon.com/datasync/latest/userguide/create-task-how-to.html#create-task-steps)

[Executing a task](https://docs.aws.amazon.com/datasync/latest/userguide/run-task.html#starting-task)

### References:

[AWS DataSync userguide](https://docs.aws.amazon.com/datasync/latest/userguide/what-is-datasync.html)

[AWS DataSync Agentless Azure Blob to Amazon](https://docs.aws.amazon.com/datasync/latest/userguide/creating-azure-blob-location.html#azure-blob-sas-tokens)