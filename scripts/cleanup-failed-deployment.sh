#!/bin/bash

# AWS DRS Orchestration - Cleanup Failed Deployment Script
# This script handles cleanup of failed CloudFormation deployments

set -e

# Configuration
PROJECT_NAME="aws-drs-orch"
ENVIRONMENT="dev"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
AWS_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if stack exists and get status
check_stack_status() {
    local stack_name="$1"
    
    if aws cloudformation describe-stacks --stack-name "$stack_name" --region "$AWS_REGION" > /dev/null 2>&1; then
        local status
        status=$(aws cloudformation describe-stacks --stack-name "$stack_name" --region "$AWS_REGION" --query 'Stacks[0].StackStatus' --output text)
        echo "$status"
    else
        echo "NOT_EXISTS"
    fi
}

# Get failed resources from stack
get_failed_resources() {
    local stack_name="$1"
    
    log_info "Getting failed resources for stack: $stack_name"
    
    aws cloudformation describe-stack-events \
        --stack-name "$stack_name" \
        --region "$AWS_REGION" \
        --query 'StackEvents[?ResourceStatus==`DELETE_FAILED`].{LogicalResourceId:LogicalResourceId,ResourceType:ResourceType,ResourceStatusReason:ResourceStatusReason}' \
        --output table
}

# Force empty and delete S3 bucket
force_delete_s3_bucket() {
    local bucket_name="$1"
    
    log_info "Force deleting S3 bucket: $bucket_name"
    
    # Check if bucket exists
    if ! aws s3api head-bucket --bucket "$bucket_name" > /dev/null 2>&1; then
        log_success "Bucket $bucket_name does not exist"
        return 0
    fi
    
    # Remove bucket policy if exists
    aws s3api delete-bucket-policy --bucket "$bucket_name" > /dev/null 2>&1 || true
    
    # Delete all object versions
    log_info "Deleting all object versions..."
    aws s3api list-object-versions --bucket "$bucket_name" --output json --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' > /tmp/versions.json 2>/dev/null || echo '{"Objects": []}' > /tmp/versions.json
    
    if [ -s /tmp/versions.json ] && [ "$(cat /tmp/versions.json | jq '.Objects | length')" -gt 0 ]; then
        aws s3api delete-objects --bucket "$bucket_name" --delete file:///tmp/versions.json > /dev/null 2>&1 || true
    fi
    
    # Delete all delete markers
    log_info "Deleting all delete markers..."
    aws s3api list-object-versions --bucket "$bucket_name" --output json --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' > /tmp/delete_markers.json 2>/dev/null || echo '{"Objects": []}' > /tmp/delete_markers.json
    
    if [ -s /tmp/delete_markers.json ] && [ "$(cat /tmp/delete_markers.json | jq '.Objects | length')" -gt 0 ]; then
        aws s3api delete-objects --bucket "$bucket_name" --delete file:///tmp/delete_markers.json > /dev/null 2>&1 || true
    fi
    
    # Force remove all remaining objects
    aws s3 rm "s3://$bucket_name" --recursive > /dev/null 2>&1 || true
    
    # Delete the bucket
    if aws s3api delete-bucket --bucket "$bucket_name" > /dev/null 2>&1; then
        log_success "Successfully deleted bucket: $bucket_name"
    else
        log_error "Failed to delete bucket: $bucket_name"
        return 1
    fi
    
    # Cleanup temp files
    rm -f /tmp/versions.json /tmp/delete_markers.json
}

# Clean up CloudTrail resources
cleanup_cloudtrail_resources() {
    local account_id
    account_id=$(aws sts get-caller-identity --query Account --output text)
    local cloudtrail_bucket="${PROJECT_NAME}-cloudtrail-${account_id}"
    
    log_info "Cleaning up CloudTrail resources..."
    
    # Stop CloudTrail if it exists
    local trail_name="${PROJECT_NAME}-trail"
    if aws cloudtrail describe-trails --trail-name-list "$trail_name" --region "$AWS_REGION" > /dev/null 2>&1; then
        log_info "Stopping CloudTrail: $trail_name"
        aws cloudtrail stop-logging --name "$trail_name" --region "$AWS_REGION" > /dev/null 2>&1 || true
    fi
    
    # Force delete CloudTrail bucket
    force_delete_s3_bucket "$cloudtrail_bucket"
}

