#!/bin/bash
# Rename source EC2 instances to comply with HealthEdge naming convention
# Format: FQDN-[AZ] where FQDN follows pattern: [service-line]-[workload]-[type][number]
# Safe for CloudShell - no user input required

set -e

REGION="us-east-1"
AZ_SUFFIX="az1"  # us-east-1c is the first AZ in the region

echo "Renaming instances to comply with HealthEdge naming convention..."
echo "Format: [service-line]-[workload]-[type][number]-[az]"
echo ""

# Database Servers - Wave 1 (Critical)
# Old: WINDBSRV01, WINDBSRV02
# New: hrp-core-db01-az1, hrp-core-db02-az1
echo "Renaming Database Servers..."
aws ec2 create-tags \
  --region "$REGION" \
  --resources "i-08079c6d44888cd37" \
  --tags Key=Name,Value=hrp-core-db01-az1

aws ec2 create-tags \
  --region "$REGION" \
  --resources "i-0ead3f8fb7d6a6745" \
  --tags Key=Name,Value=hrp-core-db02-az1

# Application Servers - Wave 2 (High Priority)
# Old: WINAPPSRV01, WINAPPSRV02
# New: hrp-core-app01-az1, hrp-core-app02-az1
echo "Renaming Application Servers..."
aws ec2 create-tags \
  --region "$REGION" \
  --resources "i-053654498d177ea0d" \
  --tags Key=Name,Value=hrp-core-app01-az1

aws ec2 create-tags \
  --region "$REGION" \
  --resources "i-0284e604b2cb3d9a4" \
  --tags Key=Name,Value=hrp-core-app02-az1

# Web Servers - Wave 3 (Medium Priority)
# Old: WINWEBSRV01, WINWEBSRV02
# New: hrp-core-web01-az1, hrp-core-web02-az1
echo "Renaming Web Servers..."
aws ec2 create-tags \
  --region "$REGION" \
  --resources "i-0a24e3429ec060c7e" \
  --tags Key=Name,Value=hrp-core-web01-az1

aws ec2 create-tags \
  --region "$REGION" \
  --resources "i-0f46d8897d2b98824" \
  --tags Key=Name,Value=hrp-core-web02-az1

echo ""
echo "✓ Renaming complete"
echo ""
echo "Naming Convention Applied:"
echo "  Service Line: hrp (HRP)"
echo "  Workload: core (HRP-Core-Platform)"
echo "  Type: db (database), app (application), web (web server)"
echo "  Number: 01, 02 (instance sequence)"
echo "  AZ: az1 (us-east-1c)"
echo ""
echo "New Instance Names:"
echo "  Wave 1 (Database):    hrp-core-db01-az1, hrp-core-db02-az1"
echo "  Wave 2 (Application): hrp-core-app01-az1, hrp-core-app02-az1"
echo "  Wave 3 (Web):         hrp-core-web01-az1, hrp-core-web02-az1"
echo ""
echo "Verify names:"
aws ec2 describe-instances \
  --region "$REGION" \
  --instance-ids \
    i-08079c6d44888cd37 \
    i-0ead3f8fb7d6a6745 \
    i-053654498d177ea0d \
    i-0284e604b2cb3d9a4 \
    i-0a24e3429ec060c7e \
    i-0f46d8897d2b98824 \
  --query 'Reservations[].Instances[].[Tags[?Key==`Name`].Value|[0],InstanceId,Placement.AvailabilityZone,Tags[?Key==`Service`].Value|[0]]' \
  --output table
