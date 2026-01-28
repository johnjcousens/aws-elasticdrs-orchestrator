# DRS Permissions Audit - Complete EC2 Permissions for All Operations

## Issue
DRS recovery operations were failing with error:
```
UnauthorizedOperation when calling DeleteLaunchTemplateVersions operation
```

**Failed Execution Details:**
- Execution ID: `7c03f004-047d-457b-b3e8-d3999e2fa7aa`
- DRS Job ID: `drsjob-51ef622e9a41c2ff4` (us-west-2)
- Servers: WINDBSRV01, WINDBSRV02
- Error: Lambda execution role lacked `ec2:DeleteLaunchTemplateVersions` permission

## Root Cause
The Lambda execution role in `cfn/master-template.yaml` was missing several EC2 permissions required by AWS DRS for complete failover, failback, and agent installation operations.

## Solution
Added comprehensive EC2 permissions based on AWS managed policy `AWSElasticDisasterRecoveryServiceRolePolicy` (v8).

## Permissions Added

### Image Operations (for DRS drill conversions)
- `ec2:RegisterImage` - Register AMIs from converted instances
- `ec2:DeregisterImage` - Clean up temporary AMIs

### Network Interface Operations
- `ec2:CreateNetworkInterface` - Create ENIs for recovery instances
- `ec2:DeleteNetworkInterface` - Clean up ENIs after termination
- `ec2:ModifyNetworkInterfaceAttribute` - Configure ENI attributes
- `ec2:CreateNetworkInterfacePermission` - Grant ENI permissions

### VPC Networking Operations (for DRS source network recovery)
- `ec2:DescribeVpcAttribute` - Query VPC configuration
- `ec2:DescribeInternetGateways` - Identify internet connectivity
- `ec2:DescribeNetworkAcls` - Query network ACL rules
- `ec2:DescribeRouteTables` - Query routing configuration
- `ec2:DescribeDhcpOptions` - Query DHCP settings
- `ec2:DescribeManagedPrefixLists` - Query managed prefix lists
- `ec2:GetManagedPrefixListEntries` - Get prefix list entries
- `ec2:GetManagedPrefixListAssociations` - Get prefix list associations

### Volume Operations
- `ec2:DescribeVolumeAttribute` - Query volume attributes (encryption, etc.)

### CloudWatch Operations
- `cloudwatch:GetMetricData` - Required by DRS for monitoring replication lag

## Verification

### Current Permissions (After Fix)
The Lambda execution role now includes ALL EC2 permissions from `AWSElasticDisasterRecoveryServiceRolePolicy`:

**Instance Operations:** DescribeInstances, DescribeInstanceStatus, DescribeInstanceTypes, DescribeInstanceAttribute, DescribeInstanceTypeOfferings, StartInstances, StopInstances, TerminateInstances, ModifyInstanceAttribute, GetConsoleOutput, GetConsoleScreenshot, RunInstances

**Volume Operations:** DescribeVolumes, DescribeVolumeAttribute, CreateVolume, DeleteVolume, AttachVolume, DetachVolume, ModifyVolume

**Snapshot Operations:** DescribeSnapshots, CreateSnapshot, DeleteSnapshot

**Image Operations:** DescribeImages, RegisterImage, DeregisterImage

**Network Operations:** DescribeSecurityGroups, CreateSecurityGroup, AuthorizeSecurityGroupIngress, AuthorizeSecurityGroupEgress, RevokeSecurityGroupEgress, DescribeSubnets, DescribeVpcs, DescribeVpcAttribute, DescribeNetworkInterfaces, CreateNetworkInterface, DeleteNetworkInterface, ModifyNetworkInterfaceAttribute, CreateNetworkInterfacePermission

**VPC Networking:** DescribeInternetGateways, DescribeNetworkAcls, DescribeRouteTables, DescribeDhcpOptions, DescribeManagedPrefixLists, GetManagedPrefixListEntries, GetManagedPrefixListAssociations

**Launch Templates:** CreateLaunchTemplate, CreateLaunchTemplateVersion, DescribeLaunchTemplates, DescribeLaunchTemplateVersions, ModifyLaunchTemplate, DeleteLaunchTemplate, DeleteLaunchTemplateVersions

**Tags:** CreateTags, DeleteTags, DescribeTags

**Availability:** DescribeAvailabilityZones, DescribeAccountAttributes, DescribeCapacityReservations, DescribeHosts, DescribeKeyPairs

**Encryption:** GetEbsEncryptionByDefault, GetEbsDefaultKmsKeyId

### Cross-Account Role Comparison
The cross-account role in `cfn/cross-account-role-stack.yaml` already had comprehensive permissions and did not require updates.

## DRS Operations Coverage

### Failover Operations ✅
- Launch recovery instances from replication snapshots
- Create and manage launch templates
- Attach volumes to recovery instances
- Configure network interfaces
- Register AMIs for drill conversions

### Failback Operations ✅
- Reverse replication from DR to primary region
- Start failback launch
- Manage failback instances
- Clean up temporary resources

### Agent Installation ✅
- Query instance metadata
- Configure security groups
- Manage network interfaces
- Access instance console output

### Drill Operations ✅
- Convert recovery instances to AMIs
- Register and deregister images
- Create snapshots for testing
- Clean up drill resources

## Testing Required
1. Deploy updated CloudFormation template to dev environment
2. Execute DRS recovery operation for test servers
3. Verify no UnauthorizedOperation errors
4. Confirm successful recovery instance launch
5. Test drill conversion (snapshot to AMI)
6. Test failback operations

## Files Modified
- `infra/orchestration/drs-orchestration/cfn/master-template.yaml` (lines 220-310)

## Reference
- AWS Managed Policy: [AWSElasticDisasterRecoveryServiceRolePolicy](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AWSElasticDisasterRecoveryServiceRolePolicy.html)
- Policy Version: v8
- Last Updated: 2026-01-24
