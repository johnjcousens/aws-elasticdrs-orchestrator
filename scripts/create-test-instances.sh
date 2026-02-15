#!/bin/bash
#===============================================================================
# Create 300 Test Instances (100 DB + 100 App + 100 Web)
# AWS CLI2 / CloudShell Compatible - No User Interaction Required
#
# Mirrors create-domain-controller.sh pattern:
#   1. Creates a Launch Template per instance (static IP + UserData)
#   2. UserData renames hostname and configures static IP inside Windows
#   3. Launches instance from the launch template
#
# Usage:
#   ./create-test-instances.sh                    # Launch all 300
#   ./create-test-instances.sh --tier db          # Launch 100 DB only
#   ./create-test-instances.sh --tier app         # Launch 100 App only
#   ./create-test-instances.sh --tier web         # Launch 100 Web only
#   ./create-test-instances.sh --dry-run          # Print plan, no launch
#   ./create-test-instances.sh --count 10         # Override count per tier
#===============================================================================

set -e

#===============================================================================
# Infrastructure Configuration (existing resources)
#===============================================================================
REGION="us-east-1"
VPC_ID="vpc-04b69e43c8ca4392c"
SECURITY_GROUP="sg-0d8ef1a705ddcab67"
KEY_NAME="keypair-WorkloadsDev-us-east-1-pem"
AMI_ID="ami-031283482dcfced88"
INSTANCE_TYPE="t3.medium"
IAM_PROFILE="ec2-baseline-role"

# Subnet assignments
SUBNETAZ4_ID="subnet-0eb84f6e52fe7bb77"   # DB:  10.229.128.0/20
SUBNETAZ6_ID="subnet-0851883a5098c2ead"   # App: 10.229.144.0/20
SUBNETAZ1_ID="subnet-04bfa725d8b944f6d"   # Web: 10.229.160.0/20

# IP configuration per tier
DB_IP_PREFIX="10.229.143"
DB_GATEWAY="10.229.128.1"
DB_PREFIX_LENGTH="20"
DB_DNS_SERVERS="10.229.128.2,8.8.8.8"
DB_DNS_SUFFIX="hrpdev.local"

APP_IP_PREFIX="10.229.159"
APP_GATEWAY="10.229.144.1"
APP_PREFIX_LENGTH="20"
APP_DNS_SERVERS="10.229.144.2,8.8.8.8"
APP_DNS_SUFFIX="hrpdev.local"

WEB_IP_PREFIX="10.229.175"
WEB_GATEWAY="10.229.160.1"
WEB_PREFIX_LENGTH="20"
WEB_DNS_SERVERS="10.229.160.2,8.8.8.8"
WEB_DNS_SUFFIX="hrpdev.local"

IP_START=101

# Defaults
COUNT=100
TIER_FILTER="all"
DRY_RUN=false
BATCH_SIZE=10
BATCH_DELAY=5
START_INDEX=1


#===============================================================================
# Parse Arguments
#===============================================================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --tier) TIER_FILTER="$2"; shift 2 ;;
        --count) COUNT="$2"; shift 2 ;;
        --start) START_INDEX="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        --batch-size) BATCH_SIZE="$2"; shift 2 ;;
        --batch-delay) BATCH_DELAY="$2"; shift 2 ;;
        --instance-type) INSTANCE_TYPE="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ "$TIER_FILTER" != "all" && "$TIER_FILTER" != "db" && "$TIER_FILTER" != "app" && "$TIER_FILTER" != "web" ]]; then
    echo "ERROR: --tier must be one of: all, db, app, web"
    exit 1
fi

if [[ "$COUNT" -lt 1 || "$COUNT" -gt 100 ]]; then
    echo "ERROR: --count must be between 1 and 100"
    exit 1
fi

#===============================================================================
# Helper Functions
#===============================================================================
log_info() { echo -e "\033[0;34m[INFO]\033[0m $1"; }
log_ok()   { echo -e "\033[0;32m[OK]\033[0m $1"; }
log_err()  { echo -e "\033[0;31m[ERROR]\033[0m $1"; }

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT_FILE="test-instances-${TIMESTAMP}.csv"

