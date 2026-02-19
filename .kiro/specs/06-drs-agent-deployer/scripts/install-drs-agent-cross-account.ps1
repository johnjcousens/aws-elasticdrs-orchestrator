<#
.SYNOPSIS
    Install AWS DRS Agent with cross-account replication support

.DESCRIPTION
    Downloads and installs the AWS Elastic Disaster Recovery (DRS) agent on Windows instances
    with support for cross-account replication using the --account-id parameter.

.PARAMETER Region
    AWS region where DRS is configured (default: us-east-1)

.PARAMETER AccountId
    Target AWS account ID for cross-account replication (required for cross-account setup)

.PARAMETER NoPrompt
    Run installer without prompts (default: true)

.PARAMETER TempDir
    Temporary directory for installer download (default: C:\Temp)

.EXAMPLE
    # Install with cross-account replication to staging account
    .\install-drs-agent-cross-account.ps1 -AccountId 891376951562

.EXAMPLE
    # Install to local account (same account as EC2 instance)
    .\install-drs-agent-cross-account.ps1

.EXAMPLE
    # Install with custom region
    .\install-drs-agent-cross-account.ps1 -Region us-west-2 -AccountId 891376951562

.NOTES
    Prerequisites:
    - EC2 instance must have IAM instance profile with AWSElasticDisasterRecoveryEc2InstancePolicy
    - For cross-account: Target account must have source account configured as "Trusted Account"
    - For cross-account: Target account must have "Failback and in-AWS right-sizing roles" enabled
    
    Author: AWS DRS Orchestration Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$AccountId = "",
    
    [Parameter(Mandatory=$false)]
    [bool]$NoPrompt = $true,
    
    [Parameter(Mandatory=$false)]
    [string]$TempDir = "C:\Temp"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Main script
