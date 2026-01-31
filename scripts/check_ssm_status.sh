#!/bin/bash

# Quick status check script
export AWS_PROFILE="111122223333_AdministratorAccess"
REGION="us-east-1"

INSTANCES=(
  "i-0d780c0fa44ba72e9"  # hrp-core-db03-az1
  "i-0117a71b9b09d45f7"  # hrp-core-db04-az1
  "i-0b5fcf61e94e9f599"  # hrp-core-app03-az1
  "i-0b40c1c713cfdeac8"  # hrp-core-app04-az1
  "i-00c5c7b3cf6d8abeb"  # hrp-core-web03-az1
  "i-04d81abd203126050"  # hrp-core-web04-az1
)

echo "=========================================="
echo "Instance Status Check"
echo "=========================================="
echo ""

# EC2 Status
echo "EC2 Instance Status:"
AWS_PAGER="" aws ec2 describe-instances \
  --region $REGION \
  --instance-ids "${INSTANCES[@]}" \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0],PrivateIpAddress]' \
  --output table

echo ""
echo "SSM Agent Status:"
AWS_PAGER="" aws ssm describe-instance-information \
  --region $REGION \
  --filters "Key=InstanceIds,Values=$(IFS=,; echo "${INSTANCES[*]}")" \
  --query 'InstanceInformationList[*].[InstanceId,PingStatus,PlatformType,AgentVersion,LastPingDateTime]' \
  --output table 2>/dev/null || echo "No SSM agents registered yet."

ONLINE_COUNT=$(AWS_PAGER="" aws ssm describe-instance-information \
  --region $REGION \
  --filters "Key=InstanceIds,Values=$(IFS=,; echo "${INSTANCES[*]}")" \
  --query 'InstanceInformationList[?PingStatus==`Online`] | length(@)' \
  --output text 2>/dev/null || echo "0")

echo ""
echo "Summary: $ONLINE_COUNT / ${#INSTANCES[@]} SSM agents online"
echo ""

if [ "$ONLINE_COUNT" -eq "${#INSTANCES[@]}" ]; then
  echo "✅ All instances ready for DRS agent installation!"
  echo ""
  echo "Run: ./deploy_drs_agents.sh"
else
  echo "⏳ Waiting for SSM agents to come online..."
  echo ""
  echo "SSM agents typically register within 2-5 minutes after instance launch."
  echo "Run this script again in a few minutes."
fi
echo ""
