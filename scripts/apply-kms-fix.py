#!/usr/bin/env python3
import json
import boto3

KEY_ID = "ab256143-c334-4d8b-bd7d-67475d8721d0"
REGION = "us-west-2"

policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Enable IAM User Permissions",
            "Effect": "Allow",
            "Principal": {"AWS": "arn:aws:iam::777788889999:root"},
            "Action": "kms:*",
            "Resource": "*"
        },
        {
            "Sid": "Allow use of the key by target account",
            "Effect": "Allow",
            "Principal": {
                "AWS": [
                    "arn:aws:iam::111122223333:root",
                    "arn:aws:iam::111122223333:role/aws-service-role/drs.amazonaws.com/AWSServiceRoleForElasticDisasterRecovery"
                ]
            },
            "Action": [
                "kms:Encrypt",
                "kms:Decrypt",
                "kms:ReEncrypt*",
                "kms:GenerateDataKey*",
                "kms:DescribeKey",
                "kms:CreateGrant",
                "kms:ListGrants",
                "kms:RevokeGrant"
            ],
            "Resource": "*"
        },
        {
            "Sid": "Allow DRS service to use the key",
            "Effect": "Allow",
            "Principal": {"Service": "drs.amazonaws.com"},
            "Action": ["kms:Decrypt", "kms:DescribeKey", "kms:CreateGrant", "kms:ListGrants"],
            "Resource": "*"
        },
        {
            "Sid": "Allow attachment of persistent resources",
            "Effect": "Allow",
            "Principal": {
                "AWS": [
                    "arn:aws:iam::111122223333:root",
                    "arn:aws:iam::111122223333:role/aws-service-role/drs.amazonaws.com/AWSServiceRoleForElasticDisasterRecovery"
                ]
            },
            "Action": ["kms:CreateGrant", "kms:ListGrants", "kms:RevokeGrant"],
            "Resource": "*",
            "Condition": {"Bool": {"kms:GrantIsForAWSResource": "true"}}
        }
    ]
}

session = boto3.Session(profile_name='777788889999_AdministratorAccess')
kms = session.client('kms', region_name=REGION)
print(f"Applying KMS policy fix to key {KEY_ID}...")
kms.put_key_policy(KeyId=KEY_ID, PolicyName='default', Policy=json.dumps(policy))
print("✓ Policy updated successfully!")
