# Decision---Human-IAM-Roles-and-Policies-Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867065386/Decision---Human-IAM-Roles-and-Policies-Design

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** David Garibaldi on October 23, 2025 at 06:52 PM

---

### Document Lifecycle Status

**Purpose**
-----------

Outline the core IAM roles, and policies which will be used within accounts. This is not a definitive list and may grow as cloud adoption maturity grows. Defining human identity and access management requirements aligns to Well-Architected best practices. It is important to define requirements that will help control human access with appropriate defined, limited and segregated access. This requires the identification of compliance requirements, compliance resources, and defining roles and responsibilities. Policysets in doc are current as of October 23, 2025

### Decision

Define human identity and access management requirements. Improve policy sets over time to improve least privilege role permissions.

Note: RDS Permission may need to be added over time once service is available to team.

Note: Users in the future will need to access VMs via SSM, but currently, users are logging into boxes via RDP and SSH.

**Implementation**
------------------

### IAM Roles and Polices Definition

Each IAM Role need to be defined with responsibilities and based on those responsibilities the access permissions are allowed or denied with the help of IAM Policy.  An IAM Policy is a JSON formatted document that provides a list of ‘Allow’ or ‘Deny’ permissions. It consists of one or more statements, each of which describes the set of permissions. The following roles and policies will be deployed in each account.

#### Default Roles

Initial set of generic roles for access inside of AWS. These roles could be separated by product, but are represented as generic roles. All Identity Center PermissionSets a have a default permission boundary placed upon them restricting actions to same OrgId.

| Role | Purpose | Capabilities | Access Policy |
| --- | --- | --- | --- |
| he-engineering-dev | Perform development tasks | Full access to AWS services and resources (this could also be used as a policy for Sandbox accounts) | Customer Managed: he-engineering-dev 
```json
{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Sid": "AllowCoreComputeServices",
      "Effect": "Allow",
      "Action": [
        "autoscaling:*",
        "ec2:*",
        "ecr:*",
        "ecs:*",
        "elasticbeanstalk:*",
        "elasticloadbalancing:*",
        "eks:*",
        "lambda:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowStorageAndDatabase",
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "rds:*",
        "dynamodb:*",
        "elasticache:*",
        "redshift:*",
        "docdb-elastic:*",
        "fsx:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowDirectoryServiceForFSx",
      "Effect": "Allow",
      "Action": [
        "ds:DescribeDirectories",
        "ds:AuthorizeApplication",
        "ds:UnauthorizeApplication",
        "ds:GetDirectoryLimits"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowSessionManagerAndSystemsManager",
      "Effect": "Allow",
      "Action": [
        "ssm:StartSession",
        "ssm:TerminateSession",
        "ssm:ResumeSession",
        "ssm:SendCommand",
        "ssm:ListCommandInvocations",
        "ssm:DescribeInstanceInformation",
        "ssm:DescribeInstanceProperties",
        "ssm:GetCommandInvocation",
        "ssm:PutParameter",
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
        "ssm:DeleteParameter",
        "ssm:DescribeParameters",
        "ssm:AddTagsToResource",
        "ssm:ListTagsForResource",
        "ec2-instance-connect:SendSSHPublicKey"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowDevelopmentIAMOperations",
      "Effect": "Allow",
      "Action": [
        "iam:DeleteRole",
        "iam:UpdateRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRole",
        "iam:ListRoles",
        "iam:PassRole",
        "iam:CreateInstanceProfile",
        "iam:DeleteInstanceProfile",
        "iam:AddRoleToInstanceProfile",
        "iam:RemoveRoleFromInstanceProfile",
        "iam:CreatePolicy",
        "iam:DeletePolicy",
        "iam:GetPolicy",
        "iam:ListPolicies",
        "iam:CreatePolicyVersion",
        "iam:DeletePolicyVersion",
        "iam:GetPolicyVersion",
        "iam:ListPolicyVersions"
      ],
      "Resource": [
        "arn:aws:iam::*:role/lambda-*",
        "arn:aws:iam::*:role/ec2-*",
        "arn:aws:iam::*:role/ecs-*",
        "arn:aws:iam::*:role/eks-*",
        "arn:aws:iam::*:role/rds-*",
        "arn:aws:iam::*:role/docdb-elastic-*",
        "arn:aws:iam::*:role/elasticache-*",
        "arn:aws:iam::*:role/fsx-*",
        "arn:aws:iam::*:instance-profile/*",
        "arn:aws:iam::*:policy/*"
      ]
    },
    {
      "Sid": "AllowCreateRoleWithBoundary",
      "Effect": "Allow",
      "Action": "iam:CreateRole",
      "Resource": [
        "arn:aws:iam::*:role/lambda-*",
        "arn:aws:iam::*:role/ec2-*",
        "arn:aws:iam::*:role/ecs-*",
        "arn:aws:iam::*:role/eks-*",
        "arn:aws:iam::*:role/rds-*",
        "arn:aws:iam::*:role/docdb-elastic-*",
        "arn:aws:iam::*:role/elasticache-*",
        "arn:aws:iam::*:role/fsx-*"
      ],
      "Condition": {
        "StringEquals": {
          "iam:PermissionsBoundary": "arn:aws:iam::${aws:PrincipalAccount}:policy/he-service-boundary"
        }
      }
    },
    {
      "Sid": "AllowReadOnlyIAMOperations",
      "Effect": "Allow",
      "Action": [
        "iam:Get*",
        "iam:List*",
        "iam:GenerateServiceLastAccessedDetails"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowLimitedSecretsManager",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:CreateSecret",
        "secretsmanager:PutSecretValue",
        "secretsmanager:UpdateSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:TagResource"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:*"
    },
    {
      "Sid": "AllowKMSForDevelopment",
      "Effect": "Allow",
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey",
        "kms:CreateGrant",
        "kms:ListKeys",
        "kms:ListAliases"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": [
            "s3.*.amazonaws.com",
            "rds.*.amazonaws.com",
            "secretsmanager.*.amazonaws.com",
            "dynamodb.*.amazonaws.com",
            "elasticache.*.amazonaws.com",
            "ec2.*.amazonaws.com",
            "docdb-elastic.*.amazonaws.com",
            "ssm.*.amazonaws.com",
            "fsx.*.amazonaws.com",
            "eks.*.amazonaws.com"
          ]
        }
      }
    },
    {
      "Sid": "AllowCloudFormationAndInfrastructure",
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "cloudwatch:*",
        "cloudtrail:LookupEvents",
        "cloudtrail:GetTrailStatus", 
        "cloudtrail:DescribeTrails",
        "cloudtrail:GetEventSelectors",
        "cloudtrail:ListTrails",
        "logs:*",
        "sns:*",
        "sqs:*",
        "events:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowResourceTagging",
      "Effect": "Allow",
      "Action": [
        "tag:GetResources",
        "tag:GetTagKeys",
        "tag:GetTagValues",
        "tag:TagResources"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowXRayTracing",
      "Effect": "Allow",
      "Action": [
        "xray:GetTraceGraph",
        "xray:GetTraceSummaries",
        "xray:BatchGetTraces",
        "xray:GetServiceGraph",
        "xray:GetTimeSeriesServiceStatistics",
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords"
      ],
      "Resource": "*"
    }
  ]
}
```
  AWS Managed: ViewOnly |
