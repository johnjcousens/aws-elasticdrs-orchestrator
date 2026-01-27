#!/usr/bin/env python3
"""Empty S3 bucket to allow CloudFormation stack deletion."""

import boto3
import sys


def empty_bucket(bucket_name: str) -> None:
    """Empty all objects and versions from S3 bucket."""
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket_name)

    print(f"Emptying bucket: {bucket_name}")

    # Delete all object versions
    try:
        bucket.object_versions.delete()
        print("✓ Deleted all object versions")
    except Exception as e:
        print(f"✗ Error deleting versions: {e}")

    # Delete all objects
    try:
        bucket.objects.all().delete()
        print("✓ Deleted all objects")
    except Exception as e:
        print(f"✗ Error deleting objects: {e}")

    print(f"✓ Bucket {bucket_name} is now empty")


if __name__ == "__main__":
    cfn = boto3.client("cloudformation", region_name="us-east-1")
    stack_name = "aws-drs-orch-dev-FrontendStack-1AGX1Z8FAPJKT"

    try:
        response = cfn.describe_stack_resources(StackName=stack_name)
        bucket_name = None

        for resource in response["StackResources"]:
            if resource["ResourceType"] == "AWS::S3::Bucket":
                bucket_name = resource["PhysicalResourceId"]
                break

        if bucket_name:
            empty_bucket(bucket_name)
        else:
            print("✗ Could not find S3 bucket in stack resources")
            sys.exit(1)

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
