#!/bin/bash

# Target account configuration
export AWS_PROFILE="444455556666_AdministratorAccess"
REGION="us-east-1"
VPC_ID="vpc-08c7f2a39d0faf1d2"
SUBNET_ID="subnet-0ac9ca70195a3a948"
SECURITY_GROUP="sg-09bb15b316d05b093"
KEY_NAME="keypair-staging-us-east-1-pem"
AMI_ID="ami-043cc489b5239c3de"
INSTANCE_TYPE="t3.large"
IAM_PROFILE="demo-ec2-profile"

echo "Creating 6 new instances (05/06 series) in account 444455556666..."
echo "VPC: $VPC_ID"
echo "Subnet: $SUBNET_ID"
echo "Security Group: $SECURITY_GROUP"
echo ""

# Database Server 05
echo "Creating hrp-core-db05-az1..."
DB05_ID=$(AWS_PAGER="" aws ec2 run-instances \
  --region $REGION \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --subnet-id $SUBNET_ID \
  --security-group-ids $SECURITY_GROUP \
  --iam-instance-profile Name=$IAM_PROFILE \
  --tag-specifications \
    'ResourceType=instance,Tags=[
      {Key=Name,Value=hrp-core-db05-az1},
      {Key=dr:enabled,Value=true},
      {Key=QSConfigName-vjvyt,Value=DailyPatchCheck},
      {Key=ResourceType,Value=Database},
      {Key=AWSDRS,Value=AllowLaunchingIntoThisInstance},
      {Key=BusinessUnit,Value=HRP},
      {Key=Customer,Value=CustomerA},
      {Key=Service,Value=DatabaseServer},
      {Key=dr:recovery-strategy,Value=drs},
      {Key=dr:priority,Value=critical},
      {Key=dr:wave,Value=1},
      {Key=MonitoringLevel,Value=Critical},
      {Key=Application,Value=HRP-Core-Platform}
    ]' \
  --query 'Instances[0].InstanceId' \
  --output text)
echo "Created: $DB05_ID"

# Database Server 06
echo "Creating hrp-core-db06-az1..."
DB06_ID=$(AWS_PAGER="" aws ec2 run-instances \
  --region $REGION \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --subnet-id $SUBNET_ID \
  --security-group-ids $SECURITY_GROUP \
  --iam-instance-profile Name=$IAM_PROFILE \
  --tag-specifications \
    'ResourceType=instance,Tags=[
      {Key=Name,Value=hrp-core-db06-az1},
      {Key=dr:enabled,Value=true},
      {Key=QSConfigName-vjvyt,Value=DailyPatchCheck},
      {Key=ResourceType,Value=Database},
      {Key=AWSDRS,Value=AllowLaunchingIntoThisInstance},
      {Key=BusinessUnit,Value=HRP},
      {Key=Customer,Value=CustomerA},
      {Key=Service,Value=DatabaseServer},
      {Key=dr:recovery-strategy,Value=drs},
      {Key=dr:priority,Value=critical},
      {Key=dr:wave,Value=1},
      {Key=MonitoringLevel,Value=Critical},
      {Key=Application,Value=HRP-Core-Platform}
    ]' \
  --query 'Instances[0].InstanceId' \
  --output text)
echo "Created: $DB06_ID"

# Application Server 05
echo "Creating hrp-core-app05-az1..."
APP05_ID=$(AWS_PAGER="" aws ec2 run-instances \
  --region $REGION \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --subnet-id $SUBNET_ID \
  --security-group-ids $SECURITY_GROUP \
  --iam-instance-profile Name=$IAM_PROFILE \
  --tag-specifications \
    'ResourceType=instance,Tags=[
      {Key=Name,Value=hrp-core-app05-az1},
      {Key=dr:enabled,Value=true},
      {Key=QSConfigName-vjvyt,Value=DailyPatchCheck},
      {Key=ResourceType,Value=Compute},
      {Key=AWSDRS,Value=AllowLaunchingIntoThisInstance},
      {Key=BusinessUnit,Value=HRP},
      {Key=Customer,Value=CustomerA},
      {Key=Service,Value=ApplicationServer},
      {Key=dr:recovery-strategy,Value=drs},
      {Key=dr:priority,Value=high},
      {Key=dr:wave,Value=2},
      {Key=MonitoringLevel,Value=Standard},
      {Key=Application,Value=HRP-Core-Platform}
    ]' \
  --query 'Instances[0].InstanceId' \
  --output text)
echo "Created: $APP05_ID"

