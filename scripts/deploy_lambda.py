#!/usr/bin/env python3
"""
Lambda Deployment Script
Automates the process of packaging and deploying Lambda functions
"""

import argparse
import hashlib
import os
import sys
import zipfile
from pathlib import Path

import boto3

# AWS clients
s3 = boto3.client("s3")
lambda_client = boto3.client("lambda")
cfn = boto3.client("cloudformation")


def calculate_file_hash(filepath):
    """Calculate SHA256 hash of file"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def create_lambda_package(source_file, package_dir, output_zip):
    """Create Lambda deployment package with dependencies"""
    print(f"\n📦 Creating Lambda package: {output_zip}")

    # Remove old zip if exists
    if os.path.exists(output_zip):
        os.remove(output_zip)
        print("  Removed old package")

    # Create zip file
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add main handler file
        zipf.write(source_file, os.path.basename(source_file))
        print(f"  ✅ Added {os.path.basename(source_file)}")

        # Add other Python files in the lambda directory (like rbac_middleware.py)
        lambda_dir = os.path.dirname(source_file)
        python_files = 0
        for file in os.listdir(lambda_dir):
            if file.endswith(".py") and file != os.path.basename(source_file):
                file_path = os.path.join(lambda_dir, file)
                if os.path.isfile(file_path):
                    zipf.write(file_path, file)
                    python_files += 1
                    print(f"  ✅ Added {file}")

        if python_files > 0:
            print(f"  ✅ Added {python_files} additional Python files")

        # Add dependencies from package directory
        if os.path.exists(package_dir):
            package_files = 0
            for root, dirs, files in os.walk(package_dir):
                # Skip __pycache__ and .pyc files
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for file in files:
                    if file.endswith(".pyc"):
                        continue

                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, package_dir)
                    zipf.write(file_path, arcname)
                    package_files += 1

            print(f"  ✅ Added {package_files} dependency files from package/")
        else:
            print(f"  ⚠️  Package directory not found: {package_dir}")

    # Get zip file size
    zip_size = os.path.getsize(output_zip)
    zip_size_mb = zip_size / (1024 * 1024)

    print(f"  📊 Package size: {zip_size_mb:.2f} MB")
    print("  🎉 Package created successfully")

    return output_zip


def upload_to_s3(local_file, bucket, s3_key):
    """Upload file to S3"""
    print(f"\n☁️  Uploading to S3: s3://{bucket}/{s3_key}")

    try:
        s3.upload_file(
            local_file,
            bucket,
            s3_key,
            ExtraArgs={"ContentType": "application/zip"},
        )
        print("  ✅ Upload successful")
        return True
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return False


def update_lambda_function(function_name, zip_file):
    """Update Lambda function code directly (bypass CloudFormation)"""
    print(f"\n🔄 Updating Lambda function: {function_name}")

    try:
        with open(zip_file, "rb") as f:
            zip_data = f.read()

        response = lambda_client.update_function_code(
            FunctionName=function_name, ZipFile=zip_data, Publish=False
        )

        print("  ✅ Function updated successfully")
        print(f"  📝 Last Modified: {response['LastModified']}")
        print(f"  🔢 Code Size: {response['CodeSize']} bytes")
        print(f"  🏷️  Version: {response['Version']}")

        # Wait for update to complete
        print("  ⏳ Waiting for update to complete...")
        waiter = lambda_client.get_waiter("function_updated")
        waiter.wait(FunctionName=function_name)
        print("  ✅ Update complete")

        return True
    except Exception as e:
        print(f"  ❌ Update failed: {e}")
        return False


def update_via_cloudformation(stack_name, bucket, s3_key):
    """Trigger CloudFormation stack update to deploy new Lambda code"""
    print(f"\n🔄 Triggering CloudFormation stack update: {stack_name}")

    try:
        # Get current stack parameters
        response = cfn.describe_stacks(StackName=stack_name)
        stack = response["Stacks"][0]

        # Extract current parameters
        parameters = [
            {"ParameterKey": p["ParameterKey"], "UsePreviousValue": True}
            for p in stack.get("Parameters", [])
        ]

        # Update stack (this will redeploy Lambda with new code from S3)
        cfn.update_stack(
            StackName=stack_name,
            UsePreviousTemplate=True,
            Parameters=parameters,
            Capabilities=["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
        )

        print("  ✅ Stack update initiated")
        print("  ⏳ Waiting for stack update to complete...")

        # Wait for update
        waiter = cfn.get_waiter("stack_update_complete")
        waiter.wait(StackName=stack_name)

        print("  ✅ Stack update complete")
        return True

    except cfn.exceptions.ClientError as e:
        if "No updates are to be performed" in str(e):
            print("  ℹ️  No updates needed - Lambda already has this code")
            return True
        else:
            print(f"  ❌ Stack update failed: {e}")
            return False
    except Exception as e:
        print(f"  ❌ Stack update failed: {e}")
        return False


def deploy_api_handler(args):
    """Deploy API Handler Lambda function"""
    print("\n" + "=" * 70)
    print("🚀 Deploying API Handler Lambda")
    print("=" * 70)

    lambda_dir = Path(__file__).parent
    source_file = lambda_dir / "index.py"
    package_dir = lambda_dir / "package"
    output_zip = lambda_dir / "api-handler.zip"

    # Create package
    create_lambda_package(str(source_file), str(package_dir), str(output_zip))

    if args.s3_only or args.full:
        # Upload to S3
        if upload_to_s3(
            str(output_zip), args.bucket, "lambda/api-handler.zip"
        ):
            print(
                f"  ✅ Lambda package available at "
                f"s3://{args.bucket}/lambda/api-handler.zip"
            )

    if args.direct or args.full:
        # Direct Lambda update
        if not update_lambda_function(args.function_name, str(output_zip)):
            return False

    if args.cfn:
        # CloudFormation update
        if not update_via_cloudformation(
            args.stack_name, args.bucket, "lambda/api-handler.zip"
        ):
            return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Lambda functions to AWS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy directly to Lambda (fastest, for development)
  python deploy_lambda.py --direct --function-name drs-orchestration-api-handler-test

  # Upload to S3 only (for CloudFormation deployments)
  python deploy_lambda.py --s3-only --bucket aws-drs-orchestration

  # Full deployment: S3 + Direct update
  python deploy_lambda.py --full --bucket aws-drs-orchestration --function-name drs-orchestration-api-handler-test

  # Deploy via CloudFormation stack update
  python deploy_lambda.py --cfn --bucket aws-drs-orchestration --stack-name drs-orchestration-test
        """,
    )

    # Deployment modes
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Deploy directly to Lambda function (bypass CloudFormation)",
    )
    parser.add_argument(
        "--s3-only",
        action="store_true",
        help="Upload to S3 only (for CloudFormation)",
    )
    parser.add_argument(
        "--cfn",
        action="store_true",
        help="Deploy via CloudFormation stack update",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full deployment: Upload to S3 + Direct Lambda update",
    )

    # Parameters
    parser.add_argument(
        "--function-name",
        default="drs-orchestration-api-handler-test",
        help="Lambda function name (for --direct)",
    )
    parser.add_argument(
        "--bucket",
        default="aws-drs-orchestration",
        help="S3 bucket for Lambda packages",
    )
    parser.add_argument(
        "--stack-name",
        default="drs-orchestration-test",
        help="CloudFormation stack name (for --cfn)",
    )
    parser.add_argument("--region", default="us-east-1", help="AWS region")

    args = parser.parse_args()

    # Validate deployment mode
    if not (args.direct or args.s3_only or args.cfn or args.full):
        parser.error(
            "Must specify deployment mode: --direct, --s3-only, --cfn, "
            "or --full"
        )

    # Configure AWS region
    os.environ["AWS_DEFAULT_REGION"] = args.region

    # Deploy
    success = deploy_api_handler(args)

    if success:
        print("\n" + "=" * 70)
        print("✅ DEPLOYMENT SUCCESSFUL")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("❌ DEPLOYMENT FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
