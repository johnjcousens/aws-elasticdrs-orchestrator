#!/bin/bash
JOB_ID="drsjob-3be07047c5f2f5f48"
REGION="us-east-1"
MAX_WAIT=1200  # 20 minutes
INTERVAL=60    # Check every minute

START_TIME=$(date +%s)

while true; do
    ELAPSED=$(($(date +%s) - START_TIME))
    
    if [ $ELAPSED -gt $MAX_WAIT ]; then
        echo "TIMEOUT after $((ELAPSED/60)) minutes"
        exit 1
    fi
    
    STATUS=$(aws drs describe-jobs --region $REGION --filters jobIDs=$JOB_ID --query 'items[0].status' --output text 2>/dev/null)
    LAUNCH_STATUS=$(aws drs describe-jobs --region $REGION --filters jobIDs=$JOB_ID --query 'items[0].participatingServers[0].launchStatus' --output text 2>/dev/null)
    RECOVERY_COUNT=$(aws drs describe-recovery-instances --region $REGION --query 'length(items)' --output text 2>/dev/null)
    
    echo "[$(date +%H:%M:%S)] Elapsed: $((ELAPSED/60))m | Job: $STATUS | Launch: $LAUNCH_STATUS | Recovery Instances: $RECOVERY_COUNT"
    
    # Check for completion
    if [ "$STATUS" = "COMPLETED" ] || [ "$LAUNCH_STATUS" = "LAUNCHED" ]; then
        echo ""
        echo "✓ JOB COMPLETED/LAUNCHED"
        echo ""
        aws drs describe-recovery-instances --region $REGION --query 'items[*].[sourceServerID,ec2InstanceID,ec2InstanceState]' --output table
        exit 0
    fi
    
    if [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "TERMINATED" ]; then
        echo ""
        echo "✗ JOB FAILED: $STATUS"
        exit 1
    fi
    
    sleep $INTERVAL
done