| he-engineering-nonprod | Perform development tasks | Full access to AWS services and resources (this could also be used as a policy for Sandbox accounts) | Customer Managed he-engineering-nonprod 
```json
A{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Sid": "AllowSessionManagerReadOnly",
      "Effect": "Allow",
      "Action": [
        "ssm:DescribeInstanceInformation",
        "ssm:DescribeInstanceProperties",
        "ssm:DescribeParameters",
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
        "ssm:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowEC2ReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ec2:DescribeInstanceAttribute",
        "ec2:DescribeImages",
        "ec2:DescribeSnapshots",
        "ec2:DescribeVolumes",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowCloudWatchLogsReadOnly",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents",
        "logs:FilterLogEvents",
        "logs:StartQuery",
        "logs:StopQuery",
        "logs:GetQueryResults"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowDatabaseServicesReadOnly",
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters",
        "rds:DescribeDBSubnetGroups",
        "rds:DescribeDBParameterGroups",
        "rds:DescribeDBClusterParameterGroups",
        "rds:DescribeDBSnapshots",
        "rds:DescribeDBClusterSnapshots",
        "rds:DescribeEventSubscriptions",
        "rds:DescribeEvents",
        "rds:ListTagsForResource",
        "docdb-elastic:GetCluster",
        "docdb-elastic:GetClusterSnapshot",
        "docdb-elastic:ListClusters",
        "docdb-elastic:ListClusterSnapshots",
        "docdb-elastic:ListPendingMaintenanceActions",
        "docdb-elastic:GetPendingMaintenanceAction",
        "docdb-elastic:ListTagsForResource",
        "elasticache:DescribeCacheClusters",
        "elasticache:DescribeReplicationGroups",
        "elasticache:DescribeCacheSubnetGroups",
        "elasticache:DescribeCacheParameterGroups",
        "elasticache:DescribeSnapshots",
        "elasticache:DescribeEvents",
        "elasticache:ListTagsForResource",
        "dynamodb:DescribeTable",
        "dynamodb:ListTables",
        "dynamodb:DescribeBackup",
        "dynamodb:ListBackups",
        "dynamodb:ListTagsOfResource",
        "redshift:DescribeClusters",
        "redshift:DescribeClusterSubnetGroups",
        "redshift:DescribeClusterParameterGroups",
        "redshift:DescribeClusterSnapshots",
        "redshift:DescribeEvents"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowStorageAndFileSystemsReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "s3:GetBucketVersioning",
        "s3:GetBucketPolicy",
        "s3:GetBucketTagging",
        "s3:GetBucketLogging",
        "s3:GetBucketNotification",
        "fsx:DescribeFileSystems",
        "fsx:DescribeBackups",
        "fsx:DescribeDataRepositoryTasks",
        "fsx:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowCloudWatchReadOnly",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:DescribeAlarms",
        "cloudwatch:DescribeAlarmsForMetric",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:GetMetricData",
        "cloudwatch:ListMetrics",
        "cloudwatch:ListDashboards",
        "cloudwatch:GetDashboard"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowKubernetesReadOnly",
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:DescribeNodegroup",
        "eks:ListNodegroups",
        "eks:DescribeAddon",
        "eks:ListAddons",
        "eks:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowComputeServicesReadOnly",
      "Effect": "Allow",
      "Action": [
        "lambda:ListFunctions",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:ListEventSourceMappings",
        "lambda:GetEventSourceMapping",
        "lambda:ListTags",
        "ecs:ListClusters",
        "ecs:DescribeClusters",
        "ecs:ListServices",
        "ecs:DescribeServices",
        "ecs:ListTasks",
        "ecs:DescribeTasks",
        "ecs:DescribeTaskDefinition",
        "ecs:ListTaskDefinitions",
        "ecr:DescribeRepositories",
        "ecr:ListImages",
        "ecr:DescribeImages",
        "ecr:GetRepositoryPolicy",
        "elasticbeanstalk:DescribeApplications",
        "elasticbeanstalk:DescribeEnvironments",
        "elasticbeanstalk:DescribeConfigurationSettings",
        "elasticbeanstalk:DescribeEvents",
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:DescribeLaunchConfigurations",
        "autoscaling:DescribeScalingActivities",
        "autoscaling:DescribePolicies",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:DescribeListeners",
        "elasticloadbalancing:DescribeRules",
        "elasticloadbalancing:DescribeTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowDirectoryServiceReadOnly",
      "Effect": "Allow",
      "Action": [
        "ds:DescribeDirectories",
        "ds:GetDirectoryLimits",
        "ds:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowInfrastructureReadOnly",
      "Effect": "Allow",
      "Action": [
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackResources",
        "cloudformation:DescribeStackEvents",
        "cloudformation:ListStacks",
        "cloudformation:GetTemplate",
        "cloudtrail:LookupEvents",
        "cloudtrail:GetTrailStatus",
        "cloudtrail:DescribeTrails",
        "cloudtrail:GetEventSelectors",
        "cloudtrail:ListTrails",
        "sns:ListTopics",
        "sns:GetTopicAttributes",
        "sns:ListSubscriptions",
        "sns:ListTagsForResource",
        "sqs:ListQueues",
        "sqs:GetQueueAttributes",
        "sqs:ListQueueTags",
        "events:ListRules",
        "events:DescribeRule",
        "events:ListTargetsByRule",
        "events:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowKMSReadOnly",
      "Effect": "Allow",
      "Action": [
        "kms:DescribeKey",
        "kms:ListKeys",
        "kms:ListAliases",
        "kms:GetKeyPolicy",
        "kms:GetKeyRotationStatus"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowIAMReadOnly",
      "Effect": "Allow",
      "Action": [
        "iam:GetRole",
        "iam:ListRoles",
        "iam:GetPolicy",
        "iam:ListPolicies",
        "iam:GetInstanceProfile",
        "iam:ListInstanceProfiles",
        "iam:ListAttachedRolePolicies",
        "iam:ListRolePolicies",
        "iam:GetRolePolicy"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowSecretsManagerReadOnly",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecrets"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyDataAccess",
      "Effect": "Deny",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "rds:DownloadDBLogFilePortion",
        "rds:DownloadCompleteDBLogFile",
        "dynamodb:GetItem",
        "dynamodb:BatchGetItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "redshift:GetClusterCredentials",
        "redshift-data:*",
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowSessionManagerOnly",
      "Effect": "Allow",
      "Action": [
        "ssm:StartSession",
        "ssm:TerminateSession",
        "ssm:ResumeSession"
      ],
      "Resource": [
        "arn:aws:ec2:*:*:instance/*",
        "arn:aws:ssm:*:*:session/*"
      ]
    },
    {
      "Sid": "AllowResourceTaggingReadOnly",
      "Effect": "Allow",
      "Action": [
        "tag:GetResources",
        "tag:GetTagKeys",
        "tag:GetTagValues"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowXRayReadOnly",
      "Effect": "Allow",
      "Action": [
        "xray:GetTraceGraph",
        "xray:GetTraceSummaries",
        "xray:BatchGetTraces",
        "xray:GetServiceGraph",
        "xray:GetTimeSeriesServiceStatistics"
      ],
      "Resource": "*"
    }
  ]
}
```
  AWS Managed: ViewOnly |
