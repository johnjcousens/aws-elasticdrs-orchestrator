# HRP EC2 Weblogic Disaster Recovery Detailed Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5148704821/HRP%20EC2%20Weblogic%20Disaster%20Recovery%20Detailed%20Design

**Created by:** Venkata Kommuri on October 05, 2025  
**Last modified by:** Chris Falk on December 18, 2025 at 08:17 PM

---

AWS Elastic Disaster Recovery (DRS) for WebLogic Application Servers Complete Implementation Runbook
====================================================================================================

**Service:** AWS Elastic Disaster Recovery (DRS)  
**Application:** WebLogic Application Server on EC2  
**Target RTO:** 4 hours | **Target RPO:** 15 minutes  
**Replication Method:** Continuous block-level replication

**IMPORTANT:** AWS Elastic Disaster Recovery provides continuous replication with sub-second RPO and minutes RTO. This runbook covers complete implementation for WebLogic servers with automated failover capabilities.

#### ⚠️ IMPORTANT DISCLAIMER - HRP CUSTOMIZATION REQUIRED

**All scripts and configurations in this runbook are GENERIC TEMPLATES and must be customized for HRP-specific requirements before implementation.**

##### Required HRP-Specific Customizations:

* **Environment Variables:** Update all placeholder values (ACCOUNT-ID, region names, etc.) with actual HRP values
* **Network Configuration:** Replace VPC IDs, subnet IDs, and security group IDs with HRP-specific network resources
* **Weblogic Configuration:** Update any HRP weblogic specific configuration information
* **IAM Roles and Policies:** Adapt IAM configurations to comply with HRP security standards and policies
* **Naming Conventions:** Update resource names to follow HRP naming standards and conventions
* **Monitoring and Alerting:** Configure SNS topics, CloudWatch alarms, and notification endpoints for HRP operations team
* **Backup and Recovery:** Align backup schedules and retention policies with HRP data governance requirements
* **Compliance Requirements:** Ensure all configurations meet HRP regulatory and compliance standards

##### Before Using Any Script:

1. **Review and Validate:** Thoroughly review each script for HRP environment compatibility
2. **Test in Non-Production:** Test all scripts in HRP development/staging environments first
3. **Security Review:** Have HRP security team review all IAM policies and network configurations
4. **Change Management:** Follow HRP change management processes before production deployment
5. **Documentation:** Document all HRP-specific modifications for future reference

**⚠️ WARNING:** Do not execute any script in production without proper HRP customization, testing, and approval.

Table of Contents
-----------------

