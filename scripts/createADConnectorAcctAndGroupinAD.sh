#!/bin/bash

set -e
set -o pipefail

# =============================================================================
# Script: Create AD Connector Account and Group in Active Directory
# Description: Creates AD service account and group via SSM on Windows DC
# =============================================================================

# Variables (can be overridden via parameters or edit here)
INSTANCE_ID="${1:-i-05cc1a64d8e6abc1f}"
AWS_REGION="${2:-us-west-2}"
SECRET_ARN="${3:-arn:aws:secretsmanager:us-west-2:128121109383:secret:adconnector-8oK6zt}"
AD_USERNAME="${4:-adconnector}"
AD_PASSWORD="${5:-}"
AD_GROUP_NAME="${6:-Connectors}"
AD_USER_DESCRIPTION="${7:-AD Connector Service Account}"
AD_GROUP_DESCRIPTION="${8:-Group for AD Connector Service Accounts}"

# =============================================================================
# Prerequisite Checks
# =============================================================================

# Ensure jq is installed
if ! command -v jq &>/dev/null; then
    echo "Error: jq is not installed. Install it using 'sudo yum install -y jq' or 'sudo apt install -y jq'"
    exit 1
fi

# =============================================================================
# Credential Retrieval
# =============================================================================

# Fetch credentials from Secrets Manager if SECRET_ARN provided
if [ -n "$SECRET_ARN" ]; then
    echo "Retrieving AD credentials from Secrets Manager..."
    SECRET_VALUE=$(aws secretsmanager get-secret-value \
        --secret-id "$SECRET_ARN" \
        --query SecretString \
        --output text \
        --region "$AWS_REGION") || { 
        echo "Error: Failed to retrieve secret from Secrets Manager"
        exit 1
    }
    
    # Extract username and password safely
    AD_USERNAME=$(echo "$SECRET_VALUE" | jq -r '.username')
    AD_PASSWORD=$(echo "$SECRET_VALUE" | jq -r '.password')
    
    # Validate extracted credentials
    if [[ -z "$AD_USERNAME" || -z "$AD_PASSWORD" || "$AD_USERNAME" == "null" || "$AD_PASSWORD" == "null" ]]; then
        echo "Error: Missing AD username or password from Secrets Manager"
        exit 1
    fi
    
    echo "✓ Credentials retrieved from Secrets Manager"
else
    echo "Using direct credentials (no SECRET_ARN provided)"
fi

# Final credential validation
if [[ -z "$AD_USERNAME" || -z "$AD_PASSWORD" ]]; then
    echo "Error: AD_USERNAME and AD_PASSWORD are required"
    exit 1
fi

# =============================================================================
# PowerShell Script
# =============================================================================

# Create PowerShell script with variable substitution
read -r -d '' POWERSHELL_SCRIPT << EOF || true
# Import Active Directory module
Import-Module ActiveDirectory

# Configuration
\$Username = "$AD_USERNAME"
\$PlainPassword = '$AD_PASSWORD'
\$SecurePassword = ConvertTo-SecureString \$PlainPassword -AsPlainText -Force
\$UserDescription = "$AD_USER_DESCRIPTION"
\$GroupName = "$AD_GROUP_NAME"
\$GroupDescription = "$AD_GROUP_DESCRIPTION"

# Get domain information
\$DomainInfo = Get-ADDomain
\$DomainDN = \$DomainInfo.DistinguishedName
\$DomainRoot = "LDAP://\$DomainDN"
\$UserOU = "CN=Users,\$DomainDN"

Write-Host "Domain: \$DomainDN"
Write-Host "Creating user '\$Username' and group '\$GroupName'..."

