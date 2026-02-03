#!/usr/bin/env python3
"""Verify DRS Cross-Account KMS Setup"""
import boto3
import json

SOURCE_ACCOUNT = "777788889999"
TARGET_ACCOUNT = "111122223333"
KEY_ID = "ab256143-c334-4d8b-bd7d-67475d8721d0"
REGION = "us-west-2"

session = boto3.Session(profile_name=f'{SOURCE_ACCOUNT}_AdministratorAccess')
kms = session.client('kms', region_name=REGION)
ec2 = session.client('ec2', region_name=REGION)

print("=== DRS Cross-Account KMS Verification ===\n")

# 1. Verify KMS key policy
print("1. KMS Key Policy:")
policy = json.loads(kms.get_key_policy(KeyId=KEY_ID, PolicyName='default')['Policy'])
has_drs_service = any(s.get('Principal', {}).get('Service') == 'drs.amazonaws.com' for s in policy['Statement'])
has_target_account = any(TARGET_ACCOUNT in str(s.get('Principal', {}).get('AWS', [])) for s in policy['Statement'])
has_create_grant = any('kms:CreateGrant' in s.get('Action', []) for s in policy['Statement'])
print(f"   ✓ DRS service principal: {has_drs_service}")
print(f"   ✓ Target account access: {has_target_account}")
print(f"   ✓ CreateGrant permission: {has_create_grant}\n")

# 2. Check EBS default encryption
print("2. EBS Default Encryption:")
ebs_encryption = ec2.get_ebs_encryption_by_default()
default_key = ec2.get_ebs_default_kms_key_id()
print(f"   Enabled: {ebs_encryption['EbsEncryptionByDefault']}")
print(f"   Default Key: {default_key.get('KmsKeyId', 'AWS managed')}\n")

# 3. Verify key grants
print("3. KMS Key Grants:")
grants = kms.list_grants(KeyId=KEY_ID)
print(f"   Active grants: {len(grants['Grants'])}")
for grant in grants['Grants'][:3]:
    print(f"   - {grant.get('GranteePrincipal', 'Unknown')[:50]}...")

print("\n✓ Verification complete!")
