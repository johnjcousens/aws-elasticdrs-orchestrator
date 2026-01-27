# Runbook - EC2 Start/Stop Automation deployment

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5425299493/Runbook%20-%20EC2%20Start/Stop%20Automation%20deployment

**Created by:** Srinath K on January 08, 2026  
**Last modified by:** Srinath K on January 08, 2026 at 01:29 PM

---


```markdown
# EC2 Auto Start/Stop Automation Solution

## Overview

The EC2 Auto Start/Stop solution provides automated instance management using AWS EventBridge, Lambda, and SNS. This system automatically starts and stops EC2 instances based on predefined schedules, helping optimize costs while ensuring instances are available during business hours.

---

## Architecture

### Components
- **AWS Lambda**: Core automation logic for starting/stopping instances
- **Amazon EventBridge**: Scheduled triggers for automation
- **Amazon SNS**: Error notifications via email
- **Amazon EC2**: Target instances with tag-based filtering
- **AWS CloudFormation**: Infrastructure as Code deployment
- **Amazon S3**: Lambda deployment package storage

### Architecture Diagram
```
EventBridge Rules → Lambda Function → EC2 API
                                  ↓
                               SNS Topic → Email Notifications
```

📋 **Detailed Architecture Diagram**: See [AWS-Architecture-Diagram.md](./AWS-Architecture-Diagram.md) for comprehensive visual architecture specifications.

---

## Features

| Feature | Description |
|---------|-------------|
| **Automated Scheduling** | Start instances at 8 AM IST, stop at 8 PM IST on weekdays |
| **Weekend Management** | Instances remain stopped from Friday 8 PM to Monday 8 AM |
| **Tag-based Filtering** | Only processes instances with `autostart=on` tag |
| **Error Notifications** | Detailed SNS email alerts for failures with instance IDs |
| **Comprehensive Logging** | CloudWatch logs for troubleshooting and audit |
| **Cost Optimization** | Estimated monthly cost: <$2 |

---

## Schedule Details

| Operation | Days | Time (IST) | Time (UTC) | Cron Expression |
|-----------|------|------------|------------|-----------------|
| **Start** | Mon-Fri | 8:00 AM | 2:30 AM | `cron(30 2 ? * MON-FRI *)` |
| **Stop** | Mon-Fri | 8:00 PM | 2:30 PM | `cron(30 14 ? * MON-FRI *)` |
| **Weekend Stop** | Friday | 8:00 PM | 2:30 PM | `cron(30 14 ? * FRI *)` |

---

## Prerequisites

### AWS Permissions Required
- EC2: `DescribeInstances`, `StartInstances`, `StopInstances`
- SNS: `Publish`
- Lambda: `InvokeFunction`
- CloudFormation: Stack management permissions
- S3: Bucket creation and object upload

### Tools Required
- AWS CLI configured with appropriate credentials
- Bash shell environment
- Email access for SNS subscription confirmation

---

## Deployment Guide

## Deployment Guide

### Console Deployment
**The Lambda code is now embedded in the CloudFormation template for automated deployment.**

### Quick Steps:
1. **Deploy**: Upload `ec2-start-stop-automation-cfn.yaml` to CloudFormation Console
2. **Configure**: Set stack name and notification email
3. **Confirm**: Accept SNS email subscription

**No manual Lambda code upload required!**

---

## Usage Instructions

### Tagging EC2 Instances
Add the `autostart` tag to instances you want to manage:

**AWS CLI:**
```bash
aws ec2 create-tags --resources i-1234567890abcdef0 --tags Key=autostart,Value=on
```

**AWS Console:**
1. Navigate to EC2 → Instances
2. Select target instance(s)
3. Actions → Instance Settings → Manage Tags
4. Add tag: Key=`autostart`, Value=`on`

### Manual Testing
Test the automation manually using AWS CLI:

**Start Operation:**
```bash
aws lambda invoke --function-name ec2-automation \
  --payload '{"action":"start"}' response.json
```

**Stop Operation:**
```bash
aws lambda invoke --function-name ec2-automation \
  --payload '{"action":"stop"}' response.json
