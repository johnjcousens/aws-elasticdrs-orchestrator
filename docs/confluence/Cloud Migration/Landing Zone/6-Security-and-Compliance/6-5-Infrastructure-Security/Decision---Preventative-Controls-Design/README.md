# Decision---Preventative-Controls-Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867034025/Decision---Preventative-Controls-Design

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:34 AM

---

### Document Lifecycle Status

**Purpose**
-----------

This document outlines AWS Organizations Service Control Policies(SCPs) which will be implemented across AWS Accounts.

**Decision**
------------

### ControlTower Mandatory SCPs for all OUs

The following SCPs will be created and enforced by Control Tower for all accounts under all AWS Organizations' OUs.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table><tbody><tr><th rowspan="2">
<span><strong>Service Control Policy Name</strong></span></th><td rowspan="2">
<span><strong>Effect</strong></span></td><td colspan="2"><span><strong>Conditions</strong></span></td><td colspan="4"><span><strong>Actions</strong></span></td><td rowspan="2">
<span><strong>Resource</strong></span></td></tr><tr><td><span><strong>1</strong></span></td><td><span><strong>2</strong></span></td><td><span><strong>1</strong></span></td><td><span><strong>2</strong></span></td><td><span><strong>3</strong></span></td><td><span><strong>4</strong></span> </td></tr><tr><th><span><strong>CloudTrail Enabled</strong></span></th><td><span>Deny</span></td><td><span>Applies for all except for principal ARNs matching "arn:aws:iam::\*:role/AWSControlTowerExecution"</span></td><td><br/></td><td><span>Update or Delete Cloudtrail</span></td><td><span>Put Event Selectors</span></td><td><span>Stop Logging</span></td><td><br/></td><td><span>Any</span></td></tr><tr><th><span><strong>Config Enabled</strong></span></th><td><span>Deny</span></td><td><span>Applies for all except for principal ARNs matching "arn: aws:iam::\*:role /AWSControlTowerExecution</span></td><td><br/></td><td><span>Delete / Put / Stop Config Configuration recorder</span></td><td><span>Delete / Put Config Delivery Channel</span></td><td><span>Delete / Put Config Retention Configuration</span></td><td><br/></td><td><span>Any</span></td></tr><tr><th><span><strong>Config Rule Policy</strong></span></th><td><span>Deny</span></td><td><span>Applies for all except for principal ARNs matching "arn: aws:iam::\*:role /AWSControlTowerExecution</span></td><td><span>Applies for all where string for tag matching "aws:ResourceTag /aws-control-tower": "managed- by-control-tower"</span></td><td><span>Put / Delete Config Rule</span></td><td><span>Put / Delete Config Configuration Aggregator</span></td><td><span>Delete Evaluation results</span></td><td><br/></td><td><span>Any</span></td></tr><tr><th><span><strong>Config Rule Tags Policy</strong></span></th><td><span>Deny</span></td><td><span>Applies for all except for principal ARNs matching "arn:aws:iam::\*:role/AWSControlTowerExecution</span></td><td><span>Applies for all values where string for tag key matching "aws-control-tower"</span></td><td><span>Tag / Untag Config Resource</span></td><td><br/></td><td><br/></td><td><br/></td><td><span>Any</span></td></tr><tr><th><span><strong>CloudWatch Event Policy</strong></span></th><td><span>Deny</span></td><td><span>Applies for all except for principal ARNs matching "arn:aws:iam::\*:role/AWSControlTowerExecution"</span></td><td><br/></td><td><span>Put / Delete / Disable CloudWatch Rule</span></td><td><span>Put / Remove Targets of CloudWatch</span> </td><td><br/></td><td><br/></td><td><span>Any resources matching:</span> <span>"arn:aws:events:\*:\*:rule/aws-controltower-\*"</span></td></tr><tr><th><span><strong>Lambda Function Policy</strong></span></th><td><span>Deny</span></td><td><span>Applies for all except for principal ARNs matching "arn:aws:iam::\*:role/AWSControlTowerExecution"</span></td><td><br/></td><td><span>Create / Delete / Update Lambda Event Source Mapping</span></td><td><span>Create / Delete / Update Code / Update Configuration  Lambda Function</span></td><td><span>Delete / Put Lambda Function Concurrency</span> </td><td><span>Add / Remove Lambda Function Permission</span></td><td><span>Any resources matching:</span> <span>"arn:aws:lambda:\*:\*:function:aws-controltower-\*"</span></td></tr><tr><th><span><strong>SNS Subscription Policy</strong></span></th><td><span>Deny</span></td><td><span>Applies for all except for principal ARNs matching "arn:aws:iam::\*:role/AWSControlTowerExecution</span></td><td><br/></td><td><span>Subscribe / Unsubscribe SNS topic</span></td><td><br/></td><td><br/></td><td><br/></td><td><span>Any resource matching:</span> <span>"arn:aws:sns:\*:\*:aws-controltower-SecurityNotifications"</span></td></tr><tr><th><span><strong>SNS Topic Policy</strong></span> </th><td><span>Deny</span></td><td><span>Applies for all except for principal ARNs matching "arn:aws:iam::\*:role/AWSControlTowerExecution</span></td><td><br/></td><td><span>Create / Delete SNS Topic</span></td><td><span>Add / Remove SNS Permissions</span> </td><td><span>Set SNS Topic Attributes</span></td><td><br/></td><td><span>Any resource matching:</span> <span>"arn:aws:sns:\*:\*:aws-controltower-\*"</span></td></tr><tr><th><span><strong>IAM Role Policy</strong></span> </th><td><span>Deny</span></td><td><span>Applies for all except for principal ARNs matching "arn:aws:iam::\*:role/AWSControlTowerExecution</span></td><td><br/></td><td><span>Attach / Delete / Detach / Put IAM Role Policy</span> </td><td><span>Create / Delete / Update / Update Description of IAM Role</span></td><td><span>Delete / Put IAM Role Permission Boundary</span></td><td><span>Update IAM Assume Role Policy</span> </td><td><span>Any resource matching:</span> <span>"arn:aws:iam::\*:role/aws-controltower-\*" or  "arn:aws:iam::\*:role/\*AWSControlTower\*"</span></td></tr></tbody></table>



