"""
AWS DRS Orchestration - S3 Bucket Cleaner Lambda Function

This Lambda function is used as a CloudFormation custom resource to empty
S3 buckets (including all versions and delete markers) before stack deletion.
This ensures that versioned S3 buckets can be properly deleted by
CloudFormation.

Author: AWS DRS Orchestration Team
Version: 1.0.0
"""

import json
import logging

import boto3
import urllib3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def send_response(
    event,
    context,
    response_status,
    response_data,
    physical_resource_id=None,
    no_echo=False,
):
    """
    Send response to CloudFormation custom resource.

    This is a simplified version of cfnresponse that works in all Lambda
    environments.
    """
    response_url = event["ResponseURL"]

    # Ensure response_status is valid
    if response_status not in ["SUCCESS", "FAILED"]:
        logger.error(f"Invalid response_status: {response_status}")
        response_status = "FAILED"

    response_body = {
        "Status": response_status,  # CloudFormation expects "Status" not "status"
        "Reason": (
            f"See the details in CloudWatch Log Stream: "
            f"{context.log_stream_name}"
        ),
        "PhysicalResourceId": (
            physical_resource_id or context.log_stream_name
        ),
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "NoEcho": no_echo,
        "Data": response_data,
    }

    json_response_body = json.dumps(response_body)

    headers = {
        "content-type": "",
        "content-length": str(len(json_response_body)),
    }

    try:
        http = urllib3.PoolManager()
        logger.info(f"Sending response to CloudFormation: {response_status}")
        logger.info(f"Response body: {json_response_body}")
        
        response = http.request(
            "PUT", response_url, body=json_response_body, headers=headers
        )
        logger.info(f"CloudFormation response status code: {response.status}")
        
        if response.status != 200:
            logger.error(f"CloudFormation response error: {response.data}")
            
    except Exception as e:
        logger.error(f"Failed to send response to CloudFormation: {e}")
        raise


def lambda_handler(event, context):
    """
    CloudFormation custom resource handler for emptying S3 buckets.

    Args:
        event: CloudFormation custom resource event
        context: Lambda context object

    Returns:
        CloudFormation response via send_response
    """
    logger.info(f"Received event: {json.dumps(event, default=str)}")

    try:
        # Extract parameters
        request_type = event["RequestType"]
        bucket_name = event["ResourceProperties"]["BucketName"]

        logger.info(f"Request type: {request_type}")
        logger.info(f"Bucket name: {bucket_name}")

        # Only process DELETE requests - ignore CREATE and UPDATE
        if request_type == "Delete":
            empty_bucket(bucket_name)
            logger.info(f"Successfully emptied bucket: {bucket_name}")
        else:
            logger.info(f"Skipping {request_type} request - no action needed")

        # Send success response
        send_response(
            event,
            context,
            "SUCCESS",
            {
                "Message": (
                    f"Bucket {bucket_name} processed successfully "
                    f"for {request_type}"
                )
            },
        )

    except Exception as e:
        logger.error(f"Error processing bucket cleanup: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        
        # Always send a response, even on error
        try:
            send_response(
                event,
                context,
                "FAILED",
                {"Message": f"Failed to process bucket cleanup: {str(e)}"},
            )
        except Exception as send_error:
            logger.error(f"Failed to send error response: {send_error}")
            # Re-raise original exception if we can't even send the response
            raise e


def empty_bucket(bucket_name):
    """
    Empty an S3 bucket by deleting all objects, versions, and delete markers.

    Args:
        bucket_name: Name of the S3 bucket to empty
    """
    s3_client = boto3.client("s3")

    try:
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.info(
                    f"Bucket {bucket_name} does not exist - nothing to clean"
                )
                return
            else:
                raise

        logger.info(f"Starting to empty bucket: {bucket_name}")

        # Delete all object versions and delete markers
        paginator = s3_client.get_paginator("list_object_versions")

        for page in paginator.paginate(Bucket=bucket_name):
            # Collect objects to delete
            objects_to_delete = []

            # Add current versions
            if "Versions" in page:
                for version in page["Versions"]:
                    objects_to_delete.append(
                        {
                            "Key": version["Key"],
                            "VersionId": version["VersionId"],
                        }
                    )

            # Add delete markers
            if "DeleteMarkers" in page:
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
                    batch = objects_to_delete[i : i + batch_size]

                    logger.info(
                        f"Deleting batch of {len(batch)} objects from "
                        f"{bucket_name}"
                    )

                    response = s3_client.delete_objects(
                        Bucket=bucket_name,
                        Delete={"Objects": batch, "Quiet": True},
                    )

                    # Log any errors
                    if "Errors" in response and response["Errors"]:
                        for error in response["Errors"]:
                            logger.warning(
                                f"Failed to delete {error['Key']}: "
                                f"{error['Message']}"
                            )

        # Verify bucket is empty
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        if "Contents" in response:
            logger.warning(
                f"Bucket {bucket_name} still contains objects after cleanup"
            )
        else:
            logger.info(f"Bucket {bucket_name} is now empty")

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            logger.info(
                f"Bucket {bucket_name} does not exist - nothing to clean"
            )
        else:
            logger.error(
                f"AWS error emptying bucket {bucket_name}: {error_code} - "
                f"{e.response['Error']['Message']}"
            )
            raise
    except Exception as e:
        logger.error(
            f"Unexpected error emptying bucket {bucket_name}: {str(e)}"
        )
        raise
