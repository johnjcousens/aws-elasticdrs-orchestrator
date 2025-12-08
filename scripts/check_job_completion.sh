#!/bin/bash
# Single comprehensive check of DRS job status

JOB_ID="drsjob-3be07047c5f2f5f48"
REGION="us-east-1"

echo "==================================================================="
echo "DRS Job Status Check - $(date)"
echo "==================================================================="
echo ""

# 1. Job Status
echo "1. JOB STATUS:"
aws drs describe-jobs --region $REGION --filters jobIDs=$JOB_ID \
  --query 'items[0].[status,participatingServers[*].[sourceServerID,launchStatus,recoveryInstanceID]]' \
  --output json | python3 -m json.tool
echo ""

# 2. Latest Log Events
echo "2. LATEST LOG EVENTS:"
aws drs describe-job-log-items --region $REGION --job-id $JOB_ID \
  --query 'items[-5:].[logDateTime,event]' --output table
echo ""

# 3. Recovery Instances
echo "3. RECOVERY INSTANCES:"
RECOVERY_COUNT=$(aws drs describe-recovery-instances --region $REGION --query 'length(items)' --output text)
echo "Count: $RECOVERY_COUNT"

if [ "$RECOVERY_COUNT" -gt 0 ]; then
    aws drs describe-recovery-instances --region $REGION \
      --query 'items[*].[sourceServerID,ec2InstanceID,ec2InstanceState,recoveryInstanceID]' \
      --output table
    echo ""
    echo "✓ RECOVERY INSTANCES EXIST"
else
    echo "✗ NO RECOVERY INSTANCES FOUND"
fi
echo ""

# 4. Conversion Server Status
echo "4. CONVERSION SERVER:"
aws ec2 describe-instances --region $REGION \
  --filters "Name=tag:Name,Values=*Conversion Server*" "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,LaunchTime]' \
  --output table

echo ""
echo "==================================================================="