ControlTower Mandatory SCPs for Core OU

The following SCPs are create and enforced by Control Tower for all accounts under all AWS Organizations' Core OU.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table><tbody><tr><th rowspan="2">
<span><strong>Service Control Policy Name</strong></span></th><td rowspan="2">
<span><strong>Effect</strong></span></td><td colspan="2"><span><strong>Conditions</strong></span></td><td colspan="4"><span><strong>Actions</strong></span></td><td rowspan="2">
<span><strong>Resource</strong></span></td></tr><tr><td><span><strong>1</strong></span></td><td><span><strong>2</strong></span></td><td><span><strong>1</strong></span></td><td><span><strong>2</strong></span></td><td><span><strong>3</strong></span></td><td><span><strong>4</strong></span> </td></tr><tr><th><span><strong>Log Archive Bucket Encryption Enabled</strong></span></th><td><span>Deny</span></td><td><span>Applies for all except for principal ARNs matching "arn:aws:iam::\*:role/AWSControlTowerExecution"</span></td><td><br/></td><td><span>Put Encryption Configuration for S3</span></td><td><br/></td><td><br/></td><td><br/></td><td><span>Any</span></td></tr><tr><th><span><strong>Log Archive Bucket Logging Enabled</strong></span></th><td><span>Deny</span></td><td><span>Applies for all except for principal ARNs matching "arn:aws:iam::\*:role/AWSControlTowerExecution"</span></td><td><br/></td><td><span>Put Bucket Logging for S3</span></td><td><br/></td><td><br/></td><td><br/></td><td><span>Any</span></td></tr><tr><th><span><strong>Log Archive Bucket Policy Changes Prohibited</strong></span></th><td><span>Deny</span></td><td><span>Applies for all except for principal ARNs matching "arn:aws:iam::\*:role/AWSControlTowerExecution"</span></td><td><br/></td><td><span>Put Bucket Policy for S3</span></td><td><br/></td><td><br/></td><td><br/></td><td><span>Any</span></td></tr><tr><th><span><strong>Log Archive Bucket Retention Policy</strong></span> </th><td><span>Deny</span></td><td><span>Applies for all except for principal ARNs matching "arn:aws:iam::\*:role/AWSControlTowerExecution"</span></td><td><br/></td><td><span>Put Lifecycle Configuration for S3</span></td><td><br/></td><td><br/></td><td><br/></td><td><span>Any</span></td></tr></tbody></table>