```

---

## Monitoring and Troubleshooting

### CloudWatch Logs
- **Log Group**: `/aws/lambda/ec2-automation`
- **Retention**: 14 days (configurable)
- **Log Level**: INFO

### SNS Notifications
Error notifications include:
- **Timestamp** of operation
- **Successful operations** count and instance IDs
- **Failed operations** with detailed error information:
  - Instance ID that failed
  - Error type (e.g., ClientError, InvalidInstanceID)
  - Detailed error message
- **CloudWatch logs reference** for additional details

### Sample Error Notification
```
Subject: EC2 Automation Error - Start Operation Failed

EC2 Instance Start Operation Report

Timestamp: 2024-01-15T10:30:00.000000+00:00

Successful Operations (2):
  ✓ Started: i-1234567890abcdef0
  ✓ Started: i-0987654321fedcba0

Failed Operations (1):
  ✗ Instance ID: i-abcdef1234567890
    Error Type: ClientError
    Error Details: An error occurred (InvalidInstanceID.NotFound) when calling the StartInstances operation

Please investigate and resolve these issues.
Check CloudWatch logs for additional details: /aws/lambda/ec2-automation
```

---

## Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| **No instances processed** | Missing `autostart=on` tag | Verify tag exists on target instances |
| **Permission errors** | Insufficient IAM permissions | Check Lambda execution role permissions |
| **Time zone issues** | Schedule confusion | Schedules use UTC with IST conversion |
| **Email not received** | SNS subscription not confirmed | Check email and confirm subscription |
| **Lambda timeout** | Too many instances | Increase Lambda timeout or batch processing |

---

## Security Considerations

### IAM Permissions
The solution follows the principle of least privilege:
- **EC2 permissions**: Limited to describe, start, and stop operations
- **SNS permissions**: Publish only to specific topic
- **No hardcoded credentials**: Uses IAM roles and environment variables

### Network Security
- Lambda function runs in AWS managed VPC
- No inbound network access required
- All communications use AWS internal networks

### Audit Trail
- All operations logged to CloudWatch
- SNS notifications provide operation history
- CloudFormation stack provides infrastructure audit

---

## Cost Analysis

| Service | Monthly Cost (Estimated) |
|---------|-------------------------|
| **Lambda** | ~$0.20 (typical usage) |
| **EventBridge** | ~$1.00 (3 rules) |
| **SNS** | ~$0.50 (notifications) |
| **CloudWatch Logs** | ~$0.30 (14-day retention) |
| **Total** | **~$2.00/month** |

*Costs may vary based on usage patterns and AWS region*

---

## File Structure

```
autostart-script/
├── cloudformation-template.yaml    # Infrastructure template
├── lambda_function.py              # Lambda function code
├── README.md                       # Basic documentation
├── EC2-Automation-Documentation.md # Comprehensive guide
├── DEPLOYMENT-GUIDE.md             # Console deployment steps
├── FIXES-APPLIED.md                # Security fixes summary
├── AWS-Architecture-Diagram.md     # Architecture diagrams
├── generate_architecture_diagram.py # Advanced diagram generator
└── generate_simple_diagram.py      # Simple diagram generator
```

---

## Support and Maintenance

### Regular Maintenance Tasks
- **Monthly**: Review CloudWatch logs for any recurring issues
- **Quarterly**: Validate instance tags and update as needed
- **Annually**: Review and update notification email addresses

### Updating the Solution
To update Lambda code:
1. Modify `lambda_function.py`
2. Run `./deploy.sh` to redeploy
3. Test functionality with manual invocation

### Scaling Considerations
- Current solution handles up to 100 instances efficiently
- For larger deployments, consider:
  - Batch processing in Lambda
  - Multiple Lambda functions by region/environment
  - Enhanced error handling and retry logic

---

## Contact Information

| Role | Contact | Responsibility |
|------|---------|----------------|
| **Solution Owner** | [Your Team] | Overall solution maintenance |
| **AWS Administrator** | [AWS Team] | Infrastructure and permissions |
| **On-call Support** | [Support Team] | Issue resolution and monitoring |

---

*Last Updated: [Current Date]*
*Version: 1.0*
```