| he-engineering-prod | Perform support tasks in production | Read-only access | Customer Managed: he-engineering-nonprod 
```json
{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Sid": "AllowSessionManagerReadOnly",
      "Effect": "Allow",
      "Action": [
        "ssm:DescribeInstanceInformation",
        "ssm:DescribeInstanceProperties",
        "ssm:DescribeParameters",
        "ssm:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowEC2ReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ec2:DescribeImages",
        "ec2:DescribeSnapshots",
        "ec2:DescribeVolumes",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowCloudWatchLogsReadOnly",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowDatabaseServicesReadOnly",
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters",
        "rds:DescribeEvents",
        "docdb-elastic:GetCluster",
        "docdb-elastic:GetClusterSnapshot",
        "docdb-elastic:ListClusters",
        "docdb-elastic:ListClusterSnapshots",
        "docdb-elastic:ListPendingMaintenanceActions",
        "docdb-elastic:GetPendingMaintenanceAction",
        "docdb-elastic:ListTagsForResource",
        "elasticache:DescribeCacheClusters",
        "elasticache:DescribeReplicationGroups",
        "elasticache:DescribeEvents",
        "dynamodb:DescribeTable",
        "dynamodb:ListTables",
        "redshift:DescribeClusters",
        "redshift:DescribeEvents"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowStorageReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "s3:GetBucketTagging",
        "fsx:DescribeFileSystems",
        "fsx:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowCloudWatchReadOnly",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:DescribeAlarms",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "cloudwatch:ListDashboards",
        "cloudwatch:GetDashboard"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowComputeServicesReadOnly",
      "Effect": "Allow",
      "Action": [
        "lambda:ListFunctions",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "ecs:ListClusters",
        "ecs:DescribeClusters",
        "ecs:ListServices",
        "ecs:DescribeServices",
        "ecs:ListTasks",
        "ecs:DescribeTasks",
        "ecr:DescribeRepositories",
        "ecr:ListImages",
        "elasticbeanstalk:DescribeApplications",
        "elasticbeanstalk:DescribeEnvironments",
        "autoscaling:DescribeAutoScalingGroups",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeTargetGroups"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowInfrastructureReadOnly",
      "Effect": "Allow",
      "Action": [
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackResources",
        "cloudformation:ListStacks",
        "cloudtrail:LookupEvents",
        "cloudtrail:GetTrailStatus",
        "cloudtrail:DescribeTrails",
        "sns:ListTopics",
        "sns:GetTopicAttributes",
        "sqs:ListQueues",
        "sqs:GetQueueAttributes",
        "events:ListRules",
        "events:DescribeRule"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowKMSReadOnly",
      "Effect": "Allow",
      "Action": [
        "kms:DescribeKey",
        "kms:ListKeys",
        "kms:ListAliases"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowIAMReadOnly",
      "Effect": "Allow",
      "Action": [
        "iam:GetRole",
        "iam:ListRoles",
        "iam:GetPolicy",
        "iam:ListPolicies"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowSecretsManagerReadOnly",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecrets"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowResourceTaggingReadOnly",
      "Effect": "Allow",
      "Action": [
        "tag:GetResources",
        "tag:GetTagKeys",
        "tag:GetTagValues"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowXRayReadOnly",
      "Effect": "Allow",
      "Action": [
        "xray:GetTraceGraph",
        "xray:GetTraceSummaries",
        "xray:BatchGetTraces",
        "xray:GetServiceGraph"
      ],
      "Resource": "*"
    }
  ]
}
```
    AWS Managed: ViewOnly |
