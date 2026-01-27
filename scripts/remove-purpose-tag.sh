#!/bin/bash
# Remove legacy Purpose tag from all EC2 instances
# Safe for CloudShell - no user input required

set -e

REGION="us-east-1"

ALL_INSTANCE_IDS=(
  "i-08079c6d44888cd37"  # hrp-core-db01-az1
  "i-0ead3f8fb7d6a6745"  # hrp-core-db02-az1
  "i-053654498d177ea0d"  # hrp-core-app01-az1
  "i-0284e604b2cb3d9a4"  # hrp-core-app02-az1
  "i-0a24e3429ec060c7e"  # hrp-core-web01-az1
  "i-0f46d8897d2b98824"  # hrp-core-web02-az1
)

echo "Removing legacy Purpose tag from all instances..."
echo ""

for instance_id in "${ALL_INSTANCE_IDS[@]}"; do
  echo "Processing $instance_id..."
  aws ec2 delete-tags \
    --region "$REGION" \
    --resources "$instance_id" \
    --tags Key=Purpose \
    2>&1 || echo "Note: Purpose tag not found on $instance_id"
done

echo ""
echo "✓ Legacy Purpose tag removed from all instances"
echo ""
echo "Verify removal:"
aws ec2 describe-instances \
  --region "$REGION" \
  --instance-ids "${ALL_INSTANCE_IDS[@]}" \
  --query 'Reservations[].Instances[].[Tags[?Key==`Name`].Value|[0],InstanceId,Tags[?Key==`Purpose`]]' \
  --output table