# Application Server 06
echo "Creating hrp-core-app06-az1..."
APP06_ID=$(AWS_PAGER="" aws ec2 run-instances \
  --region $REGION \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --subnet-id $SUBNET_ID \
  --security-group-ids $SECURITY_GROUP \
  --iam-instance-profile Name=$IAM_PROFILE \
  --tag-specifications \
    'ResourceType=instance,Tags=[
      {Key=Name,Value=hrp-core-app06-az1},
      {Key=dr:enabled,Value=true},
      {Key=QSConfigName-vjvyt,Value=DailyPatchCheck},
      {Key=ResourceType,Value=Compute},
      {Key=AWSDRS,Value=AllowLaunchingIntoThisInstance},
      {Key=BusinessUnit,Value=HRP},
      {Key=Customer,Value=CustomerA},
      {Key=Service,Value=ApplicationServer},
      {Key=dr:recovery-strategy,Value=drs},
      {Key=dr:priority,Value=high},
      {Key=dr:wave,Value=2},
      {Key=MonitoringLevel,Value=Standard},
      {Key=Application,Value=HRP-Core-Platform}
    ]' \
  --query 'Instances[0].InstanceId' \
  --output text)
echo "Created: $APP06_ID"

# Web Server 05
echo "Creating hrp-core-web05-az1..."
WEB05_ID=$(AWS_PAGER="" aws ec2 run-instances \
  --region $REGION \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --subnet-id $SUBNET_ID \
  --security-group-ids $SECURITY_GROUP \
  --iam-instance-profile Name=$IAM_PROFILE \
  --tag-specifications \
    'ResourceType=instance,Tags=[
      {Key=Name,Value=hrp-core-web05-az1},
      {Key=dr:enabled,Value=true},
      {Key=QSConfigName-vjvyt,Value=DailyPatchCheck},
      {Key=ResourceType,Value=Compute},
      {Key=AWSDRS,Value=AllowLaunchingIntoThisInstance},
      {Key=BusinessUnit,Value=HRP},
      {Key=Customer,Value=CustomerA},
      {Key=Service,Value=WebServer},
      {Key=dr:recovery-strategy,Value=drs},
      {Key=dr:priority,Value=medium},
      {Key=dr:wave,Value=3},
      {Key=MonitoringLevel,Value=Standard},
      {Key=Application,Value=HRP-Core-Platform}
    ]' \
  --query 'Instances[0].InstanceId' \
  --output text)
echo "Created: $WEB05_ID"

# Web Server 06
echo "Creating hrp-core-web06-az1..."
WEB06_ID=$(AWS_PAGER="" aws ec2 run-instances \
  --region $REGION \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --subnet-id $SUBNET_ID \
  --security-group-ids $SECURITY_GROUP \
  --iam-instance-profile Name=$IAM_PROFILE \
  --tag-specifications \
    'ResourceType=instance,Tags=[
      {Key=Name,Value=hrp-core-web06-az1},
      {Key=dr:enabled,Value=true},
      {Key=QSConfigName-vjvyt,Value=DailyPatchCheck},
      {Key=ResourceType,Value=Compute},
      {Key=AWSDRS,Value=AllowLaunchingIntoThisInstance},
      {Key=BusinessUnit,Value=HRP},
      {Key=Customer,Value=CustomerA},
      {Key=Service,Value=WebServer},
      {Key=dr:recovery-strategy,Value=drs},
      {Key=dr:priority,Value=medium},
      {Key=dr:wave,Value=3},
      {Key=MonitoringLevel,Value=Standard},
      {Key=Application,Value=HRP-Core-Platform}
    ]' \
  --query 'Instances[0].InstanceId' \
  --output text)
echo "Created: $WEB06_ID"

echo ""
echo "=========================================="
echo "All instances created successfully!"
echo "=========================================="
echo "Database Servers:"
echo "  - $DB05_ID (hrp-core-db05-az1)"
echo "  - $DB06_ID (hrp-core-db06-az1)"
echo ""
echo "Application Servers:"
echo "  - $APP05_ID (hrp-core-app05-az1)"
echo "  - $APP06_ID (hrp-core-app06-az1)"
echo ""
echo "Web Servers:"
echo "  - $WEB05_ID (hrp-core-web05-az1)"
echo "  - $WEB06_ID (hrp-core-web06-az1)"
echo ""
echo "Waiting 30 seconds for instances to initialize..."
sleep 30

echo ""
echo "Instance Status:"
AWS_PAGER="" aws ec2 describe-instances \
  --region $REGION \
  --instance-ids $DB05_ID $DB06_ID $APP05_ID $APP06_ID $WEB05_ID $WEB06_ID \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0],PrivateIpAddress]' \
  --output table

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo "1. Wait 5-10 minutes for Windows to boot and SSM agents to register"
echo "2. Deploy DRS agents: ./scripts/deploy_drs_agents.sh 444455556666 us-east-1 us-west-2"
echo ""