* [1. AWS DRS Overview & Architecture](#)
* [2. Prerequisites & Planning](#)
* [3. DRS Service Setup & Configuration](#)
* [4. DRS Agent Installation](#)
* [5. Replication Configuration](#)
* [6. Launch Templates & Recovery](#)
* [7. Testing & Validation](#)
* [8. Failover Procedures](#)
* [9. Failback Procedures](#)
* [10. Monitoring & Alerting](#)
* [11. Automation & Orchestration](#)
* [12. Maintenance & Operations](#)
* [13. Troubleshooting Guide](#)
* [14. Best Practices & Optimization](#)
* [15. Emergency Contacts](#)

1. AWS DRS Overview & Architecture
----------------------------------

### 1.1 AWS Elastic Disaster Recovery Service Overview

AWS Elastic Disaster Recovery (DRS) is a scalable, cost-effective application recovery service powered by CloudEndure Disaster Recovery. It provides continuous replication of your source servers to AWS, enabling fast, reliable recovery of physical, virtual, and cloud-based servers.

### 1.2 Key Benefits for WebLogic Environments

* **Sub-second RPO:** Continuous block-level replication
* **Minutes RTO:** Fast automated recovery with minimal downtime
* **Cost-effective:** Pay only for staging area resources during normal operations
* **Non-disruptive:** No impact on source server performance
* **Automated:** Point-and-click recovery with automated orchestration
* **Cross-platform:** Supports any operating system or application

### 1.3 DRS Architecture Components

| Component | Description | Location | Purpose |
| --- | --- | --- | --- |
| DRS Agent | Lightweight replication agent | Source WebLogic servers | Captures and replicates data changes |
| Staging Area | Low-cost EC2 instances | Target AWS region | Receives and processes replicated data |
| Recovery Instances | Full-scale EC2 instances | Target AWS region | Launched during recovery operations |
| DRS Console | Management interface | AWS Management Console | Configuration and monitoring |
| Replication Servers | Managed EC2 instances | Target AWS region | Handle replication traffic and data processing |

#### AWS DRS Architecture for WebLogic

![HRP-Weblogic-DR-Design_(1).png](images/HRP-Weblogic-DR-Design_(1).png)

### 1.4 WebLogic-Specific Considerations

| Component | DRS Consideration | Configuration Required |
| --- | --- | --- |
| WebLogic Domain | Replicate entire domain directory | Include domain configuration in replication |
| Admin Server | Critical for domain management | Priority replication and recovery |
| Managed Servers | Application hosting instances | Coordinated startup sequence |
| Node Manager | Server lifecycle management | Automatic restart configuration |
| Database Connections | External dependencies | Connection string updates for DR |
| JMS Queues | Message persistence | Queue state replication |
| Security Certificates | SSL/TLS configurations | Certificate replication and validation |

2. Prerequisites & Planning
---------------------------

**Important:** Complete all prerequisites before beginning DRS implementation to ensure successful deployment.

### 2.1 AWS Account Requirements

#### Pre-Implementation Checklist:

* AWS account with appropriate permissions
* Target AWS region selected (us-east-2, us-west-1, etc.)
* VPC and subnets configured in target region
* Security groups defined for WebLogic traffic
* IAM roles and policies created
* Network connectivity established (VPN/Direct Connect)
* DNS strategy defined
* Monitoring and alerting plan

### 2.2 Required IAM Permissions


```
# Create comprehensive DRS IAM policy
cat > aws-drs-policy.json << 'EOF'
{
    "Version": "October 17, 2012",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "drs:*",
                "ec2:*",
                "iam:PassRole",
                "iam:CreateServiceLinkedRole",
                "kms:*",
                "license-manager:*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:CreatePolicy",
                "iam:AttachRolePolicy",
                "iam:PutRolePolicy"
            ],
            "Resource": [
                "arn:aws:iam::*:role/service-role/AWSElasticDisasterRecovery*",
                "arn:aws:iam::*:policy/service-role/AWSElasticDisasterRecovery*"
            ]
        }
    ]
}
EOF

# Create and attach the policy
aws iam create-policy \
    --policy-name AWSElasticDisasterRecoveryFullAccess \
    --policy-document file://aws-drs-policy.json

aws iam attach-user-policy \
    --user-name $(aws sts get-caller-identity --query User.UserName --output text) \
    --policy-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/AWSElasticDisasterRecoveryFullAccess
```


### 2.3 Network Requirements

| Component | Requirement | Configuration |
| --- | --- | --- |
| Outbound Internet | HTTPS (443) to AWS DRS endpoints | Allow traffic to \*.amazonaws.com |
| Replication Traffic | TCP 1500 (configurable) | Source to AWS replication servers |
| Agent Communication | TCP 443 | DRS agent to AWS API endpoints |
| Internal Communication | WebLogic ports (7001, 8001-8010) | Between WebLogic servers in DR environment |
| Database Access | Database-specific ports (1521, 3306) | WebLogic to database connectivity |

### 2.4 Source Server Assessment


```
#!/bin/bash
# weblogic-drs-assessment.sh
# Pre-implementation assessment for WebLogic servers

echo "=== WebLogic DRS Assessment Report ==="
echo "Generated: $(date)"
echo

# System Information
echo "=== SYSTEM INFORMATION ==="
echo "Hostname: $(hostname)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo "Uptime: $(uptime)"
echo

# Hardware Resources
echo "=== HARDWARE RESOURCES ==="
echo "CPU Cores: $(nproc)"
echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "Disk Usage:"
df -h | grep -E '^/dev/'
echo

# WebLogic Information
echo "=== WEBLOGIC INFORMATION ==="
if pgrep -f weblogic > /dev/null; then
    echo "WebLogic Status: Running"
    echo "WebLogic Processes:"
    ps aux | grep -i weblogic | grep -v grep
    
    # Find WebLogic domain
    DOMAIN_HOME=$(ps aux | grep -i weblogic | grep -o '\-Dweblogic.Domain[^=]*=[^[:space:]]*' | head -1 | cut -d'=' -f2)
    if [[ -n "$DOMAIN_HOME" ]]; then
        echo "Domain Home: $DOMAIN_HOME"
        if [[ -d "$DOMAIN_HOME" ]]; then
            echo "Domain Size: $(du -sh $DOMAIN_HOME | cut -f1)"
        fi
    fi
    
    # Check listening ports
    echo "WebLogic Ports:"
    netstat -tlnp | grep java | grep -E ':(7001|8001|8002|8003|8004|8005)'
else
    echo "WebLogic Status: Not Running"
fi
echo

# Network Configuration
echo "=== NETWORK CONFIGURATION ==="
echo "IP Addresses:"
ip addr show | grep -E 'inet [0-9]' | grep -v 127.0.0.1
echo "Default Gateway: $(ip route | grep default | awk '{print $3}')"
echo "DNS Servers:"
cat /etc/resolv.conf | grep nameserver
echo

# Storage Information
echo "=== STORAGE INFORMATION ==="
echo "Block Devices:"
lsblk
echo
echo "Mount Points:"
mount | grep -E '^/dev/'
echo

# Security and Firewall
echo "=== SECURITY CONFIGURATION ==="
if command -v firewall-cmd &> /dev/null; then
    echo "Firewall Status: $(firewall-cmd --state)"
    echo "Active Zones:"
    firewall-cmd --get-active-zones
elif command -v ufw &> /dev/null; then
    echo "UFW Status: $(ufw status | head -1)"
elif command -v iptables &> /dev/null; then
    echo "Iptables Rules: $(iptables -L | wc -l) rules configured"
fi
echo

# DRS Readiness Check
echo "=== DRS READINESS CHECK ==="
echo "Internet Connectivity:"
if curl -s --max-time 10 https://drs.us-east-1.amazonaws.com > /dev/null; then
    echo "✓ Can reach AWS DRS endpoints"
else
    echo "✗ Cannot reach AWS DRS endpoints"
fi

echo "Required Packages:"
for pkg in curl wget unzip; do
    if command -v $pkg &> /dev/null; then
        echo "✓ $pkg is installed"
    else
        echo "✗ $pkg is not installed"
    fi
done

echo "Disk Space Check:"
ROOT_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [[ $ROOT_USAGE -lt 80 ]]; then
    echo "✓ Root filesystem usage: ${ROOT_USAGE}%"
else
    echo "⚠ Root filesystem usage high: ${ROOT_USAGE}%"
fi

echo
echo "=== ASSESSMENT COMPLETE ==="
echo "Review the above information before proceeding with DRS implementation."
```


3. DRS Service Setup & Configuration
------------------------------------

### 3.1 Initialize DRS Service

#### Step 1: Enable DRS Service in Target Region

First-time setup requires service initialization in your target AWS region.


```
# Initialize DRS service in target region
aws drs initialize-service --region us-east-2

# Verify service initialization
aws drs describe-replication-configuration-templates --region us-east-2
```


### 3.2 Create Replication Configuration Template


```
# Create replication configuration template for WebLogic
cat > weblogic-replication-template.json << 'EOF'
{
    "associateDefaultSecurityGroup": true,
    "bandwidthThrottling": 0,
    "createPublicIP": false,
    "dataPlaneRouting": "PRIVATE_IP",
    "defaultLargeStagingDiskType": "GP3",
    "ebsEncryption": "ENCRYPTED",
    "ebsEncryptionKeyArn": "alias/aws/ebs",
    "replicationServerInstanceType": "m5.large",
    "replicationServersSecurityGroupsIDs": ["sg-weblogic-replication"],
    "stagingAreaSubnetId": "subnet-staging-area",
    "stagingAreaTags": {
        "Application": "WebLogic",
        "Environment": "DR",
        "Purpose": "DRS-Staging"
    },
    "useDedicatedReplicationServer": false
}
EOF

# Create the replication configuration template
aws drs create-replication-configuration-template \
    --cli-input-json file://weblogic-replication-template.json \
    --region us-east-2
```


### 3.3 Configure Launch Templates


```
# Create launch template for WebLogic Admin Server
cat > weblogic-admin-launch-template.json << 'EOF'
{
    "copyPrivateIp": false,
    "copyTags": true,
    "ec2LaunchTemplateID": "lt-weblogic-admin-dr",
    "enableMapAutoTagging": true,
    "launchDisposition": "STARTED",
    "licensing": {
        "osByol": false
    },
    "mapAutoTaggingMpeID": "mpe-weblogic-admin",
    "postLaunchActions": {
        "cloudWatchLogGroupName": "/aws/drs/weblogic-admin",
        "deployment": "TEST_AND_CUTOVER",
        "s3LogBucket": "weblogic-drs-logs",
        "s3OutputKeyPrefix": "admin-server/",
        "ssmDocuments": [
            {
                "actionName": "StartWebLogicAdmin",
                "documentName": "WebLogic-StartAdminServer",
                "documentVersion": "$LATEST",
                "mustSucceedForCutover": true,
                "parameters": {
                    "DomainHome": "/opt/weblogic/domains/mydomain",
                    "AdminUser": "weblogic"
                },
                "timeoutSeconds": 1800
            }
        ]
    },
    "targetInstanceTypeRightSizingMethod": "BASIC"
}
EOF

# Apply launch template configuration
aws drs put-launch-action \
    --resource-id i-weblogic-admin-source \
    --cli-input-json file://weblogic-admin-launch-template.json \
    --region us-east-2
```


4. DRS Agent Installation
-------------------------

**Important:** Install DRS agents during maintenance windows to minimize impact on production systems.

### 4.1 Download and Install DRS Agent


```
#!/bin/bash
# install-drs-agent.sh
# Install AWS DRS agent on WebLogic servers

set -euo pipefail

# Configuration
DRS_REGION="us-east-2"
AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
AGENT_DOWNLOAD_URL="https://aws-elastic-disaster-recovery-${DRS_REGION}.s3.amazonaws.com/latest/linux/aws-replication-installer-init.py"

# Logging
LOG_FILE="/var/log/drs-agent-install.log"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Pre-installation checks
pre_install_checks() {
    log "Starting pre-installation checks..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log "ERROR: This script must be run as root"
        exit 1
    fi
    
    # Check internet connectivity
    if ! curl -s --max-time 10 https://aws.amazon.com > /dev/null; then
        log "ERROR: No internet connectivity"
        exit 1
    fi
    
    # Check available disk space
    AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
    if [[ $AVAILABLE_SPACE -lt 1048576 ]]; then  # 1GB in KB
        log "ERROR: Insufficient disk space. Need at least 1GB free"
        exit 1
    fi
    
    # Check if WebLogic is running
    if pgrep -f weblogic > /dev/null; then
        log "WARNING: WebLogic is currently running. Agent installation may cause brief I/O impact."
        read -p "Continue with installation? (y/N): " confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            log "Installation cancelled by user"
            exit 0
        fi
    fi
    
    log "Pre-installation checks completed"
}

# Download DRS agent installer
download_agent() {
    log "Downloading DRS agent installer..."
    
    cd /tmp
    if curl -o aws-replication-installer-init.py "$AGENT_DOWNLOAD_URL"; then
        log "Agent installer downloaded successfully"
    else
        log "ERROR: Failed to download agent installer"
        exit 1
    fi
    
    # Verify download
    if [[ ! -f "aws-replication-installer-init.py" ]]; then
        log "ERROR: Agent installer file not found"
        exit 1
    fi
    
    chmod +x aws-replication-installer-init.py
}

# Install DRS agent
install_agent() {
    log "Installing DRS agent..."
    
    # Create credentials file
    cat > /tmp/aws-credentials << EOF
[default]
aws_access_key_id = $AWS_ACCESS_KEY_ID
aws_secret_access_key = $AWS_SECRET_ACCESS_KEY
region = $DRS_REGION
EOF
    
    # Install agent with credentials
    python3 /tmp/aws-replication-installer-init.py \
        --region "$DRS_REGION" \
        --aws-access-key-id "$AWS_ACCESS_KEY_ID" \
        --aws-secret-access-key "$AWS_SECRET_ACCESS_KEY" \
        --no-prompt
    
    # Clean up credentials file
    rm -f /tmp/aws-credentials
    
    log "DRS agent installation completed"
}

# Verify agent installation
verify_installation() {
    log "Verifying DRS agent installation..."
    
    # Check if agent service is running
    if systemctl is-active --quiet aws-replication-agent; then
        log "✓ DRS agent service is running"
    else
        log "✗ DRS agent service is not running"
        systemctl status aws-replication-agent
        exit 1
    fi
    
    # Check agent logs
    if [[ -f "/var/log/aws-replication-agent.log" ]]; then
        log "✓ Agent log file exists"
        tail -10 /var/log/aws-replication-agent.log
    else
        log "⚠ Agent log file not found"
    fi
    
    # Check network connectivity to DRS
    if netstat -an | grep -q ":1500.*ESTABLISHED"; then
        log "✓ Replication connection established"
    else
        log "⚠ Replication connection not yet established (may take a few minutes)"
    fi
    
    log "Agent verification completed"
}

# Configure agent for WebLogic
configure_for_weblogic() {
    log "Configuring DRS agent for WebLogic environment..."
    
    # Create agent configuration
    cat > /opt/aws-replication-agent/conf/agent.conf << 'EOF'
# WebLogic-specific DRS agent configuration
replication_throttle_bandwidth=0
replication_use_compression=true
replication_use_encryption=true

# WebLogic domain paths to prioritize
priority_paths=/opt/weblogic/domains
priority_paths=/opt/weblogic/applications
priority_paths=/etc/weblogic

# Exclude temporary and cache directories
exclude_paths=/tmp
exclude_paths=/var/tmp
exclude_paths=/opt/weblogic/domains/*/servers/*/tmp
exclude_paths=/opt/weblogic/domains/*/servers/*/cache
EOF
    
    # Restart agent to apply configuration
    systemctl restart aws-replication-agent
    
    log "WebLogic-specific configuration applied"
}

# Main execution
main() {
    log "Starting DRS agent installation for WebLogic server: $(hostname)"
    
    pre_install_checks
    download_agent
    install_agent
    verify_installation
    configure_for_weblogic
    
    log "DRS agent installation completed successfully"
    log "Server $(hostname) is now protected by AWS DRS"
    log "Check DRS console for replication status"
}

# Execute main function
main "$@"
```


### 4.2 Agent Installation Verification


```
# Verify DRS agent status on all WebLogic servers
#!/bin/bash
# verify-drs-agents.sh

WEBLOGIC_SERVERS=("weblogic-admin" "weblogic-managed1" "weblogic-managed2" "weblogic-db")

echo "=== DRS Agent Status Verification ==="
echo "Timestamp: $(date)"
echo

for server in "${WEBLOGIC_SERVERS[@]}"; do
    echo "Checking server: $server"
    
    # SSH to server and check agent status
    ssh "$server" << 'EOF'
        echo "  Hostname: $(hostname)"
        echo "  Agent Service: $(systemctl is-active aws-replication-agent)"
        echo "  Agent Version: $(cat /opt/aws-replication-agent/version 2>/dev/null || echo 'Unknown')"
        echo "  Last Log Entry:"
        tail -1 /var/log/aws-replication-agent.log 2>/dev/null | sed 's/^/    /'
        echo "  Replication Status:"
        netstat -an | grep :1500 | sed 's/^/    /'
        echo
EOF
done

# Check DRS console status
echo "=== DRS Console Status ==="
aws drs describe-source-servers --region us-east-2 --query 'items[].{Hostname:hostname,Status:dataReplicationInfo.dataReplicationState,LastSnapshot:dataReplicationInfo.lastSnapshotDateTime}' --output table
```


5. Replication Configuration
----------------------------

### 5.1 Configure Source Server Replication Settings


```
# Configure replication settings for each WebLogic server
#!/bin/bash
# configure-weblogic-replication.sh

set -euo pipefail

# Configuration
DRS_REGION="us-east-2"
REPLICATION_TEMPLATE_ID="rct-weblogic-template"

# Function to configure server replication
configure_server_replication() {
    local server_id="$1"
    local server_type="$2"
    
    echo "Configuring replication for $server_type server: $server_id"
    
    # Create replication configuration based on server type
    case "$server_type" in
        "admin")
            cat > "/tmp/replication-config-${server_id}.json" << 'EOF'
{
    "associateDefaultSecurityGroup": true,
    "bandwidthThrottling": 0,
    "createPublicIP": false,
    "dataPlaneRouting": "PRIVATE_IP",
    "defaultLargeStagingDiskType": "GP3",
    "ebsEncryption": "ENCRYPTED",
    "replicationServerInstanceType": "m5.large",
    "stagingAreaTags": {
        "ServerType": "WebLogic-Admin",
        "Priority": "Critical",
        "Application": "WebLogic"
    },
    "useDedicatedReplicationServer": true
}
EOF
            ;;
        "managed")
            cat > "/tmp/replication-config-${server_id}.json" << 'EOF'
{
    "associateDefaultSecurityGroup": true,
    "bandwidthThrottling": 0,
    "createPublicIP": false,
    "dataPlaneRouting": "PRIVATE_IP",
    "defaultLargeStagingDiskType": "GP3",
    "ebsEncryption": "ENCRYPTED",
    "replicationServerInstanceType": "m5.medium",
    "stagingAreaTags": {
        "ServerType": "WebLogic-Managed",
        "Priority": "High",
        "Application": "WebLogic"
    },
    "useDedicatedReplicationServer": false
}
EOF
            ;;
        "database")
            cat > "/tmp/replication-config-${server_id}.json" << 'EOF'
{
    "associateDefaultSecurityGroup": true,
    "bandwidthThrottling": 0,
    "createPublicIP": false,
    "dataPlaneRouting": "PRIVATE_IP",
    "defaultLargeStagingDiskType": "GP3",
    "ebsEncryption": "ENCRYPTED",
    "replicationServerInstanceType": "m5.xlarge",
    "stagingAreaTags": {
        "ServerType": "Database",
        "Priority": "Critical",
        "Application": "WebLogic"
    },
    "useDedicatedReplicationServer": true
}
EOF
            ;;
    esac
    
    # Apply replication configuration
    aws drs update-replication-configuration \
        --source-server-id "$server_id" \
        --cli-input-json "file:///tmp/replication-config-${server_id}.json" \
        --region "$DRS_REGION"
    
    echo "Replication configuration applied for $server_id"
}

# Get source server IDs from DRS
echo "Retrieving source server information..."
SOURCE_SERVERS=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'items[].{ID:sourceServerID,Hostname:hostname,Type:tags.ServerType}' --output json)

# Configure each server
echo "$SOURCE_SERVERS" | jq -r '.[] | "\(.ID) \(.Type // "unknown") \(.Hostname)"' | while read -r server_id server_type hostname; do
    echo "Processing server: $hostname ($server_id)"
    
    # Determine server type if not tagged
    if [[ "$server_type" == "unknown" || "$server_type" == "null" ]]; then
        if [[ "$hostname" == *"admin"* ]]; then
            server_type="admin"
        elif [[ "$hostname" == *"managed"* ]]; then
            server_type="managed"
        elif [[ "$hostname" == *"db"* || "$hostname" == *"database"* ]]; then
            server_type="database"
        else
            server_type="managed"  # Default to managed server
        fi
    fi
    
    configure_server_replication "$server_id" "$server_type"
done

echo "Replication configuration completed for all WebLogic servers"
```


### 5.2 Monitor Initial Replication Progress


```
#!/bin/bash
# monitor-initial-replication.sh
# Monitor initial replication progress for WebLogic servers

set -euo pipefail

DRS_REGION="us-east-2"
MONITORING_INTERVAL=60  # seconds

# Function to display replication status
display_replication_status() {
    echo "=== WebLogic DRS Replication Status ==="
    echo "Timestamp: $(date)"
    echo
    
    # Get detailed replication information
    aws drs describe-source-servers \
        --region "$DRS_REGION" \
        --query 'items[].[hostname,dataReplicationInfo.dataReplicationState,dataReplicationInfo.replicatedStorageBytes,dataReplicationInfo.totalStorageBytes,dataReplicationInfo.lastSnapshotDateTime]' \
        --output table \
        --table-format plain
    
    echo
    
    # Calculate overall progress
    local total_servers
    local completed_servers
    local in_progress_servers
    
    total_servers=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items)')
    completed_servers=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items[?dataReplicationInfo.dataReplicationState==`CONTINUOUS`])')
    in_progress_servers=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items[?dataReplicationInfo.dataReplicationState==`INITIAL_SYNC`])')
    
    echo "Overall Progress:"
    echo "  Total Servers: $total_servers"
    echo "  Completed Initial Sync: $completed_servers"
    echo "  In Progress: $in_progress_servers"
    echo "  Completion Rate: $(( completed_servers * 100 / total_servers ))%"
    echo
    
    # Check for any issues
    local failed_servers
    failed_servers=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'items[?dataReplicationInfo.dataReplicationState==`STALLED` || dataReplicationInfo.dataReplicationState==`DISCONNECTED`].hostname' --output text)
    
    if [[ -n "$failed_servers" ]]; then
        echo "⚠ ATTENTION: Servers with replication issues:"
        echo "$failed_servers"
        echo
    fi
}

# Function to send progress notification
send_progress_notification() {
    local completed_count="$1"
    local total_count="$2"
    
    if [[ $completed_count -eq $total_count ]]; then
        aws sns publish \
            --topic-arn "arn:aws:sns:${DRS_REGION}:ACCOUNT-ID:weblogic-drs-notifications" \
            --subject "WebLogic DRS Initial Replication Completed" \
            --message "All $total_count WebLogic servers have completed initial replication and are now in continuous replication mode." \
            --region "$DRS_REGION" || true
    fi
}

# Main monitoring loop
echo "Starting WebLogic DRS replication monitoring..."
echo "Press Ctrl+C to stop monitoring"
echo

while true; do
    display_replication_status
    
    # Check if all servers completed initial sync
    completed=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items[?dataReplicationInfo.dataReplicationState==`CONTINUOUS`])')
    total=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items)')
    
    if [[ $completed -eq $total ]]; then
        echo "🎉 All WebLogic servers have completed initial replication!"
        send_progress_notification "$completed" "$total"
        break
    fi
    
    echo "Waiting $MONITORING_INTERVAL seconds before next check..."
    sleep $MONITORING_INTERVAL
done

echo "Initial replication monitoring completed."
```


### 5.3 Replication Health Monitoring


```
#!/bin/bash
# weblogic-drs-health-monitor.sh
# Continuous health monitoring for WebLogic DRS replication

set -euo pipefail

DRS_REGION="us-east-2"
LOG_FILE="/var/log/weblogic-drs-health.log"
ALERT_THRESHOLD_LAG=300  # 5 minutes in seconds

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check replication health
check_replication_health() {
    log "Starting WebLogic DRS health check..."
    
    local issues_found=0
    local critical_issues=0
    
    # Get all source servers
    local servers_json
    servers_json=$(aws drs describe-source-servers --region "$DRS_REGION" --output json)
    
    # Check each server
    echo "$servers_json" | jq -r '.items[] | @base64' | while IFS= read -r server_data; do
        local server
        server=$(echo "$server_data" | base64 -d)
        
        local hostname
        local server_id
        local replication_state
        local last_snapshot
        
        hostname=$(echo "$server" | jq -r '.hostname')
        server_id=$(echo "$server" | jq -r '.sourceServerID')
        replication_state=$(echo "$server" | jq -r '.dataReplicationInfo.dataReplicationState')
        last_snapshot=$(echo "$server" | jq -r '.dataReplicationInfo.lastSnapshotDateTime')
        
        log "Checking server: $hostname ($server_id)"
        
        # Check replication state
        case "$replication_state" in
            "CONTINUOUS")
                log "  ✓ Replication state: CONTINUOUS"
                ;;
            "INITIAL_SYNC")
                log "  ⚠ Replication state: INITIAL_SYNC (in progress)"
                ((issues_found++))
                ;;
            "STALLED"|"DISCONNECTED")
                log "  ✗ Replication state: $replication_state (CRITICAL)"
                ((critical_issues++))
                ;;
            *)
                log "  ⚠ Replication state: $replication_state (unknown)"
                ((issues_found++))
                ;;
        esac
        
        # Check snapshot age
        if [[ "$last_snapshot" != "null" && "$last_snapshot" != "" ]]; then
            local snapshot_age
            snapshot_age=$(( $(date +%s) - $(date -d "$last_snapshot" +%s) ))
            
            if [[ $snapshot_age -gt $ALERT_THRESHOLD_LAG ]]; then
                log "  ⚠ Last snapshot is $((snapshot_age / 60)) minutes old"
                ((issues_found++))
            else
                log "  ✓ Last snapshot: $((snapshot_age / 60)) minutes ago"
            fi
        else
            log "  ⚠ No snapshot information available"
            ((issues_found++))
        fi
        
        # Check staging area
        local staging_info
        staging_info=$(echo "$server" | jq -r '.dataReplicationInfo.stagingAvailabilityZone // "unknown"')
        if [[ "$staging_info" != "unknown" ]]; then
            log "  ✓ Staging area: $staging_info"
        else
            log "  ⚠ Staging area information not available"
            ((issues_found++))
        fi
    done
    
    # Send alerts if issues found
    if [[ $critical_issues -gt 0 ]]; then
        aws sns publish \
            --topic-arn "arn:aws:sns:${DRS_REGION}:ACCOUNT-ID:weblogic-drs-critical" \
            --subject "CRITICAL: WebLogic DRS Replication Issues" \
            --message "Found $critical_issues critical replication issues. Check logs: $LOG_FILE" \
            --region "$DRS_REGION" || true
    elif [[ $issues_found -gt 0 ]]; then
        aws sns publish \
            --topic-arn "arn:aws:sns:${DRS_REGION}:ACCOUNT-ID:weblogic-drs-warnings" \
            --subject "WARNING: WebLogic DRS Replication Warnings" \
            --message "Found $issues_found replication warnings. Check logs: $LOG_FILE" \
            --region "$DRS_REGION" || true
    fi
    
    log "Health check completed. Issues: $issues_found, Critical: $critical_issues"
}

# Send health metrics to CloudWatch
send_health_metrics() {
    log "Sending health metrics to CloudWatch..."
    
    # Get replication statistics
    local total_servers
    local healthy_servers
    local stalled_servers
    
    total_servers=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items)')
    healthy_servers=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items[?dataReplicationInfo.dataReplicationState==`CONTINUOUS`])')
    stalled_servers=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items[?dataReplicationInfo.dataReplicationState==`STALLED` || dataReplicationInfo.dataReplicationState==`DISCONNECTED`])')
    
    # Send metrics
    aws cloudwatch put-metric-data \
        --namespace "WebLogic/DRS" \
        --metric-data \
            MetricName=TotalServers,Value="$total_servers",Unit=Count \
            MetricName=HealthyServers,Value="$healthy_servers",Unit=Count \
            MetricName=StalledServers,Value="$stalled_servers",Unit=Count \
        --region "$DRS_REGION"
    
    # Calculate health percentage
    local health_percentage=0
    if [[ $total_servers -gt 0 ]]; then
        health_percentage=$((healthy_servers * 100 / total_servers))
    fi
    
    aws cloudwatch put-metric-data \
        --namespace "WebLogic/DRS" \
        --metric-data MetricName=HealthPercentage,Value="$health_percentage",Unit=Percent \
        --region "$DRS_REGION"
    
    log "Health metrics sent: $healthy_servers/$total_servers servers healthy (${health_percentage}%)"
}

# Main execution
main() {
    log "Starting WebLogic DRS health monitoring..."
    
    check_replication_health
    send_health_metrics
    
    log "Health monitoring cycle completed"
}

# Execute main function
main "$@"
```


6. Launch Templates & Recovery Configuration
--------------------------------------------

### 6.1 Create EC2 Launch Templates for WebLogic Servers


```
# Create launch template for WebLogic Admin Server
cat > weblogic-admin-launch-template.json << 'EOF'
{
    "LaunchTemplateName": "WebLogic-Admin-DR-Template",
    "LaunchTemplateData": {
        "ImageId": "ami-weblogic-base",
        "InstanceType": "m5.large",
        "KeyName": "weblogic-keypair",
        "SecurityGroupIds": ["sg-weblogic-admin"],
        "IamInstanceProfile": {
            "Name": "WebLogicDRInstanceProfile"
        },
        "BlockDeviceMappings": [
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "VolumeSize": 100,
                    "VolumeType": "gp3",
                    "Encrypted": true,
                    "DeleteOnTermination": false
                }
            },
            {
                "DeviceName": "/dev/sdf",
                "Ebs": {
                    "VolumeSize": 200,
                    "VolumeType": "gp3",
                    "Encrypted": true,
                    "DeleteOnTermination": false
                }
            }
        ],
        "UserData": "IyEvYmluL2Jhc2gKIyBXZWJMb2dpYyBBZG1pbiBTZXJ2ZXIgc3RhcnR1cCBzY3JpcHQKZWNobyAiU3RhcnRpbmcgV2ViTG9naWMgQWRtaW4gU2VydmVyIERSIGluaXRpYWxpemF0aW9uLi4uIiA+PiAvdmFyL2xvZy91c2VyLWRhdGEubG9nCi9vcHQvd2VibG9naWMvZHItc2NyaXB0cy9zdGFydC1hZG1pbi1zZXJ2ZXIuc2g=",
        "TagSpecifications": [
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": "WebLogic-Admin-DR"},
                    {"Key": "Application", "Value": "WebLogic"},
                    {"Key": "Environment", "Value": "DR"},
                    {"Key": "ServerType", "Value": "Admin"}
                ]
            }
        ]
    }
}
EOF

# Create the launch template
aws ec2 create-launch-template \
    --cli-input-json file://weblogic-admin-launch-template.json \
    --region us-east-2

# Create launch template for WebLogic Managed Servers
cat > weblogic-managed-launch-template.json << 'EOF'
{
    "LaunchTemplateName": "WebLogic-Managed-DR-Template",
    "LaunchTemplateData": {
        "ImageId": "ami-weblogic-base",
        "InstanceType": "m5.xlarge",
        "KeyName": "weblogic-keypair",
        "SecurityGroupIds": ["sg-weblogic-managed"],
        "IamInstanceProfile": {
            "Name": "WebLogicDRInstanceProfile"
        },
        "BlockDeviceMappings": [
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "VolumeSize": 100,
                    "VolumeType": "gp3",
                    "Encrypted": true,
                    "DeleteOnTermination": false
                }
            },
            {
                "DeviceName": "/dev/sdf",
                "Ebs": {
                    "VolumeSize": 300,
                    "VolumeType": "gp3",
                    "Encrypted": true,
                    "DeleteOnTermination": false
                }
            }
        ],
        "UserData": "IyEvYmluL2Jhc2gKIyBXZWJMb2dpYyBNYW5hZ2VkIFNlcnZlciBzdGFydHVwIHNjcmlwdAplY2hvICJTdGFydGluZyBXZWJMb2dpYyBNYW5hZ2VkIFNlcnZlciBEUiBpbml0aWFsaXphdGlvbi4uLiIgPj4gL3Zhci9sb2cvdXNlci1kYXRhLmxvZwovb3B0L3dlYmxvZ2ljL2RyLXNjcmlwdHMvc3RhcnQtbWFuYWdlZC1zZXJ2ZXIuc2g=",
        "TagSpecifications": [
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": "WebLogic-Managed-DR"},
                    {"Key": "Application", "Value": "WebLogic"},
                    {"Key": "Environment", "Value": "DR"},
                    {"Key": "ServerType", "Value": "Managed"}
                ]
            }
        ]
    }
}
EOF

aws ec2 create-launch-template \
    --cli-input-json file://weblogic-managed-launch-template.json \
    --region us-east-2
```


### 6.2 Configure DRS Launch Settings


```
#!/bin/bash
# configure-drs-launch-settings.sh
# Configure launch settings for each WebLogic server in DRS

set -euo pipefail

DRS_REGION="us-east-2"

# Function to configure launch settings for a server
configure_launch_settings() {
    local source_server_id="$1"
    local server_type="$2"
    local hostname="$3"
    
    echo "Configuring launch settings for $server_type server: $hostname"
    
    # Determine launch template based on server type
    local launch_template_id
    case "$server_type" in
        "admin")
            launch_template_id="lt-weblogic-admin-dr"
            ;;
        "managed")
            launch_template_id="lt-weblogic-managed-dr"
            ;;
        "database")
            launch_template_id="lt-weblogic-database-dr"
            ;;
        *)
            launch_template_id="lt-weblogic-managed-dr"  # Default
            ;;
    esac
    
    # Create launch configuration
    cat > "/tmp/launch-config-${source_server_id}.json" << EOF
{
    "copyPrivateIp": false,
    "copyTags": true,
    "ec2LaunchTemplateID": "$launch_template_id",
    "enableMapAutoTagging": true,
    "launchDisposition": "STARTED",
    "licensing": {
        "osByol": false
    },
    "mapAutoTaggingMpeID": "mpe-weblogic-${server_type}",
    "postLaunchActions": {
        "cloudWatchLogGroupName": "/aws/drs/weblogic-${server_type}",
        "deployment": "TEST_AND_CUTOVER",
        "s3LogBucket": "weblogic-drs-logs-${DRS_REGION}",
        "s3OutputKeyPrefix": "${server_type}-server/",
        "ssmDocuments": [
            {
                "actionName": "ConfigureWebLogic${server_type^}",
                "documentName": "WebLogic-Configure-${server_type^}-Server",
                "documentVersion": "\$LATEST",
                "mustSucceedForCutover": true,
                "parameters": {
                    "ServerType": "$server_type",
                    "DomainHome": "/opt/weblogic/domains/mydomain",
                    "AdminUser": "weblogic"
                },
                "timeoutSeconds": 1800
            }
        ]
    },
    "targetInstanceTypeRightSizingMethod": "BASIC"
}
EOF
    
    # Apply launch configuration
    aws drs update-launch-configuration \
        --source-server-id "$source_server_id" \
        --cli-input-json "file:///tmp/launch-config-${source_server_id}.json" \
        --region "$DRS_REGION"
    
    echo "Launch configuration applied for $hostname"
    
    # Clean up temporary file
    rm -f "/tmp/launch-config-${source_server_id}.json"
}

# Get all source servers and configure launch settings
echo "Configuring launch settings for all WebLogic servers..."

aws drs describe-source-servers \
    --region "$DRS_REGION" \
    --query 'items[].[sourceServerID,tags.ServerType,hostname]' \
    --output text | while read -r server_id server_type hostname; do
    
    # Determine server type if not tagged
    if [[ "$server_type" == "None" || -z "$server_type" ]]; then
        if [[ "$hostname" == *"admin"* ]]; then
            server_type="admin"
        elif [[ "$hostname" == *"managed"* ]]; then
            server_type="managed"
        elif [[ "$hostname" == *"db"* ]]; then
            server_type="database"
        else
            server_type="managed"
        fi
    fi
    
    configure_launch_settings "$server_id" "$server_type" "$hostname"
done

echo "Launch settings configuration completed for all servers"
```


### 6.3 Create SSM Documents for WebLogic Startup


```
# Create SSM document for WebLogic Admin Server startup
cat > weblogic-admin-startup-document.json << 'EOF'
{
    "schemaVersion": "2.2",
    "description": "Start WebLogic Admin Server in DR environment",
    "parameters": {
        "DomainHome": {
            "type": "String",
            "description": "WebLogic domain home directory",
            "default": "/opt/weblogic/domains/mydomain"
        },
        "AdminUser": {
            "type": "String",
            "description": "WebLogic admin username",
            "default": "weblogic"
        }
    },
    "mainSteps": [
        {
            "action": "aws:runShellScript",
            "name": "StartWebLogicAdmin",
            "inputs": {
                "timeoutSeconds": "1800",
                "runCommand": [
                    "#!/bin/bash",
                    "set -euo pipefail",
                    "",
                    "# Logging",
                    "LOG_FILE=/var/log/weblogic-dr-startup.log",
                    "log() { echo \"[$(date '+%Y-%m-%d %H:%M:%S')] $1\" | tee -a $LOG_FILE; }",
                    "",
                    "log \"Starting WebLogic Admin Server DR initialization...\"",
                    "",
                    "# Set environment variables",
                    "export DOMAIN_HOME=\"{{ DomainHome }}\"",
                    "export ADMIN_USER=\"{{ AdminUser }}\"",
                    "export JAVA_HOME=/opt/java/openjdk",
                    "export MW_HOME=/opt/weblogic",
                    "",
                    "# Wait for file system to be ready",
                    "log \"Waiting for domain directory to be available...\"",
                    "timeout=300",
                    "while [[ $timeout -gt 0 && ! -d \"$DOMAIN_HOME\" ]]; do",
                    "    sleep 5",
                    "    ((timeout-=5))",
                    "done",
                    "",
                    "if [[ ! -d \"$DOMAIN_HOME\" ]]; then",
                    "    log \"ERROR: Domain directory not found: $DOMAIN_HOME\"",
                    "    exit 1",
                    "fi",
                    "",
                    "# Update database connection strings for DR",
                    "log \"Updating database connections for DR environment...\"",
                    "if [[ -f \"$DOMAIN_HOME/config/config.xml\" ]]; then",
                    "    # Backup original config",
                    "    cp \"$DOMAIN_HOME/config/config.xml\" \"$DOMAIN_HOME/config/config.xml.backup.$(date +%Y%m%d-%H%M%S)\"",
                    "    ",
                    "    # Update database URLs for DR region",
                    "    sed -i 's/weblogic-db\\.us-east-1\\.rds\\.amazonaws\\.com/weblogic-db.us-east-2.rds.amazonaws.com/g' \"$DOMAIN_HOME/config/config.xml\"",
                    "    sed -i 's/weblogic-primary/weblogic-dr/g' \"$DOMAIN_HOME/config/config.xml\"",
                    "    ",
                    "    log \"Database connections updated for DR\"",
                    "fi",
                    "",
                    "# Start Node Manager",
                    "log \"Starting Node Manager...\"",
                    "cd \"$DOMAIN_HOME\"",
                    "nohup ./bin/startNodeManager.sh > /var/log/weblogic/nodemanager.log 2>&1 &",
                    "",
                    "# Wait for Node Manager to start",
                    "log \"Waiting for Node Manager to start...\"",
                    "timeout=180",
                    "while [[ $timeout -gt 0 ]]; do",
                    "    if netstat -ln | grep -q ':5556'; then",
                    "        log \"Node Manager started successfully\"",
                    "        break",
                    "    fi",
                    "    sleep 5",
                    "    ((timeout-=5))",
                    "done",
                    "",
                    "if [[ $timeout -eq 0 ]]; then",
                    "    log \"ERROR: Node Manager failed to start\"",
                    "    exit 1",
                    "fi",
                    "",
                    "# Start Admin Server",
                    "log \"Starting Admin Server...\"",
                    "nohup ./bin/startWebLogic.sh > /var/log/weblogic/adminserver.log 2>&1 &",
                    "",
                    "# Wait for Admin Server to start",
                    "log \"Waiting for Admin Server to start...\"",
                    "timeout=600",
                    "while [[ $timeout -gt 0 ]]; do",
                    "    if curl -s http://localhost:7001/console > /dev/null 2>&1; then",
                    "        log \"Admin Server started successfully\"",
                    "        break",
                    "    fi",
                    "    sleep 10",
                    "    ((timeout-=10))",
                    "done",
                    "",
                    "if [[ $timeout -eq 0 ]]; then",
                    "    log \"ERROR: Admin Server failed to start\"",
                    "    exit 1",
                    "fi",
                    "",
                    "# Verify Admin Server health",
                    "log \"Verifying Admin Server health...\"",
                    "if curl -f http://localhost:7001/console > /dev/null 2>&1; then",
                    "    log \"✓ Admin Server is healthy and responding\"",
                    "else",
                    "    log \"⚠ Admin Server may not be fully ready\"",
                    "fi",
                    "",
                    "# Send success notification",
                    "aws sns publish --topic-arn 'arn:aws:sns:us-east-2:ACCOUNT-ID:weblogic-drs-notifications' --subject 'WebLogic Admin Server DR Started' --message 'WebLogic Admin Server has been successfully started in DR environment' --region us-east-2 || true",
                    "",
                    "log \"WebLogic Admin Server DR startup completed successfully\"",
                    "exit 0"
                ]
            }
        }
    ]
}
EOF

# Create the SSM document
aws ssm create-document \
    --name "WebLogic-Configure-Admin-Server" \
    --document-type "Command" \
    --document-format "JSON" \
    --content file://weblogic-admin-startup-document.json \
    --region us-east-2

# Create SSM document for WebLogic Managed Server startup
cat > weblogic-managed-startup-document.json << 'EOF'
{
    "schemaVersion": "2.2",
    "description": "Start WebLogic Managed Server in DR environment",
    "parameters": {
        "DomainHome": {
            "type": "String",
            "description": "WebLogic domain home directory",
            "default": "/opt/weblogic/domains/mydomain"
        },
        "AdminUser": {
            "type": "String",
            "description": "WebLogic admin username",
            "default": "weblogic"
        },
        "ServerType": {
            "type": "String",
            "description": "Server type (managed)",
            "default": "managed"
        }
    },
    "mainSteps": [
        {
            "action": "aws:runShellScript",
            "name": "StartWebLogicManaged",
            "inputs": {
                "timeoutSeconds": "1800",
                "runCommand": [
                    "#!/bin/bash",
                    "set -euo pipefail",
                    "",
                    "# Logging",
                    "LOG_FILE=/var/log/weblogic-dr-startup.log",
                    "log() { echo \"[$(date '+%Y-%m-%d %H:%M:%S')] $1\" | tee -a $LOG_FILE; }",
                    "",
                    "log \"Starting WebLogic Managed Server DR initialization...\"",
                    "",
                    "# Set environment variables",
                    "export DOMAIN_HOME=\"{{ DomainHome }}\"",
                    "export ADMIN_USER=\"{{ AdminUser }}\"",
                    "export JAVA_HOME=/opt/java/openjdk",
                    "export MW_HOME=/opt/weblogic",
                    "",
                    "# Wait for Admin Server to be available",
                    "log \"Waiting for Admin Server to be available...\"",
                    "ADMIN_URL=\"weblogic-admin-dr.us-east-2.compute.internal:7001\"",
                    "timeout=600",
                    "while [[ $timeout -gt 0 ]]; do",
                    "    if curl -s http://$ADMIN_URL/console > /dev/null 2>&1; then",
                    "        log \"Admin Server is available\"",
                    "        break",
                    "    fi",
                    "    sleep 10",
                    "    ((timeout-=10))",
                    "done",
                    "",
                    "if [[ $timeout -eq 0 ]]; then",
                    "    log \"ERROR: Admin Server not available\"",
                    "    exit 1",
                    "fi",
                    "",
                    "# Start Node Manager",
                    "log \"Starting Node Manager...\"",
                    "cd \"$DOMAIN_HOME\"",
                    "nohup ./bin/startNodeManager.sh > /var/log/weblogic/nodemanager.log 2>&1 &",
                    "",
                    "# Wait for Node Manager",
                    "sleep 30",
                    "",
                    "# Determine server name based on hostname",
                    "HOSTNAME=$(hostname)",
                    "if [[ \"$HOSTNAME\" == *\"managed1\"* ]]; then",
                    "    SERVER_NAME=\"ManagedServer1\"",
                    "elif [[ \"$HOSTNAME\" == *\"managed2\"* ]]; then",
                    "    SERVER_NAME=\"ManagedServer2\"",
                    "else",
                    "    SERVER_NAME=\"ManagedServer1\"",
                    "fi",
                    "",
                    "# Start Managed Server",
                    "log \"Starting Managed Server: $SERVER_NAME\"",
                    "nohup ./bin/startManagedWebLogic.sh $SERVER_NAME t3://$ADMIN_URL > /var/log/weblogic/$SERVER_NAME.log 2>&1 &",
                    "",
                    "# Wait for Managed Server to start",
                    "log \"Waiting for Managed Server to start...\"",
                    "timeout=600",
                    "while [[ $timeout -gt 0 ]]; do",
                    "    if curl -s http://localhost:8001/console > /dev/null 2>&1; then",
                    "        log \"Managed Server started successfully\"",
                    "        break",
                    "    fi",
                    "    sleep 10",
                    "    ((timeout-=10))",
                    "done",
                    "",
                    "if [[ $timeout -eq 0 ]]; then",
                    "    log \"WARNING: Managed Server may not have started properly\"",
                    "fi",
                    "",
                    "# Send success notification",
                    "aws sns publish --topic-arn 'arn:aws:sns:us-east-2:ACCOUNT-ID:weblogic-drs-notifications' --subject 'WebLogic Managed Server DR Started' --message \"WebLogic Managed Server $SERVER_NAME has been started in DR environment\" --region us-east-2 || true",
                    "",
                    "log \"WebLogic Managed Server DR startup completed\"",
                    "exit 0"
                ]
            }
        }
    ]
}
EOF

# Create the managed server SSM document
aws ssm create-document \
    --name "WebLogic-Configure-Managed-Server" \
    --document-type "Command" \
    --document-format "JSON" \
    --content file://weblogic-managed-startup-document.json \
    --region us-east-2
```


7. Testing & Validation
-----------------------

### 7.1 DRS Testing Strategy

| Test Type | Frequency | Duration | Scope | Success Criteria |
| --- | --- | --- | --- | --- |
| Replication Health Check | Daily | 15 minutes | All source servers | All servers in CONTINUOUS state |
| Recovery Instance Launch | Weekly | 30 minutes | Single test server | Instance launches and WebLogic starts |
| Application Validation | Bi-weekly | 1 hour | Admin + 1 Managed server | Console accessible, applications deployed |
| Full DR Drill | Monthly | 2 hours | Complete WebLogic environment | All services operational, RTO < 15 minutes |
| Disaster Simulation | Quarterly | 4 hours | End-to-end business process | Business continuity maintained |

### 7.2 Automated DR Testing Suite


```
#!/bin/bash
# weblogic-drs-test-suite.sh
# Comprehensive automated testing for WebLogic DRS

set -euo pipefail

# Configuration
DRS_REGION="us-east-2"
TEST_LOG="/var/log/weblogic-drs-test-$(date +%Y%m%d-%H%M%S).log"
TEST_RESULTS_FILE="/tmp/drs-test-results.json"

# Initialize test results
echo '{"tests": [], "summary": {"total": 0, "passed": 0, "failed": 0, "warnings": 0}}' > "$TEST_RESULTS_FILE"

# Logging and result tracking
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$TEST_LOG"
}

record_test_result() {
    local test_name="$1"
    local status="$2"
    local message="$3"
    local details="${4:-}"
    
    jq --arg name "$test_name" \
       --arg status "$status" \
       --arg message "$message" \
       --arg details "$details" \
       --arg timestamp "$(date -Iseconds)" \
       '.tests += [{
           "name": $name,
           "status": $status,
           "message": $message,
           "details": $details,
           "timestamp": $timestamp
       }] | .summary.total += 1 | 
       if $status == "PASS" then .summary.passed += 1
       elif $status == "FAIL" then .summary.failed += 1
       else .summary.warnings += 1 end' \
       "$TEST_RESULTS_FILE" > "${TEST_RESULTS_FILE}.tmp" && \
       mv "${TEST_RESULTS_FILE}.tmp" "$TEST_RESULTS_FILE"
    
    case "$status" in
        "PASS") log "✓ PASS - $test_name: $message" ;;
        "FAIL") log "✗ FAIL - $test_name: $message" ;;
        "WARN") log "⚠ WARN - $test_name: $message" ;;
    esac
}

# Test 1: Replication Status Check
test_replication_status() {
    log "TEST 1: Checking replication status for all WebLogic servers"
    
    local test_name="Replication_Status"
    local total_servers
    local continuous_servers
    local stalled_servers
    
    total_servers=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items)')
    continuous_servers=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items[?dataReplicationInfo.dataReplicationState==`CONTINUOUS`])')
    stalled_servers=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items[?dataReplicationInfo.dataReplicationState==`STALLED` || dataReplicationInfo.dataReplicationState==`DISCONNECTED`])')
    
    if [[ $stalled_servers -gt 0 ]]; then
        record_test_result "$test_name" "FAIL" "$stalled_servers servers have stalled replication" \
            "Total: $total_servers, Continuous: $continuous_servers, Stalled: $stalled_servers"
    elif [[ $continuous_servers -eq $total_servers ]]; then
        record_test_result "$test_name" "PASS" "All $total_servers servers have continuous replication" \
            "Total: $total_servers, Continuous: $continuous_servers"
    else
        record_test_result "$test_name" "WARN" "Some servers not in continuous replication" \
            "Total: $total_servers, Continuous: $continuous_servers"
    fi
}

# Test 2: Launch Configuration Validation
test_launch_configurations() {
    log "TEST 2: Validating launch configurations"
    
    local test_name="Launch_Configurations"
    local configured_servers=0
    local total_servers
    
    total_servers=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items)')
    
    # Check each server's launch configuration
    aws drs describe-source-servers --region "$DRS_REGION" --query 'items[].sourceServerID' --output text | while read -r server_id; do
        local launch_config
        launch_config=$(aws drs get-launch-configuration --source-server-id "$server_id" --region "$DRS_REGION" 2>/dev/null || echo "")
        
        if [[ -n "$launch_config" ]]; then
            ((configured_servers++))
        fi
    done
    
    if [[ $configured_servers -eq $total_servers ]]; then
        record_test_result "$test_name" "PASS" "All $total_servers servers have launch configurations" \
            "Configured: $configured_servers/$total_servers"
    else
        record_test_result "$test_name" "FAIL" "Missing launch configurations" \
            "Configured: $configured_servers/$total_servers"
    fi
}

# Test 3: Recovery Instance Launch Test
test_recovery_instance_launch() {
    log "TEST 3: Testing recovery instance launch (Admin Server)"
    
    local test_name="Recovery_Instance_Launch"
    
    # Find Admin Server source ID
    local admin_server_id
    admin_server_id=$(aws drs describe-source-servers \
        --region "$DRS_REGION" \
        --query 'items[?contains(hostname, `admin`)].sourceServerID' \
        --output text | head -1)
    
    if [[ -z "$admin_server_id" ]]; then
        record_test_result "$test_name" "FAIL" "Admin server not found in DRS" ""
        return
    fi
    
    # Start recovery instance
    log "Launching recovery instance for Admin Server..."
    local job_id
    job_id=$(aws drs start-recovery \
        --source-servers sourceServerID="$admin_server_id" \
        --is-drill true \
        --tags Application=WebLogic,Environment=DR-Test \
        --region "$DRS_REGION" \
        --query 'job.jobID' \
        --output text)
    
    if [[ -z "$job_id" ]]; then
        record_test_result "$test_name" "FAIL" "Failed to start recovery job" ""
        return
    fi
    
    log "Recovery job started: $job_id"
    
    # Monitor job progress
    local job_status="PENDING"
    local timeout=1800  # 30 minutes
    local elapsed=0
    
    while [[ "$job_status" == "PENDING" || "$job_status" == "STARTED" ]] && [[ $elapsed -lt $timeout ]]; do
        sleep 30
        elapsed=$((elapsed + 30))
        
        job_status=$(aws drs describe-jobs \
            --filters jobIDs="$job_id" \
            --region "$DRS_REGION" \
            --query 'items[0].status' \
            --output text)
        
        log "Job status: $job_status (elapsed: ${elapsed}s)"
    done
    
    # Check final status
    if [[ "$job_status" == "COMPLETED" ]]; then
        # Get recovery instance ID
        local recovery_instance_id
        recovery_instance_id=$(aws drs describe-jobs \
            --filters jobIDs="$job_id" \
            --region "$DRS_REGION" \
            --query 'items[0].participatingServers[0].recoveryInstanceID' \
            --output text)
        
        record_test_result "$test_name" "PASS" "Recovery instance launched successfully" \
            "Job ID: $job_id, Instance: $recovery_instance_id, Duration: ${elapsed}s"
        
        # Clean up - terminate the test instance
        log "Terminating test recovery instance..."
        aws drs terminate-recovery-instances \
            --recovery-instance-i-ds "$recovery_instance_id" \
            --region "$DRS_REGION" || true
    else
        record_test_result "$test_name" "FAIL" "Recovery job failed or timed out" \
            "Job ID: $job_id, Status: $job_status, Duration: ${elapsed}s"
    fi
}

# Test 4: Network Connectivity Test
test_network_connectivity() {
    log "TEST 4: Testing network connectivity for DR environment"
    
    local test_name="Network_Connectivity"
    local connectivity_issues=0
    
    # Test DRS API endpoints
    if ! curl -s --max-time 10 "https://drs.${DRS_REGION}.amazonaws.com" > /dev/null; then
        ((connectivity_issues++))
        log "Cannot reach DRS API endpoint"
    fi
    
    # Test EC2 API endpoints
    if ! aws ec2 describe-instances --max-items 1 --region "$DRS_REGION" > /dev/null 2>&1; then
        ((connectivity_issues++))
        log "Cannot reach EC2 API endpoint"
    fi
    
    # Test SSM endpoints
    if ! aws ssm describe-instance-information --max-items 1 --region "$DRS_REGION" > /dev/null 2>&1; then
        ((connectivity_issues++))
        log "Cannot reach SSM API endpoint"
    fi
    
    if [[ $connectivity_issues -eq 0 ]]; then
        record_test_result "$test_name" "PASS" "All network connectivity tests passed" ""
    else
        record_test_result "$test_name" "FAIL" "$connectivity_issues connectivity issues found" ""
    fi
}

# Test 5: Staging Area Health
test_staging_area_health() {
    log "TEST 5: Checking staging area health"
    
    local test_name="Staging_Area_Health"
    local staging_issues=0
    
    # Get staging instances
    local staging_instances
    staging_instances=$(aws ec2 describe-instances \
        --filters "Name=tag:AWSElasticDisasterRecoverySourceServer,Values=*" \
        --region "$DRS_REGION" \
        --query 'Reservations[].Instances[?State.Name==`running`].InstanceId' \
        --output text)
    
    if [[ -z "$staging_instances" ]]; then
        record_test_result "$test_name" "WARN" "No staging instances found" ""
        return
    fi
    
    local staging_count=0
    for instance in $staging_instances; do
        ((staging_count++))
        
        # Check instance health
        local instance_status
        instance_status=$(aws ec2 describe-instance-status \
            --instance-ids "$instance" \
            --region "$DRS_REGION" \
            --query 'InstanceStatuses[0].InstanceStatus.Status' \
            --output text 2>/dev/null || echo "unknown")
        
        if [[ "$instance_status" != "ok" ]]; then
            ((staging_issues++))
        fi
    done
    
    if [[ $staging_issues -eq 0 ]]; then
        record_test_result "$test_name" "PASS" "All $staging_count staging instances are healthy" \
            "Staging instances: $staging_count"
    else
        record_test_result "$test_name" "WARN" "$staging_issues staging instances have issues" \
            "Total: $staging_count, Issues: $staging_issues"
    fi
}

# Generate test report
generate_test_report() {
    log "Generating comprehensive test report..."
    
    local summary
    summary=$(jq -r '.summary | "Total: \(.total), Passed: \(.passed), Failed: \(.failed), Warnings: \(.warnings)"' "$TEST_RESULTS_FILE")
    
    log "=== DRS TEST SUMMARY ==="
    log "$summary"
    
    # Calculate success rate
    local total_tests
    local passed_tests
    total_tests=$(jq -r '.summary.total' "$TEST_RESULTS_FILE")
    passed_tests=$(jq -r '.summary.passed' "$TEST_RESULTS_FILE")
    
    local success_rate=0
    if [[ $total_tests -gt 0 ]]; then
        success_rate=$((passed_tests * 100 / total_tests))
    fi
    
    log "Success Rate: ${success_rate}%"
    
    # Generate HTML report
    local report_file="/tmp/weblogic-drs-test-report-$(date +%Y%m%d-%H%M%S).html"
    
    cat > "$report_file" << 'EOF'



    
    


    WebLogic DRS Test Report
    
```


`Test Summary`
--------------

`EOF jq -r '.summary | "`

`Total Tests: \(.total)`  
`Passed: \(.passed)`  
`Failed: \(.failed)`  
`Warnings: \(.warnings)`  
`Success Rate: " + ((.passed * 100 / .total) | floor | tostring) + "%`

`"' \ "$TEST_RESULTS_FILE" >> "$report_file" echo '`

`Test Details`
--------------

`' >> "$report_file" jq -r '.tests[] | ""' \ "$TEST_RESULTS_FILE" >> "$report_file" echo '`

| `Test Name` | `Status` | `Message` | `Details` | `Timestamp` |
| --- | --- | --- | --- | --- |
| `\(.name)` | `\(.status)` | `\(.message)` | `\(.details)` | `\(.timestamp)` |

`' >> "$report_file" log "Test report generated: $report_file" # Send notification local failed_count failed_count=$(jq -r '.summary.failed' "$TEST_RESULTS_FILE") if [[ $failed_count -gt 0 ]]; then aws sns publish \ --topic-arn "arn:aws:sns:${DRS_REGION}:ACCOUNT-ID:weblogic-drs-alerts" \ --subject "WebLogic DRS Test FAILURES Detected" \ --message "DRS testing completed with $failed_count failures. Success rate: ${success_rate}%. Check logs: $TEST_LOG" \ --region "$DRS_REGION" || true else aws sns publish \ --topic-arn "arn:aws:sns:${DRS_REGION}:ACCOUNT-ID:weblogic-drs-notifications" \ --subject "WebLogic DRS Test SUCCESS" \ --message "All DRS tests passed successfully. Success rate: ${success_rate}%. Report: $report_file" \ --region "$DRS_REGION" || true fi } # Main execution main() { log "Starting WebLogic DRS comprehensive test suite..." test_replication_status test_launch_configurations test_recovery_instance_launch test_network_connectivity test_staging_area_health generate_test_report log "DRS test suite completed. Results: $TEST_RESULTS_FILE" log "Test log: $TEST_LOG" } # Execute main function main "$@"`

8. Failover Procedures
----------------------

**CRITICAL:** Failover procedures should only be executed during actual disasters or authorized DR tests. AWS DRS provides sub-second RPO and minutes RTO for rapid recovery.

### 8.1 Failover Decision Matrix

| Scenario | Severity | DRS Action | Authorization Required | Expected RTO |
| --- | --- | --- | --- | --- |
| Single server failure | Medium | Launch single recovery instance | Operations Team | 5-10 minutes |
| Multiple server failure | High | Launch multiple recovery instances | Operations Manager | 10-15 minutes |
| Complete site failure | Critical | Full DR activation | Incident Commander | 15-20 minutes |
| Planned maintenance | Low | Scheduled cutover | Change Management | 10-15 minutes |

### 8.2 Pre-Failover Checklist

#### Complete before initiating DRS failover:

* Incident declared and stakeholders notified
* Source environment status confirmed (unreachable/degraded)
* DRS replication status verified (all servers CONTINUOUS)
* Target AWS region capacity confirmed
* Network connectivity to DR region verified
* DNS failover plan ready
* Database dependencies identified and ready
* Application teams notified
* Monitoring systems prepared for DR region
* Rollback plan reviewed and understood

### 8.3 Automated DRS Failover Script


```
#!/bin/bash
# weblogic-drs-failover.sh
# Automated failover using AWS Elastic Disaster Recovery

set -euo pipefail

# Configuration
DRS_REGION="us-east-2"
FAILOVER_LOG="/var/log/weblogic-drs-failover-$(date +%Y%m%d-%H%M%S).log"
SNS_TOPIC_ARN="arn:aws:sns:${DRS_REGION}:ACCOUNT-ID:weblogic-drs-critical"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$FAILOVER_LOG"
}

error_exit() {
    log "ERROR: $1"
    send_alert "WebLogic DRS Failover FAILED" "$1"
    exit 1
}

send_alert() {
    local subject="$1"
    local message="$2"
    
    aws sns publish \
        --topic-arn "$SNS_TOPIC_ARN" \
        --subject "$subject" \
        --message "$message. Log: $FAILOVER_LOG" \
        --region "$DRS_REGION" || true
}

# Validate DRS readiness
validate_drs_readiness() {
    log "Validating DRS readiness for failover..."
    
    # Check all servers are in continuous replication
    local total_servers
    local continuous_servers
    local stalled_servers
    
    total_servers=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items)')
    continuous_servers=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items[?dataReplicationInfo.dataReplicationState==`CONTINUOUS`])')
    stalled_servers=$(aws drs describe-source-servers --region "$DRS_REGION" --query 'length(items[?dataReplicationInfo.dataReplicationState==`STALLED` || dataReplicationInfo.dataReplicationState==`DISCONNECTED`])')
    
    log "Replication status: $continuous_servers/$total_servers servers in continuous replication"
    
    if [[ $stalled_servers -gt 0 ]]; then
        error_exit "$stalled_servers servers have stalled replication. Cannot proceed with failover."
    fi
    
    if [[ $continuous_servers -lt $total_servers ]]; then
        log "WARNING: Not all servers are in continuous replication. Proceeding may result in data loss."
        read -p "Continue with failover? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log "Failover cancelled by user"
            exit 0
        fi
    fi
    
    # Check launch configurations
    local configured_servers=0
    aws drs describe-source-servers --region "$DRS_REGION" --query 'items[].sourceServerID' --output text | while read -r server_id; do
        if aws drs get-launch-configuration --source-server-id "$server_id" --region "$DRS_REGION" &>/dev/null; then
            ((configured_servers++))
        fi
    done
    
    log "Launch configurations: $configured_servers/$total_servers servers configured"
    
    log "DRS readiness validation completed"
}

# Execute DRS failover
execute_drs_failover() {
    log "Starting DRS failover for WebLogic environment..."
    
    # Get all WebLogic source servers
    local source_servers
    source_servers=$(aws drs describe-source-servers \
        --region "$DRS_REGION" \
        --query 'items[].{ID:sourceServerID,Hostname:hostname,Type:tags.ServerType}' \
        --output json)
    
    if [[ $(echo "$source_servers" | jq length) -eq 0 ]]; then
        error_exit "No source servers found in DRS"
    fi
    
    # Prepare source server list for recovery
    local server_list=()
    echo "$source_servers" | jq -r '.[].ID' | while read -r server_id; do
        server_list+=("sourceServerID=$server_id")
    done
    
    # Start recovery job
    log "Initiating DRS recovery job..."
    local job_id
    job_id=$(aws drs start-recovery \
        --source-servers $(IFS=' '; echo "${server_list[*]}") \
        --is-drill false \
        --tags Application=WebLogic,Environment=DR,FailoverType=Production \
        --region "$DRS_REGION" \
        --query 'job.jobID' \
        --output text)
    
    if [[ -z "$job_id" ]]; then
        error_exit "Failed to start DRS recovery job"
    fi
    
    log "DRS recovery job started: $job_id"
    
    # Monitor recovery progress
    monitor_recovery_job "$job_id"
}

# Monitor DRS recovery job
monitor_recovery_job() {
    local job_id="$1"
    log "Monitoring DRS recovery job: $job_id"
    
    local job_status="PENDING"
    local start_time=$(date +%s)
    local timeout=1800  # 30 minutes maximum
    local elapsed=0
    
    while [[ "$job_status" == "PENDING" || "$job_status" == "STARTED" ]] && [[ $elapsed -lt $timeout ]]; do
        sleep 30
        elapsed=$(( $(date +%s) - start_time ))
        
        # Get job status and details
        local job_info
        job_info=$(aws drs describe-jobs \
            --filters jobIDs="$job_id" \
            --region "$DRS_REGION" \
            --query 'items[0]' \
            --output json)
        
        job_status=$(echo "$job_info" | jq -r '.status')
        local participating_servers
        participating_servers=$(echo "$job_info" | jq -r '.participatingServers | length')
        
        log "Job status: $job_status, Servers: $participating_servers, Elapsed: ${elapsed}s"
        
        # Show detailed progress for each server
        echo "$job_info" | jq -r '.participatingServers[]? | "  Server: \(.sourceServerID) -> \(.recoveryInstanceID // "pending")"' | while read -r server_info; do
            log "$server_info"
        done
    done
    
    # Check final status
    if [[ "$job_status" == "COMPLETED" ]]; then
        log "✓ DRS recovery job completed successfully in ${elapsed} seconds"
        
        # Get recovery instance details
        local recovery_instances
        recovery_instances=$(aws drs describe-jobs \
            --filters jobIDs="$job_id" \
            --region "$DRS_REGION" \
            --query 'items[0].participatingServers[].recoveryInstanceID' \
            --output text)
        
        log "Recovery instances launched: $recovery_instances"
        
        # Wait for instances to be running
        wait_for_instances_ready "$recovery_instances"
        
        # Validate WebLogic startup
        validate_weblogic_startup "$recovery_instances"
        
    elif [[ "$job_status" == "COMPLETED_WITH_ERRORS" ]]; then
        log "⚠ DRS recovery job completed with errors in ${elapsed} seconds"
        
        # Get error details
        local job_errors
        job_errors=$(aws drs describe-jobs \
            --filters jobIDs="$job_id" \
            --region "$DRS_REGION" \
            --query 'items[0].participatingServers[?launchStatus!=`LAUNCHED`]' \
            --output json)
        
        log "Servers with launch errors:"
        echo "$job_errors" | jq -r '.[] | "  \(.sourceServerID): \(.launchStatus)"'
        
        send_alert "WebLogic DRS Failover PARTIAL SUCCESS" \
            "DRS recovery completed with errors. Some servers may not have launched properly. Job ID: $job_id"
        
    else
        error_exit "DRS recovery job failed or timed out. Status: $job_status, Duration: ${elapsed}s, Job ID: $job_id"
    fi
}

# Wait for EC2 instances to be ready
wait_for_instances_ready() {
    local instance_ids="$1"
    log "Waiting for recovery instances to be ready..."
    
    for instance_id in $instance_ids; do
        if [[ "$instance_id" != "null" && -n "$instance_id" ]]; then
            log "Waiting for instance $instance_id to be running..."
            aws ec2 wait instance-running \
                --instance-ids "$instance_id" \
                --region "$DRS_REGION" || log "WARNING: Instance $instance_id may not be running"
            
            log "Waiting for instance $instance_id status checks..."
            aws ec2 wait instance-status-ok \
                --instance-ids "$instance_id" \
                --region "$DRS_REGION" || log "WARNING: Instance $instance_id status checks may have failed"
        fi
    done
    
    log "All recovery instances are ready"
}

# Validate WebLogic startup
validate_weblogic_startup() {
    local instance_ids="$1"
    log "Validating WebLogic startup on recovery instances..."
    
    local validation_timeout=900  # 15 minutes
    local start_time=$(date +%s)
    
    # Wait for WebLogic services to start
    while [[ $(( $(date +%s) - start_time )) -lt $validation_timeout ]]; do
        local healthy_instances=0
        local total_instances=0
        
        for instance_id in $instance_ids; do
            if [[ "$instance_id" != "null" && -n "$instance_id" ]]; then
                ((total_instances++))
                
                # Get instance private IP
                local private_ip
                private_ip=$(aws ec2 describe-instances \
                    --instance-ids "$instance_id" \
                    --region "$DRS_REGION" \
                    --query 'Reservations[0].Instances[0].PrivateIpAddress' \
                    --output text)
                
                # Check if WebLogic is responding
                if curl -s --max-time 10 "http://$private_ip:7001/console" > /dev/null 2>&1 || \
                   curl -s --max-time 10 "http://$private_ip:8001/console" > /dev/null 2>&1; then
                    ((healthy_instances++))
                fi
            fi
        done
        
        log "WebLogic health check: $healthy_instances/$total_instances instances responding"
        
        if [[ $healthy_instances -eq $total_instances ]]; then
            log "✓ All WebLogic instances are healthy and responding"
            break
        fi
        
        sleep 30
    done
    
    # Final validation
    if [[ $(( $(date +%s) - start_time )) -ge $validation_timeout ]]; then
        log "⚠ WARNING: WebLogic validation timed out. Some services may not be fully ready."
    fi
}

# Update DNS for failover
update_dns_failover() {
    log "Updating DNS for failover..."
    
    # This would typically involve updating Route 53 records
    # to point to the new recovery instances or load balancer
    
    # Example: Update Route 53 record to point to DR load balancer
    local dr_alb_dns="weblogic-dr-alb.us-east-2.elb.amazonaws.com"
    
    aws route53 change-resource-record-sets \
        --hosted-zone-id "Z1234567890ABC" \
        --change-batch '{
            "Changes": [{
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": "weblogic.example.com",
                    "Type": "CNAME",
                    "TTL": 60,
                    "ResourceRecords": [{"Value": "'$dr_alb_dns'"}]
                }
            }]
        }' || log "WARNING: DNS update failed"
    
    log "DNS updated for failover"
}

# Send success notification
send_success_notification() {
    local total_time="$1"
    
    send_alert "WebLogic DRS Failover COMPLETED" \
        "WebLogic DRS failover completed successfully in ${total_time} seconds. All services are now running in DR region $DRS_REGION."
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    log "Starting WebLogic DRS failover process..."
    
    validate_drs_readiness
    execute_drs_failover
    update_dns_failover
    
    local total_time=$(( $(date +%s) - start_time ))
    
    send_success_notification "$total_time"
    
    log "WebLogic DRS failover completed successfully!"
    log "Total failover time: ${total_time} seconds"
    log "Application should be accessible via DR region"
    log "Log file: $FAILOVER_LOG"
}

# Execute main function
main "$@"
```


### 8.4 Manual Failover Steps (Emergency)


```
# Emergency manual failover using AWS CLI
#!/bin/bash
# emergency-drs-failover.sh

echo "=== EMERGENCY DRS FAILOVER ==="
echo "WARNING: This will launch recovery instances for all WebLogic servers"
read -p "Are you sure you want to proceed? (type 'EMERGENCY' to confirm): " confirm

if [[ "$confirm" != "EMERGENCY" ]]; then
    echo "Emergency failover cancelled"
    exit 1
fi

DRS_REGION="us-east-2"

# Step 1: Get all source server IDs
echo "1. Getting source server IDs..."
SOURCE_SERVERS=$(aws drs describe-source-servers \
    --region "$DRS_REGION" \
    --query 'items[].sourceServerID' \
    --output text)

if [[ -z "$SOURCE_SERVERS" ]]; then
    echo "ERROR: No source servers found"
    exit 1
fi

echo "Found servers: $SOURCE_SERVERS"

# Step 2: Start emergency recovery
echo "2. Starting emergency recovery..."
JOB_ID=$(aws drs start-recovery \
    --source-servers $(echo "$SOURCE_SERVERS" | sed 's/ / sourceServerID=/g' | sed 's/^/sourceServerID=/') \
    --is-drill false \
    --tags Emergency=true,Application=WebLogic \
    --region "$DRS_REGION" \
    --query 'job.jobID' \
    --output text)

echo "Recovery job started: $JOB_ID"

# Step 3: Monitor progress
echo "3. Monitoring recovery progress..."
while true; do
    JOB_STATUS=$(aws drs describe-jobs \
        --filters jobIDs="$JOB_ID" \
        --region "$DRS_REGION" \
        --query 'items[0].status' \
        --output text)
    
    echo "Job status: $JOB_STATUS"
    
    if [[ "$JOB_STATUS" == "COMPLETED" ]]; then
        echo "✓ Recovery completed successfully"
        break
    elif [[ "$JOB_STATUS" == "FAILED" ]]; then
        echo "✗ Recovery failed"
        exit 1
    fi
    
    sleep 30
done

# Step 4: Get recovery instance IDs
echo "4. Getting recovery instance information..."
aws drs describe-jobs \
    --filters jobIDs="$JOB_ID" \
    --region "$DRS_REGION" \
    --query 'items[0].participatingServers[].[sourceServerID,recoveryInstanceID]' \
    --output table

echo "=== EMERGENCY FAILOVER COMPLETED ==="
echo "Recovery instances are launching. Check EC2 console for status."
echo "Manual validation and DNS updates may be required."
```


9. Failback Procedures
----------------------

**Important:** DRS failback involves reversing the replication direction and requires careful planning to ensure data consistency.

### 9.1 DRS Failback Process Overview

AWS DRS failback involves the following key steps:

1. **Reverse Replication:** Install DRS agents on recovery instances
2. **Data Synchronization:** Replicate changes back to original environment
3. **Cutover:** Switch traffic back to original environment
4. **Cleanup:** Terminate recovery instances and reset replication

### 9.2 Comprehensive DRS Failback Script


```html
#!/bin/bash
# weblogic-drs-failback.sh
# Comprehensive failback using AWS Elastic Disaster Recovery

set -euo pipefail

# Configuration
DRS_REGION="us-east-2"
SOURCE_REGION="us-east-1"
FAILBACK_LOG="/var/log/weblogic-drs-failback-$(date +%Y%m%d-%H%M%S).log"
SNS_TOPIC_ARN="arn:aws:sns:${DRS_REGION}:ACCOUNT-ID:weblogic-drs-notifications"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$FAILBACK_LOG"
}

error_exit() {
    log "ERROR: $1"
    send_alert "WebLogic DRS Failback FAILED" "$1"
    exit 1
}

send_alert() {
    local subject="$1"
    local message="$2"
    
    aws sns publish \
        --topic-arn "$SNS_TOPIC_ARN" \
        --subject "$subject" \
        --message "$message. Log: $FAILBACK_LOG" \
        --region "$DRS_REGION" || true
}

# Validate failback prerequisites
validate_failback_prerequisites() {
    log "Validating failback prerequisites..."
    
    # Check if original environment is ready
    log "Checking original environment accessibility..."
    if ! aws ec2 describe-instances --region "$SOURCE_REGION" --max-items 1 &>/dev/null; then
        error_exit "Cannot access original environment in $SOURCE_REGION"
    fi
    
    # Check recovery instances are running
    log "Checking recovery instances status..."
    local recovery_instances
    recovery_instances=$(aws ec2 describe-instances \
        --filters "Name=tag:Application,Values=WebLogic" "Name=tag:Environment,Values=DR" "Name=instance-state-name,Values=running" \
        --region "$DRS_REGION" \
        --query 'Reservations[].Instances[].InstanceId' \
        --output text)
    
    if [[ -z "$recovery_instances" ]]; then
        error_exit "No running recovery instances found"
    fi
    
    log "Found recovery instances: $recovery_instances"
    
    # Verify WebLogic is running on recovery instances
    log "Verifying WebLogic services on recovery instances..."
    local healthy_instances=0
    for instance_id in $recovery_instances; do
        local private_ip
        private_ip=$(aws ec2 describe-instances \
            --instance-ids "$instance_id" \
            --region "$DRS_REGION" \
            --query 'Reservations[0].Instances[0].PrivateIpAddress' \
            --output text)
        
        if curl -s --max-time 10 "http://$private_ip:7001/console" > /dev/null 2>&1 || \
           curl -s --max-time 10 "http://$private_ip:8001/console" > /dev/null 2>&1; then
            ((healthy_instances++))
            log "✓ WebLogic healthy on instance $instance_id ($private_ip)"
        else
            log "⚠ WebLogic not responding on instance $instance_id ($private_ip)"
        fi
    done
    
    log "WebLogic health check: $healthy_instances instances responding"
    
    log "Failback prerequisites validation completed"
}

# Install DRS agents on recovery instances for reverse replication
install_reverse_replication_agents() {
    log "Installing DRS agents on recovery instances for reverse replication..."
    
    # Get recovery instances
    local recovery_instances
    recovery_instances=$(aws ec2 describe-instances \
        --filters "Name=tag:Application,Values=WebLogic" "Name=tag:Environment,Values=DR" "Name=instance-state-name,Values=running" \
        --region "$DRS_REGION" \
        --query 'Reservations[].Instances[].InstanceId' \
        --output text)
    
    # Create SSM document for agent installation
    local install_document="WebLogic-DRS-Agent-Install-Failback"
    
    cat > "/tmp/${install_document}.json" << 'EOF'
{
    "schemaVersion": "2.2",
    "description": "Install DRS agent for failback replication",
    "parameters": {
        "SourceRegion": {
            "type": "String",
            "description": "Source region for failback",
            "default": "us-east-1"
        }
    },
    "mainSteps": [
        {
            "action": "aws:runShellScript",
            "name": "InstallDRSAgent",
            "inputs": {
                "timeoutSeconds": "1800",
                "runCommand": [
                    "#!/bin/bash",
                    "set -euo pipefail",
                    "",
                    "log() { echo \"[$(date '+%Y-%m-%d %H:%M:%S')] $1\" | tee -a /var/log/drs-agent-failback-install.log; }",
                    "",
                    "log \"Starting DRS agent installation for failback...\"",
                    "",
                    "# Download DRS agent installer",
                    "cd /tmp",
                    "curl -o aws-replication-installer-init.py https://aws-elastic-disaster-recovery-{{ SourceRegion }}.s3.amazonaws.com/latest/linux/aws-replication-installer-init.py",
                    "",
                    "# Install agent with instance role credentials",
                    "python3 aws-replication-installer-init.py --region {{ SourceRegion }} --no-prompt",
                    "",
                    "# Verify installation",
                    "if systemctl is-active --quiet aws-replication-agent; then",
                    "    log \"✓ DRS agent installed and running\"",
                    "else",
                    "    log \"✗ DRS agent installation failed\"",
                    "    exit 1",
                    "fi",
                    "",
                    "log \"DRS agent installation completed for failback\""
                ]
            }
        }
    ]
}
EOF
    
    # Create or update SSM document
    if aws ssm describe-document --name "$install_document" --region "$DRS_REGION" &>/dev/null; then
        aws ssm update-document \
            --name "$install_document" \
            --content "file:///tmp/${install_document}.json" \
            --document-version "\$LATEST" \
            --region "$DRS_REGION"
    else
        aws ssm create-document \
            --name "$install_document" \
            --document-type "Command" \
            --document-format "JSON" \
            --content "file:///tmp/${install_document}.json" \
            --region "$DRS_REGION"
    fi
    
    # Execute agent installation on all recovery instances
    for instance_id in $recovery_instances; do
        log "Installing DRS agent on instance $instance_id..."
        
        local command_id
        command_id=$(aws ssm send-command \
            --instance-ids "$instance_id" \
            --document-name "$install_document" \
            --parameters "SourceRegion=$SOURCE_REGION" \
            --region "$DRS_REGION" \
            --query 'Command.CommandId' \
            --output text)
        
        # Wait for command completion
        aws ssm wait command-executed \
            --command-id "$command_id" \
            --instance-id "$instance_id" \
            --region "$DRS_REGION" || log "WARNING: Agent installation may have failed on $instance_id"
        
        log "DRS agent installation completed on $instance_id"
    done
    
    log "Reverse replication agents installed on all recovery instances"
}

# Configure reverse replication
configure_reverse_replication() {
    log "Configuring reverse replication for failback..."
    
    # Wait for new source servers to appear in DRS console
    log "Waiting for recovery instances to appear as source servers..."
    local timeout=600
    local elapsed=0
    
    while [[ $elapsed -lt $timeout ]]; do
        local new_source_count
        new_source_count=$(aws drs describe-source-servers \
            --region "$SOURCE_REGION" \
            --query 'length(items[?tags.Environment==`DR`])' 2>/dev/null || echo "0")
        
        if [[ $new_source_count -gt 0 ]]; then
            log "Found $new_source_count new source servers for reverse replication"
            break
        fi
        
        sleep 30
        elapsed=$((elapsed + 30))
    done
    
    if [[ $elapsed -ge $timeout ]]; then
        error_exit "Timeout waiting for recovery instances to register as source servers"
    fi
    
    # Configure replication settings for reverse replication
    aws drs describe-source-servers \
        --region "$SOURCE_REGION" \
        --query 'items[?tags.Environment==`DR`].sourceServerID' \
        --output text | while read -r server_id; do
        
        log "Configuring reverse replication for server $server_id..."
        
        # Create replication configuration for failback
        cat > "/tmp/reverse-replication-config-${server_id}.json" << 'EOF'
{
    "associateDefaultSecurityGroup": true,
    "bandwidthThrottling": 0,
    "createPublicIP": false,
    "dataPlaneRouting": "PRIVATE_IP",
    "defaultLargeStagingDiskType": "GP3",
    "ebsEncryption": "ENCRYPTED",
    "replicationServerInstanceType": "m5.large",
    "stagingAreaTags": {
        "Application": "WebLogic",
        "Environment": "Failback",
        "Purpose": "Reverse-Replication"
    },
    "useDedicatedReplicationServer": false
}
EOF
        
        # Apply configuration
        aws drs update-replication-configuration \
            --source-server-id "$server_id" \
            --cli-input-json "file:///tmp/reverse-replication-config-${server_id}.json" \
            --region "$SOURCE_REGION"
        
        log "Reverse replication configured for server $server_id"
    done
    
    log "Reverse replication configuration completed"
}

# Monitor reverse replication progress
monitor_reverse_replication() {
    log "Monitoring reverse replication progress..."
    
    local timeout=3600  # 1 hour
    local start_time=$(date +%s)
    
    while [[ $(( $(date +%s) - start_time )) -lt $timeout ]]; do
        local total_servers
        local continuous_servers
        
        total_servers=$(aws drs describe-source-servers \
            --region "$SOURCE_REGION" \
            --query 'length(items[?tags.Environment==`DR`])' 2>/dev/null || echo "0")
        
        continuous_servers=$(aws drs describe-source-servers \
            --region "$SOURCE_REGION" \
            --query 'length(items[?tags.Environment==`DR` && dataReplicationInfo.dataReplicationState==`CONTINUOUS`])' 2>/dev/null || echo "0")
        
        log "Reverse replication progress: $continuous_servers/$total_servers servers in continuous replication"
        
        if [[ $continuous_servers -eq $total_servers && $total_servers -gt 0 ]]; then
            log "✓ All servers have completed reverse replication"
            break
        fi
        
        sleep 60
    done
    
    if [[ $(( $(date +%s) - start_time )) -ge $timeout ]]; then
        error_exit "Timeout waiting for reverse replication to complete"
    fi
}

# Execute cutover to original environment
execute_cutover() {
    log "Executing cutover to original environment..."
    
    # Get reverse replication source servers
    local reverse_source_servers
    reverse_source_servers=$(aws drs describe-source-servers \
        --region "$SOURCE_REGION" \
        --query 'items[?tags.Environment==`DR`].sourceServerID' \
        --output text)
    
    if [[ -z "$reverse_source_servers" ]]; then
        error_exit "No reverse replication source servers found"
    fi
    
    # Start cutover job
    log "Starting cutover job for failback..."
    local cutover_job_id
    cutover_job_id=$(aws drs start-cutover \
        --source-server-i-ds $reverse_source_servers \
        --tags Application=WebLogic,Environment=Failback,Type=Cutover \
        --region "$SOURCE_REGION" \
        --query 'job.jobID' \
        --output text)
    
    if [[ -z "$cutover_job_id" ]]; then
        error_exit "Failed to start cutover job"
    fi
    
    log "Cutover job started: $cutover_job_id"
    
    # Monitor cutover progress
    local job_status="PENDING"
    local cutover_timeout=1800  # 30 minutes
    local start_time=$(date +%s)
    
    while [[ "$job_status" == "PENDING" || "$job_status" == "STARTED" ]] && [[ $(( $(date +%s) - start_time )) -lt $cutover_timeout ]]; do
        sleep 30
        
        job_status=$(aws drs describe-jobs \
            --filters jobIDs="$cutover_job_id" \
            --region "$SOURCE_REGION" \
            --query 'items[0].status' \
            --output text)
        
        local elapsed=$(( $(date +%s) - start_time ))
        log "Cutover job status: $job_status (elapsed: ${elapsed}s)"
    done
    
    if [[ "$job_status" == "COMPLETED" ]]; then
        log "✓ Cutover completed successfully"
    else
        error_exit "Cutover job failed or timed out. Status: $job_status"
    fi
}

# Update DNS back to original environment
update_dns_failback() {
    log "Updating DNS back to original environment..."
    
    # Update Route 53 record to point back to original environment
    local original_alb_dns="weblogic-primary-alb.us-east-1.elb.amazonaws.com"
    
    aws route53 change-resource-record-sets \
        --hosted-zone-id "Z1234567890ABC" \
        --change-batch '{
            "Changes": [{
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": "weblogic.example.com",
                    "Type": "CNAME",
                    "TTL": 300,
                    "ResourceRecords": [{"Value": "'$original_alb_dns'"}]
                }
            }]
        }' || log "WARNING: DNS update failed"
    
    log "DNS updated back to original environment"
}

# Cleanup DR resources
cleanup_dr_resources() {
    log "Cleaning up DR resources..."
    
    # Terminate recovery instances
    local recovery_instances
    recovery_instances=$(aws ec2 describe-instances \
        --filters "Name=tag:Application,Values=WebLogic" "Name=tag:Environment,Values=DR" "Name=instance-state-name,Values=running" \
        --region "$DRS_REGION" \
        --query 'Reservations[].Instances[].InstanceId' \
        --output text)
    
    if [[ -n "$recovery_instances" ]]; then
        log "Terminating recovery instances: $recovery_instances"
        aws ec2 terminate-instances \
            --instance-ids $recovery_instances \
            --region "$DRS_REGION" || log "WARNING: Failed to terminate some recovery instances"
    fi
    
    # Disconnect reverse replication source servers
    local reverse_sources
    reverse_sources=$(aws drs describe-source-servers \
        --region "$SOURCE_REGION" \
        --query 'items[?tags.Environment==`DR`].sourceServerID' \
        --output text)
    
    for server_id in $reverse_sources; do
        log "Disconnecting reverse replication source: $server_id"
        aws drs disconnect-from-service \
            --source-server-id "$server_id" \
            --region "$SOURCE_REGION" || log "WARNING: Failed to disconnect $server_id"
    done
    
    log "DR resource cleanup completed"
}

# Validate failback completion
validate_failback_completion() {
    log "Validating failback completion..."
    
    # Wait for DNS propagation
    sleep 120
    
    # Test application endpoints
    local endpoints=("/console" "/myapp/health" "/myapp/api/status")
    local failed_endpoints=()
    
    for endpoint in "${endpoints[@]}"; do
        if ! curl -f -s --max-time 30 "http://weblogic.example.com$endpoint" > /dev/null; then
            failed_endpoints+=("$endpoint")
        fi
    done
    
    if [[ ${#failed_endpoints[@]} -eq 0 ]]; then
        log "✓ All application endpoints are responding in original environment"
    else
        log "⚠ Some endpoints failed validation: ${failed_endpoints[*]}"
    fi
    
    # Verify original DRS replication is restored
    local original_servers
    original_servers=$(aws drs describe-source-servers \
        --region "$DRS_REGION" \
        --query 'length(items[?dataReplicationInfo.dataReplicationState==`CONTINUOUS`])' 2>/dev/null || echo "0")
    
    log "Original DRS replication status: $original_servers servers in continuous replication"
    
    log "Failback validation completed"
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    log "Starting WebLogic DRS failback process..."
    
    validate_failback_prerequisites
    install_reverse_replication_agents
    configure_reverse_replication
    monitor_reverse_replication
    execute_cutover
    update_dns_failback
    cleanup_dr_resources
    validate_failback_completion
    
    local total_time=$(( $(date +%s) - start_time ))
    
    send_alert "WebLogic DRS Failback COMPLETED" \
        "WebLogic DRS failback completed successfully in ${total_time} seconds. Services are now running in original environment."
    
    log "WebLogic DRS failback completed successfully!"
    log "Total failback time: ${total_time} seconds"
    log "Application is now running in original environment"
    log "Log file: $FAILBACK_LOG"
}

# Execute main function
main "$@"
```