# Cleanup temp files on exit
trap 'rm -f /tmp/lt-data-*.json' EXIT


#===============================================================================
# Generate UserData (matches create-domain-controller.sh pattern)
#===============================================================================
generate_userdata() {
    local hostname="$1"
    local ip="$2"
    local gateway="$3"
    local prefix_length="$4"
    local dns_servers="$5"
    local dns_suffix="$6"

    read -r -d '' USERDATA_SCRIPT << 'USERDATA_EOF' || true
<powershell>
Start-Sleep -Seconds 30
$adapter = Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object -First 1
Rename-NetAdapter -Name $adapter.Name -NewName "PRIMARY"
$adapter = Get-NetAdapter -Name "PRIMARY"
Set-NetIPInterface -InterfaceAlias $adapter.Name -Dhcp Disabled
Get-NetIPAddress -InterfaceAlias $adapter.Name -AddressFamily IPv4 | Remove-NetIPAddress -Confirm:$false
Get-NetRoute -InterfaceAlias $adapter.Name -AddressFamily IPv4 | Where-Object {$_.DestinationPrefix -eq "0.0.0.0/0"} | Remove-NetRoute -Confirm:$false
Start-Sleep -Seconds 5
New-NetIPAddress -InterfaceAlias $adapter.Name -IPAddress __IP__ -PrefixLength __PREFIX__ -DefaultGateway __GATEWAY__
Set-DnsClientServerAddress -InterfaceAlias $adapter.Name -ServerAddresses __DNS_SERVERS__
Set-DnsClient -InterfaceAlias $adapter.Name -ConnectionSpecificSuffix "__DNS_SUFFIX__"
Disable-NetAdapterBinding -Name $adapter.Name -ComponentID ms_tcpip6
Disable-NetAdapterBinding -Name $adapter.Name -ComponentID ms_lltdio
Disable-NetAdapterBinding -Name $adapter.Name -ComponentID ms_rspndr
Disable-NetAdapterBinding -Name $adapter.Name -ComponentID ms_pacer
Rename-Computer -NewName "__HOSTNAME__" -Force -Restart
</powershell>
USERDATA_EOF

    USERDATA_SCRIPT="${USERDATA_SCRIPT//__IP__/$ip}"
    USERDATA_SCRIPT="${USERDATA_SCRIPT//__PREFIX__/$prefix_length}"
    USERDATA_SCRIPT="${USERDATA_SCRIPT//__GATEWAY__/$gateway}"
    USERDATA_SCRIPT="${USERDATA_SCRIPT//__DNS_SERVERS__/$dns_servers}"
    USERDATA_SCRIPT="${USERDATA_SCRIPT//__DNS_SUFFIX__/$dns_suffix}"
    USERDATA_SCRIPT="${USERDATA_SCRIPT//__HOSTNAME__/$hostname}"

    echo "$USERDATA_SCRIPT" | base64 | tr -d '\n'
}