| he-database-dev | Perform development tasks | Full access to AWS services and resources (this could also be used as a policy for Sandbox accounts) | Customer Managed: he-engineering-nonprod 
```json
{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Sid": "AllowCoreComputeServices",
      "Effect": "Allow",
      "Action": [
        "lambda:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowS3DatabaseOperations",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetBucketVersioning",
        "s3:PutBucketVersioning",
        "s3:ListBucketVersions",
        "s3:DeleteObjectVersion",
        "s3:GetObjectVersion*"
      ],
      "Resource": [
        "arn:aws:s3:::*"
      ]
    },
    {
      "Sid": "AllowDocDBOperations",
      "Effect": "Allow",
      "Action": [
        "docdb-elastic:GetCluster",
        "docdb-elastic:GetClusterSnapshot",
        "docdb-elastic:ListClusters",
        "docdb-elastic:ListClusterSnapshots",
        "docdb-elastic:UpdateCluster",
        "docdb-elastic:CopyClusterSnapshot",
        "docdb-elastic:DeleteClusterSnapshot",
        "docdb-elastic:RestoreClusterFromSnapshot",
        "docdb-elastic:StartCluster",
        "docdb-elastic:StopCluster"
      ],
      "Resource": [
        "arn:aws:docdb-elastic:*:*:cluster:*",
        "arn:aws:docdb-elastic:*:*:cluster-snapshot:*"
      ]
    },
    {
      "Sid": "AllowFSxOperations",
      "Effect": "Allow",
      "Action": [
        "fsx:DescribeFileSystems",
        "fsx:DescribeVolumes",
        "fsx:DescribeStorageVirtualMachines",
        "fsx:CreateBackup",
        "fsx:DeleteBackup",
        "fsx:DescribeBackups"
      ],
      "Resource": [
        "arn:aws:fsx:*:*:file-system/*",
        "arn:aws:fsx:*:*:backup/*",
        "arn:aws:fsx:*:*:volume/*",
        "arn:aws:fsx:*:*:storage-virtual-machine/*"
      ]
    },
    {
      "Sid": "AllowEC2VolumeOperations",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVolumes",
        "ec2:DescribeVolumeStatus",
        "ec2:DescribeVolumeAttribute"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowDirectoryServiceForFSx",
      "Effect": "Allow",
      "Action": [
        "ds:DescribeDirectories",
        "ds:AuthorizeApplication",
        "ds:UnauthorizeApplication",
        "ds:GetDirectoryLimits"
      ],
      "Resource": "*"
    }
  ]
}

{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Sid": "AllowDevelopmentIAMOperations",
      "Effect": "Allow",
      "Action": [
        "iam:DeleteRole",
        "iam:UpdateRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRole",
        "iam:ListRoles",
        "iam:PassRole",
        "iam:CreatePolicy",
        "iam:DeletePolicy",
        "iam:GetPolicy",
        "iam:ListPolicies",
        "iam:CreatePolicyVersion",
        "iam:DeletePolicyVersion",
        "iam:GetPolicyVersion",
        "iam:ListPolicyVersions"
      ],
      "Resource": [
        "arn:aws:iam::*:role/lambda-*",
        "arn:aws:iam::*:policy/*"
      ]
    },
    {
      "Sid": "AllowCreateRoleWithBoundary",
      "Effect": "Allow",
      "Action": "iam:CreateRole",
      "Resource": [
        "arn:aws:iam::*:role/lambda-*"
      ],
      "Condition": {
        "StringEquals": {
          "iam:PermissionsBoundary": "arn:aws:iam::${aws:PrincipalAccount}:policy/he-service-boundary"
        }
      }
    },
    {
      "Sid": "AllowLimitedSecretsManager",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:CreateSecret",
        "secretsmanager:PutSecretValue",
        "secretsmanager:UpdateSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:TagResource"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:*database*"
    },
    {
      "Sid": "AllowKMSForDevelopment",
      "Effect": "Allow",
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey",
        "kms:CreateGrant",
        "kms:ListKeys",
        "kms:ListAliases"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": [
            "s3.*.amazonaws.com",
            "rds.*.amazonaws.com",
            "secretsmanager.*.amazonaws.com",
            "dynamodb.*.amazonaws.com",
            "ec2.*.amazonaws.com",
            "docdb-elastic.*.amazonaws.com",
            "ssm.*.amazonaws.com",
            "fsx.*.amazonaws.com"
          ]
        }
      }
    },
    {
      "Sid": "AllowCloudWatchOperations",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "cloudwatch:PutMetricAlarm",
        "cloudwatch:DeleteAlarms",
        "cloudwatch:DescribeAlarms"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowLogsOperations",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents",
        "logs:FilterLogEvents",
        "logs:StartQuery",
        "logs:StopQuery",
        "logs:GetQueryResults",
        "logs:DescribeQueries"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:/aws/rds/*",
        "arn:aws:logs:*:*:log-group:/aws/rds/*:*",
        "arn:aws:logs:*:*:log-group:/aws/docdb/*",
        "arn:aws:logs:*:*:log-group:/aws/docdb/*:*",
        "arn:aws:logs:*:*:log-group:/aws/lambda/*",
        "arn:aws:logs:*:*:log-group:/aws/lambda/*:*"
      ]
    },
    {
      "Sid": "AllowSNSOperations",
      "Effect": "Allow",
      "Action": [
        "sns:CreateTopic",
        "sns:DeleteTopic",
        "sns:Subscribe",
        "sns:Unsubscribe",
        "sns:Publish",
        "sns:GetTopicAttributes",
        "sns:SetTopicAttributes"
      ],
      "Resource": [
        "arn:aws:sns:*:*:*"
      ]
    },
    {
      "Sid": "AllowSQSOperations",
      "Effect": "Allow",
      "Action": [
        "sqs:CreateQueue",
        "sqs:DeleteQueue",
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:SetQueueAttributes"
      ],
      "Resource": [
        "arn:aws:sqs:*:*:*"
      ]
    },
    {
      "Sid": "AllowEventsOperations",
      "Effect": "Allow",
      "Action": [
        "events:PutRule",
        "events:DeleteRule",
        "events:PutTargets",
        "events:RemoveTargets",
        "events:DescribeRule",
        "events:ListTargetsByRule"
      ],
      "Resource": [
        "arn:aws:events:*::rule/*",
        "arn:aws:lambda:*::function:**",
        "arn:aws:sns:*:*:*"
      ]
    }
  ]
}
```
  AWS Managed: ViewOnly |
