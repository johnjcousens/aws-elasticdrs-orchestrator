#!/bin/bash

set -e
set -o pipefail

# =============================================================================
# Script: Create AD Connector in AWS
# Description: Creates an AWS Directory Service AD Connector using credentials
#              from Secrets Manager (created by createADConnectorAcctAndGroupinAD.sh)
# =============================================================================

# Variables (can be overridden via parameters)
AWS_REGION="${1:-}"
SECRET_ARN="${2:-}"
VPC_ID="${3:-}"
SUBNET_1="${4:-}"
SUBNET_2="${5:-}"
DNS_IP_1="${6:-}"
DNS_IP_2="${7:-}"
DIRECTORY_NAME="${8:-}"
NETBIOS_NAME="${9:-}"
SIZE="${10:-Small}"

# =============================================================================
# Usage Function
# =============================================================================

usage() {
    cat << EOF
Usage: $0 REGION SECRET_ARN VPC_ID SUBNET_1 SUBNET_2 DNS_1 DNS_2 DOMAIN NETBIOS [SIZE]

Creates an AWS AD Connector using credentials from Secrets Manager.

Parameters:
  REGION         AWS region (e.g., us-west-2)
  SECRET_ARN     Secrets Manager ARN with AD credentials
  VPC_ID         VPC ID for AD Connector
  SUBNET_1       First subnet ID (must be in VPC)
  SUBNET_2       Second subnet ID (must be in VPC, different AZ)
  DNS_1          First Domain Controller IP address
  DNS_2          Second Domain Controller IP address
  DOMAIN         AD domain FQDN (e.g., example.com)
  NETBIOS        NetBIOS name (e.g., EXAMPLE, max 15 chars)
  SIZE           AD Connector size: Small or Large (default: Small)

Example:
  $0 us-west-2 \\
    arn:aws:secretsmanager:us-west-2:123456:secret:adconnector-abc \\
    vpc-0abc123 \\
    subnet-0111 subnet-0222 \\
    10.100.216.10 10.100.224.10 \\
    example.com EXAMPLE Small

Prerequisites:
  - AD connector account created (createADConnectorAcctAndGroupinAD.sh)
  - Secrets Manager secret with credentials (username/password format)
  - VPC with connectivity to Domain Controllers
  - Two subnets in different Availability Zones
  - Security groups allowing AD traffic

Output:
  - Directory ID for use in registerADConnectorWithWorkspaces.sh
EOF
    exit 1
}

# =============================================================================
# Prerequisite Checks
# =============================================================================

# Check parameters
if [[ -z "$AWS_REGION" || -z "$SECRET_ARN" || -z "$VPC_ID" || -z "$SUBNET_1" || \
      -z "$SUBNET_2" || -z "$DNS_IP_1" || -z "$DNS_IP_2" || -z "$DIRECTORY_NAME" || \
      -z "$NETBIOS_NAME" ]]; then
    echo "Error: Missing required parameters"
    echo ""
    usage
fi

# Ensure jq is installed
if ! command -v jq &>/dev/null; then
    echo "Error: jq is not installed. Install it using 'sudo yum install -y jq' or 'sudo apt install -y jq'"
    exit 1
fi

# Validate SIZE parameter
if [[ "$SIZE" != "Small" && "$SIZE" != "Large" ]]; then
    echo "Error: SIZE must be 'Small' or 'Large' (got: $SIZE)"
    exit 1
fi

