#!/usr/bin/env bash
#
# DR CI/CD Pipeline Integration Script
#
# This script demonstrates how to integrate AWS DRS Orchestration Platform
# into CI/CD pipelines for automated disaster recovery testing.
#
# Use Cases:
# - Validate DR readiness before production deployments
# - Run automated DR drills on schedule
# - Test DR procedures as part of release validation
# - Ensure DR infrastructure is functional
#
# Requirements:
# - AWS CLI v2 installed and configured
# - jq for JSON parsing
# - IAM permissions for lambda:InvokeFunction on DRS Orchestration functions
# - Bash 4.0 or higher
#
# Usage:
#   ./dr_ci_pipeline.sh --plan-id <recovery-plan-id> [options]
#   ./dr_ci_pipeline.sh --list-plans
#   ./dr_ci_pipeline.sh --help
#
# Exit Codes:
#   0 - Success (DR drill passed)
#   1 - General error
#   2 - DR drill failed
#   3 - Invalid arguments
#   4 - AWS CLI error
#   5 - Timeout waiting for execution

set -euo pipefail

# Script configuration
SCRIPT_NAME=$(basename "$0")
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

# Default values
ENVIRONMENT="${DR_ENVIRONMENT:-test}"
REGION="${AWS_REGION:-us-east-1}"
EXECUTION_TYPE="DRILL"
POLL_INTERVAL=30
MAX_WAIT_TIME=3600  # 1 hour
TERMINATE_INSTANCES=true
VERBOSE=false

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Lambda function names
PROJECT_NAME="aws-drs-orchestration"
QUERY_HANDLER="${PROJECT_NAME}-query-handler-${ENVIRONMENT}"
EXECUTION_HANDLER="${PROJECT_NAME}-execution-handler-${ENVIRONMENT}"
DATA_MGMT_HANDLER="${PROJECT_NAME}-data-management-handler-${ENVIRONMENT}"

#######################################
# Print colored message
# Arguments:
#   $1 - Color code
#   $2 - Message
#######################################
print_color() {
    local color=$1
    shift
    echo -e "${color}$*${NC}"
}

#######################################
# Print info message
#######################################
info() {
    print_color "$BLUE" "[INFO] $*"
}

#######################################
# Print success message
#######################################
success() {
    print_color "$GREEN" "[SUCCESS] $*"
}

#######################################
# Print warning message
#######################################
warning() {
    print_color "$YELLOW" "[WARNING] $*"
}

#######################################
# Print error message
#######################################
error() {
    print_color "$RED" "[ERROR] $*" >&2
}

#######################################
# Print verbose message
#######################################
verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        print_color "$BLUE" "[DEBUG] $*"
    fi
}

#######################################
# Print usage information
#######################################
usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Integrate AWS DRS Orchestration into CI/CD pipelines for automated DR testing.

OPTIONS:
    --plan-id ID            Recovery plan ID to execute (required unless --list-plans)
    --list-plans            List all available recovery plans
    --environment ENV       Deployment environment (default: test)
                           Options: dev, test, staging, prod
    --region REGION         AWS region (default: us-east-1)
    --execution-type TYPE   Execution type (default: DRILL)
                           Options: DRILL, RECOVERY
    --poll-interval SEC     Seconds between status checks (default: 30)
    --max-wait-time SEC     Maximum time to wait for completion (default: 3600)
    --no-terminate          Don't terminate instances after drill
    --verbose               Enable verbose output
    --help                  Show this help message

ENVIRONMENT VARIABLES:
    DR_ENVIRONMENT          Default environment (overridden by --environment)
    AWS_REGION              Default AWS region (overridden by --region)
    AWS_PROFILE             AWS CLI profile to use

EXAMPLES:
    # List available recovery plans
    $SCRIPT_NAME --list-plans

    # Run DR drill in test environment
    $SCRIPT_NAME --plan-id 550e8400-e29b-41d4-a716-446655440000

    # Run DR drill in production (use with caution!)
    $SCRIPT_NAME --plan-id <plan-id> --environment prod --execution-type RECOVERY

    # Run with custom polling and timeout
    $SCRIPT_NAME --plan-id <plan-id> --poll-interval 60 --max-wait-time 7200

    # Keep instances running after drill
    $SCRIPT_NAME --plan-id <plan-id> --no-terminate

EXIT CODES:
    0 - DR drill completed successfully
    1 - General error
    2 - DR drill failed
    3 - Invalid arguments
    4 - AWS CLI error
    5 - Timeout waiting for execution

EOF
}

