"""
S3 Cleanup Custom Resource
Empties S3 bucket on CloudFormation stack deletion
"""

import boto3
import json
from crhelper import CfnResource

s3 = boto3.client('s3')
helper = CfnResource()


@helper.create
def create(event, context):
    """No-op for Create"""
    print("S3 Cleanup: Create event - no action required")
    return None


@helper.update
def update(event, context):
    """No-op for Update"""
    print("S3 Cleanup: Update event - no action required")
    return None


@helper.delete
def delete(event, context):
    """Empty S3 bucket on Delete"""
    bucket_name = event['ResourceProperties']['BucketName']
    print(f"S3 Cleanup: Emptying bucket: {bucket_name}")
    
    try:
        # Delete all objects
        paginator = s3.get_paginator('list_object_versions')
        page_count = 0
        object_count = 0
        
        for page in paginator.paginate(Bucket=bucket_name):
            page_count += 1
            objects = []
            
            # Get regular objects
            for obj in page.get('Versions', []):
                objects.append({
                    'Key': obj['Key'],
                    'VersionId': obj['VersionId']
                })
            
            # Get delete markers
            for obj in page.get('DeleteMarkers', []):
                objects.append({
                    'Key': obj['Key'],
                    'VersionId': obj['VersionId']
                })
            
            # Delete in batches of 1000
            if objects:
                object_count += len(objects)
                response = s3.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': objects}
                )
                
                deleted_count = len(response.get('Deleted', []))
                error_count = len(response.get('Errors', []))
                
                print(f"Page {page_count}: Deleted {deleted_count} objects, {error_count} errors")
                
                if error_count > 0:
                    print(f"Errors encountered: {response.get('Errors')}")
        
        print(f"Successfully emptied bucket: {bucket_name}")
        print(f"Total objects deleted: {object_count} across {page_count} pages")
        
    except s3.exceptions.NoSuchBucket:
        print(f"Bucket {bucket_name} does not exist - nothing to clean up")
    except Exception as e:
        print(f"Error emptying bucket: {str(e)}")
        # Don't fail - allow stack deletion to proceed
        # This ensures CloudFormation can delete the bucket even if cleanup partially fails
    
    return None


def lambda_handler(event, context):
    """Main handler for CloudFormation custom resource"""
    print(f"S3 Cleanup: Received event: {json.dumps(event, default=str)}")
    helper(event, context)
