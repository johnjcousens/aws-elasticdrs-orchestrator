$ErrorActionPreference = "Continue"

Write-Host "=== DRS Agent Uninstall Script ==="

# Check if DRS agent is installed
$uninstallPath = "C:\Program Files\AWS Replication Agent\uninstall.exe"
if (Test-Path $uninstallPath) {
    Write-Host "Found DRS agent at: $uninstallPath"
    Write-Host "Uninstalling..."
    
    Start-Process -FilePath $uninstallPath -ArgumentList "/S" -Wait -NoNewWindow
    Write-Host "Uninstall process completed"
    
    # Wait for uninstall to finish
    Start-Sleep -Seconds 15
    
    # Clean up remaining files
    $agentPath = "C:\Program Files\AWS Replication Agent"
    if (Test-Path $agentPath) {
        Write-Host "Removing remaining files..."
        Remove-Item -Path $agentPath -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Cleanup complete"
    }
} else {
    Write-Host "No DRS agent installation found"
}

# Clean up temp files
Write-Host "Cleaning temp files..."
Remove-Item -Path "C:\Temp\AwsReplication*" -Force -ErrorAction SilentlyContinue

Write-Host "=== Uninstall Complete ==="