try {
    Write-ColorOutput "`n=== AWS DRS Agent Installation ===" "Cyan"
    Write-ColorOutput "Region: $Region" "White"
    
    if ($AccountId) {
        Write-ColorOutput "Target Account: $AccountId (Cross-Account Replication)" "Yellow"
    } else {
        Write-ColorOutput "Target Account: Local account (Same-Account Replication)" "White"
    }
    
    # Check administrator privileges
    if (-not (Test-Administrator)) {
        Write-ColorOutput "`n[ERROR] This script must be run as Administrator" "Red"
        exit 1
    }
    
    Write-ColorOutput "`n[1/5] Checking prerequisites..." "Cyan"
    
    # Check if DRS agent is already installed
    $agentService = Get-Service -Name "AWS Replication Agent" -ErrorAction SilentlyContinue
    if ($agentService) {
        Write-ColorOutput "[WARNING] AWS Replication Agent service already exists" "Yellow"
        Write-ColorOutput "Status: $($agentService.Status)" "Yellow"
        
        $response = Read-Host "Do you want to reinstall? (yes/no)"
        if ($response -ne "yes") {
            Write-ColorOutput "Installation cancelled" "Yellow"
            exit 0
        }
    }
    
    # Check instance profile
    Write-ColorOutput "Checking EC2 instance profile..." "White"
    try {
        $metadata = Invoke-RestMethod -Uri "http://169.254.169.254/latest/meta-data/iam/security-credentials/" -TimeoutSec 5
        if ($metadata) {
            Write-ColorOutput "✓ Instance profile detected: $metadata" "Green"
        }
    } catch {
        Write-ColorOutput "[WARNING] Could not detect instance profile" "Yellow"
        Write-ColorOutput "Ensure this instance has AWSElasticDisasterRecoveryEc2InstancePolicy attached" "Yellow"
    }
    
    # Create temp directory
    Write-ColorOutput "`n[2/5] Creating temporary directory..." "Cyan"
    if (-not (Test-Path $TempDir)) {
        New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
        Write-ColorOutput "✓ Created: $TempDir" "Green"
    } else {
        Write-ColorOutput "✓ Using existing: $TempDir" "Green"
    }
    
    # Download installer
    Write-ColorOutput "`n[3/5] Downloading DRS agent installer..." "Cyan"
    $installerUrl = "https://aws-elastic-disaster-recovery-$Region.s3.$Region.amazonaws.com/latest/windows/AwsReplicationWindowsInstaller.exe"
    $installerPath = Join-Path $TempDir "AwsReplicationWindowsInstaller.exe"
    
    Write-ColorOutput "URL: $installerUrl" "White"
    Write-ColorOutput "Destination: $installerPath" "White"
    
    # Enable TLS 1.2
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($installerUrl, $installerPath)
    
    if (Test-Path $installerPath) {
        $fileSize = (Get-Item $installerPath).Length / 1MB
        Write-ColorOutput "✓ Downloaded successfully ($([math]::Round($fileSize, 2)) MB)" "Green"
    } else {
        throw "Failed to download installer"
    }
    
    # Build installer arguments
    Write-ColorOutput "`n[4/5] Preparing installation..." "Cyan"
    $installerArgs = @("--region", $Region)
    
    if ($AccountId) {
        $installerArgs += @("--account-id", $AccountId)
        Write-ColorOutput "Cross-account replication enabled" "Yellow"
    }
    
    if ($NoPrompt) {
        $installerArgs += "--no-prompt"
    }
    
    Write-ColorOutput "Installer arguments: $($installerArgs -join ' ')" "White"
    
    # Install agent
    Write-ColorOutput "`n[5/5] Installing DRS agent..." "Cyan"
    Write-ColorOutput "This may take several minutes..." "White"
    
    $process = Start-Process -FilePath $installerPath -ArgumentList $installerArgs -Wait -PassThru -NoNewWindow
    
    if ($process.ExitCode -eq 0) {
        Write-ColorOutput "`n✓ DRS agent installed successfully!" "Green"
        
        # Check service status
        Start-Sleep -Seconds 5
        $agentService = Get-Service -Name "AWS Replication Agent" -ErrorAction SilentlyContinue
        if ($agentService) {
            Write-ColorOutput "`nService Status: $($agentService.Status)" "Green"
            Write-ColorOutput "Service Name: $($agentService.Name)" "White"
            Write-ColorOutput "Display Name: $($agentService.DisplayName)" "White"
        }
        
        # Display next steps
        Write-ColorOutput "`n=== Next Steps ===" "Cyan"
        if ($AccountId) {
            Write-ColorOutput "1. Verify source server appears in target account ($AccountId)" "White"
            Write-ColorOutput "   aws drs describe-source-servers --region $Region" "Gray"
        } else {
            Write-ColorOutput "1. Verify source server appears in DRS console" "White"
            Write-ColorOutput "   aws drs describe-source-servers --region $Region" "Gray"
        }
        Write-ColorOutput "2. Wait for initial replication to complete (may take hours)" "White"
        Write-ColorOutput "3. Configure launch settings for recovery instance" "White"
        Write-ColorOutput "4. Test recovery with drill or recovery job" "White"
        
    } else {
        Write-ColorOutput "`n[ERROR] Installation failed with exit code: $($process.ExitCode)" "Red"
        exit $process.ExitCode
    }
    
    # Cleanup
    Write-ColorOutput "`n=== Cleanup ===" "Cyan"
    $cleanup = Read-Host "Remove installer file? (yes/no)"
    if ($cleanup -eq "yes") {
        Remove-Item -Path $installerPath -Force
        Write-ColorOutput "✓ Installer removed" "Green"
    } else {
        Write-ColorOutput "Installer kept at: $installerPath" "White"
    }
    
} catch {
    Write-ColorOutput "`n[ERROR] Installation failed: $($_.Exception.Message)" "Red"
    Write-ColorOutput "Stack trace: $($_.ScriptStackTrace)" "Red"
    exit 1
}

Write-ColorOutput "`n=== Installation Complete ===" "Cyan"
