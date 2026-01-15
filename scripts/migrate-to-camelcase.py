#!/usr/bin/env python3
"""
Script to migrate DynamoDB field names from PascalCase to camelCase
This eliminates the need for expensive transform functions
"""

import re
import os

# Field name mappings from PascalCase to camelCase
FIELD_MAPPINGS = {
    # Protection Groups
    "GroupId": "groupId",
    "GroupName": "groupName", 
    "Region": "region",
    "SourceServerIds": "sourceServerIds",
    "ServerSelectionTags": "serverSelectionTags",
    "CreatedAt": "createdAt",
    "UpdatedAt": "updatedAt",  # Field name in mapping dictionary, not historical context
    "CreatedBy": "createdBy",
    "AccountId": "accountId",
    "AssumeRoleName": "assumeRoleName",
    
    # Recovery Plans
    "PlanId": "planId",
    "PlanName": "planName",
    "Description": "description",
    "Waves": "waves",
    "WaveNumber": "waveNumber",
    "WaveName": "waveName",
    "ProtectionGroupId": "protectionGroupId",
    "ProtectionGroupIds": "protectionGroupIds",
    "WaitTime": "waitTime",
    "TotalWaves": "totalWaves",
    
    # Executions
    "ExecutionId": "executionId",
    "RecoveryPlanName": "recoveryPlanName",
    "ExecutionType": "executionType",
    "Status": "status",
    "StartTime": "startTime",
    "EndTime": "endTime",
    "InitiatedBy": "initiatedBy",
    "CurrentWave": "currentWave",
    "ErrorMessage": "errorMessage",
    "PausedBeforeWave": "pausedBeforeWave",
    "SelectionMode": "selectionMode",
    "HasActiveDrsJobs": "hasActiveDrsJobs",
    
    # Server details
    "ServerStatuses": "serverStatuses",
    "SourceServerId": "sourceServerId",
    "LaunchStatus": "launchStatus",
    "RecoveryInstanceID": "recoveryInstanceId",
    "Error": "error",
    "ServerIds": "serverIds",
    "Servers": "servers",
    "InstanceId": "instanceId",
    "LaunchTime": "launchTime",
    "InstanceType": "instanceType",
    "PrivateIp": "privateIp",
    "Ec2State": "ec2State",
    "EnrichedServers": "enrichedServers",
    "JobId": "jobId",
    
    # Target Accounts
    "AccountName": "accountName",
    "CrossAccountRoleArn": "crossAccountRoleArn",
}

def update_field_names_in_file(file_path):
    """Update field names in a Python file"""
    print(f"Processing {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Update DynamoDB Key operations
    for pascal, camel in FIELD_MAPPINGS.items():
        # Key={"PascalCase": value} -> Key={"camelCase": value}
        content = re.sub(
            rf'Key=\{{\s*["\']({pascal})["\']\s*:',
            rf'Key={{"{camel}":',
            content
        )
        
        # .get("PascalCase") -> .get("camelCase")
        content = re.sub(
            rf'\.get\(\s*["\']({pascal})["\']\s*([,)])',
            rf'.get("{camel}"\2',
            content
        )
        
        # ["PascalCase"] -> ["camelCase"]
        content = re.sub(
            rf'\[\s*["\']({pascal})["\']\s*\]',
            rf'["{camel}"]',
            content
        )
        
        # "PascalCase": value -> "camelCase": value (in dict literals)
        content = re.sub(
            rf'["\']({pascal})["\']\s*:',
            rf'"{camel}":',
            content
        )
    
    # Update specific DynamoDB operations
    content = re.sub(r'IndexName="PlanIdIndex"', 'IndexName="planIdIndex"', content)
    content = re.sub(r'Key\("PlanId"\)', 'Key("planId")', content)
    content = re.sub(r'Attr\("PlanId"\)', 'Attr("planId")', content)
    content = re.sub(r'Key\("GroupId"\)', 'Key("groupId")', content)
    content = re.sub(r'Attr\("GroupId"\)', 'Attr("groupId")', content)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Updated {file_path}")
        return True
    else:
        print(f"No changes needed in {file_path}")
        return False

def main():
    """Main migration function"""
    files_to_update = [
        "lambda/api-handler/index.py",
        "lambda/orchestration-stepfunctions/index.py",
        "lambda/execution-finder/index.py", 
        "lambda/execution-poller/index.py",
        "lambda/notification-formatter/index.py",
        "lambda/frontend-builder/index.py",
        "lambda/bucket-cleaner/index.py"
    ]
    
    updated_files = []
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            if update_field_names_in_file(file_path):
                updated_files.append(file_path)
        else:
            print(f"File not found: {file_path}")
    
    print(f"\nMigration complete! Updated {len(updated_files)} files:")
    for file_path in updated_files:
        print(f"  - {file_path}")
    
    print("\nNext steps:")
    print("1. Remove transform functions from api-handler")
    print("2. Update frontend TypeScript interfaces if needed")
    print("3. Test functionality")
    print("4. Deploy via GitHub Actions")

if __name__ == "__main__":
    main()