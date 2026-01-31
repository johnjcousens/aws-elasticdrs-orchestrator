#!/bin/bash

# Attach IAM instance profile to enable SSM and DRS
export AWS_PROFILE="111122223333_AdministratorAccess"
REGION="us-east-1"
INSTANCE_PROFILE="demo-ec2-profile"

INSTANCES=(
  "i-0d780c0fa44ba72e9"  # hrp-core-db03-az1
  "i-0117a71b9b09d45f7"  # hrp-core-db04-az1
  "i-0b5fcf61e94e9f599"  # hrp-core-app03-az1
  "i-0b40c1c713cfdeac8"  # hrp-core-app04-az1
  "i-00c5c7b3cf6d8abeb"  # hrp-core-web03-az1
  "i-04d81abd203126050"  # hrp-core-web04-az1
)

echo "=========================================="
echo "Attaching IAM Instance Profile"
echo "=========================================="
echo "Profile: $INSTANCE_PROFILE"
echo "Region: $REGION"
echo ""

for instance_id in "${INSTANCES[@]}"; do
  echo "Attaching profile to $instance_id..."
  
  AWS_PAGER="" aws ec2 associate-iam-instance-profile \
    --region $REGION \
    --instance-id $instance_id \
    --iam-instance-profile Name=$INSTANCE_PROFILE \
    --output text > /dev/null 2>&1
  
  if [ $? -eq 0 ]; then
    echo "  ✅ Success"
  else
    echo "  ❌ Failed (may already be attached)"
  fi
done

echo ""
echo "Verifying IAM profiles..."
AWS_PAGER="" aws ec2 describe-instances \
  --region $REGION \
  --instance-ids "${INSTANCES[@]}" \
  --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],IamInstanceProfile.Arn]' \
  --output table

echo ""
echo "=========================================="
echo "IAM Profile Attachment Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Wait 2-3 minutes for SSM agents to register"
echo "2. Run: ./check_ssm_status.sh"
echo "3. When all SSM agents are online, run: ./deploy_drs_agents.sh"
echo ""