# Clean up nested stacks
cleanup_nested_stacks() {
    local parent_stack="$1"
    
    log_info "Finding nested stacks for: $parent_stack"
    
    # Get nested stack names
    local nested_stacks
    nested_stacks=$(aws cloudformation list-stack-resources \
        --stack-name "$parent_stack" \
        --region "$AWS_REGION" \
        --query 'StackResourceSummaries[?ResourceType==`AWS::CloudFormation::Stack`].PhysicalResourceId' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$nested_stacks" ]; then
        for nested_stack in $nested_stacks; do
            log_info "Cleaning up nested stack: $nested_stack"
            
            local nested_status
            nested_status=$(check_stack_status "$nested_stack")
            
            if [ "$nested_status" != "NOT_EXISTS" ]; then
                log_info "Nested stack $nested_stack status: $nested_status"
                
                # If nested stack is in failed state, try to clean it up
                if [[ "$nested_status" == *"FAILED"* ]]; then
                    get_failed_resources "$nested_stack"
                    
                    # Try to delete the nested stack
                    aws cloudformation delete-stack --stack-name "$nested_stack" --region "$AWS_REGION" > /dev/null 2>&1 || true
                fi
            fi
        done
    fi
}

# Main cleanup function
cleanup_failed_deployment() {
    log_info "=== AWS DRS Orchestration - Cleanup Failed Deployment ==="
    log_info "Stack Name: $STACK_NAME"
    log_info "Region: $AWS_REGION"
    echo ""
    
    # Check stack status
    local stack_status
    stack_status=$(check_stack_status "$STACK_NAME")
    
    log_info "Current stack status: $stack_status"
    
    if [ "$stack_status" = "NOT_EXISTS" ]; then
        log_success "Stack does not exist - no cleanup needed"
        return 0
    fi
    
    # If stack is in failed state, perform cleanup
    if [[ "$stack_status" == *"FAILED"* ]]; then
        log_warning "Stack is in failed state - performing cleanup"
        
        # Show failed resources
        get_failed_resources "$STACK_NAME"
        
        # Clean up nested stacks first
        cleanup_nested_stacks "$STACK_NAME"
        
        # Clean up specific problematic resources
        cleanup_cloudtrail_resources
        
        # Try to delete the main stack
        log_info "Attempting to delete main stack..."
        aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$AWS_REGION"
        
        # Wait for deletion with timeout
        log_info "Waiting for stack deletion (timeout: 10 minutes)..."
        if timeout 600 aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$AWS_REGION" 2>/dev/null; then
            log_success "Stack deleted successfully"
        else
            log_error "Stack deletion timed out or failed"
            
            # Check final status
            local final_status
            final_status=$(check_stack_status "$STACK_NAME")
            log_info "Final stack status: $final_status"
            
            if [ "$final_status" = "NOT_EXISTS" ]; then
                log_success "Stack was eventually deleted"
            else
                log_error "Stack cleanup failed - manual intervention required"
                return 1
            fi
        fi
    else
        log_info "Stack is not in failed state - no cleanup needed"
    fi
    
    log_success "Cleanup completed successfully"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --stack-name NAME    Stack name to cleanup (default: $STACK_NAME)"
            echo "  --region REGION      AWS region (default: $AWS_REGION)"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check dependencies
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI is not installed or not in PATH"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    log_error "jq is not installed or not in PATH"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    log_error "AWS credentials not configured or invalid"
    exit 1
fi

# Run cleanup
cleanup_failed_deployment