| he-database-nonprod | Perform development tasks in a non-production environment | Full access to database services | Customer Managed: he-database-nonprod 
```
{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Sid": "AllowDatabaseServicesReadOnly",
      "Effect": "Allow",
      "Action": [
        "docdb-elastic:GetCluster",
        "docdb-elastic:GetClusterSnapshot",
        "docdb-elastic:ListClusters",
        "docdb-elastic:ListClusterSnapshots"
      ],
      "Resource": [
        "arn:aws:docdb-elastic:*:*:cluster:*",
        "arn:aws:docdb-elastic:*:*:cluster-snapshot:*"
      ]
    },
    {
      "Sid": "AllowStorageReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetBucketVersioning",
        "s3:ListBucketVersions",
        "s3:GetObjectVersion",
        "fsx:DescribeFileSystems",
        "fsx:DescribeVolumes",
        "fsx:DescribeStorageVirtualMachines",
        "fsx:DescribeBackups"
      ],
      "Resource": [
        "arn:aws:s3:::*",
        "arn:aws:fsx:*:*:file-system/*",
        "arn:aws:fsx:*:*:volume/*",
        "arn:aws:fsx:*:*:storage-virtual-machine/*"
      ]
    },
    {
      "Sid": "AllowEC2VolumeReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVolumes",
        "ec2:DescribeVolumeStatus",
        "ec2:DescribeVolumeAttribute"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowCloudWatchReadOnly",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "cloudwatch:DescribeAlarms"
      ],
      "Resource": [
        "arn:aws:cloudwatch:*:*:alarm:*"
      ]
    },
    {
      "Sid": "AllowLambdaReadOnly",
      "Effect": "Allow",
      "Action": [
        "lambda:ListFunctions",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowDirectoryServiceReadOnly",
      "Effect": "Allow",
      "Action": [
        "ds:DescribeDirectories",
        "ds:GetDirectoryLimits"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowLogsReadOnly",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents",
        "logs:FilterLogEvents"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:/aws/docdb/*",
        "arn:aws:logs:*:*:log-group:/aws/lambda/*"
      ]
    },
    {
      "Sid": "AllowSNSReadOnly",
      "Effect": "Allow",
      "Action": [
        "sns:GetTopicAttributes",
        "sns:ListTopics"
      ],
      "Resource": [
        "arn:aws:sns:*:*:*"
      ]
    },
    {
      "Sid": "AllowSQSReadOnly",
      "Effect": "Allow",
      "Action": [
        "sqs:GetQueueAttributes",
        "sqs:ListQueues"
      ],
      "Resource": [
        "arn:aws:sqs:*:*:*"
      ]
    },
    {
      "Sid": "AllowEventsReadOnly",
      "Effect": "Allow",
      "Action": [
        "events:DescribeRule",
        "events:ListRules",
        "events:ListTargetsByRule"
      ],
      "Resource": [
        "arn:aws:events:*:*:rule/*"
      ]
    },
    {
      "Sid": "AllowKMSReadOnly",
      "Effect": "Allow",
      "Action": [
        "kms:DescribeKey",
        "kms:ListKeys",
        "kms:ListAliases"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowSecretsManagerReadOnly",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecrets"
      ],
      "Resource": "*"
    }
  ]
}
```
  AWS Managed: ViewOnly |
| he-database-prod | Perform database support tasks in production | Limited access to database services | Customer Managed: he-database-prod 
```json
{
  "Version": "October 17, 2012",
  "Statement": [

    {
      "Sid": "AllowDatabaseServicesReadOnly",
      "Effect": "Allow",
      "Action": [
        "docdb-elastic:GetCluster",
        "docdb-elastic:GetClusterSnapshot",
        "docdb-elastic:ListClusters",
        "docdb-elastic:ListClusterSnapshots"
      ],
      "Resource": [
        "arn:aws:docdb-elastic:*:*:cluster:*",
        "arn:aws:docdb-elastic:*:*:cluster-snapshot:*"
        ]
    },
    {
      "Sid": "AllowStorageReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetBucketVersioning",
        "s3:ListBucketVersions",
        "s3:GetObjectVersion",
        "fsx:DescribeFileSystems",
        "fsx:DescribeVolumes",
        "fsx:DescribeStorageVirtualMachines",
        "fsx:DescribeBackups"
      ],
      "Resource": [
        "arn:aws:s3:::*",
        "arn:aws:fsx:*:*:file-system/*",
        "arn:aws:fsx:*:*:volume/*",
        "arn:aws:fsx:*:*:storage-virtual-machine/*"
      ]
    },
    {
      "Sid": "AllowEC2VolumeReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVolumes",
        "ec2:DescribeVolumeStatus",
        "ec2:DescribeVolumeAttribute"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowCloudWatchReadOnly",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:DescribeAlarms",
        "cloudwatch:GetMetricStatistics"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowLambdaReadOnly",
      "Effect": "Allow",
      "Action": [
        "lambda:ListFunctions",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowDirectoryServiceReadOnly",
      "Effect": "Allow",
      "Action": [
        "ds:DescribeDirectories",
        "ds:GetDirectoryLimits"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowLogsReadOnly",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:/aws/docdb/*",
        "arn:aws:logs:*:*:log-group:/aws/lambda/*"
      ]
    },
    {
      "Sid": "AllowSNSReadOnly",
      "Effect": "Allow",
      "Action": [
        "sns:GetTopicAttributes",
        "sns:ListTopics"
      ],
      "Resource": [
        "arn:aws:sns:*:*:*"
      ]
    },
    {
      "Sid": "AllowSQSReadOnly",
      "Effect": "Allow",
      "Action": [
        "sqs:GetQueueAttributes",
        "sqs:ListQueues"
      ],
      "Resource": [
        "arn:aws:sqs:*:*:*"
      ]
    },
    {
      "Sid": "AllowEventsReadOnly",
      "Effect": "Allow",
      "Action": [
        "events:DescribeRule",
        "events:ListRules",
        "events:ListTargetsByRule"
      ],
      "Resource": [
        "arn:aws:events:*:*:rule/*"
      ]
    },
    {
      "Sid": "AllowKMSReadOnly",
      "Effect": "Allow",
      "Action": [
        "kms:DescribeKey",
        "kms:ListKeys",
        "kms:ListAliases"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowSecretsManagerReadOnly",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecrets"
      ],
      "Resource": "*"
    }
  ]
}
```
  AWS Managed: ViewOnly |
