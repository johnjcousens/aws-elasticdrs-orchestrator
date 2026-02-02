"""
Frontend Deployer Custom Resource

Consolidated Lambda function that handles:
- CREATE: Deploy pre-built React application to S3 with CloudFormation
  configuration injection
- UPDATE: Redeploy frontend with updated configuration
- DELETE: Empty S3 bucket ONLY during actual stack deletion (not UPDATE
  operations)

This Lambda replaces the separate frontend-builder and bucket-cleaner functions
to simplify the architecture and prevent data loss during UPDATE operations.

Key Design Decisions:
1. Stable PhysicalResourceId: Uses `frontend-deployer-{bucket_name}` to prevent
   CloudFormation from treating UPDATE operations as resource replacements.
2. Safe DELETE Handling: Only empties bucket when stack status contains
   "DELETE_IN_PROGRESS". Skips cleanup for UPDATE operations and rollbacks.
3. Graceful Error Recovery: DELETE always returns SUCCESS to allow stack
   deletion to continue, even if cleanup fails.
"""

import json
import logging
import os
import shutil
import tempfile
import traceback

import boto3
from botocore.exceptions import ClientError
from crhelper import CfnResource

# Import security utilities (mandatory - no fallback)
from shared.security_utils import (
    log_security_event,
    safe_aws_client_call,
    sanitize_string_input,
    validate_file_path,
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
cloudfront = boto3.client("cloudfront")
cfn = boto3.client("cloudformation")

# Use a stable PhysicalResourceId to prevent CloudFormation from
# treating updates as resource replacements (which triggers DELETE)
helper = CfnResource(
    json_logging=False,
    log_level="INFO",
    boto_level="CRITICAL",
    polling_interval=2,
)


def get_physical_resource_id(bucket_name: str) -> str:
    """
    Generate stable PhysicalResourceId based on bucket name.

    This deterministic ID prevents CloudFormation from treating UPDATE
    operations as resource replacements (which would trigger DELETE events
    and potential data loss).

    Args:
        bucket_name: The S3 bucket name for frontend hosting

    Returns:
        Stable PhysicalResourceId in format: frontend-deployer-{bucket_name}
    """
    return f"frontend-deployer-{bucket_name}"


def should_empty_bucket(stack_id: str, bucket_name: str) -> tuple:
    """
    Determine if bucket should be emptied based on stack status.

    SAFETY FIRST: Only empties bucket during confirmed stack deletion.
    Skips cleanup for UPDATE operations, rollbacks, and uncertain scenarios.

    Args:
        stack_id: CloudFormation stack ID from the event
        bucket_name: S3 bucket name for logging

    Returns:
        Tuple of (should_empty: bool, reason: str, stack_status: str)
    """
    if not stack_id:
        return (False, "no_stack_id", "unknown")

    try:
        response = cfn.describe_stacks(StackName=stack_id)
        stack_status = response["Stacks"][0]["StackStatus"]

        # Log stack status when making cleanup decisions (Requirement 8.2)
        print(f"Frontend Deployer DELETE: Stack status is '{stack_status}'")
        logger.info(f"Frontend Deployer DELETE: Stack status is '{stack_status}'")
        log_security_event(
            "stack_status_checked",
            {
                "bucket_name": bucket_name,
                "stack_status": stack_status,
                "stack_id": stack_id,
            },
        )

        # SAFETY CHECK 1: Never empty during UPDATE_ROLLBACK
        # This means an UPDATE failed and is rolling back - bucket should stay
        if "UPDATE_ROLLBACK" in stack_status:
            return (False, "update_rollback_in_progress", stack_status)

        # SAFETY CHECK 2: Only proceed if stack is actively being DELETED
        # DELETE_IN_PROGRESS: Stack deletion in progress - safe to empty
        # DELETE_FAILED: Stack deletion failed (likely due to bucket) - retry
        if stack_status in ["DELETE_IN_PROGRESS", "DELETE_FAILED"]:
            return (True, "stack_deletion", stack_status)

        # SAFETY CHECK 3: Any other status means NOT a deletion - skip cleanup
        # This includes UPDATE_IN_PROGRESS, UPDATE_COMPLETE, etc.
        return (False, "not_stack_deletion", stack_status)

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        # SAFETY CHECK 4: If stack doesn't exist, be VERY careful
        # This could mean:
        # a) Stack was deleted (safe to empty bucket)
        # b) Wrong stack ID provided (NOT safe)
        # Default to NOT emptying unless we're certain
        if error_code == "ValidationError" and "does not exist" in str(e):
            print(
                "Frontend Deployer DELETE: Stack does not exist - "
                "skipping cleanup for safety (stack may have been deleted "
                "already or wrong stack ID)"
            )
            logger.warning(
                "Frontend Deployer DELETE: Stack does not exist - " "skipping cleanup for safety"
            )
            log_security_event(
                "stack_not_found_skip_cleanup",
                {
                    "bucket_name": bucket_name,
                    "stack_id": stack_id,
                    "reason": "Cannot verify stack deletion intent",
                },
                severity="WARN",
            )
            return (False, "stack_not_found", "UNKNOWN")

        # Other errors - skip cleanup to be safe
        stack_trace = traceback.format_exc()
        print(
            f"Frontend Deployer DELETE: Could not check stack status: {e} - "
            f"skipping cleanup to be safe"
        )
        logger.error(f"Frontend Deployer DELETE: Could not check stack status: {e}")
        logger.error(f"Frontend Deployer DELETE Stack trace: {stack_trace}")
        log_security_event(
            "stack_status_check_failed",
            {
                "bucket_name": bucket_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "stack_trace": stack_trace,
            },
            severity="WARN",
        )
        return (False, "status_check_failed", "unknown")

    except Exception as e:
        # If we can't check status, skip cleanup to be safe
        stack_trace = traceback.format_exc()
        print(
            f"Frontend Deployer DELETE: Could not check stack status: {e} - "
            f"skipping cleanup to be safe"
        )
        logger.error(f"Frontend Deployer DELETE: Could not check stack status: {e}")
        logger.error(f"Frontend Deployer DELETE Stack trace: {stack_trace}")
        log_security_event(
            "stack_status_check_failed",
            {
                "bucket_name": bucket_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "stack_trace": stack_trace,
            },
            severity="WARN",
        )
        return (False, "status_check_failed", "unknown")


def empty_bucket(bucket_name: str) -> int:
    """
    Empty an S3 bucket by deleting all objects, versions, and delete markers.

    Args:
        bucket_name: Name of the S3 bucket to empty

    Returns:
        int: Total number of objects deleted
    """
    total_deleted = 0

    try:
        # Check if bucket exists
        try:
            s3.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                print(
                    f"Frontend Deployer: Bucket {bucket_name} does not exist " f"- nothing to clean"
                )
                logger.info(f"Bucket {bucket_name} does not exist - nothing to clean")
                log_security_event(
                    "bucket_not_found",
                    {"bucket_name": bucket_name},
                )
                return 0
            else:
                raise

        print(f"Frontend Deployer: Starting to empty bucket: {bucket_name}")
        logger.info(f"Starting to empty bucket: {bucket_name}")

        # Delete all object versions and delete markers
        paginator = s3.get_paginator("list_object_versions")

        # Track if we found any objects
        found_objects = False

        for page in paginator.paginate(Bucket=bucket_name):
            # Collect objects to delete
            objects_to_delete = []

            # Add current versions
            if "Versions" in page:
                found_objects = True
                for version in page["Versions"]:
                    objects_to_delete.append(
                        {
                            "Key": version["Key"],
                            "VersionId": version["VersionId"],
                        }
                    )

            # Add delete markers
            if "DeleteMarkers" in page:
                found_objects = True
                for marker in page["DeleteMarkers"]:
                    objects_to_delete.append(
                        {
                            "Key": marker["Key"],
                            "VersionId": marker["VersionId"],
                        }
                    )

            # Delete objects in batches (max 1000 per request)
            if objects_to_delete:
                batch_size = 1000
                for i in range(0, len(objects_to_delete), batch_size):
                    batch = objects_to_delete[i: i + batch_size]

                    print(
                        f"Frontend Deployer: Deleting batch of {len(batch)} "
                        f"objects from {bucket_name}"
                    )
                    logger.info(f"Deleting batch of {len(batch)} objects from " f"{bucket_name}")

                    response = s3.delete_objects(
                        Bucket=bucket_name,
                        Delete={"Objects": batch, "Quiet": False},
                    )

                    # Log any errors
                    if "Errors" in response and response["Errors"]:
                        for error in response["Errors"]:
                            logger.warning(
                                f"Failed to delete {error['Key']} "
                                f"(version {error.get('VersionId', 'N/A')}): "
                                f"{error['Code']} - {error['Message']}"
                            )

                    # Count successful deletions
                    if "Deleted" in response:
                        total_deleted += len(response["Deleted"])

        if not found_objects:
            print(f"Frontend Deployer: Bucket {bucket_name} is already empty")
            logger.info(f"Bucket {bucket_name} is already empty")

        # Verify bucket is empty by checking both regular objects and versions
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        versions_response = s3.list_object_versions(Bucket=bucket_name, MaxKeys=1)

        has_objects = "Contents" in response
        has_versions = "Versions" in versions_response
        has_markers = "DeleteMarkers" in versions_response

        if has_objects or has_versions or has_markers:
            logger.warning(
                f"Bucket {bucket_name} still contains objects after cleanup: "
                f"objects={has_objects}, versions={has_versions}, "
                f"markers={has_markers}"
            )
            print(f"Frontend Deployer: ⚠️ Bucket {bucket_name} still has " f"content after cleanup")
        else:
            print(f"Frontend Deployer: Bucket {bucket_name} is now empty")
            logger.info(f"Bucket {bucket_name} is now empty")

        return total_deleted

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            print(f"Frontend Deployer: Bucket {bucket_name} does not exist - " f"nothing to clean")
            logger.info(f"Bucket {bucket_name} does not exist - nothing to clean")
            return 0
        else:
            # Log full stack trace on errors (Requirement 8.5)
            stack_trace = traceback.format_exc()
            logger.error(
                f"AWS error emptying bucket {bucket_name}: {error_code} - "
                f"{e.response['Error']['Message']}"
            )
            logger.error(f"Stack trace: {stack_trace}")
            log_security_event(
                "bucket_empty_aws_error",
                {
                    "bucket_name": bucket_name,
                    "error_code": error_code,
                    "error_message": e.response["Error"]["Message"],
                    "stack_trace": stack_trace,
                },
                severity="ERROR",
            )
            raise


def use_prebuilt_dist(frontend_dir):
    """Use pre-built dist/ folder from Lambda package (no npm required)"""
    print("Using pre-built dist folder from Lambda package...")

    # Security validation for file paths
    validate_file_path(frontend_dir)
    frontend_dir = sanitize_string_input(frontend_dir)
    log_security_event("using_prebuilt_dist", {"frontend_dir": frontend_dir})

    dist_dir = os.path.join(frontend_dir, "dist")

    if not os.path.exists(dist_dir):
        error_msg = (
            f"Pre-built dist directory not found at {dist_dir}. "
            f"Lambda package must include pre-built frontend/dist/ folder."
        )
        log_security_event(
            "dist_directory_not_found",
            {"dist_dir": dist_dir, "error": error_msg},
        )
        raise FileNotFoundError(error_msg)

    # Count files in dist
    file_count = sum(1 for root, dirs, files in os.walk(dist_dir) for f in files)
    print(f"Found pre-built dist directory with {file_count} files")

    return dist_dir


def inject_aws_config_into_dist(dist_dir, properties):
    """
    Generate aws-config.js, aws-config.json, and inject script tag into
    index.html
    """
    print("Injecting AWS configuration into pre-built dist...")

    # Security validation for inputs
    validate_file_path(dist_dir)
    dist_dir = sanitize_string_input(dist_dir)
    region = sanitize_string_input(
        properties.get("region", os.environ.get("AWS_REGION", "us-west-2"))
    )
    log_security_event("injecting_aws_config", {"dist_dir": dist_dir, "region": region})

    # Create configuration object with sanitized values
    config_obj = {
        "region": region,
        "userPoolId": sanitize_string_input(properties.get("UserPoolId", "")),
        "userPoolClientId": sanitize_string_input(properties.get("UserPoolClientId", "")),
        "identityPoolId": sanitize_string_input(properties.get("IdentityPoolId", "")),
        "apiEndpoint": sanitize_string_input(properties.get("ApiEndpoint", "")),
    }

    # 1. Create aws-config.json at ROOT level (for fetch() in index.html)
    config_json_path = os.path.join(dist_dir, "aws-config.json")
    with open(config_json_path, "w") as f:
        json.dump(config_obj, f, indent=2)

    print("✅ Generated aws-config.json at ROOT level")
    print(f"  Region: {region}")
    print(f"  User Pool ID: {properties.get('UserPoolId', '')}")
    print(f"  API Endpoint: {properties.get('ApiEndpoint', '')}")

    # 2. Create aws-config.js in assets/ (for backwards compatibility)
    config_js_content = f"""// AWS Configuration - Auto-generated by CloudFormation Custom Resource
// DO NOT EDIT - This file is automatically generated during CloudFormation deployment

window.AWS_CONFIG = {{
  Auth: {{
    Cognito: {{
      region: '{region}',
      userPoolId: '{properties.get('UserPoolId', '')}',
      userPoolClientId: '{properties.get('UserPoolClientId', '')}',
      identityPoolId: '{properties.get('IdentityPoolId', '')}',
      loginWith: {{
        email: true
      }}
    }}
  }},
  API: {{
    REST: {{
      DRSOrchestration: {{
        endpoint: '{properties.get('ApiEndpoint', '')}',
        region: '{region}'
      }}
    }}
  }}
}};
"""  # noqa: E231,E241,E202,E501,E702

    # Create assets directory if it doesn't exist
    assets_dir = os.path.join(dist_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    config_js_path = os.path.join(assets_dir, "aws-config.js")
    with open(config_js_path, "w") as f:
        f.write(config_js_content)

    print("✅ Generated aws-config.js in dist/assets/ (backwards compatibility)")

    # 3. Inject script tag into index.html to load aws-config.js before React
    index_html_path = os.path.join(dist_dir, "index.html")
    if os.path.exists(index_html_path):
        with open(index_html_path, "r") as f:
            html_content = f.read()

        # Add script tag BEFORE the first script tag (React bundle)
        # This ensures aws-config.js loads and executes BEFORE React starts
        # Find the first <script tag and insert our config script before it
        import re

        script_pattern = r"(<script[^>]*>)"
        match = re.search(script_pattern, html_content, re.IGNORECASE)

        if match:
            # Insert config script before first script tag
            insert_pos = match.start()
            config_script = '    <script src="/assets/aws-config.js"></script>\n    '
            html_content = html_content[:insert_pos] + config_script + html_content[insert_pos:]
            print("✅ Injected aws-config.js script tag BEFORE React bundle")
        else:
            # Fallback: insert before </head> if no script tags found
            script_tag = '    <script src="/assets/aws-config.js"></script>\n  </head>'
            html_content = html_content.replace("</head>", script_tag)
            print("✅ Injected aws-config.js script tag before </head> " "(no script tags found)")

        with open(index_html_path, "w") as f:
            f.write(html_content)
    else:
        print(f"⚠️  WARNING: index.html not found at {index_html_path}")


def upload_to_s3(dist_dir, bucket_name):
    """Upload all files from dist directory to S3 with proper cache headers"""
    uploaded_files = []

    # Security validation for S3 inputs
    validate_file_path(dist_dir)
    bucket_name = sanitize_string_input(bucket_name)

    for root, dirs, files in os.walk(dist_dir):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, dist_dir)
            s3_key = relative_path.replace("\\", "/")

            # Security validation for file paths
            validate_file_path(local_path)
            s3_key = sanitize_string_input(s3_key)

            # Determine content type
            content_type = get_content_type(file)

            # Set cache control based on file type
            # index.html & aws-config.json: no cache (always fetch fresh)
            # Static assets: long-term cache (immutable with hashed filenames)
            if file in ["index.html", "aws-config.json"]:
                cache_control = "no-cache, no-store, must-revalidate"
            else:
                cache_control = "public, max-age=31536000, immutable"

            def upload_call():
                return s3.upload_file(
                    local_path,
                    bucket_name,
                    s3_key,
                    ExtraArgs={
                        "ContentType": content_type,
                        "CacheControl": cache_control,
                    },
                )

            safe_aws_client_call(upload_call)

            uploaded_files.append(s3_key)
            print(f"  Uploaded: {s3_key} ({content_type}, {cache_control})")

    return uploaded_files


def get_content_type(filename):
    """Determine content type from file extension"""
    ext = os.path.splitext(filename)[1].lower()

    content_types = {
        ".html": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".ttf": "font/ttf",
        ".eot": "application/vnd.ms-fontobject",
        ".txt": "text/plain",
        ".xml": "application/xml",
        ".pdf": "application/pdf",
    }

    return content_types.get(ext, "application/octet-stream")


@helper.create
@helper.update
def create_or_update(event, context):
    """Deploy pre-built frontend to S3 and invalidate CloudFront cache."""
    properties = event["ResourceProperties"]

    # Security validation for CloudFormation inputs
    bucket_name = sanitize_string_input(properties["BucketName"])
    distribution_id = sanitize_string_input(properties["DistributionId"])
    frontend_version = sanitize_string_input(properties.get("FrontendBuildVersion", "v1"))

    # Stable PhysicalResourceId prevents CloudFormation replacement behavior
    # CRITICAL: This ID must be deterministic and based ONLY on the bucket name
    # Using a consistent prefix ensures UPDATE operations are never treated as
    # resource replacements (which would trigger DELETE events and data loss)
    helper.PhysicalResourceId = get_physical_resource_id(bucket_name)

    log_security_event(
        "frontend_deployment_started",
        {
            "bucket_name": bucket_name,
            "distribution_id": distribution_id,
            "frontend_version": frontend_version,
            "request_id": context.aws_request_id,
            "physical_resource_id": helper.PhysicalResourceId,
        },
    )

    print(
        f"Frontend Deployer: Deploying frontend version {frontend_version} "
        f"to bucket: {bucket_name}"
    )

    try:
        # Get frontend source from Lambda package
        lambda_frontend_path = "/var/task/frontend"
        if not os.path.exists(lambda_frontend_path):
            error_msg = f"Frontend source not found in Lambda package at " f"{lambda_frontend_path}"
            log_security_event(
                "frontend_source_not_found",
                {"path": lambda_frontend_path, "error": error_msg},
            )
            raise FileNotFoundError(error_msg)

        print(f"Found frontend source in Lambda package at " f"{lambda_frontend_path}")

        # Use pre-built dist/ folder (no npm build required)
        dist_dir = use_prebuilt_dist(lambda_frontend_path)

        # Create temporary copy of dist to inject config
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dist = os.path.join(temp_dir, "dist")
            shutil.copytree(dist_dir, temp_dist)

            # Inject AWS configuration into pre-built dist
            inject_aws_config_into_dist(temp_dist, properties)

            # Upload dist to S3
            print("Uploading build artifacts to S3...")
            uploaded_files = upload_to_s3(temp_dist, bucket_name)

            print(f"✅ Upload complete. Total files: {len(uploaded_files)}")

        # Invalidate CloudFront cache
        print("Creating CloudFront invalidation...")

        def invalidation_call():
            return cloudfront.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    "Paths": {"Quantity": 1, "Items": ["/*"]},
                    "CallerReference": str(context.aws_request_id),
                },
            )

        invalidation_response = safe_aws_client_call(invalidation_call)

        invalidation_id = invalidation_response["Invalidation"]["Id"]

        # Log CloudFront invalidation ID on successful cache invalidation
        # (Requirement 8.4)
        print(f"Frontend Deployer: CloudFront invalidation created: " f"{invalidation_id}")
        logger.info(f"Frontend Deployer: CloudFront invalidation created: " f"{invalidation_id}")
        log_security_event(
            "cloudfront_invalidation_created",
            {
                "distribution_id": distribution_id,
                "invalidation_id": invalidation_id,
                "caller_reference": str(context.aws_request_id),
            },
        )

        # Log number of files deployed on successful deployment
        # (Requirement 8.3)
        print(f"Frontend Deployer: ✅ Deployed {len(uploaded_files)} files to " f"{bucket_name}")
        logger.info(
            f"Frontend Deployer: ✅ Deployed {len(uploaded_files)} " f"files to {bucket_name}"
        )

        print(f"🎉 Frontend deployment complete! (version: {frontend_version})")

        log_security_event(
            "frontend_deployment_completed",
            {
                "bucket_name": bucket_name,
                "files_deployed": len(uploaded_files),
                "invalidation_id": invalidation_id,
                "frontend_version": frontend_version,
            },
        )

        return {
            "BucketName": bucket_name,
            "FilesDeployed": len(uploaded_files),
            "InvalidationId": invalidation_id,
            "BuildType": "pre-built-react",
            "ConfigFiles": "aws-config.json + aws-config.js",
            "FrontendVersion": frontend_version,
        }

    except Exception as e:
        # Log full stack trace on errors (Requirement 8.5)
        error_msg = f"Error deploying frontend: {str(e)}"
        stack_trace = traceback.format_exc()

        print(f"Frontend Deployer ERROR: {error_msg}")
        logger.error(f"Frontend Deployer ERROR: {error_msg}")
        logger.error(f"Frontend Deployer ERROR Stack trace: {stack_trace}")

        log_security_event(
            "frontend_deployment_error",
            {
                "error": str(e),
                "error_type": type(e).__name__,
                "bucket_name": bucket_name,
                "stack_trace": stack_trace,
            },
            severity="ERROR",
        )

        print(stack_trace)
        raise RuntimeError(error_msg)


