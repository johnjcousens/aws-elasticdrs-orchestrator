#!/usr/bin/env python3

"""
Backend CamelCase Migration Script
Systematically converts PascalCase field names to camelCase in Lambda functions
"""

import os
import re
import sys
from pathlib import Path

# Field name mappings: PascalCase -> camelCase
FIELD_MAPPINGS = {
    # Core entity fields
    "GroupId": "groupId",
    "PlanId": "planId", 
    "ExecutionId": "executionId",
    "SourceServerId": "sourceServerId",
    "WaveName": "waveName",
    "ProtectionGroupId": "protectionGroupId",
    "RecoveryPlanName": "recoveryPlanName",
    
    # Protection Group fields
    "ServerSelectionTags": "serverSelectionTags",
    "SourceServerIds": "sourceServerIds",
    "GroupName": "groupName",
    
    # Launch Config fields
    "LaunchConfig": "launchConfig",
    "SubnetId": "subnetId",
    "SecurityGroupIds": "securityGroupIds",
    "InstanceType": "instanceType",
    "InstanceProfileName": "instanceProfileName",
    "CopyPrivateIp": "copyPrivateIp",
    "CopyTags": "copyTags",
    "TargetInstanceTypeRightSizingMethod": "targetInstanceTypeRightSizingMethod",
    "LaunchDisposition": "launchDisposition",
    "Licensing": "licensing",
    
    # Execution fields
    "ExecutionType": "executionType",
    "InitiatedBy": "initiatedBy",
    "DryRun": "dryRun",
    "TopicArn": "topicArn",
    
    # Timestamp fields
    "CreatedAt": "createdAt",
    "UpdatedAt": "updatedAt", 
    "StartTime": "startTime",
    "EndTime": "endTime",
}

# Files to process
LAMBDA_FILES = [
    "lambda/api-handler/index.py",
    "lambda/orchestration-stepfunctions/index.py",
    "lambda/execution-poller/index.py",
    "lambda/execution-finder/index.py",
    "lambda/shared/security_utils.py",
]

def backup_file(file_path):
    """Create a backup of the original file"""
    backup_path = f"{file_path}.backup"
    if os.path.exists(file_path):
        with open(file_path, 'r') as original:
            with open(backup_path, 'w') as backup:
                backup.write(original.read())
        print(f"✅ Created backup: {backup_path}")

def migrate_file(file_path):
    """Migrate a single file from PascalCase to camelCase"""
    if not os.path.exists(file_path):
        print(f"⚠️  File not found: {file_path}")
        return False
    
    print(f"\n🔄 Processing: {file_path}")
    
    # Create backup
    backup_file(file_path)
    
    # Read file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_made = 0
    
    # Apply field mappings
    for pascal_case, camel_case in FIELD_MAPPINGS.items():
        # Pattern 1: Dictionary key access - body["PascalCase"]
        pattern1 = f'body\\["{pascal_case}"\\]'
        replacement1 = f'body["{camel_case}"]'
        new_content = re.sub(pattern1, replacement1, content)
        if new_content != content:
            count = len(re.findall(pattern1, content))
            print(f"  📝 Updated {count} body['{pascal_case}'] -> body['{camel_case}']")
            changes_made += count
            content = new_content
        
        # Pattern 2: Dictionary key check - "PascalCase" in body
        pattern2 = f'"{pascal_case}" in body'
        replacement2 = f'"{camel_case}" in body'
        new_content = re.sub(pattern2, replacement2, content)
        if new_content != content:
            count = len(re.findall(pattern2, content))
            print(f"  📝 Updated {count} '{pascal_case}' in body -> '{camel_case}' in body")
            changes_made += count
            content = new_content
        
        # Pattern 3: Dictionary get method - body.get("PascalCase")
        pattern3 = f'body\\.get\\("{pascal_case}"'
        replacement3 = f'body.get("{camel_case}"'
        new_content = re.sub(pattern3, replacement3, content)
        if new_content != content:
            count = len(re.findall(pattern3, content))
            print(f"  📝 Updated {count} body.get('{pascal_case}') -> body.get('{camel_case}')")
            changes_made += count
            content = new_content
        
        # Pattern 4: DynamoDB field names in expressions
        pattern4 = f'"{pascal_case}":'
        replacement4 = f'"{camel_case}":'
        # Only replace in dictionary contexts, not in comments
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if not line.strip().startswith('#') and pattern4 in line:
                new_line = line.replace(pattern4, replacement4)
                if new_line != line:
                    changes_made += 1
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        content = '\n'.join(new_lines)
        
        # Pattern 5: Error messages and field references
        pattern5 = f'"{pascal_case}"'
        replacement5 = f'"{camel_case}"'
        # Be more selective - only in error contexts
        if 'field' in pascal_case.lower() or 'message' in pascal_case.lower():
            new_content = re.sub(pattern5, replacement5, content)
            if new_content != content:
                count = len(re.findall(pattern5, content)) - len(re.findall(pattern5, new_content))
                if count > 0:
                    print(f"  📝 Updated {count} error field references '{pascal_case}' -> '{camel_case}'")
                    changes_made += count
                    content = new_content
    
    # Special handling for DynamoDB operations
    # Update Key() expressions for queries
    for pascal_case, camel_case in FIELD_MAPPINGS.items():
        if pascal_case in ["GroupId", "PlanId", "ExecutionId"]:
            pattern = f'Key\\("{pascal_case}"\\)'
            replacement = f'Key("{camel_case}")'
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                count = len(re.findall(pattern, content))
                print(f"  📝 Updated {count} Key('{pascal_case}') -> Key('{camel_case}')")
                changes_made += count
                content = new_content
    
    # Write updated content
    if changes_made > 0:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Applied {changes_made} changes to {file_path}")
        return True
    else:
        print(f"ℹ️  No changes needed for {file_path}")
        # Remove backup if no changes made
        backup_path = f"{file_path}.backup"
        if os.path.exists(backup_path):
            os.remove(backup_path)
        return False

