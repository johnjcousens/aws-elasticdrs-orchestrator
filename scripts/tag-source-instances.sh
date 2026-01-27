#!/bin/bash
# Tag source EC2 instances in us-east-1c with DR tags
# Safe for CloudShell - no user input required

set -e

REGION="us-east-1"

# Database Servers - Critical tier, must come up first
# MonitoringLevel=Critical → dr:priority=critical, dr:wave=1
DB_INSTANCE_IDS=(
  "i-08079c6d44888cd37"  # WINDBSRV01 - Primary DB for CustomerA
  "i-0ead3f8fb7d6a6745"  # WINDBSRV02 - Secondary DB for CustomerA
)

# Application Servers - Standard tier, depends on database
# MonitoringLevel=Standard → dr:priority=high, dr:wave=2
APP_INSTANCE_IDS=(
  "i-053654498d177ea0d"  # WINAPPSRV01 - App tier for CustomerA
  "i-0284e604b2cb3d9a4"  # WINAPPSRV02 - App tier for CustomerA
)

# Web Servers - Standard tier, depends on app servers
# MonitoringLevel=Standard → dr:priority=medium, dr:wave=3
WEB_INSTANCE_IDS=(
  "i-0a24e3429ec060c7e"  # WINWEBSRV01 - Web frontend for CustomerA
  "i-0f46d8897d2b98824"  # WINWEBSRV02 - Web frontend for CustomerA
)

ALL_INSTANCE_IDS=("${DB_INSTANCE_IDS[@]}" "${APP_INSTANCE_IDS[@]}" "${WEB_INSTANCE_IDS[@]}")

echo "Removing old dr:strategy tag and applying correct tags..."

# Tag Database Servers - Wave 1 (Critical)
for instance_id in "${DB_INSTANCE_IDS[@]}"; do
  echo "Processing Database Server $instance_id..."
  
  # Remove old incorrect tag
  aws ec2 delete-tags \
    --region "$REGION" \
    --resources "$instance_id" \
    --tags Key=dr:strategy \
    2>&1 || echo "Note: dr:strategy tag not found on $instance_id"
  
  # Apply correct tags
  aws ec2 create-tags \
    --region "$REGION" \
    --resources "$instance_id" \
    --tags \
      Key=BusinessUnit,Value=HRP \
      Key=ResourceType,Value=Database \
      Key=Service,Value=DatabaseServer \
      Key=Application,Value=HRP-Core-Platform \
      Key=Customer,Value=CustomerA \
      Key=MonitoringLevel,Value=Critical \
      Key=dr:enabled,Value=true \
      Key=dr:recovery-strategy,Value=drs \
      Key=dr:priority,Value=critical \
      Key=dr:wave,Value=1 \
      Key=AWSDRS,Value=AllowLaunchingIntoThisInstance \
    2>&1 || echo "Warning: Failed to tag $instance_id"
done

# Tag Application Servers - Wave 2 (High Priority)
for instance_id in "${APP_INSTANCE_IDS[@]}"; do
  echo "Processing Application Server $instance_id..."
  
  # Remove old incorrect tag
  aws ec2 delete-tags \
    --region "$REGION" \
    --resources "$instance_id" \
    --tags Key=dr:strategy \
    2>&1 || echo "Note: dr:strategy tag not found on $instance_id"
  
  # Apply correct tags
  aws ec2 create-tags \
    --region "$REGION" \
    --resources "$instance_id" \
    --tags \
      Key=BusinessUnit,Value=HRP \
      Key=ResourceType,Value=Compute \
      Key=Service,Value=ApplicationServer \
      Key=Application,Value=HRP-Core-Platform \
      Key=Customer,Value=CustomerA \
      Key=MonitoringLevel,Value=Standard \
      Key=dr:enabled,Value=true \
      Key=dr:recovery-strategy,Value=drs \
      Key=dr:priority,Value=high \
      Key=dr:wave,Value=2 \
      Key=AWSDRS,Value=AllowLaunchingIntoThisInstance \
    2>&1 || echo "Warning: Failed to tag $instance_id"
done

# Tag Web Servers - Wave 3 (Medium Priority)
for instance_id in "${WEB_INSTANCE_IDS[@]}"; do
  echo "Processing Web Server $instance_id..."
  
  # Remove old incorrect tag
  aws ec2 delete-tags \
    --region "$REGION" \
    --resources "$instance_id" \
    --tags Key=dr:strategy \
    2>&1 || echo "Note: dr:strategy tag not found on $instance_id"
  
  # Apply correct tags
  aws ec2 create-tags \
    --region "$REGION" \
    --resources "$instance_id" \
    --tags \
      Key=BusinessUnit,Value=HRP \
      Key=ResourceType,Value=Compute \
      Key=Service,Value=WebServer \
      Key=Application,Value=HRP-Core-Platform \
      Key=Customer,Value=CustomerA \
      Key=MonitoringLevel,Value=Standard \
      Key=dr:enabled,Value=true \
      Key=dr:recovery-strategy,Value=drs \
      Key=dr:priority,Value=medium \
      Key=dr:wave,Value=3 \
      Key=AWSDRS,Value=AllowLaunchingIntoThisInstance \
    2>&1 || echo "Warning: Failed to tag $instance_id"
done

echo "✓ Tagging complete"
echo ""
echo "DR Wave/Priority Mapping:"
echo "  Wave 1 (Critical):  Database Servers - Must recover first"
echo "  Wave 2 (High):      Application Servers - Depend on databases"
echo "  Wave 3 (Medium):    Web Servers - Depend on app servers"
echo ""
echo "Verify tags:"
aws ec2 describe-tags \
  --region "$REGION" \
  --filters "Name=resource-id,Values=${ALL_INSTANCE_IDS[*]}" "Name=key,Values=Application,Customer,MonitoringLevel,dr:priority,dr:wave" \
  --query 'Tags[*].[ResourceId,Key,Value]' \
  --output table
