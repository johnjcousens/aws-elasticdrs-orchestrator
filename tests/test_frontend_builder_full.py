#!/usr/bin/env python3
"""
Full localhost test environment for frontend-builder Lambda
Mocks AWS services (S3, CloudFront) to test complete deployment flow
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add Lambda package to path
LAMBDA_PACKAGE_PATH = "/tmp/frontend-builder-package"
sys.path.insert(0, LAMBDA_PACKAGE_PATH)

# Test configuration
TEST_CONFIG = {
    "BucketName": "test-frontend-bucket",
    "DistributionId": "d123456789abcdef",
    "SourceBucket": "aws-drs-orch-dev",
    "ApiEndpoint": "https://test-api.execute-api.us-east-1.amazonaws.com/prod",
    "UserPoolId": "us-east-1_testABC123",
    "UserPoolClientId": "test-client-id-123456",
    "Region": "us-east-1",
}


class MockS3Client:
    """Mock S3 client for testing"""

    def __init__(self):
        self.uploaded_files = []
        self.deleted_objects = []

    def upload_file(self, local_path, bucket, key, ExtraArgs=None):
        """Mock S3 upload_file"""
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")

        file_size = os.path.getsize(local_path)
        self.uploaded_files.append(
            {"local_path": local_path, "bucket": bucket, "key": key, "size": file_size, "extra_args": ExtraArgs}
        )
        print(f"  [MOCK S3] Uploaded: {key} ({file_size} bytes)")
        return {}

    def get_paginator(self, operation):
        """Mock S3 paginator"""
        paginator = Mock()
        paginator.paginate = Mock(
            return_value=[
                {
                    "Versions": [
                        {"Key": "index.html", "VersionId": "v1"},
                        {"Key": "assets/app.js", "VersionId": "v1"},
                    ],
                    "DeleteMarkers": [],
                }
            ]
        )
        return paginator

    def delete_objects(self, Bucket, Delete):
        """Mock S3 delete_objects"""
        objects = Delete.get("Objects", [])
        self.deleted_objects.extend(objects)
        print(f"  [MOCK S3] Deleted {len(objects)} objects from {Bucket}")
        return {"Deleted": objects}

    @property
    def exceptions(self):
        """Mock S3 exceptions"""

        class Exceptions:
            class NoSuchBucket(Exception):
                pass

        return Exceptions()


class MockCloudFrontClient:
    """Mock CloudFront client for testing"""

    def __init__(self):
        self.invalidations = []

    def create_invalidation(self, DistributionId, InvalidationBatch):
        """Mock CloudFront create_invalidation"""
        invalidation_id = f"I{len(self.invalidations) + 1}ABCDEFGHIJK"
        self.invalidations.append(
            {
                "distribution_id": DistributionId,
                "paths": InvalidationBatch["Paths"]["Items"],
                "invalidation_id": invalidation_id,
            }
        )
        print(f"  [MOCK CloudFront] Created invalidation: {invalidation_id}")
        return {"Invalidation": {"Id": invalidation_id, "Status": "InProgress"}}


def test_full_deployment_flow():
    """Test complete deployment flow with mocked AWS services"""
    print("\n" + "=" * 60)
    print("FULL DEPLOYMENT FLOW TEST")
    print("=" * 60)

    # Create mock AWS clients
    mock_s3 = MockS3Client()
    mock_cloudfront = MockCloudFrontClient()

    # Mock context
    mock_context = Mock()
    mock_context.aws_request_id = "test-request-12345"

    # Create CloudFormation event
    event = {
        "RequestType": "Create",
        "ResourceProperties": TEST_CONFIG,
        "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack/guid",
        "RequestId": "test-request-12345",
        "LogicalResourceId": "BuildAndDeployFrontendResource",
    }

    print(f"\n📋 Test Configuration:")
    print(f"  Bucket: {TEST_CONFIG['BucketName']}")
    print(f"  Distribution: {TEST_CONFIG['DistributionId']}")
    print(f"  API Endpoint: {TEST_CONFIG['ApiEndpoint']}")
    print(f"  User Pool: {TEST_CONFIG['UserPoolId']}")

    try:
        # Patch boto3 clients
        with patch("boto3.client") as mock_boto3_client:

            def get_mock_client(service_name, **kwargs):
                if service_name == "s3":
                    return mock_s3
                elif service_name == "cloudfront":
                    return mock_cloudfront
                else:
                    return Mock()

            mock_boto3_client.side_effect = get_mock_client

            # Import Lambda handler (after patching boto3)
            from index import create_or_update

            print("\n🚀 Starting deployment...")

            # Patch the Lambda frontend path to use local package path
            with patch("os.path.exists") as mock_exists:
                original_exists = os.path.exists

                def custom_exists(path):
                    # Redirect /var/task/frontend to local package path
                    if path == "/var/task/frontend":
                        return original_exists(os.path.join(LAMBDA_PACKAGE_PATH, "frontend"))
                    return original_exists(path)

                mock_exists.side_effect = custom_exists

                # Patch use_prebuilt_dist to use local path
                with patch("index.use_prebuilt_dist") as mock_use_prebuilt:

                    def custom_use_prebuilt(frontend_dir):
                        # Use local package path instead of /var/task
                        local_frontend = os.path.join(LAMBDA_PACKAGE_PATH, "frontend")
                        dist_dir = os.path.join(local_frontend, "dist")
                        if not os.path.exists(dist_dir):
                            raise FileNotFoundError(f"dist not found at {dist_dir}")
                        print(f"Using pre-built dist folder from Lambda package...")
                        print(
                            f"Found pre-built dist directory with {sum(1 for _ in Path(dist_dir).rglob('*') if _.is_file())} files"
                        )
                        return dist_dir

                    mock_use_prebuilt.side_effect = custom_use_prebuilt

                    # Execute Lambda handler
                    result = create_or_update(event, mock_context)

            print("\n✅ Deployment completed successfully!")
            print(f"\n📊 Deployment Results:")
            print(f"  Files Deployed: {result.get('FilesDeployed', 0)}")
            print(f"  Build Type: {result.get('BuildType', 'unknown')}")
            print(f"  Config Files: {result.get('ConfigFiles', 'unknown')}")
            print(f"  Invalidation ID: {result.get('InvalidationId', 'none')}")

            # Verify S3 uploads
            print(f"\n📦 S3 Upload Summary:")
            print(f"  Total files uploaded: {len(mock_s3.uploaded_files)}")

            # Group by file type
            file_types = {}
            for upload in mock_s3.uploaded_files:
                ext = os.path.splitext(upload["key"])[1] or "no-ext"
                file_types[ext] = file_types.get(ext, 0) + 1

            for ext, count in sorted(file_types.items()):
                print(f"    {ext}: {count} files")

            # Check for required files
            uploaded_keys = [u["key"] for u in mock_s3.uploaded_files]
            required_files = ["index.html", "aws-config.json"]

            print(f"\n✓ Required Files Check:")
            for req_file in required_files:
                if req_file in uploaded_keys:
                    print(f"  ✅ {req_file}")
                else:
                    print(f"  ❌ {req_file} - MISSING!")
                    return False

            # Check cache control headers
            print(f"\n✓ Cache Control Headers:")
            for upload in mock_s3.uploaded_files[:5]:  # Show first 5
                key = upload["key"]
                cache_control = upload["extra_args"].get("CacheControl", "none")
                print(f"  {key}: {cache_control}")

            # Verify CloudFront invalidation
            print(f"\n☁️  CloudFront Invalidation:")
            if mock_cloudfront.invalidations:
                inv = mock_cloudfront.invalidations[0]
                print(f"  ✅ Invalidation created: {inv['invalidation_id']}")
                print(f"  Paths: {inv['paths']}")
            else:
                print(f"  ❌ No invalidation created!")
                return False

            print("\n🎉 ALL CHECKS PASSED!")
            return True

    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_delete_flow():
    """Test CloudFormation delete flow"""
    print("\n" + "=" * 60)
    print("DELETE FLOW TEST")
    print("=" * 60)

    # Create mock AWS clients
    mock_s3 = MockS3Client()

    # Mock context
    mock_context = Mock()
    mock_context.aws_request_id = "test-delete-request-12345"

    # Create CloudFormation delete event
    event = {
        "RequestType": "Delete",
        "ResourceProperties": TEST_CONFIG,
        "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack/guid",
        "RequestId": "test-delete-request-12345",
        "LogicalResourceId": "BuildAndDeployFrontendResource",
    }

    try:
        # Patch boto3 clients
        with patch("boto3.client") as mock_boto3_client:
            mock_boto3_client.return_value = mock_s3

            # Import Lambda handler
            from index import delete

            print("\n🗑️  Starting bucket cleanup...")

            # Execute delete handler
            result = delete(event, mock_context)

            print("\n✅ Cleanup completed successfully!")
            print(f"\n📊 Cleanup Results:")
            print(f"  Objects deleted: {len(mock_s3.deleted_objects)}")

            for obj in mock_s3.deleted_objects[:5]:  # Show first 5
                print(f"    - {obj['Key']} (version: {obj['VersionId']})")

            if len(mock_s3.deleted_objects) > 5:
                print(f"    ... and {len(mock_s3.deleted_objects) - 5} more")

            print("\n🎉 DELETE TEST PASSED!")
            return True

    except Exception as e:
        print(f"\n❌ Delete failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_config_injection_details():
    """Test config injection with detailed output"""
    print("\n" + "=" * 60)
    print("CONFIG INJECTION DETAILED TEST")
    print("=" * 60)

    try:
        from index import inject_aws_config_into_dist

        # Create temp copy of dist
        with tempfile.TemporaryDirectory() as temp_dir:
            import shutil

            source_dist = os.path.join(LAMBDA_PACKAGE_PATH, "frontend/dist")
            temp_dist = os.path.join(temp_dir, "dist")
            shutil.copytree(source_dist, temp_dist)

            print(f"\n📁 Working directory: {temp_dist}")

            # Inject config
            properties = {
                "Region": TEST_CONFIG["Region"],
                "UserPoolId": TEST_CONFIG["UserPoolId"],
                "UserPoolClientId": TEST_CONFIG["UserPoolClientId"],
                "ApiEndpoint": TEST_CONFIG["ApiEndpoint"],
            }

            print(f"\n⚙️  Injecting configuration...")
            inject_aws_config_into_dist(temp_dist, properties)

            # Verify aws-config.json
            config_json_path = os.path.join(temp_dist, "aws-config.json")
            if os.path.exists(config_json_path):
                with open(config_json_path, "r") as f:
                    config_data = json.load(f)

                print(f"\n✅ aws-config.json created:")
                print(json.dumps(config_data, indent=2))
            else:
                print(f"\n❌ aws-config.json NOT created!")
                return False

            # Verify aws-config.js
            config_js_path = os.path.join(temp_dist, "assets/aws-config.js")
            if os.path.exists(config_js_path):
                with open(config_js_path, "r") as f:
                    js_content = f.read()

                print(f"\n✅ aws-config.js created ({len(js_content)} bytes)")
                print(f"First 200 chars:")
                print(js_content[:200] + "...")
            else:
                print(f"\n❌ aws-config.js NOT created!")
                return False

            # Verify index.html injection
            index_html_path = os.path.join(temp_dist, "index.html")
            with open(index_html_path, "r") as f:
                html_content = f.read()

            if "aws-config.js" in html_content:
                print(f"\n✅ index.html references aws-config.js")

                # Find the script tag
                import re

                script_match = re.search(r"<script[^>]*aws-config\.js[^>]*>", html_content)
                if script_match:
                    print(f"Script tag: {script_match.group()}")
            else:
                print(f"\n❌ index.html does NOT reference aws-config.js!")
                return False

            print("\n🎉 CONFIG INJECTION TEST PASSED!")
            return True

    except Exception as e:
        print(f"\n❌ Config injection failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_all_tests():
    """Run all localhost tests"""
    print("\n" + "=" * 60)
    print("FRONTEND-BUILDER LOCALHOST TEST SUITE")
    print("=" * 60)
    print(f"Lambda package: {LAMBDA_PACKAGE_PATH}")

    if not os.path.exists(LAMBDA_PACKAGE_PATH):
        print(f"\n❌ FATAL: Lambda package not found at {LAMBDA_PACKAGE_PATH}")
        return False

    tests = [
        ("Config Injection Details", test_config_injection_details),
        ("Full Deployment Flow", test_full_deployment_flow),
        ("Delete Flow", test_delete_flow),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {test_name}")
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nResults: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED - Ready for CloudFormation deployment!")
        print("\nNext steps:")
        print("1. Upload Lambda: aws s3 cp /tmp/frontend-builder.zip s3://aws-drs-orch-dev/lambda/")
        print("2. Deploy stack: aws cloudformation deploy --stack-name aws-drs-orch-dev ...")
        return True
    else:
        print(f"\n❌ {total_count - passed_count} TESTS FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