#### Sample Custom SCPs for All OUs

Use the following table to document any Service Control Policies (SCPs) that are to be implemented through Landing Zone Accelerator



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<td rowspan="2">
<span><strong>Service Control Policy Name</strong></span>

</td>
<td rowspan="2">
<span><strong>Effect</strong></span>

</td>
<td colspan="2">
<span><strong>Conditions</strong></span>

</td>
<td>
<span><strong>Actions</strong></span>
<br/>
<br/>

</td>
<td rowspan="2">
<span><strong>Resource</strong></span>

</td>
<td rowspan="2">
<span><strong>Enable?</strong></span>

</td>
</tr>
<tr>
<td>
<span><strong>1</strong></span>

</td>
<td>
<span><strong>2</strong></span>

</td>
<td>
<span><strong>1</strong></span>

</td>
</tr>
<tr>
<td>
<span><strong>IAM User Creation</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>

<br/>

</td>
<td>
<span>Except for principal ARNs matching:</span> 
<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

</td>
<td>
<span>CreateUser</span>

</td>
<td>
<span>Any</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>1</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>Allowed Regions</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>
<span>Except for us-west-2</span>

</td>
<td>
<span>Except for principal ARNs matching:</span> 
<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>
<br/><span>"arn:aws:iam::\*:role/service-role/AWSControlTowerAdmin"</span>
<br/><span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-lambda-delete-default-vpc"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-saml-administrator"</span>

</td>
<td>
<span>All \*</span>

</td>
<td>
<span>Any</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>2</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>GuardDuty Enabled</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>

<br/>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>
<br/><span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-crossaccount-securitybaseline"</span>

</td>
<td>
<span>DeleteDetector</span>

<span>UpdateDetector</span>

<span>StopMonitoringMembers</span>

<span>DeleteMembers</span>

<span>DisassociateMembers</span>

<span>DisassociateFromManagementAccount</span>

</td>
<td>
<span>Any</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>3</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>SecurityHub Enabled</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>

<br/>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-crossaccount-securitybaseline"</span>

</td>
<td>
<span>DisableSecurityHub</span>

<span>DeleteMembers</span>

<span>DisassociateMembers</span>

<span>DisassociateFromManagementAccount</span>

</td>
<td>
<span>Any</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>4</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>Access Analyzer Enabled</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>

<br/>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

</td>
<td>
<span>DeleteAnalyzer</span>

</td>
<td>
<span>Any resources matching:</span>

<span>"arn:aws:access-analyzer:\*:\*:analyzer/&lt;Namespace&gt;-\*"</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>5</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>Custom CloudWatch Events Persist</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>

<br/>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

</td>
<td>
<span>Put / Delete / Disable CloudWatch Rule</span>

<span>Put / Remove Targets of CloudWatch</span>

</td>
<td>
<span>Any resources matching:</span>

<span>"arn:aws:events:\*:\*:rule/&lt;Namespace&gt;-\*"</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>6</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>Custom CloudWatch Alarms Persist</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>

<br/>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

</td>
<td>
<span>DeleteAlarms</span>

<span>EnableAlarmActions</span>

<span>DisableAlarmActions</span>

<span>PutMetricAlarm</span>

<span>SetAlarmState</span>

</td>
<td>
<span>Any resources matching:</span>

<span>"arn:aws:cloudwatch:\*:\*: alarm :&lt;Namespace&gt;-\*"</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>7</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>Custom Confg Rules Persist</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>
<span>Applies for all where string for tag matching "aws: ResourceTag/baseline":"managed-resource"</span>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