#######################################
# Check prerequisites
#######################################
check_prerequisites() {
    info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed"
        error "Install from: https://aws.amazon.com/cli/"
        exit 4
    fi
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        error "jq is not installed"
        error "Install from: https://stedolan.github.io/jq/"
        exit 4
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials are not configured"
        error "Configure with: aws configure"
        exit 4
    fi
    
    local caller_identity
    caller_identity=$(aws sts get-caller-identity)
    verbose "AWS Identity: $(echo "$caller_identity" | jq -r '.Arn')"
    
    success "Prerequisites check passed"
}

#######################################
# Invoke Lambda function
# Arguments:
#   $1 - Function name
#   $2 - JSON payload
# Returns:
#   JSON response from Lambda
#######################################
invoke_lambda() {
    local function_name=$1
    local payload=$2
    
    verbose "Invoking Lambda: $function_name"
    verbose "Payload: $payload"
    
    local response
    local status_code
    
    # Invoke Lambda and capture response
    response=$(aws lambda invoke \
        --function-name "$function_name" \
        --payload "$payload" \
        --region "$REGION" \
        --cli-binary-format raw-in-base64-out \
        /dev/stdout 2>&1)
    
    status_code=$?
    
    if [[ $status_code -ne 0 ]]; then
        error "Lambda invocation failed"
        error "Response: $response"
        exit 4
    fi
    
    verbose "Response: $response"
    
    # Check for error in response
    if echo "$response" | jq -e '.error' &> /dev/null; then
        local error_code
        local error_message
        error_code=$(echo "$response" | jq -r '.error')
        error_message=$(echo "$response" | jq -r '.message')
        error "Lambda returned error: $error_code - $error_message"
        exit 1
    fi
    
    echo "$response"
}

#######################################
# List available recovery plans
#######################################
list_recovery_plans() {
    info "Listing available recovery plans..."
    
    local payload
    payload=$(jq -n '{operation: "list_recovery_plans"}')
    
    local response
    response=$(invoke_lambda "$QUERY_HANDLER" "$payload")
    
    local plans
    plans=$(echo "$response" | jq -r '.recoveryPlans')
    
    local plan_count
    plan_count=$(echo "$plans" | jq 'length')
    
    if [[ $plan_count -eq 0 ]]; then
        warning "No recovery plans found"
        return
    fi
    
    echo ""
    echo "================================================================================"
    echo "AVAILABLE RECOVERY PLANS ($plan_count)"
    echo "================================================================================"
    echo ""
    
    echo "$plans" | jq -r '.[] | 
        "Plan ID: \(.planId)\n" +
        "Name: \(.name)\n" +
        "Description: \(.description // "N/A")\n" +
        "Protection Group: \(.protectionGroupName // "N/A")\n" +
        "Waves: \(.waveCount // 0)\n" +
        "Status: \(.status // "N/A")\n"'
}

#######################################
# Get recovery plan details
# Arguments:
#   $1 - Plan ID
# Returns:
#   JSON plan details
#######################################
get_recovery_plan() {
    local plan_id=$1
    
    verbose "Getting recovery plan: $plan_id"
    
    local payload
    payload=$(jq -n --arg planId "$plan_id" '{
        operation: "get_recovery_plan",
        planId: $planId
    }')
    
    invoke_lambda "$QUERY_HANDLER" "$payload"
}

#######################################
# Start recovery execution
# Arguments:
#   $1 - Plan ID
#   $2 - Execution type (DRILL or RECOVERY)
# Returns:
#   JSON execution start response
#######################################
start_execution() {
    local plan_id=$1
    local execution_type=$2
    
    info "Starting $execution_type execution for plan: $plan_id"
    
    local payload
    payload=$(jq -n \
        --arg planId "$plan_id" \
        --arg executionType "$execution_type" \
        '{
            operation: "start_execution",
            parameters: {
                planId: $planId,
                executionType: $executionType,
                initiatedBy: "ci-cd-pipeline"
            }
        }')
    
    invoke_lambda "$EXECUTION_HANDLER" "$payload"
}

#######################################
# Get execution status
# Arguments:
#   $1 - Execution ID
# Returns:
#   JSON execution details
#######################################
get_execution() {
    local execution_id=$1
    
    verbose "Getting execution status: $execution_id"
    
    local payload
    payload=$(jq -n --arg executionId "$execution_id" '{
        operation: "get_execution",
        executionId: $executionId
    }')
    
    invoke_lambda "$QUERY_HANDLER" "$payload"
}

