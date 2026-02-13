#!/bin/bash
set -e

# Script to empty frontend S3 buckets for stack deletion
# This handles versioned buckets by deleting all versions and delete markers
#
# IMPORTANT: Set your AWS account ID before running:
#   export AWS_ACCOUNT_ID=your-account-id
#
# Example account ID is provided as default for testing

# Configuration
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-123456789012}"  # Replace with your AWS account ID

empty_bucket() {
    local bucket_name=$1
    
    echo "=================================================="
    echo "Emptying bucket: $bucket_name"
    echo "=================================================="
    
    # Check if bucket exists
    if ! aws s3api head-bucket --bucket "$bucket_name" 2>/dev/null; then
        echo "✓ Bucket $bucket_name does not exist - skipping"
        return 0
    fi
    
    echo "Deleting all object versions and delete markers..."
    
    # Delete all versions
    aws s3api list-object-versions \
        --bucket "$bucket_name" \
        --output json \
        --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' \
        | jq -r '.Objects[]? | "\(.Key)\t\(.VersionId)"' \
        | while IFS=$'\t' read -r key version; do
            if [ -n "$key" ] && [ -n "$version" ]; then
                echo "  Deleting version: $key ($version)"
                aws s3api delete-object \
                    --bucket "$bucket_name" \
                    --key "$key" \
                    --version-id "$version" >/dev/null
            fi
        done
    
    # Delete all delete markers
    aws s3api list-object-versions \
        --bucket "$bucket_name" \
        --output json \
        --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' \
        | jq -r '.Objects[]? | "\(.Key)\t\(.VersionId)"' \
        | while IFS=$'\t' read -r key version; do
            if [ -n "$key" ] && [ -n "$version" ]; then
                echo "  Deleting marker: $key ($version)"
                aws s3api delete-object \
                    --bucket "$bucket_name" \
                    --key "$key" \
                    --version-id "$version" >/dev/null
            fi
        done
    
    # Verify bucket is empty
    object_count=$(aws s3api list-object-versions --bucket "$bucket_name" --output json | jq -r '[.Versions?, .DeleteMarkers?] | flatten | length')
    
    if [ "$object_count" -eq 0 ]; then
        echo "✓ Bucket $bucket_name is now empty"
    else
        echo "⚠ Warning: Bucket $bucket_name still has $object_count objects"
    fi
    
    echo ""
}

# Empty both frontend buckets
empty_bucket "hrp-drs-tech-adapter-fe-${AWS_ACCOUNT_ID}-test"
empty_bucket "hrp-drs-tech-adapter-fe-${AWS_ACCOUNT_ID}-dev"

echo "=================================================="
echo "✓ All frontend buckets emptied"
echo "=================================================="