| he-devops-dev | Perform development and pipeline deployment tasks in non production |  | Customer Managed: he-database-prod 
```json
{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Sid": "AllowCoreComputeServices",
      "Effect": "Allow",
      "Action": [
        "autoscaling:*",
        "ec2:*",
        "ecr:*",
        "ecs:*",
        "elasticbeanstalk:*",
        "elasticloadbalancing:*",
        "eks:*",
        "lambda:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowStorageAndDatabase",
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "rds:*",
        "dynamodb:*",
        "elasticache:*",
        "redshift:*",
        "docdb-elastic:*",
        "fsx:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowDirectoryServiceForFSx",
      "Effect": "Allow",
      "Action": [
        "ds:DescribeDirectories",
        "ds:AuthorizeApplication",
        "ds:UnauthorizeApplication",
        "ds:GetDirectoryLimits"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowSessionManagerAndSystemsManager",
      "Effect": "Allow",
      "Action": [
        "ssm:StartSession",
        "ssm:TerminateSession",
        "ssm:ResumeSession",
        "ssm:SendCommand",
        "ssm:ListCommandInvocations",
        "ssm:DescribeInstanceInformation",
        "ssm:DescribeInstanceProperties",
        "ssm:GetCommandInvocation",
        "ssm:PutParameter",
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
        "ssm:DeleteParameter",
        "ssm:DescribeParameters",
        "ssm:AddTagsToResource",
        "ssm:ListTagsForResource",
        "ec2-instance-connect:SendSSHPublicKey"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowDevelopmentIAMOperations",
      "Effect": "Allow",
      "Action": [
        "iam:DeleteRole",
        "iam:UpdateRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRole",
        "iam:ListRoles",
        "iam:PassRole",
        "iam:CreateInstanceProfile",
        "iam:DeleteInstanceProfile",
        "iam:AddRoleToInstanceProfile",
        "iam:RemoveRoleFromInstanceProfile",
        "iam:CreatePolicy",
        "iam:DeletePolicy",
        "iam:GetPolicy",
        "iam:ListPolicies",
        "iam:CreatePolicyVersion",
        "iam:DeletePolicyVersion",
        "iam:GetPolicyVersion",
        "iam:ListPolicyVersions"
      ],
      "Resource": [
        "arn:aws:iam::*:role/lambda-*",
        "arn:aws:iam::*:role/ec2-*",
        "arn:aws:iam::*:role/ecs-*",
        "arn:aws:iam::*:role/eks-*",
        "arn:aws:iam::*:role/rds-*",
        "arn:aws:iam::*:role/docdb-elastic-*",
        "arn:aws:iam::*:role/elasticache-*",
        "arn:aws:iam::*:role/fsx-*",
        "arn:aws:iam::*:instance-profile/*",
        "arn:aws:iam::*:policy/*"
      ]
    },
    {
      "Sid": "AllowCreateRoleWithBoundary",
      "Effect": "Allow",
      "Action": "iam:CreateRole",
      "Resource": [
        "arn:aws:iam::*:role/lambda-*",
        "arn:aws:iam::*:role/ec2-*",
        "arn:aws:iam::*:role/ecs-*",
        "arn:aws:iam::*:role/eks-*",
        "arn:aws:iam::*:role/rds-*",
        "arn:aws:iam::*:role/docdb-elastic-*",
        "arn:aws:iam::*:role/elasticache-*",
        "arn:aws:iam::*:role/fsx-*"
      ],
      "Condition": {
        "StringEquals": {
          "iam:PermissionsBoundary": "arn:aws:iam::${aws:PrincipalAccount}:policy/he-service-boundary"
        }
      }
    },
    {
      "Sid": "AllowReadOnlyIAMOperations",
      "Effect": "Allow",
      "Action": [
        "iam:Get*",
        "iam:List*",
        "iam:GenerateServiceLastAccessedDetails"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowLimitedSecretsManager",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:CreateSecret",
        "secretsmanager:PutSecretValue",
        "secretsmanager:UpdateSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:TagResource"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:*"
    },
    {
      "Sid": "AllowKMSForDevelopment",
      "Effect": "Allow",
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey",
        "kms:CreateGrant",
        "kms:ListKeys",
        "kms:ListAliases"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": [
            "s3.*.amazonaws.com",
            "rds.*.amazonaws.com",
            "secretsmanager.*.amazonaws.com",
            "dynamodb.*.amazonaws.com",
            "elasticache.*.amazonaws.com",
            "ec2.*.amazonaws.com",
            "docdb-elastic.*.amazonaws.com",
            "ssm.*.amazonaws.com",
            "fsx.*.amazonaws.com",
            "eks.*.amazonaws.com"
          ]
        }
      }
    },
    {
      "Sid": "AllowCloudFormationAndInfrastructure",
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "cloudwatch:*",
        "cloudtrail:LookupEvents",
        "cloudtrail:GetTrailStatus", 
        "cloudtrail:DescribeTrails",
        "cloudtrail:GetEventSelectors",
        "cloudtrail:ListTrails",
        "logs:*",
        "sns:*",
        "sqs:*",
        "events:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowResourceTagging",
      "Effect": "Allow",
      "Action": [
        "tag:GetResources",
        "tag:GetTagKeys",
        "tag:GetTagValues",
        "tag:TagResources"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowXRayTracing",
      "Effect": "Allow",
      "Action": [
        "xray:GetTraceGraph",
        "xray:GetTraceSummaries",
        "xray:BatchGetTraces",
        "xray:GetServiceGraph",
        "xray:GetTimeSeriesServiceStatistics",
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords"
      ],
      "Resource": "*"
    }
  ]
}
```
  AWS Managed: ViewOnly |