# Validate NetBIOS name length
if [[ ${#NETBIOS_NAME} -gt 15 ]]; then
    echo "Error: NetBIOS name must be 15 characters or less (got: ${#NETBIOS_NAME})"
    exit 1
fi

echo "=== AWS AD Connector Deployment ==="
echo "Region: $AWS_REGION"
echo "VPC: $VPC_ID"
echo "Domain: $DIRECTORY_NAME"
echo "NetBIOS: $NETBIOS_NAME"
echo "Size: $SIZE"
echo ""

# =============================================================================
# AWS Resource Validation
# =============================================================================

echo "✓ Validating AWS resources..."

# Validate VPC exists
VPC_CHECK=$(aws ec2 describe-vpcs \
    --vpc-ids "$VPC_ID" \
    --region "$AWS_REGION" \
    --query "Vpcs[0].VpcId" \
    --output text 2>/dev/null || echo "")

if [[ -z "$VPC_CHECK" || "$VPC_CHECK" == "None" ]]; then
    echo "Error: VPC $VPC_ID not found in region $AWS_REGION"
    exit 1
fi
echo "  - VPC exists: $VPC_ID"

# Validate Subnet 1
SUBNET_1_INFO=$(aws ec2 describe-subnets \
    --subnet-ids "$SUBNET_1" \
    --region "$AWS_REGION" \
    --query "Subnets[0].[SubnetId,VpcId,AvailabilityZone]" \
    --output json 2>/dev/null || echo "[]")

SUBNET_1_VPC=$(echo "$SUBNET_1_INFO" | jq -r '.[1]')
SUBNET_1_AZ=$(echo "$SUBNET_1_INFO" | jq -r '.[2]')

if [[ -z "$SUBNET_1_VPC" || "$SUBNET_1_VPC" == "null" ]]; then
    echo "Error: Subnet $SUBNET_1 not found in region $AWS_REGION"
    exit 1
fi

if [[ "$SUBNET_1_VPC" != "$VPC_ID" ]]; then
    echo "Error: Subnet $SUBNET_1 is not in VPC $VPC_ID (found in: $SUBNET_1_VPC)"
    exit 1
fi
echo "  - Subnet 1 exists: $SUBNET_1 ($SUBNET_1_AZ)"

# Validate Subnet 2
SUBNET_2_INFO=$(aws ec2 describe-subnets \
    --subnet-ids "$SUBNET_2" \
    --region "$AWS_REGION" \
    --query "Subnets[0].[SubnetId,VpcId,AvailabilityZone]" \
    --output json 2>/dev/null || echo "[]")

SUBNET_2_VPC=$(echo "$SUBNET_2_INFO" | jq -r '.[1]')
SUBNET_2_AZ=$(echo "$SUBNET_2_INFO" | jq -r '.[2]')

if [[ -z "$SUBNET_2_VPC" || "$SUBNET_2_VPC" == "null" ]]; then
    echo "Error: Subnet $SUBNET_2 not found in region $AWS_REGION"
    exit 1
fi

if [[ "$SUBNET_2_VPC" != "$VPC_ID" ]]; then
    echo "Error: Subnet $SUBNET_2 is not in VPC $VPC_ID (found in: $SUBNET_2_VPC)"
    exit 1
fi
echo "  - Subnet 2 exists: $SUBNET_2 ($SUBNET_2_AZ)"

# Validate subnets are in different AZs
if [[ "$SUBNET_1_AZ" == "$SUBNET_2_AZ" ]]; then
    echo "Error: Subnets must be in different Availability Zones"
    echo "  Subnet 1 ($SUBNET_1): $SUBNET_1_AZ"
    echo "  Subnet 2 ($SUBNET_2): $SUBNET_2_AZ"
    exit 1
fi
echo "  - Subnets in different AZs ✓"

# =============================================================================
# Credential Retrieval
# =============================================================================

echo ""
echo "✓ Retrieving AD credentials from Secrets Manager..."

SECRET_VALUE=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRET_ARN" \
    --query SecretString \
    --output text \
    --region "$AWS_REGION" 2>&1) || {
    echo "Error: Failed to retrieve secret from Secrets Manager"
    echo "$SECRET_VALUE"
    exit 1
}

# Extract username and password
AD_USER=$(echo "$SECRET_VALUE" | jq -r '.username')
AD_PASSWORD=$(echo "$SECRET_VALUE" | jq -r '.password')

# Validate extracted credentials
if [[ -z "$AD_USER" || -z "$AD_PASSWORD" || "$AD_USER" == "null" || "$AD_PASSWORD" == "null" ]]; then
    echo "Error: Missing AD username or password from Secrets Manager"
    echo "Secret must contain: {\"username\":\"...\", \"password\":\"...\"}"
    exit 1
fi

echo "  - Username: $AD_USER"
echo "  - Password: [REDACTED]"

# =============================================================================
# AD Connector Creation
# =============================================================================

echo ""
echo "✓ Creating AD Connector..."

# Build JSON payload
JSON_PAYLOAD=$(jq -n \
    --arg name "$DIRECTORY_NAME" \
    --arg short "$NETBIOS_NAME" \
    --arg pass "$AD_PASSWORD" \
    --arg size "$SIZE" \
    --arg user "$AD_USER" \
    --arg vpc "$VPC_ID" \
    --arg subnet1 "$SUBNET_1" \
    --arg subnet2 "$SUBNET_2" \
    --arg dns1 "$DNS_IP_1" \
    --arg dns2 "$DNS_IP_2" \
    '{
        Name: $name,
        ShortName: $short,
        Password: $pass,
        Size: $size,
        ConnectSettings: {
            VpcId: $vpc,
            SubnetIds: [$subnet1, $subnet2],
            CustomerDnsIps: [$dns1, $dns2],
            CustomerUserName: $user
        }
    }')

# Create AD Connector
CREATE_OUTPUT=$(aws ds connect-directory \
    --cli-input-json "$JSON_PAYLOAD" \
    --region "$AWS_REGION" \
    --output json 2>&1) || {
    echo "Error: Failed to create AD Connector"
    echo "$CREATE_OUTPUT"
    exit 1
}

DIRECTORY_ID=$(echo "$CREATE_OUTPUT" | jq -r '.DirectoryId')

if [[ -z "$DIRECTORY_ID" || "$DIRECTORY_ID" == "null" ]]; then
    echo "Error: Failed to get Directory ID from response"
    echo "$CREATE_OUTPUT"
    exit 1
fi

echo "  - AD Connector initiated: $DIRECTORY_ID"

# =============================================================================
# Status Monitoring
# =============================================================================

echo ""
echo "Waiting for AD Connector to become Active..."
echo "(This typically takes 5-10 minutes)"
echo ""

MAX_ATTEMPTS=30  # 30 attempts * 30 seconds = 15 minutes
ATTEMPT=0
START_TIME=$(date +%s)

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    # Get directory status
    STATUS_OUTPUT=$(aws ds describe-directories \
        --directory-ids "$DIRECTORY_ID" \
        --region "$AWS_REGION" \
        --query "DirectoryDescriptions[0].[State,StateLastUpdatedDateTime]" \
        --output json 2>/dev/null || echo '["Unknown",null]')
    
    STATUS=$(echo "$STATUS_OUTPUT" | jq -r '.[0]')
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    case "$STATUS" in
        "Active")
            echo "✓ AD Connector is Active (${ELAPSED}s)"
            break
            ;;
        "Failed"|"Impaired"|"Deleted")
            echo "Error: AD Connector creation failed with status: $STATUS"
            
            # Get error details
            ERROR_MSG=$(aws ds describe-directories \
                --directory-ids "$DIRECTORY_ID" \
                --region "$AWS_REGION" \
                --query "DirectoryDescriptions[0].StageReason" \
                --output text 2>/dev/null || echo "No error details available")
            
            echo "Error details: $ERROR_MSG"
            exit 1
            ;;
        "Creating"|"Requested")
            echo "Status: $STATUS... (${ELAPSED}s)"
            sleep 30
            ATTEMPT=$((ATTEMPT + 1))
            ;;
        *)
            echo "Status: $STATUS... (${ELAPSED}s)"
            sleep 30
            ATTEMPT=$((ATTEMPT + 1))
            ;;
    esac
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "Error: AD Connector creation timed out after 15 minutes"
    echo "Current status: $STATUS"
    echo ""
    echo "Check AWS Console for details:"
    echo "https://console.aws.amazon.com/directoryservicev2/#!/directories/$DIRECTORY_ID"
    exit 1