#######################################
# Monitor execution until completion
# Arguments:
#   $1 - Execution ID
# Returns:
#   Final execution status
#######################################
monitor_execution() {
    local execution_id=$1
    local start_time
    start_time=$(date +%s)
    
    info "Monitoring execution: $execution_id"
    info "Poll interval: ${POLL_INTERVAL}s, Max wait: ${MAX_WAIT_TIME}s"
    
    local terminal_statuses=("COMPLETED" "FAILED" "CANCELLED" "PARTIAL")
    
    while true; do
        local current_time
        current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        # Check timeout
        if [[ $elapsed -gt $MAX_WAIT_TIME ]]; then
            error "Timeout waiting for execution to complete (${MAX_WAIT_TIME}s)"
            exit 5
        fi
        
        # Get execution status
        local execution
        execution=$(get_execution "$execution_id")
        
        local status
        local current_wave
        local total_waves
        status=$(echo "$execution" | jq -r '.status')
        current_wave=$(echo "$execution" | jq -r '.currentWave // 0')
        total_waves=$(echo "$execution" | jq -r '.totalWaves // 0')
        
        # Display status
        local timestamp
        timestamp=$(date '+%H:%M:%S')
        info "[$timestamp] Status: $status, Wave: $current_wave/$total_waves, Elapsed: ${elapsed}s"
        
        # Check if execution is complete
        for terminal_status in "${terminal_statuses[@]}"; do
            if [[ "$status" == "$terminal_status" ]]; then
                success "Execution finished with status: $status"
                echo "$execution"
                return
            fi
        done
        
        # Wait before next poll
        sleep "$POLL_INTERVAL"
    done
}

#######################################
# Get recovery instances
# Arguments:
#   $1 - Execution ID
# Returns:
#   JSON recovery instances
#######################################
get_recovery_instances() {
    local execution_id=$1
    
    verbose "Getting recovery instances for execution: $execution_id"
    
    local payload
    payload=$(jq -n --arg executionId "$execution_id" '{
        operation: "get_recovery_instances",
        parameters: {
            executionId: $executionId
        }
    }')
    
    invoke_lambda "$EXECUTION_HANDLER" "$payload"
}

#######################################
# Terminate recovery instances
# Arguments:
#   $1 - Execution ID
# Returns:
#   JSON termination response
#######################################
terminate_instances() {
    local execution_id=$1
    
    info "Terminating recovery instances for execution: $execution_id"
    
    local payload
    payload=$(jq -n --arg executionId "$execution_id" '{
        operation: "terminate_instances",
        parameters: {
            executionId: $executionId
        }
    }')
    
    invoke_lambda "$EXECUTION_HANDLER" "$payload"
}

#######################################
# Display execution summary
# Arguments:
#   $1 - Execution JSON
#######################################
display_execution_summary() {
    local execution=$1
    
    echo ""
    echo "================================================================================"
    echo "EXECUTION SUMMARY"
    echo "================================================================================"
    echo ""
    
    local execution_id
    local status
    local current_wave
    local total_waves
    execution_id=$(echo "$execution" | jq -r '.executionId')
    status=$(echo "$execution" | jq -r '.status')
    current_wave=$(echo "$execution" | jq -r '.currentWave // 0')
    total_waves=$(echo "$execution" | jq -r '.totalWaves // 0')
    
    echo "Execution ID: $execution_id"
    echo "Status: $status"
    echo "Waves: $current_wave/$total_waves"
    echo ""
    
    # Display wave details
    local waves
    waves=$(echo "$execution" | jq -r '.waves // []')
    
    if [[ $(echo "$waves" | jq 'length') -gt 0 ]]; then
        echo "Wave Status:"
        echo "$waves" | jq -r '.[] | 
            "  - \(.waveName): \(.status // "UNKNOWN") " +
            "(\(.serversLaunched // 0)/\(.serverCount // 0) servers)"'
        echo ""
    fi
}

#######################################
# Display instance summary
# Arguments:
#   $1 - Instances JSON
#######################################
display_instance_summary() {
    local instances_json=$1
    
    local instances
    instances=$(echo "$instances_json" | jq -r '.instances // []')
    
    local instance_count
    instance_count=$(echo "$instances" | jq 'length')
    
    echo ""
    echo "================================================================================"
    echo "RECOVERY INSTANCES ($instance_count)"
    echo "================================================================================"
    echo ""
    
    if [[ $instance_count -eq 0 ]]; then
        warning "No recovery instances found"
        return
    fi
    
    echo "$instances" | jq -r '.[] | 
        "Instance: \(.name)\n" +
        "  EC2 ID: \(.ec2InstanceId)\n" +
        "  State: \(.ec2InstanceState)\n" +
        "  Type: \(.instanceType)\n" +
        "  Region: \(.region)\n" +
        "  Private IP: \(.privateIp // "N/A")\n" +
        "  Public IP: \(.publicIp // "N/A")\n" +
        "  Wave: \(.waveName // "N/A")\n"'
}