| he-devops-nonprod | Perform development and pipeline deployment tasks in non production |  | AWS Managed: he-devops-nonprod 
```json
{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Sid": "AllowSessionManagerReadOnly",
      "Effect": "Allow",
      "Action": [
        "ssm:DescribeInstanceInformation",
        "ssm:DescribeInstanceProperties",
        "ssm:DescribeParameters",
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
        "ssm:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowEC2ReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ec2:DescribeInstanceAttribute",
        "ec2:DescribeImages",
        "ec2:DescribeSnapshots",
        "ec2:DescribeVolumes",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowCloudWatchLogsReadOnly",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents",
        "logs:FilterLogEvents",
        "logs:StartQuery",
        "logs:StopQuery",
        "logs:GetQueryResults"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowDatabaseServicesReadOnly",
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters",
        "rds:DescribeDBSubnetGroups",
        "rds:DescribeDBParameterGroups",
        "rds:DescribeDBClusterParameterGroups",
        "rds:DescribeDBSnapshots",
        "rds:DescribeDBClusterSnapshots",
        "rds:DescribeEventSubscriptions",
        "rds:DescribeEvents",
        "rds:ListTagsForResource",
        "docdb-elastic:GetCluster",
        "docdb-elastic:GetClusterSnapshot",
        "docdb-elastic:ListClusters",
        "docdb-elastic:ListClusterSnapshots",
        "docdb-elastic:ListPendingMaintenanceActions",
        "docdb-elastic:GetPendingMaintenanceAction",
        "docdb-elastic:ListTagsForResource",
        "elasticache:DescribeCacheClusters",
        "elasticache:DescribeReplicationGroups",
        "elasticache:DescribeCacheSubnetGroups",
        "elasticache:DescribeCacheParameterGroups",
        "elasticache:DescribeSnapshots",
        "elasticache:DescribeEvents",
        "elasticache:ListTagsForResource",
        "dynamodb:DescribeTable",
        "dynamodb:ListTables",
        "dynamodb:DescribeBackup",
        "dynamodb:ListBackups",
        "dynamodb:ListTagsOfResource",
        "redshift:DescribeClusters",
        "redshift:DescribeClusterSubnetGroups",
        "redshift:DescribeClusterParameterGroups",
        "redshift:DescribeClusterSnapshots",
        "redshift:DescribeEvents"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowStorageAndFileSystemsReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "s3:GetBucketVersioning",
        "s3:GetBucketPolicy",
        "s3:GetBucketTagging",
        "s3:GetBucketLogging",
        "s3:GetBucketNotification",
        "fsx:DescribeFileSystems",
        "fsx:DescribeBackups",
        "fsx:DescribeDataRepositoryTasks",
        "fsx:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowCloudWatchReadOnly",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:DescribeAlarms",
        "cloudwatch:DescribeAlarmsForMetric",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:GetMetricData",
        "cloudwatch:ListMetrics",
        "cloudwatch:ListDashboards",
        "cloudwatch:GetDashboard"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowKubernetesReadOnly",
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:DescribeNodegroup",
        "eks:ListNodegroups",
        "eks:DescribeAddon",
        "eks:ListAddons",
        "eks:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowComputeServicesReadOnly",
      "Effect": "Allow",
      "Action": [
        "lambda:ListFunctions",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:ListEventSourceMappings",
        "lambda:GetEventSourceMapping",
        "lambda:ListTags",
        "ecs:ListClusters",
        "ecs:DescribeClusters",
        "ecs:ListServices",
        "ecs:DescribeServices",
        "ecs:ListTasks",
        "ecs:DescribeTasks",
        "ecs:DescribeTaskDefinition",
        "ecs:ListTaskDefinitions",
        "ecr:DescribeRepositories",
        "ecr:ListImages",
        "ecr:DescribeImages",
        "ecr:GetRepositoryPolicy",
        "elasticbeanstalk:DescribeApplications",
        "elasticbeanstalk:DescribeEnvironments",
        "elasticbeanstalk:DescribeConfigurationSettings",
        "elasticbeanstalk:DescribeEvents",
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:DescribeLaunchConfigurations",
        "autoscaling:DescribeScalingActivities",
        "autoscaling:DescribePolicies",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:DescribeListeners",
        "elasticloadbalancing:DescribeRules",
        "elasticloadbalancing:DescribeTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowDirectoryServiceReadOnly",
      "Effect": "Allow",
      "Action": [
        "ds:DescribeDirectories",
        "ds:GetDirectoryLimits",
        "ds:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowInfrastructureReadOnly",
      "Effect": "Allow",
      "Action": [
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackResources",
        "cloudformation:DescribeStackEvents",
        "cloudformation:ListStacks",
        "cloudformation:GetTemplate",
        "cloudtrail:LookupEvents",
        "cloudtrail:GetTrailStatus",
        "cloudtrail:DescribeTrails",
        "cloudtrail:GetEventSelectors",
        "cloudtrail:ListTrails",
        "sns:ListTopics",
        "sns:GetTopicAttributes",
        "sns:ListSubscriptions",
        "sns:ListTagsForResource",
        "sqs:ListQueues",
        "sqs:GetQueueAttributes",
        "sqs:ListQueueTags",
        "events:ListRules",
        "events:DescribeRule",
        "events:ListTargetsByRule",
        "events:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowKMSReadOnly",
      "Effect": "Allow",
      "Action": [
        "kms:DescribeKey",
        "kms:ListKeys",
        "kms:ListAliases",
        "kms:GetKeyPolicy",
        "kms:GetKeyRotationStatus"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowIAMReadOnly",
      "Effect": "Allow",
      "Action": [
        "iam:GetRole",
        "iam:ListRoles",
        "iam:GetPolicy",
        "iam:ListPolicies",
        "iam:GetInstanceProfile",
        "iam:ListInstanceProfiles",
        "iam:ListAttachedRolePolicies",
        "iam:ListRolePolicies",
        "iam:GetRolePolicy"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowSecretsManagerReadOnly",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecrets"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyDataAccess",
      "Effect": "Deny",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "rds:DownloadDBLogFilePortion",
        "rds:DownloadCompleteDBLogFile",
        "dynamodb:GetItem",
        "dynamodb:BatchGetItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "redshift:GetClusterCredentials",
        "redshift-data:*",
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowSessionManagerOnly",
      "Effect": "Allow",
      "Action": [
        "ssm:StartSession",
        "ssm:TerminateSession",
        "ssm:ResumeSession"
      ],
      "Resource": [
        "arn:aws:ec2:*:*:instance/*",
        "arn:aws:ssm:*:*:session/*"
      ]
    },
    {
      "Sid": "AllowResourceTaggingReadOnly",
      "Effect": "Allow",
      "Action": [
        "tag:GetResources",
        "tag:GetTagKeys",
        "tag:GetTagValues"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowXRayReadOnly",
      "Effect": "Allow",
      "Action": [
        "xray:GetTraceGraph",
        "xray:GetTraceSummaries",
        "xray:BatchGetTraces",
        "xray:GetServiceGraph",
        "xray:GetTimeSeriesServiceStatistics"
      ],
      "Resource": "*"
    }
  ]
}
```
  AWS Managed: ViewOnly |