def remove_transform_functions(file_path):
    """Remove eliminated transform functions"""
    if not os.path.exists(file_path):
        return False
    
    print(f"\n🗑️  Removing transform functions from: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Functions to remove
    transform_functions = [
        "transform_execution_to_camelcase",
        "transform_execution_to_camelcase_lightweight", 
        "transform_pg_to_camelcase",
        "transform_plan_to_camelcase"
    ]
    
    for func_name in transform_functions:
        # Remove function definitions (multi-line)
        pattern = rf'def {func_name}\([^)]*\):.*?(?=\ndef |\nclass |\n[A-Z]|\Z)'
        content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # Remove function calls
        pattern = rf'{func_name}\([^)]*\)'
        matches = re.findall(pattern, content)
        if matches:
            print(f"  🗑️  Found {len(matches)} calls to {func_name}")
            # Replace calls with direct return of the argument
            content = re.sub(rf'{func_name}\(([^)]*)\)', r'\1', content)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Removed transform functions from {file_path}")
        return True
    
    return False

def validate_migration():
    """Validate the migration was successful"""
    print("\n🔍 Validating migration...")
    
    issues_found = 0
    
    for file_path in LAMBDA_FILES:
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for remaining PascalCase patterns
        for pascal_case in FIELD_MAPPINGS.keys():
            # Look for problematic patterns
            patterns = [
                f'body\\["{pascal_case}"\\]',
                f'"{pascal_case}" in body',
                f'body\\.get\\("{pascal_case}"'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    print(f"⚠️  {file_path}: Found {len(matches)} remaining '{pascal_case}' references")
                    issues_found += len(matches)
    
    if issues_found == 0:
        print("✅ Migration validation passed - no PascalCase references found")
        return True
    else:
        print(f"❌ Migration validation failed - {issues_found} issues found")
        return False

def main():
    """Main migration function"""
    print("========================================")
    print("🚀 Backend CamelCase Migration")
    print("========================================")
    
    # Check if we're in the right directory
    if not os.path.exists("lambda"):
        print("❌ Error: lambda directory not found. Run from project root.")
        sys.exit(1)
    
    total_files_changed = 0
    
    # Process each Lambda file
    for file_path in LAMBDA_FILES:
        if migrate_file(file_path):
            total_files_changed += 1
    
    # Remove transform functions
    api_handler_path = "lambda/api-handler/index.py"
    if remove_transform_functions(api_handler_path):
        print("✅ Transform functions removed")
    
    # Validate migration
    validation_passed = validate_migration()
    
    # Summary
    print("\n========================================")
    print("📊 Migration Summary")
    print("========================================")
    print(f"Files processed: {len(LAMBDA_FILES)}")
    print(f"Files changed: {total_files_changed}")
    print(f"Validation: {'✅ PASSED' if validation_passed else '❌ FAILED'}")
    
    if total_files_changed > 0:
        print("\n💡 Next steps:")
        print("1. Test the changes locally")
        print("2. Run the validation script: ./scripts/validate-camelcase-consistency.sh")
        print("3. Commit and deploy via GitHub Actions")
        print("4. Remove .backup files if everything works correctly")
    
    return 0 if validation_passed else 1

if __name__ == "__main__":
    sys.exit(main())