fi

# =============================================================================
# Verification
# =============================================================================

echo ""
echo "=== Retrieving AD Connector Details ==="

# Get full directory information
DIR_INFO=$(aws ds describe-directories \
    --directory-ids "$DIRECTORY_ID" \
    --region "$AWS_REGION" \
    --output json)

DIR_NAME=$(echo "$DIR_INFO" | jq -r '.DirectoryDescriptions[0].Name')
DIR_SHORT=$(echo "$DIR_INFO" | jq -r '.DirectoryDescriptions[0].ShortName')
DIR_SIZE=$(echo "$DIR_INFO" | jq -r '.DirectoryDescriptions[0].Size')
DIR_VPC=$(echo "$DIR_INFO" | jq -r '.DirectoryDescriptions[0].VpcSettings.VpcId')
DIR_SUBNETS=$(echo "$DIR_INFO" | jq -r '.DirectoryDescriptions[0].VpcSettings.SubnetIds[]' | tr '\n' ', ' | sed 's/,$//')
DIR_DNS=$(echo "$DIR_INFO" | jq -r '.DirectoryDescriptions[0].ConnectSettings.CustomerDnsIps[]' | tr '\n' ', ' | sed 's/,$//')
DIR_USERNAME=$(echo "$DIR_INFO" | jq -r '.DirectoryDescriptions[0].ConnectSettings.CustomerUserName')

echo ""
echo "✅ AD Connector deployed successfully!"
echo ""
echo "==================================="
echo "Directory Information"
echo "==================================="
echo "Directory ID: $DIRECTORY_ID"
echo "DNS Name: $DIR_NAME"
echo "NetBIOS Name: $DIR_SHORT"
echo "Status: Active"
echo "Size: $DIR_SIZE"
echo "Username: $DIR_USERNAME"
echo "VPC: $DIR_VPC"
echo "Subnets: $DIR_SUBNETS"
echo "DNS Servers: $DIR_DNS"
echo "Region: $AWS_REGION"
echo "==================================="
echo ""
echo "Next Steps:"
echo "  1. Register with WorkSpaces:"
echo "     ./registerADConnectorWithWorkspaces.sh $DIRECTORY_ID $AWS_REGION <SUBNET_1> <SUBNET_2>"
echo ""
echo "  2. Verify connectivity:"
echo "     aws ds describe-directories --directory-ids $DIRECTORY_ID --region $AWS_REGION"
echo ""
echo "  3. View in AWS Console:"
echo "     https://console.aws.amazon.com/directoryservicev2/#!/directories/$DIRECTORY_ID"
echo ""

# Output Directory ID for scripting use (parseable format)
echo "DIRECTORY_ID=$DIRECTORY_ID"