<span>"arn:aws:iam::\*:role/aws-controltower-\*"</span>

</td>
<td>
<span>Put / Delete Config Rule</span>

<span>Delete Evaluation results</span>

</td>
<td>
<span>Any</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>8</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>Custom Confg Rules Tags Persist</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>
<span>Applies for all values where string for tag key matching</span>

<span>"baseline"</span>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-lambda--configruletagging-\*"</span>

</td>
<td>
<span>TagResource</span>

<span>UnTagResource</span>

</td>
<td>
<span>Any</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>9</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>Centrally managed Lambda Functions Persist</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>

<br/>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-service-catalog"</span>

</td>
<td>
<span>Create / Delete /</span>

<span>Update Lambda Event Source Mapping</span>

<span>Create / Delete / Update Code / Update Configuration Lambda Function</span>

<span>Delete / Put Lambda Function Concurrency</span>

<span>Add / Remove Lambda Function Permission</span>

</td>
<td>
<span>Any resources matching:</span>

<span>"arn:aws:lambda:\*:\*: function:&lt;Namespace&gt;-\*"</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>10</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>Centrally managed application IAM Roles Persist</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>

<br/>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

<span>"arn:aws:iam::\*:role/aws-controltower-\*"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-breakglass"</span> 
<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-service-catalog"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-saml-administrator"</span>

</td>
<td>
<span>AttachRolePolicy</span>

<span>DetachRolePolicy</span>

<span>UpdateAssumeRolePolicy</span>

<span>DeleteRole</span>

<span>UpdateRole</span>

<span>UpdateRoleDescription</span>

<span>DeleteRolePolicy</span>

<span>PutRolePolicy</span>

</td>
<td>
<span>Any resources matching:</span>

<span>"arn:aws:iam::\*:\*/&lt;Namespace&gt;-\*"</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>11</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>IAM Password Policy Persist</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>

<br/>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>
<br/><span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-lambda-iampasswordpolicy"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-crossaccount-securitybaseline"</span>

</td>
<td>
<span>Delete/Update IAM password Policy</span>

</td>
<td>
<span>Any</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>12</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>IAM IdP Persists</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>

<br/>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

<span>"arn:aws:iam::\*:role/aws-controltower-\*"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-breakglass"</span> 
<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-service-catalog"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-saml-administrator"</span>

</td>
<td>
<span>CreateSAMLProvider</span>

<span>DeleteSAMLProvider</span>

<span>UpdateSAMLProvider</span>

</td>
<td>
<span>Any resources matching:</span>

<span>"arn:aws:iam::\*:\*/&lt;Namespace&gt;-\*"</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>13</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>Centrally managed CloudFormation Stacks Persist</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>

<br/>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-saml-administrator"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-service-catalog"</span>

</td>
<td>
<span>Create\*</span>

<span>Delete\*</span>

<span>Update\*</span>

<span>SetStackPolicy</span>

</td>
<td>
<span>Any resources matching:</span>
<br/><span>"arn:aws:cloudformation:\*:\*:stack/&lt;Namespace&gt;\*",</span>
<br/><span>"arn:aws:cloudformation:\*:\*:stack/CustomControlTower-\*",</span>
<br/><span>"arn:aws:cloudformation:\*:\*:stack/StackSet-CustomControlTower-\*"</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>14</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>Centrally managed SSM Parameters Persist</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>

<br/>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

</td>
<td>
<span>Delete parameters</span>

</td>
<td>
<span>Any resources matching:</span>
<br/><span>"arn:aws:ssm:\*:\*:parameter/&lt;Namespace&gt;/\*"</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>15</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>Default SG configurations Persist</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>
<span>Applies for all where string for tag matching "aws: ResourceTag/baseline":"managed-resource"</span>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-saml-administrator"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-saml-securityresponse"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-lambda-cleanupdefaultsg-\*"</span>

<span>arn:aws:iam::\*:role/&lt;Namespace&gt;-role-service-catalog"</span>

</td>
<td>
<span>AuthorizeSecurityGroupEgress</span>

<span>AuthorizeSecurityGroupIngress</span>

<span>DeleteSecurityGroup</span>