@helper.delete
def delete(event, context):
    """
    Handle delete events from CloudFormation.

    CRITICAL SAFETY LOGIC:
    This function ONLY empties the S3 bucket when we can CONFIRM the stack
    is being deleted. We check the stack status and only proceed if:

    1. Stack status is DELETE_IN_PROGRESS (deletion in progress)
    2. Stack status is DELETE_FAILED (deletion failed, likely due to bucket)

    We NEVER empty the bucket if:
    - Stack status contains UPDATE_ROLLBACK (update failed, rolling back)
    - Stack status is anything else (UPDATE_IN_PROGRESS, etc.)
    - Stack doesn't exist (could be wrong ID, not safe to assume)
    - We can't verify stack status (fail safe)

    This prevents accidental data loss during UPDATE operations where
    CloudFormation sends DELETE events for old resources.

    SAFETY RULES:
    1. Only empty bucket when stack status is DELETE_IN_PROGRESS or DELETE_FAILED
    2. Skip cleanup for UPDATE_ROLLBACK operations (explicit check)
    3. Skip cleanup for all other statuses (not a deletion)
    4. Skip cleanup if status check fails (safe default)
    5. Always return SUCCESS to allow stack deletion to continue
    """
    properties = event["ResourceProperties"]
    bucket_name = properties["BucketName"]
    stack_id = event.get("StackId", "")

    print(f"Frontend Deployer DELETE: Received delete event for bucket " f"{bucket_name}")
    logger.info(f"Frontend Deployer DELETE: Received delete event for bucket " f"{bucket_name}")

    # Check stack status - only empty bucket during actual stack deletion
    # Skip cleanup for all other scenarios (UPDATE operations, rollbacks, etc.)
    should_empty, reason, stack_status = should_empty_bucket(stack_id, bucket_name)

    if not should_empty:
        cleanup_decision = f"skip_{reason}"
        print(
            f"Frontend Deployer DELETE: Skipping bucket cleanup - "
            f"{reason} (status: {stack_status})"
        )
        logger.info(
            f"Frontend Deployer DELETE: Skipping bucket cleanup - "
            f"{reason} (status: {stack_status})"
        )
        log_security_event(
            "bucket_cleanup_skipped",
            {
                "bucket_name": bucket_name,
                "reason": reason,
                "stack_status": stack_status,
                "cleanup_decision": cleanup_decision,
            },
        )
        return None

    # Stack is being deleted - proceed with cleanup
    print(
        f"Frontend Deployer DELETE: Stack is being deleted "
        f"(status: {stack_status}), proceeding with bucket cleanup"
    )
    logger.info(
        f"Frontend Deployer DELETE: Stack is being deleted "
        f"(status: {stack_status}), proceeding with bucket cleanup"
    )
    log_security_event(
        "bucket_cleanup_proceeding",
        {
            "bucket_name": bucket_name,
            "stack_status": stack_status,
            "cleanup_decision": "proceed",
        },
    )

    print(f"Frontend Deployer DELETE: Emptying bucket {bucket_name} " f"before deletion...")
    logger.info(f"Frontend Deployer DELETE: Emptying bucket {bucket_name} " f"before deletion...")

    try:
        delete_count = empty_bucket(bucket_name)

        print(
            f"Frontend Deployer DELETE: ✅ Bucket emptied successfully. "
            f"Total objects deleted: {delete_count}"
        )
        log_security_event(
            "bucket_cleanup_completed",
            {
                "bucket_name": bucket_name,
                "objects_deleted": delete_count,
            },
        )
        return None

    except Exception as e:
        # Log full stack trace on errors (Requirement 8.5)
        stack_trace = traceback.format_exc()
        error_msg = f"Error emptying bucket {bucket_name}: {str(e)}"

        print(f"Frontend Deployer DELETE: {error_msg}")
        logger.error(f"Frontend Deployer DELETE: {error_msg}")
        logger.error(f"Frontend Deployer DELETE Stack trace: {stack_trace}")

        log_security_event(
            "bucket_cleanup_error",
            {
                "bucket_name": bucket_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "stack_trace": stack_trace,
            },
            severity="ERROR",
        )

        # Don't raise - allow stack deletion to continue even if cleanup fails
        print("Frontend Deployer DELETE: ⚠️ Continuing with stack deletion " "despite cleanup error")
        logger.warning(
            "Frontend Deployer DELETE: Continuing with stack deletion " "despite cleanup error"
        )
        return None


def lambda_handler(event, context):
    """Main handler for CloudFormation custom resource"""
    # Log CloudFormation event type at start of each invocation
    # (Requirement 8.1)
    request_type = event.get("RequestType", "Unknown")
    bucket_name = event.get("ResourceProperties", {}).get("BucketName", "unknown")

    print(f"Frontend Deployer: Received {request_type} event")
    logger.info(f"Frontend Deployer: Received {request_type} event")
    log_security_event(
        "cfn_event_received",
        {
            "request_type": request_type,
            "bucket_name": bucket_name,
            "request_id": event.get("RequestId", "unknown"),
            "logical_resource_id": event.get("LogicalResourceId", "unknown"),
        },
    )

    print(f"Frontend Deployer: Full event: {json.dumps(event, default=str)}")
    helper(event, context)
