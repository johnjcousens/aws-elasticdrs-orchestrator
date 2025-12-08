#!/bin/bash
# Monitor active DRS job until completion

JOB_ID="drsjob-3be07047c5f2f5f48"
REGION="us-east-1"

echo "Monitoring DRS Job: $JOB_ID"
echo "Started at: $(date)"
echo ""

while true; do
    # Get job status
    JOB_STATUS=$(aws drs describe-jobs --region $REGION --filters jobIDs=$JOB_ID --query 'items[0].status' --output text 2>/dev/null)
    
    if [ -z "$JOB_STATUS" ]; then
        echo "ERROR: Job not found"
        exit 1
    fi
    
    # Get participating servers
    SERVERS=$(aws drs describe-jobs --region $REGION --filters jobIDs=$JOB_ID --query 'items[0].participatingServers[*].[sourceServerID,launchStatus,recoveryInstanceID]' --output text 2>/dev/null)
    
    # Get latest log event
    LATEST_EVENT=$(aws drs describe-job-log-items --region $REGION --job-id $JOB_ID --query 'items[-1].[logDateTime,event]' --output text 2>/dev/null)
    
    clear
    echo "==================================================================="
    echo "  DRS Job Monitor - $(date +%H:%M:%S)"
    echo "==================================================================="
    echo ""
    echo "Job ID: $JOB_ID"
    echo "Status: $JOB_STATUS"
    echo ""
    echo "Latest Event: $LATEST_EVENT"
    echo ""
    echo "Participating Servers:"
    echo "$SERVERS" | while read line; do
        echo "  $line"
    done
    echo ""
    
    # Check for completion
    if [ "$JOB_STATUS" = "COMPLETED" ]; then
        echo "✓ JOB COMPLETED"
        
        # Check for recovery instances
        echo ""
        echo "Checking recovery instances..."
        aws drs describe-recovery-instances --region $REGION --query 'items[*].[sourceServerID,ec2InstanceID,ec2InstanceState]' --output table
        
        exit 0
    elif [ "$JOB_STATUS" = "FAILED" ] || [ "$JOB_STATUS" = "TERMINATED" ]; then
        echo "✗ JOB FAILED: $JOB_STATUS"
        exit 1
    fi
    
    sleep 30
done