</td>
<td>
<span>Any</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>16</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>Automation tags configurations Persist</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>
<span>Applies for all values where string for tag key matching</span>

<span>"baseline", "Associate-with", "Propagate-to", "Attach-to-tgw",</span>

<span>"backup","patch","availability\_zone"</span>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-saml-administrator"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-lambda-configruletagging-\*"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-lambda-cleanupdefaultsg-\*"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-service-catalog"</span>

</td>
<td>
<span>CreateTags</span>

<span>DeleteTags</span>

</td>
<td>
<span>Any</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>17</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>WAF Logs Kinesis Firehose Persist</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>

<br/>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-saml-administrator"</span>

</td>
<td>
<span>DeleteDeliveryStream</span>

<span>StopDeliveryStreamEncryption</span>

<span>UpdateDestination</span>

</td>
<td>
<span>Any resources matching:</span>
<br/><span>"arn:aws:firehose:\*:\*:deliverystream/aws-waf-logs-kinesis-baseline"</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>18</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>WAF Firewall Manager Policy Persists</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>
<span>Applies for all where string for tag matching "aws: ResourceTag/baseline":"managed-resource"</span>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

<span>"arn:aws:iam::\*:role/&lt;Namespace&gt;-role-saml-administrator"</span>

</td>
<td>
<span>DeletePolicy</span>

<span>PutPolicy</span>

</td>
<td>
<span>Any</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>19</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
<tr>
<td>
<span><strong>WAF Firewall Manager Policy Tag Persists</strong></span>

</td>
<td>
<span>Deny</span>

</td>
<td>
<span>Applies for all values where string for tag key matching</span>

<span>"baseline"</span>

</td>
<td>
<span>Except for principal ARNs matching:</span>

<span>"arn:aws:iam::\*:role/AWSControlTowerExecution"</span>

</td>
<td>
<span>TagResource</span>

<span>UnTagResource</span>

</td>
<td>
<span>Any</span>

</td>
<td>
<ac:task-list>
<ac:task>
<ac:task-id>20</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
</ac:task>
</ac:task-list> </td>
</tr>
</tbody>
</table>