#######################################
# Run complete DR workflow
# Arguments:
#   $1 - Plan ID
#######################################
run_dr_workflow() {
    local plan_id=$1
    
    echo ""
    echo "================================================================================"
    echo "DR CI/CD PIPELINE - $EXECUTION_TYPE MODE"
    echo "================================================================================"
    echo "Environment: $ENVIRONMENT"
    echo "Region: $REGION"
    echo "Plan ID: $plan_id"
    echo "================================================================================"
    echo ""
    
    # Step 1: Get recovery plan details
    info "[Step 1/6] Getting recovery plan details..."
    local plan
    plan=$(get_recovery_plan "$plan_id")
    
    local plan_name
    local protection_group
    local wave_count
    plan_name=$(echo "$plan" | jq -r '.name')
    protection_group=$(echo "$plan" | jq -r '.protectionGroupName // "N/A"')
    wave_count=$(echo "$plan" | jq -r '.waves | length')
    
    success "Plan: $plan_name"
    info "  Protection Group: $protection_group"
    info "  Waves: $wave_count"
    
    # Display wave information
    echo "$plan" | jq -r '.waves[]? | 
        "    - Wave \(.waveNumber): \(.name) " +
        "(\(.serverCount // 0) servers)"'
    
    # Step 2: Start execution
    echo ""
    info "[Step 2/6] Starting $EXECUTION_TYPE execution..."
    local start_result
    start_result=$(start_execution "$plan_id" "$EXECUTION_TYPE")
    
    local execution_id
    local initial_status
    execution_id=$(echo "$start_result" | jq -r '.executionId')
    initial_status=$(echo "$start_result" | jq -r '.status')
    
    success "Execution started: $execution_id"
    info "  Initial Status: $initial_status"
    
    # Step 3: Monitor execution
    echo ""
    info "[Step 3/6] Monitoring execution progress..."
    local final_execution
    final_execution=$(monitor_execution "$execution_id")
    
    # Step 4: Display execution summary
    echo ""
    info "[Step 4/6] Execution completed"
    display_execution_summary "$final_execution"
    
    local final_status
    final_status=$(echo "$final_execution" | jq -r '.status')
    
    # Check if execution succeeded
    if [[ "$final_status" != "COMPLETED" ]]; then
        error "DR drill failed with status: $final_status"
        exit 2
    fi
    
    # Step 5: Get recovery instances
    echo ""
    info "[Step 5/6] Getting recovery instance details..."
    local instances
    instances=$(get_recovery_instances "$execution_id")
    
    display_instance_summary "$instances"
    
    # Step 6: Terminate instances (if enabled)
    if [[ "$TERMINATE_INSTANCES" == "true" ]]; then
        echo ""
        info "[Step 6/6] Terminating recovery instances..."
        
        local terminate_result
        terminate_result=$(terminate_instances "$execution_id")
        
        local termination_status
        local total_instances
        termination_status=$(echo "$terminate_result" | jq -r '.status')
        total_instances=$(echo "$terminate_result" | jq -r '.details.totalInstances')
        
        success "Termination initiated: $termination_status"
        info "  Total instances: $total_instances"
        
        # Display termination jobs
        echo "$terminate_result" | jq -r '.details.terminationJobs[]? | 
            "    - Job \(.jobId): \(.instanceCount) instances in \(.region)"'
    else
        echo ""
        warning "[Step 6/6] Skipping instance termination (--no-terminate flag)"
        warning "  Remember to manually terminate instances to avoid costs!"
    fi
    
    # Final success message
    echo ""
    echo "================================================================================"
    success "DR DRILL COMPLETED SUCCESSFULLY"
    echo "================================================================================"
    echo ""
}

#######################################
# Main function
#######################################
main() {
    local plan_id=""
    local list_plans=false
    
    # Parse command-line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --plan-id)
                plan_id="$2"
                shift 2
                ;;
            --list-plans)
                list_plans=true
                shift
                ;;
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --region)
                REGION="$2"
                shift 2
                ;;
            --execution-type)
                EXECUTION_TYPE="$2"
                shift 2
                ;;
            --poll-interval)
                POLL_INTERVAL="$2"
                shift 2
                ;;
            --max-wait-time)
                MAX_WAIT_TIME="$2"
                shift 2
                ;;
            --no-terminate)
                TERMINATE_INSTANCES=false
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 3
                ;;
        esac
    done
    
    # Update function names with environment
    QUERY_HANDLER="${PROJECT_NAME}-query-handler-${ENVIRONMENT}"
    EXECUTION_HANDLER="${PROJECT_NAME}-execution-handler-${ENVIRONMENT}"
    DATA_MGMT_HANDLER="${PROJECT_NAME}-data-management-handler-${ENVIRONMENT}"
    
    # Check prerequisites
    check_prerequisites
    
    # Execute requested operation
    if [[ "$list_plans" == "true" ]]; then
        list_recovery_plans
    elif [[ -n "$plan_id" ]]; then
        run_dr_workflow "$plan_id"
    else
        error "Either --plan-id or --list-plans is required"
        usage
        exit 3
    fi
}

# Run main function
main "$@"