# Create AD User if not exists
if (-not (Get-ADUser -Filter {SamAccountName -eq \$Username} -ErrorAction SilentlyContinue)) {
    New-ADUser -SamAccountName \$Username \`
        -UserPrincipalName "\$Username@\$(\$DomainInfo.DNSRoot)" \`
        -Name \$Username \`
        -GivenName \$Username \`
        -DisplayName "\$Username Account" \`
        -Path \$UserOU \`
        -AccountPassword \$SecurePassword \`
        -Enabled \$true \`
        -ChangePasswordAtLogon \$false \`
        -PasswordNeverExpires \$true \`
        -Description \$UserDescription
    Write-Host "✓ User '\$Username' created"
} else {
    Write-Host "✓ User '\$Username' already exists"
    Set-ADUser -Identity \$Username -PasswordNeverExpires \$true -Description \$UserDescription
}

# Create Group if not exists
if (-not (Get-ADGroup -Filter {Name -eq \$GroupName} -ErrorAction SilentlyContinue)) {
    New-ADGroup -Name \$GroupName -GroupScope Global -Path \$UserOU -Description \$GroupDescription
    Write-Host "✓ Group '\$GroupName' created"
} else {
    Write-Host "✓ Group '\$GroupName' already exists"
    Set-ADGroup -Identity \$GroupName -Description \$GroupDescription
}

# Add user to group
\$GroupMembers = Get-ADGroupMember -Identity \$GroupName -ErrorAction SilentlyContinue | Select-Object -ExpandProperty SamAccountName
if (\$Username -notin \$GroupMembers) {
    Add-ADGroupMember -Identity \$GroupName -Members \$Username
    Write-Host "✓ User added to group"
} else {
    Write-Host "✓ User already in group"
}

# Delegate permissions to group on domain root
Write-Host "Applying delegation permissions..."

\$IdentitySID = (Get-ADGroup -Identity \$GroupName).SID
\$DomainObject = [ADSI]\$DomainRoot
\$SecurityDescriptor = \$DomainObject.psbase.ObjectSecurity

# User object GUID
\$UserObjectGUID = New-Object Guid "bf967aba-0de6-11d0-a285-00aa003049e2"

# Create and apply ACEs
\$AceCreateDeleteUsers = New-Object System.DirectoryServices.ActiveDirectoryAccessRule \`
    (\$IdentitySID, "CreateChild, DeleteChild", "Allow", \$UserObjectGUID, "None")
\$AceReadWriteUsers = New-Object System.DirectoryServices.ActiveDirectoryAccessRule \`
    (\$IdentitySID, "ReadProperty, WriteProperty", "Allow", \$UserObjectGUID, "None")

\$SecurityDescriptor.AddAccessRule(\$AceCreateDeleteUsers)
\$SecurityDescriptor.AddAccessRule(\$AceReadWriteUsers)
\$DomainObject.psbase.CommitChanges()

Write-Host "✓ Delegation applied successfully"
Write-Host ""
Write-Host "==================================="
Write-Host "Configuration Complete"
Write-Host "==================================="
Write-Host "User: \$Username"
Write-Host "Group: \$GroupName"
Write-Host "Domain: \$DomainDN"
Write-Host "==================================="
EOF

# =============================================================================
# Execute via SSM
# =============================================================================

echo ""
echo "Executing PowerShell script on instance $INSTANCE_ID..."

# Send SSM command
COMMAND_OUTPUT=$(aws ssm send-command \
    --document-name "AWS-RunPowerShellScript" \
    --instance-ids "$INSTANCE_ID" \
    --parameters "commands=[$(echo "$POWERSHELL_SCRIPT" | jq -Rs .)]" \
    --region "$AWS_REGION" \
    --output json) || {
    echo "Error: Failed to send SSM command"
    exit 1
}

COMMAND_ID=$(echo "$COMMAND_OUTPUT" | jq -r '.Command.CommandId')

if [[ -z "$COMMAND_ID" || "$COMMAND_ID" == "null" ]]; then
    echo "Error: Failed to get command ID"
    exit 1
fi

echo "✓ Command sent (ID: $COMMAND_ID)"
echo "Waiting for completion..."

# Wait for command completion (max 5 minutes)
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    STATUS=$(aws ssm get-command-invocation \
        --command-id "$COMMAND_ID" \
        --instance-id "$INSTANCE_ID" \
        --region "$AWS_REGION" \
        --query 'Status' \
        --output text 2>/dev/null || echo "Pending")
    
    case "$STATUS" in
        "Success")
            echo "✓ Command completed successfully"
            break
            ;;
        "Failed"|"Cancelled"|"TimedOut")
            echo "Error: Command failed with status: $STATUS"
            exit 1
            ;;
        *)
            sleep 10
            ATTEMPT=$((ATTEMPT + 1))
            ;;
    esac
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "Error: Command timeout after 5 minutes"
    exit 1
fi

# Get command output
echo ""
echo "=== Command Output ==="
OUTPUT=$(aws ssm get-command-invocation \
    --command-id "$COMMAND_ID" \
    --instance-id "$INSTANCE_ID" \
    --region "$AWS_REGION" \
    --query 'StandardOutputContent' \
    --output text)

if [[ -n "$OUTPUT" && "$OUTPUT" != "None" ]]; then
    echo "$OUTPUT"
fi
echo "======================"

# Check for errors
ERRORS=$(aws ssm get-command-invocation \
    --command-id "$COMMAND_ID" \
    --instance-id "$INSTANCE_ID" \
    --region "$AWS_REGION" \
    --query 'StandardErrorContent' \
    --output text 2>/dev/null || echo "")

if [[ -n "$ERRORS" && "$ERRORS" != "None" ]]; then
    echo ""
    echo "Errors detected:"
    echo "$ERRORS"
    exit 1
fi

# =============================================================================
# Verification
# =============================================================================

echo ""
echo "Verifying AD objects..."

# Create verification PowerShell script
read -r -d '' VERIFY_SCRIPT << EOF || true
Import-Module ActiveDirectory

\$Username = "$AD_USERNAME"
\$GroupName = "$AD_GROUP_NAME"
\$VerificationFailed = \$false

Write-Host "==================================="
Write-Host "AD Object Verification"
Write-Host "==================================="
Write-Host ""

# Verify user exists
try {
    \$User = Get-ADUser -Filter {SamAccountName -eq \$Username} -Properties PasswordNeverExpires -ErrorAction Stop
    Write-Host "✓ User '\$Username' exists"
    Write-Host "  - Enabled: \$(\$User.Enabled)"
    Write-Host "  - Password Never Expires: \$(\$User.PasswordNeverExpires)"
    Write-Host "  - Description: \$(\$User.Description)"
} catch {
    Write-Host "✗ User '\$Username' NOT FOUND"
    \$VerificationFailed = \$true
}

Write-Host ""

# Verify group exists
try {
    \$Group = Get-ADGroup -Filter {Name -eq \$GroupName} -Properties Description -ErrorAction Stop
    Write-Host "✓ Group '\$GroupName' exists"
    Write-Host "  - Description: \$(\$Group.Description)"
} catch {
    Write-Host "✗ Group '\$GroupName' NOT FOUND"
    \$VerificationFailed = \$true
}

Write-Host ""

# Verify membership
try {
    \$Members = Get-ADGroupMember -Identity \$GroupName -ErrorAction Stop | Select-Object -ExpandProperty SamAccountName
    if (\$Username -in \$Members) {
        Write-Host "✓ User '\$Username' is member of '\$GroupName'"
    } else {
        Write-Host "✗ User '\$Username' is NOT a member of '\$GroupName'"
        \$VerificationFailed = \$true
    }
} catch {
    Write-Host "✗ Failed to check group membership"
    \$VerificationFailed = \$true
}

Write-Host ""
Write-Host "==================================="

if (\$VerificationFailed) {
    Write-Host "✗ VERIFICATION FAILED"
    Write-Host "==================================="
    exit 1
} else {
    Write-Host "✓ VERIFICATION PASSED"
    Write-Host "==================================="
}
EOF

# Send verification command
VERIFY_OUTPUT=$(aws ssm send-command \
    --document-name "AWS-RunPowerShellScript" \
    --instance-ids "$INSTANCE_ID" \
    --parameters "commands=[$(echo "$VERIFY_SCRIPT" | jq -Rs .)]" \
    --region "$AWS_REGION" \
    --output json) || {
    echo "Warning: Failed to send verification command"
}

VERIFY_COMMAND_ID=$(echo "$VERIFY_OUTPUT" | jq -r '.Command.CommandId')

if [[ -n "$VERIFY_COMMAND_ID" && "$VERIFY_COMMAND_ID" != "null" ]]; then
    # Wait for verification command
    ATTEMPT=0
    while [ $ATTEMPT -lt 20 ]; do
        VERIFY_STATUS=$(aws ssm get-command-invocation \
            --command-id "$VERIFY_COMMAND_ID" \
            --instance-id "$INSTANCE_ID" \
            --region "$AWS_REGION" \
            --query 'Status' \
            --output text 2>/dev/null || echo "Pending")
        
        case "$VERIFY_STATUS" in
            "Success")
                break
                ;;
            "Failed"|"Cancelled"|"TimedOut")
                echo "Warning: Verification command failed"
                break
                ;;
            *)
                sleep 5
                ATTEMPT=$((ATTEMPT + 1))
                ;;
        esac
    done
    
    # Get verification output
    VERIFY_RESULT=$(aws ssm get-command-invocation \
        --command-id "$VERIFY_COMMAND_ID" \
        --instance-id "$INSTANCE_ID" \
        --region "$AWS_REGION" \
        --query 'StandardOutputContent' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$VERIFY_RESULT" && "$VERIFY_RESULT" != "None" ]]; then
        echo ""
        echo "$VERIFY_RESULT"
    fi
fi

# =============================================================================
# Success
# =============================================================================

echo ""
echo "✅ AD Connector account created successfully!"
echo ""
echo "Configuration:"
echo "  User: $AD_USERNAME"
echo "  Group: $AD_GROUP_NAME"
echo "  Instance: $INSTANCE_ID"
echo "  Region: $AWS_REGION"
echo ""
echo "Next: Use these credentials to create your AD Connector"