| he-devops-prod | Perform devops support tasks in production | Read-only access | ReadOnly(AWS managed policy) |
| he-manage-prod | Perform support tasks in production | Full access to AWS services and resources | Customer Managed: he-manage-prod 
```json
{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Sid": "AllowSessionManagerReadOnly",
      "Effect": "Allow",
      "Action": [
        "ssm:DescribeInstanceInformation",
        "ssm:DescribeInstanceProperties",
        "ssm:DescribeParameters",
        "ssm:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowEC2ReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ec2:DescribeImages",
        "ec2:DescribeSnapshots",
        "ec2:DescribeVolumes",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowCloudWatchLogsReadOnly",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowDatabaseServicesReadOnly",
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters",
        "rds:DescribeEvents",
        "docdb-elastic:GetCluster",
        "docdb-elastic:GetClusterSnapshot",
        "docdb-elastic:ListClusters",
        "docdb-elastic:ListClusterSnapshots",
        "docdb-elastic:ListPendingMaintenanceActions",
        "docdb-elastic:GetPendingMaintenanceAction",
        "docdb-elastic:ListTagsForResource",
        "elasticache:DescribeCacheClusters",
        "elasticache:DescribeReplicationGroups",
        "elasticache:DescribeEvents",
        "dynamodb:DescribeTable",
        "dynamodb:ListTables",
        "redshift:DescribeClusters",
        "redshift:DescribeEvents"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowStorageReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "s3:GetBucketTagging",
        "fsx:DescribeFileSystems",
        "fsx:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowCloudWatchReadOnly",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:DescribeAlarms",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "cloudwatch:ListDashboards",
        "cloudwatch:GetDashboard"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowComputeServicesReadOnly",
      "Effect": "Allow",
      "Action": [
        "lambda:ListFunctions",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "ecs:ListClusters",
        "ecs:DescribeClusters",
        "ecs:ListServices",
        "ecs:DescribeServices",
        "ecs:ListTasks",
        "ecs:DescribeTasks",
        "ecr:DescribeRepositories",
        "ecr:ListImages",
        "elasticbeanstalk:DescribeApplications",
        "elasticbeanstalk:DescribeEnvironments",
        "autoscaling:DescribeAutoScalingGroups",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeTargetGroups"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowInfrastructureReadOnly",
      "Effect": "Allow",
      "Action": [
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackResources",
        "cloudformation:ListStacks",
        "cloudtrail:LookupEvents",
        "cloudtrail:GetTrailStatus",
        "cloudtrail:DescribeTrails",
        "sns:ListTopics",
        "sns:GetTopicAttributes",
        "sqs:ListQueues",
        "sqs:GetQueueAttributes",
        "events:ListRules",
        "events:DescribeRule"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowKMSReadOnly",
      "Effect": "Allow",
      "Action": [
        "kms:DescribeKey",
        "kms:ListKeys",
        "kms:ListAliases"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowIAMReadOnly",
      "Effect": "Allow",
      "Action": [
        "iam:GetRole",
        "iam:ListRoles",
        "iam:GetPolicy",
        "iam:ListPolicies"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowSecretsManagerReadOnly",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecrets"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowResourceTaggingReadOnly",
      "Effect": "Allow",
      "Action": [
        "tag:GetResources",
        "tag:GetTagKeys",
        "tag:GetTagValues"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowXRayReadOnly",
      "Effect": "Allow",
      "Action": [
        "xray:GetTraceGraph",
        "xray:GetTraceSummaries",
        "xray:BatchGetTraces",
        "xray:GetServiceGraph"
      ],
      "Resource": "*"
    }
  ]
}
```
  AWS Managed: ViewOnly |
|  |  |  |  |
|  |  |  |  |
| he-sandbox-admin | full admin access to sandbox accounts | Admin Access | AWS Managed: AdministratorAccess |

#### Role Specific

At present, there are no Trust Policies identified for roles except for the Break Glass role should it be required.

| Role | Purpose | Capabilities | Trust Policy | Access Policy |
| --- | --- | --- | --- | --- |
| he-role-breakglass | Emergency access in case Okta is down | Full access to AWS services and resources | Customer Managed: he-role-breakglass Trust Policy "Version": "October 17, 2012",  "Statement": \[  {  "Effect": "Allow",  "Principal": {  "AWS": "arn:aws:iam::<ManagementAccountID>:user/<Namespace>-user-breakglass"  },  "Action": "sts:AssumeRole",  "Condition": {  "Bool": {  "aws:MultiFactorAuthPresent": "true"  }  }  }  \]  } | AWS Managed: AdministratorAccess |
| he-role-viewonly | Low risk access into an AWS environment without the ability to read data sources | Provides access to configuration, meta, and log information. |  | AWS Managed: View-Only |
| he-role-readonly | Access into an AWS environment with the ability to view data sources | Provides read access to all services and resources within an AWS account |  | AWS Managed: Read-Only |
| he-finops-mgmt | This role is designed for users who need to manage AWS financial operations, cost optimization, and marketplace activities. | * **Marketplace Management**: Approve and manage AWS Marketplace software purchases and subscriptions * **Budget Administration**: Create, modify, and manage AWS budgets and budget actions * **Cost Analysis**: Access detailed billing and cost data for financial reporting * **Savings Plans**: Purchase and manage AWS Savings Plans for cost optimization * **Billing Operations**: Handle billing conductor configurations and cost allocation |  | Customer Managed:  HE-FinOps-Reporting  AWS Managed:  AWSBillingConductorFullAccess  AWSBudgetsActions\_RolePolicyForResouceAdministrationWithSSM  AWSMarketPlaceFullAccess  AWSSavingsPlansFullAccess  Billing  ComuteOptimizerReadOnlyAccess  CostOptimizationHubAdminAccess |
| he-role-networkops | Access for troubleshooting and fixing networking issues | Provides access to support troubleshooting network issues |  | Customer Managed: he-role-networkops 
```json
{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Sid": "VPCManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateVpc",
        "ec2:DeleteVpc",
        "ec2:ModifyVpcAttribute",
        "ec2:DescribeVpcs",
        "ec2:CreateSubnet",
        "ec2:DeleteSubnet",
        "ec2:ModifySubnetAttribute",
        "ec2:DescribeSubnets",
        "ec2:CreateRouteTable",
        "ec2:DeleteRouteTable",
        "ec2:CreateRoute",
        "ec2:DeleteRoute",
        "ec2:AssociateRouteTable",
        "ec2:DisassociateRouteTable",
        "ec2:DescribeRouteTables"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SecurityGroupManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateSecurityGroup",
        "ec2:DeleteSecurityGroup",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:UpdateSecurityGroupRuleDescriptionsIngress",
        "ec2:UpdateSecurityGroupRuleDescriptionsEgress",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSecurityGroupRules"
      ],
      "Resource": "*"
    },
    {
      "Sid": "NetworkConnectivity",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateVpcPeeringConnection",
        "ec2:DeleteVpcPeeringConnection",
        "ec2:AcceptVpcPeeringConnection",
        "ec2:RejectVpcPeeringConnection",
        "ec2:DescribeVpcPeeringConnections",
        "ec2:CreateVpnGateway",
        "ec2:DeleteVpnGateway",
        "ec2:AttachVpnGateway",
        "ec2:DetachVpnGateway",
        "ec2:DescribeVpnGateways",
        "ec2:CreateCustomerGateway",
        "ec2:DeleteCustomerGateway",
        "ec2:DescribeCustomerGateways",
        "ec2:CreateVpnConnection",
        "ec2:DeleteVpnConnection",
        "ec2:DescribeVpnConnections"
      ],
      "Resource": "*"
    },
    {
      "Sid": "NetworkMonitoring",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeAddresses",
        "ec2:DescribeNetworkAcls",
        "ec2:DescribeDhcpOptions",
        "ec2:DescribeFlowLogs",
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Sid": "LoadBalancerManagement",
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "NetworkFirewall",
      "Effect": "Allow",
      "Action": [
        "network-firewall:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "TagManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateTags",
        "ec2:DeleteTags"
      ],
      "Resource": "*"
    }
  ]
}
```
  AWS Managed: ViewOnly |
|  |  |  |  |  |