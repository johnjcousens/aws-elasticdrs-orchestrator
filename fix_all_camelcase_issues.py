#!/usr/bin/env python3
"""
Systematic CamelCase Migration Fix
Fixes ALL field name inconsistencies in the API handler
"""

import re

def fix_api_handler():
    """Fix all camelCase issues in the API handler"""
    
    # Read the current file
    with open('lambda/api-handler/index.py', 'r') as f:
        content = f.read()
    
    # Define all the fixes needed
    fixes = [
        # Database field references - make all camelCase
        ('Key={"GroupId":', 'Key={"groupId":'),
        ('Key={"PlanId":', 'Key={"planId":'),
        ('Key={"ExecutionId":', 'Key={"executionId":'),
        ('Key={"AccountId":', 'Key={"accountId":'),
        
        # Field access patterns - make all camelCase
        ('existing_group.get("Version"', 'existing_group.get("version"'),
        ('existing_group.get("GroupName"', 'existing_group.get("groupName"'),
        ('existing_group.get("Region"', 'existing_group.get("region"'),
        ('existing_group.get("SourceServerIds"', 'existing_group.get("sourceServerIds"'),
        ('existing_group.get("ServerSelectionTags"', 'existing_group.get("serverSelectionTags"'),
        ('existing_group.get("LaunchConfig"', 'existing_group.get("launchConfig"'),
        ('existing_group.get("AccountId"', 'existing_group.get("accountId"'),
        ('existing_group.get("AssumeRoleName"', 'existing_group.get("assumeRoleName"'),
        
        # API input validation - make all camelCase
        ('"GroupName" in body', '"groupName" in body'),
        ('"Region" in body', '"region" in body'),
        ('"SourceServerIds" in body', '"sourceServerIds" in body'),
        ('"ServerSelectionTags" in body', '"serverSelectionTags" in body'),
        ('"LaunchConfig" in body', '"launchConfig" in body'),
        ('"Description" in body', '"description" in body'),
        
        # Body field access - make all camelCase
        ('body["GroupName"]', 'body["groupName"]'),
        ('body["Region"]', 'body["region"]'),
        ('body["SourceServerIds"]', 'body["sourceServerIds"]'),
        ('body["ServerSelectionTags"]', 'body["serverSelectionTags"]'),
        ('body["LaunchConfig"]', 'body["launchConfig"]'),
        ('body["Description"]', 'body["description"]'),
        
        # Update expression field names - make all camelCase
        ('LastModifiedDate = :timestamp', 'lastModifiedDate = :timestamp'),
        ('Version = :new_version', 'version = :new_version'),
        ('GroupName = :name', 'groupName = :name'),
        ('SourceServerIds = :servers', 'sourceServerIds = :servers'),
        ('ServerSelectionTags = :tags', 'serverSelectionTags = :tags'),
        ('LaunchConfig = :launchConfig', 'launchConfig = :launchConfig'),
        
        # Condition expressions - make all camelCase
        ('Version = :current_version', 'version = :current_version'),
        ('attribute_not_exists(Version)', 'attribute_not_exists(version)'),
        
        # Error messages - make all camelCase
        ('"field": "GroupName"', '"field": "groupName"'),
        ('"field": "Region"', '"field": "region"'),
        
        # Wave field references - make all camelCase
        ('wave.get("ProtectionGroupId")', 'wave.get("protectionGroupId")'),
        ('wave.get("WaveName")', 'wave.get("waveName")'),
        
        # Plan field references - make all camelCase
        ('plan.get("PlanId")', 'plan.get("planId")'),
        ('plan.get("PlanName")', 'plan.get("planName")'),
        ('plan.get("Waves")', 'plan.get("waves")'),
        
        # Execution field references - make all camelCase
        ('execution.get("ExecutionId")', 'execution.get("executionId")'),
        ('execution.get("PlanId")', 'execution.get("planId")'),
        ('execution.get("Status")', 'execution.get("status")'),
        
        # DynamoDB attribute names in expressions
        ('"#desc": "Description"', '"#desc": "description"'),
        ('"#status": "Status"', '"#status": "status"'),
    ]
    
    # Apply all fixes
    for old, new in fixes:
        content = content.replace(old, new)
    
    # Write the fixed content back
    with open('lambda/api-handler/index.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed all camelCase issues in API handler")

if __name__ == "__main__":
    fix_api_handler()