**Note:** Some AWS services do not have [endpoints](https://docs.aws.amazon.com/general/latest/gr/rande.html) in the us-east-1 region, therefore, if [CUSTOMER] plans on using these services in the future, they should be added to the "NotAction" element of the "GRALLOWEDREGIONS" statement.

### **AMS Accelerate Access**

If using AMS Accelerate, a number of API calls will need to be allowed at the SCP layer in [Customer]'s organization to allow automated tooling to scan the environment. The following exceptions will need to be made if there are any Deny statements blocking general API service calls like EC2 or SSM.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table><tbody><tr><th rowspan="2">
<span><strong>Service Control Policy Name</strong></span></th><td rowspan="2">
<span><strong>Effect</strong></span></td><td colspan="2"><span><strong>Conditions</strong></span></td><td colspan="4"><span><strong>Actions</strong></span></td><td rowspan="2">
<span><strong>Resource</strong></span></td></tr><tr><td><span><strong>1</strong></span></td><td><span><strong>2</strong></span></td><td><span><strong>1</strong></span></td><td><span><strong>2</strong></span></td><td><span><strong>3</strong></span></td><td><span><strong>4</strong></span> </td></tr><tr><th><span><strong>SSM Maintenance Windows Policy</strong></span></th><td><span>Allow</span></td><td><span>Applies for all except for principal ARNs matching "arn:aws:iam::\*:role/aws\_managedservices\_onboarding\_role"</span></td><td><br/></td><td><span>Describe SSM Maintenance Window (ssm:DescribeMaintenanceWindow\*)</span></td><td><br/></td><td><br/></td><td><br/></td><td><span>Any</span></td></tr><tr><th><span><strong>EC2 Describe Policy</strong></span></th><td><span>Allow</span></td><td><span>Applies for all except for principal ARNs matching "arn: aws:iam::\*:role /<span>aws\_managedservices\_onboarding\_role"</span></span></td><td><br/></td><td><span>Describe EC2 Calls:</span><ul><li>DescribeImages</li><li>DescribeSecurityGroups</li><li>DescribeVpcs</li><li>DescribeVolumes</li><li>DescribeSnapshots</li><li>DescribeInstances</li><li>ReportInstanceStatus</li></ul></td><td><br/></td><td><br/></td><td><br/></td><td><span>Any</span></td></tr><tr><th colspan="1">RDS Policy</th><td colspan="1">Allow</td><td colspan="1"><span>Applies for all except for principal ARNs matching "arn: aws:iam::\*:role /<span>aws\_managedservices\_onboarding\_role"</span></span></td><td colspan="1"><br/></td><td colspan="1">RDS Describe DB Instances</td><td colspan="1"><br/></td><td colspan="1"><br/></td><td colspan="1"><br/></td><td colspan="1">Any</td></tr><tr><th colspan="1">AWS Config Rule Policy</th><td colspan="1">Allow</td><td colspan="1"><span>Applies for all except for principal ARNs matching "arn: aws:iam::\*:role /<span>aws\_managedservices\_onboarding\_role"</span></span></td><td colspan="1"><br/></td><td colspan="1">AWS Config API Calls:<ul><li>DescribeConfigRules</li><li>DescribeRemediationConfigurations</li><li>DescribeConformancePacks</li></ul></td><td colspan="1"><br/></td><td colspan="1"><br/></td><td colspan="1"><br/></td><td colspan="1">Any</td></tr><tr><th colspan="1">AWS Backup Policy</th><td colspan="1">Allow</td><td colspan="1"><span>Applies for all except for principal ARNs matching "arn: aws:iam::\*:role /<span>aws\_managedservices\_onboarding\_role"</span></span></td><td colspan="1"><br/></td><td colspan="1">Backup API Calls:<ul><li>ListBackupPlans</li><li>ListBackupVaults</li><li>GetBackupPlan</li></ul></td><td colspan="1"><br/></td><td colspan="1"><br/></td><td colspan="1"><br/></td><td colspan="1">Any</td></tr><tr><th colspan="1">AWS Organizations Policy</th><td colspan="1">Allow</td><td colspan="1"><span>Applies for all except for principal ARNs matching "arn: aws:iam::\*:role /<span>aws\_managedservices\_onboarding\_role"</span></span></td><td colspan="1"><br/></td><td colspan="1">ListPolicies and DescribePolicy</td><td colspan="1"><br/></td><td colspan="1"><br/></td><td colspan="1"><br/></td><td colspan="1">Any</td></tr><tr><th colspan="1">SSM Describe Policy</th><td colspan="1">Allow</td><td colspan="1"><span>Applies for all except for principal ARNs matching "arn: aws:iam::\*:role /<span>aws\_managedservices\_onboarding\_role"</span></span></td><td colspan="1"><br/></td><td colspan="1">DescribeInstanceInformation</td><td colspan="1"><br/></td><td colspan="1"><br/></td><td colspan="1"><br/></td><td colspan="1">Any</td></tr><tr><th colspan="1">Glue Policy</th><td colspan="1">Allow</td><td colspan="1"><span>Applies for all except for principal ARNs matching "arn: aws:iam::\*:role /<span>aws\_managedservices\_onboarding\_role"</span></span></td><td colspan="1"><div class="content-wrapper">If Glue Catalog Encryption is enabled, \[Customer\] will need to add permissions to the CMK to allow Change Record and Patch Reporting to deploy.<ac:structured-macro ac:macro-id="c92f052c-e443-4775-a526-5675694e2399" ac:name="code" ac:schema-version="1"><ac:parameter ac:name="title">Glue Policy</ac:parameter></ac:structured-macro></div></td><td colspan="1">kms:DescribeKeyglue:GetDataCatalogEncryptionSettings<br/></td><td colspan="1"><br/></td><td colspan="1"><br/></td><td colspan="1"><br/></td><td colspan="1">Any</td></tr></tbody></table>



### **AWS Control Tower Guardrails**

A guardrail is a high-level rule that provides ongoing governance for your overall AWS environment. It's expressed in plain language. Through guardrails, AWS Control Tower implements *preventive* or *detective* controls that help you govern your resources and monitor compliance across groups of AWS accounts. A guardrail applies to an entire organizational unit (OU), and every AWS account within the OU is affected by the guardrail. Therefore, when users perform work in any AWS account in your landing zone, they're always subject to the guardrails that are governing their account's OU.

#### Control Tower Mandatory Guardrails

| Name | Guidance | Category | Behavior |
| --- | --- | --- | --- |
| [Disallow deletion of log archive](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#disallow-audit-bucket-deletion) | Mandatory | Audit logs | Prevention |
| [Detect public read access setting for log archive](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#log-archive-public-read) | Mandatory | Audit logs | Detection |
| [Detect public write access setting for log archive](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#log-archive-public-write) | Mandatory | Audit logs | Detection |
| [Disallow configuration changes to CloudTrail](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#cloudtrail-configuration-changes) | Mandatory | Audit logs | Prevention |
| [Integrate CloudTrail events with CloudWatch Logs](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#cloudtrail-integrate-events-logs) | Mandatory | Monitoring | Prevention |
| [Enable CloudTrail in all available regions](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#cloudtrail-enable-region) | Mandatory | Audit logs | Prevention |
| [Enable integrity validation for CloudTrail log file](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#cloudtrail-enable-validation) | Mandatory | Audit logs | Prevention |
| [Disallow changes to Amazon CloudWatch set up by AWS Control Tower](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#cloudwatch-disallow-changes) | Mandatory | Control Tower Setup | Prevention |
| [Disallow deletion of AWS Config Aggregation Authorizations created by AWS Control Tower](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#config-aggregation-authorization-policy) | Mandatory | Control Tower Setup | Prevention |
| [Disallow changes to tags created by AWS Control Tower for AWS Config resources](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#cloudwatch-disallow-config-changes) | Mandatory | Control Tower Setup | Prevention |
| [Disallow configuration changes to AWS Config](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#config-disallow-changes) | Mandatory | Audit logs | Prevention |
| [Enable AWS Config in all available regions](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#config-enable-regions) | Mandatory | Audit logs | Prevention |
| [Disallow changes to AWS Config Rules set up by AWS Control Tower](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#config-rule-disallow-changes) | Mandatory | Control Tower Setup | Prevention |
| [Disallow Changes to Encryption Configuration for AWS Control Tower Created S3 Buckets in Log Archive](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#disallow-changes-s3-buckets-created) | Mandatory | Audit logs | Prevention |
| [Disallow changes to lifecycle configuration for AWS Control Tower created Amazon S3 buckets in log archive](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#disallow-lifecycle-changes-s3-buckets-created) | Mandatory | Audit logs | Prevention |
| [Disallow changes to logging configuration for AWS Control Tower created Amazon S3 buckets in log archive](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#disallow-logging-changes-s3-buckets-created) | Mandatory | Audit logs | Prevention |
| [Disallow changes to bucket policy for AWS Control Tower created Amazon S3 buckets in log archive](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#disallow-policy-changes-s3-buckets-created) | Mandatory | Audit logs | Prevention |
| [Disallow changes to AWS IAM roles set up by AWS Control Tower and AWS CloudFormation](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#iam-disallow-changes) | Mandatory | Control Tower Setup | Prevention |
| [Disallow changes to AWS Lambda functions set up by AWS Control Tower](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#lambda-disallow-changes) | Mandatory | Control Tower Setup | Prevention |
| [Disallow changes to Amazon CloudWatch Logs log groups set up by AWS Control Tower](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#log-group-deletion-policy) | Mandatory | Audit logs | Prevention |
| [Disallow changes to Amazon SNS set up by AWS Control Tower](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#sns-disallow-changes) | Mandatory | Control Tower Setup | Prevention |
| [Disallow changes to Amazon SNS subscriptions set up by AWS Control Tower](https://docs.aws.amazon.com/controltower/latest/userguide/mandatory-guardrails.html#sns-subscriptions-disallow-changes) | Mandatory | Control Tower Setup | Prevention |

**Attachments:**