#===============================================================================
# Create Launch Template + Launch Instance (per-instance)
#===============================================================================
launch_instance() {
    local name="$1"
    local ip="$2"
    local subnet="$3"
    local gateway="$4"
    local prefix_length="$5"
    local dns_servers="$6"
    local dns_suffix="$7"
    local resource_type="$8"
    local priority="$9"
    local wave="${10}"
    local service_name="${11}"
    local customer="${12}"

    if [[ "$DRY_RUN" == true ]]; then
        echo "  [DRY-RUN] LT: $name | IP: $ip | GW: $gateway | Subnet: $subnet | Wave: $wave"
        return 0
    fi

    # Check if launch template already exists
    EXISTING_LT=$(aws ec2 describe-launch-templates \
        --launch-template-names "$name" \
        --region "$REGION" \
        --query 'LaunchTemplates[0].LaunchTemplateId' \
        --output text 2>/dev/null || echo "")

    if [[ -n "$EXISTING_LT" && "$EXISTING_LT" != "None" ]]; then
        log_info "Launch template exists: $name ($EXISTING_LT)"
        LT_ID="$EXISTING_LT"
    else
        # Generate UserData
        USERDATA_BASE64=$(generate_userdata "$name" "$ip" "$gateway" "$prefix_length" "$dns_servers" "$dns_suffix")

        # Get AZ from subnet
        AZ_ID=$(aws ec2 describe-subnets \
            --subnet-ids "$subnet" \
            --region "$REGION" \
            --query 'Subnets[0].AvailabilityZoneId' \
            --output text)

        # Build launch template JSON
        local lt_file="/tmp/lt-data-${name}.json"
        cat > "$lt_file" << EOF
{
    "EbsOptimized": true,
    "IamInstanceProfile": {"Name": "$IAM_PROFILE"},
    "NetworkInterfaces": [{
        "AssociatePublicIpAddress": false,
        "DeleteOnTermination": true,
        "DeviceIndex": 0,
        "Groups": ["$SECURITY_GROUP"],
        "InterfaceType": "interface",
        "PrivateIpAddresses": [{"Primary": true, "PrivateIpAddress": "$ip"}],
        "SubnetId": "$subnet",
        "NetworkCardIndex": 0
    }],
    "ImageId": "$AMI_ID",
    "InstanceType": "$INSTANCE_TYPE",
    "KeyName": "$KEY_NAME",
    "Monitoring": {"Enabled": false},
    "Placement": {"AvailabilityZoneId": "$AZ_ID", "Tenancy": "default"},
    "DisableApiTermination": false,
    "InstanceInitiatedShutdownBehavior": "stop",
    "UserData": "$USERDATA_BASE64",
    "TagSpecifications": [
        {"ResourceType": "instance", "Tags": [
            {"Key": "Name", "Value": "$name"},
            {"Key": "ResourceType", "Value": "$resource_type"},
            {"Key": "AWSDRS", "Value": "AllowLaunchingIntoThisInstance"},
            {"Key": "BusinessUnit", "Value": "HRP"},
            {"Key": "Customer", "Value": "$customer"},
            {"Key": "Service", "Value": "$service_name"},
            {"Key": "dr:enabled", "Value": "true"},
            {"Key": "dr:recovery-strategy", "Value": "drs"},
            {"Key": "dr:priority", "Value": "$priority"},
            {"Key": "dr:wave", "Value": "$wave"},
            {"Key": "MonitoringLevel", "Value": "Standard"},
            {"Key": "Application", "Value": "HRP-Core-Platform"},
            {"Key": "Environment", "Value": "Dev"},
            {"Key": "ComplianceScope", "Value": "None"},
            {"Key": "Backup", "Value": "NotRequired"},
            {"Key": "DataClassification", "Value": "Internal"},
            {"Key": "Owner", "Value": "ie@healthedge.com"}
        ]},
        {"ResourceType": "network-interface", "Tags": [
            {"Key": "Name", "Value": "$name"},
            {"Key": "ResourceType", "Value": "$resource_type"},
            {"Key": "Environment", "Value": "Dev"}
        ]},
        {"ResourceType": "volume", "Tags": [
            {"Key": "Name", "Value": "$name"},
            {"Key": "ResourceType", "Value": "$resource_type"},
            {"Key": "Environment", "Value": "Dev"}
        ]}
    ],
    "MetadataOptions": {"HttpTokens": "required", "HttpPutResponseHopLimit": 2, "HttpEndpoint": "enabled"},
    "PrivateDnsNameOptions": {"HostnameType": "ip-name", "EnableResourceNameDnsARecord": false, "EnableResourceNameDnsAAAARecord": false}
}
EOF

        LT_ID=$(aws ec2 create-launch-template \
            --launch-template-name "$name" \
            --launch-template-data "file://$lt_file" \
            --region "$REGION" \
            --query 'LaunchTemplate.LaunchTemplateId' \
            --output text 2>&1) || {
                log_err "Failed to create launch template $name: $LT_ID"
                echo "$name,$ip,$subnet,LT_FAILED,,," >> "$OUTPUT_FILE"
                rm -f "$lt_file"
                return 1
            }

        rm -f "$lt_file"
    fi

    # Launch instance from template
    INSTANCE_ID=$(aws ec2 run-instances \
        --launch-template "LaunchTemplateId=$LT_ID" \
        --region "$REGION" \
        --query 'Instances[0].InstanceId' \
        --output text 2>&1) || {
            log_err "Failed to launch $name: $INSTANCE_ID"
            echo "$name,$ip,$subnet,LAUNCH_FAILED,$LT_ID,," >> "$OUTPUT_FILE"
            return 1
        }

    log_ok "$name | $ip | LT: $LT_ID | Instance: $INSTANCE_ID"
    echo "$name,$ip,$subnet,$INSTANCE_ID,$LT_ID,$resource_type,$priority,$wave" >> "$OUTPUT_FILE"
    return 0
}


