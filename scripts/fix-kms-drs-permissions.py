#!/usr/bin/env python3
"""
Fix KMS Key Policy for DRS Authorization

Adds DRS service permissions to KMS key policy to resolve:
"Not authorized to use key" errors during DRS recovery operations.
"""

import json
import boto3
import sys

KEY_ID = "ab256143-c334-4d8b-bd7d-67475d8721d0"
REGION = "us-west-2"

def main():
    kms = boto3.client('kms', region_name=REGION)
    
    print(f"Fetching current policy for key {KEY_ID}...")
    
    try:
        response = kms.get_key_policy(KeyId=KEY_ID, PolicyName='default')
        policy = json.loads(response['Policy'])
        
        # Check if DRS statement already exists
        for stmt in policy.get('Statement', []):
            if stmt.get('Sid') == 'AllowDRSService':
                print("✓ DRS permissions already exist in key policy")
                return
        
        # Add DRS statement
        drs_statement = {
            "Sid": "AllowDRSService",
            "Effect": "Allow",
            "Principal": {"Service": "drs.amazonaws.com"},
            "Action": [
                "kms:Decrypt",
                "kms:DescribeKey",
                "kms:CreateGrant"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "kms:ViaService": [
                        f"ec2.{REGION}.amazonaws.com",
                        f"drs.{REGION}.amazonaws.com"
                    ]
                }
            }
        }
        
        policy['Statement'].append(drs_statement)
        
        print("Updating key policy...")
        kms.put_key_policy(
            KeyId=KEY_ID,
            PolicyName='default',
            Policy=json.dumps(policy, indent=2)
        )
        
        print("✓ Successfully updated KMS key policy")
        print("\nYou can now retry the DRS drill for server s-569b0c7877c6b6e29")
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
