#!/bin/bash

# Target account configuration
export AWS_PROFILE="111122223333_AdministratorAccess"
REGION="us-east-1"
VPC_ID="vpc-08c7f2a39d0faf1d2"
SUBNET_ID="subnet-0de127c19dc67593e"
SECURITY_GROUP="sg-021589d4447675144"
KEY_NAME="RSA-PEM-TARGET-us-east-1"
AMI_ID="ami-043cc489b5239c3de"
INSTANCE_TYPE="t3.large"

echo "Creating 6 new instances in account 111122223333..."
echo "VPC: $VPC_ID"
echo "Subnet: $SUBNET_ID"
echo "Security Group: $SECURITY_GROUP"
echo ""

# Database Server 03
echo "Creating hrp-core-db03-az1..."
DB03_ID=$(AWS_PAGER="" aws ec2 run-instances \
  --region $REGION \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --subnet-id $SUBNET_ID \
  --security-group-ids $SECURITY_GROUP \
  --tag-specifications \
    'ResourceType=instance,Tags=[
      {Key=Name,Value=hrp-core-db03-az1},
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
echo "Created: $DB03_ID"

# Database Server 04
echo "Creating hrp-core-db04-az1..."
DB04_ID=$(AWS_PAGER="" aws ec2 run-instances \
  --region $REGION \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --subnet-id $SUBNET_ID \
  --security-group-ids $SECURITY_GROUP \
  --tag-specifications \
    'ResourceType=instance,Tags=[
      {Key=Name,Value=hrp-core-db04-az1},
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
echo "Created: $DB04_ID"

# Application Server 03
echo "Creating hrp-core-app03-az1..."
APP03_ID=$(AWS_PAGER="" aws ec2 run-instances \
  --region $REGION \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --subnet-id $SUBNET_ID \
  --security-group-ids $SECURITY_GROUP \
  --tag-specifications \
    'ResourceType=instance,Tags=[
      {Key=Name,Value=hrp-core-app03-az1},
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
echo "Created: $APP03_ID"

# Application Server 04
echo "Creating hrp-core-app04-az1..."
APP04_ID=$(AWS_PAGER="" aws ec2 run-instances \
  --region $REGION \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --subnet-id $SUBNET_ID \
  --security-group-ids $SECURITY_GROUP \
  --tag-specifications \
    'ResourceType=instance,Tags=[
      {Key=Name,Value=hrp-core-app04-az1},
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
echo "Created: $APP04_ID"

# Web Server 03
echo "Creating hrp-core-web03-az1..."
WEB03_ID=$(AWS_PAGER="" aws ec2 run-instances \
  --region $REGION \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --subnet-id $SUBNET_ID \
  --security-group-ids $SECURITY_GROUP \
  --tag-specifications \
    'ResourceType=instance,Tags=[
      {Key=Name,Value=hrp-core-web03-az1},
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
echo "Created: $WEB03_ID"

# Web Server 04
echo "Creating hrp-core-web04-az1..."
WEB04_ID=$(AWS_PAGER="" aws ec2 run-instances \
  --region $REGION \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --subnet-id $SUBNET_ID \
  --security-group-ids $SECURITY_GROUP \
  --tag-specifications \
    'ResourceType=instance,Tags=[
      {Key=Name,Value=hrp-core-web04-az1},
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
echo "Created: $WEB04_ID"

echo ""
echo "=========================================="
echo "All instances created successfully!"
echo "=========================================="
echo "Database Servers:"
echo "  - $DB03_ID (hrp-core-db03-az1)"
echo "  - $DB04_ID (hrp-core-db04-az1)"
echo ""
echo "Application Servers:"
echo "  - $APP03_ID (hrp-core-app03-az1)"
echo "  - $APP04_ID (hrp-core-app04-az1)"
echo ""
echo "Web Servers:"
echo "  - $WEB03_ID (hrp-core-web03-az1)"
echo "  - $WEB04_ID (hrp-core-web04-az1)"
echo ""
echo "Waiting 30 seconds for instances to initialize..."
sleep 30

echo ""
echo "Instance Status:"
AWS_PAGER="" aws ec2 describe-instances \
  --region $REGION \
  --instance-ids $DB03_ID $DB04_ID $APP03_ID $APP04_ID $WEB03_ID $WEB04_ID \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0],PrivateIpAddress]' \
  --output table