#===============================================================================
# Launch a full tier (100 instances)
#===============================================================================
launch_tier() {
    local tier_name="$1"
    local name_prefix="$2"
    local az_suffix="$3"
    local ip_prefix="$4"
    local subnet_id="$5"
    local gateway="$6"
    local prefix_length="$7"
    local dns_servers="$8"
    local dns_suffix="$9"
    local resource_type="${10}"
    local priority="${11}"
    local wave="${12}"
    local service_name="${13}"
    echo ""
    echo "======================================================"
    echo " Launching $COUNT ${tier_name} Servers"
    echo " Subnet: $subnet_id"
    echo " IP Range: ${ip_prefix}.$((IP_START + START_INDEX - 1)) - ${ip_prefix}.$((IP_START + START_INDEX + COUNT - 2))"
    echo " Gateway: $gateway / Prefix: /$prefix_length"
    echo " Pattern: Launch Template + UserData (rename + re-IP)"
    echo "======================================================"

    local success=0
    local failed=0

    for i in $(seq "$START_INDEX" "$((START_INDEX + COUNT - 1))"); do
        local num=$(printf "%03d" "$i")
        local name="hrp-dev-${name_prefix}-${az_suffix}-${num}"
        local last_octet=$((IP_START + i - 1))
        local ip="${ip_prefix}.${last_octet}"

        # Assign customer based on position (25 per customer)
        if [[ "$i" -le 25 ]]; then
            local customer="CustomerA"
        elif [[ "$i" -le 50 ]]; then
            local customer="CustomerB"
        elif [[ "$i" -le 75 ]]; then
            local customer="CustomerC"
        else
            local customer="CustomerD"
        fi

        launch_instance "$name" "$ip" "$subnet_id" \
            "$gateway" "$prefix_length" "$dns_servers" "$dns_suffix" \
            "$resource_type" "$priority" "$wave" "$service_name" "$customer"

        if [[ $? -eq 0 ]]; then
            ((success++))
        else
            ((failed++))
        fi

        # Batch throttle to avoid API rate limits
        if [[ $(( (i - START_INDEX + 1) % BATCH_SIZE)) -eq 0 && "$DRY_RUN" != true && "$i" -lt "$((START_INDEX + COUNT - 1))" ]]; then
            log_info "Batch $(( (i - START_INDEX + 1) / BATCH_SIZE)) complete. Pausing ${BATCH_DELAY}s..."
            sleep "$BATCH_DELAY"
        fi
    done

    echo "------------------------------------------------------"
    echo " ${tier_name}: $success launched, $failed failed"
    echo "------------------------------------------------------"
}

#===============================================================================
# Main Execution
#===============================================================================
echo "######################################################"
echo "# Test Instance Deployment"
echo "# Pattern: Launch Template + UserData (hostname + IP)"
echo "######################################################"
echo ""
echo "Region:         $REGION"
echo "VPC:            $VPC_ID"
echo "Instance Type:  $INSTANCE_TYPE"
echo "AMI:            $AMI_ID"
echo "Security Group: $SECURITY_GROUP"
echo "IAM Profile:    $IAM_PROFILE"
echo "Key Pair:       $KEY_NAME"
echo "Count per tier: $COUNT"
echo "Tier filter:    $TIER_FILTER"
echo "Dry run:        $DRY_RUN"
echo ""

if [[ "$DRY_RUN" != true ]]; then
    # Verify AWS credentials
    CALLER=$(aws sts get-caller-identity --region "$REGION" --query 'Account' --output text 2>/dev/null || echo "")
    if [[ -z "$CALLER" ]]; then
        log_err "AWS credentials not configured."
        exit 1
    fi
    log_ok "AWS Account: $CALLER"

    # Initialize output CSV
    echo "Name,IP,Subnet,InstanceId,LaunchTemplateId,ResourceType,Priority,Wave" > "$OUTPUT_FILE"
    log_info "Tracking file: $OUTPUT_FILE"
fi

echo ""

# DB Servers: wave 1, critical priority
if [[ "$TIER_FILTER" == "all" || "$TIER_FILTER" == "db" ]]; then
    launch_tier "Database" "db" "az4" \
        "$DB_IP_PREFIX" "$SUBNETAZ4_ID" "$DB_GATEWAY" "$DB_PREFIX_LENGTH" \
        "$DB_DNS_SERVERS" "$DB_DNS_SUFFIX" \
        "Database" "critical" "1" "DatabaseServer"
fi

# App Servers: wave 2, high priority
if [[ "$TIER_FILTER" == "all" || "$TIER_FILTER" == "app" ]]; then
    launch_tier "Application" "app" "az6" \
        "$APP_IP_PREFIX" "$SUBNETAZ6_ID" "$APP_GATEWAY" "$APP_PREFIX_LENGTH" \
        "$APP_DNS_SERVERS" "$APP_DNS_SUFFIX" \
        "Compute" "high" "2" "ApplicationServer"
fi

# Web Servers: wave 3, medium priority
if [[ "$TIER_FILTER" == "all" || "$TIER_FILTER" == "web" ]]; then
    launch_tier "Web" "web" "az1" \
        "$WEB_IP_PREFIX" "$SUBNETAZ1_ID" "$WEB_GATEWAY" "$WEB_PREFIX_LENGTH" \
        "$WEB_DNS_SERVERS" "$WEB_DNS_SUFFIX" \
        "Web" "medium" "3" "WebServer"
fi

echo ""
echo "######################################################"
echo "# Deployment Complete"
echo "######################################################"
echo ""

if [[ "$DRY_RUN" == true ]]; then
    echo "DRY RUN - No resources were created."
else
    LAUNCHED=$(tail -n +2 "$OUTPUT_FILE" | grep -v "FAILED" | wc -l | tr -d ' ')
    ERRORS=$(tail -n +2 "$OUTPUT_FILE" | grep "FAILED" | wc -l | tr -d ' ')
    echo "Launched: $LAUNCHED"
    echo "Failed:   $ERRORS"
    echo "Details:  $OUTPUT_FILE"
    echo ""
    echo "Each instance will:"
    echo "  1. Boot with DHCP"
    echo "  2. UserData renames NIC to PRIMARY"
    echo "  3. Configures static IP, gateway, DNS"
    echo "  4. Renames hostname to match Name tag"
    echo "  5. Reboots to apply hostname"
    echo ""
    echo "To check status:"
    echo "  AWS_PAGER=\"\" aws ec2 describe-instances --region $REGION \\"
    echo "    --filters 'Name=tag:Application,Values=HRP-Core-Platform' 'Name=instance-state-name,Values=running' \\"
    echo "    --query 'Reservations[].Instances[].[Tags[?Key==\`Name\`].Value|[0],PrivateIpAddress,State.Name]' \\"
    echo "    --output table"
    echo ""
    echo "To terminate all test instances:"
    echo "  IDS=\$(AWS_PAGER=\"\" aws ec2 describe-instances --region $REGION \\"
    echo "    --filters 'Name=tag:Application,Values=HRP-Core-Platform' 'Name=instance-state-name,Values=running' \\"
    echo "    --query 'Reservations[].Instances[].InstanceId' --output text)"
    echo "  AWS_PAGER=\"\" aws ec2 terminate-instances --region $REGION --instance-ids \$IDS"
    echo ""
    echo "To delete all launch templates:"
    echo "  for lt in \$(AWS_PAGER=\"\" aws ec2 describe-launch-templates --region $REGION \\"
    echo "    --query 'LaunchTemplates[?starts_with(LaunchTemplateName,\`hrp-dev-\`)].LaunchTemplateName' --output text); do"
    echo "    AWS_PAGER=\"\" aws ec2 delete-launch-template --launch-template-name \"\$lt\" --region $REGION"
    echo "  done"
fi

echo ""
echo "######################################################"
